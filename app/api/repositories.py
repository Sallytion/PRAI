"""
Repositories API Routes - MongoDB/Beanie
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List

from app.core.github_client import GitHubClient
from app.models.user import User
from app.models.repository import Repository
from app.core.auth import verify_token
from app.config import get_settings

settings = get_settings()
router = APIRouter()


async def get_current_user_from_token(request: Request) -> User:
    """Dependency to get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    user = await User.get(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/")
async def list_github_repositories(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get user's GitHub repositories"""
    github_client = GitHubClient(current_user.access_token)
    
    try:
        repos = github_client.get_user_repos()
        return {"repositories": repos}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch repositories: {str(e)}")


@router.get("/tracked")
async def list_tracked_repositories(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get user's tracked repositories"""
    repositories = await Repository.find(
        Repository.user_id == str(current_user.id)
    ).to_list()
    
    return {
        "repositories": [
            {
                "id": str(repo.id),
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.url,
                "is_active": repo.is_active,
                "webhook_configured": repo.webhook_configured,
                "created_at": repo.created_at.isoformat()
            }
            for repo in repositories
        ]
    }


@router.post("/track/{owner}/{repo}")
async def track_repository(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Start tracking a repository"""
    repo_full_name = f"{owner}/{repo}"
    github_client = GitHubClient(current_user.access_token)
    
    try:
        # Get repository details
        repo = github_client.get_repository(repo_full_name)
        
        # Check if already tracked
        existing_repo = await Repository.find_one(
            Repository.github_repo_id == repo.id
        )
        
        if existing_repo:
            raise HTTPException(status_code=400, detail="Repository already tracked")
        
        # Create repository record
        new_repo = Repository(
            user_id=str(current_user.id),
            github_repo_id=repo.id,
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            url=repo.html_url,
            default_branch=repo.default_branch,
            is_private=repo.private,
            is_active=True
        )
        
        await new_repo.insert()
        
        return {
            "message": "Repository tracked successfully",
            "repository": {
                "id": str(new_repo.id),
                "name": new_repo.name,
                "full_name": new_repo.full_name,
                "webhook_configured": new_repo.webhook_configured
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to track repository: {str(e)}")


@router.post("/{repo_id}/webhook")
async def setup_webhook(
    repo_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Set up GitHub webhook for a repository"""
    try:
        repository = await Repository.get(repo_id)
        if not repository or repository.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    github_client = GitHubClient(current_user.access_token)
    
    try:
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/webhooks/github"
        events = ["pull_request", "pull_request_review"]
        
        github_client.setup_webhook(repository.full_name, webhook_url, events)
        
        repository.webhook_configured = True
        await repository.save()
        
        return {
            "message": "Webhook configured successfully",
            "webhook_url": webhook_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to setup webhook: {str(e)}")


@router.delete("/{repo_id}")
async def untrack_repository(
    repo_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Stop tracking a repository"""
    try:
        repository = await Repository.get(repo_id)
        if not repository or repository.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    await repository.delete()
    
    return {"message": "Repository untracked successfully"}


@router.get("/{repo_id}/pull-requests")
async def get_repository_prs(
    repo_id: str,
    state: str = "open",
    current_user: User = Depends(get_current_user_from_token)
):
    """Get pull requests for a repository"""
    try:
        repository = await Repository.get(repo_id)
        if not repository or repository.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    github_client = GitHubClient(current_user.access_token)
    
    try:
        prs = github_client.get_pull_requests(repository.full_name, state)
        return {"pull_requests": prs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch PRs: {str(e)}")
