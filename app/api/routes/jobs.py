"""Job management API routes."""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime

from app.core.logging import logger
from app.models.job import JobStatus, JobStatusResponse, JobListResponse
from app.services.job_service import job_service
from app.api.dependencies import check_rate_limit


router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of an asynchronous transcription job",
    responses={
        200: {"description": "Job status retrieved successfully"},
        404: {"description": "Job not found"}
    }
)
async def get_job_status(job_id: str):
    """Get job status endpoint."""
    try:
        status = job_service.get_job_status(job_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "job_not_found",
                    "message": f"Job {job_id} not found",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to retrieve job status",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get(
    "/jobs",
    response_model=JobListResponse,
    summary="List jobs",
    description="List transcription jobs with optional filtering",
    dependencies=[Depends(check_rate_limit)]
)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """List jobs endpoint."""
    try:
        return job_service.list_jobs(
            status=status,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to list jobs",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.delete(
    "/jobs/{job_id}",
    summary="Delete job",
    description="Delete a completed or failed job",
    dependencies=[Depends(check_rate_limit)]
)
async def delete_job(job_id: str):
    """Delete job endpoint."""
    try:
        success = job_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "job_not_found",
                    "message": f"Job {job_id} not found or cannot be deleted",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        return {
            "message": "Job deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to delete job",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.post(
    "/jobs/{job_id}/cancel",
    summary="Cancel job",
    description="Cancel a pending or processing job",
    dependencies=[Depends(check_rate_limit)]
)
async def cancel_job(job_id: str):
    """Cancel job endpoint."""
    try:
        success = job_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "cannot_cancel",
                    "message": f"Job {job_id} cannot be cancelled",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        return {
            "message": "Job cancelled successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to cancel job",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )