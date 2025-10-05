#!/usr/bin/env python
"""Check async infrastructure status."""
import sys
import time
from app.config import settings
from app.core.redis_client import redis_client
from app.core.logging import logger


def check_redis():
    """Check Redis connection."""
    try:
        redis_client.connect()
        if redis_client.is_connected():
            logger.info("✓ Redis is connected")
            return True
        else:
            logger.error("✗ Redis is not connected")
            return False
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False


def check_celery():
    """Check Celery workers."""
    try:
        from tasks.celery_app import celery_app
        
        inspect = celery_app.control.inspect()
        workers = inspect.active()
        
        if workers and len(workers) > 0:
            logger.info(f"✓ Celery workers active: {len(workers)}")
            for worker_name, tasks in workers.items():
                logger.info(f"  - {worker_name}: {len(tasks)} active tasks")
            return True
        else:
            logger.error("✗ No Celery workers found")
            return False
    except Exception as e:
        logger.error(f"✗ Celery check failed: {e}")
        return False


def check_queue_stats():
    """Check queue statistics."""
    try:
        from tasks.celery_app import celery_app
        
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info("Queue Statistics:")
            for worker_name, worker_stats in stats.items():
                logger.info(f"  Worker: {worker_name}")
                logger.info(f"    Pool: {worker_stats.get('pool', {})}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to get queue stats: {e}")
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("Async Infrastructure Status Check")
    logger.info("=" * 60)
    
    if not settings.enable_async:
        logger.warning("⚠ Async processing is disabled in configuration")
        sys.exit(1)
    
    results = []
    
    # Check Redis
    logger.info("\n1. Checking Redis...")
    results.append(check_redis())
    
    # Check Celery
    logger.info("\n2. Checking Celery workers...")
    results.append(check_celery())
    
    # Check queue stats
    logger.info("\n3. Checking queue statistics...")
    check_queue_stats()
    
    # Summary
    logger.info("\n" + "=" * 60)
    if all(results):
        logger.info("✓ All checks passed - Async infrastructure is ready")
        sys.exit(0)
    else:
        logger.error("✗ Some checks failed - Please review the errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()