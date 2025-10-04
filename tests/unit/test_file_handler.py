"""Test file handling utilities."""

import pytest
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
from app.utils.file_handler import SecureFileHandler


class TestSecureFileHandler:
    """Test secure file handler."""
    
    def test_initialization(self, temp_dir):
        """Test handler initialization."""
        handler = SecureFileHandler(str(temp_dir))
        assert handler.base_dir == temp_dir.resolve()
        assert handler.base_dir.exists()
    
    def test_get_safe_path(self, temp_dir):
        """Test safe path generation."""
        handler = SecureFileHandler(str(temp_dir))
        safe_path = handler.get_safe_path("test.mp3")
        
        assert safe_path.parent == temp_dir
        assert safe_path.suffix == '.mp3'
        assert str(safe_path).startswith(str(temp_dir))
    
    def test_directory_traversal_protection(self, temp_dir):
        """Test protection against directory traversal."""
        handler = SecureFileHandler(str(temp_dir))
        
        # This should not raise, but path should be safely contained
        safe_path = handler.get_safe_path("../../../etc/passwd")
        assert str(safe_path).startswith(str(temp_dir))
    
    @pytest.mark.asyncio
    async def test_save_upload(self, temp_dir):
        """Test saving uploaded file."""
        handler = SecureFileHandler(str(temp_dir))
        
        content = b"test audio data"
        file = UploadFile(
            filename="test.mp3",
            file=BytesIO(content)
        )
        
        saved_path = await handler.save_upload(file)
        
        assert saved_path.exists()
        assert saved_path.read_bytes() == content
    
    def test_cleanup_file(self, temp_dir):
        """Test file cleanup."""
        handler = SecureFileHandler(str(temp_dir))
        
        # Create a test file
        test_file = temp_dir / "test.mp3"
        test_file.write_text("test")
        
        assert test_file.exists()
        
        result = handler.cleanup_file(test_file)
        
        assert result is True
        assert not test_file.exists()
    
    def test_get_file_size(self, temp_dir):
        """Test getting file size."""
        handler = SecureFileHandler(str(temp_dir))
        
        test_file = temp_dir / "test.mp3"
        content = b"test data"
        test_file.write_bytes(content)
        
        size = handler.get_file_size(test_file)
        assert size == len(content)