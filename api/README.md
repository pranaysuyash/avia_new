# Audio/Video Transcription REST API

A high-performance REST API built with FastAPI for audio/video transcription with collaboration features.

## Features

- 🔐 **JWT Authentication** with refresh tokens
- 🚀 **High Performance** with async/await
- 📝 **Auto Documentation** via OpenAPI/Swagger
- 🔄 **Real-time Updates** via WebSocket (coming soon)
- 🛡️ **Rate Limiting** to prevent abuse
- 📊 **Comprehensive Logging** and monitoring
- 🔒 **Security Headers** and CORS support
- 💼 **Team Collaboration** features
- 📤 **File Upload** with background processing

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r api/requirements.txt

# Run the API server
python run_api.py
```

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Optional Services
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your-key-here
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## Authentication

### Register a new user

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using the token

Include the token in the Authorization header:

```bash
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Core Endpoints

### Transcripts

#### List transcripts
```bash
GET /api/v1/transcripts/?page=1&per_page=20
```

#### Create transcript
```bash
POST /api/v1/transcripts/
{
  "title": "Meeting Notes",
  "content": "Transcript content here...",
  "language": "en",
  "team_id": null
}
```

#### Get transcript
```bash
GET /api/v1/transcripts/{transcript_id}
```

#### Update transcript
```bash
PUT /api/v1/transcripts/{transcript_id}
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

#### Delete transcript
```bash
DELETE /api/v1/transcripts/{transcript_id}
```

#### Share transcript
```bash
POST /api/v1/transcripts/{transcript_id}/share
{
  "permission": "view",
  "expires_at": "2024-12-31T23:59:59",
  "password": "optional_password"
}
```

### Teams

#### List teams
```bash
GET /api/v1/teams/
```

#### Create team
```bash
POST /api/v1/teams/
{
  "name": "Engineering Team",
  "description": "Core development team"
}
```

#### Add team member
```bash
POST /api/v1/teams/{team_id}/members
{
  "email": "newmember@example.com",
  "role": "member"
}
```

### Media Processing

#### Upload file
```bash
POST /api/v1/media/upload
Content-Type: multipart/form-data

file: audio_file.mp3
language: en
model: base
```

#### Check job status
```bash
GET /api/v1/media/status/{job_id}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 60,
  "result": null,
  "created_at": "2024-01-01T00:00:00",
  "completed_at": null
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default**: 100 requests per minute per user
- **Headers**: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- **Status**: 429 Too Many Requests when exceeded

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "details": {
    "field": "additional_info"
  }
}
```

Common error codes:
- `AUTHENTICATION_ERROR`: Invalid credentials
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid input
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

## Security

The API implements multiple security layers:

1. **Authentication**: JWT with refresh tokens
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Prevent abuse
4. **Input Validation**: Pydantic models
5. **SQL Injection**: Parameterized queries
6. **XSS Prevention**: Output encoding
7. **CORS**: Configurable origins
8. **Security Headers**: HSTS, CSP, etc.

## Testing

### Run tests
```bash
pytest api/tests/
```

### Test with curl
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Test with Python client
```bash
python test_api.py
```

## Development

### Project Structure
```
api/
├── __init__.py       # Package initialization
├── app.py           # FastAPI application
├── auth.py          # Authentication endpoints
├── transcripts.py   # Transcript endpoints
├── teams.py         # Team endpoints
├── media.py         # Media processing endpoints
├── users.py         # User management endpoints
├── middleware.py    # Custom middleware
├── exceptions.py    # Custom exceptions
├── requirements.txt # Dependencies
└── README.md       # This file
```

### Adding new endpoints

1. Create a new router file (e.g., `analytics.py`)
2. Define Pydantic models for request/response
3. Implement endpoint functions
4. Add router to main app
5. Update documentation

Example:
```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

analytics_router = APIRouter()

class StatsResponse(BaseModel):
    total_transcripts: int
    total_users: int

@analytics_router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(get_current_user)):
    # Implementation here
    return StatsResponse(...)
```

## Deployment

### Using Uvicorn (Development)
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Using Gunicorn (Production)
```bash
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Docker Compose
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/dbname
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=dbname
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass

  redis:
    image: redis:7
```

## Monitoring

### Health Check
```bash
GET /api/v1/health
```

### Metrics (Prometheus format)
```bash
GET /api/v1/metrics
```

### Logging
- Application logs: `app.log`
- Access logs: `access.log`
- Error logs: `error.log`

## Performance

### Optimization Tips
1. Use connection pooling for database
2. Implement caching with Redis
3. Use CDN for static assets
4. Enable response compression
5. Optimize database queries
6. Use background tasks for heavy processing

### Benchmarking
```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/transcripts/

# Using wrk
wrk -t12 -c400 -d30s --latency http://localhost:8000/api/v1/health
```

## Support

For issues or questions:
1. Check the API documentation
2. Review error messages
3. Check server logs
4. Open an issue on GitHub

## License

MIT License - see LICENSE file for details