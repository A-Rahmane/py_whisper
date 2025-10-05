#!/bin/bash
# Start Flower monitoring UI

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start Flower
echo "Starting Flower on http://localhost:5555"
celery -A tasks.celery_app flower --port=5555