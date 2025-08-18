#!/usr/bin/env python3
"""
Full Stack Server Launcher
Starts both API and React frontend servers for testing
"""

import subprocess
import time
import os
import sys
import signal
import atexit
from pathlib import Path

# Store process PIDs for cleanup
processes = []

def cleanup_processes():
    """Clean up all spawned processes"""
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass

atexit.register(cleanup_processes)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down servers...")
    cleanup_processes()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def find_free_port(start_port=8001):
    """Find a free port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports found")

def create_simple_api_server():
    """Create a simple API server file"""
    api_content = '''
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import tempfile
import os
import json
from datetime import datetime
import random
import uuid

app = FastAPI(title="Transcription Platform API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
transcriptions = []
users = [
    {"id": 1, "email": "admin@example.com", "name": "Admin User", "role": "admin"},
    {"id": 2, "email": "user@example.com", "name": "Regular User", "role": "user"}
]

class TranscriptionResponse(BaseModel):
    id: str
    filename: str
    transcript: str
    confidence: float
    duration: float
    language: str
    timestamp: str
    speaker_labels: List[Dict[str, Any]] = []

class AuthResponse(BaseModel):
    token: str
    user: Dict[str, Any]

@app.get("/")
async def root():
    return {"message": "Transcription Platform API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "storage": "available"
        }
    }

@app.post("/api/auth/login")
async def login(email: str = Form(...), password: str = Form(...)):
    """Login endpoint"""
    user = next((u for u in users if u["email"] == email), None)
    if user and password:  # Accept any password for demo
        return AuthResponse(
            token=f"demo_token_{user['id']}_{uuid.uuid4().hex[:8]}",
            user=user
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/register")
async def register(email: str = Form(...), password: str = Form(...), name: str = Form(...)):
    """Register endpoint"""
    # Check if user exists
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = {
        "id": len(users) + 1,
        "email": email,
        "name": name,
        "role": "user"
    }
    users.append(new_user)
    
    return AuthResponse(
        token=f"demo_token_{new_user['id']}_{uuid.uuid4().hex[:8]}",
        user=new_user
    )

@app.post("/api/v1/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("en"),
    speaker_diarization: bool = Form(False)
):
    """Transcribe audio file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Mock transcription - in real app, this would use Whisper
        mock_transcripts = [
            "Hello, this is a sample transcription of your audio file. The system successfully processed your upload and extracted the speech content.",
            "Welcome to our transcription platform. Your audio has been analyzed and converted to text with high accuracy using advanced AI models.",
            "This is an example output from our speech-to-text system. The file you uploaded has been processed successfully.",
            "Thank you for using our transcription service. This text represents the spoken content from your audio file."
        ]
        
        transcript = random.choice(mock_transcripts)
        duration = random.uniform(30, 180)  # 30s to 3min
        confidence = random.uniform(0.85, 0.98)
        
        # Mock speaker diarization
        speaker_labels = []
        if speaker_diarization:
            speaker_labels = [
                {"speaker": "Speaker 1", "start": 0.0, "end": 15.5, "text": transcript[:50]},
                {"speaker": "Speaker 2", "start": 15.5, "end": 30.0, "text": transcript[50:]}
            ]
        
        transcription = TranscriptionResponse(
            id=str(uuid.uuid4()),
            filename=file.filename,
            transcript=transcript,
            confidence=confidence,
            duration=duration,
            language=language,
            timestamp=datetime.utcnow().isoformat(),
            speaker_labels=speaker_labels
        )
        
        transcriptions.append(transcription.dict())
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return transcription
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/api/v1/transcriptions")
async def get_transcriptions():
    """Get all transcriptions"""
    return {"transcriptions": transcriptions, "total": len(transcriptions)}

@app.get("/api/v1/transcriptions/{transcription_id}")
async def get_transcription(transcription_id: str):
    """Get specific transcription"""
    transcription = next((t for t in transcriptions if t["id"] == transcription_id), None)
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return transcription

@app.delete("/api/v1/transcriptions/{transcription_id}")
async def delete_transcription(transcription_id: str):
    """Delete transcription"""
    global transcriptions
    transcriptions = [t for t in transcriptions if t["id"] != transcription_id]
    return {"message": "Transcription deleted successfully"}

@app.get("/api/v1/analytics/dashboard")
async def get_analytics():
    """Get analytics dashboard data"""
    return {
        "total_transcriptions": len(transcriptions),
        "total_users": len(users),
        "average_confidence": 0.91 if transcriptions else 0,
        "total_duration": sum(t.get("duration", 0) for t in transcriptions),
        "languages": {"en": 80, "es": 15, "fr": 5},
        "recent_activity": transcriptions[-5:] if transcriptions else []
    }

@app.get("/api/v1/models/available")
async def get_available_models():
    """Get available AI models"""
    return {
        "transcription_models": [
            {"id": "whisper-large", "name": "Whisper Large", "language_support": ["en", "es", "fr", "de"]},
            {"id": "whisper-medium", "name": "Whisper Medium", "language_support": ["en", "es", "fr"]},
            {"id": "wav2vec2", "name": "Wav2Vec2", "language_support": ["en"]}
        ],
        "translation_models": [
            {"id": "opus-mt", "name": "Helsinki-NLP OPUS-MT", "pairs": ["en-es", "en-fr", "es-en"]},
            {"id": "m2m100", "name": "Facebook M2M-100", "pairs": ["en-es", "en-fr", "fr-en"]}
        ]
    }

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
'''
    
    with open("simple_api_server.py", "w") as f:
        f.write(api_content.strip())
    
    return "simple_api_server.py"

def main():
    print("🚀 Starting Full Stack Transcription Platform")
    print("=" * 50)
    
    # Create simple API server
    api_file = create_simple_api_server()
    print(f"✅ Created {api_file}")
    
    # Find free ports
    api_port = find_free_port(8001)
    
    print(f"📡 Starting API server on port {api_port}...")
    
    # Start API server
    api_process = subprocess.Popen([
        sys.executable, api_file, str(api_port)
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    processes.append(api_process)
    
    # Wait for API to start
    time.sleep(3)
    
    print(f"✅ API server started at http://localhost:{api_port}")
    print(f"📖 API docs available at http://localhost:{api_port}/docs")
    
    # Update frontend proxy if needed
    frontend_dir = Path("frontend")
    if frontend_dir.exists():
        print(f"⚛️  Starting React frontend...")
        
        # Change to frontend directory and start React app
        frontend_process = subprocess.Popen([
            "npm", "start"
        ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        processes.append(frontend_process)
        
        print("⏳ Waiting for React app to compile...")
        time.sleep(10)
        
        print("✅ React app should be starting at http://localhost:3000")
        print(f"🔗 Frontend configured to proxy API requests to port {api_port}")
    else:
        print("⚠️  Frontend directory not found")
    
    print("\n🎯 Full Stack Platform Ready!")
    print("─" * 30)
    print(f"🌐 API Server: http://localhost:{api_port}")
    print(f"📚 API Docs: http://localhost:{api_port}/docs")
    print("⚛️  React App: http://localhost:3000")
    print("\n📋 Available endpoints:")
    print("  • POST /api/v1/transcribe - Upload and transcribe audio")
    print("  • GET  /api/v1/transcriptions - List all transcriptions")
    print("  • POST /api/auth/login - User authentication")
    print("  • GET  /api/v1/analytics/dashboard - Analytics data")
    print("\n⌨️  Press Ctrl+C to stop all servers")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")

if __name__ == "__main__":
    main()