"""Test input validation utilities."""

import pytest
from io import BytesIO
from fastapi import UploadFile
from app.utils.validators import (
    validate_file_extension,
    validate_mime_type,
    validate_file_size,
    validate_magic_bytes,
    validate_upload_file,
)
from app.core.exceptions import InvalidFileFormatError, FileTooLargeError


class TestFileExtensionValidation:
    """Test file extension validation."""
    
    def test_valid_audio_extensions(self):
        """Test valid audio file extensions."""
        valid_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
        for ext in valid_extensions:
            result = validate_file_extension(f"test{ext}")
            assert result == ext
    
    def test_valid_video_extensions(self):
        """Test valid video file extensions."""
        valid_extensions = ['.mp4', '.webm', '.avi', '.mov']
        for ext in valid_extensions:
            result = validate_file_extension(f"test{ext}")
            assert result == ext
    
    def test_case_insensitive(self):
        """Test extension validation is case-insensitive."""
        result = validate_file_extension("test.MP3")
        assert result == '.mp3'
    
    def test_invalid_extension(self):
        """Test invalid extension raises error."""
        with pytest.raises(InvalidFileFormatError):
            validate_file_extension("test.txt")
    
    def test_no_extension(self):
        """Test file without extension raises error."""
        with pytest.raises(InvalidFileFormatError):
            validate_file_extension("test")


class TestMimeTypeValidation:
    """Test MIME type validation."""
    
    def test_valid_audio_mime_types(self):
        """Test valid audio MIME types."""
        valid_types = ['audio/mpeg', 'audio/wav', 'audio/ogg']
        for mime_type in valid_types:
            validate_mime_type(mime_type)  # Should not raise
    
    def test_valid_video_mime_types(self):
        """Test valid video MIME types."""
        valid_types = ['video/mp4', 'video/webm', 'video/x-msvideo']
        for mime_type in valid_types:
            validate_mime_type(mime_type)  # Should not raise
    
    def test_invalid_mime_type(self):
        """Test invalid MIME type raises error."""
        with pytest.raises(InvalidFileFormatError):
            validate_mime_type('text/plain')


class TestFileSizeValidation:
    """Test file size validation."""
    
    def test_valid_file_size(self):
        """Test file within size limit."""
        validate_file_size(1024 * 1024)  # 1MB - should not raise
    
    def test_file_too_large(self):
        """Test file exceeding size limit raises error."""
        from app.config import settings
        with pytest.raises(FileTooLargeError):
            validate_file_size(settings.max_file_size + 1)


class TestMagicBytesValidation:
    """Test magic bytes validation."""
    
    def test_valid_mp3_magic_bytes(self):
        """Test valid MP3 magic bytes."""
        header = b'ID3\x03\x00\x00\x00'
        assert validate_magic_bytes(header, '.mp3') is True
    
    def test_valid_wav_magic_bytes(self):
        """Test valid WAV magic bytes."""
        header = b'RIFF\x00\x00\x00\x00WAVE'
        assert validate_magic_bytes(header, '.wav') is True
    
    def test_invalid_magic_bytes(self):
        """Test invalid magic bytes."""
        header = b'INVALID\x00\x00\x00'
        assert validate_magic_bytes(header, '.mp3') is False


@pytest.mark.asyncio
class TestUploadFileValidation:
    """Test complete upload file validation."""
    
    async def test_valid_upload(self, sample_audio_bytes):
        """Test valid file upload."""
        file = UploadFile(
            filename="test.wav",
            file=BytesIO(sample_audio_bytes)
        )
        file.content_type = "audio/wav"
        
        ext, size = await validate_upload_file(file)
        assert ext == '.wav'
        assert size > 0
    
    async def test_invalid_extension_upload(self):
        """Test upload with invalid extension."""
        file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"test content")
        )
        file.content_type = "text/plain"
        
        with pytest.raises(InvalidFileFormatError):
            await validate_upload_file(file)