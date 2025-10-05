#!/usr/bin/env python
"""Purge all tasks from Celery queue."""
import sys
from app.core.logging import logger


def purge_queue():
    """Purge all pending tasks."""
    try:
        from tasks.celery_app import celery_app
        
        result = celery_app.control.purge()
        logger.info(f"Purged {result} tasks from queue")
        return True
    except Exception as e:
        logger.error(f"Failed to purge queue: {e}")
        return False


def main():
    """Main function."""
    logger.warning("This will delete all pending tasks from the queue!")
    response = input("Are you sure? (yes/no): ")
    
    if response.lower() != "yes":
        logger.info("Cancelled")
        sys.exit(0)
    
    if purge_queue():
        logger.info("Queue purged successfully")
        sys.exit(0)
    else:
        logger.error("Failed to purge queue")
        sys.exit(1)


if __name__ == "__main__":
    main()