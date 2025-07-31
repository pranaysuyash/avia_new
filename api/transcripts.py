"""
Transcript endpoints for the API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import get_db_session, User, Transcript, TranscriptShare
from .auth import get_current_user
from .exceptions import APIException
from sharing.share_manager import ShareManager
from versioning.version_manager import VersionManager

logger = logging.getLogger(__name__)

# Router setup
transcripts_router = APIRouter()


# Pydantic models
class TranscriptCreate(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    team_id: Optional[int] = None
    language: str = "en"


class TranscriptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TranscriptResponse(BaseModel):
    id: int
    user_id: int
    team_id: Optional[int]
    title: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int
    is_shared: bool = False
    share_count: int = 0


class TranscriptListResponse(BaseModel):
    transcripts: List[TranscriptResponse]
    total: int
    page: int
    per_page: int


class ShareRequest(BaseModel):
    permission: str = Field(..., regex="^(view|edit|admin)$")
    expires_at: Optional[datetime] = None
    password: Optional[str] = None
    max_views: Optional[int] = None


class ShareResponse(BaseModel):
    share_id: str
    share_url: str
    permission: str
    expires_at: Optional[datetime]
    created_at: datetime


class VersionResponse(BaseModel):
    version: int
    title: str
    created_at: datetime
    created_by: str
    change_summary: Optional[str]
    content_preview: str


# Endpoints
@transcripts_router.get("/", response_model=TranscriptListResponse)
async def list_transcripts(
    current_user: User = Depends(get_current_user),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """List user's transcripts with pagination"""
    db = next(get_db_session())
    
    # Base query
    query = db.query(Transcript).filter(Transcript.user_id == current_user.id)
    
    # Apply filters
    if team_id:
        query = query.filter(Transcript.team_id == team_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Transcript.title.ilike(search_term)) |
            (Transcript.content.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    transcripts = query.order_by(Transcript.created_at.desc()).offset(offset).limit(per_page).all()
    
    # Convert to response
    transcript_list = []
    for transcript in transcripts:
        share_count = db.query(TranscriptShare).filter(
            TranscriptShare.transcript_id == transcript.id
        ).count()
        
        transcript_list.append(TranscriptResponse(
            id=transcript.id,
            user_id=transcript.user_id,
            team_id=transcript.team_id,
            title=transcript.title,
            content=transcript.content,
            metadata=transcript.metadata or {},
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            version=transcript.version,
            is_shared=share_count > 0,
            share_count=share_count
        ))
    
    return TranscriptListResponse(
        transcripts=transcript_list,
        total=total,
        page=page,
        per_page=per_page
    )


@transcripts_router.post("/", response_model=TranscriptResponse, status_code=status.HTTP_201_CREATED)
async def create_transcript(
    transcript: TranscriptCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new transcript"""
    db = next(get_db_session())
    
    # Verify team membership if team_id provided
    if transcript.team_id:
        # Check if user is member of the team
        is_member = any(m.team_id == transcript.team_id for m in current_user.team_memberships)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )
    
    # Create transcript
    db_transcript = Transcript(
        user_id=current_user.id,
        team_id=transcript.team_id,
        title=transcript.title,
        content=transcript.content,
        metadata=transcript.metadata,
        version=1
    )
    
    db.add(db_transcript)
    db.commit()
    db.refresh(db_transcript)
    
    # Create initial version
    version_manager = VersionManager(db)
    version_manager.create_version(
        transcript_id=db_transcript.id,
        user_id=current_user.id,
        title=transcript.title,
        content=transcript.content,
        change_summary="Initial version"
    )
    
    logger.info(f"Created transcript {db_transcript.id} for user {current_user.id}")
    
    return TranscriptResponse(
        id=db_transcript.id,
        user_id=db_transcript.user_id,
        team_id=db_transcript.team_id,
        title=db_transcript.title,
        content=db_transcript.content,
        metadata=db_transcript.metadata or {},
        created_at=db_transcript.created_at,
        updated_at=db_transcript.updated_at,
        version=db_transcript.version,
        is_shared=False,
        share_count=0
    )


@transcripts_router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get a specific transcript"""
    db = next(get_db_session())
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Get share count
    share_count = db.query(TranscriptShare).filter(
        TranscriptShare.transcript_id == transcript.id
    ).count()
    
    return TranscriptResponse(
        id=transcript.id,
        user_id=transcript.user_id,
        team_id=transcript.team_id,
        title=transcript.title,
        content=transcript.content,
        metadata=transcript.metadata or {},
        created_at=transcript.created_at,
        updated_at=transcript.updated_at,
        version=transcript.version,
        is_shared=share_count > 0,
        share_count=share_count
    )


@transcripts_router.put("/{transcript_id}", response_model=TranscriptResponse)
async def update_transcript(
    transcript_id: int,
    update: TranscriptUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a transcript"""
    db = next(get_db_session())
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Update fields
    if update.title is not None:
        transcript.title = update.title
    if update.content is not None:
        transcript.content = update.content
    if update.metadata is not None:
        transcript.metadata = update.metadata
    
    transcript.version += 1
    transcript.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(transcript)
    
    # Create version
    version_manager = VersionManager(db)
    version_manager.create_version(
        transcript_id=transcript.id,
        user_id=current_user.id,
        title=transcript.title,
        content=transcript.content,
        change_summary="Updated via API"
    )
    
    # Get share count
    share_count = db.query(TranscriptShare).filter(
        TranscriptShare.transcript_id == transcript.id
    ).count()
    
    return TranscriptResponse(
        id=transcript.id,
        user_id=transcript.user_id,
        team_id=transcript.team_id,
        title=transcript.title,
        content=transcript.content,
        metadata=transcript.metadata or {},
        created_at=transcript.created_at,
        updated_at=transcript.updated_at,
        version=transcript.version,
        is_shared=share_count > 0,
        share_count=share_count
    )


@transcripts_router.delete("/{transcript_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcript(
    transcript_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a transcript"""
    db = next(get_db_session())
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Delete transcript (cascades to related records)
    db.delete(transcript)
    db.commit()
    
    logger.info(f"Deleted transcript {transcript_id} for user {current_user.id}")


@transcripts_router.post("/{transcript_id}/share", response_model=ShareResponse)
async def share_transcript(
    transcript_id: int,
    share_request: ShareRequest,
    current_user: User = Depends(get_current_user)
):
    """Share a transcript"""
    db = next(get_db_session())
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Create share
    share_manager = ShareManager(db)
    share = share_manager.create_share(
        transcript_id=transcript.id,
        shared_by_id=current_user.id,
        permission=share_request.permission,
        expires_at=share_request.expires_at,
        password=share_request.password,
        max_views=share_request.max_views
    )
    
    # Generate share URL
    share_url = f"https://api.example.com/shared/{share.share_id}"
    
    return ShareResponse(
        share_id=share.share_id,
        share_url=share_url,
        permission=share.permission,
        expires_at=share.expires_at,
        created_at=share.created_at
    )


@transcripts_router.get("/{transcript_id}/versions", response_model=List[VersionResponse])
async def get_transcript_versions(
    transcript_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get version history for a transcript"""
    db = next(get_db_session())
    
    # Verify ownership
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.user_id == current_user.id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Get versions
    version_manager = VersionManager(db)
    versions = version_manager.get_versions(transcript_id)
    
    # Convert to response
    version_list = []
    for version in versions:
        version_list.append(VersionResponse(
            version=version.version,
            title=version.title,
            created_at=version.created_at,
            created_by=version.user.username,
            change_summary=version.change_summary,
            content_preview=version.content[:200] + "..." if len(version.content) > 200 else version.content
        ))
    
    return version_list