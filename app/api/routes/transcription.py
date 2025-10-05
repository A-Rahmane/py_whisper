"""Transcription API routes."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime

from app.config import settings
from app.core.logging import logger
from app.core.redis_client import redis_client
from app.core.exceptions import (
    InvalidFileFormatError,
    FileTooLargeError,
    InvalidParameterError,
    TranscriptionFailedError
)
from app.models.requests import ModelSize, ResponseFormat, TimestampGranularity
from app.models.responses import TranscriptionResponse, ErrorResponse
from app.models.job import JobSubmitResponse, JobStatus
from app.services.transcription_service import transcription_service
from app.services.job_service import job_service
from app.api.dependencies import check_rate_limit
from app.utils.validators import validate_upload_file
from app.utils.file_handler import SecureFileHandler


router = APIRouter(prefix="/api/v1", tags=["transcription"])


@router.post(
    "/transcribe",
    summary="Transcribe audio/video file (synchronous)",
    description="""
    Upload an audio or video file to transcribe its content to text synchronously.
    
    **Supported formats:**
    - Audio: MP3, WAV, OGG, FLAC, M4A, AAC, WMA
    - Video: MP4, WebM, AVI, MOV, MKV, FLV
    
    **Limits:**
    - Maximum file size: 1GB
    - Maximum duration: one hour
    
    **Note:** For files longer than 10 minutes, consider using the async endpoint.
    """,
    responses={
        200: {"model": TranscriptionResponse},
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    dependencies=[Depends(check_rate_limit)]
)
async def transcribe(
    file: UploadFile = File(..., description="Audio/video file to transcribe"),
    language: Optional[str] = Form(None, description="ISO 639-1 language code (e.g., 'en', 'es')"),
    model: str = Form(ModelSize.BASE, description="Model size: tiny, base, small, medium, large, large-v3"),
    response_format: str = Form(ResponseFormat.JSON, description="Output format: json, text, srt, vtt"),
    timestamp_granularity: str = Form(TimestampGranularity.SEGMENT, description="Timestamp level: word, segment"),
    temperature: float = Form(0.0, ge=0.0, le=1.0, description="Sampling temperature (0.0-1.0)")
):
    """Transcribe audio/video file endpoint (synchronous)."""
    try:
        result = await transcription_service.transcribe_file(
            file=file,
            language=language,
            model=model,
            response_format=response_format,
            timestamp_granularity=timestamp_granularity,
            temperature=temperature
        )
        
        # Return based on format
        if response_format in [ResponseFormat.TEXT, ResponseFormat.SRT, ResponseFormat.VTT]:
            return JSONResponse(content=result)
        else:
            return result
        
    except InvalidFileFormatError as e:
        logger.warning(f"Invalid file format: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_format",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except FileTooLargeError as e:
        logger.warning(f"File too large: {e}")
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except InvalidParameterError as e:
        logger.warning(f"Invalid parameter: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_parameter",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except TranscriptionFailedError as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "transcription_failed",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.post(
    "/transcribe-async",
    response_model=JobSubmitResponse,
    summary="Transcribe audio/video file (asynchronous)",
    description="""
    Upload an audio or video file to transcribe asynchronously.
    
    This endpoint immediately returns a job ID and processes the file in the background.
    Use the `/status/{job_id}` endpoint to check progress and retrieve results.
    
    **Supported formats:**
    - Audio: MP3, WAV, OGG, FLAC, M4A, AAC, WMA
    - Video: MP4, WebM, AVI, MOV, MKV, FLV
    
    **Limits:**
    - Maximum file size: 1GB
    - Maximum duration: one hour
    
    **Recommended for:**
    - Files longer than 10 minutes
    - Batch processing
    - Large files
    """,
    responses={
        202: {"model": JobSubmitResponse},
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    },
    dependencies=[Depends(check_rate_limit)]
)
async def transcribe_async(
    file: UploadFile = File(..., description="Audio/video file to transcribe"),
    language: Optional[str] = Form(None, description="ISO 639-1 language code (e.g., 'en', 'es')"),
    model: str = Form(ModelSize.BASE, description="Model size: tiny, base, small, medium, large, large-v3"),
    response_format: str = Form(ResponseFormat.JSON, description="Output format: json, text, srt, vtt"),
    timestamp_granularity: str = Form(TimestampGranularity.SEGMENT, description="Timestamp level: word, segment"),
    temperature: float = Form(0.0, ge=0.0, le=1.0, description="Sampling temperature (0.0-1.0)")
):
    """Transcribe audio/video file endpoint (asynchronous)."""
    try:
        # Check if async is enabled
        if not settings.enable_async:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "service_unavailable",
                    "message": "Asynchronous processing is not enabled",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # Check Redis connection
        if not redis_client.is_connected():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "service_unavailable",
                    "message": "Job queue is not available",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            )
        
        # Validate file
        file_ext, file_size = await validate_upload_file(file)
        logger.info(f"Processing async request: {file.filename} ({file_size} bytes)")
        
        # Save uploaded file
        file_handler = SecureFileHandler()
        input_path = await file_handler.save_upload(file)
        
        # Get audio duration for estimation
        from app.core.transcription.processor import AudioProcessor
        audio_processor = AudioProcessor()
        audio_info = audio_processor.get_audio_info(input_path)
        
        # Create job
        job_id = job_service.create_job(
            file_path=str(input_path),
            language=language,
            model=model,
            response_format=response_format,
            timestamp_granularity=timestamp_granularity,
            temperature=temperature,
            metadata={
                "filename": file.filename,
                "file_size": file_size,
                "duration": audio_info['duration']
            }
        )
        
        # Submit to Celery
        from tasks.transcription_tasks import transcribe_file_task
        
        transcribe_file_task.apply_async(
            args=[
                job_id,
                str(input_path),
                language,
                model,
                response_format,
                timestamp_granularity,
                temperature
            ],
            task_id=job_id,  # Use job_id as task_id for tracking
            countdown=0
        )
        
        # Estimate processing time
        estimated_time = job_service.estimate_processing_time(
            duration=audio_info['duration'],
            model=model
        )
        
        logger.info(f"Job submitted: {job_id}")
        
        return JobSubmitResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Transcription job accepted and queued for processing",
            status_url=f"/api/v1/status/{job_id}",
            estimated_time=estimated_time
        )
        
    except InvalidFileFormatError as e:
        logger.warning(f"Invalid file format: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_format",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except FileTooLargeError as e:
        logger.warning(f"File too large: {e}")
        raise HTTPException(
            status_code=413,
            detail={
                "error": "file_too_large",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )