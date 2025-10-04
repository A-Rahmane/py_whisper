"""Application configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "transcription-service"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Whisper
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_model_dir: str = "./models"
    
    # File Processing
    max_file_size: int = 1073741824  # 1GB
    max_duration: int = 10800  # 3 hours
    temp_dir: str = "./temp"
    cleanup_interval: int = 3600
    
    # Security
    enable_rate_limit: bool = True
    rate_limit_per_minute: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        Path(self.whisper_model_dir).mkdir(parents=True, exist_ok=True)
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)


settings = Settings()