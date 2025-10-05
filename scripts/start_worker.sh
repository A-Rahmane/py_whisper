#!/bin/bash
# Start Celery worker

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start worker
echo "Starting Celery worker..."
celery -A tasks.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=50 \
    --time-limit=3900 \
    --soft-time-limit=3600