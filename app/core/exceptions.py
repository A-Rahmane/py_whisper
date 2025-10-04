"""Custom exception classes."""


class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class InvalidFileFormatError(TranscriptionError):
    """Raised when file format is not supported."""
    pass


class FileTooLargeError(TranscriptionError):
    """Raised when file exceeds size limit."""
    pass


class InvalidParameterError(TranscriptionError):
    """Raised when request parameters are invalid."""
    pass


class TranscriptionFailedError(TranscriptionError):
    """Raised when transcription process fails."""
    pass


class ModelLoadError(TranscriptionError):
    """Raised when Whisper model fails to load."""
    pass


class ProcessingError(TranscriptionError):
    """Raised when unexpected processing error occurs."""
    pass


class ResourceExhaustedError(TranscriptionError):
    """Raised when server resources are exhausted."""
    pass