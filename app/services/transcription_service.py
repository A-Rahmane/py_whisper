"""Transcription service orchestration."""
import time
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import UploadFile
from app.config import settings
from app.core.logging import logger
from app.core.exceptions import InvalidParameterError, TranscriptionFailedError
from app.core.transcription.engine import whisper_engine
from app.core.transcription.processor import AudioProcessor
from app.core.transcription.formatter import OutputFormatter
from app.utils.file_handler import SecureFileHandler
from app.utils.validators import validate_upload_file, ALLOWED_VIDEO_EXTENSIONS
from app.models.requests import TimestampGranularity, ResponseFormat


class TranscriptionService:
    """Main transcription service."""
    
    def __init__(self):
        """Initialize service."""
        self.file_handler = SecureFileHandler()
        self.audio_processor = AudioProcessor()
        self.formatter = OutputFormatter()
    
    async def transcribe_file(
        self,
        file: UploadFile,
        language: Optional[str] = None,
        model: str = "base",
        response_format: str = ResponseFormat.JSON,
        timestamp_granularity: str = TimestampGranularity.SEGMENT,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """
        Transcribe uploaded file.
        
        Args:
            file: Uploaded audio/video file
            language: Optional language code
            model: Whisper model size
            response_format: Output format
            timestamp_granularity: Timestamp level
            temperature: Sampling temperature
            
        Returns:
            Transcription result (format depends on response_format)
            
        Raises:
            InvalidParameterError: If parameters are invalid
            TranscriptionFailedError: If transcription fails
        """
        temp_files = []
        
        try:
            # Validate file
            file_ext, file_size = await validate_upload_file(file)
            logger.info(f"Processing file: {file.filename} ({file_size} bytes)")
            
            # Save uploaded file
            input_path = await self.file_handler.save_upload(file)
            temp_files.append(input_path)
            
            # Get audio info and validate duration
            audio_info = self.audio_processor.get_audio_info(input_path)
            
            if audio_info['duration'] > settings.max_duration:
                raise InvalidParameterError(
                    f"Audio duration {audio_info['duration']:.1f}s exceeds "
                    f"maximum {settings.max_duration}s"
                )
            
            logger.info(
                f"Audio info: duration={audio_info['duration']:.2f}s, "
                f"codec={audio_info['codec']}, sr={audio_info['sample_rate']}"
            )
            
            # Process video files - extract audio
            audio_path = input_path
            if file_ext in ALLOWED_VIDEO_EXTENSIONS:
                audio_path = input_path.with_suffix('.wav')
                self.audio_processor.extract_audio_from_video(input_path, audio_path)
                temp_files.append(audio_path)
            
            # Convert to WAV if needed
            if file_ext != '.wav':
                wav_path = input_path.with_stem(input_path.stem + '_converted').with_suffix('.wav')
                self.audio_processor.convert_to_wav(audio_path, wav_path)
                temp_files.append(wav_path)
                audio_path = wav_path
            
            # Transcribe
            word_timestamps = (timestamp_granularity == TimestampGranularity.WORD)
            
            result = whisper_engine.transcribe(
                audio_path=audio_path,
                language=language,
                model_name=model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                temperature=temperature,
                word_timestamps=word_timestamps
            )
            
            # Format output
            if response_format == ResponseFormat.TEXT:
                return {"result": self.formatter.to_text(result)}
            elif response_format == ResponseFormat.SRT:
                return {"result": self.formatter.to_srt(result)}
            elif response_format == ResponseFormat.VTT:
                return {"result": self.formatter.to_vtt(result)}
            else:  # JSON
                return result
            
        except (InvalidParameterError, TranscriptionFailedError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise TranscriptionFailedError(f"Transcription failed: {str(e)}")
        
        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                self.file_handler.cleanup_file(temp_file)


# Global service instance
transcription_service = TranscriptionService()