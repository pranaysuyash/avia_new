"""
Comprehensive API and Developer Platform
Provides REST API endpoints for all application features
"""

__version__ = "1.0.0"

# Avoid importing heavy app modules at package import time to prevent side effects
# that are not needed when importing submodules like api.api_main.
# If you need create_app, import it directly from api.app.
__all__ = []