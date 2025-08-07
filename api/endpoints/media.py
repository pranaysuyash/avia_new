"""
Media API Endpoints
File upload, processing and media management
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import tempfile
import os
import shutil
from pydantic import BaseModel, Field

from api.dependencies import get_db, get_current_user
from database.models import User

router = APIRouter(prefix="/media", tags=["Media"])

class MediaUploadResponse(BaseModel):
    """Media upload response"""
    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    status: str = Field(..., description="Upload status")

class MediaInfo(BaseModel):
    """Media file information"""
    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    uploaded_at: datetime = Field(..., description="Upload timestamp")

@router.post("/upload", response_model=MediaUploadResponse)
async def upload_media_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a media file"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Check file size (100MB limit)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 100MB limit"
            )
        
        # Generate file ID and save temporarily
        file_id = f"media_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # In production, save to cloud storage
        # For now, save to temp directory
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        return MediaUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            content_type=file.content_type,
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/{file_id}")
async def get_media_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get media file information"""
    try:
        # In production, query from database
        # For now, return mock data
        return {
            "file_id": file_id,
            "filename": "sample.mp4",
            "size": 1024000,
            "content_type": "video/mp4",
            "uploaded_at": datetime.now().isoformat(),
            "owner_id": str(current_user.id)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get media info: {str(e)}"
        )

@router.get("/{file_id}/download")
async def download_media_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download a media file"""
    try:
        # In production, check permissions and stream from storage
        # For now, return error message
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or expired"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )

@router.delete("/{file_id}")
async def delete_media_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a media file"""
    try:
        # In production, delete from storage and database
        # For now, return success message
        return {"message": "File deleted successfully", "file_id": file_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )

@router.get("/")
async def list_media_files(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's media files"""
    try:
        # In production, query from database
        # For now, return mock data
        return {
            "files": [
                {
                    "file_id": f"media_{i}",
                    "filename": f"file_{i}.mp4",
                    "size": 1024000 + i * 1000,
                    "content_type": "video/mp4",
                    "uploaded_at": datetime.now().isoformat()
                }
                for i in range(min(limit, 5))
            ],
            "total": 5,
            "page": offset // limit + 1,
            "per_page": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )