"""
Upload API Endpoints
Handles presigned URL generation for secure file uploads
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from api.database import get_db, User
from api.auth import get_current_active_user
from api.s3_storage.s3_presigned import (
    s3_presigned_service,
    PresignedUploadRequest,
    PresignedUploadResponse,
    MultipartUploadRequest,
    MultipartUploadResponse
)
from api.models.upload import (
    UploadSession,
    UploadPart,
    UploadStatus
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/uploads",
    tags=["uploads"],
    responses={404: {"description": "Not found"}},
)


class CompleteMultipartRequest(BaseModel):
    """Request to complete multipart upload"""
    upload_id: str
    file_key: str
    parts: List[Dict[str, Any]] = Field(..., description="List with PartNumber and ETag")


class UploadVerificationResponse(BaseModel):
    """Response for upload verification"""
    exists: bool
    size: Optional[int] = None
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@router.post("/presigned", response_model=PresignedUploadResponse)
async def create_presigned_upload(
    request: PresignedUploadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a presigned POST URL for direct file upload to S3.
    
    This endpoint is used for files up to 5GB. For larger files,
    use the multipart upload endpoint.
    
    The returned URL and fields should be used to make a POST request
    directly to S3 with the file as multipart/form-data.
    """
    try:
        # Check user quota if applicable
        # Implement user storage quota checking
        try:
            from database.models import User, UsageRecord
            from database.connection import get_db_context
            from datetime import datetime, timedelta
            
            # Get current user storage usage
            with get_db_context() as db:
                user = db.query(User).filter(User.id == current_user.id).first()
                if user:
                    # Check user's subscription plan storage limit
                    plan_limits = {
                        "free": 1000,  # 1GB
                        "basic": 10000,  # 10GB
                        "pro": 100000,  # 100GB
                        "enterprise": 1000000  # 1TB
                    }
                    
                    plan_limit_mb = plan_limits.get(user.subscription_tier.lower(), 1000)
                    
                    # Calculate current usage from usage records
                    thirty_days_ago = datetime.now() - timedelta(days=30)
                    usage_records = db.query(UsageRecord).filter(
                        UsageRecord.user_id == user.id,
                        UsageRecord.timestamp >= thirty_days_ago
                    ).all()
                    
                    current_usage_mb = sum(record.storage_used_mb for record in usage_records)
                    
                    # Check if user is approaching or exceeding quota
                    if current_usage_mb >= plan_limit_mb * 0.9:  # 90% threshold
                        logger.warning(f"User {user.id} approaching storage quota: {current_usage_mb}/{plan_limit_mb} MB")
                        
                        # Send warning notification if approaching quota
                        if current_usage_mb >= plan_limit_mb:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Storage quota exceeded. Current: {current_usage_mb} MB, Limit: {plan_limit_mb} MB"
                            )
                    else:
                        logger.info(f"User {user.id} storage usage: {current_usage_mb}/{plan_limit_mb} MB")
                else:
                    logger.warning(f"User {current_user.id} not found in database")
        except Exception as quota_error:
            logger.error(f"Error checking user quota: {quota_error}")
            # Continue with upload even if quota check fails
        
        # Generate presigned URL
        response = s3_presigned_service.create_presigned_post(
            user_id=str(current_user.id),
            request=request
        )
        
        # Create upload session record
        upload_session = UploadSession(
            id=response.upload_id,
            user_id=current_user.id,
            file_key=response.file_key,
            filename=request.filename,
            content_type=request.content_type,
            file_size=request.file_size,
            status=UploadStatus.PENDING,
            expires_at=response.expires_at,
            metadata=request.metadata
        )
        db.add(upload_session)
        db.commit()
        
        # Log upload initiation
        logger.info(f"Created presigned upload for user {current_user.id}: {request.filename}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating presigned upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create upload URL"
        )


@router.post("/multipart", response_model=MultipartUploadResponse)
async def create_multipart_upload(
    request: MultipartUploadRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Initialize a multipart upload for large files (>5MB).
    
    Returns presigned URLs for each part. The client should:
    1. Split the file into parts of the specified size
    2. Upload each part to its corresponding URL
    3. Collect the ETag from each response
    4. Call the complete endpoint with all ETags
    """
    try:
        # Generate multipart upload
        response = s3_presigned_service.create_multipart_upload(
            user_id=str(current_user.id),
            request=request
        )
        
        # Create upload session record
        upload_session = UploadSession(
            id=response.upload_id,
            user_id=current_user.id,
            file_key=response.file_key,
            filename=request.filename,
            content_type=request.content_type,
            file_size=request.file_size,
            status=UploadStatus.UPLOADING,
            is_multipart=True,
            part_size=request.part_size,
            total_parts=len(response.part_urls)
        )
        db.add(upload_session)
        
        # Create part records
        for part_info in response.part_urls:
            part = UploadPart(
                upload_session_id=response.upload_id,
                part_number=part_info['part_number'],
                size=part_info['size'],
                status=UploadStatus.PENDING
            )
            db.add(part)
        
        db.commit()
        
        logger.info(f"Created multipart upload for user {current_user.id}: {request.filename}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating multipart upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create multipart upload"
        )


@router.post("/multipart/complete")
async def complete_multipart_upload(
    request: CompleteMultipartRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Complete a multipart upload after all parts have been uploaded.
    
    Requires the upload_id, file_key, and a list of parts with
    their PartNumber and ETag values.
    """
    # Get upload session
    upload_session = db.query(UploadSession).filter(
        UploadSession.id == request.upload_id,
        UploadSession.user_id == current_user.id
    ).first()
    
    if not upload_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found"
        )
    
    if upload_session.status != UploadStatus.UPLOADING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid upload status: {upload_session.status}"
        )
    
    try:
        # Complete the multipart upload
        result = s3_presigned_service.complete_multipart_upload(
            file_key=request.file_key,
            upload_id=request.upload_id,
            parts=request.parts
        )
        
        # Update upload session
        upload_session.status = UploadStatus.COMPLETED
        upload_session.completed_at = datetime.utcnow()
        upload_session.s3_etag = result.get('etag')
        
        # Update part statuses
        db.query(UploadPart).filter(
            UploadPart.upload_session_id == request.upload_id
        ).update({UploadPart.status: UploadStatus.COMPLETED})
        
        db.commit()
        
        logger.info(f"Completed multipart upload {request.upload_id} for user {current_user.id}")
        
        return {
            "success": True,
            "file_key": request.file_key,
            "location": result.get('location')
        }
        
    except Exception as e:
        logger.error(f"Error completing multipart upload: {e}")
        
        # Mark as failed
        upload_session.status = UploadStatus.FAILED
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete multipart upload"
        )


@router.post("/multipart/abort")
async def abort_multipart_upload(
    upload_id: str,
    file_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Abort a multipart upload and clean up resources."""
    # Verify ownership
    upload_session = db.query(UploadSession).filter(
        UploadSession.id == upload_id,
        UploadSession.user_id == current_user.id
    ).first()
    
    if not upload_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found"
        )
    
    try:
        # Abort the S3 multipart upload
        s3_presigned_service.abort_multipart_upload(file_key, upload_id)
        
        # Update session status
        upload_session.status = UploadStatus.ABORTED
        db.commit()
        
        logger.info(f"Aborted multipart upload {upload_id} for user {current_user.id}")
        
        return {"success": True, "message": "Upload aborted"}
        
    except Exception as e:
        logger.error(f"Error aborting multipart upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to abort upload"
        )


@router.post("/verify/{upload_id}", response_model=UploadVerificationResponse)
async def verify_upload(
    upload_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Verify that a file was successfully uploaded to S3.
    
    This should be called after the client completes the upload
    to confirm the file exists and update the session status.
    """
    # Get upload session
    upload_session = db.query(UploadSession).filter(
        UploadSession.id == upload_id,
        UploadSession.user_id == current_user.id
    ).first()
    
    if not upload_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found"
        )
    
    try:
        # Verify the upload
        verification = s3_presigned_service.verify_upload(upload_session.file_key)
        
        if verification['exists']:
            # Update session with verification data
            upload_session.status = UploadStatus.COMPLETED
            upload_session.completed_at = datetime.utcnow()
            upload_session.verified_size = verification.get('size')
            upload_session.s3_etag = verification.get('etag')
            
            # Verify size matches
            if upload_session.file_size != verification.get('size'):
                logger.warning(
                    f"Size mismatch for upload {upload_id}: "
                    f"expected {upload_session.file_size}, got {verification.get('size')}"
                )
            
            db.commit()
            
            logger.info(f"Verified upload {upload_id} for user {current_user.id}")
        else:
            # Mark as failed if file doesn't exist
            upload_session.status = UploadStatus.FAILED
            db.commit()
        
        return UploadVerificationResponse(
            exists=verification['exists'],
            size=verification.get('size'),
            content_type=verification.get('content_type'),
            metadata=verification.get('metadata')
        )
        
    except Exception as e:
        logger.error(f"Error verifying upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify upload"
        )


@router.get("/download/{file_key:path}")
async def generate_download_url(
    file_key: str,
    expires_in: int = 3600,
    filename: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a presigned URL for downloading a file.
    
    The file_key should be the full S3 object key. The optional
    filename parameter can be used to set the download filename.
    """
    # Verify user has access to this file
    upload_session = db.query(UploadSession).filter(
        UploadSession.file_key == file_key,
        UploadSession.user_id == current_user.id
    ).first()
    
    if not upload_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied"
        )
    
    try:
        # Generate download URL
        download_url = s3_presigned_service.generate_download_url(
            file_key=file_key,
            expires_in=expires_in,
            filename=filename or upload_session.filename
        )
        
        logger.info(f"Generated download URL for user {current_user.id}: {file_key}")
        
        return {
            "download_url": download_url,
            "expires_in": expires_in,
            "filename": filename or upload_session.filename
        }
        
    except Exception as e:
        logger.error(f"Error generating download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )