"""
Reviews API Routes - MongoDB/Beanie
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import List
from beanie.operators import In
from beanie import PydanticObjectId

from app.models.user import User
from app.models.repository import Repository
from app.models.pull_request import PullRequest
from app.models.review import Review, ReviewStatus
from app.core.auth import verify_token
from app.tasks.review_tasks import process_pr_review

router = APIRouter()


async def get_current_user_from_token(request: Request) -> User:
    """Dependency to get current user from JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        print(f"❌ Auth header missing or invalid: {auth_header}")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
    except Exception as e:
        print(f"❌ Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await User.get(user_id)
    
    if not user:
        print(f"❌ User not found for ID: {user_id}")
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/repository/{repo_id}/pr/{pr_number}")
async def trigger_review(
    repo_id: str,
    pr_number: int,
    current_user: User = Depends(get_current_user_from_token)
):
    """Manually trigger a review for a pull request"""
    
    # Verify repository belongs to user
    try:
        repository = await Repository.get(repo_id)
        if not repository or repository.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Process review synchronously so user sees loader
    try:
        await process_pr_review(
            repository_id=repo_id,
            pr_number=pr_number,
            user_id=str(current_user.id)
        )
        
        # Get the created review
        pr = await PullRequest.find_one(
            PullRequest.repository_id == repo_id,
            PullRequest.pr_number == pr_number
        )
        
        if pr:
            review = await Review.find_one(
                Review.pull_request_id == str(pr.id)
            )
            
            if review:
                return {
                    "message": "Review completed successfully",
                    "review_id": str(review.id),
                    "status": review.status.value
                }
        
        return {
            "message": "Review completed",
            "repository": repository.full_name,
            "pr_number": pr_number,
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


@router.get("/repository/{repo_id}")
async def list_repository_reviews(
    repo_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all reviews for a repository"""
    
    # Verify repository belongs to user
    try:
        repository = await Repository.get(repo_id)
        if not repository or repository.user_id != str(current_user.id):
            raise HTTPException(status_code=404, detail="Repository not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get all pull requests for this repository
    pull_requests = await PullRequest.find(
        PullRequest.repository_id == repo_id
    ).to_list()
    
    pr_ids = [str(pr.id) for pr in pull_requests]
    
    # Get all reviews for these PRs
    if pr_ids:
        reviews = await Review.find(
            In(Review.pull_request_id, pr_ids)
        ).sort(-Review.created_at).to_list()
    else:
        reviews = []
    
    # Create PR lookup for efficiency
    pr_lookup = {str(pr.id): pr for pr in pull_requests}
    
    return {
        "reviews": [
            {
                "id": str(review.id),
                "pr_number": pr_lookup[review.pull_request_id].pr_number,
                "pr_title": pr_lookup[review.pull_request_id].title,
                "status": review.status.value,
                "severity": review.severity.value if review.severity else None,
                "created_at": review.created_at.isoformat(),
                "completed_at": review.completed_at.isoformat() if review.completed_at else None,
                "execution_time": review.execution_time_seconds
            }
            for review in reviews if review.pull_request_id in pr_lookup
        ]
    }


@router.get("/{review_id}")
async def get_review_details(
    review_id: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get detailed review results"""
    
    try:
        review_obj_id = PydanticObjectId(review_id)
    except:
        raise HTTPException(status_code=404, detail="Invalid review ID")
    
    review = await Review.find_one(
        Review.id == review_obj_id,
        Review.user_id == str(current_user.id)
    )
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Get associated PR
    try:
        pr_obj_id = PydanticObjectId(review.pull_request_id)
        pull_request = await PullRequest.get(pr_obj_id)
    except:
        pull_request = None
    
    return {
        "id": str(review.id),
        "status": review.status.value,
        "severity": review.severity.value if review.severity else None,
        "pr_number": pull_request.pr_number if pull_request else None,
        "pr_title": pull_request.title if pull_request else None,
        "pr_url": pull_request.github_url if pull_request else None,
        "logic_analysis": review.logic_analysis,
        "readability_analysis": review.readability_analysis,
        "performance_analysis": review.performance_analysis,
        "security_analysis": review.security_analysis,
        "overall_summary": review.overall_summary,
        "recommendations": review.recommendations,
        "created_at": review.created_at.isoformat(),
        "completed_at": review.completed_at.isoformat() if review.completed_at else None,
        "execution_time": review.execution_time_seconds,
        "error_message": review.error_message
    }


@router.get("/")
async def list_all_reviews(
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all reviews for the current user"""
    
    reviews = await Review.find(
        Review.user_id == str(current_user.id)
    ).sort(-Review.created_at).to_list()
    
    # Get all related PRs and repositories
    pr_ids = [review.pull_request_id for review in reviews]
    if pr_ids:
        # Convert string IDs to PydanticObjectId for querying by _id
        pr_obj_ids = []
        for pid in pr_ids:
            try:
                pr_obj_ids.append(PydanticObjectId(pid))
            except:
                pass
                
        pull_requests = await PullRequest.find(
            In(PullRequest.id, pr_obj_ids)
        ).to_list()
    else:
        pull_requests = []
    
    pr_lookup = {str(pr.id): pr for pr in pull_requests}
    
    # Get repositories
    repo_ids = [pr.repository_id for pr in pull_requests]
    if repo_ids:
        # Convert string IDs to PydanticObjectId for querying by _id
        repo_obj_ids = []
        for rid in repo_ids:
            try:
                repo_obj_ids.append(PydanticObjectId(rid))
            except:
                pass
                
        repositories = await Repository.find(
            In(Repository.id, repo_obj_ids)
        ).to_list()
    else:
        repositories = []
    
    repo_lookup = {str(repo.id): repo for repo in repositories}
    
    return {
        "reviews": [
            {
                "id": str(review.id),
                "repository_name": repo_lookup[pr_lookup[review.pull_request_id].repository_id].full_name if review.pull_request_id in pr_lookup and pr_lookup[review.pull_request_id].repository_id in repo_lookup else "Unknown",
                "pr_number": pr_lookup[review.pull_request_id].pr_number if review.pull_request_id in pr_lookup else None,
                "pr_title": pr_lookup[review.pull_request_id].title if review.pull_request_id in pr_lookup else None,
                "status": review.status.value,
                "severity": review.severity.value if review.severity else None,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ]
    }
