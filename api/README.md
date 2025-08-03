# Transcription Platform API

Production-ready FastAPI backend for the audio/video transcription platform with enterprise collaboration features.

## Features

- 🔐 **JWT Authentication** with refresh tokens
- 👥 **Team Collaboration** with role-based permissions
- 🔑 **API Key Management** for programmatic access
- 📄 **File Upload & Processing** for audio/video transcription
- 🔄 **Real-time Updates** via WebSocket
- 📊 **Usage Analytics** and quota management
- 🛡️ **Security** with rate limiting and CORS
- 📚 **Auto-generated API Documentation** (OpenAPI/Swagger)

## Quick Start

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run the API

```bash
# Development mode with auto-reload
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/logout` - Logout current user
- `POST /api/auth/refresh` - Refresh access token

### User Management
- `GET /api/users/profile` - Get user profile
- `PUT /api/users/profile` - Update profile
- `POST /api/users/api-keys` - Create API key
- `GET /api/users/api-keys` - List API keys
- `DELETE /api/users/api-keys/{id}` - Delete API key

### Transcriptions
- `POST /api/transcriptions/upload` - Upload file for transcription
- `GET /api/transcriptions` - List transcriptions
- `GET /api/transcriptions/{id}` - Get transcription details
- `DELETE /api/transcriptions/{id}` - Delete transcription

### Teams
- `POST /api/teams` - Create team
- `GET /api/teams` - List user's teams
- `GET /api/teams/{id}` - Get team details
- `POST /api/teams/{id}/members` - Invite team member
- `DELETE /api/teams/{id}/members/{userId}` - Remove member

### WebSocket
- `WS /ws/collaboration/{sessionId}` - Real-time collaboration

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api

# Run specific test file
pytest api/test_auth.py -v
```

## Database Migrations

Using Alembic for database migrations:

```bash
# Initialize migrations (first time only)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

See `.env.example` for all configuration options. Key variables:

- `DATABASE_URL` - Database connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens (min 32 chars)
- `ALLOWED_ORIGINS` - CORS allowed origins
- `ENVIRONMENT` - development/staging/production

## API Authentication

### Bearer Token (JWT)

Include the JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/users/profile
```

### API Key

Include the API key in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/api/transcriptions
```

## WebSocket Events

Connect to WebSocket for real-time collaboration:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/collaboration/session123');

// Send cursor position
ws.send(JSON.stringify({
  type: 'cursor',
  userId: 'user123',
  position: { line: 10, column: 5 }
}));

// Send content change
ws.send(JSON.stringify({
  type: 'content',
  userId: 'user123',
  change: { type: 'insert', position: 100, text: 'Hello' }
}));
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Set a strong JWT_SECRET_KEY** (minimum 32 characters)
3. **Configure CORS properly** for your frontend domains
4. **Enable rate limiting** to prevent abuse
5. **Use environment variables** for sensitive configuration
6. **Regularly update dependencies** for security patches

## Troubleshooting

### Database Connection Issues
- Ensure DATABASE_URL is correctly formatted
- Check database server is running
- Verify network connectivity

### Authentication Errors
- Verify JWT_SECRET_KEY is set
- Check token expiration
- Ensure CORS is configured for your frontend

### File Upload Issues
- Check file size limits
- Verify allowed file extensions
- Ensure storage permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your License Here]