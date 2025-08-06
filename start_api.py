#!/usr/bin/env python3
"""
Simple API starter script
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from api.app import app
import uvicorn

if __name__ == "__main__":
    # Set default environment variables if not set
    os.environ.setdefault('JWT_SECRET_KEY', 'development-secret-key-change-in-production')
    os.environ.setdefault('API_HOST', '127.0.0.1')
    os.environ.setdefault('API_PORT', '8000')
    
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', '8000'))
    
    print(f"Starting API server on http://{host}:{port}")
    print(f"API docs available at http://{host}:{port}/api/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )