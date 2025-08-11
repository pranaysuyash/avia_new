# Audio/Video Transcription Platform - Production Guide

[![CI/CD Pipeline](https://github.com/yourusername/transcription-platform/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/yourusername/transcription-platform/actions)
[![codecov](https://codecov.io/gh/yourusername/transcription-platform/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/transcription-platform)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

Enterprise-grade audio/video transcription and analysis platform with AI-powered features, built with React, FastAPI, and cutting-edge ML models.

### Key Features
- 🎙️ **Multi-format Support**: Audio (MP3, WAV, M4A) and Video (MP4, AVI, MOV) transcription
- 🤖 **AI-Powered**: Advanced NER, sentiment analysis, and content summarization
- 🌐 **Multi-language**: Support for 50+ languages with automatic detection
- 📱 **PWA**: Offline support with service workers
- 🔐 **Enterprise Security**: JWT with refresh tokens, RBAC, audit logging
- 📊 **Analytics**: Real-time metrics and performance monitoring
- 🔄 **Real-time Updates**: WebSocket support for live transcription
- 🎨 **Modern UI**: React with Material-UI and responsive design

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Security](#security)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend"
        A[React App] --> B[React Query]
        A --> C[Service Worker]
        A --> D[Sentry]
    end
    
    subgraph "Backend"
        E[FastAPI] --> F[PostgreSQL]
        E --> G[Redis]
        E --> H[Celery]
        E --> I[ML Models]
    end
    
    subgraph "External Services"
        J[OpenAI Whisper]
        K[AWS S3]
        L[Sentry]
    end
    
    A -->|REST/WS| E
    E --> J
    E --> K
    D --> L
    E --> L
```

### Tech Stack

#### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: React Query (TanStack Query)
- **UI Library**: Material-UI v5
- **Build Tool**: Create React App (Webpack)
- **Testing**: Jest, React Testing Library, Playwright
- **PWA**: Service Workers with Workbox
- **Error Tracking**: Sentry
- **Performance**: Web Vitals monitoring

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 14+ with SQLAlchemy ORM
- **Cache**: Redis 7+
- **Queue**: Celery with Redis broker
- **ML Models**: 
  - Whisper (transcription)
  - SpaCy (NER)
  - Transformers (sentiment, summarization)
- **Authentication**: JWT with refresh tokens
- **API Docs**: OpenAPI/Swagger

## 📦 Prerequisites

### System Requirements
- Node.js 18+ and npm 9+
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- FFmpeg (for media processing)
- 8GB+ RAM recommended
- 10GB+ free disk space

### Development Tools
- Git
- Docker & Docker Compose (optional)
- VS Code or preferred IDE

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/transcription-platform.git
cd transcription-platform
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download ML models
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm

# Setup database
createdb transcription_db
alembic upgrade head

# Create .env file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm ci

# Create .env file
cp .env.example .env.local
# Edit .env.local with your configuration

# Install Playwright for E2E tests
npx playwright install
```

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/transcription_db
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Sentry
SENTRY_DSN=your-sentry-dsn

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Feature Flags
ENABLE_ML_MODELS=true
ENABLE_WEBSOCKETS=true
ENABLE_RATE_LIMITING=true
```

#### Frontend (.env.local)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_SENTRY_DSN=your-sentry-dsn
REACT_APP_GOOGLE_ANALYTICS_ID=your-ga-id
```

## 💻 Development

### Starting Development Servers

#### Backend
```bash
# Start API server with hot reload
python run_api.py

# Or with uvicorn directly
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (in separate terminal)
celery -A celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A celery_app beat --loglevel=info
```

#### Frontend
```bash
cd frontend
npm start  # Starts on http://localhost:3000
```

### Development with Docker

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests with coverage
pytest -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run with parallel execution
pytest -n auto

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Frontend Tests
```bash
cd frontend

# Unit tests
npm test

# Unit tests with coverage
npm test -- --coverage

# E2E tests
npm run test:e2e

# E2E tests with UI
npm run test:e2e:ui

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🚀 Deployment

### Production Build

#### Frontend
```bash
cd frontend
npm run build

# Output in frontend/build/
# Serve with any static file server
```

#### Backend
```bash
# Build Docker image
docker build -t transcription-api .

# Or use production requirements
pip install -r requirements-prod.txt
```

### Docker Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: transcription-api:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    command: gunicorn api.app:app -w 4 -k uvicorn.workers.UvicornWorker

  frontend:
    image: nginx:alpine
    volumes:
      - ./frontend/build:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=transcription_db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transcription-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: transcription-api
  template:
    metadata:
      labels:
        app: transcription-api
    spec:
      containers:
      - name: api
        image: transcription-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Cloud Deployment Options

#### AWS
```bash
# Using AWS Copilot
copilot app init transcription
copilot env init --name production
copilot svc deploy --name api --env production
```

#### Google Cloud
```bash
# Using Cloud Run
gcloud run deploy transcription-api \
  --image gcr.io/project-id/transcription-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku
```bash
# Create app
heroku create transcription-platform

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

# Deploy
git push heroku main
```

## 📊 Monitoring

### Health Checks
- API Health: `GET /api/health`
- Database Health: `GET /api/health/db`
- Redis Health: `GET /api/health/redis`

### Metrics Endpoints
- Prometheus metrics: `GET /metrics`
- Custom metrics: `GET /api/metrics`

### Logging
```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

### Performance Monitoring
- Frontend: Web Vitals (LCP, FID, CLS, TTFB)
- Backend: APM with Datadog/New Relic
- Database: pg_stat_statements
- Redis: redis-cli INFO

## 🔒 Security

### Security Headers
```python
# Implemented in api/middleware/security.py
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'"
}
```

### Rate Limiting
```python
# Configured per endpoint
rate_limits = {
    "default": "100/hour",
    "auth": "5/minute",
    "upload": "10/hour",
    "api": "1000/hour"
}
```

### Authentication Flow
1. User login → JWT access token (30 min) + refresh token (7 days)
2. Access token expires → Use refresh token to get new access token
3. Refresh token expires → User must login again

### CORS Configuration
```python
origins = [
    "http://localhost:3000",
    "https://yourdomain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📚 API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Authentication
```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
```

#### Transcription
```http
POST /api/transcriptions/upload
GET /api/transcriptions
GET /api/transcriptions/{id}
DELETE /api/transcriptions/{id}
GET /api/transcriptions/{id}/export
```

#### Real-time
```websocket
WS /ws/transcription/{session_id}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string
psql $DATABASE_URL

# Reset database
dropdb transcription_db
createdb transcription_db
alembic upgrade head
```

#### 2. Redis Connection Error
```bash
# Check Redis is running
redis-cli ping

# Clear Redis cache
redis-cli FLUSHALL
```

#### 3. ML Model Loading Error
```bash
# Re-download models
python -m spacy download en_core_web_sm --force

# Check model path
python -c "import spacy; print(spacy.util.get_data_path())"
```

#### 4. Frontend Build Error
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Style
- Backend: Black, isort, flake8, mypy
- Frontend: ESLint, Prettier
- Commits: Conventional Commits

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- OpenAI for Whisper model
- Hugging Face for transformer models
- All open-source contributors

## 📞 Support

- Documentation: [docs.transcription-platform.com](https://docs.transcription-platform.com)
- Issues: [GitHub Issues](https://github.com/yourusername/transcription-platform/issues)
- Email: support@transcription-platform.com
- Discord: [Join our community](https://discord.gg/transcription)

---

Built with ❤️ by the Transcription Platform Team