"""
Storage Service
Handles file storage with support for local and cloud storage (S3, GCS, Azure)
"""

import os
import hashlib
import shutil
import logging
from typing import Optional, Dict, Any, BinaryIO, List
from datetime import datetime, timedelta
import mimetypes
from pathlib import Path
import tempfile

import boto3
from botocore.exceptions import ClientError
from google.cloud import storage as gcs
from azure.storage.blob import BlobServiceClient, BlobClient
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


class StorageProvider:
    """Base storage provider interface"""
    
    async def upload_file(self, file_path: str, key: str) -> str:
        raise NotImplementedError
    
    async def download_file(self, key: str, destination: str) -> str:
        raise NotImplementedError
    
    async def delete_file(self, key: str) -> bool:
        raise NotImplementedError
    
    async def file_exists(self, key: str) -> bool:
        raise NotImplementedError
    
    async def get_file_url(self, key: str, expiry: int = 3600) -> str:
        raise NotImplementedError
    
    async def list_files(self, prefix: str = "") -> List[str]:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    """Local file system storage provider"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to local storage"""
        destination = self.base_path / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, destination)
        return str(destination)
    
    async def download_file(self, key: str, destination: str) -> str:
        """Download file from local storage"""
        source = self.base_path / key
        if not source.exists():
            raise FileNotFoundError(f"File not found: {key}")
        
        shutil.copy2(source, destination)
        return destination
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from local storage"""
        file_path = self.base_path / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in local storage"""
        return (self.base_path / key).exists()
    
    async def get_file_url(self, key: str, expiry: int = 3600) -> str:
        """Get file URL (local path)"""
        return f"file://{self.base_path / key}"
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in local storage"""
        path = self.base_path / prefix
        if not path.exists():
            return []
        
        files = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.base_path)
                files.append(str(relative_path))
        
        return files


class S3StorageProvider(StorageProvider):
    """AWS S3 storage provider"""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1', **kwargs):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region, **kwargs)
        self.s3_resource = boto3.resource('s3', region_name=region, **kwargs)
    
    async def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to S3"""
        try:
            # Detect content type
            content_type, _ = mimetypes.guess_type(file_path)
            
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs=extra_args
            )
            
            return f"s3://{self.bucket_name}/{key}"
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def download_file(self, key: str, destination: str) -> str:
        """Download file from S3"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                key,
                destination
            )
            return destination
            
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            raise
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError:
            return False
    
    async def get_file_url(self, key: str, expiry: int = 3600) -> str:
        """Generate presigned URL for S3 object"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiry
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
            
            return files
            
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []


class GCSStorageProvider(StorageProvider):
    """Google Cloud Storage provider"""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        self.bucket_name = bucket_name
        self.client = gcs.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
    
    async def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to GCS"""
        blob = self.bucket.blob(key)
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type:
            blob.content_type = content_type
        
        blob.upload_from_filename(file_path)
        return f"gs://{self.bucket_name}/{key}"
    
    async def download_file(self, key: str, destination: str) -> str:
        """Download file from GCS"""
        blob = self.bucket.blob(key)
        blob.download_to_filename(destination)
        return destination
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from GCS"""
        blob = self.bucket.blob(key)
        blob.delete()
        return True
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in GCS"""
        blob = self.bucket.blob(key)
        return blob.exists()
    
    async def get_file_url(self, key: str, expiry: int = 3600) -> str:
        """Generate signed URL for GCS object"""
        blob = self.bucket.blob(key)
        url = blob.generate_signed_url(
            expiration=datetime.utcnow() + timedelta(seconds=expiry),
            method='GET'
        )
        return url
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in GCS bucket"""
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]


class AzureStorageProvider(StorageProvider):
    """Azure Blob Storage provider"""
    
    def __init__(self, connection_string: str, container_name: str):
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
    
    async def upload_file(self, file_path: str, key: str) -> str:
        """Upload file to Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(key)
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        
        with open(file_path, 'rb') as data:
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings={'content_type': content_type} if content_type else None
            )
        
        return f"azure://{self.container_name}/{key}"
    
    async def download_file(self, key: str, destination: str) -> str:
        """Download file from Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(key)
        
        with open(destination, 'wb') as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())
        
        return destination
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(key)
        blob_client.delete_blob()
        return True
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in Azure Blob Storage"""
        blob_client = self.container_client.get_blob_client(key)
        return blob_client.exists()
    
    async def get_file_url(self, key: str, expiry: int = 3600) -> str:
        """Generate SAS URL for Azure Blob"""
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        
        sas_token = generate_blob_sas(
            account_name=self.blob_service_client.account_name,
            container_name=self.container_name,
            blob_name=key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(seconds=expiry)
        )
        
        return f"{self.blob_service_client.url}{self.container_name}/{key}?{sas_token}"
    
    async def list_files(self, prefix: str = "") -> List[str]:
        """List files in Azure container"""
        blobs = self.container_client.list_blobs(name_starts_with=prefix)
        return [blob.name for blob in blobs]


class StorageService:
    """Unified storage service with multiple provider support"""
    
    def __init__(self, provider: str = 'local', **provider_config):
        self.provider_name = provider
        self.provider = self._initialize_provider(provider, **provider_config)
        self.cache_path = Path(tempfile.gettempdir()) / "storage_cache"
        self.cache_path.mkdir(exist_ok=True)
    
    def _initialize_provider(self, provider: str, **config) -> StorageProvider:
        """Initialize storage provider"""
        
        if provider == 'local':
            base_path = config.get('base_path', './storage')
            return LocalStorageProvider(base_path)
        
        elif provider == 's3':
            return S3StorageProvider(
                bucket_name=config['bucket_name'],
                region=config.get('region', 'us-east-1'),
                aws_access_key_id=config.get('aws_access_key_id'),
                aws_secret_access_key=config.get('aws_secret_access_key')
            )
        
        elif provider == 'gcs':
            return GCSStorageProvider(
                bucket_name=config['bucket_name'],
                project_id=config.get('project_id')
            )
        
        elif provider == 'azure':
            return AzureStorageProvider(
                connection_string=config['connection_string'],
                container_name=config['container_name']
            )
        
        else:
            raise ValueError(f"Unsupported storage provider: {provider}")
    
    async def upload_file(
        self,
        file_path: str,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Upload file to storage"""
        
        # Generate key if not provided
        if not key:
            file_hash = self._calculate_file_hash(file_path)
            extension = Path(file_path).suffix
            key = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{file_hash}{extension}"
        
        # Upload file
        storage_path = await self.provider.upload_file(file_path, key)
        
        # Store metadata if provided
        if metadata:
            metadata_key = f"{key}.metadata.json"
            metadata_path = self.cache_path / "metadata.json"
            
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f)
            
            await self.provider.upload_file(str(metadata_path), metadata_key)
        
        logger.info(f"File uploaded: {storage_path}")
        return storage_path
    
    async def download_file(
        self,
        key: str,
        destination: Optional[str] = None
    ) -> str:
        """Download file from storage"""
        
        # Use cache if no destination specified
        if not destination:
            destination = self.cache_path / Path(key).name
        
        # Download file
        file_path = await self.provider.download_file(key, str(destination))
        
        logger.info(f"File downloaded: {file_path}")
        return file_path
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from storage"""
        
        # Delete main file
        success = await self.provider.delete_file(key)
        
        # Try to delete metadata
        metadata_key = f"{key}.metadata.json"
        if await self.provider.file_exists(metadata_key):
            await self.provider.delete_file(metadata_key)
        
        logger.info(f"File deleted: {key}")
        return success
    
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in storage"""
        return await self.provider.file_exists(key)
    
    async def get_file_url(
        self,
        key: str,
        expiry: int = 3600
    ) -> str:
        """Get temporary URL for file access"""
        return await self.provider.get_file_url(key, expiry)
    
    async def list_files(
        self,
        prefix: str = "",
        max_results: Optional[int] = None
    ) -> List[str]:
        """List files in storage"""
        
        files = await self.provider.list_files(prefix)
        
        if max_results:
            files = files[:max_results]
        
        return files
    
    async def copy_file(
        self,
        source_key: str,
        destination_key: str
    ) -> str:
        """Copy file within storage"""
        
        # Download to temp location
        temp_file = self.cache_path / "temp_copy"
        await self.provider.download_file(source_key, str(temp_file))
        
        # Upload to new location
        result = await self.provider.upload_file(str(temp_file), destination_key)
        
        # Clean up temp file
        temp_file.unlink()
        
        return result
    
    async def move_file(
        self,
        source_key: str,
        destination_key: str
    ) -> str:
        """Move file within storage"""
        
        # Copy file
        result = await self.copy_file(source_key, destination_key)
        
        # Delete original
        await self.delete_file(source_key)
        
        return result
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()[:16]  # Use first 16 characters
    
    async def get_file_info(self, key: str) -> Dict[str, Any]:
        """Get file information"""
        
        # Check if file exists
        if not await self.file_exists(key):
            return None
        
        # Try to get metadata
        metadata_key = f"{key}.metadata.json"
        metadata = {}
        
        if await self.provider.file_exists(metadata_key):
            metadata_path = self.cache_path / "temp_metadata.json"
            await self.provider.download_file(metadata_key, str(metadata_path))
            
            with open(metadata_path, 'r') as f:
                import json
                metadata = json.load(f)
            
            metadata_path.unlink()
        
        return {
            'key': key,
            'exists': True,
            'url': await self.get_file_url(key),
            'metadata': metadata
        }