#!/usr/bin/env python3
"""
OpenAPI Schema
Enhanced API documentation with detailed schemas
"""

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI schema"""
    
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Transcription Platform API",
        version="1.0.0",
        description="""
# Transcription Platform API

Welcome to the Transcription Platform API. This API provides programmatic access to audio/video transcription services with advanced features including speaker diarization, team collaboration, and analytics.

## Authentication

The API uses API keys for authentication. Include your API key in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
```

Or use the X-API-Key header:

```
X-API-Key: YOUR_API_KEY
```

## Rate Limiting

API requests are rate limited based on your subscription plan:

- **Free**: 60 requests/minute, 1,000 requests/hour
- **Basic**: 120 requests/minute, 5,000 requests/hour
- **Pro**: 300 requests/minute, 20,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:
- `X-RateLimit-Limit-*`: Current rate limits
- `X-RateLimit-Remaining-*`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Webhooks

Subscribe to real-time events using webhooks. Configure webhooks in your developer dashboard to receive notifications for:

- Transcript events (created, completed, failed)
- Team events (member added/removed)
- Usage events (limit warnings)

## SDKs

Official SDKs are available for:
- Python: `pip install transcription-platform`
- JavaScript/TypeScript: `npm install @transcription/sdk`

## Versioning

The API is versioned via the URL path. The current version is v1. We guarantee backward compatibility within a major version.

## Error Handling

The API uses standard HTTP status codes and returns detailed error messages:

```json
{
    "error": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "details": {
        "limit": 60,
        "remaining": 0,
        "reset": 1234567890
    }
}
```
        """,
        routes=app.routes,
        tags=[
            {
                "name": "transcripts",
                "description": "Manage transcriptions",
                "externalDocs": {
                    "description": "Transcription guide",
                    "url": "https://docs.example.com/transcripts"
                }
            },
            {
                "name": "teams",
                "description": "Team collaboration features"
            },
            {
                "name": "analytics",
                "description": "Usage analytics and insights"
            },
            {
                "name": "webhooks",
                "description": "Webhook management"
            },
            {
                "name": "developers",
                "description": "Developer resources"
            }
        ],
        servers=[
            {
                "url": "https://api.example.com/v1",
                "description": "Production server"
            },
            {
                "url": "https://api-staging.example.com/v1",
                "description": "Staging server"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "API key authentication. Use format: Bearer YOUR_API_KEY"
        },
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Alternative API key header"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [
        {"ApiKeyAuth": []},
        {"ApiKeyHeader": []}
    ]
    
    # Add common schemas
    openapi_schema["components"]["schemas"].update({
        "Error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "Error code"
                },
                "message": {
                    "type": "string",
                    "description": "Human-readable error message"
                },
                "details": {
                    "type": "object",
                    "description": "Additional error details"
                }
            },
            "required": ["error", "message"]
        },
        "Pagination": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1
                },
                "per_page": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                }
            }
        },
        "PaginatedResponse": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {}
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "per_page": {"type": "integer"},
                        "total": {"type": "integer"},
                        "pages": {"type": "integer"}
                    }
                }
            }
        },
        "TranscriptRequest": {
            "type": "object",
            "properties": {
                "audio_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL of audio/video file to transcribe"
                },
                "language": {
                    "type": "string",
                    "default": "en",
                    "description": "Language code (ISO 639-1)"
                },
                "enable_diarization": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable speaker diarization"
                },
                "max_speakers": {
                    "type": "integer",
                    "minimum": 2,
                    "maximum": 10,
                    "description": "Maximum number of speakers"
                },
                "webhook_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Webhook URL for completion notification"
                },
                "metadata": {
                    "type": "object",
                    "description": "Custom metadata"
                }
            },
            "required": ["audio_url"]
        },
        "TranscriptResponse": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "completed", "failed"]
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                },
                "completed_at": {
                    "type": "string",
                    "format": "date-time"
                },
                "duration": {
                    "type": "number",
                    "description": "Duration in seconds"
                },
                "language": {"type": "string"},
                "speakers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        }
                    }
                },
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "speaker": {"type": "string"},
                            "text": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                },
                "text": {
                    "type": "string",
                    "description": "Full transcript text"
                },
                "metadata": {"type": "object"}
            }
        },
        "WebhookEvent": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string"},
                "created": {
                    "type": "string",
                    "format": "date-time"
                },
                "data": {"type": "object"}
            }
        }
    })
    
    # Add webhook event examples
    openapi_schema["components"]["examples"] = {
        "TranscriptCompletedEvent": {
            "value": {
                "id": "evt_1234567890",
                "type": "transcript.completed",
                "created": "2024-01-20T12:00:00Z",
                "data": {
                    "transcript_id": "tr_abc123",
                    "duration": 300.5,
                    "word_count": 1523,
                    "speaker_count": 2
                }
            }
        },
        "UsageLimitWarning": {
            "value": {
                "id": "evt_0987654321",
                "type": "usage.limit.warning",
                "created": "2024-01-20T12:00:00Z",
                "data": {
                    "usage_type": "transcripts",
                    "current": 850,
                    "limit": 1000,
                    "percentage": 85
                }
            }
        }
    }
    
    # Add response examples for common errors
    openapi_schema["components"]["responses"] = {
        "401": {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"},
                    "example": {
                        "error": "unauthorized",
                        "message": "Invalid or missing API key"
                    }
                }
            }
        },
        "403": {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"},
                    "example": {
                        "error": "insufficient_scope",
                        "message": "This endpoint requires 'transcripts:write' scope"
                    }
                }
            }
        },
        "429": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"},
                    "example": {
                        "error": "rate_limit_exceeded",
                        "message": "Rate limit exceeded",
                        "details": {
                            "limit": 60,
                            "remaining": 0,
                            "reset": 1234567890
                        }
                    }
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

def add_api_documentation(app: FastAPI):
    """Add enhanced API documentation to FastAPI app"""
    
    # Override the default OpenAPI schema
    app.openapi = lambda: custom_openapi(app)
    
    # Add custom documentation endpoints
    @app.get("/api/v1/", tags=["root"])
    async def api_root():
        """API root endpoint with useful links"""
        return {
            "message": "Welcome to the Transcription Platform API",
            "version": "1.0.0",
            "documentation": {
                "openapi": "/api/v1/docs",
                "redoc": "/api/v1/redoc",
                "postman": "https://www.postman.com/transcription-platform",
                "guides": "https://docs.example.com"
            },
            "endpoints": {
                "transcripts": "/api/v1/transcripts",
                "teams": "/api/v1/teams",
                "analytics": "/api/v1/analytics",
                "webhooks": "/api/v1/developers/webhooks",
                "api_keys": "/api/v1/developers/keys"
            },
            "sdks": {
                "python": "pip install transcription-platform",
                "javascript": "npm install @transcription/sdk"
            }
        }
    
    return app