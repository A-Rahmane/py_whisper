"""Integration tests for async transcription API."""
import pytest
import time
from io import BytesIO
from fastapi.testclient import TestClient


class TestAsyncTranscription:
    """Test async transcription endpoints."""
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_async_transcribe_submission(self, client, sample_audio_bytes):
        """Test async transcription job submission."""
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        response = client.post("/api/v1/transcribe-async", files=files)
        
        assert response.status_code == 202
        data = response.json()
        
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "status_url" in data
        assert "estimated_time" in data
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_job_status_check(self, client, sample_audio_bytes):
        """Test job status endpoint."""
        # Submit job
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        submit_response = client.post("/api/v1/transcribe-async", files=files)
        assert submit_response.status_code == 202
        
        job_id = submit_response.json()["job_id"]
        
        # Check status
        status_response = client.get(f"/api/v1/status/{job_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] in ["pending", "processing", "completed"]
    
    @