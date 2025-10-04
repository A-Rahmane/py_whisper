"""Health check API routes."""
from fastapi import APIRouter
from datetime import datetime
import time
from app.config import settings
from app.models.responses import HealthResponse
from app.core.transcription.engine import whisper_engine


router = APIRouter(tags=["health"])

# Track service start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and status"
)
async def health_check():
    """Health check endpoint."""
    uptime = time.time() - _start_time
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        model=settings.whisper_model,
        device=settings.whisper_device,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime
    )


@router.get(
    "/health/live",
    summary="Liveness probe",
    description="Check if service is alive (for Kubernetes)"
)
async def liveness():
    """Liveness probe for container orchestration."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description="Check if service is ready to accept requests"
)
async def readiness():
    """Readiness probe for container orchestration."""
    checks = {
        "model_loaded": whisper_engine.model_manager.is_model_loaded(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type
        ),
        "temp_dir_writable": _check_temp_dir()
    }
    
    is_ready = all(checks.values())
    status_code = 200 if is_ready else 503
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks
    }, status_code


def _check_temp_dir() -> bool:
    """Check if temp directory is writable."""
    try:
        from pathlib import Path
        temp_path = Path(settings.temp_dir)
        return temp_path.exists() and temp_path.is_dir()
    except Exception:
        return False