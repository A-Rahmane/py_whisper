"""Job management service."""
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from app.config import settings
from app.core.logging import logger
from app.core.redis_client import redis_client
from app.models.job import (
    JobStatus,
    JobInfo,
    JobStatusResponse,
    JobSubmitResponse,
    JobListResponse
)
from app.core.exceptions import InvalidParameterError


class JobService:
    """Service for managing transcription jobs."""
    
    def __init__(self):
        """Initialize job service."""
        self.redis_client = redis_client
    
    def create_job(
        self,
        file_path: str,
        language: Optional[str] = None,
        model: str = "base",
        response_format: str = "json",
        timestamp_granularity: str = "segment",
        temperature: float = 0.0,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Create a new transcription job.
        
        Args:
            file_path: Path to the file
            language: Optional language code
            model: Whisper model size
            response_format: Output format
            timestamp_granularity: Timestamp level
            temperature: Sampling temperature
            metadata: Additional metadata
            
        Returns:
            Job ID
            
        Raises:
            InvalidParameterError: If parameters are invalid
        """
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Prepare job parameters
            params = {
                "language": language,
                "model": model,
                "response_format": response_format,
                "timestamp_granularity": timestamp_granularity,
                "temperature": temperature
            }
            
            # Create job in Redis
            success = self.redis_client.create_job(
                job_id=job_id,
                file_path=file_path,
                params=params,
                metadata=metadata
            )
            
            if not success:
                raise InvalidParameterError("Failed to create job")
            
            logger.info(f"Job created: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobStatusResponse if found, None otherwise
        """
        try:
            job_info = self.redis_client.get_job(job_id)
            
            if not job_info:
                return None
            
            # Calculate estimated completion time
            estimated_completion = None
            if job_info.status == JobStatus.PROCESSING and job_info.started_at:
                # Rough estimate: 1 minute of audio takes ~6 seconds on base model
                # This should be improved with actual metrics
                if job_info.metadata and 'duration' in job_info.metadata:
                    duration = job_info.metadata['duration']
                    processing_time_estimate = duration * 0.1  # 10% of audio duration
                    started_at = datetime.fromisoformat(job_info.started_at)
                    estimated_completion = started_at + timedelta(seconds=processing_time_estimate)
            
            return JobStatusResponse(
                job_id=job_info.job_id,
                status=job_info.status,
                progress=job_info.progress,
                created_at=job_info.created_at,
                started_at=job_info.started_at,
                completed_at=job_info.completed_at,
                failed_at=job_info.failed_at,
                estimated_completion=estimated_completion,
                error=job_info.error,
                detail=job_info.detail,
                result=job_info.result
            )
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> JobListResponse:
        """
        List jobs with pagination.
        
        Args:
            status: Filter by status
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            JobListResponse with paginated results
        """
        try:
            # Get all jobs (Redis limitation - not ideal for large scale)
            all_jobs = self.redis_client.list_jobs(status=status, limit=1000)
            
            # Sort by created_at descending
            all_jobs.sort(key=lambda x: x.created_at, reverse=True)
            
            # Paginate
            total = len(all_jobs)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            jobs_page = all_jobs[start_idx:end_idx]
            
            return JobListResponse(
                jobs=jobs_page,
                total=total,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return JobListResponse(jobs=[], total=0, page=page, page_size=page_size)
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or processing job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        try:
            job_info = self.redis_client.get_job(job_id)
            
            if not job_info:
                logger.warning(f"Job not found for cancellation: {job_id}")
                return False
            
            # Only cancel if pending or processing
            if job_info.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
                logger.warning(f"Cannot cancel job {job_id} with status {job_info.status}")
                return False
            
            # Revoke Celery task if it's processing
            if job_info.status == JobStatus.PROCESSING:
                from tasks.celery_app import celery_app
                celery_app.control.revoke(job_id, terminate=True)
            
            # Update job status
            self.redis_client.update_job(
                job_id=job_id,
                status=JobStatus.CANCELLED
            )
            
            logger.info(f"Job cancelled: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a completed or failed job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            # Get file path for cleanup
            file_path = self.redis_client.get_job_file_path(job_id)
            
            # Delete file if exists
            if file_path:
                from app.utils.file_handler import SecureFileHandler
                file_handler = SecureFileHandler()
                file_handler.cleanup_file(Path(file_path))
            
            # Delete job from Redis
            return self.redis_client.delete_job(job_id)
            
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def estimate_processing_time(self, duration: float, model: str) -> int:
        """
        Estimate processing time in seconds.
        
        Args:
            duration: Audio duration in seconds
            model: Model name
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimates based on CPU processing (adjust based on your hardware)
        multipliers = {
            "tiny": 0.05,
            "base": 0.1,
            "small": 0.2,
            "medium": 0.5,
            "large": 1.0,
            "large-v3": 1.0,
        }
        
        multiplier = multipliers.get(model, 0.1)
        
        # If using GPU, processing is faster
        if settings.whisper_device == "cuda":
            multiplier *= 0.3  # 70% faster on GPU
        
        return int(duration * multiplier)


# Global job service instance
job_service = JobService()