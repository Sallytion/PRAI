"""
Background Review Task Handler (using FastAPI BackgroundTasks)
"""
import time
from datetime import datetime

from app.config import get_settings
from app.models.repository import Repository
from app.models.user import User
from app.models.pull_request import PullRequest
from app.models.review import Review, ReviewStatus
from app.core.github_client import GitHubClient
from app.core.review_generator import ReviewGenerator

settings = get_settings()


async def process_pr_review(repository_id: str, pr_number: int, user_id: str):
    """
    Background task to process PR review with multi-agent system.
    
    Args:
        repository_id: MongoDB ObjectId of the repository
        pr_number: Pull request number
        user_id: MongoDB ObjectId of the user
    """
    start_time = time.time()
    
    try:
        # Get repository and user
        repository = await Repository.get(repository_id)
        user = await User.get(user_id)
        
        if not repository or not user:
            print(f"❌ Repository or user not found")
            return
        
        # Get or create PR record
        pr = await PullRequest.find_one(
            PullRequest.repository_id == repository_id,
            PullRequest.pr_number == pr_number
        )
        
        if not pr:
            # Fetch PR data from GitHub
            github_client = GitHubClient(user.access_token)
            pr_data = github_client.get_pull_request(repository.full_name, pr_number)
            
            if not pr_data:
                print(f"❌ PR #{pr_number} not found on GitHub")
                return
            
            pr = PullRequest(
                repository_id=str(repository.id),
                pr_number=pr_number,
                title=pr_data['title'],
                author=pr_data['author'],
                github_url=pr_data['url'],
                additions=pr_data.get('additions', 0),
                deletions=pr_data.get('deletions', 0),
                changed_files=pr_data.get('changed_files', 0)
            )
            await pr.insert()
        
        # Create review record
        review = Review(
            user_id=str(user.id),
            pull_request_id=str(pr.id),
            status=ReviewStatus.IN_PROGRESS
        )
        await review.insert()
        
        # Generate review using multi-agent system
        github_client = GitHubClient(user.access_token)
        files_data = github_client.get_pr_files(repository.full_name, pr_number)
        
        pr_data = {
            'title': pr.title,
            'number': pr.pr_number,
            'author': pr.author,
            'description': pr.description or '',
            'additions': pr.additions,
            'deletions': pr.deletions,
            'changed_files': pr.changed_files
        }
        
        review_generator = ReviewGenerator()
        review_results = review_generator.generate_review(pr_data, files_data)
        
        # Update review with results
        review.status = ReviewStatus.COMPLETED
        review.logic_analysis = review_results.get('logic_analysis')
        review.readability_analysis = review_results.get('readability_analysis')
        review.performance_analysis = review_results.get('performance_analysis')
        review.security_analysis = review_results.get('security_analysis')
        review.overall_summary = review_results.get('overall_summary')
        review.severity = review_results.get('severity')
        review.recommendations = review_results.get('recommendations')
        review.execution_time_seconds = int(time.time() - start_time)
        review.completed_at = datetime.utcnow()
        
        await review.save()
        
        # Post comment to GitHub
        try:
            comment_body = review_generator.format_review_comment(review_results)
            comment = github_client.post_pr_comment(
                repository.full_name,
                pr_number,
                comment_body
            )
            review.github_comment_id = comment.id
            await review.save()
        except Exception as e:
            print(f"⚠️ Failed to post comment to GitHub: {str(e)}")
        
        print(f"✅ Review completed for PR #{pr_number} in {repository.full_name}")
        
    except Exception as e:
        print(f"❌ Error processing review: {str(e)}")
        
        # Update review as failed
        if 'review' in locals():
            review.status = ReviewStatus.FAILED
            review.error_message = str(e)
            review.execution_time_seconds = int(time.time() - start_time)
            await review.save()
