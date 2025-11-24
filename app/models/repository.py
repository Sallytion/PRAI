"""
Repository Model - MongoDB/Beanie Document
"""
from beanie import Document, Link
from pydantic import Field
from datetime import datetime
from typing import Optional
from bson import ObjectId


class Repository(Document):
    user_id: str  # Reference to User document ID
    github_repo_id: int = Field(..., unique=True)
    name: str
    full_name: str = Field(..., unique=True)
    description: Optional[str] = None
    url: str
    default_branch: str = "main"
    is_private: bool = False
    webhook_configured: bool = False
    webhook_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "repositories"
        indexes = [
            "user_id",
            "github_repo_id",
            "full_name"
        ]
