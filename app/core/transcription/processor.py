"""Audio preprocessing utilities."""
import ffmpeg
from pathlib import Path
from typing import Tuple, Optional
from app.core.logging import logger
from app.core.exceptions import ProcessingError


class AudioProcessor:
    """Handle audio preprocessing for Whisper."""
    
    @staticmethod
    def get_audio_info(file_path: Path) -> dict:
        """
        Get audio file information.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
            
        Raises:
            ProcessingError: If unable to read file
        """
        try:
            probe = ffmpeg.probe(str(file_path))
            
            # Find audio stream
            audio_stream = next(
                (stream for stream in probe['streams'] 
                 if stream['codec_type'] == 'audio'),
                None
            )
            
            if not audio_stream:
                raise ProcessingError("No audio stream found in file")
            
            duration = float(probe['format'].get('duration', 0))
            
            return {
                'duration': duration,
                'codec': audio_stream.get('codec_name'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bit_rate': int(audio_stream.get('bit_rate', 0))
            }
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg probe error: {e.stderr.decode() if e.stderr else str(e)}")
            raise ProcessingError(f"Failed to read audio file: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            raise ProcessingError(f"Failed to process audio file: {str(e)}")
    
    @staticmethod
    def convert_to_wav(input_path: Path, output_path: Path) -> Path:
        """
        Convert audio to WAV format for Whisper.
        Converts to mono, 16kHz as required by Whisper.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            
        Returns:
            Path to converted file
            
        Raises:
            ProcessingError: If conversion fails
        """
        try:
            logger.info(f"Converting {input_path} to WAV format")
            
            (
                ffmpeg
                .input(str(input_path))
                .output(
                    str(output_path),
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,                 # Mono
                    ar='16000'            # 16kHz sample rate
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            
            logger.info(f"Conversion successful: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg conversion error: {error_msg}")
            raise ProcessingError(f"Audio conversion failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected conversion error: {e}")
            raise ProcessingError(f"Audio conversion failed: {str(e)}")
    
    @staticmethod
    def extract_audio_from_video(video_path: Path, audio_path: Path) -> Path:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            audio_path: Path for extracted audio
            
        Returns:
            Path to extracted audio
            
        Raises:
            ProcessingError: If extraction fails
        """
        try:
            logger.info(f"Extracting audio from {video_path}")
            
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(audio_path),
                    acodec='pcm_s16le',
                    ac=1,
                    ar='16000',
                    vn=None  # No video
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
            
            logger.info(f"Audio extraction successful: {audio_path}")
            return audio_path
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg extraction error: {error_msg}")
            raise ProcessingError(f"Audio extraction failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected extraction error: {e}")
            raise ProcessingError(f"Audio extraction failed: {str(e)}")