"""
Enhanced Authentication Middleware with Cross-Platform Support
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedAuthMiddleware:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_for_development")
        self.algorithm = "HS256"
        
    async def __call__(self, request: Request, call_next):
        # Skip authentication for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/api/auth"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
            
        # Extract authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Try alternative header names for different platforms
            auth_header = request.headers.get("authorization") or request.headers.get("X-API-Key")
            
        if not auth_header:
            logger.warning(f"No authorization header found for path: {request.url.path}")
            # For development, allow requests without auth
            if os.getenv("ENVIRONMENT", "development") == "development":
                logger.info("Development mode: allowing request without authentication")
                return await call_next(request)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
            
        # Handle different auth formats
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
        elif auth_header.startswith("bearer "):
            token = auth_header[7:]  # Handle lowercase bearer
        elif auth_header.startswith("ApiKey "):
            token = auth_header[8:]  # Handle API Key format
        else:
            token = auth_header  # Assume raw token
            
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format"
            )
            
        # Validate token
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            request.state.user = payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            # For development, log the error but allow the request
            if os.getenv("ENVIRONMENT", "development") == "development":
                logger.info("Development mode: allowing request with invalid token")
                request.state.user = None
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
                
        return await call_next(request)

# Create middleware instance
auth_middleware = EnhancedAuthMiddleware()