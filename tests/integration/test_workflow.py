"""Test complete transcription workflow."""

import pytest
from pathlib import Path
from io import BytesIO
from app.utils.file_handler import SecureFileHandler
from app.utils.validators import validate_upload_file
from app.core.transcription.processor import AudioProcessor
from app.core.transcription.formatter import OutputFormatter
from fastapi import UploadFile


class TestTranscriptionWorkflow:
    """Test end-to-end transcription workflow."""
    
    @pytest.mark.asyncio
    async def test_file_upload_and_cleanup(self, temp_dir, sample_audio_bytes):
        """Test file upload and cleanup workflow."""
        handler = SecureFileHandler(str(temp_dir))
        
        # Create upload file
        file = UploadFile(
            filename="test.wav",
            file=BytesIO(sample_audio_bytes)
        )
        file.content_type = "audio/wav"
        
        # Validate
        ext, size = await validate_upload_file(file)
        assert ext == '.wav'
        
        # Save
        saved_path = await handler.save_upload(file)
        assert saved_path.exists()
        
        # Cleanup
        handler.cleanup_file(saved_path)
        assert not saved_path.exists()
    
    def test_audio_info_extraction(self, sample_audio_path):
        """Test audio information extraction."""
        processor = AudioProcessor()
        
        info = processor.get_audio_info(sample_audio_path)
        
        assert "duration" in info
        assert "codec" in info
        assert "sample_rate" in info
        assert info["duration"] > 0
    
    def test_output_format_conversion(self):
        """Test converting between output formats."""
        formatter = OutputFormatter()
        
        sample_result = {
            "text": "Test transcription.",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Test transcription.",
                    "confidence": 0.9
                }
            ]
        }
        
        # Test all formats
        text = formatter.to_text(sample_result)
        assert isinstance(text, str)
        assert text == "Test transcription."
        
        srt = formatter.to_srt(sample_result)
        assert "1\n" in srt
        assert "Test transcription." in srt
        
        vtt = formatter.to_vtt(sample_result)
        assert vtt.startswith("WEBVTT")
        assert "Test transcription." in vtt