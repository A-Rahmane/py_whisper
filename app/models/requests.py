"""Request models."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from enum import Enum


class ModelSize(str, Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V3 = "large-v3"


class ResponseFormat(str, Enum):
    """Response format options."""
    JSON = "json"
    TEXT = "text"
    SRT = "srt"
    VTT = "vtt"


class TimestampGranularity(str, Enum):
    """Timestamp granularity options."""
    WORD = "word"
    SEGMENT = "segment"


class TranscriptionRequest(BaseModel):
    """Transcription request parameters."""
    
    language: Optional[str] = Field(
        None,
        description="ISO 639-1 language code (e.g., 'en', 'ar', 'fr')",
        min_length=2,
        max_length=2
    )
    model: ModelSize = Field(
        ModelSize.BASE,
        description="Whisper model size"
    )
    response_format: ResponseFormat = Field(
        ResponseFormat.JSON,
        description="Output format"
    )
    timestamp_granularity: TimestampGranularity = Field(
        TimestampGranularity.SEGMENT,
        description="Timestamp level"
    )
    temperature: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Sampling temperature"
    )
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code."""
        if v is not None:
            return v.lower()
        return v

    class Config:
        use_enum_values = True