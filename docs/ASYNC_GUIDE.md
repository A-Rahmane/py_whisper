# Async Transcription Guide

## Overview

The async transcription feature allows you to process large audio/video files in the background without blocking your application.

## When to Use Async

Use async processing when:
- Files are longer than 10 minutes
- You need to process multiple files concurrently
- You want to provide immediate response to users
- Processing large batches of files

## Architecture

```
Client → API → Redis Queue → Celery Worker → Whisper Engine
                    ↓
              Status Updates
```

## Usage

### 1. Submit Job

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe-async" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "model=base"
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Transcription job accepted and queued for processing",
  "status_url": "/api/v1/status/abc-123-def-456",
  "estimated_time": 30
}
```

### 2. Check Status

```bash
curl "http://localhost:8000/api/v1/status/abc-123-def-456"
```

Response (Processing):
```json
{
  "job_id": "abc-123-def-456",
  "status": "processing",
  "progress": 45,
  "created_at": "2025-10-04T10:00:00Z",
  "started_at": "2025-10-04T10:00:05Z",
  "estimated_completion": "2025-10-04T10:05:00Z"
}
```

Response (Completed):
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-10-04T10:00:00Z",
  "completed_at": "2025-10-04T10:02:30Z",
  "result": {
    "text": "Full transcription text...",
    "language": "en",
    "duration": 125.5,
    "segments": [...]
  }
}
```

### 3. List Jobs

```bash
curl "http://localhost:8000/api/v1/jobs?status=processing&page=1&page_size=20"
```

### 4. Cancel Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/abc-123-def-456/cancel"
```

### 5. Delete Job

```bash
curl -X DELETE "http://localhost:8000/api/v1/jobs/abc-123-def-456"
```

## Monitoring

### Flower UI

Access Celery monitoring at: http://localhost:5555

### Check Infrastructure

```bash
python scripts/check_async.py
```

## Troubleshooting

### Workers Not Starting

Check logs:
```bash
docker-compose logs transcription-worker
```

Restart workers:
```bash
docker-compose restart transcription-worker
```

### Redis Connection Issues

Check Redis:
```bash
docker-compose logs redis
```

Test connection:
```bash
redis-cli -h localhost -p 6379 ping
```

### Job Stuck in Queue

Purge queue:
```bash
python scripts/purge_queue.py
```

### High Memory Usage

Reduce worker concurrency in docker-compose.yml:
```yaml
command: celery -A tasks.celery_app worker --loglevel=info --concurrency=1
```

## Configuration

### Environment Variables

```bash
# Enable async processing
ENABLE_ASYNC=true

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Job settings
JOB_RESULT_TTL=86400  # 24 hours
MAX_JOB_RETRY=3
JOB_RETRY_DELAY=60

# Worker settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Scaling Workers

Increase replicas in docker-compose.yml:
```yaml
transcription-worker:
  deploy:
    replicas: 4  # Run 4 worker containers
```

Or use docker-compose scale:
```bash
docker-compose up -d --scale transcription-worker=4
```

## Best Practices

1. **Job Cleanup**: Delete completed jobs periodically to free resources
2. **Monitoring**: Use Flower to monitor worker health and queue length
3. **Retry Logic**: Configured automatically for transient failures
4. **Resource Limits**: Set appropriate memory and CPU limits per worker
5. **Result TTL**: Adjust `JOB_RESULT_TTL` based on your requirements

## Performance Tips

1. Use smaller models (base/small) for faster processing
2. Enable GPU if available (`WHISPER_DEVICE=cuda`)
3. Adjust worker concurrency based on available cores
4. Use SSD for temporary file storage
5. Monitor queue length and scale workers accordingly