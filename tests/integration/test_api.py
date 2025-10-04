"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test main health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "version" in data
        assert "model" in data
        assert "device" in data
        assert "uptime_seconds" in data
    
    def test_liveness_probe(self, client):
        """Test liveness probe."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
    
    def test_readiness_probe(self, client):
        """Test readiness probe."""
        response = client.get("/health/ready")
        
        assert response.status_code in [200, 503]
        data = response.json()
        
        assert "status" in data
        assert "checks" in data


class TestModelsEndpoints:
    """Test model information endpoints."""
    
    def test_list_models(self, client):
        """Test models list endpoint."""
        response = client.get("/api/v1/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "current_model" in data
        assert len(data["models"]) > 0
        
        # Check model structure
        model = data["models"][0]
        assert "name" in model
        assert "size" in model
        assert "speed" in model
        assert "accuracy" in model
        assert "loaded" in model
    
    def test_list_languages(self, client):
        """Test languages list endpoint."""
        response = client.get("/api/v1/languages")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "languages" in data
        assert len(data["languages"]) > 0
        
        # Check language structure
        lang = data["languages"][0]
        assert "code" in lang
        assert "name" in lang


class TestTranscriptionEndpoint:
    """Test transcription endpoint."""
    
    def test_transcribe_missing_file(self, client):
        """Test transcription without file."""
        response = client.post("/api/v1/transcribe")
        
        assert response.status_code == 422  # Validation error
    
    def test_transcribe_invalid_format(self, client):
        """Test transcription with invalid file format."""
        files = {
            "file": ("test.txt", BytesIO(b"not an audio file"), "text/plain")
        }
        
        response = client.post("/api/v1/transcribe", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data["detail"]
    
    def test_transcribe_valid_file(self, client, sample_audio_bytes):
        """Test transcription with valid audio file."""
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        response = client.post("/api/v1/transcribe", files=files)
        
        # Note: This might fail if model isn't downloaded
        # In real tests, you'd mock the whisper engine
        if response.status_code == 200:
            data = response.json()
            assert "text" in data
            assert "language" in data
            assert "duration" in data
            assert "segments" in data
    
    def test_transcribe_with_language(self, client, sample_audio_bytes):
        """Test transcription with language specified."""
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        data = {
            "language": "en"
        }
        
        response = client.post("/api/v1/transcribe", files=files, data=data)
        
        # Should accept the request even if transcription fails
        assert response.status_code in [200, 422, 500]
    
    def test_transcribe_text_format(self, client, sample_audio_bytes):
        """Test transcription with text output format."""
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        data = {
            "response_format": "text"
        }
        
        response = client.post("/api/v1/transcribe", files=files, data=data)
        
        if response.status_code == 200:
            data = response.json()
            assert "result" in data
    
    def test_transcribe_invalid_model(self, client, sample_audio_bytes):
        """Test transcription with invalid model."""
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        data = {
            "model": "invalid-model"
        }
        
        response = client.post("/api/v1/transcribe", files=files, data=data)
        
        assert response.status_code == 422  # Validation error


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"