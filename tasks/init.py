"""Celery tasks package."""
from tasks.celery_app import celery_app
from tasks.transcription_tasks import transcribe_file_task

__all__ = ['celery_app', 'transcribe_file_task']