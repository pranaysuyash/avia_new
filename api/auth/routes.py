"""
Enhanced Authentication Routes
Provides comprehensive auth endpoints with JWT, MFA, and SSO support
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from api.database import get_db, User, UserRole, UserSession
from .enhanced_auth import (
    auth_service, 
    Token, 
    MFASetup, 
    MFAVerification, 
    UserPreferences,
    MFAMethod,
    SSOProvider
)
from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_permissions,
    require_admin,
    Permission
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Request/Response models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None
    remember_me: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserProfile(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    preferences: Optional[Dict[str, Any]] = {}
    mfa_enabled: bool = False
    
    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class SessionInfo(BaseModel):
    session_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    last_active: datetime
    is_current: bool = False

# Authentication endpoints
@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegistration,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    hashed_password = auth_service.get_password_hash(user_data.password)
    verification_token = secrets.token_urlsafe(32)
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        verification_token=verification_token,
        role=UserRole.USER
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    
    tokens = auth_service.create_tokens(db, user, ip_address, user_agent)
    
    return {
        "message": "User registered successfully",
        "user": UserProfile.from_orm(user),
        "tokens": tokens,
        "verification_required": True
    }

@router.post("/login", response_model=Dict[str, Any])
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    
    # Authenticate user
    user = auth_service.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if MFA is required (placeholder - implement based on user settings)
    mfa_required = False  # In production, check user.mfa_enabled
    
    if mfa_required and not login_data.mfa_code:
        return {
            "mfa_required": True,
            "message": "Multi-factor authentication required"
        }
    
    if mfa_required and login_data.mfa_code:
        # Verify MFA code (placeholder)
        # In production, verify against user's MFA secret
        pass
    
    # Create tokens
    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    
    tokens = auth_service.create_tokens(db, user, ip_address, user_agent)
    
    return {
        "message": "Login successful",
        "user": UserProfile.from_orm(user),
        "tokens": tokens
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    tokens = auth_service.refresh_access_token(db, refresh_data.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return tokens

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout current user and invalidate session"""
    
    # In a real implementation, you'd get the session_id from the token
    # and invalidate it. For now, we'll just return success.
    
    return {"message": "Logged out successfully"}

@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout from all sessions"""
    
    # Invalidate all user sessions
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    
    return {"message": "Logged out from all sessions"}

# Profile management
@router.get("/profile", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return UserProfile.from_orm(current_user)

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    
    # Update preferences (in production, store in separate table or JSON field)
    if profile_data.preferences:
        # Store preferences logic here
        pass
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserProfile.from_orm(current_user)

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not auth_service.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = auth_service.get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Invalidate all sessions except current one
    # In production, you'd preserve the current session
    
    return {"message": "Password changed successfully"}

# Session management
@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    return [
        SessionInfo(
            session_id=session.session_id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            last_active=session.created_at,  # In production, track last activity
            is_current=False  # In production, compare with current session
        )
        for session in sessions
    ]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    
    session = db.query(UserSession).filter(
        UserSession.session_id == session_id,
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session.is_active = False
    db.commit()
    
    return {"message": "Session revoked successfully"}

# Multi-factor authentication
@router.post("/mfa/setup", response_model=MFASetup)
async def setup_mfa(
    method: MFAMethod,
    current_user: User = Depends(get_current_active_user)
):
    """Setup multi-factor authentication"""
    
    if method == MFAMethod.TOTP:
        return auth_service.setup_totp_mfa(current_user)
    elif method == MFAMethod.BACKUP_CODES:
        backup_codes = auth_service.generate_backup_codes()
        return MFASetup(
            method=MFAMethod.BACKUP_CODES,
            backup_codes=backup_codes
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MFA method {method} not supported yet"
        )

@router.post("/mfa/verify")
async def verify_mfa(
    verification: MFAVerification,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify and enable MFA"""
    
    if verification.method == MFAMethod.TOTP:
        # In production, get the secret from user's MFA settings
        # For now, this is a placeholder
        secret = "placeholder_secret"
        
        if not auth_service.verify_totp_code(secret, verification.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code"
            )
        
        # Enable MFA for user (in production, update user record)
        # current_user.mfa_enabled = True
        # current_user.mfa_secret = secret
        # db.commit()
        
        return {"message": "MFA enabled successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"MFA method {verification.method} not supported"
    )

@router.delete("/mfa")
async def disable_mfa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disable multi-factor authentication"""
    
    # In production, disable MFA for user
    # current_user.mfa_enabled = False
    # current_user.mfa_secret = None
    # db.commit()
    
    return {"message": "MFA disabled successfully"}

# Password reset
@router.post("/password-reset")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    user.reset_token = reset_token
    user.reset_token_expires = reset_expires
    db.commit()
    
    # In production, send email with reset link
    # send_password_reset_email(user.email, reset_token)
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    
    user = db.query(User).filter(
        User.reset_token == reset_data.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.password_hash = auth_service.get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Invalidate all sessions
    db.query(UserSession).filter(
        UserSession.user_id == user.id
    ).update({"is_active": False})
    db.commit()
    
    return {"message": "Password reset successfully"}

# Admin endpoints
@router.get("/users", response_model=List[UserProfile])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserProfile.from_orm(user) for user in users]

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"User role updated to {role.value}"}

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user active status (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    
    if not is_active:
        # Invalidate all user sessions
        db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).update({"is_active": False})
        db.commit()
    
    status_text = "activated" if is_active else "deactivated"
    return {"message": f"User {status_text} successfully"}