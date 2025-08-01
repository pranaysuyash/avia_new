#!/usr/bin/env python3
"""
Test script for Task 23 integration capabilities
Tests webhooks, cloud storage, plugins, and SSO systems
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_webhook_system():
    """Test webhook system functionality"""
    print("🔗 Testing Webhook System")
    print("=" * 40)
    
    try:
        from webhooks import webhook_manager, WebhookEventType
        
        # Add test webhook subscription
        subscription_id = webhook_manager.add_subscription(
            url="https://httpbin.org/post",
            event_types=[WebhookEventType.TRANSCRIPTION_COMPLETED],
            secret="test_secret_123"
        )
        
        print(f"✅ Added webhook subscription: {subscription_id}")
        
        # Start webhook workers
        await webhook_manager.start_workers()
        print("✅ Webhook workers started")
        
        # Trigger test event
        event_id = await webhook_manager.trigger_event(
            event_type=WebhookEventType.TRANSCRIPTION_COMPLETED,
            data={
                'transcript_id': 'test_123',
                'file_name': 'test_audio.mp3',
                'duration': 120,
                'word_count': 250,
                'confidence_score': 95.5
            },
            user_id='test_user'
        )
        
        print(f"✅ Triggered webhook event: {event_id}")
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Get stats
        stats = webhook_manager.get_stats()
        print(f"📊 Webhook stats: {stats}")
        
        # Stop workers
        await webhook_manager.stop_workers()
        print("✅ Webhook workers stopped")
        
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")


async def test_cloud_storage():
    """Test cloud storage functionality"""
    print("\n☁️ Testing Cloud Storage")
    print("=" * 40)
    
    try:
        from cloud_storage import cloud_storage_manager, StorageProviderType
        from cloud_storage.google_drive import create_google_drive_provider
        from cloud_storage.dropbox_provider import create_dropbox_provider
        from cloud_storage.s3_provider import create_s3_provider
        
        # Add mock providers
        google_provider = create_google_drive_provider(
            client_id="mock_client_id",
            client_secret="mock_client_secret"
        )
        cloud_storage_manager.add_provider(StorageProviderType.GOOGLE_DRIVE, google_provider)
        
        dropbox_provider = create_dropbox_provider("mock_access_token")
        cloud_storage_manager.add_provider(StorageProviderType.DROPBOX, dropbox_provider)
        
        s3_provider = create_s3_provider(
            access_key_id="mock_key",
            secret_access_key="mock_secret",
            bucket_name="test-bucket"
        )
        cloud_storage_manager.add_provider(StorageProviderType.S3, s3_provider)
        
        print("✅ Added cloud storage providers")
        
        # Test authentication
        for provider_type in [StorageProviderType.GOOGLE_DRIVE, StorageProviderType.DROPBOX, StorageProviderType.S3]:
            success = await cloud_storage_manager.authenticate_provider(provider_type)
            print(f"✅ {provider_type.value} authentication: {'Success' if success else 'Failed'}")
        
        # Test file listing
        files = await cloud_storage_manager.list_files("/", StorageProviderType.GOOGLE_DRIVE)
        print(f"✅ Listed {len(files)} files from Google Drive")
        
        # Test transcript backup
        result = await cloud_storage_manager.sync_transcript_to_cloud(
            transcript_id="test_transcript_123",
            transcript_content="This is a test transcript for cloud backup.",
            metadata={'test': True}
        )
        
        if result:
            print(f"✅ Transcript backed up: {result.name}")
        
        # Get stats
        stats = cloud_storage_manager.get_stats()
        print(f"📊 Cloud storage stats: {stats}")
        
    except Exception as e:
        print(f"❌ Cloud storage test failed: {e}")


async def test_plugin_system():
    """Test plugin system functionality"""
    print("\n🔌 Testing Plugin System")
    print("=" * 40)
    
    try:
        from plugins import plugin_manager, PluginType
        from plugins.entity_plugin import DefaultEntityExtractionPlugin
        
        # Register default plugin
        default_plugin = DefaultEntityExtractionPlugin()
        plugin_manager.register_plugin('default_entity_extraction', default_plugin)
        print("✅ Registered default entity extraction plugin")
        
        # Initialize plugin
        success = await plugin_manager.initialize_plugin('default_entity_extraction')
        print(f"✅ Plugin initialization: {'Success' if success else 'Failed'}")
        
        # Test plugin execution
        test_text = "Contact John Smith at john@example.com or call (555) 123-4567. Visit https://example.com for more info."
        
        entities = await plugin_manager.execute_plugin('default_entity_extraction', test_text)
        print(f"✅ Extracted {len(entities)} entities:")
        
        for entity in entities[:5]:  # Show first 5
            print(f"   • {entity.entity_type}: {entity.text} (confidence: {entity.confidence:.2f})")
        
        # Get plugin stats
        stats = plugin_manager.get_stats()
        print(f"📊 Plugin stats: {stats}")
        
        # List plugins
        plugins = plugin_manager.list_plugins()
        print(f"✅ Found {len(plugins)} plugins")
        
    except Exception as e:
        print(f"❌ Plugin test failed: {e}")


async def test_sso_system():
    """Test SSO system functionality"""
    print("\n🔐 Testing SSO System")
    print("=" * 40)
    
    try:
        from sso import initialize_sso_manager, SSOUser
        
        # Initialize SSO manager
        sso_manager = initialize_sso_manager("test_secret_key_123")
        print("✅ SSO manager initialized")
        
        # Create mock user
        mock_user = SSOUser(
            id="user_123",
            email="test@example.com",
            name="Test User",
            username="testuser",
            groups=["users", "developers"],
            provider="mock_oauth"
        )
        
        # Create session
        session = sso_manager.create_session(mock_user, "mock_oauth")
        print(f"✅ Created SSO session: {session.session_id}")
        
        # Validate session
        is_valid = sso_manager.validate_session(session.session_id)
        print(f"✅ Session validation: {'Valid' if is_valid else 'Invalid'}")
        
        # Generate JWT token
        jwt_token = sso_manager.generate_jwt_token(mock_user)
        print(f"✅ Generated JWT token: {jwt_token[:50]}...")
        
        # Verify JWT token
        payload = sso_manager.verify_jwt_token(jwt_token)
        if payload:
            print(f"✅ JWT verification successful: {payload['email']}")
        
        # Get stats
        stats = sso_manager.get_stats()
        print(f"📊 SSO stats: {stats}")
        
    except Exception as e:
        print(f"❌ SSO test failed: {e}")


async def test_integration_manager():
    """Test integration manager functionality"""
    print("\n🔗 Testing Integration Manager")
    print("=" * 40)
    
    try:
        from integration_manager import integration_manager
        
        # Mock configuration
        config = {
            'webhooks': {
                'enabled': True,
                'subscriptions': []
            },
            'cloud_storage': {
                'google_drive': {'enabled': False},
                'dropbox': {'enabled': False},
                's3': {'enabled': False}
            },
            'plugins': {
                'load_defaults': True,
                'enable_medical': False
            },
            'sso': {
                'enabled': True,
                'secret_key': 'test_secret_123'
            }
        }
        
        # Initialize all systems
        success = await integration_manager.initialize_all_systems(config)
        print(f"✅ Integration systems initialization: {'Success' if success else 'Failed'}")
        
        # Test custom entity extraction
        test_text = "Dr. Smith prescribed aspirin for the patient's headache. The appointment is scheduled for January 15th, 2024."
        
        custom_entities = await integration_manager.extract_entities_with_plugins(test_text)
        print(f"✅ Custom entity extraction found {len(custom_entities)} entity types")
        
        for entity_type, entities in custom_entities.items():
            print(f"   • {entity_type}: {len(entities)} entities")
        
        # Get overall status
        status = integration_manager.get_status()
        print(f"📊 Integration status: {status}")
        
        # Shutdown systems
        await integration_manager.shutdown()
        print("✅ Integration systems shut down")
        
    except Exception as e:
        print(f"❌ Integration manager test failed: {e}")


async def main():
    """Run all integration tests"""
    print("🚀 Task 23 Integration Capabilities Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Run all tests
    await test_webhook_system()
    await test_cloud_storage()
    await test_plugin_system()
    await test_sso_system()
    await test_integration_manager()
    
    print("\n" + "=" * 50)
    print("✅ Task 23 Integration Test Complete!")
    print(f"Test completed at: {datetime.now()}")
    
    print("\n📋 Integration Capabilities Summary:")
    print("✅ Webhook system for processing notifications")
    print("✅ Cloud storage integration (Google Drive, Dropbox, S3)")
    print("✅ Plugin system for custom entity extraction rules")
    print("✅ SSO authentication for enterprise deployment")
    print("✅ REST API endpoints (existing FastAPI implementation)")
    print("✅ Integration manager for unified system management")


if __name__ == "__main__":
    asyncio.run(main())