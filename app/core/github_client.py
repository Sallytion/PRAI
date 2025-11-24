"""
GitHub API Client Wrapper
"""
from github import Github, GithubIntegration
from typing import Optional, List, Dict
from app.config import get_settings

settings = get_settings()


class GitHubClient:
    """GitHub API client for interacting with repositories and PRs"""
    
    def __init__(self, access_token: str):
        self.client = Github(access_token)
        self.access_token = access_token
    
    def get_user(self):
        """Get authenticated user"""
        return self.client.get_user()
    
    def get_user_repos(self) -> List[Dict]:
        """Get user's repositories"""
        user = self.client.get_user()
        repos = []
        for repo in user.get_repos():
            repos.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "url": repo.html_url,
                "default_branch": repo.default_branch,
            })
        return repos
    
    def get_repository(self, repo_full_name: str):
        """Get a specific repository"""
        return self.client.get_repo(repo_full_name)
    
    def get_pull_requests(self, repo_full_name: str, state: str = "open") -> List[Dict]:
        """Get pull requests for a repository"""
        repo = self.get_repository(repo_full_name)
        prs = []
        for pr in repo.get_pulls(state=state):
            prs.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "url": pr.html_url,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
            })
        return prs
    
    def get_pull_request(self, repo_full_name: str, pr_number: int) -> Dict:
        """Get a specific pull request"""
        repo = self.get_repository(repo_full_name)
        pr = repo.get_pull(pr_number)
        return {
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "author": pr.user.login,
            "url": pr.html_url,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "body": pr.body or "",
        }
    
    def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str:
        """Get the diff for a pull request"""
        repo = self.get_repository(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        # Get all files changed in the PR
        files = pr.get_files()
        diff_content = []
        
        for file in files:
            diff_content.append(f"File: {file.filename}")
            diff_content.append(f"Status: {file.status}")
            diff_content.append(f"Additions: {file.additions}, Deletions: {file.deletions}")
            if file.patch:
                diff_content.append("\n" + file.patch)
            diff_content.append("\n" + "="*80 + "\n")
        
        return "\n".join(diff_content)
    
    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[Dict]:
        """Get detailed file changes for a PR"""
        repo = self.get_repository(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        files_data = []
        for file in pr.get_files():
            files_data.append({
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "patch": file.patch,
                "raw_url": file.raw_url,
                "blob_url": file.blob_url,
            })
        
        return files_data
    
    def create_pr_comment(self, repo_full_name: str, pr_number: int, body: str):
        """Create a comment on a pull request"""
        repo = self.get_repository(repo_full_name)
        pr = repo.get_pull(pr_number)
        return pr.create_issue_comment(body)
    
    def post_pr_comment(self, repo_full_name: str, pr_number: int, body: str):
        """Alias for create_pr_comment"""
        return self.create_pr_comment(repo_full_name, pr_number, body)
    
    def create_pr_review(
        self, 
        repo_full_name: str, 
        pr_number: int, 
        body: str, 
        event: str = "COMMENT",
        comments: Optional[List[Dict]] = None
    ):
        """
        Create a review on a pull request
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            pr_number: PR number
            body: Review body
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
            comments: List of line-specific comments
        """
        repo = self.get_repository(repo_full_name)
        pr = repo.get_pull(pr_number)
        
        if comments:
            # Create review with line comments
            pr.create_review(
                body=body,
                event=event,
                comments=comments
            )
        else:
            # Create simple review
            pr.create_review(body=body, event=event)
    
    def setup_webhook(self, repo_full_name: str, webhook_url: str, events: List[str]):
        """Set up webhook for a repository"""
        repo = self.get_repository(repo_full_name)
        
        config = {
            "url": webhook_url,
            "content_type": "json",
            "secret": settings.GITHUB_WEBHOOK_SECRET,
        }
        
        repo.create_hook(
            name="web",
            config=config,
            events=events,
            active=True
        )
