"""Authentication package for Audio/Video Transcription App"""

from .auth_manager import auth_manager, AuthManager
from .auth_ui import render_auth_page, require_authentication, get_current_user

__all__ = [
    'auth_manager',
    'AuthManager',
    'render_auth_page',
    'require_authentication',
    'get_current_user'
]