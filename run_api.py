#!/usr/bin/env python3
"""
Script to run the FastAPI server
"""

import uvicorn
import logging
import os
from api import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Run the API server"""
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting API server on {host}:{port}")
    
    # Create app
    app = create_app()
    
    # Run server
    if workers > 1:
        # Production mode with multiple workers
        uvicorn.run(
            "api:app",
            host=host,
            port=port,
            workers=workers,
            log_level="info",
            access_log=True
        )
    else:
        # Development mode with auto-reload
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )


if __name__ == "__main__":
    main()