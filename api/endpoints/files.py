"""
File Management API Endpoints
REST API for managing uploaded files and media
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse
from typing import Optional, List
import logging
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.dependencies import auth_required, create_api_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["File Management"])

class FileInfo(BaseModel):
    id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: str
    status: str
    transcription_id: Optional[str] = None

@router.get("/recent")
async def get_recent_files(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = "test_user"
):
    """Get recently uploaded files"""
    try:
        # Mock recent files
        files = [
            FileInfo(
                id=f"file_{i:03d}",
                filename=f"audio_{i}.wav",
                size=1024000 * (i + 1),
                content_type="audio/wav",
                uploaded_at=(datetime.now() - timedelta(hours=i)).isoformat(),
                status="completed",
                transcription_id=f"transcript_{i:03d}"
            )
            for i in range(1, limit + 1)
        ]
        
        return create_api_response({
            "files": files,
            "total_files": len(files)
        }, "Recent files retrieved successfully")
        
    except Exception as e:
        logger.error(f"Failed to get recent files: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent files")

@router.delete("/{file_id}")
async def delete_file(
    file_id: str = Path(...),
    user_id: str = "test_user"
):
    """Delete an uploaded file"""
    try:
        if not file_id.startswith("file_"):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Mock deletion
        logger.info(f"Deleted file {file_id}")
        
        return create_api_response(
            {"file_id": file_id, "deleted_at": datetime.now().isoformat()},
            "File deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@router.get("/{file_id}/download")
async def download_file(
    file_id: str = Path(...),
    user_id: str = "test_user"
):
    """Download original file"""
    try:
        if not file_id.startswith("file_"):
            raise HTTPException(status_code=404, detail="File not found")
        
        # In real implementation, return actual file
        # For now, return mock response
        return create_api_response({
            "download_url": f"/api/files/{file_id}/download",
            "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }, "Download URL generated")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate download")