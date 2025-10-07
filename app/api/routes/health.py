"""Health check API routes."""
from fastapi import APIRouter, Response, status
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from datetime import datetime
import time
from app.config import settings
from app.models.responses import HealthResponse
from app.core.transcription.engine import whisper_engine
from app.core.redis_client import redis_client


router = APIRouter(tags=["health"])

# Track service start time
_start_time = time.time()


@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check service health and status"
)
async def health_check():
    """Global service health report."""
    uptime = time.time() - _start_time

    checks = {
        "model_loaded": whisper_engine.model_manager.is_model_loaded(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type
        ),
        "temp_dir_writable": _check_temp_dir(),
        "redis_connected": _check_redis() if settings.enable_async else None,
        "celery_workers": _check_celery_workers() if settings.enable_async else None,
    }

    # Health classification
    if all(v is True or v is None for v in checks.values()):
        service_status = "healthy"
    elif checks.get("redis_connected") is False or checks.get("celery_workers") is False:
        service_status = "degraded"  # partial feature loss
    else:
        service_status = "unhealthy"
    
    return HealthResponse(
        status=service_status,
        version=settings.app_version,
        model=settings.whisper_model,
        device=settings.whisper_device,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        checks=checks
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
async def readiness(response: Response):
    """Readiness probe for container orchestration."""
    checks = {
        "model_loaded": whisper_engine.model_manager.is_model_loaded(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type
        ),
        "temp_dir_writable": _check_temp_dir(),
        "redis_connected": _check_redis() if settings.enable_async else True,
    }
    
    is_ready = all(checks.values())
    response.status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks
    }


@router.get(
    "/health/async",
    summary="Async infrastructure health",
    description="Check async processing infrastructure health"
)
async def async_health(response: Response):
    """Check async infrastructure health."""
    if not settings.enable_async:
        response.status_code = status.HTTP_200_OK
        return {
            "status": "disabled",
            "message": "Async processing is not enabled"
        }
    
    checks = {
        "redis_connected": _check_redis(),
        "celery_workers": _check_celery_workers()
    }
    
    is_healthy = all(checks.values())
    response.status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "checks": checks
    }


# --- Dependency checks ---

def _check_temp_dir() -> bool:
    """Check if temp directory is writable."""
    try:
        from pathlib import Path
        temp_path = Path(settings.temp_dir)
        return temp_path.exists() and temp_path.is_dir()
    except Exception:
        return False


def _check_redis() -> bool:
    """Check Redis connection."""
    try:
        # Prefer cached 'available' flag over active ping for quick response
        if redis_client.available:
            return True
        return redis_client.is_connected()
    except:
        return False


def _check_celery_workers() -> bool:
    """Check if Celery workers are available."""
    try:
        from tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        workers = inspect.active()
        return bool(workers) # same as:  workers is not None and len(workers) > 0
    except:
        return False