#!/usr/bin/env python3
"""
Start the real FastAPI backend server
Uses your existing api/main.py with all the real endpoints
"""

import subprocess
import sys
import os
from pathlib import Path

def start_real_backend():
    """Start the real FastAPI backend"""
    print("🚀 Starting Real FastAPI Backend Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/api/docs")
    print("🔧 Using your existing FastAPI application with real endpoints")
    print()
    
    # Check if we're in virtual environment
    venv_python = Path("venv/bin/python")
    if venv_python.exists():
        python_cmd = str(venv_python)
        print("✅ Using virtual environment")
    else:
        python_cmd = sys.executable
        print("⚠️  Using system Python")
    
    try:
        # Start the real FastAPI server using uvicorn
        cmd = [
            python_cmd, "-m", "uvicorn", 
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        print(f"🔧 Running: {' '.join(cmd)}")
        print()
        
        # Run the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure you're in the virtual environment: source venv/bin/activate")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check if port 8000 is available: lsof -i :8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    start_real_backend()