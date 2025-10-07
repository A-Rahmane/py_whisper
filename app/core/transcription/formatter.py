"""Output format conversion utilities."""
from typing import Dict, Any, List
from datetime import timedelta


class OutputFormatter:
    """Format transcription output in different formats."""
    
    @staticmethod
    def to_text(result: Dict[str, Any]) -> str:
        """
        Format as plain text.
        
        Args:
            result: Transcription result
            
        Returns:
            Plain text transcription
        """
        return result["text"]
    
    @staticmethod
    def to_srt(result: Dict[str, Any]) -> str:
        """
        Format as SRT subtitle format.
        
        Args:
            result: Transcription result
            
        Returns:
            SRT formatted string
        """
        srt_output = []
        
        for segment in result["segments"]:
            # Format timestamps
            start = OutputFormatter._format_timestamp_srt(segment["start"])
            end = OutputFormatter._format_timestamp_srt(segment["end"])
            
            # SRT format: index, timestamp range, text, blank line
            srt_output.append(f"{segment['id'] + 1}")
            srt_output.append(f"{start} --> {end}")
            srt_output.append(segment["text"])
            srt_output.append("")  # Blank line
        
        return "\n".join(srt_output)
    
    @staticmethod
    def to_vtt(result: Dict[str, Any]) -> str:
        """
        Format as WebVTT subtitle format.
        
        Args:
            result: Transcription result
            
        Returns:
            VTT formatted string
        """
        vtt_output = ["WEBVTT", ""]
        
        for segment in result["segments"]:
            # Format timestamps
            start = OutputFormatter._format_timestamp_vtt(segment["start"])
            end = OutputFormatter._format_timestamp_vtt(segment["end"])
            
            # VTT format
            vtt_output.append(f"{start} --> {end}")
            vtt_output.append(segment["text"])
            vtt_output.append("")  # Blank line
        
        return "\n".join(vtt_output)
    
    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """
        Format timestamp for SRT (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp
        """
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
    
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_timestamp_vtt(seconds: float) -> str:
        """
        Format timestamp for VTT (HH:MM:SS.mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp
        """
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"