# Audio/Video Transcription REST API Documentation

## Overview

The Transcription API provides a comprehensive REST interface for audio/video transcription, entity extraction, content analysis, and export functionality. The API supports both JWT token and API key authentication.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

The API supports two authentication methods:

### 1. JWT Token Authentication
Use for interactive applications and user sessions.

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/v1/transcription/history
```

### 2. API Key Authentication
Use for server-to-server communication and automation.

```bash
# Generate API key (requires JWT token)
curl -X POST http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Production API key"}'

# Use API key in requests
curl -H "Authorization: ApiKey YOUR_API_KEY" \
  http://localhost:8000/api/v1/transcription/history
```

## Rate Limiting

- **Default limit**: 1000 requests per hour per user
- **Burst limit**: 50 requests per minute
- **Headers returned**:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## Endpoints

### General Endpoints

#### Health Check
```http
GET /health
```

Returns API health status and service availability.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "security": "operational",
    "database": "operational",
    "ai_services": "operational"
  }
}
```

#### API Information
```http
GET /
```

Returns API information and available endpoints.

### Authentication Endpoints

#### Login
```http
POST /api/v1/auth/login
```

Authenticate user and receive JWT token.

**Request Body**:
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Authentication successful",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user_id": "john_doe",
    "expires_at": "2025-01-09T10:00:00Z"
  }
}
```

#### Generate API Key
```http
POST /api/v1/auth/api-key
Authorization: Bearer {token}
```

Generate a new API key for programmatic access.

**Request Body**:
```json
{
  "description": "Production server key"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

Get information about the authenticated user.

### Transcription Endpoints

#### Upload Audio/Video File
```http
POST /api/v1/transcription/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

Upload a file for transcription processing.

**Form Data**:
- `file`: Audio/video file (required)

**Supported Formats**:
- Audio: MP3, WAV, M4A, FLAC
- Video: MP4, AVI, MOV, MKV, WebM
- Max size: 2GB

**Response**:
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "data": {
    "file_id": "upload_john_doe_1704700000",
    "file_name": "interview.mp3",
    "file_size": 25600000,
    "content_type": "audio/mpeg"
  }
}
```

#### Process Transcription
```http
POST /api/v1/transcription/process?file_id={file_id}
Authorization: Bearer {token}
```

Process an uploaded file for transcription.

**Request Body**:
```json
{
  "use_api": false,
  "language": "en",
  "model": "base",
  "enable_diarization": true,
  "extract_entities": true
}
```

**Parameters**:
- `use_api`: Use OpenAI API (true) or local Whisper model (false)
- `language`: Language code or "auto" for detection
- `model`: Whisper model size (tiny, base, small, medium, large)
- `enable_diarization`: Enable speaker identification
- `extract_entities`: Extract named entities

**Response**:
```json
{
  "success": true,
  "message": "Transcription completed successfully",
  "data": {
    "transcript_id": "transcript_john_doe_1704700000",
    "text": "This is the transcribed text...",
    "language": "en",
    "duration": 300.5,
    "word_count": 1250,
    "entities": [
      {
        "text": "John Smith",
        "label": "PERSON",
        "start": 10,
        "end": 20,
        "confidence": 0.95
      }
    ],
    "speakers": [
      {
        "speaker_id": "SPEAKER_00",
        "start_time": 0.0,
        "end_time": 45.3,
        "text": "Hello, this is speaker one...",
        "confidence": 0.87
      }
    ],
    "confidence": 0.92,
    "processing_time": 12.5,
    "created_at": "2025-01-08T10:00:00Z"
  }
}
```

#### Get Transcription Status
```http
GET /api/v1/transcription/status/{transcript_id}
Authorization: Bearer {token}
```

Get the status and details of a specific transcription.

#### Get Transcription History
```http
GET /api/v1/transcription/history?limit=10&offset=0
Authorization: Bearer {token}
```

Get user's transcription history with pagination.

**Query Parameters**:
- `limit`: Number of results per page (1-100, default: 10)
- `offset`: Number of results to skip (default: 0)

### Search Endpoints

#### Search Transcriptions
```http
POST /api/v1/search/query
Authorization: Bearer {token}
```

Search through transcriptions using advanced search capabilities.

**Request Body**:
```json
{
  "query": "machine learning",
  "limit": 20,
  "offset": 0,
  "filters": {
    "language": "en",
    "date_from": "2025-01-01",
    "date_to": "2025-01-31"
  },
  "sort_by": "relevance",
  "include_snippets": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Search completed",
  "data": {
    "results": [
      {
        "transcript_id": "transcript_123",
        "title": "AI Conference Talk",
        "snippet": "...discussing machine learning algorithms...",
        "score": 0.95,
        "created_at": "2025-01-05T14:30:00Z",
        "duration": 1800,
        "word_count": 3500
      }
    ],
    "total_count": 42,
    "page": 1,
    "per_page": 20
  }
}
```

### Export Endpoints

#### Generate Export
```http
POST /api/v1/export/generate
Authorization: Bearer {token}
```

Export transcription in various formats.

**Request Body**:
```json
{
  "transcript_id": "transcript_123",
  "format": "pdf",
  "include_metadata": true,
  "include_entities": true,
  "include_speakers": true,
  "custom_template": null
}
```

**Supported Formats**:
- JSON, CSV, PDF, DOCX, TXT, Markdown, HTML, XML, XLSX

**Response**:
```json
{
  "success": true,
  "message": "Export generated successfully",
  "data": {
    "download_url": "/api/v1/export/download/export_123.pdf",
    "file_name": "transcript_export.pdf",
    "file_size": 256000,
    "expires_at": "2025-01-09T10:00:00Z"
  }
}
```

### Content Insights Endpoints

#### Generate Insights
```http
POST /api/v1/insights/analyze
Authorization: Bearer {token}
```

Generate AI-powered insights from transcription.

**Request Body**:
```json
{
  "transcript_id": "transcript_123",
  "analysis_types": ["summary", "sentiment", "topics", "key_moments"]
}
```

**Available Analysis Types**:
- `summary`: Generate content summary
- `sentiment`: Analyze sentiment
- `topics`: Extract main topics
- `speakers`: Analyze speaker patterns
- `key_moments`: Identify important moments
- `action_items`: Extract action items

### Video Processing Endpoints

#### Process Video
```http
POST /api/v1/video/process?file_id={file_id}
Authorization: Bearer {token}
```

Process video for frame extraction and scene detection.

**Request Body**:
```json
{
  "extract_frames": true,
  "detect_scenes": true,
  "generate_thumbnails": true,
  "keyframe_interval": 10.0,
  "thumbnail_count": 5
}
```

### Security Endpoints

#### Get Security Status
```http
GET /api/v1/security/status
Authorization: Bearer {token}
```

Get security status and audit information (admin only).

#### List API Keys
```http
GET /api/v1/auth/api-keys
Authorization: Bearer {token}
```

List user's API keys (without the actual keys).

#### Revoke API Key
```http
DELETE /api/v1/auth/api-key/{key_id}
Authorization: Bearer {token}
```

Revoke a specific API key.

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": "Detailed error message",
  "status_code": 400,
  "timestamp": "2025-01-08T10:00:00Z"
}
```

### Common Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `413` - Payload Too Large
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## WebSocket Events

For real-time updates, connect to the WebSocket endpoint:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

### Event Types

- `transcription.started`
- `transcription.progress`
- `transcription.completed`
- `transcription.failed`

## SDK Examples

### Python
```python
import requests

class TranscriptionAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"ApiKey {api_key}"}
    
    def upload_file(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/transcription/upload",
                files=files,
                headers=self.headers
            )
        return response.json()
```

### JavaScript
```javascript
class TranscriptionAPI {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/transcription/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `ApiKey ${this.apiKey}`
      },
      body: formData
    });

    return response.json();
  }
}
```

## Best Practices

1. **Authentication**
   - Use JWT tokens for user sessions
   - Use API keys for server-to-server communication
   - Rotate API keys regularly

2. **File Uploads**
   - Compress large files before upload
   - Use appropriate chunk sizes for streaming
   - Handle upload failures with retry logic

3. **Rate Limiting**
   - Implement exponential backoff for retries
   - Monitor rate limit headers
   - Cache responses when possible

4. **Error Handling**
   - Always check response status codes
   - Handle network timeouts
   - Implement proper error logging

5. **Performance**
   - Use pagination for list endpoints
   - Request only needed fields
   - Implement client-side caching

## Support

For API support, bug reports, or feature requests:
- Email: api-support@transcription-platform.com
- Documentation: https://docs.transcription-platform.com
- Status Page: https://status.transcription-platform.com