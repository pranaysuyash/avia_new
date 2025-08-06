"""
Simplified FastAPI application to get API running
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create simplified FastAPI application"""
    
    app = FastAPI(
        title="Audio/Video Transcription API (Simplified)",
        description="Simplified REST API for testing",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/api/v1")
    async def root():
        return {
            "name": "Audio/Video Transcription API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/api/docs"
        }
    
    # Health check
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "api"
        }
    
    # Basic transcription endpoint
    @app.post("/api/v1/transcripts")
    async def create_transcript():
        return {
            "id": "test-transcript-id",
            "status": "pending",
            "message": "Transcript creation endpoint (mock)"
        }
    
    @app.get("/api/v1/transcripts")
    async def list_transcripts():
        return {
            "transcripts": [],
            "total": 0,
            "message": "Transcript list endpoint (mock)"
        }
    
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)