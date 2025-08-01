"""
Cloud storage management system
"""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, BinaryIO
import mimetypes

logger = logging.getLogger(__name__)


class StorageProviderType(Enum):
    """Types of cloud storage providers"""
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    LOCAL = "local"


@dataclass
class StorageFile:
    """Represents a file in cloud storage"""
    id: str
    name: str
    path: str
    size: int
    mime_type: str
    created_at: datetime
    modified_at: datetime
    provider: StorageProviderType
    download_url: Optional[str] = None
    share_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StorageCredentials:
    """Storage provider credentials"""
    provider: StorageProviderType
    credentials: Dict[str, Any]
    active: bool = True
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class StorageProvider(ABC):
    """Abstract base class for cloud storage providers"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.authenticated = False
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the storage provider"""
        pass
    
    @abstractmethod
    async def upload_file(
        self,
        file_path: str,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageFile:
        """Upload a file to cloud storage"""
        pass
    
    @abstractmethod
    async def upload_stream(
        self,
        stream: BinaryIO,
        remote_path: str,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageFile:
        """Upload a file stream to cloud storage"""
        pass
    
    @abstractmethod
    async def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from cloud storage"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file from cloud storage"""
        pass
    
    @abstractmethod
    async def list_files(
        self,
        folder_path: str = "/",
        limit: int = 100
    ) -> List[StorageFile]:
        """List files in a folder"""
        pass
    
    @abstractmethod
    async def create_folder(self, folder_path: str) -> bool:
        """Create a folder"""
        pass
    
    @abstractmethod
    async def get_file_info(self, file_id: str) -> Optional[StorageFile]:
        """Get file information"""
        pass
    
    @abstractmethod
    async def create_share_link(
        self,
        file_id: str,
        permission: str = "read",
        expires_at: Optional[datetime] = None
    ) -> str:
        """Create a shareable link for a file"""
        pass
    
    @abstractmethod
    def get_provider_type(self) -> StorageProviderType:
        """Get the provider type"""
        pass


class CloudStorageManager:
    """Manages multiple cloud storage providers"""
    
    def __init__(self):
        self.providers: Dict[StorageProviderType, StorageProvider] = {}
        self.default_provider: Optional[StorageProviderType] = None
        
        logger.info("Cloud storage manager initialized")
    
    def add_provider(
        self,
        provider_type: StorageProviderType,
        provider: StorageProvider
    ):
        """Add a storage provider"""
        self.providers[provider_type] = provider
        
        # Set as default if it's the first provider
        if self.default_provider is None:
            self.default_provider = provider_type
        
        logger.info(f"Added {provider_type.value} storage provider")
    
    def remove_provider(self, provider_type: StorageProviderType):
        """Remove a storage provider"""
        if provider_type in self.providers:
            del self.providers[provider_type]
            
            # Update default if needed
            if self.default_provider == provider_type:
                self.default_provider = next(iter(self.providers.keys()), None)
            
            logger.info(f"Removed {provider_type.value} storage provider")
    
    def get_provider(self, provider_type: StorageProviderType) -> Optional[StorageProvider]:
        """Get a storage provider"""
        return self.providers.get(provider_type)
    
    def list_providers(self) -> List[StorageProviderType]:
        """List available providers"""
        return list(self.providers.keys())
    
    def set_default_provider(self, provider_type: StorageProviderType):
        """Set the default storage provider"""
        if provider_type in self.providers:
            self.default_provider = provider_type
            logger.info(f"Set {provider_type.value} as default provider")
    
    async def authenticate_provider(self, provider_type: StorageProviderType) -> bool:
        """Authenticate a storage provider"""
        provider = self.providers.get(provider_type)
        if not provider:
            return False
        
        try:
            result = await provider.authenticate()
            if result:
                logger.info(f"Successfully authenticated {provider_type.value}")
            else:
                logger.warning(f"Failed to authenticate {provider_type.value}")
            return result
        except Exception as e:
            logger.error(f"Error authenticating {provider_type.value}: {e}")
            return False
    
    async def upload_file(
        self,
        file_path: str,
        remote_path: str,
        provider_type: Optional[StorageProviderType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[StorageFile]:
        """Upload a file using specified or default provider"""
        
        provider_type = provider_type or self.default_provider
        if not provider_type:
            logger.error("No storage provider available")
            return None
        
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider {provider_type.value} not found")
            return None
        
        if not provider.authenticated:
            if not await self.authenticate_provider(provider_type):
                logger.error(f"Failed to authenticate {provider_type.value}")
                return None
        
        try:
            # Add default metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'uploaded_by': 'transcription_app',
                'upload_time': datetime.utcnow().isoformat(),
                'original_path': file_path
            })
            
            result = await provider.upload_file(file_path, remote_path, metadata)
            logger.info(f"Successfully uploaded {file_path} to {provider_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading file to {provider_type.value}: {e}")
            return None
    
    async def upload_stream(
        self,
        stream: BinaryIO,
        remote_path: str,
        mime_type: str,
        provider_type: Optional[StorageProviderType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[StorageFile]:
        """Upload a file stream using specified or default provider"""
        
        provider_type = provider_type or self.default_provider
        if not provider_type:
            logger.error("No storage provider available")
            return None
        
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider {provider_type.value} not found")
            return None
        
        if not provider.authenticated:
            if not await self.authenticate_provider(provider_type):
                logger.error(f"Failed to authenticate {provider_type.value}")
                return None
        
        try:
            # Add default metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'uploaded_by': 'transcription_app',
                'upload_time': datetime.utcnow().isoformat(),
                'mime_type': mime_type
            })
            
            result = await provider.upload_stream(stream, remote_path, mime_type, metadata)
            logger.info(f"Successfully uploaded stream to {provider_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading stream to {provider_type.value}: {e}")
            return None
    
    async def download_file(
        self,
        file_id: str,
        local_path: str,
        provider_type: Optional[StorageProviderType] = None
    ) -> bool:
        """Download a file using specified or default provider"""
        
        provider_type = provider_type or self.default_provider
        if not provider_type:
            logger.error("No storage provider available")
            return False
        
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider {provider_type.value} not found")
            return False
        
        if not provider.authenticated:
            if not await self.authenticate_provider(provider_type):
                logger.error(f"Failed to authenticate {provider_type.value}")
                return False
        
        try:
            result = await provider.download_file(file_id, local_path)
            if result:
                logger.info(f"Successfully downloaded file from {provider_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error downloading file from {provider_type.value}: {e}")
            return False
    
    async def list_files(
        self,
        folder_path: str = "/",
        provider_type: Optional[StorageProviderType] = None,
        limit: int = 100
    ) -> List[StorageFile]:
        """List files using specified or default provider"""
        
        provider_type = provider_type or self.default_provider
        if not provider_type:
            logger.error("No storage provider available")
            return []
        
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider {provider_type.value} not found")
            return []
        
        if not provider.authenticated:
            if not await self.authenticate_provider(provider_type):
                logger.error(f"Failed to authenticate {provider_type.value}")
                return []
        
        try:
            result = await provider.list_files(folder_path, limit)
            logger.info(f"Listed {len(result)} files from {provider_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error listing files from {provider_type.value}: {e}")
            return []
    
    async def create_share_link(
        self,
        file_id: str,
        provider_type: Optional[StorageProviderType] = None,
        permission: str = "read",
        expires_at: Optional[datetime] = None
    ) -> Optional[str]:
        """Create a share link using specified or default provider"""
        
        provider_type = provider_type or self.default_provider
        if not provider_type:
            logger.error("No storage provider available")
            return None
        
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider {provider_type.value} not found")
            return None
        
        if not provider.authenticated:
            if not await self.authenticate_provider(provider_type):
                logger.error(f"Failed to authenticate {provider_type.value}")
                return None
        
        try:
            result = await provider.create_share_link(file_id, permission, expires_at)
            logger.info(f"Created share link using {provider_type.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating share link with {provider_type.value}: {e}")
            return None
    
    async def sync_transcript_to_cloud(
        self,
        transcript_id: str,
        transcript_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        provider_type: Optional[StorageProviderType] = None
    ) -> Optional[StorageFile]:
        """Sync a transcript to cloud storage"""
        
        # Create temporary file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            transcript_data = {
                'id': transcript_id,
                'content': transcript_content,
                'metadata': metadata or {},
                'exported_at': datetime.utcnow().isoformat()
            }
            json.dump(transcript_data, f, indent=2)
            temp_path = f.name
        
        try:
            # Upload to cloud storage
            remote_path = f"transcripts/{transcript_id}.json"
            result = await self.upload_file(
                temp_path,
                remote_path,
                provider_type,
                metadata
            )
            
            return result
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    async def backup_audio_file(
        self,
        audio_file_path: str,
        transcript_id: str,
        provider_type: Optional[StorageProviderType] = None
    ) -> Optional[StorageFile]:
        """Backup an audio file to cloud storage"""
        
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        
        # Determine file extension and MIME type
        _, ext = os.path.splitext(audio_file_path)
        mime_type, _ = mimetypes.guess_type(audio_file_path)
        
        # Create remote path
        remote_path = f"audio/{transcript_id}{ext}"
        
        # Add metadata
        metadata = {
            'transcript_id': transcript_id,
            'file_type': 'audio',
            'original_filename': os.path.basename(audio_file_path),
            'mime_type': mime_type
        }
        
        result = await self.upload_file(
            audio_file_path,
            remote_path,
            provider_type,
            metadata
        )
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cloud storage statistics"""
        return {
            'total_providers': len(self.providers),
            'available_providers': [p.value for p in self.providers.keys()],
            'default_provider': self.default_provider.value if self.default_provider else None,
            'authenticated_providers': [
                p.value for p, provider in self.providers.items()
                if provider.authenticated
            ]
        }


# Global cloud storage manager instance
cloud_storage_manager = CloudStorageManager()