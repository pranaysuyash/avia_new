#!/usr/bin/env python3
"""
Transcription API Endpoints with RBAC
Enhanced with role-based access control
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from database.models import Transcript, User, TeamMember
from database.connection import get_db
from auth.rbac_service import Permission, ResourceType
from api.middleware.rbac_middleware import require_permission, require_any_permission
from api.auth_routes_enhanced import get_current_user_flexible
from services.transcription_service import TranscriptionService
from services.subscription_service import SubscriptionService
from api.middleware.usage_tracking import check_usage_limit, track_resource_usage
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcripts", tags=["transcripts"])

# Initialize services with dependency injection
def get_transcription_service(db: Session = Depends(get_db)) -> TranscriptionService:
    return TranscriptionService(db)

def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)

# Request/Response Models
from pydantic import BaseModel, Field

class TranscriptCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    language: str = Field("en", description="Language code")
    team_id: Optional[int] = None
    is_public: bool = False

class TranscriptUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    is_public: Optional[bool] = None

class TranscriptShareRequest(BaseModel):
    permission: str = Field("view", description="view, comment, or edit")
    expires_in_days: Optional[int] = None
    password: Optional[str] = None
    max_views: Optional[int] = None

class TranscriptResponse(BaseModel):
    id: int
    title: str
    content: str
    file_name: Optional[str]
    file_size: Optional[int]
    duration: Optional[float]
    language: str
    confidence: Optional[float]
    word_count: Optional[int]
    entities: Optional[Dict[str, Any]]
    summary: Optional[str]
    model_used: Optional[str]
    processing_time: Optional[float]
    is_public: bool
    created_at: datetime
    updated_at: datetime
    user: Dict[str, Any]
    team: Optional[Dict[str, Any]]
    can_edit: bool
    can_delete: bool
    can_share: bool

# Endpoints

@router.post("/", response_model=TranscriptResponse)
@require_permission(Permission.TRANSCRIPT_CREATE)
async def create_transcript(
    file: UploadFile = File(...),
    title: str = Form(...),
    language: str = Form("en"),
    team_id: Optional[int] = Form(None),
    is_public: bool = Form(False),
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Create new transcript from audio/video file"""
    # Check usage limits before processing
    allowed, message, usage_info = subscription_service.check_usage_limit(
        user_id=current_user.id,
        usage_type='transcripts',
        amount=1
    )
    
    if not allowed:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                'error': 'usage_limit_exceeded',
                'message': message,
                'usage': usage_info,
                'upgrade_url': '/subscription'
            }
        )
    
    # Validate team access if team_id provided
    if team_id:
        team_member = db.query(TeamMember).filter(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            )
        ).first()
        
        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this team"
            )
    
    # Process transcription
    try:
        # Get file size for storage tracking
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)  # Reset file position
        
        # Check minutes estimate (rough estimate: 1MB audio = 1 minute)
        estimated_minutes = max(1, file_size / (1024 * 1024))
        minutes_allowed, minutes_msg, minutes_info = subscription_service.check_usage_limit(
            user_id=current_user.id,
            usage_type='minutes',
            amount=int(estimated_minutes)
        )
        
        if not minutes_allowed:
            raise HTTPException(
                status_code=402,
                detail={
                    'error': 'minutes_limit_exceeded',
                    'message': minutes_msg,
                    'usage': minutes_info,
                    'upgrade_url': '/subscription'
                }
            )
        
        result = await transcription_service.process_file(
            file=file,
            user_id=current_user.id,
            title=title,
            language=language,
            team_id=team_id,
            is_public=is_public
        )
        
        # Track usage after successful transcription
        subscription_service.track_usage(
            user_id=current_user.id,
            usage_type='transcripts',
            quantity=1,
            resource_type='transcript',
            resource_id=result['id'],
            description=f"Transcription: {title}"
        )
        
        # Track minutes used
        actual_minutes = result.get('duration', 0) / 60.0
        if actual_minutes > 0:
            subscription_service.track_usage(
                user_id=current_user.id,
                usage_type='minutes',
                quantity=actual_minutes,
                resource_type='transcript',
                resource_id=result['id'],
                description=f"Audio duration: {actual_minutes:.1f} minutes"
            )
        
        # Track storage used
        storage_gb = file_size / (1024 ** 3)
        subscription_service.track_usage(
            user_id=current_user.id,
            usage_type='storage',
            quantity=storage_gb,
            resource_type='transcript',
            resource_id=result['id'],
            description=f"File storage: {file.filename}"
        )
        
        # Return formatted response
        return TranscriptResponse(
            **result,
            user={
                "id": current_user.id,
                "username": current_user.username,
                "full_name": current_user.full_name
            },
            team={"id": team_id, "name": "Team"} if team_id else None,
            can_edit=True,
            can_delete=True,
            can_share=True
        )
    
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/", response_model=List[TranscriptResponse])
@require_permission(Permission.TRANSCRIPT_READ)
async def list_transcripts(
    skip: int = 0,
    limit: int = 100,
    team_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends()
):
    """List accessible transcripts"""
    db = next(get_db())
    
    # Base query
    query = db.query(Transcript)
    
    # Filter by access
    if current_user.role != "admin":
        # Get user's team IDs
        user_teams = db.query(TeamMember.team_id).filter(
            TeamMember.user_id == current_user.id
        ).subquery()
        
        # Filter by ownership or team membership
        query = query.filter(
            or_(
                Transcript.user_id == current_user.id,
                Transcript.team_id.in_(user_teams),
                Transcript.is_public == True
            )
        )
    
    # Apply filters
    if team_id:
        query = query.filter(Transcript.team_id == team_id)
    
    if search:
        query = query.filter(
            or_(
                Transcript.title.ilike(f"%{search}%"),
                Transcript.content.ilike(f"%{search}%")
            )
        )
    
    # Get results
    transcripts = query.offset(skip).limit(limit).all()
    
    # Format response
    results = []
    for transcript in transcripts:
        can_edit = transcript.user_id == current_user.id or current_user.role == "admin"
        can_delete = can_edit
        can_share = can_edit
        
        results.append(TranscriptResponse(
            id=transcript.id,
            title=transcript.title,
            content=transcript.content,
            file_name=transcript.file_name,
            file_size=transcript.file_size,
            duration=transcript.duration,
            language=transcript.language,
            confidence=transcript.confidence,
            word_count=transcript.word_count,
            entities=transcript.entities,
            summary=transcript.summary,
            model_used=transcript.model_used,
            processing_time=transcript.processing_time,
            is_public=transcript.is_public,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            user={
                "id": transcript.user.id,
                "username": transcript.user.username,
                "full_name": transcript.user.full_name
            },
            team={"id": transcript.team.id, "name": transcript.team.name} if transcript.team else None,
            can_edit=can_edit,
            can_delete=can_delete,
            can_share=can_share
        ))
    
    return results

@router.get("/{transcript_id}", response_model=TranscriptResponse)
@require_permission(Permission.TRANSCRIPT_READ, ResourceType.TRANSCRIPT, "transcript_id")
async def get_transcript(
    transcript_id: int,
    current_user: User = Depends()
):
    """Get specific transcript"""
    db = next(get_db())
    
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Permission already checked by decorator
    can_edit = transcript.user_id == current_user.id or current_user.role == "admin"
    can_delete = can_edit
    can_share = can_edit
    
    return TranscriptResponse(
        id=transcript.id,
        title=transcript.title,
        content=transcript.content,
        file_name=transcript.file_name,
        file_size=transcript.file_size,
        duration=transcript.duration,
        language=transcript.language,
        confidence=transcript.confidence,
        word_count=transcript.word_count,
        entities=transcript.entities,
        summary=transcript.summary,
        model_used=transcript.model_used,
        processing_time=transcript.processing_time,
        is_public=transcript.is_public,
        created_at=transcript.created_at,
        updated_at=transcript.updated_at,
        user={
            "id": transcript.user.id,
            "username": transcript.user.username,
            "full_name": transcript.user.full_name
        },
        team={"id": transcript.team.id, "name": transcript.team.name} if transcript.team else None,
        can_edit=can_edit,
        can_delete=can_delete,
        can_share=can_share
    )

@router.put("/{transcript_id}", response_model=TranscriptResponse)
@require_permission(Permission.TRANSCRIPT_UPDATE, ResourceType.TRANSCRIPT, "transcript_id")
async def update_transcript(
    transcript_id: int,
    request: TranscriptUpdateRequest,
    current_user: User = Depends()
):
    """Update transcript"""
    db = next(get_db())
    
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Update fields
    if request.title is not None:
        transcript.title = request.title
    if request.content is not None:
        transcript.content = request.content
        transcript.word_count = len(request.content.split())
    if request.entities is not None:
        transcript.entities = request.entities
    if request.summary is not None:
        transcript.summary = request.summary
    if request.is_public is not None:
        transcript.is_public = request.is_public
    
    transcript.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(transcript)
    
    return TranscriptResponse(
        id=transcript.id,
        title=transcript.title,
        content=transcript.content,
        file_name=transcript.file_name,
        file_size=transcript.file_size,
        duration=transcript.duration,
        language=transcript.language,
        confidence=transcript.confidence,
        word_count=transcript.word_count,
        entities=transcript.entities,
        summary=transcript.summary,
        model_used=transcript.model_used,
        processing_time=transcript.processing_time,
        is_public=transcript.is_public,
        created_at=transcript.created_at,
        updated_at=transcript.updated_at,
        user={
            "id": transcript.user.id,
            "username": transcript.user.username,
            "full_name": transcript.user.full_name
        },
        team={"id": transcript.team.id, "name": transcript.team.name} if transcript.team else None,
        can_edit=True,
        can_delete=True,
        can_share=True
    )

@router.delete("/{transcript_id}")
@require_permission(Permission.TRANSCRIPT_DELETE, ResourceType.TRANSCRIPT, "transcript_id")
async def delete_transcript(
    transcript_id: int,
    current_user: User = Depends()
):
    """Delete transcript"""
    db = next(get_db())
    
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    db.delete(transcript)
    db.commit()
    
    return {"message": "Transcript deleted successfully"}

@router.post("/{transcript_id}/share", response_model=Dict[str, Any])
@require_permission(Permission.TRANSCRIPT_SHARE, ResourceType.TRANSCRIPT, "transcript_id")
async def share_transcript(
    transcript_id: int,
    request: TranscriptShareRequest,
    current_user: User = Depends()
):
    """Create shareable link for transcript"""
    db = next(get_db())
    
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Create share link
    from database.models import SharedLink, SharePermission
    import secrets
    
    share_token = secrets.token_urlsafe(32)
    
    shared_link = SharedLink(
        transcript_id=transcript_id,
        share_token=share_token,
        created_by_id=current_user.id,
        permission=SharePermission(request.permission),
        expires_at=datetime.utcnow() + timedelta(days=request.expires_in_days) if request.expires_in_days else None,
        max_views=request.max_views
    )
    
    if request.password:
        from auth.auth_service_enhanced import AuthenticationService
        auth_service = AuthenticationService(get_db)
        shared_link.password_hash = auth_service._hash_password(request.password)
    
    db.add(shared_link)
    db.commit()
    
    return {
        "share_url": f"/shared/{share_token}",
        "share_token": share_token,
        "expires_at": shared_link.expires_at,
        "permission": request.permission
    }

@router.post("/{transcript_id}/export")
@require_permission(Permission.TRANSCRIPT_EXPORT, ResourceType.TRANSCRIPT, "transcript_id")
async def export_transcript(
    transcript_id: int,
    format: str = "txt",
    current_user: User = Depends()
):
    """Export transcript in various formats"""
    db = next(get_db())
    
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    # Export logic here
    if format == "txt":
        content = transcript.content
    elif format == "srt":
        # Convert to SRT format
        content = transcription_service.export_as_srt(transcript)
    elif format == "vtt":
        # Convert to WebVTT format
        content = transcription_service.export_as_vtt(transcript)
    elif format == "json":
        # Export as JSON
        content = {
            "title": transcript.title,
            "content": transcript.content,
            "entities": transcript.entities,
            "summary": transcript.summary,
            "metadata": {
                "language": transcript.language,
                "duration": transcript.duration,
                "confidence": transcript.confidence,
                "created_at": transcript.created_at.isoformat()
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )
    
    return {"content": content, "format": format}