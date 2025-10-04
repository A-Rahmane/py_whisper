"""Test output formatting."""

import pytest
from app.core.transcription.formatter import OutputFormatter


@pytest.fixture
def sample_result():
    """Sample transcription result."""
    return {
        "text": "Hello world. This is a test.",
        "language": "en",
        "duration": 10.5,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world.",
                "confidence": 0.95
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 5.0,
                "text": "This is a test.",
                "confidence": 0.92
            }
        ]
    }


class TestOutputFormatter:
    """Test output formatter."""
    
    def test_to_text(self, sample_result):
        """Test plain text formatting."""
        result = OutputFormatter.to_text(sample_result)
        assert result == "Hello world. This is a test."
        assert isinstance(result, str)
    
    def test_to_srt(self, sample_result):
        """Test SRT formatting."""
        result = OutputFormatter.to_srt(sample_result)
        
        assert "1\n" in result
        assert "00:00:00,000 --> 00:00:02,500" in result
        assert "Hello world." in result
        assert "2\n" in result
        assert "This is a test." in result
    
    def test_to_vtt(self, sample_result):
        """Test VTT formatting."""
        result = OutputFormatter.to_vtt(sample_result)
        
        assert result.startswith("WEBVTT")
        assert "00:00:00.000 --> 00:00:02.500" in result
        assert "Hello world." in result
    
    def test_srt_timestamp_format(self):
        """Test SRT timestamp formatting."""
        timestamp = OutputFormatter._format_timestamp_srt(65.500)
        assert timestamp == "00:01:05,500"
    
    def test_vtt_timestamp_format(self):
        """Test VTT timestamp formatting."""
        timestamp = OutputFormatter._format_timestamp_vtt(65.500)
        assert timestamp == "00:01:05.500"