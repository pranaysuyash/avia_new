"""
Main FastAPI application setup
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from .auth import auth_router
from .transcripts import transcripts_router
from .teams import teams_router
from .media import media_router
from .users import users_router
from .websocket_routes import websocket_router
from .middleware import RateLimitMiddleware, LoggingMiddleware
from .exceptions import APIException
from database import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting API server...")
    init_db()
    yield
    # Shutdown
    logger.info("Shutting down API server...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Audio/Video Transcription API",
        description="REST API for audio/video transcription with collaboration features",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Add middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure based on environment
    )
    
    # Custom middlewares
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    app.add_middleware(LoggingMiddleware)
    
    # Exception handlers
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
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
    @app.get("/api/v1/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "api"
        }
    
    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(transcripts_router, prefix="/api/v1/transcripts", tags=["Transcripts"])
    app.include_router(teams_router, prefix="/api/v1/teams", tags=["Teams"])
    app.include_router(media_router, prefix="/api/v1/media", tags=["Media"])
    app.include_router(websocket_router, prefix="/api/v1", tags=["WebSocket"])
    
    return app


# Create app instance
app = create_app()