"""
Main API Application
FastAPI-based REST API for the transcription platform
"""

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys
import logging
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_manager import SecurityManager
from .auth import APIAuthManager, api_key_required, jwt_required
from .models import *
from .endpoints.transcription import router as transcription_router
from .endpoints.search import router as search_router
from .endpoints.export import router as export_router
from .endpoints.insights import router as insights_router
from .endpoints.video import router as video_router
from .endpoints.security import router as security_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global security manager
security_manager = SecurityManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle"""
    # Startup
    logger.info("Starting API server...")
    logger.info("Security manager initialized")
    yield
    # Shutdown
    logger.info("Shutting down API server...")


def create_api_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title="Audio/Video Transcription API",
        description="Comprehensive REST API for transcription, analysis, and content processing",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        
        # Add security headers
        headers = security_manager.security_headers
        for header, value in headers.items():
            response.headers[header] = value
        
        return response
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8501", "http://localhost:8502"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )
    
    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        # Extract API key or user ID from request
        user_id = None
        auth_header = request.headers.get("Authorization")
        
        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user_id = security_manager.access_control.validate_token(token)
            elif auth_header.startswith("ApiKey "):
                api_key = auth_header[7:]
                user_id = security_manager.access_control.validate_api_key(api_key)
        
        if user_id:
            if not security_manager.access_control.check_rate_limit(user_id):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": 3600}
                )
        
        response = await call_next(request)
        return response
    
    # Root endpoint
    @app.get("/", tags=["General"])
    async def root():
        """API root endpoint with basic information"""
        return {
            "name": "Audio/Video Transcription API",
            "version": "1.0.0",
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "transcription": "/api/v1/transcription",
                "search": "/api/v1/search",
                "export": "/api/v1/export",
                "insights": "/api/v1/insights",
                "video": "/api/v1/video",
                "security": "/api/v1/security"
            }
        }
    
    # Health check endpoint
    @app.get("/health", tags=["General"])
    async def health_check():
        """Health check endpoint for monitoring"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": {
                "security": "operational",
                "database": "operational",
                "ai_services": "operational"
            }
        }
    
    # Metrics endpoint (protected)
    @app.get("/metrics", dependencies=[Depends(api_key_required)], tags=["General"])
    async def metrics():
        """API metrics endpoint"""
        return {
            "requests_total": 0,  # Would be tracked in production
            "requests_per_second": 0,
            "active_sessions": len(security_manager.access_control.session_tokens),
            "api_keys_active": len(security_manager.access_control.permissions["api_keys"]),
            "uptime_seconds": 0,
            "memory_usage_mb": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    # Include API routers
    app.include_router(transcription_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(export_router, prefix="/api/v1")
    app.include_router(insights_router, prefix="/api/v1")
    app.include_router(video_router, prefix="/api/v1")
    app.include_router(security_router, prefix="/api/v1")
    
    # Error handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return app


# Create the app instance
app = create_api_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )