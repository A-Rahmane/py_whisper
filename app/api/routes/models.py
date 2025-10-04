"""Model information API routes."""
from fastapi import APIRouter
from typing import List
from app.config import settings
from app.models.responses import ModelsResponse, ModelInfo, LanguagesResponse, LanguageInfo
from app.core.transcription.engine import whisper_engine


router = APIRouter(prefix="/api/v1", tags=["models"])


# Model information
MODELS_INFO = [
    {
        "name": "tiny",
        "size": "75 MB",
        "speed": "32x",
        "accuracy": "Basic"
    },
    {
        "name": "base",
        "size": "142 MB",
        "speed": "16x",
        "accuracy": "Good"
    },
    {
        "name": "small",
        "size": "466 MB",
        "speed": "6x",
        "accuracy": "Better"
    },
    {
        "name": "medium",
        "size": "1.5 GB",
        "speed": "2x",
        "accuracy": "High"
    },
    {
        "name": "large-v3",
        "size": "2.9 GB",
        "speed": "1x",
        "accuracy": "Best"
    }
]


# Supported languages (subset of most common)
LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "it", "name": "Italian"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "ru", "name": "Russian"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "nl", "name": "Dutch"},
    {"code": "pl", "name": "Polish"},
    {"code": "tr", "name": "Turkish"},
]


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="List available models",
    description="Get information about available Whisper models"
)
async def list_models():
    """List available Whisper models."""
    models = []
    
    for model_info in MODELS_INFO:
        is_loaded = whisper_engine.model_manager.is_model_loaded(
            model_info["name"],
            settings.whisper_device,
            settings.whisper_compute_type
        )
        
        models.append(ModelInfo(
            name=model_info["name"],
            size=model_info["size"],
            speed=model_info["speed"],
            accuracy=model_info["accuracy"],
            loaded=is_loaded
        ))
    
    return ModelsResponse(
        models=models,
        current_model=settings.whisper_model
    )


@router.get(
    "/languages",
    response_model=LanguagesResponse,
    summary="List supported languages",
    description="Get list of supported languages for transcription"
)
async def list_languages():
    """List supported languages."""
    languages = [LanguageInfo(**lang) for lang in LANGUAGES]
    return LanguagesResponse(languages=languages)