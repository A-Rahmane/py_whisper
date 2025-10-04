"""Response models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class WordTimestamp(BaseModel):
    """Word-level timestamp."""
    word: str
    start: float
    end: float
    confidence: float


class Segment(BaseModel):
    """Transcription segment with timestamps."""
    id: int
    start: float
    end: float
    text: str
    confidence: float
    words: Optional[List[WordTimestamp]] = None


class TranscriptionResponse(BaseModel):
    """Transcription result."""
    text: str = Field(description="Full transcription text")
    language: str = Field(description="Detected or specified language")
    language_probability: float = Field(description="Language detection confidence")
    duration: float = Field(description="Audio duration in seconds")
    segments: List[Segment] = Field(description="Transcription segments")
    words: Optional[List[WordTimestamp]] = Field(
        None,
        description="Word-level timestamps (if requested)"
    )
    processing_time: float = Field(description="Processing time in seconds")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    model: str
    device: str
    timestamp: datetime
    uptime_seconds: float


class ModelInfo(BaseModel):
    """Model information."""
    name: str
    size: str
    speed: str
    accuracy: str
    loaded: bool = False


class ModelsResponse(BaseModel):
    """Available models response."""
    models: List[ModelInfo]
    current_model: str


class LanguageInfo(BaseModel):
    """Language information."""
    code: str
    name: str


class LanguagesResponse(BaseModel):
    """Supported languages response."""
    languages: List[LanguageInfo]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None