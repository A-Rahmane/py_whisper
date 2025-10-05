"""Celery application configuration."""
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from app.config import settings
from app.core.logging import logger

# Create Celery app
celery_app = Celery(
    "transcription_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['tasks.transcription_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time
    timezone='UTC',
    enable_utc=True,
    
    # Results
    result_expires=settings.job_result_ttl,
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Worker
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Prevent memory leaks
    
    # Retry
    task_default_retry_delay=settings.job_retry_delay,
    task_max_retries=settings.max_job_retry,
    
    # Performance
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
)


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Log when worker is ready."""
    logger.info(f"Celery worker ready: {sender.hostname}")


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    """Log when worker shuts down."""
    logger.info(f"Celery worker shutting down: {sender.hostname}")


if __name__ == '__main__':
    celery_app.start()