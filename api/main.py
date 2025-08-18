"""
Main API Application
Production-ready FastAPI backend for the transcription platform
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
import os
import secrets
import uuid
import logging

# Import our database models and auth utilities
from api.database import get_db, User, Transcript, Team, TeamMember, TeamRole, APIKey
from api.auth import (
    authenticate_user, create_user, create_access_token, create_refresh_token,
    get_current_active_user, get_current_admin_user, get_user_by_email,
    create_api_key
)
from api.storage import storage_service
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
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
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
    app.add_middleware(
        RateLimitMiddleware,
        redis_client=redis_client,
        requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
    )

# Setup GraphQL
graphql_router = create_graphql_router()
app.include_router(graphql_router)

# Import and include upload endpoints
from api.endpoints.upload import router as upload_router
app.include_router(upload_router)

# Import and include cached transcription endpoints
from api.endpoints.transcription_cached import router as transcription_cached_router
app.include_router(transcription_cached_router)

# Setup API Explorer and Documentation
api_explorer = setup_api_explorer(app)

# GraphQL Playground (development only)
if os.getenv("ENVIRONMENT", "development") == "development":
    @app.get("/graphql-playground", response_class=HTMLResponse)
    async def graphql_playground():
        return get_graphql_playground_html()

# ===========================
# Pydantic Models
# ===========================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    company: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class TranscriptionCreate(BaseModel):
    title: str
    language: str = "auto"
    method: str = "basic"
    team_id: Optional[int] = None

class TranscriptionResponse(BaseModel):
    id: str
    title: str
    status: str
    created_at: datetime
    duration: Optional[float]
    text: Optional[str]
    entities: Optional[Dict[str, List[str]]]
    confidence: Optional[float]
    
    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class TeamMemberInvite(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")

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
# Authentication Endpoints
# ===========================

@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate username from email if not provided
    username = user.email.split('@')[0]
    
    # Create user
    try:
        db_user = create_user(
            db=db,
            email=user.email,
            password=user.password,
            username=username,
            full_name=user.name
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(db_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(db_user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": UserResponse(
            id=db_user.id,
            email=db_user.email,
            name=db_user.full_name or db_user.username,
            role=db_user.role.value,
            created_at=db_user.created_at
        )
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email and password"""
    # OAuth2 spec uses 'username' field, but we accept email
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.full_name or user.username,
            role=user.role.value,
            created_at=user.created_at
        )
    }

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    # Implement refresh token logic
    # This is a placeholder - implement proper refresh token validation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not implemented"
    )

@app.post("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout current user"""
    # In production, you would invalidate the token here
    # For now, the client should discard the token
    return {"message": "Successfully logged out"}

# ===========================
# User Endpoints
# ===========================

@app.get("/api/users/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.full_name or current_user.username,
        role=current_user.role.value,
        created_at=current_user.created_at
    )

@app.put("/api/users/profile", response_model=UserResponse)
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

@app.post("/api/users/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
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

@app.get("/api/users/api-keys", response_model=List[Dict[str, Any]])
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

@app.delete("/api/users/api-keys/{key_id}")
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

# ===========================
# Transcription Endpoints
# ===========================

@app.post("/api/transcriptions/upload", response_model=TranscriptionResponse)
async def upload_transcription(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    language: str = "auto",
    method: str = "basic",
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a file for transcription"""
    # Validate file
    allowed_extensions = {'.mp3', '.wav', '.mp4', '.mov', '.m4a', '.ogg', '.webm'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024  # 500MB in bytes
    file_size = 0
    
    # Read file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
        )
    
    # Validate team membership if team_id provided
    if team_id:
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )
    
    try:
        # Upload file to storage
        object_key, file_url, stored_size = storage_service.upload_file(
            file=file.file,
            filename=file.filename,
            user_id=current_user.id,
            content_type=file.content_type
        )
        
        # Create transcription record
        transcript = Transcript(
            user_id=current_user.id,
            team_id=team_id,
            title=title or file.filename,
            content="",  # Will be filled after processing
            file_name=file.filename,
            file_size=stored_size,
            language=language,
            model_used=method,
            entities={},
            # Store the S3 object key for later retrieval
            summary=object_key  # Temporarily using summary field for storage key
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        # Queue transcription job with Celery
        try:
            from api.tasks import process_transcription
            task = process_transcription.delay(transcript.id, object_key)
            logger.info(f"Queued transcription task: {task.id}")
        except Exception as e:
            logger.error(f"Failed to queue transcription task: {e}")
            # Continue anyway - task can be queued manually later
        
        logger.info(f"Created transcription job {transcript.id} with file {object_key}")
        
        return TranscriptionResponse(
            id=str(transcript.id),
            title=transcript.title,
            status="processing",
            created_at=transcript.created_at,
            duration=None,
            text=None,
            entities=None,
            confidence=None
        )
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        # Clean up database record if created
        if 'transcript' in locals():
            db.delete(transcript)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@app.get("/api/transcriptions", response_model=List[TranscriptionResponse])
async def list_transcriptions(
    skip: int = 0,
    limit: int = Field(default=20, le=100),
    team_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's transcriptions"""
    query = db.query(Transcript).filter(Transcript.user_id == current_user.id)
    
    if team_id:
        query = query.filter(Transcript.team_id == team_id)
    
    transcriptions = query.order_by(Transcript.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        TranscriptionResponse(
            id=str(t.id),
            title=t.title,
            status="completed" if t.content else "processing",
            created_at=t.created_at,
            duration=t.duration,
            text=t.content[:100] + "..." if t.content and len(t.content) > 100 else t.content,
            entities=t.entities,
            confidence=t.confidence
        )
        for t in transcriptions
    ]

@app.get("/api/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific transcription"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcription_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    return TranscriptionResponse(
        id=str(transcript.id),
        title=transcript.title,
        status="completed" if transcript.content else "processing",
        created_at=transcript.created_at,
        duration=transcript.duration,
        text=transcript.content,
        entities=transcript.entities,
        confidence=transcript.confidence
    )

@app.delete("/api/transcriptions/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a transcription"""
    transcript = db.query(Transcript).filter(
        Transcript.id == transcription_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    db.delete(transcript)
    db.commit()
    
    return {"message": "Transcription deleted successfully"}

# ===========================
# Team Endpoints
# ===========================

@app.post("/api/teams", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_team(
    team: TeamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new team"""
    # Create team
    db_team = Team(
        name=team.name,
        description=team.description,
        owner_id=current_user.id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # Add owner as team member
    owner_member = TeamMember(
        team_id=db_team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
        invited_by_id=current_user.id
    )
    db.add(owner_member)
    db.commit()
    
    logger.info(f"User {current_user.id} created team {db_team.id}")
    
    return {
        "id": db_team.id,
        "name": db_team.name,
        "description": db_team.description,
        "owner_id": db_team.owner_id,
        "created_at": db_team.created_at,
        "member_count": 1
    }

@app.get("/api/teams", response_model=List[Dict[str, Any]])
async def list_teams(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's teams"""
    # Get teams where user is a member
    team_memberships = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    
    teams = []
    for membership in team_memberships:
        team = membership.team
        member_count = db.query(TeamMember).filter(
            TeamMember.team_id == team.id
        ).count()
        
        teams.append({
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "role": membership.role.value,
            "member_count": member_count,
            "created_at": team.created_at
        })
    
    return teams

@app.get("/api/teams/{team_id}")
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get team details"""
    # Check membership
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )
    
    team = membership.team
    members = db.query(TeamMember).filter(TeamMember.team_id == team_id).all()
    
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "created_at": team.created_at,
        "your_role": membership.role.value,
        "members": [
            {
                "id": m.user.id,
                "email": m.user.email,
                "name": m.user.full_name or m.user.username,
                "role": m.role.value,
                "joined_at": m.joined_at
            }
            for m in members
        ]
    }

@app.post("/api/teams/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_team_member(
    team_id: int,
    invite: TeamMemberInvite,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite a member to team"""
    # Check if user is admin or owner of the team
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can invite members"
        )
    
    # Find user by email
    invited_user = get_user_by_email(db, invite.email)
    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. They must register first."
        )
    
    # Check if already a member
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == invited_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a team member"
        )
    
    # Add member
    new_member = TeamMember(
        team_id=team_id,
        user_id=invited_user.id,
        role=TeamRole[invite.role.upper()],
        invited_by_id=current_user.id
    )
    db.add(new_member)
    db.commit()
    
    logger.info(f"User {current_user.id} added {invited_user.id} to team {team_id}")
    
    return {
        "message": "Member added successfully",
        "user_id": invited_user.id,
        "email": invited_user.email,
        "role": invite.role
    }

@app.delete("/api/teams/{team_id}/members/{user_id}")
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a member from team"""
    # Check if user is admin or owner
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or membership.role not in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners and admins can remove members"
        )
    
    # Can't remove the owner
    team = db.query(Team).filter(Team.id == team_id).first()
    if team.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the team owner"
        )
    
    # Remove member
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}

# ===========================
# Storage Endpoints
# ===========================

@app.get("/api/storage/presigned-upload")
async def get_presigned_upload_url(
    filename: str,
    content_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get a presigned URL for direct file upload from client"""
    # Validate file extension
    allowed_extensions = {'.mp3', '.wav', '.mp4', '.mov', '.m4a', '.ogg', '.webm'}
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    try:
        upload_url, object_key = storage_service.get_upload_url(
            filename=filename,
            user_id=current_user.id,
            content_type=content_type
        )
        
        return {
            "upload_url": upload_url,
            "object_key": object_key,
            "expires_in": 3600  # 1 hour
        }
    except Exception as e:
        logger.error(f"Failed to generate upload URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )

@app.get("/api/storage/download/{transcription_id}")
async def download_transcription_file(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download the original audio/video file for a transcription"""
    # Get transcription
    transcript = db.query(Transcript).filter(
        Transcript.id == transcription_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Get object key (temporarily stored in summary field)
    object_key = transcript.summary
    if not object_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Generate presigned download URL
        download_url = storage_service.get_file_url(object_key, expires_in=3600)
        
        return {
            "download_url": download_url,
            "filename": transcript.file_name,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )

@app.get("/api/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get storage statistics for the current user"""
    try:
        stats = storage_service.get_storage_stats(current_user.id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        return {
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "file_count": 0,
            "files": []
        }

# ===========================
# Health Check
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

# Import signaling server
from api.websocket.signaling_server import signaling_server

# ===========================
# WebSocket endpoints
# ===========================

@app.websocket("/ws/signaling")
async def websocket_signaling(websocket: WebSocket):
    """WebRTC signaling endpoint for real-time collaboration"""
    await signaling_server.handle_connection(websocket)

@app.get("/api/v1/rooms/{room_id}")
async def get_room_info(
    room_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get information about a collaboration room"""
    return signaling_server.get_room_info(room_id)

@app.get("/api/v1/rooms")
async def get_all_rooms(
    current_user: User = Depends(get_current_admin_user)
):
    """Get all active collaboration rooms (admin only)"""
    return signaling_server.get_all_rooms()

# ===========================
# WebSocket for Real-time
# ===========================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected to session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected from session {session_id}")

    async def broadcast(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[session_id].discard(conn)

manager = ConnectionManager()

@app.websocket("/ws/collaboration/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = None
):
    """
    WebSocket for real-time collaboration
    
    Authentication: Pass JWT token as query parameter
    Example: ws://localhost:8000/ws/collaboration/session123?token=YOUR_JWT_TOKEN
    """
    # Authenticate WebSocket connection
    if token:
        try:
            # Verify JWT token
            from api.auth import decode_token, get_user_by_id
            payload = decode_token(token)
            if not payload or payload.get("type") != "access":
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            # Get user from database
            db = next(get_db())
            user = get_user_by_id(db, int(user_id))
            db.close()
            
            if not user or not user.is_active:
                await websocket.close(code=4001, reason="User not found or inactive")
                return
            
            # Store user info in connection
            websocket.state.user = user
            logger.info(f"WebSocket authenticated for user {user.email}")
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
    else:
        # Allow anonymous connections with limited functionality
        websocket.state.user = None
        logger.info("Anonymous WebSocket connection")
    
    # Accept connection
    await manager.connect(websocket, session_id)
    
    # Send initial connection success message
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "session_id": session_id,
        "user_id": websocket.state.user.id if hasattr(websocket.state, 'user') and websocket.state.user else None,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Validate message type
            if "type" not in data:
                await websocket.send_json({"error": "Missing message type"})
                continue
            
            # Add user info to messages if authenticated
            if hasattr(websocket.state, 'user') and websocket.state.user:
                data["userId"] = websocket.state.user.id
                data["userName"] = websocket.state.user.full_name or websocket.state.user.username
            
            # Handle different message types
            if data["type"] == "cursor":
                await manager.broadcast({
                    "type": "cursor",
                    "userId": data.get("userId"),
                    "userName": data.get("userName"),
                    "position": data.get("position"),
                    "timestamp": datetime.utcnow().isoformat()
                }, session_id)
            elif data["type"] == "content":
                # Only authenticated users can modify content
                if not hasattr(websocket.state, 'user') or not websocket.state.user:
                    await websocket.send_json({
                        "error": "Authentication required for content changes"
                    })
                    continue
                
                await manager.broadcast({
                    "type": "content",
                    "userId": data.get("userId"),
                    "userName": data.get("userName"),
                    "change": data.get("change"),
                    "timestamp": datetime.utcnow().isoformat()
                }, session_id)
            elif data["type"] == "presence":
                await manager.broadcast({
                    "type": "presence",
                    "userId": data.get("userId"),
                    "userName": data.get("userName"),
                    "status": data.get("status"),
                    "timestamp": datetime.utcnow().isoformat()
                }, session_id)
            elif data["type"] == "comment":
                # Only authenticated users can comment
                if not hasattr(websocket.state, 'user') or not websocket.state.user:
                    await websocket.send_json({
                        "error": "Authentication required for comments"
                    })
                    continue
                
                await manager.broadcast({
                    "type": "comment",
                    "userId": data.get("userId"),
                    "userName": data.get("userName"),
                    "comment": data.get("comment"),
                    "position": data.get("position"),
                    "timestamp": datetime.utcnow().isoformat()
                }, session_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        # Notify others about disconnection
        if hasattr(websocket.state, 'user') and websocket.state.user:
            await manager.broadcast({
                "type": "presence",
                "userId": websocket.state.user.id,
                "userName": websocket.state.user.full_name or websocket.state.user.username,
                "status": "offline",
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)

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