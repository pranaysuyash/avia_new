"""
File Storage Service
Handles file uploads/downloads with S3-compatible storage (MinIO/AWS S3)
"""

import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Tuple, BinaryIO
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """S3-compatible storage service for audio/video files"""
    
    def __init__(self):
        # Get configuration from environment
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("STORAGE_BUCKET", "transcriptions")
        self.use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        # Initialize S3 client
        self.s3_client = self._create_client()
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _create_client(self):
        """Create S3 client with proper configuration"""
        # Build endpoint URL
        protocol = "https" if self.use_ssl else "http"
        endpoint = f"{protocol}://{self.endpoint_url}"
        
        # Create client
        try:
            client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )
            return client
        except Exception as e:
            logger.error(f"Failed to create S3 client: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    logger.info(f"Created bucket '{self.bucket_name}'")
                    
                    # Set bucket policy for public read (optional)
                    self._set_bucket_policy()
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def _set_bucket_policy(self):
        """Set bucket policy for controlled access"""
        # This is optional - you might want private buckets in production
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/public/*"
                }
            ]
        }
        
        try:
            import json
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(policy)
            )
        except Exception as e:
            logger.warning(f"Could not set bucket policy: {e}")
    
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        user_id: int,
        content_type: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Upload a file to S3
        
        Returns:
            Tuple of (object_key, file_url, file_size)
        """
        # Generate unique object key
        file_extension = os.path.splitext(filename)[1]
        object_key = f"uploads/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4()}{file_extension}"
        
        # Detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
        
        try:
            # Get file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            # Upload file
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {
                        'original_filename': filename,
                        'user_id': str(user_id),
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                }
            )
            
            # Generate file URL
            file_url = self.get_file_url(object_key)
            
            logger.info(f"Uploaded file: {object_key} (size: {file_size} bytes)")
            return object_key, file_url, file_size
            
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def download_file(self, object_key: str) -> bytes:
        """Download a file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found: {object_key}")
            logger.error(f"Failed to download file: {e}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted file: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def get_file_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def get_upload_url(
        self,
        filename: str,
        user_id: int,
        content_type: Optional[str] = None,
        expires_in: int = 3600
    ) -> Tuple[str, str]:
        """
        Generate a presigned URL for direct upload from client
        
        Returns:
            Tuple of (upload_url, object_key)
        """
        # Generate object key
        file_extension = os.path.splitext(filename)[1]
        object_key = f"uploads/{user_id}/{datetime.utcnow().strftime('%Y/%m/%d')}/{uuid.uuid4()}{file_extension}"
        
        # Detect content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
        
        try:
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields={
                    'Content-Type': content_type,
                    'x-amz-meta-original_filename': filename,
                    'x-amz-meta-user_id': str(user_id)
                },
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 0, 500 * 1024 * 1024]  # Max 500MB
                ],
                ExpiresIn=expires_in
            )
            
            return response['url'], object_key
        except Exception as e:
            logger.error(f"Failed to generate upload URL: {e}")
            raise
    
    def file_exists(self, object_key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
    
    def get_file_metadata(self, object_key: str) -> dict:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', 'application/octet-stream'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {}),
                'etag': response.get('ETag', '').strip('"')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File not found: {object_key}")
            raise
    
    def list_user_files(self, user_id: int, prefix: Optional[str] = None) -> list:
        """List all files for a user"""
        base_prefix = f"uploads/{user_id}/"
        if prefix:
            base_prefix += prefix
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=base_prefix,
                MaxKeys=1000
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def get_storage_stats(self, user_id: int) -> dict:
        """Get storage statistics for a user"""
        files = self.list_user_files(user_id)
        
        total_size = sum(f['size'] for f in files)
        file_count = len(files)
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'files': files
        }

# Singleton instance
storage_service = StorageService()

# Export for easy access
__all__ = ['storage_service', 'StorageService']