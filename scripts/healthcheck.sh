#!/bin/bash
# Docker healthcheck script

set -e

# Check if service is responding
response=$(curl -f -s http://localhost:8000/health/live || echo "failed")

if [ "$response" = "failed" ]; then
    echo "Health check failed: service not responding"
    exit 1
fi

echo "Health check passed"
exit 0