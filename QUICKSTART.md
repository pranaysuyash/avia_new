# Quick Start Guide

## 🚀 Getting Started with Video NER Application

This guide will help you get the Video NER application up and running quickly.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for React frontend)

## Quick Setup (Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd video-ner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# Database
POSTGRES_USER=transcription_user
POSTGRES_PASSWORD=development_password
POSTGRES_DB=transcription_app

# Security
JWT_SECRET_KEY=your-secret-key-here
STREAMLIT_SERVER_COOKIE_SECRET=your-cookie-secret

# API Keys
OPENAI_API_KEY=your-openai-api-key
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 3. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d db redis

# Run database migrations
make setup-db
make migrate
```

### 4. Start Services

#### Option A: Run Everything with Docker
```bash
make docker-run
```

#### Option B: Run Services Individually
```bash
# Terminal 1: API Server
make run-api

# Terminal 2: Streamlit App
make run-app

# Terminal 3: WebSocket Server (optional)
make run-websocket
```

### 5. Access the Application

- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health

## Quick Test

### 1. Test Transcription

```python
import requests

# Upload and transcribe audio
with open("test_audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/transcribe",
        files={"file": f},
        data={"language": "en"}
    )
    print(response.json())
```

### 2. Test with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Transcribe audio
curl -X POST http://localhost:8000/api/transcribe \
  -F "file=@test_audio.wav" \
  -F "language=en"
```

## Common Commands

```bash
# Run tests
make test

# Run specific test
pytest tests/test_auth_service.py -v

# Format code
make format

# Lint code
make lint

# Type checking
make type-check

# Clean up
make clean
```

## Docker Development

### Build Images
```bash
docker-compose build
```

### View Logs
```bash
docker-compose logs -f api
docker-compose logs -f app
```

### Reset Everything
```bash
docker-compose down -v
docker-compose up -d
```

## Project Structure

```
video-ner/
├── api/                    # FastAPI backend
│   ├── endpoints/         # API endpoints
│   ├── middleware/        # Custom middleware
│   └── auth_service.py    # Authentication
├── database/              # Database schemas and models
├── websocket/             # WebSocket server
├── monitoring/            # Logging and metrics
├── tests/                 # Test suite
├── desktop_app/           # Electron desktop app
├── mobile/                # React Native mobile app
└── docs/                  # Documentation
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code
- Add tests
- Update documentation

### 3. Run Tests
```bash
make test
make lint
```

### 4. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps db

# Check connection
docker-compose exec db psql -U transcription_user -d transcription_app
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -r api_requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
```

### Docker Issues
```bash
# Reset Docker
docker system prune -a
docker-compose down -v
docker-compose up -d --build
```

## API Authentication

### Get JWT Token
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "testuser", "password": "testpass"}
)
token = response.json()["access_token"]
```

### Use Token in Requests
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/transcripts",
    headers=headers
)
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read Documentation**: Check `docs/` directory
3. **Run Examples**: Try scripts in `examples/` directory
4. **Customize Settings**: Modify `config.py`
5. **Add Features**: See `SECURITY_AUDIT_COMPLETION.md` for roadmap

## Need Help?

- Check existing issues on GitHub
- Read the full documentation in `docs/`
- Contact the development team

---

Happy coding! 🎉