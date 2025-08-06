"""
Test suite for API Platform and Developer Portal
Tests API key management, webhooks, SDK generation, and analytics.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
import uuid
import hashlib
import hmac
import json
from unittest.mock import Mock, patch, MagicMock

from api_platform_system import (
    APIManager, DeveloperPortal, SDKGenerator,
    WebhookManager, APIAnalytics
)

class TestAPIManager:
    """Test API Manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_manager = APIManager()
    
    def test_generate_api_key(self):
        """Test API key generation"""
        # Generate key
        api_key = self.api_manager.generate_api_key(
            name="Test Key",
            user_id="test_user_123"
        )
        
        # Verify key format
        assert api_key.startswith("sk_")
        assert len(api_key) > 20
        
        # Verify key is stored
        assert hasattr(self.api_manager, 'api_keys')
        assert api_key in self.api_manager.api_keys
        
        # Verify metadata
        metadata = self.api_manager.api_keys[api_key]
        assert metadata['name'] == "Test Key"
        assert metadata['user_id'] == "test_user_123"
    
    def test_validate_api_key(self):
        """Test API key validation"""
        # Generate key
        api_key = self.api_manager.generate_api_key(
            name="Test Key",
            user_id="test_user_123"
        )
        
        # Test valid key
        is_valid, user_id = self.api_manager.validate_api_key(api_key)
        assert is_valid is True
        assert user_id == "test_user_123"
        
        # Test invalid key
        is_valid, user_id = self.api_manager.validate_api_key("invalid_key")
        assert is_valid is False
        assert user_id is None
    
    def test_revoke_api_key(self):
        """Test API key revocation"""
        # Generate key
        api_key = self.api_manager.generate_api_key(
            name="Test Key",
            user_id="test_user_123"
        )
        
        # Revoke key
        result = self.api_manager.revoke_api_key(api_key)
        assert result is True
        
        # Verify key is invalid
        is_valid, _ = self.api_manager.validate_api_key(api_key)
        assert is_valid is False
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        api_key = self.api_manager.generate_api_key(
            name="Test Key",
            user_id="test_user_123"
        )
        
        # Set custom rate limit
        self.api_manager.api_keys[api_key]['rate_limit'] = 10
        
        # Test within limit
        for i in range(10):
            allowed = self.api_manager.check_rate_limit(api_key)
            assert allowed is True
        
        # Test exceeding limit
        allowed = self.api_manager.check_rate_limit(api_key)
        assert allowed is False

class TestWebhookManager:
    """Test Webhook Manager functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.webhook_manager = WebhookManager()
    
    def test_register_webhook(self):
        """Test webhook registration"""
        webhook_id = str(uuid.uuid4())
        url = "https://example.com/webhook"
        events = ["transcription.completed", "analysis.completed"]
        secret = "test_secret"
        
        # Register webhook
        result = self.webhook_manager.register_webhook(
            webhook_id=webhook_id,
            url=url,
            events=events,
            secret=secret
        )
        
        assert result is True
        assert webhook_id in self.webhook_manager.webhooks
        
        # Verify webhook data
        webhook = self.webhook_manager.webhooks[webhook_id]
        assert webhook['url'] == url
        assert webhook['events'] == events
        assert webhook['secret'] == secret
    
    @pytest.mark.asyncio
    async def test_send_webhook(self):
        """Test webhook sending"""
        webhook_id = str(uuid.uuid4())
        url = "https://example.com/webhook"
        events = ["test.event"]
        secret = "test_secret"
        
        # Register webhook
        self.webhook_manager.register_webhook(
            webhook_id=webhook_id,
            url=url,
            events=events,
            secret=secret
        )
        
        # Mock HTTP client
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.json = asyncio.coroutine(lambda: {"status": "ok"})
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Send webhook
            result = await self.webhook_manager.send_webhook(
                webhook_id=webhook_id,
                event_type="test.event",
                data={"test": "data"}
            )
            
            assert result['status_code'] == 200
            assert 'response_time' in result
    
    def test_webhook_signature(self):
        """Test webhook signature generation"""
        webhook_id = str(uuid.uuid4())
        secret = "test_secret"
        
        # Register webhook
        self.webhook_manager.register_webhook(
            webhook_id=webhook_id,
            url="https://example.com/webhook",
            events=["test.event"],
            secret=secret
        )
        
        # Generate signature
        payload = {"test": "data"}
        signature = self.webhook_manager._generate_signature(
            webhook_id, payload
        )
        
        # Verify signature format
        assert signature.startswith("sha256=")
        
        # Verify signature correctness
        expected_sig = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == f"sha256={expected_sig}"

class TestSDKGenerator:
    """Test SDK Generator functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sdk_generator = SDKGenerator()
    
    @patch('os.makedirs')
    @patch('builtins.open', create=True)
    def test_generate_python_sdk(self, mock_open, mock_makedirs):
        """Test Python SDK generation"""
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Generate SDK
        sdk_path = self.sdk_generator.generate_sdk(
            language="python",
            config={
                "package_name": "test-sdk",
                "version": "1.0.0",
                "include_examples": True,
                "include_tests": True,
                "async_support": True
            }
        )
        
        # Verify SDK was generated
        assert sdk_path is not None
        assert "test-sdk" in sdk_path
        
        # Verify files were created
        assert mock_open.call_count > 0
        assert mock_makedirs.called
    
    def test_supported_languages(self):
        """Test supported language check"""
        supported = ["python", "javascript", "typescript", "go", "java"]
        
        for lang in supported:
            assert self.sdk_generator.is_language_supported(lang) is True
        
        assert self.sdk_generator.is_language_supported("cobol") is False
    
    def test_generate_client_code(self):
        """Test client code generation"""
        # Generate Python client
        client_code = self.sdk_generator._generate_python_client({
            "package_name": "test-sdk",
            "async_support": True
        })
        
        # Verify code contains expected elements
        assert "class Client" in client_code
        assert "def __init__" in client_code
        assert "api_key" in client_code
        
        # Verify async support
        assert "async def" in client_code
        assert "AsyncClient" in client_code

class TestDeveloperPortal:
    """Test Developer Portal functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.portal = DeveloperPortal()
    
    def test_get_documentation(self):
        """Test documentation retrieval"""
        docs = self.portal.get_documentation("getting-started")
        
        assert docs is not None
        assert "title" in docs
        assert "content" in docs
        assert docs["title"] == "Getting Started"
    
    def test_generate_openapi_spec(self):
        """Test OpenAPI spec generation"""
        spec = self.portal.generate_openapi_spec()
        
        # Verify OpenAPI structure
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        
        # Verify version
        assert spec["openapi"] == "3.0.0"
        
        # Verify endpoints
        assert "/transcribe" in spec["paths"]
        assert "/analyze" in spec["paths"]
    
    def test_get_code_example(self):
        """Test code example retrieval"""
        # Get Python example
        example = self.portal.get_code_example("python", "authentication")
        
        assert example is not None
        assert "import" in example
        assert "api_key" in example
        
        # Test invalid language
        example = self.portal.get_code_example("cobol", "authentication")
        assert example is None
    
    def test_get_postman_collection(self):
        """Test Postman collection generation"""
        collection = self.portal.get_postman_collection()
        
        # Verify collection structure
        assert "info" in collection
        assert "item" in collection
        assert collection["info"]["schema"].startswith("https://schema.getpostman.com")

class TestAPIAnalytics:
    """Test API Analytics functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analytics = APIAnalytics()
    
    def test_log_api_call(self):
        """Test API call logging"""
        # Log a call
        self.analytics.log_api_call(
            api_key="test_key",
            endpoint="/api/v1/transcribe",
            method="POST",
            status_code=200,
            response_time=245.5,
            user_id="test_user"
        )
        
        # Verify call was logged
        assert len(self.analytics.logs) == 1
        
        log = self.analytics.logs[0]
        assert log['api_key'] == "test_key"
        assert log['endpoint'] == "/api/v1/transcribe"
        assert log['status_code'] == 200
    
    def test_get_analytics(self):
        """Test analytics calculation"""
        # Log multiple calls
        for i in range(10):
            self.analytics.log_api_call(
                api_key="test_key",
                endpoint="/api/v1/transcribe",
                method="POST",
                status_code=200 if i < 8 else 500,
                response_time=100 + i * 10,
                user_id="test_user"
            )
        
        # Get analytics
        now = datetime.utcnow()
        analytics = self.analytics.get_analytics(
            user_id="test_user",
            start_time=now - timedelta(hours=1),
            end_time=now
        )
        
        # Verify analytics
        assert analytics['total_requests'] == 10
        assert analytics['success_rate'] == 80.0
        assert analytics['error_rate'] == 20.0
        assert analytics['avg_response_time'] == 145.0
    
    def test_get_top_endpoints(self):
        """Test top endpoints calculation"""
        # Log calls to different endpoints
        endpoints = [
            "/api/v1/transcribe",
            "/api/v1/analyze",
            "/api/v1/transcribe",
            "/api/v1/transcribe",
            "/api/v1/analyze"
        ]
        
        for endpoint in endpoints:
            self.analytics.log_api_call(
                api_key="test_key",
                endpoint=endpoint,
                method="POST",
                status_code=200,
                response_time=100,
                user_id="test_user"
            )
        
        # Get top endpoints
        top_endpoints = self.analytics.get_top_endpoints(
            user_id="test_user",
            limit=2
        )
        
        # Verify results
        assert len(top_endpoints) == 2
        assert top_endpoints[0]['endpoint'] == "/api/v1/transcribe"
        assert top_endpoints[0]['count'] == 3
        assert top_endpoints[1]['endpoint'] == "/api/v1/analyze"
        assert top_endpoints[1]['count'] == 2

class TestIntegration:
    """Test integration between components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_manager = APIManager()
        self.webhook_manager = WebhookManager()
        self.analytics = APIAnalytics()
    
    @pytest.mark.asyncio
    async def test_full_api_flow(self):
        """Test complete API flow"""
        # 1. Generate API key
        api_key = self.api_manager.generate_api_key(
            name="Integration Test",
            user_id="test_user"
        )
        
        # 2. Validate API key
        is_valid, user_id = self.api_manager.validate_api_key(api_key)
        assert is_valid is True
        
        # 3. Check rate limit
        allowed = self.api_manager.check_rate_limit(api_key)
        assert allowed is True
        
        # 4. Log API call
        self.analytics.log_api_call(
            api_key=api_key,
            endpoint="/api/v1/transcribe",
            method="POST",
            status_code=200,
            response_time=150.0,
            user_id=user_id
        )
        
        # 5. Register webhook
        webhook_id = str(uuid.uuid4())
        self.webhook_manager.register_webhook(
            webhook_id=webhook_id,
            url="https://example.com/webhook",
            events=["transcription.completed"],
            secret="test_secret"
        )
        
        # 6. Send webhook (mocked)
        with patch('aiohttp.ClientSession'):
            result = await self.webhook_manager.send_webhook(
                webhook_id=webhook_id,
                event_type="transcription.completed",
                data={"transcription_id": "test_123"}
            )
        
        # 7. Get analytics
        analytics = self.analytics.get_analytics(
            user_id=user_id,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow()
        )
        
        assert analytics['total_requests'] == 1
        assert analytics['success_rate'] == 100.0

def test_api_platform_documentation():
    """Test that API platform is properly documented"""
    portal = DeveloperPortal()
    
    # Check all documentation sections exist
    sections = [
        "getting-started",
        "authentication", 
        "api-reference",
        "webhooks",
        "rate-limiting",
        "error-handling"
    ]
    
    for section in sections:
        docs = portal.get_documentation(section)
        assert docs is not None
        assert len(docs.get("content", "")) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])