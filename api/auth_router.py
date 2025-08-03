"""
Authentication API Router
Handles login, registration, and token management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

from auth.auth_manager import auth_manager
from .auth import get_current_user, get_current_user_or_api_key, create_api_response, create_error_response

logger = logging.getLogger(__name__)

# Mock security manager for now
class MockSecurityManager:
    class AccessControl:
        def validate_user_credentials(self, email, password):
            # Use auth_manager for validation
            if auth_manager.validate_user(email, password):
                return {'id': '1', 'email': email, 'name': 'Test User'}
            return None
        
        def user_exists(self, email):
            return False  # For testing
        
        def create_user(self, email, password, name):
            return '1'
        
        def generate_token(self, user_id):
            return "mock_token_" + user_id
        
        def generate_api_key(self, user_id):
            return "mock_api_key_" + user_id
        
        def revoke_api_key(self, api_key, user_id):
            return True
        
        def get_user_info(self, user_id):
            return {'id': user_id, 'email': 'test@example.com', 'name': 'Test User'}
    
    class AuditLogger:
        def log_authentication(self, user_id, event, success=True, metadata=None):
            logger.info(f"Auth event: {event} for user {user_id}, success: {success}")
    
    def __init__(self):
        self.access_control = self.AccessControl()
        self.audit_logger = self.AuditLogger()

security_manager = MockSecurityManager()

# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours


class APIKeyResponse(BaseModel):
    api_key: str
    created_at: datetime


@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    try:
        # Validate credentials and get user ID
        user_data = security_manager.access_control.validate_user_credentials(
            request.email, request.password
        )
        
        if not user_data:
            security_manager.audit_logger.log_authentication(
                request.email, False, "API"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Generate JWT token
        token = security_manager.access_control.generate_token(user_data['id'])
        
        # Log successful authentication
        security_manager.audit_logger.log_authentication(
            user_data['id'], True, "API"
        )
        
        return TokenResponse(access_token=token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        if security_manager.access_control.user_exists(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_id = security_manager.access_control.create_user(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Generate JWT token for immediate login
        token = security_manager.access_control.generate_token(user_id)
        
        # Log user creation
        logger.info(f"New user registered: {request.email}")
        
        return create_api_response({
            "user_id": user_id,
            "email": request.email,
            "username": request.username,
            "access_token": token
        }, "User registered successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/generate-api-key", response_model=APIKeyResponse)
async def generate_api_key(user_id: str = Depends(get_current_user)):
    """Generate a new API key for the authenticated user"""
    try:
        api_key = security_manager.access_control.generate_api_key(user_id)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate API key"
            )
        
        return APIKeyResponse(
            api_key=api_key,
            created_at=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/revoke-api-key")
async def revoke_api_key(
    api_key: str,
    user_id: str = Depends(get_current_user)
):
    """Revoke an API key"""
    try:
        success = security_manager.access_control.revoke_api_key(api_key, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke API key"
            )
        
        return create_api_response({
            "api_key": api_key,
            "revoked": True
        }, "API key revoked successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_or_api_key)):
    """Get current user information"""
    try:
        user_info = security_manager.access_control.get_user_info(user_id)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return create_api_response(user_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/refresh")
async def refresh_token(user_id: str = Depends(get_current_user)):
    """Refresh JWT token"""
    try:
        new_token = security_manager.access_control.generate_token(user_id)
        
        return TokenResponse(access_token=new_token)
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@auth_router.post("/logout")
async def logout(user_id: str = Depends(get_current_user_or_api_key)):
    """Logout user (invalidate token on client side)"""
    try:
        # Log logout event
        security_manager.audit_logger.log_authentication(
            user_id, True, "LOGOUT"
        )
        
        return create_api_response({
            "logged_out": True
        }, "Logged out successfully")
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )