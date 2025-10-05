"""Input validation utilities."""
import os
from typing import Set, Tuple
from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import (
    InvalidFileFormatError,
    FileTooLargeError
)


# Allowed file extensions
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {
    '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma'
}

ALLOWED_VIDEO_EXTENSIONS: Set[str] = {
    '.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv'
}

ALLOWED_EXTENSIONS = ALLOWED_AUDIO_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

# Allowed MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac',
    'audio/mp4', 'audio/aac', 'audio/x-ms-wma',
    'video/mp4', 'video/webm', 'video/x-msvideo',
    'video/quicktime', 'video/x-matroska', 'video/x-flv'
}

# Magic bytes for format validation
MAGIC_BYTES = {
    '.mp3': [b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'],
    '.wav': [b'RIFF'],
    '.ogg': [b'OggS'],
    '.flac': [b'fLaC'],
    '.mp4': [b'ftyp', b'mdat', b'moov'],
    '.webm': [b'\x1a\x45\xdf\xa3'],
    '.avi': [b'RIFF'],
}


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Lowercase file extension
        
    Raises:
        InvalidFileFormatError: If extension is not supported
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    if not file_ext:
        raise InvalidFileFormatError("File has no extension")
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileFormatError(
            f"Unsupported file format: {file_ext}. "
            f"Supported formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    
    return file_ext


def validate_mime_type(content_type: str) -> None:
    """
    Validate MIME type.
    
    Args:
        content_type: MIME type from upload
        
    Raises:
        InvalidFileFormatError: If MIME type is not supported
    """
    if content_type not in ALLOWED_MIME_TYPES:
        raise InvalidFileFormatError(
            f"Invalid MIME type: {content_type}"
        )


def validate_file_size(file_size: int) -> None:
    """
    Validate file size.
    
    Args:
        file_size: Size of file in bytes
        
    Raises:
        FileTooLargeError: If file exceeds size limit
    """
    if file_size > settings.max_file_size:
        max_size_mb = settings.max_file_size / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        raise FileTooLargeError(
            f"File size {actual_size_mb:.2f}MB exceeds limit {max_size_mb:.2f}MB"
        )


def validate_magic_bytes(header: bytes, file_ext: str) -> bool:
    """
    Validate file magic bytes match extension.
    
    Args:
        header: First bytes of file
        file_ext: File extension
        
    Returns:
        True if valid, False otherwise
    """
    if file_ext not in MAGIC_BYTES:
        return True  # No validation available for this type
    
    expected_bytes = MAGIC_BYTES[file_ext]
    
    for magic in expected_bytes:
        if magic in header:
            return True
    
    return False


async def validate_upload_file(file: UploadFile) -> Tuple[str, int]:
    """
    Comprehensive file validation.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (file_extension, file_size)
        
    Raises:
        InvalidFileFormatError: If file format is invalid
        FileTooLargeError: If file is too large
    """
    # Validate extension
    file_ext = validate_file_extension(file.filename)
    
    # Validate MIME type
    validate_mime_type(file.content_type)
    
    # Get file size
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()  # Get current position (end = total size)
    file.file.seek(0)  # Reset to start
    
    # Validate size
    validate_file_size(file_size)
    
    # Validate magic bytes
    header = await file.read(32)
    await file.seek(0)
    
    if not validate_magic_bytes(header, file_ext):
        raise InvalidFileFormatError(
            f"File header does not match {file_ext} format"
        )
    
    return file_ext, file_size