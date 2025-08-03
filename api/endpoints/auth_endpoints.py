"""
Authentication API Endpoints
Handles user registration, login, logout, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any
import logging

from ..auth_service import jwt_auth_service
from ..auth import create_api_response, create_error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('username')
    def validate_username(cls, v):
        # Username should only contain letters, numbers, underscore, hyphen
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscore, and hyphen')
        return v


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    permissions: Optional[Dict[str, Any]] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    
    @validator('new_password')
    def validate_new_password(cls, v, values):
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user account"""
    try:
        success, message, user_data = jwt_auth_service.register_user(
            email=request.email,
            username=request.username,
            password=request.password,
            full_name=request.full_name
        )
        
        if success:
            # Remove sensitive data
            if user_data:
                user_data.pop('verification_token', None)
            
            return create_api_response(
                data=user_data,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, req: Request):
    """Login with username/email and password"""
    try:
        # Get client info
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get('User-Agent')
        
        success, message, session_data = jwt_auth_service.authenticate_user(
            username_or_email=request.username_or_email,
            password=request.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if success:
            return create_api_response(
                data=session_data,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        success, message, token_data = jwt_auth_service.refresh_token(
            refresh_token=request.refresh_token
        )
        
        if success:
            return create_api_response(
                data=token_data,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=AuthResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout and invalidate current session"""
    try:
        token = credentials.credentials
        success = jwt_auth_service.logout(token)
        
        if success:
            return create_api_response(
                data=None,
                message="Logged out successfully"
            )
        else:
            return create_api_response(
                data=None,
                message="Logout completed"  # Don't reveal if token was invalid
            )
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=AuthResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    try:
        token = credentials.credentials
        user_info = jwt_auth_service.validate_token(token)
        
        if user_info:
            return create_api_response(
                data=user_info,
                message="User information retrieved"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post("/api-keys", response_model=AuthResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new API key for the authenticated user"""
    try:
        token = credentials.credentials
        user_info = jwt_auth_service.validate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Calculate expiration
        expires_at = None
        if request.expires_in_days:
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
        
        success, message, api_key_data = jwt_auth_service.create_api_key(
            user_id=user_info['user_id'],
            name=request.name,
            permissions=request.permissions
        )
        
        if success:
            return create_api_response(
                data=api_key_data,
                message=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@router.get("/api-keys", response_model=AuthResponse)
async def list_api_keys(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """List all API keys for the authenticated user"""
    try:
        token = credentials.credentials
        user_info = jwt_auth_service.validate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user's API keys from database
        from ..auth_service import jwt_auth_service
        db = jwt_auth_service._get_db()
        
        try:
            from database.models import APIKey
            api_keys = db.query(APIKey).filter(
                APIKey.user_id == user_info['user_id']
            ).all()
            
            keys_data = [
                {
                    'id': key.id,
                    'name': key.name,
                    'key_prefix': key.key_prefix,
                    'created_at': key.created_at.isoformat(),
                    'last_used': key.last_used.isoformat() if key.last_used else None,
                    'is_active': key.is_active,
                    'expires_at': key.expires_at.isoformat() if key.expires_at else None
                }
                for key in api_keys
            ]
            
            return create_api_response(
                data={'api_keys': keys_data},
                message=f"Found {len(keys_data)} API keys"
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List API keys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list API keys"
        )


@router.delete("/api-keys/{key_id}", response_model=AuthResponse)
async def revoke_api_key(
    key_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Revoke an API key"""
    try:
        token = credentials.credentials
        user_info = jwt_auth_service.validate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Revoke API key
        from ..auth_service import jwt_auth_service
        db = jwt_auth_service._get_db()
        
        try:
            from database.models import APIKey
            api_key = db.query(APIKey).filter(
                APIKey.id == key_id,
                APIKey.user_id == user_info['user_id']
            ).first()
            
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            api_key.is_active = False
            db.commit()
            
            return create_api_response(
                data={'key_id': key_id},
                message="API key revoked successfully"
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke API key error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )


@router.post("/verify", response_model=AuthResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify if a token is valid"""
    try:
        token = credentials.credentials
        user_info = jwt_auth_service.validate_token(token)
        
        if user_info:
            return create_api_response(
                data={'valid': True, 'user': user_info},
                message="Token is valid"
            )
        else:
            return create_api_response(
                data={'valid': False},
                message="Token is invalid or expired"
            )
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return create_api_response(
            data={'valid': False},
            message="Token verification failed"
        )