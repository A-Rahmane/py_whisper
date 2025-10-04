"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_path(temp_dir):
    """Create a minimal valid WAV file for testing."""
    # Create a minimal WAV file (1 second of silence at 16kHz)
    import wave
    import struct
    
    wav_path = temp_dir / "test_audio.wav"
    
    with wave.open(str(wav_path), 'w') as wav_file:
        # Set parameters: 1 channel, 2 bytes per sample, 16kHz
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        
        # Write 1 second of silence (16000 samples of value 0)
        for _ in range(16000):
            wav_file.writeframes(struct.pack('h', 0))
    
    return wav_path


@pytest.fixture
def sample_audio_bytes():
    """Create sample audio file bytes."""
    import wave
    import struct
    import io
    
    buffer = io.BytesIO()
    
    with wave.open(buffer, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        
        for _ in range(16000):  # 1 second
            wav_file.writeframes(struct.pack('h', 0))
    
    buffer.seek(0)
    return buffer.read()