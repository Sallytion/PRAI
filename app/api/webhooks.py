"""
GitHub Webhooks API Routes - MongoDB/Beanie
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import hmac
import hashlib

from app.models.repository import Repository
from app.models.pull_request import PullRequest, PRStatus
from app.config import get_settings
from app.tasks.review_tasks import process_pr_review

settings = get_settings()
router = APIRouter()


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


@router.post("/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle GitHub webhook events"""
    
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    payload_body = await request.body()
    
    if not verify_webhook_signature(payload_body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Get event type
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    if event_type == "ping":
        return {"message": "Webhook configured successfully"}
    
    if event_type == "pull_request":
        await handle_pull_request_event(payload, background_tasks)
    
    elif event_type == "pull_request_review":
        # Handle review events if needed
        pass
    
    return {"status": "processed"}


async def handle_pull_request_event(
    payload: dict,
    background_tasks: BackgroundTasks
):
    """Handle pull request events"""
    action = payload.get("action")
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    
    # Find repository in database
    repository = await Repository.find_one(
        Repository.github_repo_id == repo_data["id"]
    )
    
    if not repository or not repository.is_active:
        return
    
    # Create or update PR record
    pull_request = await PullRequest.find_one(
        PullRequest.repository_id == str(repository.id),
        PullRequest.pr_number == pr_data["number"]
    )
    
    if action in ["opened", "synchronize", "reopened"]:
        # New PR or updated PR
        if not pull_request:
            pull_request = PullRequest(
                repository_id=str(repository.id),
                pr_number=pr_data["number"],
                title=pr_data["title"],
                description=pr_data.get("body", ""),
                author=pr_data["user"]["login"],
                status=PRStatus.OPEN,
                github_url=pr_data["html_url"],
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
                changed_files=pr_data.get("changed_files", 0)
            )
            await pull_request.insert()
        else:
            pull_request.title = pr_data["title"]
            pull_request.description = pr_data.get("body", "")
            pull_request.additions = pr_data.get("additions", 0)
            pull_request.deletions = pr_data.get("deletions", 0)
            pull_request.changed_files = pr_data.get("changed_files", 0)
            await pull_request.save()
        
        # Trigger review in background
        background_tasks.add_task(
            process_pr_review,
            repository_id=str(repository.id),
            pr_number=pr_data["number"],
            user_id=repository.user_id
        )
    
    elif action == "closed":
        if pull_request:
            pull_request.status = PRStatus.MERGED if pr_data.get("merged") else PRStatus.CLOSED
            await pull_request.save()
