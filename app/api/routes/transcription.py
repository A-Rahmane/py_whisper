"""Transcription API routes."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.core.logging import logger
from app.core.exceptions import (
    InvalidFileFormatError,
    FileTooLargeError,
    InvalidParameterError,
    TranscriptionFailedError
)
from app.models.requests import ModelSize, ResponseFormat, TimestampGranularity
from app.models.responses import TranscriptionResponse, ErrorResponse
from app.services.transcription_service import transcription_service
from datetime import datetime


router = APIRouter(prefix="/api/v1", tags=["transcription"])


@router.post(
    "/transcribe",
    summary="Transcribe audio/video file",
    description="""
    Upload an audio or video file to transcribe its content to text.
    
    **Supported formats:**
    - Audio: MP3, WAV, OGG, FLAC, M4A, AAC, WMA
    - Video: MP4, WebM, AVI, MOV, MKV, FLV
    
    **Limits:**
    - Maximum file size: 1GB
    - Maximum duration: 3 hours
    """,
    responses={
        200: {"model": TranscriptionResponse},
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def transcribe(
    file: UploadFile = File(..., description="Audio/video file to transcribe"),
    language: Optional[str] = Form(None, description="ISO 639-1 language code (e.g., 'en', 'es')"),
    model: str = Form(ModelSize.BASE, description="Model size: tiny, base, small, medium, large, large-v3"),
    response_format: str = Form(ResponseFormat.JSON, description="Output format: json, text, srt, vtt"),
    timestamp_granularity: str = Form(TimestampGranularity.SEGMENT, description="Timestamp level: word, segment"),
    temperature: float = Form(0.0, ge=0.0, le=1.0, description="Sampling temperature (0.0-1.0)")
):
    """Transcribe audio/video file endpoint."""
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