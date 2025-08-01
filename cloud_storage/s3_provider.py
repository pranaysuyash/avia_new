"""
AWS S3 storage provider implementation
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, BinaryIO
import mimetypes

from .storage_manager import StorageProvider, StorageFile, StorageProviderType

logger = logging.getLogger(__name__)


class S3Provider(StorageProvider):
    """AWS S3 storage provider"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.client = None
        self.bucket_name = credentials.get('bucket_name')
    
    async def authenticate(self) -> bool:
        """Authenticate with AWS S3"""
        try:
            # Mock implementation - in real use, would use boto3
            required_keys = ['access_key_id', 'secret_access_key', 'bucket_name']
            if all(key in self.credentials for key in required_keys):
                logger.info("S3 authentication successful (mock)")
                self.authenticated = True
                return True
            else:
                logger.error("Missing S3 credentials")
                return False
                
        except Exception as e:
            logger.error(f"S3 authentication failed: {e}")
            return False
    
    async def upload_file(
        self,
        file_path: str,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageFile:
        """Upload a file to S3"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Mock implementation
        file_stats = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        logger.info(f"Mock: Uploading {file_path} to S3 bucket {self.bucket_name} at {remote_path}")
        
        return StorageFile(
            id=f"s3_{hash(remote_path)}",
            name=os.path.basename(remote_path),
            path=remote_path,
            size=file_stats.st_size,
            mime_type=mime_type or 'application/octet-stream',
            created_at=datetime.utcnow(),
            modified_at=datetime.fromtimestamp(file_stats.st_mtime),
            provider=StorageProviderType.S3,
            download_url=f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}",
            share_url=f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}",
            metadata=metadata
        )
    
    async def upload_stream(
        self,
        stream: BinaryIO,
        remote_path: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageFile:
        """Upload a file stream to S3"""
        
        logger.info(f"Mock: Uploading stream to S3 bucket {self.bucket_name} at {remote_path}")
        
        stream_size = 0
        stream.seek(0, 2)
        stream_size = stream.tell()
        stream.seek(0)
        
        return StorageFile(
            id=f"s3_stream_{hash(remote_path)}",
            name=os.path.basename(remote_path),
            path=remote_path,
            size=stream_size,
            mime_type=mime_type,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            provider=StorageProviderType.S3,
            download_url=f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}",
            share_url=f"https://{self.bucket_name}.s3.amazonaws.com/{remote_path}",
            metadata=metadata
        )
    
    async def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from S3"""
        
        logger.info(f"Mock: Downloading {file_id} from S3 to {local_path}")
        
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'w') as f:
                f.write(f"Mock S3 file content for {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating mock download file: {e}")
            return False
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from S3"""
        
        logger.info(f"Mock: Deleting {file_id} from S3")
        return True
    
    async def list_files(
        self,
        folder_path: str = "/",
        limit: int = 100
    ) -> List[StorageFile]:
        """List files in an S3 prefix"""
        
        logger.info(f"Mock: Listing files in S3 prefix {folder_path}")
        
        mock_files = []
        for i in range(min(4, limit)):
            mock_files.append(StorageFile(
                id=f"s3_file_{i}",
                name=f"s3_file_{i}.txt",
                path=f"{folder_path}/s3_file_{i}.txt",
                size=256 * (i + 1),
                mime_type="text/plain",
                created_at=datetime.utcnow(),
                modified_at=datetime.utcnow(),
                provider=StorageProviderType.S3,
                download_url=f"https://{self.bucket_name}.s3.amazonaws.com/{folder_path}/s3_file_{i}.txt",
                share_url=f"https://{self.bucket_name}.s3.amazonaws.com/{folder_path}/s3_file_{i}.txt"
            ))
        
        return mock_files
    
    async def create_folder(self, folder_path: str) -> bool:
        """Create a folder (prefix) in S3"""
        
        logger.info(f"Mock: Creating folder {folder_path} in S3")
        # S3 doesn't have real folders, just prefixes
        return True
    
    async def get_file_info(self, file_id: str) -> Optional[StorageFile]:
        """Get file information from S3"""
        
        logger.info(f"Mock: Getting file info for {file_id} from S3")
        
        return StorageFile(
            id=file_id,
            name=f"s3_{file_id}.txt",
            path=f"/files/s3_{file_id}.txt",
            size=2048,
            mime_type="text/plain",
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            provider=StorageProviderType.S3,
            download_url=f"https://{self.bucket_name}.s3.amazonaws.com/files/s3_{file_id}.txt",
            share_url=f"https://{self.bucket_name}.s3.amazonaws.com/files/s3_{file_id}.txt"
        )
    
    async def create_share_link(
        self,
        file_id: str,
        permission: str = "read",
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create a presigned URL for an S3 file"""
        
        logger.info(f"Mock: Creating presigned URL for {file_id}")
        
        # Mock presigned URL (in real implementation, would use boto3 generate_presigned_url)
        expiry = expires_at or (datetime.utcnow() + timedelta(hours=1))
        expiry_timestamp = int(expiry.timestamp())
        
        return f"https://{self.bucket_name}.s3.amazonaws.com/{file_id}?X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=mock_signature_{expiry_timestamp}"
    
    def get_provider_type(self) -> StorageProviderType:
        """Get the provider type"""
        return StorageProviderType.S3


def create_s3_provider(
    access_key_id: str,
    secret_access_key: str,
    bucket_name: str,
    region: str = 'us-east-1'
) -> S3Provider:
    """Create a configured S3 provider"""
    
    credentials = {
        'access_key_id': access_key_id,
        'secret_access_key': secret_access_key,
        'bucket_name': bucket_name,
        'region': region
    }
    
    return S3Provider(credentials)