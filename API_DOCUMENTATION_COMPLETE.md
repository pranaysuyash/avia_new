# Complete API Documentation
## Video NER Platform - All Endpoints Reference

### Table of Contents
1. [Authentication & Authorization](#authentication--authorization)
2. [Phase 1: Core Features](#phase-1-core-features)
3. [Phase 2: Advanced Features](#phase-2-advanced-features)  
4. [Phase 3: Platform-Specific Features](#phase-3-platform-specific-features)
5. [Error Handling](#error-handling)
6. [Rate Limiting & Quotas](#rate-limiting--quotas)
7. [WebSocket Endpoints](#websocket-endpoints)

---

## Authentication & Authorization

All API endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Auth Endpoints

#### `POST /api/v1/auth/login`
**Description:** User login  
**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "token": "eyJ0eXAiOiJKV1Q...",
    "refresh_token": "refresh_token_here",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "role": "user"
    }
  }
}
```

#### `POST /api/v1/auth/refresh`
**Description:** Refresh access token  
**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

---

## Phase 1: Core Features

### Entity Extraction API

#### `POST /api/v1/entity-extraction/extract`
**Description:** Extract entities from base64-encoded image  
**Rate Limit:** 100 requests/hour  
**Request Body:**
```json
{
  "image_data": "base64_encoded_image_data",
  "extraction_config": {
    "confidence_threshold": 0.5,
    "max_entities": 100,
    "entity_types": ["all"]
  },
  "include_visualization": true,
  "output_format": "json"
}
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "task_id": "task_123",
    "status": "processing",
    "message": "Entity extraction started"
  }
}
```

#### `POST /api/v1/entity-extraction/extract/upload`
**Description:** Extract entities from uploaded image file  
**Content-Type:** multipart/form-data  
**Parameters:**
- `file` (file): Image file
- `extraction_config` (string): JSON config
- `include_visualization` (boolean): Include visualization

#### `POST /api/v1/entity-extraction/batch`
**Description:** Extract entities from multiple images  
**Rate Limit:** 20 requests/hour  
**Request Body:**
```json
{
  "images": ["base64_image_1", "base64_image_2"],
  "extraction_config": {
    "confidence_threshold": 0.6,
    "max_entities": 50
  },
  "include_visualization": false
}
```

#### `GET /api/v1/entity-extraction/status/{task_id}`
**Description:** Get extraction task status  
**Response:**
```json
{
  "status": "success", 
  "data": {
    "task_id": "task_123",
    "status": "completed",
    "progress": 100,
    "result": {
      "entities": [...],
      "entity_count": 15,
      "processing_time": 2.34
    }
  }
}
```

#### `GET /api/v1/entity-extraction/results/{task_id}`
**Description:** Get extraction results  
**Query Parameters:**
- `format` (string): "json" or "csv"

#### `GET /api/v1/entity-extraction/supported-entities`
**Description:** Get supported entity types  
**Response:**
```json
{
  "status": "success",
  "data": {
    "entity_types": [
      {
        "type": "people",
        "description": "Detect and identify people in images",
        "attributes": ["name", "age_range", "gender", "emotion"]
      }
    ]
  }
}
```

### Document Analysis API

#### `POST /api/v1/document-analysis/analyze`
**Description:** Analyze document content  
**Request Body:**
```json
{
  "document_data": "base64_encoded_document",
  "document_type": "pdf",
  "analysis_options": {
    "extract_text": true,
    "analyze_structure": true,
    "detect_entities": true,
    "sentiment_analysis": true
  }
}
```

#### `GET /api/v1/document-analysis/status/{task_id}`
**Description:** Get analysis task status

#### `GET /api/v1/document-analysis/report/{task_id}`
**Description:** Get analysis report  
**Response:**
```json
{
  "status": "success",
  "data": {
    "document_type": "pdf",
    "total_pages": 10,
    "extracted_text": "Document content...",
    "entities": [...],
    "sentiment_score": 0.75,
    "key_topics": ["topic1", "topic2"],
    "structure_analysis": {
      "headings": [...],
      "tables": [...],
      "images": [...]
    }
  }
}
```

### Notifications API

#### `GET /api/v1/notifications`
**Description:** Get user notifications  
**Query Parameters:**
- `unread_only` (boolean): Filter unread notifications
- `category` (string): Filter by category
- `limit` (integer): Number of notifications
- `offset` (integer): Pagination offset

**Response:**
```json
{
  "status": "success",
  "data": {
    "notifications": [
      {
        "id": "notif_123",
        "title": "Processing Complete",
        "message": "Your video analysis is ready",
        "category": "processing",
        "read": false,
        "created_at": "2025-01-08T10:30:00Z",
        "metadata": {
          "task_id": "task_456",
          "action_url": "/results/task_456"
        }
      }
    ],
    "total": 25,
    "unread_count": 5
  }
}
```

#### `POST /api/v1/notifications`
**Description:** Create notification (admin only)  
**Request Body:**
```json
{
  "title": "System Maintenance",
  "message": "Scheduled maintenance on January 15th",
  "category": "system",
  "priority": "high",
  "recipients": ["all"] // or specific user IDs
}
```

#### `PUT /api/v1/notifications/{notification_id}/read`
**Description:** Mark notification as read

#### `DELETE /api/v1/notifications/{notification_id}`
**Description:** Delete notification

#### `GET /api/v1/notifications/preferences`
**Description:** Get notification preferences  
**Response:**
```json
{
  "status": "success",
  "data": {
    "email_notifications": true,
    "push_notifications": true,
    "categories": {
      "processing": true,
      "security": true,
      "marketing": false
    },
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00"
    }
  }
}
```

#### `PUT /api/v1/notifications/preferences`
**Description:** Update notification preferences

---

## Phase 2: Advanced Features

### LLM Providers API

#### `GET /api/v1/llm-providers`
**Description:** List available LLM providers  
**Response:**
```json
{
  "status": "success",
  "data": {
    "providers": [
      {
        "id": "openai",
        "name": "OpenAI",
        "status": "active",
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "features": ["text-generation", "embeddings"],
        "pricing_tier": "premium"
      },
      {
        "id": "anthropic", 
        "name": "Anthropic",
        "status": "configured",
        "models": ["claude-3-opus", "claude-3-sonnet"],
        "features": ["text-generation", "analysis"],
        "pricing_tier": "premium"
      }
    ],
    "active_provider": "openai"
  }
}
```

#### `POST /api/v1/llm-providers/configure`
**Description:** Configure LLM provider  
**Rate Limit:** 10 requests/hour  
**Request Body:**
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "settings": {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000,
    "timeout": 30
  },
  "fallback_provider": "anthropic"
}
```

#### `POST /api/v1/llm-providers/test`
**Description:** Test provider connection  
**Request Body:**
```json
{
  "provider": "openai",
  "test_prompt": "Hello, world!",
  "test_type": "basic" // or "comprehensive"
}
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "provider": "openai",
    "success": true,
    "response": "Hello! How can I help you today?",
    "latency": 234,
    "model_used": "gpt-4",
    "tokens_used": {
      "input": 3,
      "output": 8
    }
  }
}
```

#### `PUT /api/v1/llm-providers/{provider}/switch`
**Description:** Switch active provider

#### `POST /api/v1/llm-providers/benchmark`
**Description:** Benchmark multiple providers  
**Request Body:**
```json
{
  "providers": ["openai", "anthropic"],
  "test_cases": [
    {
      "prompt": "Summarize this text: ...",
      "expected_keywords": ["summary", "key points"],
      "criteria": ["accuracy", "speed", "cost"]
    }
  ],
  "iterations": 5
}
```

#### `GET /api/v1/llm-providers/usage/stats`
**Description:** Get usage statistics  
**Query Parameters:**
- `time_range` (string): "1h", "24h", "7d", "30d"
- `provider` (string): Filter by provider

### Marketplace API

#### `GET /api/v1/marketplace/browse`
**Description:** Browse marketplace items  
**Query Parameters:**
- `category` (string): "plugins", "templates", "themes", "models"
- `sort_by` (string): "popularity", "rating", "price", "recent"
- `search` (string): Search query
- `price_range` (string): "free", "paid", "0-10", "10-50"
- `limit` (integer): Items per page
- `offset` (integer): Pagination offset

**Response:**
```json
{
  "status": "success",
  "data": {
    "items": [
      {
        "id": "plugin_123",
        "name": "Advanced OCR Plugin",
        "description": "Enhanced OCR with 99% accuracy",
        "category": "plugins",
        "price": 29.99,
        "currency": "USD",
        "rating": 4.8,
        "downloads": 15420,
        "publisher": {
          "name": "TechCorp",
          "verified": true
        },
        "version": "2.1.0",
        "compatibility": ["v2.0+"],
        "preview_images": ["url1", "url2"],
        "features": ["accuracy", "speed", "multi-language"]
      }
    ],
    "total": 156,
    "categories": [
      {"name": "plugins", "count": 45},
      {"name": "templates", "count": 78}
    ]
  }
}
```

#### `GET /api/v1/marketplace/{item_id}`
**Description:** Get item details  
**Response:**
```json
{
  "status": "success",
  "data": {
    "item": {
      "id": "plugin_123",
      "name": "Advanced OCR Plugin",
      "detailed_description": "Full description with features...",
      "changelog": [...],
      "reviews": [
        {
          "user": "john_doe",
          "rating": 5,
          "comment": "Excellent plugin!",
          "date": "2025-01-01"
        }
      ],
      "system_requirements": {
        "min_version": "2.0.0",
        "memory": "4GB",
        "storage": "100MB"
      }
    }
  }
}
```

#### `POST /api/v1/marketplace/{item_id}/install`
**Description:** Install marketplace item  
**Rate Limit:** 50 requests/hour  
**Request Body:**
```json
{
  "version": "2.1.0",
  "configuration": {
    "auto_update": true,
    "enable_telemetry": false
  },
  "payment_method": "card_123" // for paid items
}
```

#### `GET /api/v1/marketplace/installed`
**Description:** Get installed items

#### `PUT /api/v1/marketplace/installed/{item_id}/configure`
**Description:** Configure installed item

#### `DELETE /api/v1/marketplace/installed/{item_id}`
**Description:** Uninstall item

### AI Dubbing API

#### `POST /api/v1/ai-dubbing/synthesize`
**Description:** Synthesize speech from text  
**Rate Limit:** 20 requests/hour  
**Request Body:**
```json
{
  "text": "Hello, this is a test message",
  "language": "en-US",
  "voice_id": "voice_123",
  "options": {
    "speed": 1.0,
    "pitch": 0,
    "volume": 1.0,
    "emotion": "neutral",
    "speaking_style": "conversational"
  },
  "output_format": "mp3"
}
```

#### `POST /api/v1/ai-dubbing/video`
**Description:** Dub video content  
**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "source_language": "en",
  "target_languages": ["es", "fr", "de"],
  "voice_matching": true,
  "lip_sync": true,
  "preserve_timing": true
}
```

#### `GET /api/v1/ai-dubbing/status/{job_id}`
**Description:** Get dubbing job status

#### `GET /api/v1/ai-dubbing/result/{job_id}`
**Description:** Get dubbing results

#### `GET /api/v1/ai-dubbing/languages`
**Description:** List supported languages  
**Response:**
```json
{
  "status": "success",
  "data": {
    "languages": [
      {
        "code": "en-US",
        "name": "English (US)",
        "voices": [
          {
            "id": "voice_123",
            "name": "Sarah",
            "gender": "female",
            "age": "adult",
            "accent": "american"
          }
        ]
      }
    ]
  }
}
```

#### `POST /api/v1/ai-dubbing/voice-profiles`
**Description:** Create custom voice profile  
**Request Body:**
```json
{
  "name": "Custom Voice",
  "audio_samples": ["base64_sample_1", "base64_sample_2"],
  "language": "en-US",
  "gender": "neutral",
  "age_range": "adult",
  "description": "Professional narrator voice"
}
```

---

## Phase 3: Platform-Specific Features

### Audio Preprocessing (Mobile)

#### `POST /api/v1/audio/preprocess`
**Description:** Preprocess audio for mobile devices  
**Request Body:**
```json
{
  "audio_data": "base64_encoded_audio",
  "processing_options": {
    "noise_reduction": true,
    "noise_reduction_level": 0.8,
    "normalize": true,
    "trim_silence": true,
    "enhance_speech": true
  },
  "format": "wav",
  "sample_rate": 44100
}
```

#### `POST /api/v1/audio/enhance`
**Description:** Apply audio enhancements  
**Request Body:**
```json
{
  "audio_data": "base64_encoded_audio",
  "enhancements": {
    "eq_preset": "voice_clarity",
    "compression": {
      "threshold": -20,
      "ratio": 4,
      "attack": 5,
      "release": 50
    },
    "reverb": {
      "enabled": false,
      "room_size": 0.5,
      "damping": 0.5
    }
  }
}
```

#### `POST /api/v1/audio/convert`
**Description:** Convert audio format

#### `POST /api/v1/audio/batch-preprocess`
**Description:** Batch audio preprocessing

### Image Preprocessing (Mobile)

#### `POST /api/v1/image/preprocess`
**Description:** Preprocess images for mobile  
**Request Body:**
```json
{
  "image_data": "base64_encoded_image",
  "preprocessing_options": {
    "grayscale": true,
    "denoise": true,
    "deskew": true,
    "contrast_enhancement": true,
    "binarization": {
      "method": "otsu",
      "threshold": null
    }
  },
  "target_use": "ocr"
}
```

#### `POST /api/v1/image/enhance`
**Description:** Apply image enhancements

#### `POST /api/v1/image/apply-filters`
**Description:** Apply image filters

#### `POST /api/v1/image/batch-process`
**Description:** Batch image processing

### Support System (Mobile)

#### `POST /api/v1/support/tickets`
**Description:** Create support ticket  
**Request Body:**
```json
{
  "subject": "App crashes on large files",
  "description": "Detailed description of the issue",
  "category": "technical",
  "priority": "high",
  "attachments": [
    {
      "filename": "crash_log.txt",
      "data": "base64_encoded_data"
    }
  ],
  "device_info": {
    "platform": "iOS",
    "version": "15.5",
    "app_version": "2.1.0",
    "device_model": "iPhone 13"
  }
}
```

#### `GET /api/v1/support/tickets`
**Description:** Get user tickets

#### `PUT /api/v1/support/tickets/{ticket_id}/update`
**Description:** Update ticket

#### `POST /api/v1/support/tickets/{ticket_id}/rate`
**Description:** Rate support experience

#### `POST /api/v1/support/chat/start`
**Description:** Start live chat session  
**Request Body:**
```json
{
  "topic": "Technical Support",
  "initial_message": "Need help with video processing",
  "preferred_language": "en",
  "priority": "normal"
}
```

#### `POST /api/v1/support/chat/{session_id}/message`
**Description:** Send chat message

#### `POST /api/v1/support/chat/{session_id}/upload`
**Description:** Upload file in chat

#### `POST /api/v1/support/chat/{session_id}/end`
**Description:** End chat session

### OCR Processor (Desktop)

#### `POST /api/v1/ocr/process`
**Description:** Process single image with OCR  
**Request Body:**
```json
{
  "image_data": "base64_encoded_image",
  "ocr_options": {
    "language": ["eng", "fra"],
    "page_segmentation_mode": 3,
    "ocr_engine_mode": 2,
    "confidence_threshold": 0.6,
    "preserve_formatting": true,
    "detect_orientation": true
  },
  "output_format": "structured"
}
```

#### `POST /api/v1/ocr/process-document`
**Description:** Process PDF/document with OCR  
**Request Body:**
```json
{
  "document_data": "base64_encoded_pdf",
  "document_type": "pdf",
  "ocr_options": {
    "language": ["eng"],
    "extract_tables": true,
    "extract_images": true,
    "searchable_pdf": true
  },
  "page_range": "1-5"
}
```

#### `POST /api/v1/ocr/batch-process`
**Description:** Batch OCR processing

#### `POST /api/v1/ocr/detect-language`
**Description:** Auto-detect text language

#### `POST /api/v1/ocr/extract-tables`
**Description:** Extract tables from documents

### Meeting Automation (Desktop)

#### `POST /api/v1/meetings/create`
**Description:** Create new meeting  
**Request Body:**
```json
{
  "title": "Project Review Meeting",
  "scheduled_time": "2025-01-10T14:00:00Z",
  "duration_minutes": 60,
  "participants": [
    {
      "email": "john@example.com",
      "role": "presenter"
    }
  ],
  "settings": {
    "auto_recording": true,
    "transcription_enabled": true,
    "ai_notes": true,
    "action_item_detection": true
  }
}
```

#### `POST /api/v1/meetings/{meeting_id}/start-recording`
**Description:** Start meeting recording

#### `POST /api/v1/meetings/{meeting_id}/transcribe`
**Description:** Real-time transcription

#### `GET /api/v1/meetings/{meeting_id}/action-items`
**Description:** Extract action items

#### `POST /api/v1/meetings/{meeting_id}/generate-summary`
**Description:** Generate AI meeting summary

#### `GET /api/v1/meetings/{meeting_id}/analytics`
**Description:** Get meeting analytics

#### `POST /api/v1/meetings/schedule-recurring`
**Description:** Schedule recurring meetings

---

## Error Handling

### Standard Error Response Format
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "The provided image format is not supported",
    "details": {
      "field": "image_data",
      "supported_formats": ["jpg", "png", "gif"]
    }
  },
  "timestamp": "2025-01-08T10:30:00Z",
  "request_id": "req_123456"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_INPUT` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `QUOTA_EXCEEDED` | 429 | Rate limit or quota exceeded |
| `FILE_TOO_LARGE` | 413 | Uploaded file exceeds size limit |
| `PROCESSING_ERROR` | 500 | Internal processing error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limiting & Quotas

### Rate Limits by Endpoint Category

| Category | Limit | Window | Quota Reset |
|----------|--------|---------|-------------|
| Authentication | 10 req/min | 1 minute | N/A |
| Entity Extraction | 100 req/hour | 1 hour | Daily |
| LLM Providers | 50 req/hour | 1 hour | Hourly |
| AI Dubbing | 20 req/hour | 1 hour | Daily |
| OCR Processing | 200 req/hour | 1 hour | Daily |
| Support API | 100 req/hour | 1 hour | Hourly |

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1641646800
X-RateLimit-Retry-After: 3600
```

### Quota Management

#### `GET /api/v1/user/quota`
**Description:** Get current quota usage  
**Response:**
```json
{
  "status": "success",
  "data": {
    "quotas": {
      "entity_extraction": {
        "used": 45,
        "limit": 100,
        "reset_date": "2025-01-09T00:00:00Z"
      },
      "ai_dubbing": {
        "used": 12,
        "limit": 50,
        "reset_date": "2025-01-09T00:00:00Z"
      }
    },
    "subscription": "pro",
    "billing_cycle": "monthly"
  }
}
```

---

## WebSocket Endpoints

### Real-time Notifications
**URL:** `wss://api.example.com/ws/notifications`  
**Auth:** Bearer token in query parameter: `?token=<jwt_token>`

**Message Format:**
```json
{
  "type": "notification",
  "data": {
    "id": "notif_123",
    "title": "Processing Complete",
    "message": "Your analysis is ready",
    "category": "processing",
    "timestamp": "2025-01-08T10:30:00Z"
  }
}
```

### Live Chat
**URL:** `wss://api.example.com/ws/chat/{session_id}`

**Message Types:**
- `message` - Chat message
- `typing` - Typing indicator
- `file_upload` - File upload notification
- `agent_joined` - Support agent joined
- `session_ended` - Chat session ended

### Meeting Real-time Updates
**URL:** `wss://api.example.com/ws/meetings/{meeting_id}`

**Message Types:**
- `transcript_chunk` - Real-time transcription
- `participant_joined` - Participant joined
- `recording_status` - Recording status change
- `action_item` - New action item detected

---

## SDK Examples

### JavaScript/TypeScript
```typescript
import { VideoNERClient } from '@video-ner/sdk';

const client = new VideoNERClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.example.com'
});

// Extract entities from image
const result = await client.entityExtraction.extract({
  imageData: base64Image,
  config: {
    confidenceThreshold: 0.7,
    entityTypes: ['people', 'objects']
  }
});
```

### Python
```python
from video_ner_sdk import VideoNERClient

client = VideoNERClient(api_key='your_api_key')

# Process document with OCR
result = client.ocr.process_document(
    document_data=pdf_data,
    document_type='pdf',
    options={'language': ['eng', 'fra']}
)
```

### cURL Examples

#### Extract Entities
```bash
curl -X POST "https://api.example.com/api/v1/entity-extraction/extract" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "base64_image_data",
    "extraction_config": {
      "confidence_threshold": 0.6
    }
  }'
```

#### Create Support Ticket
```bash
curl -X POST "https://api.example.com/api/v1/support/tickets" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "API Issue",
    "description": "Getting timeout errors",
    "category": "technical",
    "priority": "high"
  }'
```

---

## Changelog

### Version 2.1.0 (2025-01-08)
- Added Phase 2 advanced features (LLM Providers, Marketplace, AI Dubbing)
- Added Phase 3 platform-specific features (Mobile preprocessing, Desktop OCR/Meetings)
- Enhanced error handling and rate limiting
- Added WebSocket support for real-time features
- Improved documentation with comprehensive examples

### Version 2.0.0 (2024-12-15)
- Initial Phase 1 implementation (Entity Extraction, Document Analysis, Notifications)
- Core authentication and authorization system
- Basic rate limiting and quota management

---

*For technical support, contact: [support@example.com](mailto:support@example.com)*  
*API Status Page: [status.example.com](https://status.example.com)*