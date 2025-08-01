"""
Integration manager for task 23 - API capabilities, webhooks, cloud storage, plugins, and SSO
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import all integration components
from webhooks import webhook_manager, WebhookEventType
from cloud_storage import cloud_storage_manager, StorageProviderType
from cloud_storage.google_drive import create_google_drive_provider
from cloud_storage.dropbox_provider import create_dropbox_provider
from cloud_storage.s3_provider import create_s3_provider
from plugins import plugin_manager, PluginType
from plugins.entity_plugin import DefaultEntityExtractionPlugin, MedicalEntityExtractionPlugin
from sso import initialize_sso_manager

logger = logging.getLogger(__name__)


class IntegrationManager:
    """Manages all integration capabilities for task 23"""
    
    def __init__(self):
        self.initialized = False
        self.webhook_system_running = False
        self.cloud_providers_configured = []
        self.plugins_loaded = 0
        self.sso_enabled = False
        
        logger.info("Integration manager initialized")
    
    async def initialize_all_systems(self, config: Dict[str, Any]) -> bool:
        """Initialize all integration systems"""
        try:
            logger.info("Initializing integration systems...")
            
            # Initialize webhook system
            await self._initialize_webhooks(config.get('webhooks', {}))
            
            # Initialize cloud storage
            await self._initialize_cloud_storage(config.get('cloud_storage', {}))
            
            # Initialize plugin system
            await self._initialize_plugins(config.get('plugins', {}))
            
            # Initialize SSO
            await self._initialize_sso(config.get('sso', {}))
            
            self.initialized = True
            logger.info("All integration systems initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing integration systems: {e}")
            return False
    
    async def _initialize_webhooks(self, config: Dict[str, Any]):
        """Initialize webhook system"""
        logger.info("Initializing webhook system...")
        
        # Start webhook workers if enabled
        if config.get('enabled', True):
            await webhook_manager.start_workers()
            self.webhook_system_running = True
            
            # Add default webhook subscriptions from config
            subscriptions = config.get('subscriptions', [])
            for sub_config in subscriptions:
                try:
                    event_types = [
                        WebhookEventType(event) for event in sub_config.get('event_types', [])
                    ]
                    
                    webhook_manager.add_subscription(
                        url=sub_config['url'],
                        event_types=event_types,
                        secret=sub_config.get('secret'),
                        headers=sub_config.get('headers', {}),
                        timeout=sub_config.get('timeout', 30),
                        retry_count=sub_config.get('retry_count', 3)
                    )
                    
                    logger.info(f"Added webhook subscription: {sub_config['url']}")
                    
                except Exception as e:
                    logger.error(f"Error adding webhook subscription: {e}")
        
        logger.info("Webhook system initialized")
    
    async def _initialize_cloud_storage(self, config: Dict[str, Any]):
        """Initialize cloud storage providers"""
        logger.info("Initializing cloud storage providers...")
        
        # Google Drive
        google_config = config.get('google_drive', {})
        if google_config.get('enabled', False):
            try:
                provider = create_google_drive_provider(
                    client_id=google_config['client_id'],
                    client_secret=google_config['client_secret'],
                    refresh_token=google_config.get('refresh_token')
                )
                
                cloud_storage_manager.add_provider(StorageProviderType.GOOGLE_DRIVE, provider)
                
                if await cloud_storage_manager.authenticate_provider(StorageProviderType.GOOGLE_DRIVE):
                    self.cloud_providers_configured.append('google_drive')
                    logger.info("Google Drive provider configured")
                
            except Exception as e:
                logger.error(f"Error configuring Google Drive: {e}")
        
        # Dropbox
        dropbox_config = config.get('dropbox', {})
        if dropbox_config.get('enabled', False):
            try:
                provider = create_dropbox_provider(
                    access_token=dropbox_config['access_token']
                )
                
                cloud_storage_manager.add_provider(StorageProviderType.DROPBOX, provider)
                
                if await cloud_storage_manager.authenticate_provider(StorageProviderType.DROPBOX):
                    self.cloud_providers_configured.append('dropbox')
                    logger.info("Dropbox provider configured")
                
            except Exception as e:
                logger.error(f"Error configuring Dropbox: {e}")
        
        # AWS S3
        s3_config = config.get('s3', {})
        if s3_config.get('enabled', False):
            try:
                provider = create_s3_provider(
                    access_key_id=s3_config['access_key_id'],
                    secret_access_key=s3_config['secret_access_key'],
                    bucket_name=s3_config['bucket_name'],
                    region=s3_config.get('region', 'us-east-1')
                )
                
                cloud_storage_manager.add_provider(StorageProviderType.S3, provider)
                
                if await cloud_storage_manager.authenticate_provider(StorageProviderType.S3):
                    self.cloud_providers_configured.append('s3')
                    logger.info("S3 provider configured")
                
            except Exception as e:
                logger.error(f"Error configuring S3: {e}")
        
        # Set default provider
        if self.cloud_providers_configured:
            default_provider = config.get('default_provider')
            if default_provider:
                provider_type = StorageProviderType(default_provider)
                cloud_storage_manager.set_default_provider(provider_type)
        
        logger.info(f"Cloud storage initialized with {len(self.cloud_providers_configured)} providers")
    
    async def _initialize_plugins(self, config: Dict[str, Any]):
        """Initialize plugin system"""
        logger.info("Initializing plugin system...")
        
        # Load plugins from directory
        plugin_directory = config.get('directory', 'plugins')
        loaded_count = plugin_manager.load_plugins_from_directory(plugin_directory)
        
        # Register default plugins
        if config.get('load_defaults', True):
            # Default entity extraction plugin
            default_plugin = DefaultEntityExtractionPlugin()
            plugin_manager.register_plugin('default_entity_extraction', default_plugin)
            await plugin_manager.initialize_plugin('default_entity_extraction')
            
            # Medical entity extraction plugin
            if config.get('enable_medical', False):
                medical_plugin = MedicalEntityExtractionPlugin()
                plugin_manager.register_plugin('medical_entity_extraction', medical_plugin)
                await plugin_manager.initialize_plugin('medical_entity_extraction')
        
        # Load plugin configurations
        for plugin_id in plugin_manager.plugins.keys():
            plugin_manager.load_plugin_config(plugin_id)
        
        self.plugins_loaded = len(plugin_manager.plugins)
        logger.info(f"Plugin system initialized with {self.plugins_loaded} plugins")
    
    async def _initialize_sso(self, config: Dict[str, Any]):
        """Initialize SSO system"""
        logger.info("Initializing SSO system...")
        
        if config.get('enabled', False):
            secret_key = config.get('secret_key')
            if not secret_key:
                logger.error("SSO secret key not provided")
                return
            
            # Initialize SSO manager
            sso_manager = initialize_sso_manager(secret_key)
            
            # Configure OAuth providers
            oauth_providers = config.get('oauth_providers', {})
            for provider_id, provider_config in oauth_providers.items():
                if provider_config.get('enabled', False):
                    # This would be implemented with actual OAuth providers
                    logger.info(f"OAuth provider {provider_id} would be configured here")
            
            # Configure SAML providers
            saml_providers = config.get('saml_providers', {})
            for provider_id, provider_config in saml_providers.items():
                if provider_config.get('enabled', False):
                    # This would be implemented with actual SAML providers
                    logger.info(f"SAML provider {provider_id} would be configured here")
            
            self.sso_enabled = True
            logger.info("SSO system initialized")
    
    async def trigger_webhook_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        team_id: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> Optional[str]:
        """Trigger a webhook event"""
        if not self.webhook_system_running:
            return None
        
        try:
            event_id = await webhook_manager.trigger_event(
                event_type=event_type,
                data=data,
                user_id=user_id,
                team_id=team_id,
                resource_id=resource_id
            )
            return event_id
        except Exception as e:
            logger.error(f"Error triggering webhook event: {e}")
            return None
    
    async def backup_to_cloud(
        self,
        file_path: str,
        remote_path: str,
        provider: Optional[str] = None
    ) -> bool:
        """Backup a file to cloud storage"""
        if not self.cloud_providers_configured:
            logger.warning("No cloud storage providers configured")
            return False
        
        try:
            provider_type = StorageProviderType(provider) if provider else None
            result = await cloud_storage_manager.upload_file(
                file_path=file_path,
                remote_path=remote_path,
                provider_type=provider_type
            )
            
            if result:
                logger.info(f"Successfully backed up {file_path} to cloud storage")
                return True
            else:
                logger.error(f"Failed to backup {file_path} to cloud storage")
                return False
                
        except Exception as e:
            logger.error(f"Error backing up to cloud: {e}")
            return False
    
    async def extract_entities_with_plugins(self, text: str) -> Dict[str, Any]:
        """Extract entities using loaded plugins"""
        if not self.plugins_loaded:
            return {}
        
        all_entities = []
        
        # Get entity extraction plugins
        entity_plugins = plugin_manager.get_plugins_by_type(PluginType.ENTITY_EXTRACTION)
        
        for plugin_id, plugin in entity_plugins:
            try:
                entities = await plugin_manager.execute_plugin(plugin_id, text)
                
                # Convert to dict format
                plugin_entities = []
                for entity in entities:
                    plugin_entities.append({
                        'text': entity.text,
                        'type': entity.entity_type,
                        'start': entity.start_pos,
                        'end': entity.end_pos,
                        'confidence': entity.confidence,
                        'source': plugin_id
                    })
                
                all_entities.extend(plugin_entities)
                
            except Exception as e:
                logger.error(f"Error executing plugin {plugin_id}: {e}")
        
        # Group entities by type
        grouped_entities = {}
        for entity in all_entities:
            entity_type = entity['type']
            if entity_type not in grouped_entities:
                grouped_entities[entity_type] = []
            grouped_entities[entity_type].append(entity)
        
        return grouped_entities
    
    async def shutdown(self):
        """Shutdown all integration systems"""
        logger.info("Shutting down integration systems...")
        
        # Stop webhook system
        if self.webhook_system_running:
            await webhook_manager.stop_workers()
            self.webhook_system_running = False
        
        # Cleanup plugins
        for plugin_id in list(plugin_manager.plugins.keys()):
            plugin_manager.unregister_plugin(plugin_id)
        
        self.initialized = False
        logger.info("Integration systems shut down")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all integration systems"""
        return {
            'initialized': self.initialized,
            'webhook_system': {
                'running': self.webhook_system_running,
                'stats': webhook_manager.get_stats() if self.webhook_system_running else {}
            },
            'cloud_storage': {
                'providers_configured': self.cloud_providers_configured,
                'stats': cloud_storage_manager.get_stats()
            },
            'plugins': {
                'loaded': self.plugins_loaded,
                'stats': plugin_manager.get_stats()
            },
            'sso': {
                'enabled': self.sso_enabled
            }
        }


# Global integration manager instance
integration_manager = IntegrationManager()


# Helper functions for easy integration
async def trigger_transcription_completed_webhook(
    transcript_id: str,
    file_name: str,
    duration: float,
    word_count: int,
    confidence_score: float,
    user_id: Optional[str] = None
):
    """Helper to trigger transcription completed webhook"""
    await integration_manager.trigger_webhook_event(
        event_type=WebhookEventType.TRANSCRIPTION_COMPLETED,
        data={
            'transcript_id': transcript_id,
            'file_name': file_name,
            'duration': duration,
            'word_count': word_count,
            'confidence_score': confidence_score,
            'processing_time': 0,  # Would be calculated
            'language': 'en',
            'model_used': 'whisper-1'
        },
        user_id=user_id,
        resource_id=transcript_id
    )


async def backup_transcript_to_cloud(
    transcript_id: str,
    transcript_content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Helper to backup transcript to cloud storage"""
    return await cloud_storage_manager.sync_transcript_to_cloud(
        transcript_id=transcript_id,
        transcript_content=transcript_content,
        metadata=metadata
    )


async def extract_custom_entities(text: str) -> Dict[str, Any]:
    """Helper to extract entities using custom plugins"""
    return await integration_manager.extract_entities_with_plugins(text)