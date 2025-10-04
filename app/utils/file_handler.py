"""File handling utilities."""
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.config import settings
from app.core.logging import logger


class SecureFileHandler:
    """Handle file operations securely."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize file handler.
        
        Args:
            base_dir: Base directory for file operations
        """
        self.base_dir = Path(base_dir or settings.temp_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def get_safe_path(self, filename: str) -> Path:
        """
        Generate safe file path preventing directory traversal.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe file path
            
        Raises:
            ValueError: If path would escape base directory
        """
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        ext = os.path.splitext(filename)[1].lower()
        safe_filename = f"{unique_id}{ext}"
        
        # Construct path and ensure it's within base directory
        file_path = (self.base_dir / safe_filename).resolve()
        
        if not str(file_path).startswith(str(self.base_dir)):
            raise ValueError("Invalid file path - directory traversal detected")
        
        return file_path
    
    async def save_upload(self, file: UploadFile) -> Path:
        """
        Safely save uploaded file.
        
        Args:
            file: Uploaded file
            
        Returns:
            Path to saved file
        """
        file_path = self.get_safe_path(file.filename)
        
        logger.info(f"Saving uploaded file to {file_path}")
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):  # 8KB chunks
                    await f.write(chunk)
            
            logger.info(f"File saved successfully: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            # Clean up partial file if it exists
            if file_path.exists():
                file_path.unlink()
            raise
    
    def cleanup_file(self, file_path: Path) -> bool:
        """
        Safely delete file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if file_path.exists() and file_path.is_file():
                # Verify file is within base directory
                if str(file_path.resolve()).startswith(str(self.base_dir)):
                    file_path.unlink()
                    logger.info(f"Cleaned up file: {file_path}")
                    return True
                else:
                    logger.warning(f"Refused to delete file outside base dir: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")
            return False
    
    def get_file_size(self, file_path: Path) -> int:
        """
        Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        return file_path.stat().st_size if file_path.exists() else 0