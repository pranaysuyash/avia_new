"""
Storage Management Router
Handles file storage, presigned URLs, and storage statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging

# Import database and auth utilities
from api.database import get_db, User, Transcript
from api.auth import get_current_active_user
from api.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storage", tags=["storage"])

# ===========================
# Storage Endpoints
# ===========================

@router.get("/presigned-upload")
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

@router.get("/download/{transcription_id}")
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

@router.get("/stats")
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