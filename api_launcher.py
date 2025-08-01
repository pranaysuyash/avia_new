#!/usr/bin/env python3
"""
API Server Launcher
Starts the FastAPI server with proper configuration
"""

import os
import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    required = ['fastapi', 'uvicorn', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("\nTo install API dependencies, run:")
        print("pip install fastapi uvicorn python-multipart httpx")
        return False
    
    return True

def start_api_server():
    """Start the API server"""
    if not check_dependencies():
        return
    
    print("🚀 Starting Audio/Video Transcription API Server...")
    print("=" * 50)
    
    # Set environment variables
    os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # Start uvicorn
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'api.api_main:app',
        '--reload',
        '--host', '0.0.0.0',
        '--port', '8000'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("\n📖 API Documentation will be available at:")
    print("   http://localhost:8000/docs (Swagger UI)")
    print("   http://localhost:8000/redoc (ReDoc)")
    print("\n🔐 Default API credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n✅ API server stopped")

if __name__ == "__main__":
    start_api_server()