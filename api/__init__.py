"""
REST API for Audio/Video Transcription App
Built with FastAPI for high performance and automatic documentation
"""

from .app import create_app
from .auth import auth_router
from .transcripts import transcripts_router
from .teams import teams_router
from .media import media_router
from .users import users_router

__all__ = [
    'create_app',
    'auth_router',
    'transcripts_router',
    'teams_router',
    'media_router',
    'users_router'
]