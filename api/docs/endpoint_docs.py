"""
Detailed endpoint documentation for FastAPI routes
Provides comprehensive documentation for each API endpoint
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, File, UploadFile, Query, Path, Body
from pydantic import BaseModel, Field
import datetime

# Documentation for authentication endpoints
AUTH_DOCS = {
    "register": {
        "summary": "Register new user",
        "description": """
        Create a new user account with the provided credentials.
        
        **Requirements:**
        - Username must be 3-50 characters
        - Password must be at least 8 characters with complexity requirements
        - Email must be valid and unique
        
        **Returns:**
        - User ID and success message
        - Verification email is sent if email service is configured
        """,
        "responses": {
            201: {
                "description": "User successfully created",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "message": "User registered successfully",
                            "user_id": 123,
                            "username": "johndoe"
                        }
                    }
                }
            },
            400: {
                "description": "Invalid input or user already exists"
            }
        }
    },
    "login": {
        "summary": "User login",
        "description": """
        Authenticate user and receive JWT tokens.
        
        **Login options:**
        - Username and password
        - Email and password
        
        **Returns:**
        - Access token (24 hour expiry)
        - Refresh token (30 day expiry)
        - User information
        
        **Rate limit:** 10 attempts per 5 minutes
        """,
        "responses": {
            200: {
                "description": "Login successful",
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJhbGciOiJIUzI1NiIs...",
                            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                            "token_type": "bearer",
                            "expires_in": 86400,
                            "user": {
                                "id": 123,
                                "username": "johndoe",
                                "email": "john@example.com"
                            }
                        }
                    }
                }
            },
            401: {
                "description": "Invalid credentials"
            },
            429: {
                "description": "Too many login attempts"
            }
        }
    },
    "refresh": {
        "summary": "Refresh access token",
        "description": """
        Exchange a valid refresh token for a new access token.
        
        **Process:**
        1. Validate refresh token
        2. Check if session is still active
        3. Generate new access token
        4. Optionally rotate refresh token
        
        **Security:** Old tokens are invalidated after use
        """,
        "responses": {
            200: {
                "description": "Token refreshed successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "access_token": "eyJhbGciOiJIUzI1NiIs...",
                            "token_type": "bearer",
                            "expires_in": 86400
                        }
                    }
                }
            }
        }
    }
}

# Documentation for transcription endpoints
TRANSCRIPTION_DOCS = {
    "upload": {
        "summary": "Upload file for transcription",
        "description": """
        Upload an audio or video file for transcription processing.
        
        **Supported formats:**
        - Audio: MP3, WAV, M4A, FLAC, OGG, WMA, AAC
        - Video: MP4, AVI, MOV, MKV, WebM, FLV
        
        **File limits:**
        - Maximum size: 2GB
        - Maximum duration: 4 hours
        
        **Processing:**
        - Files are validated and queued for processing
        - Use webhook or polling to check status
        - Processing time depends on file duration and selected features
        
        **Rate limit:** 50 uploads per hour
        """,
        "responses": {
            202: {
                "description": "File accepted for processing",
                "content": {
                    "application/json": {
                        "example": {
                            "transcript_id": 456,
                            "status": "queued",
                            "estimated_time": 300,
                            "webhook_url": "https://your-app.com/webhook"
                        }
                    }
                }
            },
            400: {
                "description": "Invalid file format or size"
            },
            507: {
                "description": "Storage quota exceeded"
            }
        }
    },
    "process": {
        "summary": "Process transcription with options",
        "description": """
        Configure and start transcription processing with advanced options.
        
        **Features:**
        - Language detection or specific language
        - Model selection (tiny to large-v3)
        - Speaker diarization
        - Named Entity Recognition
        - Timestamp generation
        - Confidence scores
        
        **Models:**
        - `tiny`: Fastest, least accurate (39M parameters)
        - `base`: Fast, good accuracy (74M parameters)
        - `small`: Balanced (244M parameters)
        - `medium`: Accurate (769M parameters)
        - `large`: Most accurate (1550M parameters)
        - `large-v2`: Updated large model
        - `large-v3`: Latest and best model
        
        **Rate limit:** 20 processes per hour
        """,
        "request_body": {
            "content": {
                "application/json": {
                    "example": {
                        "transcript_id": 456,
                        "language": "auto",
                        "model": "large-v3",
                        "enable_diarization": True,
                        "enable_ner": True,
                        "enable_timestamps": True,
                        "vocabulary": ["technical", "terms"],
                        "webhook_url": "https://your-app.com/webhook"
                    }
                }
            }
        }
    },
    "status": {
        "summary": "Get transcription status",
        "description": """
        Check the current status of a transcription job.
        
        **Status values:**
        - `queued`: Waiting to be processed
        - `processing`: Currently being transcribed
        - `completed`: Successfully transcribed
        - `failed`: Processing failed
        - `cancelled`: Job was cancelled
        
        **Progress tracking:**
        - Percentage complete for processing jobs
        - Current step (audio extraction, transcription, post-processing)
        - Estimated time remaining
        """,
        "responses": {
            200: {
                "description": "Status retrieved",
                "content": {
                    "application/json": {
                        "example": {
                            "transcript_id": 456,
                            "status": "processing",
                            "progress": 45,
                            "current_step": "transcribing",
                            "started_at": "2024-01-01T12:00:00Z",
                            "estimated_completion": "2024-01-01T12:05:00Z"
                        }
                    }
                }
            }
        }
    }
}

# Documentation for search endpoints
SEARCH_DOCS = {
    "search": {
        "summary": "Search transcripts",
        "description": """
        Search through transcripts with advanced filtering and ranking.
        
        **Search features:**
        - Full-text search with relevance ranking
        - Fuzzy matching for typos
        - Boolean operators (AND, OR, NOT)
        - Phrase search with quotes
        - Wildcards (* and ?)
        
        **Filters:**
        - Date range
        - Language
        - Speaker
        - Confidence score
        - Duration
        - File type
        
        **Results:**
        - Highlighted snippets
        - Relevance scores
        - Faceted counts
        
        **Rate limit:** 100 searches per 5 minutes
        """,
        "parameters": [
            {
                "name": "q",
                "in": "query",
                "required": True,
                "description": "Search query",
                "schema": {"type": "string"},
                "example": "machine learning"
            },
            {
                "name": "language",
                "in": "query",
                "description": "Filter by language",
                "schema": {"type": "string"},
                "example": "en"
            },
            {
                "name": "date_from",
                "in": "query",
                "description": "Start date (ISO format)",
                "schema": {"type": "string", "format": "date"},
                "example": "2024-01-01"
            },
            {
                "name": "date_to",
                "in": "query",
                "description": "End date (ISO format)",
                "schema": {"type": "string", "format": "date"},
                "example": "2024-12-31"
            }
        ]
    },
    "semantic_search": {
        "summary": "Semantic search using AI",
        "description": """
        Search using semantic understanding rather than exact matches.
        
        **How it works:**
        1. Query is converted to embeddings
        2. Compared against transcript embeddings
        3. Returns semantically similar content
        
        **Use cases:**
        - Find discussions about concepts
        - Locate similar topics across transcripts
        - Discovery of related content
        
        **Limitations:**
        - Requires pre-computed embeddings
        - More resource intensive
        - May have slight delay
        """
    }
}

# Documentation for export endpoints
EXPORT_DOCS = {
    "export": {
        "summary": "Export transcript",
        "description": """
        Export transcripts in various formats for different use cases.
        
        **Formats:**
        - `txt`: Plain text
        - `srt`: Subtitle format with timestamps
        - `vtt`: WebVTT for HTML5 video
        - `json`: Structured data with metadata
        - `pdf`: Formatted document
        - `docx`: Microsoft Word document
        
        **Options:**
        - Include timestamps
        - Include speaker labels
        - Include confidence scores
        - Custom formatting
        
        **Rate limit:** 30 exports per hour
        """,
        "parameters": [
            {
                "name": "format",
                "in": "query",
                "required": True,
                "description": "Export format",
                "schema": {
                    "type": "string",
                    "enum": ["txt", "srt", "vtt", "json", "pdf", "docx"]
                }
            },
            {
                "name": "include_timestamps",
                "in": "query",
                "description": "Include timestamps in export",
                "schema": {"type": "boolean", "default": False}
            },
            {
                "name": "include_speakers",
                "in": "query",
                "description": "Include speaker labels",
                "schema": {"type": "boolean", "default": True}
            }
        ]
    }
}

# Documentation for team endpoints
TEAM_DOCS = {
    "create_team": {
        "summary": "Create new team",
        "description": """
        Create a new team workspace for collaboration.
        
        **Features:**
        - Shared transcript library
        - Team member management
        - Role-based permissions
        - Usage quotas
        - Activity tracking
        
        **Roles:**
        - `owner`: Full control
        - `admin`: Manage team and content
        - `member`: Create and edit content
        - `viewer`: Read-only access
        
        **Limits:**
        - Free: 5 team members
        - Pro: 20 team members
        - Enterprise: Unlimited
        """
    },
    "invite_member": {
        "summary": "Invite team member",
        "description": """
        Send invitation to join team.
        
        **Process:**
        1. Generate invitation link
        2. Send email notification
        3. Link expires after 7 days
        4. New member gets assigned role
        
        **Permissions required:** Owner or Admin
        """
    }
}

# Documentation for analytics endpoints
ANALYTICS_DOCS = {
    "usage_stats": {
        "summary": "Get usage statistics",
        "description": """
        Retrieve detailed usage analytics for your account or team.
        
        **Metrics:**
        - Total transcriptions
        - Processing time
        - Storage usage
        - API calls
        - Cost breakdown
        
        **Aggregations:**
        - Daily, weekly, monthly
        - By user (team accounts)
        - By language
        - By feature usage
        
        **Export:**
        - CSV format available
        - Scheduled reports via email
        """
    },
    "insights": {
        "summary": "Content insights",
        "description": """
        AI-powered insights from your transcribed content.
        
        **Analysis includes:**
        - Topic clustering
        - Sentiment trends
        - Key phrase extraction
        - Speaker analytics
        - Content summarization
        
        **Requirements:**
        - Minimum 10 transcripts
        - Insights updated daily
        - Available for Pro and Enterprise plans
        """
    }
}

# Response examples for common scenarios
RESPONSE_EXAMPLES = {
    "success": {
        "description": "Successful operation",
        "value": {
            "success": True,
            "message": "Operation completed successfully",
            "data": {"id": 123, "status": "completed"}
        }
    },
    "validation_error": {
        "description": "Validation error",
        "value": {
            "error": "Validation Error",
            "detail": [
                {
                    "loc": ["body", "email"],
                    "msg": "Invalid email format",
                    "type": "value_error"
                }
            ],
            "status_code": 422
        }
    },
    "unauthorized": {
        "description": "Authentication required",
        "value": {
            "error": "Unauthorized",
            "detail": "Invalid or missing authentication token",
            "status_code": 401
        }
    },
    "rate_limit": {
        "description": "Rate limit exceeded",
        "value": {
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please retry after 3600 seconds",
            "status_code": 429,
            "retry_after": 3600
        }
    },
    "server_error": {
        "description": "Internal server error",
        "value": {
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "status_code": 500,
            "request_id": "req_abc123"
        }
    }
}

# WebSocket event documentation
WEBSOCKET_EVENTS = {
    "connection": {
        "description": "WebSocket connection events",
        "events": {
            "connect": {
                "description": "Client connects with JWT token",
                "example": {
                    "token": "eyJhbGciOiJIUzI1NiIs..."
                }
            },
            "authenticated": {
                "description": "Connection authenticated successfully",
                "example": {
                    "user_id": 123,
                    "connection_id": "conn_abc123"
                }
            },
            "error": {
                "description": "Connection error",
                "example": {
                    "error": "Invalid token",
                    "code": 4001
                }
            }
        }
    },
    "transcription": {
        "description": "Transcription progress events",
        "events": {
            "transcription.progress": {
                "description": "Progress update",
                "example": {
                    "transcript_id": 456,
                    "progress": 75,
                    "current_step": "post-processing"
                }
            },
            "transcription.complete": {
                "description": "Transcription completed",
                "example": {
                    "transcript_id": 456,
                    "status": "completed",
                    "duration": 180.5,
                    "word_count": 1523
                }
            }
        }
    },
    "collaboration": {
        "description": "Real-time collaboration events",
        "events": {
            "user.joined": {
                "description": "User joined transcript",
                "example": {
                    "user_id": 789,
                    "username": "jane_doe",
                    "transcript_id": 456
                }
            },
            "comment.added": {
                "description": "New comment added",
                "example": {
                    "comment_id": 321,
                    "user_id": 789,
                    "text": "Great point here!",
                    "timestamp": 45.3
                }
            }
        }
    }
}