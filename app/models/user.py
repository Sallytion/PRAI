"""
User Model - MongoDB/Beanie Document
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional


class User(Document):
    github_id: int = Field(..., unique=True)
    username: str = Field(..., unique=True)
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            "github_id",
            "username",
            "email"
        ]
