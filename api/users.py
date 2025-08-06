"""
User management endpoints for the API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import logging

from database import get_db_session, User
from .auth import get_current_user
from auth.auth_manager import AuthManager

logger = logging.getLogger(__name__)

# Router setup
users_router = APIRouter()


# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserProfile(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    is_active: bool
    transcript_count: int
    team_count: int
    last_login: Optional[datetime] = None


class UserStats(BaseModel):
    total_transcripts: int
    total_processing_time: float
    total_words: int
    favorite_language: str
    activity_this_month: int
    storage_used_mb: float


# Endpoints
@users_router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    db = next(get_db_session())
    auth_manager = AuthManager(db)
    
    # Check if user exists
    if auth_manager.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = auth_manager.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password
    )
    
    logger.info(f"Created new user {user.id} via API")
    
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        created_at=user.created_at,
        is_active=user.is_active,
        transcript_count=0,
        team_count=0
    )


@users_router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    db = next(get_db_session())
    
    # Get counts
    transcript_count = len(current_user.transcripts)
    team_count = len(current_user.team_memberships)
    
    # Get last login from activity
    last_activity = db.query(User.activities).filter(
        User.activities.any(activity_type="login")
    ).order_by(User.activities.c.created_at.desc()).first()
    
    last_login = last_activity.created_at if last_activity else None
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
        transcript_count=transcript_count,
        team_count=team_count,
        last_login=last_login
    )


@users_router.put("/profile", response_model=UserProfile)
async def update_profile(
    update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    db = next(get_db_session())
    
    # Check username uniqueness
    if update.username and update.username != current_user.username:
        existing = db.query(User).filter(User.username == update.username).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check email uniqueness
    if update.email and update.email != current_user.email:
        existing = db.query(User).filter(User.email == update.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update fields
    if update.username:
        current_user.username = update.username
    if update.email:
        current_user.email = update.email
    
    db.commit()
    db.refresh(current_user)
    
    # Return updated profile
    transcript_count = len(current_user.transcripts)
    team_count = len(current_user.team_memberships)
    
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
        transcript_count=transcript_count,
        team_count=team_count
    )


@users_router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    db = next(get_db_session())
    auth_manager = AuthManager(db)
    
    # Verify current password
    if not auth_manager.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = auth_manager.hash_password(password_data.new_password)
    db.commit()
    
    # Log activity
    auth_manager.log_activity(current_user.id, "password_changed", {"via": "api"})
    
    return {"message": "Password changed successfully"}


@users_router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics"""
    db = next(get_db_session())
    
    # Calculate stats
    total_transcripts = len(current_user.transcripts)
    total_words = sum(len(t.content.split()) for t in current_user.transcripts)
    total_processing_time = sum(
        t.metadata.get("duration", 0) for t in current_user.transcripts 
        if t.metadata
    )
    
    # Get favorite language
    languages = {}
    for transcript in current_user.transcripts:
        lang = transcript.metadata.get("language", "en") if transcript.metadata else "en"
        languages[lang] = languages.get(lang, 0) + 1
    
    favorite_language = max(languages.items(), key=lambda x: x[1])[0] if languages else "en"
    
    # Activity this month
    from datetime import datetime, timedelta
    month_ago = datetime.utcnow() - timedelta(days=30)
    activity_this_month = db.query(User.transcripts).filter(
        User.transcripts.c.created_at >= month_ago
    ).count()
    
    # Storage used (rough estimate)
    storage_used_mb = (total_words * 5) / (1024 * 1024)  # Rough estimate: 5 bytes per word
    
    return UserStats(
        total_transcripts=total_transcripts,
        total_processing_time=total_processing_time,
        total_words=total_words,
        favorite_language=favorite_language,
        activity_this_month=activity_this_month,
        storage_used_mb=round(storage_used_mb, 2)
    )


@users_router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    confirm: bool = False
):
    """Delete user account"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm account deletion by setting confirm=true"
        )
    
    db = next(get_db_session())
    
    # Log activity before deletion
    auth_manager = AuthManager(db)
    auth_manager.log_activity(current_user.id, "account_deleted", {})
    
    # Delete user (cascades to all related data)
    db.delete(current_user)
    db.commit()
    
    logger.info(f"Deleted user account {current_user.id}")
    
    return {"message": "Account deleted successfully"}