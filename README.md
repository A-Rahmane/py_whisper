# Whisper Transcription Microservice

A high-performance Python microservice for audio and video transcription using OpenAI's Whisper model with support for both synchronous and asynchronous processing.

## Features

- 🎯 Accurate speech-to-text transcription using Whisper
- 🌍 Multi-language support with automatic detection
- 📝 Multiple output formats (JSON, Text, SRT, VTT)
- ⚡ Fast processing with faster-whisper
- 🎬 Support for audio and video files
- 🔄 Asynchronous processing for large files
- 🔒 Secure file handling with validation
- 📊 Built-in health checks and monitoring
- 🐳 Docker ready with multi-container setup
- 🌸 Flower UI for task monitoring

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Async Processing](#async-processing)
- [Configuration](#configuration)
- [Development](#development)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/A-Rahmane/py_whisper.git
cd transcription-service

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower UI: http://localhost:5555

### Test the API

```bash
# Synchronous transcription
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=en"

# Asynchronous transcription
curl -X POST "http://localhost:8000/api/v1/transcribe-async" \
  -F "file=@audio.mp3" \
  -F "model=base"
```

## Installation

### Prerequisites

- Python 3.11+
- FFmpeg
- Redis (for async processing)
- Docker and Docker Compose (recommended)

### Local Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Download Whisper models
python scripts/download_models.py --model base

# Start Redis (required for async)
redis-server

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start Celery worker
celery -A tasks.celery_app worker --loglevel=info

# Optionally, start Flower for monitoring
celery -A tasks.celery_app flower --port=5555
```

## Usage

### Synchronous Transcription

```python
import requests

# Upload and transcribe
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/transcribe',
        files={'file': f},
        data={
            'language': 'en',
            'model': 'base',
            'response_format': 'json'
        }
    )

result = response.json()
print(result['text'])
```

### Asynchronous Transcription

```python
import requests
import time

# Submit job
with open('audio.mp3', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/transcribe-async',
        files={'file': f},
        data={'model': 'base', 'language': 'en'}
    )

job_id = response.json()['job_id']
print(f"Job submitted: {job_id}")

# Poll for completion
while True:
    status = requests.get(
        f'http://localhost:8000/api/v1/status/{job_id}'
    ).json()
    
    if status['status'] == 'completed':
        print("Transcription:", status['result']['text'])
        break
    elif status['status'] == 'failed':
        print("Error:", status['error'])
        break
    
    print(f"Progress: {status.get('progress', 0)}%")
    time.sleep(2)
```

### Using cURL

```bash
# Synchronous
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "language=en" \
  -F "model=base" \
  -F "response_format=json"

# Asynchronous
curl -X POST "http://localhost:8000/api/v1/transcribe-async" \
  -F "file=@audio.mp3" \
  -F "model=base"

# Check status
curl "http://localhost:8000/api/v1/status/{job_id}"

# List jobs
curl "http://localhost:8000/api/v1/jobs?status=processing"

# Cancel job
curl -X POST "http://localhost:8000/api/v1/jobs/{job_id}/cancel"

# Delete job
curl -X DELETE "http://localhost:8000/api/v1/jobs/{job_id}"
```

## API Reference

### Endpoints

#### Health Check
- `GET /health` - Service health status
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /health/async` - Async infrastructure health

#### Models
- `GET /api/v1/models` - List available Whisper models
- `GET /api/v1/languages` - List supported languages

#### Transcription
- `POST /api/v1/transcribe` - Synchronous transcription
- `POST /api/v1/transcribe-async` - Asynchronous transcription

#### Job Management
- `GET /api/v1/status/{job_id}` - Get job status
- `GET /api/v1/jobs` - List jobs
- `POST /api/v1/jobs/{job_id}/cancel` - Cancel job
- `DELETE /api/v1/jobs/{job_id}` - Delete job

### Supported Formats

**Audio:**
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- FLAC (.flac)
- M4A (.m4a)
- AAC (.aac)
- WMA (.wma)

**Video:**
- MP4 (.mp4)
- WebM (.webm)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)
- FLV (.flv)

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| file | File | Required | Audio/video file to transcribe |
| language | String | Auto-detect | ISO 639-1 language code (e.g., 'en', 'es') |
| model | String | base | Model size: tiny, base, small, medium, large, large-v3 |
| response_format | String | json | Output format: json, text, srt, vtt |
| timestamp_granularity | String | segment | Timestamp level: word, segment |
| temperature | Float | 0.0 | Sampling temperature (0.0-1.0) |

### Response Format

**Synchronous (JSON):**
```json
{
  "text": "Full transcription text",
  "language": "en",
  "language_probability": 0.98,
  "duration": 125.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, this is a test.",
      "confidence": 0.95,
      "words": [
        {
          "word": "Hello",
          "start": 0.0,
          "end": 0.5,
          "confidence": 0.96
        }
      ]
    }
  ],
  "processing_time": 12.3
}
```

**Asynchronous (Job Submission):**
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "message": "Transcription job accepted and queued for processing",
  "status_url": "/api/v1/status/abc-123-def-456",
  "estimated_time": 30
}
```

**Job Status:**
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-10-04T10:00:00Z",
  "completed_at": "2025-10-04T10:02:30Z",
  "result": {
    "text": "Full transcription text",
    "language": "en",
    "segments": []
  }
}
```

## Async Processing

### When to Use Async

Use asynchronous processing when:
- Files are longer than 10 minutes
- Processing multiple files concurrently
- Need immediate response to users
- Handling batch processing

### Architecture

```
Client → API → Redis Queue → Celery Worker → Whisper Engine
                    ↓
              Status Updates
```

### Workflow

1. **Submit Job**: Upload file and receive job ID
2. **Poll Status**: Check job progress periodically
3. **Retrieve Result**: Get transcription when completed
4. **Cleanup**: Delete job when no longer needed

### Example

```python
import requests
import time

def transcribe_async(file_path, model='base'):
    # Submit job
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/transcribe-async',
            files={'file': f},
            data={'model': model}
        )
    
    job_id = response.json()['job_id']
    
    # Wait for completion
    while True:
        status = requests.get(
            f'http://localhost:8000/api/v1/status/{job_id}'
        ).json()
        
        if status['status'] == 'completed':
            return status['result']
        elif status['status'] == 'failed':
            raise Exception(status.get('error', 'Unknown error'))
        
        time.sleep(2)

# Use it
result = transcribe_async('audio.mp3', model='base')
print(result['text'])
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Application
APP_NAME=transcription-service
APP_VERSION=1.0.0
LOG_LEVEL=INFO
DEBUG=false

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Whisper Configuration
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_MODEL_DIR=./models

# File Processing
MAX_FILE_SIZE=1073741824
MAX_DURATION=3600
TEMP_DIR=./temp
CLEANUP_INTERVAL=3600

# Security
ENABLE_RATE_LIMIT=true
RATE_LIMIT_PER_MINUTE=30

# Async Processing
ENABLE_ASYNC=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
JOB_RESULT_TTL=86400
MAX_JOB_RETRY=3
JOB_RETRY_DELAY=60
```

### Model Selection

| Model | Size | VRAM | Speed | Use Case |
|-------|------|------|-------|----------|
| tiny | 75MB | ~1GB | 32x | Real-time, low-resource |
| base | 142MB | ~1GB | 16x | Development, fast processing |
| small | 466MB | ~2GB | 6x | Good accuracy, reasonable speed |
| medium | 1.5GB | ~5GB | 2x | High accuracy for production |
| large-v3 | 2.9GB | ~10GB | 1x | Best accuracy, multilingual |

### Compute Types

- **int8**: Fastest, lowest memory, slight accuracy loss (CPU recommended)
- **float16**: Balanced speed/accuracy (GPU recommended)
- **float32**: Highest accuracy, slowest, most memory

## Development

### Project Structure

```
transcription-service/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── transcription.py
│   │   │   ├── health.py
│   │   │   ├── models.py
│   │   │   └── jobs.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── transcription/
│   │   │   ├── engine.py
│   │   │   ├── processor.py
│   │   │   └── formatter.py
│   │   ├── redis_client.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── models/
│   │   ├── requests.py
│   │   ├── responses.py
│   │   └── job.py
│   ├── services/
│   │   ├── transcription_service.py
│   │   └── job_service.py
│   ├── utils/
│   │   ├── file_handler.py
│   │   └── validators.py
│   ├── config.py
│   └── main.py
├── tasks/
│   ├── celery_app.py
│   └── transcription_tasks.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── scripts/
│   ├── download_models.py
│   ├── check_async.py
│   └── purge_queue.py
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.worker
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run async tests (requires Redis and Celery)
pytest tests/integration/test_async_api.py --run-async -v
```

### Code Quality

```bash
# Format code
black app/ tasks/ tests/

# Sort imports
isort app/ tasks/ tests/

# Lint
flake8 app/ tasks/ --max-line-length=100

# Type checking
mypy app/ tasks/
```

### Download Models

```bash
# Download single model
python scripts/download_models.py --model base

# Download multiple models
python scripts/download_models.py --model base --model small

# Download all models
python scripts/download_models.py --all

# Specify custom directory
python scripts/download_models.py --model base --model-dir /path/to/models
```

## Deployment

### Docker Compose

```bash
# Start all services
docker-compose up -d

# Scale workers
docker-compose up -d --scale transcription-worker=4

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Individual Services

```bash
# Start API only
docker-compose up -d transcription-api

# Start workers only
docker-compose up -d transcription-worker

# Start Redis only
docker-compose up -d redis

# Restart a service
docker-compose restart transcription-worker
```

### Production Deployment

```bash
# Build production image
docker build -t transcription-service:1.0.0 .

# Run with production settings
docker run -d \
  --name transcription-api \
  -p 8000:8000 \
  -e WHISPER_MODEL=small \
  -e WHISPER_DEVICE=cuda \
  -e ENABLE_ASYNC=true \
  -v $(pwd)/models:/models \
  transcription-service:1.0.0
```

## Monitoring

### Flower UI

Access Celery monitoring at http://localhost:5555

Features:
- View active workers
- Monitor task queue
- Track task execution
- View task history
- Real-time statistics

### Health Checks

```bash
# Main health check
curl http://localhost:8000/health

# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe
curl http://localhost:8000/health/ready

# Async infrastructure health
curl http://localhost:8000/health/async
```

### Check Infrastructure

```bash
# Check async components
python scripts/check_async.py

# Output:
# ✓ Redis is connected
# ✓ Celery workers active: 2
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f transcription-worker

# View last 100 lines
docker-compose logs --tail=100 transcription-api
```

## Testing

### Manual Testing

```bash
# Test synchronous endpoint
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@test.mp3" \
  -F "model=base"

# Test asynchronous endpoint
curl -X POST "http://localhost:8000/api/v1/transcribe-async" \
  -F "file=@test.mp3"
```

### Automated Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_validators.py -v

# Run specific test
pytest tests/unit/test_validators.py::TestFileExtensionValidation::test_valid_audio_extensions -v
```

### Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 -p test.mp3 -T multipart/form-data \
  http://localhost:8000/api/v1/transcribe

# Using locust (install first: pip install locust)
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose logs transcription-api

# Check if ports are available
lsof -i :8000
lsof -i :6379

# Restart services
docker-compose restart
```

#### Redis Connection Failed

```bash
# Check Redis status
docker-compose ps redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Restart Redis
docker-compose restart redis
```

#### Workers Not Processing Jobs

```bash
# Check worker status
docker-compose logs transcription-worker

# Check worker count
docker-compose ps | grep worker

# Restart workers
docker-compose restart transcription-worker

# Scale workers
docker-compose up -d --scale transcription-worker=4
```

#### Model Loading Fails

```bash
# Check available disk space
df -h

# Download models manually
python scripts/download_models.py --model base

# Check model directory permissions
ls -la models/

# Clear model cache
rm -rf models/*
```

#### High Memory Usage

```bash
# Check memory usage
docker stats

# Reduce worker concurrency
# Edit docker-compose.yml:
# command: celery -A tasks.celery_app worker --concurrency=1

# Use smaller model
# Set WHISPER_MODEL=tiny or WHISPER_MODEL=base
```

#### Jobs Stuck in Queue

```bash
# Check queue status
python scripts/check_async.py

# Purge queue
python scripts/purge_queue.py

# Restart workers
docker-compose restart transcription-worker
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart service
docker-compose restart transcription-api

# View detailed logs
docker-compose logs -f transcription-api
```

### Performance Issues

```bash
# Use GPU if available
export WHISPER_DEVICE=cuda
export WHISPER_COMPUTE_TYPE=float16

# Use smaller model for faster processing
export WHISPER_MODEL=tiny

# Increase worker concurrency
docker-compose up -d --scale transcription-worker=4

# Optimize file processing
export TEMP_DIR=/tmp/transcription  # Use faster storage
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)

## Acknowledgments

- OpenAI Whisper for the transcription model
- faster-whisper for optimized inference
- FastAPI for the web framework
- Celery for async task processing
