"""
Comprehensive API and Developer Platform
Provides REST API endpoints for all application features
"""

__version__ = "1.0.0"

from .app import create_app

__all__ = ['create_app']