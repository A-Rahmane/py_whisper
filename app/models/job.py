"""Job models for async processing."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    """Job creation request."""
    language: Optional[str] = None
    model: str = "base"
    response_format: str = "json"
    timestamp_granularity: str = "segment"
    temperature: float = 0.0


class JobInfo(BaseModel):
    """Job information."""
    job_id: str
    status: JobStatus
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error: Optional[str] = None
    detail: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: JobStatus
    progress: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None
    detail: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class JobSubmitResponse(BaseModel):
    """Job submission response."""
    job_id: str
    status: JobStatus
    message: str
    status_url: str
    estimated_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class JobListResponse(BaseModel):
    """List of jobs response."""
    jobs: list[JobInfo]
    total: int
    page: int
    page_size: int