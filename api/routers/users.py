"""
User Management Router
Handles user profile management and API key operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

# Import database and auth utilities
from api.database import get_db, User, APIKey
from api.auth import get_current_active_user, create_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

# ===========================
# Pydantic Models
# ===========================

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str  # Only returned on creation
    created_at: datetime
    expires_at: Optional[datetime]

# ===========================
# User Profile Endpoints
# ===========================

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if name:
        current_user.full_name = name
        db.commit()
        db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

# ===========================
# API Key Management
# ===========================

@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_user_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current user"""
    raw_key, api_key = create_api_key(db, current_user, key_data.name)
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,  # Only shown once!
        created_at=api_key.created_at,
        expires_at=api_key.expires_at
    )

@router.get("/api-keys", response_model=List[Dict[str, Any]])
async def list_user_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's API keys (without the actual keys)"""
    return [
        {
            "id": key.id,
            "name": key.name,
            "last_used_at": key.last_used_at,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "is_active": key.is_active
        }
        for key in current_user.api_keys
    ]

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}