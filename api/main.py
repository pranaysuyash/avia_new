"""
Main API Application
Production-ready FastAPI backend for the transcription platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import GraphQL and documentation utilities
from api.graphql_api import create_graphql_router, get_graphql_playground_html
from api.docs.interactive_explorer import setup_api_explorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry
from api.utils.sentry_config import init_sentry, sentry_middleware
init_sentry(app_name="transcription-api")

# Initialize FastAPI app
app = FastAPI(
    title="Transcription Platform API",
    description="Enterprise-grade audio/video transcription platform with collaboration features",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Import middleware
from api.middleware import (
    RateLimitMiddleware,
    LoggingMiddleware,
    SecurityHeadersMiddleware,
    create_redis_client
)

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3003,http://localhost:3005,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers
app.add_middleware(SecurityHeadersMiddleware)

# Add Sentry middleware
app.middleware("http")(sentry_middleware)

# Add logging middleware
if os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true":
    app.add_middleware(LoggingMiddleware)

# Add rate limiting if Redis is available
redis_client = create_redis_client()
if redis_client:
    from api.middleware.rate_limiter import RateLimiter
    rate_limiter = RateLimiter(
        redis_client=redis_client,
        default_limit=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        default_window=60  # 1 minute window
    )
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter
    )

# ===========================
# Include Modular Routers
# ===========================

# Core API routers
from api.routers.auth import router as auth_router
from api.routers.users import router as users_router
from api.routers.transcription import router as transcription_router
from api.routers.teams import router as teams_router
from api.routers.storage import router as storage_router
from api.routers.websocket import router as websocket_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(transcription_router)
app.include_router(teams_router)
app.include_router(storage_router)
app.include_router(websocket_router)

# Setup GraphQL
graphql_router = create_graphql_router()
app.include_router(graphql_router)

# Existing endpoint routers
from api.endpoints.upload import router as upload_router
app.include_router(upload_router)

from api.endpoints.transcription_cached import router as transcription_cached_router
app.include_router(transcription_cached_router)

from api.endpoints.frame_ocr import router as frame_ocr_router
app.include_router(frame_ocr_router)

# Setup API Explorer and Documentation
api_explorer = setup_api_explorer(app)

# GraphQL Playground (development only)
if os.getenv("ENVIRONMENT", "development") == "development":
    @app.get("/graphql-playground", response_class=HTMLResponse)
    async def graphql_playground():
        return get_graphql_playground_html()

# ===========================
# Exception Handlers
# ===========================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ===========================
# Health Check Endpoints
# ===========================

@app.get("/health")
async def root_health_check():
    """Root health check endpoint"""
    return {
        "status": "healthy",
        "service": "transcription-api",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# ===========================
# Run the application
# ===========================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting API server on {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )