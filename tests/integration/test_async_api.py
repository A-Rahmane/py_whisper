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
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_job_completion(self, client, sample_audio_bytes):
        """Test complete async transcription workflow."""
        # Submit job
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        submit_response = client.post("/api/v1/transcribe-async", files=files)
        assert submit_response.status_code == 202
        
        job_id = submit_response.json()["job_id"]
        
        # Poll for completion (max 60 seconds)
        max_attempts = 60
        for attempt in range(max_attempts):
            status_response = client.get(f"/api/v1/status/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                assert "result" in status_data
                assert "text" in status_data["result"]
                return
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
            
            time.sleep(1)
        
        pytest.fail("Job did not complete within 60 seconds")
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_job_cancellation(self, client, sample_audio_bytes):
        """Test job cancellation."""
        # Submit job
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        submit_response = client.post("/api/v1/transcribe-async", files=files)
        assert submit_response.status_code == 202
        
        job_id = submit_response.json()["job_id"]
        
        # Cancel job
        cancel_response = client.post(f"/api/v1/jobs/{job_id}/cancel")
        assert cancel_response.status_code == 200
        
        # Check status
        status_response = client.get(f"/api/v1/status/{job_id}")
        status_data = status_response.json()
        
        assert status_data["status"] in ["cancelled", "completed"]
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_list_jobs(self, client, sample_audio_bytes):
        """Test listing jobs."""
        # Submit a few jobs
        for i in range(3):
            files = {
                "file": (f"test{i}.wav", BytesIO(sample_audio_bytes), "audio/wav")
            }
            client.post("/api/v1/transcribe-async", files=files)
        
        # List jobs
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert len(data["jobs"]) >= 3
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_job_deletion(self, client, sample_audio_bytes):
        """Test job deletion."""
        # Submit and complete job
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        submit_response = client.post("/api/v1/transcribe-async", files=files)
        job_id = submit_response.json()["job_id"]
        
        # Wait a bit for job to process
        time.sleep(5)
        
        # Delete job
        delete_response = client.delete(f"/api/v1/jobs/{job_id}")
        
        # Should succeed or return 404 if already cleaned up
        assert delete_response.status_code in [200, 404]
    
    def test_async_disabled_error(self, client, sample_audio_bytes, monkeypatch):
        """Test error when async is disabled."""
        from app.config import settings
        
        # Temporarily disable async
        monkeypatch.setattr(settings, "enable_async", False)
        
        files = {
            "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
        }
        
        response = client.post("/api/v1/transcribe-async", files=files)
        assert response.status_code == 503
        
        data = response.json()
        assert "error" in data["detail"]
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-async"),
        reason="Async tests require Redis and Celery"
    )
    def test_job_with_different_formats(self, client, sample_audio_bytes):
        """Test async transcription with different output formats."""
        formats = ["json", "text", "srt", "vtt"]
        
        for fmt in formats:
            files = {
                "file": ("test.wav", BytesIO(sample_audio_bytes), "audio/wav")
            }
            data = {
                "response_format": fmt
            }
            
            response = client.post("/api/v1/transcribe-async", files=files, data=data)
            assert response.status_code == 202
            
            job_id = response.json()["job_id"]
            
            # Poll for completion
            for _ in range(30):
                status_response = client.get(f"/api/v1/status/{job_id}")
                status_data = status_response.json()
                
                if status_data["status"] == "completed":
                    assert "result" in status_data
                    break
                
                time.sleep(1)