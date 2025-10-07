"""
Transcription Services Router
Handles transcription upload, processing, and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging

# Import database and auth utilities
from api.database import get_db, User, Transcript, TeamMember
from api.auth import get_current_active_user
from api.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcriptions", tags=["transcription"])

# ===========================
# Pydantic Models
# ===========================

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

# ===========================
# Transcription Endpoints
# ===========================

@router.post("/upload", response_model=TranscriptionResponse)
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

@router.get("", response_model=List[TranscriptionResponse])
async def list_transcriptions(
    skip: int = 0,
    limit: int = Query(default=20, le=100),
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

@router.get("/{transcription_id}", response_model=TranscriptionResponse)
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

@router.delete("/{transcription_id}")
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