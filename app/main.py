"""FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime

from app.config import settings
from app.core.logging import logger, setup_logging
from app.api.routes import transcription, health, models
from app.core.transcription.engine import whisper_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Configuration: model={settings.whisper_model}, device={settings.whisper_device}")
    
    # Preload default model
    try:
        logger.info("Preloading Whisper model...")
        whisper_engine.model_manager.preload_model(
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type
        )
        logger.info("Model preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload model: {e}")
        logger.warning("Service will load model on first request")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Whisper-based audio/video transcription microservice",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Generate request ID
    request_id = f"{int(start_time * 1000)}-{id(request)}"
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "metadata": {
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        }
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "metadata": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            }
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "request_id": request_id,
                "metadata": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2)
                }
            },
            exc_info=True
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(transcription.router)
app.include_router(models.router)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if not settings.debug else 1,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )