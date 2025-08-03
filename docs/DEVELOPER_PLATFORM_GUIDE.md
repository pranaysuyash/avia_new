# Developer Platform & Public API Guide

## Overview

The Developer Platform provides comprehensive API access to the Transcription Platform, enabling third-party developers to integrate transcription capabilities into their applications. It includes API key management, SDKs, webhooks, and extensive documentation.

## Key Features

### 1. API Key Management
- **Secure Key Generation**: Strong, unique API keys with prefix identification
- **Granular Scopes**: Fine-grained permissions for different API operations
- **Rate Limiting**: Configurable rate limits per key
- **IP Restrictions**: Optional IP allowlisting
- **Usage Tracking**: Detailed usage statistics and analytics

### 2. RESTful API
- **Version**: v1 (stable)
- **Base URL**: `https://api.example.com/v1`
- **Authentication**: Bearer token (API key)
- **Format**: JSON request/response
- **Rate Limits**: Based on subscription tier

### 3. SDKs
- **Python SDK**: Full-featured client library with async support
- **JavaScript/TypeScript SDK**: Browser and Node.js compatible
- **Community SDKs**: Ruby, Go, PHP, Java, C#/.NET

### 4. Webhooks
- **Real-time Events**: Instant notifications for transcript status changes
- **Reliable Delivery**: Automatic retries with exponential backoff
- **Security**: HMAC signature verification
- **Event Types**: Comprehensive event catalog

### 5. Developer Portal
- **Interactive Documentation**: Live API testing
- **Code Examples**: Language-specific examples
- **Usage Analytics**: Real-time usage monitoring
- **API Key Management**: Self-service key management

## Architecture

### API Authentication Flow

```
┌─────────┐     ┌────────────┐     ┌──────────────┐
│ Client  │────▶│ API Auth   │────▶│ API Service  │
└─────────┘     │ Middleware │     └──────────────┘
                └────────────┘              │
                      │                     ▼
                      ▼              ┌──────────────┐
                ┌────────────┐       │   Database   │
                │Rate Limiter│       └──────────────┘
                └────────────┘
```

### Components

1. **API Key Service** (`services/api_key_service.py`)
   - Key generation and validation
   - Scope management
   - Usage tracking
   - Rate limit enforcement

2. **API Auth Middleware** (`api/middleware/api_auth_middleware.py`)
   - Request authentication
   - Scope verification
   - Rate limiting
   - Usage logging

3. **Developer Endpoints** (`api/endpoints/developers.py`)
   - API key CRUD operations
   - Webhook management
   - Documentation endpoints

4. **Webhook Service** (`services/webhook_service.py`)
   - Event delivery
   - Retry logic
   - Signature generation
   - Delivery logging

5. **Developer Portal UI** (`streamlit_developer_portal.py`)
   - Web interface for developers
   - API key management
   - Documentation browser
   - Usage analytics

## API Reference

### Authentication

All API requests must include an API key:

```http
Authorization: Bearer sk_live_your_api_key_here
```

Or using the X-API-Key header:

```http
X-API-Key: sk_live_your_api_key_here
```

### Core Endpoints

#### Create Transcript

```http
POST /v1/transcripts
Content-Type: application/json

{
  "audio_url": "https://example.com/audio.mp3",
  "language": "en",
  "enable_diarization": true,
  "max_speakers": 3,
  "webhook_url": "https://your-app.com/webhook"
}
```

Response:
```json
{
  "id": "tr_abc123",
  "status": "processing",
  "created_at": "2024-01-20T12:00:00Z"
}
```

#### Get Transcript

```http
GET /v1/transcripts/{transcript_id}
```

Response:
```json
{
  "id": "tr_abc123",
  "status": "completed",
  "text": "This is the transcribed text...",
  "duration": 300.5,
  "speakers": [...],
  "segments": [...]
}
```

### API Scopes

| Scope | Description |
|-------|-------------|
| `transcripts:read` | Read transcript data |
| `transcripts:write` | Create and update transcripts |
| `transcripts:delete` | Delete transcripts |
| `analytics:read` | View usage analytics |
| `teams:read` | View team information |
| `teams:write` | Manage teams |
| `webhooks:write` | Manage webhooks |
| `account:read` | View account details |

### Rate Limits

Rate limits are enforced per API key and vary by plan:

| Plan | Per Minute | Per Hour | Per Day |
|------|------------|----------|---------|
| Free | 60 | 1,000 | 10,000 |
| Basic | 120 | 5,000 | 50,000 |
| Pro | 300 | 20,000 | 200,000 |
| Enterprise | Custom | Custom | Custom |

Rate limit headers:
- `X-RateLimit-Limit-*`: Current limits
- `X-RateLimit-Remaining-*`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp for reset

### Error Handling

Standard HTTP status codes with detailed error messages:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded",
  "details": {
    "limit": 60,
    "remaining": 0,
    "reset_in": 45
  }
}
```

Error codes:
- `unauthorized`: Invalid or missing API key
- `insufficient_scope`: Missing required scope
- `rate_limit_exceeded`: Rate limit hit
- `validation_error`: Invalid request data
- `not_found`: Resource not found
- `internal_error`: Server error

## SDK Usage

### Python SDK

Installation:
```bash
pip install transcription-platform
```

Basic usage:
```python
from transcription_platform import TranscriptionClient

client = TranscriptionClient(api_key="YOUR_API_KEY")

# Create transcript
transcript = client.create_transcript(
    audio_url="https://example.com/audio.mp3",
    language="en",
    enable_diarization=True
)

# Wait for completion
completed = client.wait_for_completion(transcript.id)
print(completed.text)
```

### JavaScript/TypeScript SDK

Installation:
```bash
npm install @transcription/sdk
```

Basic usage:
```typescript
import { TranscriptionClient } from '@transcription/sdk';

const client = new TranscriptionClient('YOUR_API_KEY');

// Create transcript
const transcript = await client.createTranscript({
  audioUrl: 'https://example.com/audio.mp3',
  language: 'en',
  enableDiarization: true
});

// Wait for completion
const completed = await client.waitForCompletion(transcript.id);
console.log(completed.text);
```

## Webhooks

### Configuration

Create a webhook endpoint:

```http
POST /v1/developers/webhooks
Content-Type: application/json

{
  "name": "Production Webhook",
  "url": "https://your-app.com/webhook",
  "events": ["transcript.completed", "transcript.failed"],
  "max_retries": 3,
  "timeout_seconds": 30
}
```

### Event Structure

```json
{
  "id": "evt_123",
  "type": "transcript.completed",
  "created": "2024-01-20T12:00:00Z",
  "data": {
    "transcript_id": "tr_abc123",
    "duration": 300.5,
    "word_count": 1523
  }
}
```

### Signature Verification

Verify webhook signatures for security:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
```

### Event Types

- **Transcript Events**
  - `transcript.created`: New transcript created
  - `transcript.completed`: Processing completed
  - `transcript.failed`: Processing failed
  - `transcript.updated`: Transcript updated
  - `transcript.deleted`: Transcript deleted

- **Team Events**
  - `team.member.added`: Member added to team
  - `team.member.removed`: Member removed

- **Usage Events**
  - `usage.limit.warning`: 80% of limit reached
  - `usage.limit.exceeded`: Limit exceeded

## Best Practices

### 1. API Key Security
- Never expose API keys in client-side code
- Use environment variables for storage
- Rotate keys regularly
- Use IP restrictions for production

### 2. Error Handling
- Implement exponential backoff for retries
- Handle rate limits gracefully
- Log errors for debugging
- Provide user-friendly error messages

### 3. Performance
- Use webhooks for async operations
- Batch requests when possible
- Cache responses appropriately
- Monitor API usage

### 4. Webhook Implementation
- Respond quickly (< 5 seconds)
- Process events asynchronously
- Verify signatures
- Handle duplicate events

## Examples

### Batch Processing

```python
import asyncio
from transcription_platform import TranscriptionClient

async def process_batch(audio_urls):
    client = TranscriptionClient(api_key="YOUR_API_KEY")
    
    # Create transcripts
    tasks = []
    for url in audio_urls:
        transcript = await client.create_transcript(audio_url=url)
        tasks.append(client.wait_for_completion(transcript.id))
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks)
    
    return results
```

### Webhook Handler

```python
from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    if not verify_signature(request.data, signature):
        return 'Unauthorized', 401
    
    # Parse event
    event = json.loads(request.data)
    
    # Handle event
    if event['type'] == 'transcript.completed':
        process_completed_transcript(event['data'])
    
    return 'OK', 200
```

### Export Formats

```javascript
// Export transcript in different formats
const client = new TranscriptionClient('YOUR_API_KEY');

// Plain text
const text = await client.exportTranscript(transcriptId, {
  format: 'txt'
});

// SRT subtitles
const srt = await client.exportTranscript(transcriptId, {
  format: 'srt',
  includeSpeakers: false
});

// JSON with all data
const json = await client.exportTranscript(transcriptId, {
  format: 'json'
});
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key validity
   - Ensure correct header format
   - Verify key hasn't expired

2. **403 Forbidden**
   - Check required scopes
   - Verify IP restrictions
   - Ensure resource ownership

3. **429 Rate Limited**
   - Check rate limit headers
   - Implement backoff strategy
   - Consider upgrading plan

4. **Webhook Delivery Failures**
   - Verify endpoint accessibility
   - Check response time
   - Review error logs

### Debug Mode

Enable debug logging in SDKs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

```javascript
const client = new TranscriptionClient('YOUR_API_KEY', {
  debug: true
});
```

## Migration Guide

### From v0 to v1

1. **Authentication**: Change from query parameter to header
2. **Endpoints**: Update base URL to `/v1`
3. **Response Format**: New standardized format
4. **Error Codes**: Updated error code system

## Support

- **Documentation**: https://docs.example.com/api
- **API Status**: https://status.example.com
- **Support Email**: api-support@example.com
- **Community Forum**: https://forum.example.com
- **GitHub**: https://github.com/transcription-platform