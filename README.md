# Whisper Transcription Microservice

A high-performance Python microservice for audio and video transcription using OpenAI's Whisper model.

## Features

- 🎯 Accurate speech-to-text transcription
- 🌍 Multi-language support with automatic detection
- 📝 Multiple output formats (JSON, Text, SRT, VTT)
- ⚡ Fast processing with faster-whisper
- 🎬 Support for audio and video files
- 🔒 Secure file handling
- 📊 Built-in health checks and monitoring
- 🐳 Docker ready

## Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd transcription-service
```

## Async Processing

### Starting Services

```bash
# Start all services (API + Redis + Workers + Flower)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f transcription-worker
```

### Using Async API

See [docs/ASYNC_GUIDE.md](docs/ASYNC_GUIDE.md) for complete async usage guide.

Quick example:
```python
import requests
import time

# Submit job
response = requests.post(
    "http://localhost:8000/api/v1/transcribe-async",
    files={"file": open("audio.mp3", "rb")},
    data={"model": "base", "language": "en"}
)

job_id = response.json()["job_id"]

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8000/api/v1/status/{job_id}").json()
    
    if status["status"] == "completed":
        print(status["result"]["text"])
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error']}")
        break
    
    print(f"Progress: {status.get('progress', 0)}%")
    time.sleep(2)
```

### Monitoring

Access Flower UI for real-time monitoring:
- URL: http://localhost:5555
- View active workers, tasks, and queue status

### Troubleshooting

Check async infrastructure:
```bash
python scripts/check_async.py
```

Purge stuck jobs:
```bash
python scripts/purge_queue.py
```
```

## Summary

🎉 **Phase 2 Implementation Complete!**

You now have:

✅ **Redis Integration** - Job storage and queue management  
✅ **Celery Workers** - Background task processing  
✅ **Async Endpoints** - `/transcribe-async`, `/status/{job_id}`, `/jobs`  
✅ **Job Management** - Create, track, cancel, delete jobs  
✅ **Progress Tracking** - Real-time progress updates  
✅ **Multi-container Setup** - Docker Compose with API, Workers, Redis, Flower  
✅ **Monitoring** - Flower UI for Celery monitoring  
✅ **Health Checks** - Async infrastructure health endpoints  
✅ **Management Scripts** - Worker management and queue maintenance  
✅ **Testing** - Integration tests for async features  
✅ **Documentation** - Complete async usage guide  

### Next Steps to Deploy:

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Verify infrastructure**:
```bash
python scripts/check_async.py
```

4. **Test async endpoint**:
```bash
curl -X POST "http://localhost:8000/api/v1/transcribe-async" \
  -F "file=@test.mp3"
```

5. **Monitor with Flower**:
```
Open http://localhost:5555
```