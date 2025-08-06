"""
Test Suite for Third-Party Ecosystem
Comprehensive tests for plugin architecture, webhooks, external APIs, and integrations
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sqlite3

# Import the modules to test
from third_party_ecosystem import (
    ThirdPartyEcosystem, 
    IntegrationHelpers,
    IntegrationType,
    IntegrationStatus,
    PluginMetadata,
    WebhookConfig,
    ExternalAPIConfig
)

class TestThirdPartyEcosystem:
    """Test cases for the main ThirdPartyEcosystem class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def ecosystem(self, temp_db):
        """Create a ThirdPartyEcosystem instance for testing"""
        return ThirdPartyEcosystem(db_path=temp_db)
    
    def test_database_initialization(self, ecosystem):
        """Test that the database is properly initialized"""
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        
        # Check that all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'plugins', 'webhooks', 'integrations', 
            'external_apis', 'plugin_marketplace'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"
        
        conn.close()
    
    def test_external_apis_loading(self, ecosystem):
        """Test that external APIs are properly loaded"""
        assert len(ecosystem.external_apis) > 0
        
        # Check for key APIs
        expected_apis = ['openai', 'huggingface', 'elevenlabs', 'salesforce', 'hubspot']
        for api in expected_apis:
            assert api in ecosystem.external_apis, f"API {api} not found"
        
        # Check API configuration structure
        openai_config = ecosystem.external_apis['openai']
        assert openai_config.name == "OpenAI"
        assert openai_config.base_url == "https://api.openai.com/v1"
        assert openai_config.auth_type == "bearer"
        assert len(openai_config.models) > 0
        assert len(openai_config.capabilities) > 0
    
    def test_plugin_installation(self, ecosystem):
        """Test plugin installation functionality"""
        plugin_config = {
            'name': 'Test Plugin',
            'version': '1.0.0',
            'description': 'A test plugin',
            'author': 'Test Author',
            'category': 'test'
        }
        
        plugin_id = ecosystem.install_plugin("dummy_path", plugin_config)
        
        assert plugin_id is not None
        assert len(plugin_id) == 16  # MD5 hash truncated to 16 chars
        
        # Verify plugin is in database
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[1] == plugin_config['name']  # name column
        assert result[2] == plugin_config['version']  # version column
    
    def test_plugin_activation(self, ecosystem):
        """Test plugin activation functionality"""
        # First install a plugin
        plugin_config = {
            'name': 'Test Plugin',
            'version': '1.0.0',
            'description': 'A test plugin',
            'author': 'Test Author',
            'category': 'test'
        }
        
        plugin_id = ecosystem.install_plugin("dummy_path", plugin_config)
        
        # Activate the plugin
        result = ecosystem.activate_plugin(plugin_id)
        assert result is True
        
        # Verify plugin is active in database
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM plugins WHERE id = ?", (plugin_id,))
        status = cursor.fetchone()[0]
        conn.close()
        
        assert status == 'active'
        assert plugin_id in ecosystem.plugins
    
    def test_plugin_execution(self, ecosystem):
        """Test plugin execution functionality"""
        # Install and activate a plugin
        plugin_config = {
            'name': 'Test Plugin',
            'version': '1.0.0',
            'description': 'A test plugin',
            'author': 'Test Author',
            'category': 'test'
        }
        
        plugin_id = ecosystem.install_plugin("dummy_path", plugin_config)
        ecosystem.activate_plugin(plugin_id)
        
        # Execute plugin method
        result = ecosystem.execute_plugin(plugin_id, "test_method", "arg1", "arg2", param1="value1")
        
        assert result is not None
        assert "Plugin" in result
        assert "test_method" in result
        
        # Verify usage count is updated
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT usage_count FROM plugins WHERE id = ?", (plugin_id,))
        usage_count = cursor.fetchone()[0]
        conn.close()
        
        assert usage_count == 1
    
    def test_webhook_registration(self, ecosystem):
        """Test webhook registration functionality"""
        webhook_id = ecosystem.register_webhook(
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["test.event"],
            secret="test_secret"
        )
        
        assert webhook_id is not None
        assert len(webhook_id) == 16
        
        # Verify webhook is in database
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[1] == "Test Webhook"  # name column
        assert result[2] == "https://example.com/webhook"  # url column
        assert webhook_id in ecosystem.webhooks
    
    @pytest.mark.asyncio
    async def test_webhook_triggering(self, ecosystem):
        """Test webhook triggering functionality"""
        # Register a webhook
        webhook_id = ecosystem.register_webhook(
            name="Test Webhook",
            url="https://httpbin.org/post",  # Use httpbin for testing
            events=["test.event"],
            secret="test_secret"
        )
        
        # Mock the HTTP request to avoid actual network calls
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Trigger webhooks
            await ecosystem.trigger_webhooks("test.event", {"test": "data"})
            
            # Verify the request was made
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_external_api_call(self, ecosystem):
        """Test external API call functionality"""
        # Mock the HTTP request
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"result": "success"}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Make API call
            result = await ecosystem.call_external_api(
                "openai", 
                "/completions", 
                method="POST",
                data={"prompt": "test"}
            )
            
            assert result == {"result": "success"}
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_salesforce_sync(self, ecosystem):
        """Test Salesforce CRM sync functionality"""
        # Mock the HTTP request
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"id": "SF_LEAD_123", "success": True}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Test lead creation
            lead_data = {
                'FirstName': 'John',
                'LastName': 'Doe',
                'Email': 'john.doe@example.com',
                'Company': 'Test Corp'
            }
            
            result = await ecosystem.sync_with_salesforce('create_lead', lead_data)
            
            assert result["success"] is True
            assert "id" in result
    
    @pytest.mark.asyncio
    async def test_hubspot_sync(self, ecosystem):
        """Test HubSpot CRM sync functionality"""
        # Mock the HTTP request
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"id": "HS_CONTACT_456", "properties": {}}
            mock_post.return_value.__aenter__.return_value = mock_response
            
            # Test contact creation
            contact_data = {
                'firstname': 'Jane',
                'lastname': 'Smith',
                'email': 'jane.smith@example.com'
            }
            
            result = await ecosystem.sync_with_hubspot('create_contact', contact_data)
            
            assert "id" in result
            assert result["id"] == "HS_CONTACT_456"
    
    def test_zapier_trigger_creation(self, ecosystem):
        """Test Zapier trigger configuration creation"""
        trigger_config = ecosystem.create_zapier_trigger(
            "test_trigger",
            "A test trigger",
            {"sample": "data"}
        )
        
        assert trigger_config["key"] == "test_trigger"
        assert trigger_config["noun"] == "Test Trigger"
        assert "operation" in trigger_config
        assert trigger_config["operation"]["sample"] == {"sample": "data"}
    
    def test_zapier_action_creation(self, ecosystem):
        """Test Zapier action configuration creation"""
        input_fields = [
            {"key": "field1", "label": "Field 1", "type": "string", "required": True}
        ]
        
        action_config = ecosystem.create_zapier_action(
            "test_action",
            "A test action",
            input_fields
        )
        
        assert action_config["key"] == "test_action"
        assert action_config["noun"] == "Test Action"
        assert "operation" in action_config
        assert action_config["operation"]["inputFields"] == input_fields
    
    def test_browser_extension_manifest(self, ecosystem):
        """Test browser extension manifest generation"""
        manifest = ecosystem.generate_browser_extension_manifest("Test Extension")
        
        assert manifest["manifest_version"] == 3
        assert manifest["name"] == "Test Extension"
        assert "permissions" in manifest
        assert "host_permissions" in manifest
        assert "background" in manifest
        assert "content_scripts" in manifest
        assert "action" in manifest
    
    def test_marketplace_search(self, ecosystem):
        """Test marketplace search functionality"""
        # Add some test data to marketplace
        conn = sqlite3.connect(ecosystem.db_path)
        cursor = conn.cursor()
        
        test_plugins = [
            ("plugin1", "AI Analyzer", "Analyze content with AI", "ai", "AI Corp", "1.0.0"),
            ("plugin2", "PDF Processor", "Process PDF files", "document", "Doc Inc", "2.0.0"),
            ("plugin3", "Video Transcriber", "Transcribe videos", "media", "Media Co", "1.5.0")
        ]
        
        for plugin_data in test_plugins:
            cursor.execute('''
                INSERT INTO plugin_marketplace 
                (id, name, description, category, author, version)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', plugin_data)
        
        conn.commit()
        conn.close()
        
        # Test search
        results = ecosystem.search_marketplace("AI")
        assert len(results) >= 1
        
        # Test category filter
        results = ecosystem.search_marketplace("", category="ai")
        assert len(results) >= 1
    
    def test_integration_analytics(self, ecosystem):
        """Test integration analytics functionality"""
        # Install some test plugins and webhooks
        plugin_id = ecosystem.install_plugin("dummy", {"name": "Test Plugin"})
        ecosystem.activate_plugin(plugin_id)
        
        webhook_id = ecosystem.register_webhook(
            "Test Webhook", 
            "https://example.com", 
            ["test.event"]
        )
        
        # Get analytics
        analytics = ecosystem.get_integration_analytics()
        
        assert "plugins" in analytics
        assert "webhooks" in analytics
        assert "apis" in analytics
        assert analytics["total_plugins"] >= 1
        assert analytics["total_webhooks"] >= 1
        assert analytics["total_apis"] >= 1

class TestIntegrationHelpers:
    """Test cases for integration helper functions"""
    
    def test_slack_notification_creation(self):
        """Test Slack notification payload creation"""
        payload = IntegrationHelpers.create_slack_notification(
            "https://hooks.slack.com/test",
            "Test message",
            "#general"
        )
        
        assert payload["text"] == "Test message"
        assert payload["channel"] == "#general"
        assert payload["username"] == "AI Media Processor"
        assert payload["icon_emoji"] == ":robot_face:"
    
    def test_discord_embed_creation(self):
        """Test Discord embed payload creation"""
        embed = IntegrationHelpers.create_discord_embed(
            "Test Title",
            "Test Description",
            0xff0000
        )
        
        assert "embeds" in embed
        assert len(embed["embeds"]) == 1
        
        embed_data = embed["embeds"][0]
        assert embed_data["title"] == "Test Title"
        assert embed_data["description"] == "Test Description"
        assert embed_data["color"] == 0xff0000
        assert "timestamp" in embed_data
    
    def test_crm_contact_formatting(self):
        """Test CRM contact data formatting"""
        contact = IntegrationHelpers.format_crm_contact(
            "John Doe",
            "john.doe@example.com",
            "Test Corp",
            "+1-555-123-4567",
            "AI Media Processor"
        )
        
        assert contact["firstname"] == "John"
        assert contact["lastname"] == "Doe"
        assert contact["email"] == "john.doe@example.com"
        assert contact["company"] == "Test Corp"
        assert contact["phone"] == "+1-555-123-4567"
        assert contact["source"] == "AI Media Processor"
        assert contact["hs_lead_status"] == "NEW"
        assert contact["lifecyclestage"] == "lead"

class TestDataModels:
    """Test cases for data models and enums"""
    
    def test_integration_type_enum(self):
        """Test IntegrationType enum"""
        assert IntegrationType.PLUGIN.value == "plugin"
        assert IntegrationType.WEBHOOK.value == "webhook"
        assert IntegrationType.ZAPIER.value == "zapier"
        assert IntegrationType.CRM.value == "crm"
    
    def test_integration_status_enum(self):
        """Test IntegrationStatus enum"""
        assert IntegrationStatus.ACTIVE.value == "active"
        assert IntegrationStatus.INACTIVE.value == "inactive"
        assert IntegrationStatus.PENDING.value == "pending"
        assert IntegrationStatus.ERROR.value == "error"
    
    def test_plugin_metadata_dataclass(self):
        """Test PluginMetadata dataclass"""
        metadata = PluginMetadata(
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            category="test",
            permissions=["read", "write"],
            dependencies=["numpy", "pandas"],
            entry_point="main.py",
            config_schema={"type": "object"},
            supported_formats=["pdf", "docx"],
            min_api_version="1.0.0"
        )
        
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0.0"
        assert len(metadata.permissions) == 2
        assert len(metadata.dependencies) == 2
        assert len(metadata.supported_formats) == 2
    
    def test_webhook_config_dataclass(self):
        """Test WebhookConfig dataclass"""
        config = WebhookConfig(
            url="https://example.com/webhook",
            events=["test.event"],
            secret="secret_key",
            headers={"Authorization": "Bearer token"},
            retry_count=5,
            timeout=60,
            active=True
        )
        
        assert config.url == "https://example.com/webhook"
        assert len(config.events) == 1
        assert config.secret == "secret_key"
        assert config.retry_count == 5
        assert config.timeout == 60
        assert config.active is True
    
    def test_external_api_config_dataclass(self):
        """Test ExternalAPIConfig dataclass"""
        config = ExternalAPIConfig(
            name="Test API",
            base_url="https://api.example.com",
            api_key="test_key",
            auth_type="bearer",
            rate_limit=1000,
            endpoints={"users": "/users", "posts": "/posts"},
            models=["model1", "model2"],
            capabilities=["text_generation", "analysis"]
        )
        
        assert config.name == "Test API"
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "test_key"
        assert config.auth_type == "bearer"
        assert config.rate_limit == 1000
        assert len(config.endpoints) == 2
        assert len(config.models) == 2
        assert len(config.capabilities) == 2

class TestErrorHandling:
    """Test cases for error handling and edge cases"""
    
    @pytest.fixture
    def ecosystem(self):
        """Create ecosystem with temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        ecosystem = ThirdPartyEcosystem(db_path=db_path)
        yield ecosystem
        
        os.unlink(db_path)
    
    def test_plugin_execution_nonexistent_plugin(self, ecosystem):
        """Test plugin execution with non-existent plugin"""
        with pytest.raises(ValueError, match="Plugin .* not found"):
            ecosystem.execute_plugin("nonexistent_plugin", "test_method")
    
    def test_plugin_activation_nonexistent_plugin(self, ecosystem):
        """Test plugin activation with non-existent plugin"""
        result = ecosystem.activate_plugin("nonexistent_plugin")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_external_api_call_nonexistent_api(self, ecosystem):
        """Test external API call with non-existent API"""
        with pytest.raises(ValueError, match="API configuration .* not found"):
            await ecosystem.call_external_api("nonexistent_api", "/test")
    
    @pytest.mark.asyncio
    async def test_webhook_triggering_network_error(self, ecosystem):
        """Test webhook triggering with network error"""
        # Register a webhook
        webhook_id = ecosystem.register_webhook(
            "Test Webhook",
            "https://invalid-url-that-does-not-exist.com/webhook",
            ["test.event"]
        )
        
        # Mock network error
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = Exception("Network error")
            
            # This should not raise an exception, but handle the error gracefully
            await ecosystem.trigger_webhooks("test.event", {"test": "data"})
    
    def test_marketplace_search_empty_query(self, ecosystem):
        """Test marketplace search with empty query"""
        results = ecosystem.search_marketplace("")
        assert isinstance(results, list)
    
    def test_integration_analytics_empty_database(self, ecosystem):
        """Test integration analytics with empty database"""
        analytics = ecosystem.get_integration_analytics()
        
        assert analytics["total_plugins"] == 0
        assert analytics["total_webhooks"] == 0
        assert analytics["total_apis"] > 0  # External APIs are loaded by default

class TestPerformance:
    """Test cases for performance and scalability"""
    
    @pytest.fixture
    def ecosystem(self):
        """Create ecosystem with temporary database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        ecosystem = ThirdPartyEcosystem(db_path=db_path)
        yield ecosystem
        
        os.unlink(db_path)
    
    def test_bulk_plugin_installation(self, ecosystem):
        """Test installing multiple plugins"""
        plugin_ids = []
        
        for i in range(10):
            plugin_config = {
                'name': f'Test Plugin {i}',
                'version': '1.0.0',
                'description': f'Test plugin number {i}',
                'author': 'Test Author',
                'category': 'test'
            }
            
            plugin_id = ecosystem.install_plugin("dummy_path", plugin_config)
            plugin_ids.append(plugin_id)
        
        assert len(plugin_ids) == 10
        assert len(set(plugin_ids)) == 10  # All IDs should be unique
    
    def test_bulk_webhook_registration(self, ecosystem):
        """Test registering multiple webhooks"""
        webhook_ids = []
        
        for i in range(10):
            webhook_id = ecosystem.register_webhook(
                name=f"Test Webhook {i}",
                url=f"https://example.com/webhook/{i}",
                events=[f"test.event.{i}"]
            )
            webhook_ids.append(webhook_id)
        
        assert len(webhook_ids) == 10
        assert len(set(webhook_ids)) == 10  # All IDs should be unique
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, ecosystem):
        """Test concurrent external API calls"""
        # Mock the HTTP requests
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"result": "success"}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Make concurrent API calls
            tasks = []
            for i in range(5):
                task = ecosystem.call_external_api(
                    "openai", 
                    "/completions", 
                    method="POST",
                    data={"prompt": f"test {i}"}
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            for result in results:
                assert result == {"result": "success"}

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])