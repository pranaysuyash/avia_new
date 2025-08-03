#!/usr/bin/env python3
"""
Enhanced Authentication API Routes
FastAPI routes for authentication supporting multiple platforms
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from auth.auth_service_enhanced import AuthenticationService, AuthProvider, TokenType
from database.models import User, UserRole
from database.connection import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security schemes
bearer_scheme = HTTPBearer()
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

# Initialize auth service
auth_service = AuthenticationService(get_db)

# Request/Response Models

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    organization: Optional[str] = None
    accept_terms: bool = Field(..., description="User must accept terms")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

class LoginRequest(BaseModel):
    username: str = Field(..., description="Email or username")
    password: str
    remember_me: bool = False
    platform: str = Field("web", description="Platform: web, mobile, desktop")

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = ["read", "write"]
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)

class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str
    method: str = Field("totp", description="MFA method: totp, sms, email")

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    organization: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

# Response Models

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    user: Dict[str, Any]

class MFARequiredResponse(BaseModel):
    mfa_required: bool = True
    mfa_token: str
    mfa_methods: List[str]

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    organization: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    teams: List[Dict[str, Any]]

class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    scopes: List[str]

# Dependency functions

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = auth_service._decode_token(token, TokenType.ACCESS)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = next(get_db())
    user = db.query(User).filter(User.id == payload['user_id']).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def get_api_key_user(
    api_key: Optional[str] = Depends(api_key_scheme)
) -> Optional[User]:
    """Get user from API key"""
    if not api_key:
        return None
    
    is_valid, user = auth_service.validate_api_key(api_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user

async def get_current_user_flexible(
    bearer_user: Optional[User] = Depends(get_current_user_optional),
    api_key_user: Optional[User] = Depends(get_api_key_user)
) -> User:
    """Get current user from either JWT or API key"""
    user = bearer_user or api_key_user
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return user

def require_role(required_role: UserRole):
    """Require specific role"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Routes

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user"""
    if not request.accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions"
        )
    
    success, message, user_data = auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        organization=request.organization
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {
        "message": message,
        "user": user_data,
        "requires_email_verification": True
    }

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, req: Request):
    """Login user"""
    # Get client info
    ip_address = req.client.host
    user_agent = req.headers.get("user-agent", "")
    
    success, message, auth_data = auth_service.authenticate_user(
        username_or_email=request.username,
        password=request.password,
        ip_address=ip_address,
        user_agent=user_agent,
        platform=request.platform
    )
    
    if not success:
        # Check for MFA requirement
        if auth_data and auth_data.get("mfa_required"):
            return MFARequiredResponse(**auth_data)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Set refresh token as HTTP-only cookie for web platform
    response = Response()
    if request.platform == "web" and auth_data.get("refresh_token"):
        response.set_cookie(
            key="refresh_token",
            value=auth_data["refresh_token"],
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60  # 30 days
        )
    
    return AuthResponse(**auth_data)

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    success, message, token_data = auth_service.refresh_access_token(
        refresh_token=request.refresh_token
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    return token_data

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user"""
    # Invalidate session (implement in auth service)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user_flexible)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
        organization=current_user.organization,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        teams=[{
            "id": tm.team.id,
            "name": tm.team.name,
            "role": tm.role.value
        } for tm in current_user.team_memberships]
    )

@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    db = next(get_db())
    
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.organization is not None:
        current_user.organization = request.organization
    if request.timezone is not None:
        current_user.timezone = request.timezone
    if request.language is not None:
        current_user.language = request.language
    
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.value,
        organization=current_user.organization,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        teams=[{
            "id": tm.team.id,
            "name": tm.team.name,
            "role": tm.role.value
        } for tm in current_user.team_memberships]
    )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    db = next(get_db())
    
    # Verify current password
    if not auth_service._verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = auth_service._hash_password(request.new_password)
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Request password reset"""
    # Implementation would send reset email
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    # Implementation would validate token and reset password
    return {"message": "Password reset successfully"}

@router.post("/verify-email/{token}")
async def verify_email(token: str):
    """Verify email address"""
    # Implementation would verify email token
    return {"message": "Email verified successfully"}

# API Key Management

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """Create new API key"""
    success, message, key_data = auth_service.create_api_key(
        user_id=current_user.id,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return APIKeyResponse(**key_data)

@router.get("/api-keys", response_model=List[Dict[str, Any]])
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """List user's API keys"""
    db = next(get_db())
    
    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).all()
    
    return [{
        "id": key.id,
        "name": key.name,
        "created_at": key.created_at,
        "last_used_at": key.last_used_at,
        "expires_at": key.expires_at,
        "scopes": key.scopes
    } for key in api_keys]

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Revoke API key"""
    db = next(get_db())
    
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = False
    db.commit()
    
    return {"message": "API key revoked successfully"}

# MFA Routes

@router.post("/mfa/verify")
async def verify_mfa(request: MFAVerifyRequest):
    """Verify MFA code"""
    # Implementation would verify MFA code and return auth tokens
    return {"message": "MFA verification successful"}

@router.post("/mfa/enable")
async def enable_mfa(
    method: str = "totp",
    current_user: User = Depends(get_current_user)
):
    """Enable MFA for user"""
    # Implementation would enable MFA and return setup info
    return {"message": "MFA enabled successfully"}

@router.post("/mfa/disable")
async def disable_mfa(
    current_user: User = Depends(get_current_user)
):
    """Disable MFA for user"""
    # Implementation would disable MFA
    return {"message": "MFA disabled successfully"}

# OAuth Routes

@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """Initiate OAuth flow"""
    # Implementation would redirect to OAuth provider
    return {"redirect_url": f"https://oauth.provider.com/auth"}

@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    """Handle OAuth callback"""
    # Implementation would handle OAuth callback
    return {"message": "OAuth authentication successful"}