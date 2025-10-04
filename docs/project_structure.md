transcription-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── transcription.py
│   │       ├── health.py
│   │       └── models.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── transcription/
│   │       ├── __init__.py
│   │       ├── engine.py
│   │       ├── processor.py
│   │       └── formatter.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── transcription_service.py
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py
│       └── validators.py
├── tests/
├── docker/
├── scripts/
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md