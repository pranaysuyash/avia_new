"""
Transcription API Python SDK

A comprehensive Python SDK for the Audio/Video Transcription Platform API.
Provides easy-to-use interfaces for transcription, analysis, and team management.
"""

from .client import TranscriptionClient
from .models import (
    Transcript, TranscriptStatus, Team, TeamMember, User,
    TranscriptionOptions, AnalysisOptions, WebhookEvent
)
from .exceptions import (
    TranscriptionAPIError, AuthenticationError, RateLimitError,
    ValidationError, NotFoundError, ServerError
)

__version__ = "1.0.0"
__author__ = "Transcription API Team"
__email__ = "support@transcriptionapi.com"

__all__ = [
    "TranscriptionClient",
    "Transcript",
    "TranscriptStatus", 
    "Team",
    "TeamMember",
    "User",
    "TranscriptionOptions",
    "AnalysisOptions",
    "WebhookEvent",
    "TranscriptionAPIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError"
]