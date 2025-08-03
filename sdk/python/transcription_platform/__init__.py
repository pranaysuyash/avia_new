#!/usr/bin/env python3
"""
Transcription Platform Python SDK
Official Python SDK for the Transcription Platform API
"""

__version__ = "1.0.0"

from .client import TranscriptionClient
from .exceptions import (
    TranscriptionError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError
)
from .models import (
    Transcript,
    TranscriptSegment,
    Speaker,
    Team,
    TeamMember,
    Usage,
    Webhook,
    WebhookEvent
)

__all__ = [
    "TranscriptionClient",
    "TranscriptionError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
    "Transcript",
    "TranscriptSegment",
    "Speaker",
    "Team",
    "TeamMember",
    "Usage",
    "Webhook",
    "WebhookEvent"
]