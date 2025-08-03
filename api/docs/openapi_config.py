"""
OpenAPI/Swagger configuration for API documentation
Provides comprehensive API documentation with examples and schemas
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Audio/Video Transcription API",
        version="2.0.0",
        description="""
# Audio/Video Transcription API

A comprehensive API for transcribing audio and video files with advanced features including:
- 🎯 **Named Entity Recognition (NER)**
- 🔤 **Multi-language Support**
- 👥 **Speaker Diarization**
- 🤝 **Real-time Collaboration**
- 📊 **Analytics and Insights**
- 🔒 **Enterprise Security**

## Authentication

This API uses **JWT (JSON Web Token)** authentication. To access protected endpoints:

1. Register a new account or login to get an access token
2. Include the token in the `Authorization` header: `Bearer YOUR_TOKEN`
3. Refresh tokens before they expire using the refresh endpoint

### API Keys

For programmatic access, you can generate API keys from your account dashboard.
Include the API key in the `X-API-Key` header.

## Rate Limiting

API endpoints are rate limited to ensure fair usage:
- **Default**: 100 requests per hour
- **Authentication**: 10 attempts per 5 minutes
- **Transcription**: 20 processes per hour
- **Export**: 30 exports per hour

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Total allowed requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## WebSocket Support

Real-time features are available via WebSocket connections at `/ws`.
Connect with your JWT token: `ws://api.example.com/ws?token=YOUR_TOKEN`

## Error Responses

All errors follow a consistent format:
```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Pagination

List endpoints support pagination with query parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)
- `sort_by`: Field to sort by
- `order`: Sort order (asc/desc)
        """,
        routes=app.routes,
        tags=[
            {
                "name": "Authentication",
                "description": "User registration, login, and token management"
            },
            {
                "name": "Transcription",
                "description": "Audio/video transcription operations"
            },
            {
                "name": "NER",
                "description": "Named Entity Recognition and analysis"
            },
            {
                "name": "Search",
                "description": "Search transcripts and content"
            },
            {
                "name": "Export",
                "description": "Export transcripts in various formats"
            },
            {
                "name": "Analytics",
                "description": "Usage analytics and insights"
            },
            {
                "name": "Teams",
                "description": "Team collaboration features"
            },
            {
                "name": "Sharing",
                "description": "Share transcripts with others"
            },
            {
                "name": "Monitoring",
                "description": "Health checks and system monitoring"
            }
        ],
        servers=[
            {
                "url": "https://api.transcription.com",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.transcription.com",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT authentication token"
        },
        "apiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for programmatic access"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"bearerAuth": []},
        {"apiKeyAuth": []}
    ]
    
    # Add example responses
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    },
                    "example": {
                        "error": "Unauthorized",
                        "detail": "Invalid or missing authentication token",
                        "status_code": 401
                    }
                }
            }
        },
        "RateLimitError": {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ErrorResponse"
                    },
                    "example": {
                        "error": "Rate limit exceeded",
                        "detail": "Too many requests. Please retry after 3600 seconds",
                        "status_code": 429,
                        "retry_after": 3600
                    }
                }
            },
            "headers": {
                "Retry-After": {
                    "description": "Seconds until rate limit resets",
                    "schema": {"type": "integer"}
                },
                "X-RateLimit-Limit": {
                    "description": "Total allowed requests",
                    "schema": {"type": "integer"}
                },
                "X-RateLimit-Remaining": {
                    "description": "Remaining requests",
                    "schema": {"type": "integer"}
                }
            }
        },
        "ValidationError": {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/ValidationErrorResponse"
                    }
                }
            }
        }
    }
    
    # Add webhook documentation
    openapi_schema["webhooks"] = {
        "transcriptionComplete": {
            "post": {
                "summary": "Transcription completed",
                "description": "Webhook called when transcription processing is complete",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event": {"type": "string", "example": "transcription.complete"},
                                    "transcript_id": {"type": "integer"},
                                    "status": {"type": "string", "enum": ["completed", "failed"]},
                                    "timestamp": {"type": "string", "format": "date-time"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Webhook processed successfully"}
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return openapi_schema


def configure_swagger_ui(app: FastAPI):
    """
    Configure Swagger UI with custom settings
    """
    app.openapi = lambda: custom_openapi(app)
    
    # Custom Swagger UI configuration
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.staticfiles import StaticFiles
    from fastapi import Request
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html(request: Request):
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "persistAuthorization": True,
                "displayRequestDuration": True,
                "filter": True,
                "showExtensions": True,
                "showCommonExtensions": True,
                "displayOperationId": False,
                "defaultModelsExpandDepth": 2,
                "defaultModelExpandDepth": 2,
                "docExpansion": "list",
                "deepLinking": True,
                "showMutatedRequest": True,
                "tryItOutEnabled": True
            }
        )
    
    # ReDoc configuration
    from fastapi.openapi.docs import get_redoc_html
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html(request: Request):
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )


# Example schemas for common responses
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "error": {"type": "string", "description": "Error message"},
        "detail": {"type": "string", "description": "Detailed error information"},
        "status_code": {"type": "integer", "description": "HTTP status code"},
        "timestamp": {"type": "string", "format": "date-time", "description": "Error timestamp"}
    },
    "required": ["error", "status_code"]
}

PAGINATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {"type": "array", "description": "List of items"},
        "total": {"type": "integer", "description": "Total number of items"},
        "page": {"type": "integer", "description": "Current page number"},
        "per_page": {"type": "integer", "description": "Items per page"},
        "pages": {"type": "integer", "description": "Total number of pages"}
    }
}

# API Examples
API_EXAMPLES = {
    "register_user": {
        "summary": "Register new user",
        "value": {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }
    },
    "login_user": {
        "summary": "Login with username",
        "value": {
            "username": "johndoe",
            "password": "SecurePass123!"
        }
    },
    "login_email": {
        "summary": "Login with email",
        "value": {
            "username": "john@example.com",
            "password": "SecurePass123!"
        }
    },
    "transcription_request": {
        "summary": "Process transcription",
        "value": {
            "title": "Meeting Recording",
            "language": "en",
            "model": "large-v3",
            "enable_diarization": True,
            "enable_ner": True,
            "webhook_url": "https://your-app.com/webhook"
        }
    },
    "search_query": {
        "summary": "Search transcripts",
        "value": {
            "query": "machine learning",
            "filters": {
                "language": "en",
                "date_from": "2024-01-01",
                "date_to": "2024-12-31"
            },
            "page": 1,
            "per_page": 20
        }
    }
}