"""
Review Model - MongoDB/Beanie Document
"""
from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any, List


class ReviewStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewSeverity(str, PyEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Review(Document):
    user_id: str  # Reference to User document ID
    pull_request_id: str  # Reference to PullRequest document ID
    status: ReviewStatus = ReviewStatus.PENDING
    
    # Agent-specific results
    logic_analysis: Optional[Dict[str, Any]] = None
    readability_analysis: Optional[Dict[str, Any]] = None
    performance_analysis: Optional[Dict[str, Any]] = None
    security_analysis: Optional[Dict[str, Any]] = None
    
    # Aggregated results
    overall_summary: Optional[str] = None
    severity: Optional[ReviewSeverity] = None
    recommendations: Optional[List[str]] = None
    
    # Metadata
    execution_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    github_comment_id: Optional[int] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Settings:
        name = "reviews"
        indexes = [
            "user_id",
            "pull_request_id",
            "status",
            "created_at"
        ]
