#!/usr/bin/env python3
"""
Simple FastAPI backend server for frontend-v2 development
Provides basic endpoints to support the frontend without full backend complexity
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import time
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="AI Media Platform API",
    description="Development API server for frontend-v2",
    version="1.0.0"
)

# Enable CORS for frontend development
import os
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3003,http://localhost:3005,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USER = {
    "id": "dev-user-1",
    "name": "Development User",
    "email": "dev@example.com",
    "avatar": None,
    "initials": "DU",
    "role": "admin",
    "teamId": "team-1",
    "preferences": {
        "theme": "system",
        "language": "en",
        "notifications": True
    },
    "subscription": {
        "plan": "enterprise",
        "status": "active",
        "expiresAt": "2024-12-31T23:59:59Z"
    }
}

MOCK_STATS = {
    "totalFiles": 47234,
    "totalProcessingTime": "12,847 hrs",
    "accuracyRate": 99.3,
    "activeJobs": 23,
    "completedJobs": 1847,
    "failedJobs": 12,
    "storageUsed": "2.4 TB",
    "storageLimit": "10 TB",
    "creditsUsed": 8750,
    "creditsLimit": 10000,
    "trends": {
        "files": {"value": 47234, "change": "+23%", "trend": "up"},
        "accuracy": {"value": 99.3, "change": "+1.2%", "trend": "up"},
        "processing": {"value": 12847, "change": "+18%", "trend": "up"},
        "storage": {"value": 2.4, "change": "+15%", "trend": "up"}
    }
}

MOCK_JOBS = [
    {
        "id": "job-1",
        "name": "Board_Meeting_Q4_2024.mp4",
        "type": "video",
        "status": "completed",
        "accuracy": 99.1,
        "duration": "1:23:45",
        "createdAt": "2024-01-15T10:30:00Z",
        "completedAt": "2024-01-15T11:53:45Z",
        "aiFeatures": ["Sentiment Analysis", "Action Items", "Key Insights", "Speaker Diarization"],
        "fileSize": "1.2 GB"
    },
    {
        "id": "job-2",
        "name": "Medical_Consultation_Case_447.wav",
        "type": "audio",
        "status": "processing",
        "accuracy": 0,
        "duration": "45:32",
        "createdAt": "2024-01-15T11:00:00Z",
        "aiFeatures": ["Clinical NER", "HIPAA Compliance", "Medical Terminology"],
        "fileSize": "156 MB",
        "progress": random.randint(60, 90)
    },
    {
        "id": "job-3",
        "name": "Legal_Deposition_2024_03.mp4",
        "type": "video",
        "status": "completed",
        "accuracy": 98.7,
        "duration": "2:18:45",
        "createdAt": "2024-01-15T09:15:00Z",
        "completedAt": "2024-01-15T11:33:45Z",
        "aiFeatures": ["Legal Entity Extraction", "Compliance Check", "Redaction"],
        "fileSize": "2.8 GB"
    }
]

MOCK_AI_ENGINES = [
    {
        "id": "engine-1",
        "name": "Speech-to-Text Engine",
        "type": "transcription",
        "status": "active",
        "activeJobs": 45,
        "totalJobs": 2847,
        "averageProcessingTime": "2.3 min",
        "accuracy": 99.2,
        "lastHealthCheck": datetime.now().isoformat(),
        "version": "2.1.0",
        "capabilities": ["Multi-language", "Real-time", "Batch processing"]
    },
    {
        "id": "engine-2",
        "name": "Video Intelligence",
        "type": "video",
        "status": "active",
        "activeJobs": 23,
        "totalJobs": 1456,
        "averageProcessingTime": "8.7 min",
        "accuracy": 98.8,
        "lastHealthCheck": datetime.now().isoformat(),
        "version": "1.8.2",
        "capabilities": ["Object detection", "Scene analysis", "OCR"]
    },
    {
        "id": "engine-3",
        "name": "Medical AI (HIPAA)",
        "type": "medical",
        "status": "active",
        "activeJobs": 18,
        "totalJobs": 892,
        "averageProcessingTime": "4.1 min",
        "accuracy": 99.7,
        "lastHealthCheck": datetime.now().isoformat(),
        "version": "3.0.1",
        "capabilities": ["Clinical NER", "HIPAA compliance", "Medical terminology"]
    }
]

MOCK_SYSTEM_STATUS = {
    "overall": "healthy",
    "services": [
        {
            "name": "API Gateway",
            "status": "healthy",
            "responseTime": random.randint(40, 60),
            "uptime": "99.9%",
            "lastCheck": datetime.now().isoformat()
        },
        {
            "name": "Transcription Service",
            "status": "healthy",
            "responseTime": random.randint(100, 150),
            "uptime": "99.8%",
            "lastCheck": datetime.now().isoformat()
        },
        {
            "name": "Database",
            "status": "healthy",
            "responseTime": random.randint(10, 25),
            "uptime": "99.9%",
            "lastCheck": datetime.now().isoformat()
        }
    ],
    "resources": {
        "cpu": {"usage": random.randint(40, 60), "limit": 100},
        "memory": {"usage": random.randint(50, 70), "limit": 100},
        "storage": {"usage": random.randint(20, 30), "limit": 100},
        "gpu": {"usage": random.randint(70, 85), "limit": 100}
    }
}

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str
    rememberMe: Optional[bool] = False

class LoginResponse(BaseModel):
    user: Dict[str, Any]
    token: str
    refreshToken: str

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Simple mock authentication
    if request.email == "dev@example.com" and request.password == "password":
        return LoginResponse(
            user=MOCK_USER,
            token="mock-jwt-token-12345",
            refreshToken="mock-refresh-token-67890"
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

@app.get("/api/auth/profile")
async def get_profile():
    return {"user": MOCK_USER}

@app.post("/api/auth/refresh")
async def refresh_token():
    return {"token": "new-mock-jwt-token-12345"}

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    # Add some randomness to make it feel live
    stats = MOCK_STATS.copy()
    stats["activeJobs"] = random.randint(20, 30)
    return {"stats": stats}

@app.get("/api/dashboard/recent-jobs")
async def get_recent_jobs(limit: int = 10):
    # Update processing job progress
    jobs = MOCK_JOBS.copy()
    for job in jobs:
        if job["status"] == "processing":
            job["progress"] = random.randint(60, 95)
    return {"jobs": jobs[:limit]}

@app.get("/api/dashboard/system-status")
async def get_system_status():
    # Update response times to simulate real monitoring
    status = MOCK_SYSTEM_STATUS.copy()
    for service in status["services"]:
        service["responseTime"] = random.randint(10, 200)
        service["lastCheck"] = datetime.now().isoformat()
    
    # Update resource usage
    status["resources"]["cpu"]["usage"] = random.randint(40, 70)
    status["resources"]["memory"]["usage"] = random.randint(50, 80)
    status["resources"]["gpu"]["usage"] = random.randint(60, 90)
    
    return {"status": status}

# AI engines endpoint
@app.get("/api/ai/engines/status")
async def get_ai_engines_status():
    # Update active jobs count
    engines = MOCK_AI_ENGINES.copy()
    for engine in engines:
        engine["activeJobs"] = random.randint(10, 50)
        engine["lastHealthCheck"] = datetime.now().isoformat()
    return {"engines": engines}

# Media upload endpoint
@app.post("/api/media_ingestion")
async def upload_media(file: UploadFile = File(...)):
    # Simulate file processing
    file_id = f"file-{int(time.time())}"
    
    return {
        "file": {
            "id": file_id,
            "name": file.filename,
            "originalName": file.filename,
            "size": file.size or 1024000,
            "type": file.content_type or "application/octet-stream",
            "mimeType": file.content_type or "application/octet-stream",
            "uploadedAt": datetime.now().isoformat(),
            "status": "uploaded",
            "metadata": {
                "format": "mp4" if file.filename and file.filename.endswith('.mp4') else "unknown"
            },
            "processingJobs": []
        }
    }

# Job status endpoint
@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    # Find job or return mock
    job = next((j for j in MOCK_JOBS if j["id"] == job_id), None)
    if not job:
        job = {
            "id": job_id,
            "name": f"job-{job_id}.mp4",
            "type": "video",
            "status": "processing",
            "accuracy": 0,
            "duration": "unknown",
            "progress": random.randint(30, 80)
        }
    
    return {"job": job}

# Media files list
@app.get("/api/media/list")
async def list_media_files():
    return {
        "files": [
            {
                "id": "file-1",
                "name": "sample-video.mp4",
                "originalName": "sample-video.mp4",
                "size": 1024000,
                "type": "video",
                "uploadedAt": datetime.now().isoformat(),
                "status": "completed"
            }
        ],
        "total": 1
    }

# User endpoints
@app.get("/api/users/profile")
async def get_user_profile():
    return {"user": MOCK_USER}

@app.patch("/api/users/profile")
async def update_user_profile(updates: Dict[str, Any]):
    updated_user = MOCK_USER.copy()
    updated_user.update(updates)
    return {"user": updated_user}

if __name__ == "__main__":
    print("🚀 Starting AI Media Platform Development Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔧 This is a development server with mock data")
    print()
    
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )