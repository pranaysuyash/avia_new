"""
S3 Presigned URL Service
Handles secure direct uploads to S3 using presigned URLs
"""

import os
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from botocore.exceptions import ClientError
import hashlib
import mimetypes
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class PresignedUploadRequest(BaseModel):
    """Request model for presigned upload URL"""
    filename: str
    content_type: str
    file_size: int = Field(gt=0, le=5368709120)  # Max 5GB
    metadata: Optional[Dict[str, str]] = None


class PresignedUploadResponse(BaseModel):
    """Response model for presigned upload URL"""
    upload_id: str
    upload_url: str
    upload_fields: Dict[str, str]
    file_key: str
    expires_at: datetime


class MultipartUploadRequest(BaseModel):
    """Request model for multipart upload initialization"""
    filename: str
    content_type: str
    file_size: int = Field(gt=5242880)  # Min 5MB for multipart
    part_size: int = Field(default=10485760, ge=5242880)  # Default 10MB, min 5MB


class MultipartUploadResponse(BaseModel):
    """Response model for multipart upload"""
    upload_id: str
    file_key: str
    part_urls: List[Dict[str, any]]
    part_size: int


class S3PresignedService:
    """Service for handling S3 presigned URL operations"""
    
    def __init__(
        self,
        bucket_name: str = None,
        region_name: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        url_expiration: int = 3600,  # 1 hour default
        max_file_size: int = 5368709120,  # 5GB default
        allowed_content_types: List[str] = None
    ):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.url_expiration = url_expiration
        self.max_file_size = max_file_size
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            region_name=self.region_name,
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        # Allowed content types
        self.allowed_content_types = allowed_content_types or [
            'audio/mpeg',
            'audio/mp3',
            'audio/wav',
            'audio/webm',
            'audio/ogg',
            'audio/m4a',
            'video/mp4',
            'video/webm',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'application/octet-stream'  # For unknown types
        ]
    
    def generate_file_key(self, user_id: str, filename: str) -> str:
        """Generate a unique S3 key for the file"""
        # Clean filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '.-_')
        
        # Generate unique path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Create hierarchical structure
        return f"uploads/{user_id}/{timestamp}/{unique_id}_{safe_filename}"
    
    def validate_content_type(self, content_type: str) -> bool:
        """Validate if content type is allowed"""
        return content_type in self.allowed_content_types
    
    def create_presigned_post(
        self,
        user_id: str,
        request: PresignedUploadRequest
    ) -> PresignedUploadResponse:
        """
        Create a presigned POST URL for direct upload to S3
        Used for files up to 5GB
        """
        # Validate content type
        if not self.validate_content_type(request.content_type):
            raise ValueError(f"Content type {request.content_type} not allowed")
        
        # Validate file size
        if request.file_size > self.max_file_size:
            raise ValueError(f"File size exceeds maximum of {self.max_file_size} bytes")
        
        # Generate file key
        file_key = self.generate_file_key(user_id, request.filename)
        
        # Set up conditions and fields
        conditions = [
            ["content-length-range", 0, request.file_size + 1024],  # Allow slight overhead
            {"Content-Type": request.content_type},
            {"x-amz-meta-user-id": user_id},
            {"x-amz-meta-original-filename": request.filename},
        ]
        
        fields = {
            "Content-Type": request.content_type,
            "x-amz-meta-user-id": user_id,
            "x-amz-meta-original-filename": request.filename,
            "x-amz-meta-upload-timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add custom metadata if provided
        if request.metadata:
            for key, value in request.metadata.items():
                meta_key = f"x-amz-meta-{key}"
                conditions.append({meta_key: value})
                fields[meta_key] = value
        
        try:
            # Generate presigned POST
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=file_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=self.url_expiration
            )
            
            # Create response
            upload_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(seconds=self.url_expiration)
            
            return PresignedUploadResponse(
                upload_id=upload_id,
                upload_url=response['url'],
                upload_fields=response['fields'],
                file_key=file_key,
                expires_at=expires_at
            )
            
        except ClientError as e:
            logger.error(f"Error generating presigned POST: {e}")
            raise
    
    def create_multipart_upload(
        self,
        user_id: str,
        request: MultipartUploadRequest
    ) -> MultipartUploadResponse:
        """
        Initialize multipart upload for large files (>5MB)
        Returns presigned URLs for each part
        """
        # Validate content type
        if not self.validate_content_type(request.content_type):
            raise ValueError(f"Content type {request.content_type} not allowed")
        
        # Generate file key
        file_key = self.generate_file_key(user_id, request.filename)
        
        # Calculate number of parts
        num_parts = (request.file_size + request.part_size - 1) // request.part_size
        
        try:
            # Initialize multipart upload
            response = self.s3_client.create_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                ContentType=request.content_type,
                Metadata={
                    'user-id': user_id,
                    'original-filename': request.filename,
                    'upload-timestamp': datetime.utcnow().isoformat(),
                }
            )
            
            upload_id = response['UploadId']
            
            # Generate presigned URLs for each part
            part_urls = []
            for part_number in range(1, num_parts + 1):
                presigned_url = self.s3_client.generate_presigned_url(
                    'upload_part',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_key,
                        'UploadId': upload_id,
                        'PartNumber': part_number
                    },
                    ExpiresIn=self.url_expiration
                )
                
                part_urls.append({
                    'part_number': part_number,
                    'url': presigned_url,
                    'size': min(request.part_size, 
                               request.file_size - (part_number - 1) * request.part_size)
                })
            
            return MultipartUploadResponse(
                upload_id=upload_id,
                file_key=file_key,
                part_urls=part_urls,
                part_size=request.part_size
            )
            
        except ClientError as e:
            logger.error(f"Error creating multipart upload: {e}")
            raise
    
    def complete_multipart_upload(
        self,
        file_key: str,
        upload_id: str,
        parts: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Complete a multipart upload
        
        Args:
            file_key: S3 object key
            upload_id: Multipart upload ID
            parts: List of dicts with 'PartNumber' and 'ETag'
        """
        try:
            response = self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            return {
                'location': response.get('Location'),
                'etag': response.get('ETag'),
                'version_id': response.get('VersionId')
            }
            
        except ClientError as e:
            logger.error(f"Error completing multipart upload: {e}")
            raise
    
    def abort_multipart_upload(self, file_key: str, upload_id: str):
        """Abort a multipart upload"""
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=file_key,
                UploadId=upload_id
            )
        except ClientError as e:
            logger.error(f"Error aborting multipart upload: {e}")
            raise
    
    def generate_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> str:
        """Generate a presigned URL for downloading a file"""
        params = {
            'Bucket': self.bucket_name,
            'Key': file_key
        }
        
        # Add content disposition for custom filename
        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise
    
    def verify_upload(self, file_key: str) -> Dict[str, any]:
        """Verify that a file was successfully uploaded"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            return {
                'exists': True,
                'size': response.get('ContentLength'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return {'exists': False}
            raise


# Global instance
s3_presigned_service = S3PresignedService()