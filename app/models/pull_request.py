"""
Pull Request Model - MongoDB/Beanie Document
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional


class PRStatus(str, PyEnum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PullRequest(Document):
    repository_id: str  # Reference to Repository document ID
    pr_number: int
    title: str
    description: Optional[str] = None
    author: str
    status: PRStatus = PRStatus.OPEN
    github_url: str
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "pull_requests"
        indexes = [
            "repository_id",
            "pr_number",
            "status"
        ]
