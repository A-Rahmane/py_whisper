"""Whisper transcription engine."""
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from faster_whisper import WhisperModel
from app.config import settings
from app.core.logging import logger
from app.core.exceptions import ModelLoadError, TranscriptionFailedError


class ModelManager:
    """Manage Whisper model loading and caching."""
    
    _instance = None
    _lock = threading.Lock()
    _models: Dict[str, WhisperModel] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(
        self,
        model_name: str,
        device: str,
        compute_type: str
    ) -> WhisperModel:
        """
        Load and cache Whisper model.
        
        Args:
            model_name: Model size (tiny, base, small, medium, large, large-v3)
            device: Device to use (cpu, cuda)
            compute_type: Computation type (int8, float16, float32)
            
        Returns:
            Loaded WhisperModel instance
            
        Raises:
            ModelLoadError: If model loading fails
        """
        cache_key = f"{model_name}_{device}_{compute_type}"
        
        with self._lock:
            if cache_key not in self._models:
                try:
                    logger.info(f"Loading Whisper model: {cache_key}")
                    start_time = time.time()
                    
                    self._models[cache_key] = WhisperModel(
                        model_name,
                        device=device,
                        compute_type=compute_type,
                        download_root=settings.whisper_model_dir
                    )
                    
                    load_time = time.time() - start_time
                    logger.info(f"Model loaded successfully in {load_time:.2f}s: {cache_key}")
                    
                except Exception as e:
                    logger.error(f"Failed to load model {cache_key}: {e}")
                    raise ModelLoadError(f"Failed to load Whisper model: {str(e)}")
            
            return self._models[cache_key]
    
    def preload_model(self, model_name: str, device: str, compute_type: str) -> None:
        """Preload a model during startup."""
        try:
            self.get_model(model_name, device, compute_type)
        except Exception as e:
            logger.error(f"Failed to preload model: {e}")
    
    def is_model_loaded(self, model_name: str, device: str, compute_type: str) -> bool:
        """Check if a model is loaded."""
        cache_key = f"{model_name}_{device}_{compute_type}"
        return cache_key in self._models


class WhisperEngine:
    """Whisper transcription engine."""
    
    def __init__(self):
        """Initialize engine."""
        self.model_manager = ModelManager()
    
    def transcribe(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        temperature: float = 0.0,
        word_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detection)
            model_name: Whisper model size
            device: Device to use
            compute_type: Computation type
            temperature: Sampling temperature
            word_timestamps: Whether to include word-level timestamps
            
        Returns:
            Dictionary containing transcription results
            
        Raises:
            TranscriptionFailedError: If transcription fails
        """
        try:
            logger.info(f"Starting transcription: {audio_path}")
            start_time = time.time()
            
            # Load model
            model = self.model_manager.get_model(model_name, device, compute_type)
            
            # Transcribe
            segments, info = model.transcribe(
                str(audio_path),
                language=language,
                temperature=temperature,
                word_timestamps=word_timestamps,
                vad_filter=True,  # Enable voice activity detection
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=100
                )
            )
            
            # Convert segments generator to list
            segments_list = list(segments)
            
            # Extract full text
            full_text = " ".join([segment.text.strip() for segment in segments_list])
            
            # Format segments
            formatted_segments = []
            all_words = []
            
            for idx, segment in enumerate(segments_list):
                seg_dict = {
                    "id": idx,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": segment.avg_logprob  # Use avg_logprob as confidence
                }
                
                # Add word timestamps if requested
                if word_timestamps and segment.words:
                    seg_words = []
                    for word in segment.words:
                        word_dict = {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "confidence": word.probability
                        }
                        seg_words.append(word_dict)
                        all_words.append(word_dict)
                    
                    seg_dict["words"] = seg_words
                
                formatted_segments.append(seg_dict)
            
            processing_time = time.time() - start_time
            
            result = {
                "text": full_text,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": formatted_segments,
                "words": all_words if word_timestamps else None,
                "processing_time": processing_time
            }
            
            logger.info(
                f"Transcription completed in {processing_time:.2f}s "
                f"for {info.duration:.2f}s audio ({info.language})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionFailedError(f"Transcription failed: {str(e)}")


# Global engine instance
whisper_engine = WhisperEngine()