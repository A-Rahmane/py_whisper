"""Celery tasks for transcription processing."""
import time
from pathlib import Path
from typing import Dict, Any
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from tasks.celery_app import celery_app
from app.config import settings
from app.core.logging import logger
from app.core.redis_client import redis_client
from app.core.transcription.engine import whisper_engine
from app.core.transcription.processor import AudioProcessor
from app.core.transcription.formatter import OutputFormatter
from app.models.job import JobStatus
from app.models.requests import TimestampGranularity, ResponseFormat
from app.utils.file_handler import SecureFileHandler
from app.utils.validators import ALLOWED_VIDEO_EXTENSIONS
from app.core.exceptions import TranscriptionFailedError


class TranscriptionTask(Task):
    """Base task class for transcription with progress tracking."""
    
    def __init__(self):
        super().__init__()
        self.audio_processor = AudioProcessor()
        self.formatter = OutputFormatter()
        self.file_handler = SecureFileHandler()
    
    def update_progress(self, job_id: str, progress: int, status: JobStatus = None):
        """Update job progress in Redis."""
        try:
            redis_client.update_job(
                job_id=job_id,
                status=status or JobStatus.PROCESSING,
                progress=progress
            )
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}")


@celery_app.task(
    base=TranscriptionTask,
    bind=True,
    name='tasks.transcribe_file',
    max_retries=settings.max_job_retry,
    soft_time_limit=3600,  # 1 hour soft limit
    time_limit=3900,  # 65 minutes hard limit
)
def transcribe_file_task(
    self: TranscriptionTask,
    job_id: str,
    file_path: str,
    language: str = None,
    model: str = "base",
    response_format: str = ResponseFormat.JSON,
    timestamp_granularity: str = TimestampGranularity.SEGMENT,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Transcribe audio/video file asynchronously.
    
    Args:
        job_id: Unique job identifier
        file_path: Path to the file
        language: Optional language code
        model: Whisper model size
        response_format: Output format
        timestamp_granularity: Timestamp level
        temperature: Sampling temperature
        
    Returns:
        Transcription result
    """
    temp_files = []
    
    try:
        logger.info(f"Starting transcription job: {job_id}")
        
        # Update status to processing
        redis_client.update_job(
            job_id=job_id,
            status=JobStatus.PROCESSING,
            progress=0
        )
        
        input_path = Path(file_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        temp_files.append(input_path)
        
        # Step 1: Get audio info (5% progress)
        self.update_progress(job_id, 5)
        audio_info = self.audio_processor.get_audio_info(input_path)
        
        logger.info(
            f"Job {job_id}: Audio duration={audio_info['duration']:.2f}s, "
            f"codec={audio_info['codec']}"
        )
        
        # Step 2: Process video files if needed (15% progress)
        self.update_progress(job_id, 15)
        audio_path = input_path
        file_ext = input_path.suffix.lower()
        
        if file_ext in ALLOWED_VIDEO_EXTENSIONS:
            audio_path = input_path.with_suffix('.wav')
            self.audio_processor.extract_audio_from_video(input_path, audio_path)
            temp_files.append(audio_path)
        
        # Step 3: Convert to WAV if needed (25% progress)
        self.update_progress(job_id, 25)
        if file_ext != '.wav':
            wav_path = input_path.with_stem(input_path.stem + '_converted').with_suffix('.wav')
            self.audio_processor.convert_to_wav(audio_path, wav_path)
            temp_files.append(wav_path)
            audio_path = wav_path
        
        # Step 4: Transcribe (30-90% progress)
        self.update_progress(job_id, 30)
        word_timestamps = (timestamp_granularity == TimestampGranularity.WORD)
        
        logger.info(f"Job {job_id}: Starting Whisper transcription with model={model}")
        
        result = whisper_engine.transcribe(
            audio_path=audio_path,
            language=language,
            model_name=model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            temperature=temperature,
            word_timestamps=word_timestamps
        )
        
        # Step 5: Format output (95% progress)
        self.update_progress(job_id, 95)
        
        if response_format == ResponseFormat.TEXT:
            formatted_result = {"result": self.formatter.to_text(result)}
        elif response_format == ResponseFormat.SRT:
            formatted_result = {"result": self.formatter.to_srt(result)}
        elif response_format == ResponseFormat.VTT:
            formatted_result = {"result": self.formatter.to_vtt(result)}
        else:  # JSON
            formatted_result = result
        
        # Step 6: Complete (100% progress)
        redis_client.update_job(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            result=formatted_result
        )
        
        logger.info(
            f"Job {job_id} completed successfully in {result.get('processing_time', 0):.2f}s"
        )
        
        return formatted_result
        
    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} exceeded time limit")
        redis_client.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error="timeout",
            detail="Transcription exceeded time limit"
        )
        raise
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        
        # Update job as failed
        redis_client.update_job(
            job_id=job_id,
            status=JobStatus.FAILED,
            error="transcription_failed",
            detail=str(e)
        )
        
        # Retry if possible
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=settings.job_retry_delay)
        
        raise TranscriptionFailedError(f"Transcription failed: {str(e)}")
        
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                self.file_handler.cleanup_file(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_file}: {e}")


@celery_app.task(name='tasks.cleanup_job')
def cleanup_job_task(job_id: str):
    """
    Cleanup job data and files.
    
    Args:
        job_id: Job identifier
    """
    try:
        logger.info(f"Cleaning up job: {job_id}")
        
        # Get file path
        file_path = redis_client.get_job_file_path(job_id)
        
        # Delete file if exists
        if file_path:
            file_handler = SecureFileHandler()
            file_handler.cleanup_file(Path(file_path))
        
        # Delete job from Redis
        redis_client.delete_job(job_id)
        
        logger.info(f"Job cleanup completed: {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to cleanup job {job_id}: {e}")