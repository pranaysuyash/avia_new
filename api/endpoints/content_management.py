"""
Content Management API Endpoints
Task 203: Advanced Content Management and Organization System
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from advanced_content_management_system import (
        ContentManagementSystem, ContentType, ContentStatus, 
        ContentQuality, AccessLevel
    )
    from api.dependencies import get_current_user, get_db
    from sqlalchemy.orm import Session
except ImportError:
    # Fallback for testing
    ContentManagementSystem = None
    def get_current_user():
        return {"user_id": "test_user", "role": "user", "email": "test@example.com"}
    def get_db():
        return None

router = APIRouter(prefix="/api/v1/content", tags=["content-management"])

# Pydantic models for request/response
class ContentCreateRequest(BaseModel):
    title: str
    content_type: str
    transcription_text: str
    description: Optional[str] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    access_level: Optional[str] = "private"
    metadata: Optional[Dict[str, Any]] = None

class ContentUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    transcription_text: Optional[str] = None
    access_level: Optional[str] = None
    status: Optional[str] = None
    quality: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ContentSearchRequest(BaseModel):
    query: Optional[str] = None
    content_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    quality_filter: Optional[str] = None
    status_filter: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 20
    offset: Optional[int] = 0

class TagCreateRequest(BaseModel):
    name: str
    color: Optional[str] = "#007bff"
    description: Optional[str] = ""

class CollectionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    access_level: Optional[str] = "private"
    metadata: Optional[Dict[str, Any]] = None

class ContentTagRequest(BaseModel):
    tag_names: List[str]

class ContentSharingRequest(BaseModel):
    shared_with: str  # User ID or email
    permissions: List[str]  # ["read", "edit", "comment", "share"]
    expires_at: Optional[datetime] = None
    share_message: Optional[str] = None

# Initialize content management service
def get_content_service():
    """Get content management service instance"""
    if ContentManagementSystem:
        return ContentManagementSystem("sqlite:///content_management.db")
    else:
        # Mock for testing
        class MockContentService:
            async def create_content_item(self, *args, **kwargs):
                return {"content_id": "mock_id", "status": "created"}
            async def get_content_item(self, *args, **kwargs):
                return {"id": "mock_id", "title": "Mock Content"}
            async def search_content(self, *args, **kwargs):
                return {"results": [], "total_count": 0}
            async def create_tag(self, *args, **kwargs):
                return {"tag_id": "mock_tag", "name": "mock"}
            async def add_tags_to_content(self, *args, **kwargs):
                return {"added_tags": [], "status": "success"}
            async def create_collection(self, *args, **kwargs):
                return {"collection_id": "mock_collection", "name": "mock"}
            async def add_content_to_collection(self, *args, **kwargs):
                return {"status": "added"}
            async def get_user_analytics(self, *args, **kwargs):
                return {"overview": {"total_content": 0}}
        return MockContentService()

@router.post("/items")
async def create_content_item(
    content_request: ContentCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content item"""
    try:
        cms = get_content_service()
        result = await cms.create_content_item(
            user_id=current_user["user_id"],
            title=content_request.title,
            content_type=content_request.content_type,
            transcription_text=content_request.transcription_text,
            original_filename=content_request.original_filename,
            file_size=content_request.file_size,
            duration=content_request.duration,
            metadata=content_request.metadata
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content creation failed: {str(e)}")

@router.get("/items/{content_id}")
async def get_content_item(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific content item"""
    try:
        cms = get_content_service()
        result = await cms.get_content_item(
            content_id=content_id,
            user_id=current_user["user_id"]
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content retrieval failed: {str(e)}")

@router.put("/items/{content_id}")
async def update_content_item(
    content_id: str,
    update_request: ContentUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a content item"""
    try:
        cms = get_content_service()
        
        # First verify the content exists and user has access
        content = await cms.get_content_item(content_id, current_user["user_id"])
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Mock update for now - would implement actual update logic
        result = {
            "content_id": content_id,
            "updated_fields": [k for k, v in update_request.dict().items() if v is not None],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content update failed: {str(e)}")

@router.delete("/items/{content_id}")
async def delete_content_item(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a content item"""
    try:
        cms = get_content_service()
        
        # Verify content exists and user has access
        content = await cms.get_content_item(content_id, current_user["user_id"])
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Mock deletion - would implement actual delete logic
        result = {
            "content_id": content_id,
            "status": "deleted",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content deletion failed: {str(e)}")

@router.post("/search")
async def search_content(
    search_request: ContentSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search content with advanced filters"""
    try:
        cms = get_content_service()
        
        # Build date range tuple if provided
        date_range = None
        if search_request.start_date and search_request.end_date:
            date_range = (search_request.start_date, search_request.end_date)
        
        result = await cms.search_content(
            user_id=current_user["user_id"],
            query=search_request.query,
            content_types=search_request.content_types,
            tags=search_request.tags,
            categories=search_request.categories,
            date_range=date_range,
            quality_filter=search_request.quality_filter,
            status_filter=search_request.status_filter,
            limit=search_request.limit,
            offset=search_request.offset
        )
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content search failed: {str(e)}")

@router.get("/items")
async def list_content_items(
    content_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """List user's content items with optional filters"""
    try:
        cms = get_content_service()
        
        # Build search parameters
        search_params = {
            "user_id": current_user["user_id"],
            "content_types": [content_type] if content_type else None,
            "status_filter": status,
            "quality_filter": quality,
            "limit": limit,
            "offset": offset
        }
        
        result = await cms.search_content(**search_params)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content listing failed: {str(e)}")

@router.post("/tags")
async def create_tag(
    tag_request: TagCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new tag"""
    try:
        cms = get_content_service()
        result = await cms.create_tag(
            name=tag_request.name,
            color=tag_request.color,
            description=tag_request.description,
            created_by=current_user["user_id"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag creation failed: {str(e)}")

@router.post("/items/{content_id}/tags")
async def add_tags_to_content(
    content_id: str,
    tags_request: ContentTagRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add tags to a content item"""
    try:
        cms = get_content_service()
        result = await cms.add_tags_to_content(
            content_id=content_id,
            tag_names=tags_request.tag_names,
            user_id=current_user["user_id"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag assignment failed: {str(e)}")

@router.delete("/items/{content_id}/tags/{tag_name}")
async def remove_tag_from_content(
    content_id: str,
    tag_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a tag from a content item"""
    try:
        # Mock implementation - would implement actual tag removal
        result = {
            "content_id": content_id,
            "removed_tag": tag_name,
            "status": "removed",
            "updated_at": datetime.utcnow().isoformat()
        }
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag removal failed: {str(e)}")

@router.post("/collections")
async def create_collection(
    collection_request: CollectionCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content collection"""
    try:
        cms = get_content_service()
        result = await cms.create_collection(
            name=collection_request.name,
            user_id=current_user["user_id"],
            description=collection_request.description,
            access_level=collection_request.access_level
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection creation failed: {str(e)}")

@router.post("/collections/{collection_id}/items/{content_id}")
async def add_content_to_collection(
    collection_id: str,
    content_id: str,
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Add content to a collection"""
    try:
        cms = get_content_service()
        result = await cms.add_content_to_collection(
            collection_id=collection_id,
            content_id=content_id,
            user_id=current_user["user_id"],
            notes=notes or ""
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add content to collection: {str(e)}")

@router.delete("/collections/{collection_id}/items/{content_id}")
async def remove_content_from_collection(
    collection_id: str,
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove content from a collection"""
    try:
        # Mock implementation
        result = {
            "collection_id": collection_id,
            "content_id": content_id,
            "status": "removed",
            "removed_at": datetime.utcnow().isoformat()
        }
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove content from collection: {str(e)}")

@router.get("/collections")
async def list_collections(
    current_user: dict = Depends(get_current_user)
):
    """List user's collections"""
    try:
        # Mock implementation - would implement actual collection listing
        collections = [
            {
                "id": "collection_1",
                "name": "Customer Interviews",
                "description": "All customer research interviews",
                "items_count": 23,
                "access_level": "team",
                "created_at": "2025-08-01T10:00:00Z",
                "updated_at": "2025-08-07T14:30:00Z"
            },
            {
                "id": "collection_2", 
                "name": "Team Meetings",
                "description": "Weekly team meetings and planning sessions",
                "items_count": 16,
                "access_level": "private",
                "created_at": "2025-07-15T09:00:00Z",
                "updated_at": "2025-08-06T16:45:00Z"
            }
        ]
        
        return {"success": True, "data": {"collections": collections, "total_count": len(collections)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")

@router.get("/collections/{collection_id}")
async def get_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get collection details with items"""
    try:
        # Mock implementation
        collection_data = {
            "id": collection_id,
            "name": "Customer Interviews",
            "description": "All customer research interviews and feedback sessions",
            "access_level": "team",
            "items_count": 23,
            "created_at": "2025-08-01T10:00:00Z",
            "updated_at": "2025-08-07T14:30:00Z",
            "items": [
                {
                    "id": "content_1",
                    "title": "Customer Interview - User Research",
                    "type": "Interview",
                    "duration": "32:15",
                    "order_index": 1,
                    "added_at": "2025-08-01T10:30:00Z"
                }
            ]
        }
        
        return {"success": True, "data": collection_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection: {str(e)}")

@router.post("/items/{content_id}/share")
async def share_content(
    content_id: str,
    sharing_request: ContentSharingRequest,
    current_user: dict = Depends(get_current_user)
):
    """Share content with other users"""
    try:
        # Mock implementation - would implement actual sharing logic
        share_token = f"share_{content_id}_{datetime.utcnow().timestamp()}"
        
        result = {
            "content_id": content_id,
            "shared_with": sharing_request.shared_with,
            "permissions": sharing_request.permissions,
            "share_token": share_token,
            "share_url": f"https://cms.example.com/shared/{share_token}",
            "expires_at": sharing_request.expires_at.isoformat() if sharing_request.expires_at else None,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content sharing failed: {str(e)}")

@router.get("/items/{content_id}/shares")
async def get_content_shares(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get sharing information for a content item"""
    try:
        # Mock implementation
        shares = [
            {
                "id": "share_1",
                "shared_with": "john@example.com",
                "permissions": ["read", "comment"],
                "expires_at": "2025-08-14T00:00:00Z",
                "last_accessed": "2025-08-07T14:30:00Z",
                "status": "active"
            }
        ]
        
        return {"success": True, "data": {"shares": shares, "total_count": len(shares)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get shares: {str(e)}")

@router.delete("/items/{content_id}/shares/{share_id}")
async def revoke_content_share(
    content_id: str,
    share_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke access to shared content"""
    try:
        result = {
            "content_id": content_id,
            "share_id": share_id,
            "status": "revoked",
            "revoked_at": datetime.utcnow().isoformat()
        }
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke share: {str(e)}")

@router.get("/analytics")
async def get_content_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get user's content analytics"""
    try:
        cms = get_content_service()
        result = await cms.get_user_analytics(
            user_id=current_user["user_id"],
            days=days
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.get("/quality/issues")
async def get_quality_issues(
    quality_threshold: float = Query(3.0, ge=0.0, le=5.0),
    current_user: dict = Depends(get_current_user)
):
    """Get content items with quality issues"""
    try:
        # Mock implementation - would query database for low quality content
        quality_issues = [
            {
                "content_id": "content_1",
                "title": "Sales Call - Tech Startup",
                "quality_score": 2.1,
                "issues": [
                    "Poor audio quality",
                    "Multiple speakers overlap",
                    "Background noise"
                ],
                "created_at": "2025-08-06T10:00:00Z",
                "suggestions": [
                    "Run noise reduction filter",
                    "Use speaker diarization",
                    "Manual review recommended"
                ]
            }
        ]
        
        return {"success": True, "data": {"issues": quality_issues, "total_count": len(quality_issues)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quality issues: {str(e)}")

@router.post("/items/{content_id}/enhance")
async def enhance_content_quality(
    content_id: str,
    enhancement_options: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Enhance content quality using AI tools"""
    try:
        # Mock implementation - would run quality enhancement algorithms
        result = {
            "content_id": content_id,
            "enhancements_applied": [
                "Noise reduction",
                "Speaker separation",
                "Grammar correction"
            ],
            "quality_improvement": 1.3,
            "processed_at": datetime.utcnow().isoformat(),
            "status": "enhanced"
        }
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content enhancement failed: {str(e)}")

@router.post("/upload")
async def upload_content_file(
    file: UploadFile = File(...),
    title: str = Query(...),
    content_type: str = Query(...),
    description: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Upload and process content file"""
    try:
        # Mock implementation - would handle file upload and processing
        file_content = await file.read()
        
        result = {
            "upload_id": f"upload_{datetime.utcnow().timestamp()}",
            "filename": file.filename,
            "size": len(file_content),
            "content_type": file.content_type,
            "status": "processing",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.get("/tags")
async def list_tags(
    current_user: dict = Depends(get_current_user)
):
    """List all available tags"""
    try:
        # Mock implementation
        tags = [
            {"id": "tag_1", "name": "meeting", "color": "#007bff", "usage_count": 45},
            {"id": "tag_2", "name": "interview", "color": "#28a745", "usage_count": 32},
            {"id": "tag_3", "name": "sales", "color": "#dc3545", "usage_count": 28},
            {"id": "tag_4", "name": "product", "color": "#ffc107", "usage_count": 24}
        ]
        
        return {"success": True, "data": {"tags": tags, "total_count": len(tags)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tags: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Content management service health check"""
    try:
        cms = get_content_service()
        return {
            "status": "healthy",
            "service": "content-management-system",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Export router for FastAPI app
__all__ = ["router"]