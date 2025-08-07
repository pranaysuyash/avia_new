"""
Users API Endpoints
User management and profile endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from api.dependencies import get_db, get_current_user
from database.models import User

router = APIRouter(prefix="/users", tags=["Users"])

class UserProfile(BaseModel):
    """User profile response model"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User display name")
    created_at: datetime = Field(..., description="Account creation date")
    is_active: bool = Field(..., description="User status")

class UpdateUserRequest(BaseModel):
    """Update user profile request"""
    name: Optional[str] = Field(None, description="Display name")
    email: Optional[str] = Field(None, description="Email address")

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile"""
    try:
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, 'name', None),
            created_at=current_user.created_at,
            is_active=current_user.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )

@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    try:
        if update_data.name is not None:
            setattr(current_user, 'name', update_data.name)
        if update_data.email is not None:
            # Check if email is already taken
            existing_user = db.query(User).filter(
                User.email == update_data.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use"
                )
            current_user.email = update_data.email
        
        db.commit()
        db.refresh(current_user)
        
        return UserProfile(
            id=str(current_user.id),
            email=current_user.email,
            name=getattr(current_user, 'name', None),
            created_at=current_user.created_at,
            is_active=current_user.is_active
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )

@router.get("/list")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users (admin only)"""
    try:
        # Basic implementation - in production, add proper admin check
        users = db.query(User).offset(offset).limit(limit).all()
        total = db.query(User).count()
        
        return {
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "name": getattr(user, 'name', None),
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ],
            "total": total,
            "page": offset // limit + 1,
            "per_page": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account"""
    try:
        current_user.is_active = False
        db.commit()
        
        return {"message": "Account deactivated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )