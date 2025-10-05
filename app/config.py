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
    max_file_size: int = 1_073_741_824  # 1GB
    max_duration: int = 3600  # an hour
    temp_dir: str = "./temp"
    cleanup_interval: int = 3600
    
    # Security
    enable_rate_limit: bool = True
    rate_limit_per_minute: int = 30
    
    # Async Processing
    enable_async: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    job_result_ttl: int = 86400  # 24 hours
    max_job_retry: int = 3
    job_retry_delay: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        Path(self.whisper_model_dir).mkdir(parents=True, exist_ok=True)
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Auto-configure Celery URLs if not provided
        if self.enable_async:
            if not self.celery_broker_url:
                redis_auth = f":{self.redis_password}@" if self.redis_password else ""
                self.celery_broker_url = (
                    f"redis://{redis_auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
                )
            
            if not self.celery_result_backend:
                redis_auth = f":{self.redis_password}@" if self.redis_password else ""
                self.celery_result_backend = (
                    f"redis://{redis_auth}{self.redis_host}:{self.redis_port}/{self.redis_db + 1}"
                )


settings = Settings()