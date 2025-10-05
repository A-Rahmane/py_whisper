"""Pytest configuration and fixtures."""
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--run-async",
        action="store_true",
        default=False,
        help="Run async integration tests (requires Redis and Celery)"
    )


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
    import wave
    import struct
    
    wav_path = temp_dir / "test_audio.wav"
    
    with wave.open(str(wav_path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        
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
        
        for _ in range(16000):
            wav_file.writeframes(struct.pack('h', 0))
    
    buffer.seek(0)
    return buffer.read()


@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis is available for testing."""
    try:
        from app.core.redis_client import redis_client
        redis_client.connect()
        is_available = redis_client.is_connected()
        redis_client.disconnect()
        return is_available
    except:
        return False


@pytest.fixture(scope="session")
def celery_available():
    """Check if Celery worker is available for testing."""
    try:
        from tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        workers = inspect.active()
        return workers is not None and len(workers) > 0
    except:
        return False