"""
Production FastAPI application with enhanced authentication system
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import core components
from api.core import APIGateway, setup_logging, get_logger
from api.auth import auth_router, sso_router, get_current_user, require_permissions, Permission

# Setup logging
logger = setup_logging(
    service_name="production_api_auth",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_format="json",
    enable_console=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting production API with enhanced authentication")
    yield
    logger.info("Shutting down production API")

def create_production_app_with_auth() -> FastAPI:
    """Create production-ready FastAPI application with enhanced auth"""
    
    # Create API Gateway
    gateway = APIGateway(
        title="Production API with Enhanced Authentication",
        description="""
        Enterprise-grade transcription platform with comprehensive authentication:
        
        ## Authentication Features
        - JWT-based authentication with refresh tokens
        - Role-based access control (RBAC)
        - Multi-factor authentication (MFA)
        - Single Sign-On (SSO) with Google, Microsoft, Okta
        - Session management with device tracking
        - API key authentication for service-to-service
        
        ## Security Features
        - Bcrypt password hashing
        - Rate limiting per user/IP
        - CSRF protection
        - Comprehensive audit logging
        - Session invalidation
        
        ## Authorization
        Use Bearer token in Authorization header:
        `Authorization: Bearer <your_jwt_token>`
        
        Or use API key in header:
        `X-API-Key: <your_api_key>`
        """,
        version="1.0.0",
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )
    
    app = gateway.get_app()
    app.router.lifespan_context = lifespan
    
    # Include authentication routers
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(sso_router, tags=["SSO"])
    
    # Protected endpoints examples
    @app.get("/api/protected", tags=["Protected"])
    async def protected_endpoint(
        current_user = Depends(get_current_user)
    ):
        """Example protected endpoint requiring authentication"""
        return {
            "message": "Access granted to protected resource",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "role": current_user.role.value
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
    
    @app.get("/api/admin-only", tags=["Admin"])
    async def admin_only_endpoint(
        current_user = Depends(require_permissions(Permission.ADMIN_READ))
    ):
        """Example admin-only endpoint"""
        return {
            "message": "Admin access granted",
            "admin_data": {
                "system_status": "operational",
                "user_count": 1250,
                "active_sessions": 89
            }
        }
    
    @app.get("/api/transcripts", tags=["Transcripts"])
    async def list_transcripts(
        current_user = Depends(require_permissions(Permission.TRANSCRIPT_READ))
    ):
        """List user's transcripts (requires transcript read permission)"""
        return {
            "transcripts": [
                {
                    "id": "trans_123",
                    "title": "Meeting Recording",
                    "status": "completed",
                    "created_at": "2024-01-01T10:00:00Z"
                },
                {
                    "id": "trans_124", 
                    "title": "Interview Audio",
                    "status": "processing",
                    "created_at": "2024-01-01T11:00:00Z"
                }
            ],
            "total": 2,
            "user_id": current_user.id
        }
    
    @app.post("/api/transcripts", tags=["Transcripts"])
    async def create_transcript(
        current_user = Depends(require_permissions(Permission.TRANSCRIPT_WRITE))
    ):
        """Create new transcript (requires transcript write permission)"""
        return {
            "message": "Transcript creation initiated",
            "transcript_id": "trans_125",
            "status": "processing",
            "user_id": current_user.id
        }
    
    # Public endpoints (no auth required)
    @app.get("/api/public/info", tags=["Public"])
    async def public_info():
        """Public endpoint with service information"""
        return {
            "service": "Production Transcription API",
            "version": "1.0.0",
            "features": [
                "JWT Authentication",
                "Role-based Access Control",
                "Multi-factor Authentication", 
                "Single Sign-On",
                "Session Management",
                "API Key Authentication"
            ],
            "auth_endpoints": {
                "login": "/api/auth/login",
                "register": "/api/auth/register",
                "sso_providers": "/api/auth/sso/providers"
            }
        }
    
    logger.info("Production FastAPI app with enhanced auth created successfully")
    return app

# Create the application instance
app = create_production_app_with_auth()

# Export for use in other modules
__all__ = ["app", "create_production_app_with_auth"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.production_app_with_auth:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )