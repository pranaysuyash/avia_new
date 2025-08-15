"""
Comprehensive tests for Production Authentication & Authorization System

Tests all major functionality including:
- User registration and authentication
- OAuth 2.0 flows
- JWT token management
- API key management
- Rate limiting
- Role-based access control (RBAC)
- Session management
- Security features

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
import asyncio
import secrets
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from production_auth_system import (
    ProductionAuthSystem,
    User,
    Session,
    APIKey,
    Permission,
    RolePermission,
    UserRole,
    AuthProvider,
    SessionStatus,
    RateLimitTier,
    PasswordManager,
    TokenManager,
    OAuthManager,
    RateLimiter,
    AuthDatabase
)


class TestProductionAuthSystem(unittest.TestCase):
    """Test suite for Production Authentication System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_auth.db")
        self.auth_system = ProductionAuthSystem(db_path=self.db_path)
        
        # Test data
        self.test_email = "test@example.com"
        self.test_password = "TestPassword123!"
        self.test_user_data = {
            'email': self.test_email,
            'password': self.test_password,
            'full_name': "Test User",
            'username': "testuser"
        }
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.auth_system, ProductionAuthSystem)
        self.assertIsInstance(self.auth_system.db, AuthDatabase)
        self.assertIsNotNone(self.auth_system.secret_key)
        self.assertIsNotNone(self.auth_system.password_manager)
        self.assertIsNotNone(self.auth_system.token_manager)
        self.assertIsNotNone(self.auth_system.oauth_manager)
        self.assertIsNotNone(self.auth_system.rate_limiter)
    
    def test_user_dataclass(self):
        """Test User dataclass"""
        user = User(
            user_id="test_123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.USER,
            provider=AuthProvider.LOCAL
        )
        
        self.assertEqual(user.user_id, "test_123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, UserRole.USER)
        self.assertEqual(user.provider, AuthProvider.LOCAL)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_verified)
        self.assertIsInstance(user.created_at, datetime)
    
    def test_session_dataclass(self):
        """Test Session dataclass"""
        now = datetime.now()
        session = Session(
            session_id="session_123",
            user_id="user_123",
            access_token="access_token",
            refresh_token="refresh_token",
            expires_at=now + timedelta(hours=1),
            refresh_expires_at=now + timedelta(days=30)
        )
        
        self.assertEqual(session.session_id, "session_123")
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        self.assertFalse(session.is_expired())
        self.assertFalse(session.is_refresh_expired())
        
        # Test expiry
        expired_session = Session(
            session_id="expired_123",
            user_id="user_123",
            access_token="token",
            refresh_token="refresh",
            expires_at=now - timedelta(hours=1),
            refresh_expires_at=now + timedelta(days=30)
        )
        self.assertTrue(expired_session.is_expired())
        self.assertFalse(expired_session.is_refresh_expired())
    
    def test_api_key_dataclass(self):
        """Test APIKey dataclass"""
        api_key = APIKey(
            key_id="key_123",
            user_id="user_123",
            key_hash="hash123",
            name="Test API Key",
            permissions=["read", "write"],
            rate_limit_tier=RateLimitTier.BASIC
        )
        
        self.assertEqual(api_key.key_id, "key_123")
        self.assertEqual(api_key.name, "Test API Key")
        self.assertEqual(len(api_key.permissions), 2)
        self.assertTrue(api_key.is_active)
        self.assertFalse(api_key.is_expired())
        
        # Test expiry
        expired_key = APIKey(
            key_id="expired_key",
            user_id="user_123",
            key_hash="hash",
            name="Expired Key",
            expires_at=datetime.now() - timedelta(days=1)
        )
        self.assertTrue(expired_key.is_expired())
    
    def test_password_manager(self):
        """Test password hashing and verification"""
        pm = PasswordManager()
        password = "TestPassword123!"
        
        # Test hashing
        password_hash = pm.hash_password(password)
        self.assertIsInstance(password_hash, str)
        self.assertNotEqual(password, password_hash)
        
        # Test verification
        self.assertTrue(pm.verify_password(password, password_hash))
        self.assertFalse(pm.verify_password("wrong_password", password_hash))
        
        # Test different passwords produce different hashes
        hash1 = pm.hash_password(password)
        hash2 = pm.hash_password(password)
        self.assertNotEqual(hash1, hash2)  # Due to salt
    
    def test_token_manager(self):
        """Test JWT token management"""
        tm = TokenManager("test_secret_key")
        
        test_user = User(
            user_id="test_123",
            email="test@example.com",
            role=UserRole.USER,
            provider=AuthProvider.LOCAL
        )
        
        # Test access token generation and verification
        access_token = tm.generate_access_token(test_user)
        self.assertIsInstance(access_token, str)
        
        payload = tm.verify_token(access_token, 'access')
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], test_user.user_id)
        self.assertEqual(payload['email'], test_user.email)
        self.assertEqual(payload['role'], test_user.role.value)
        
        # Test refresh token generation and verification
        refresh_token = tm.generate_refresh_token(test_user)
        self.assertIsInstance(refresh_token, str)
        
        # Test invalid token
        invalid_payload = tm.verify_token("invalid_token", 'access')
        self.assertIsNone(invalid_payload)
    
    @patch.dict(os.environ, {'GOOGLE_CLIENT_ID': 'test_client_id'})
    def test_oauth_manager(self):
        """Test OAuth manager"""
        oauth = OAuthManager()
        
        # Test authorization URL generation
        auth_url = oauth.get_authorization_url(
            AuthProvider.GOOGLE,
            "http://localhost/callback",
            "test_state"
        )
        self.assertIsInstance(auth_url, str)
        self.assertIn("accounts.google.com", auth_url)
        self.assertIn("test_state", auth_url)
    
    @patch('production_auth_system.aiohttp.ClientSession')
    async def test_oauth_token_exchange(self, mock_session):
        """Test OAuth token exchange"""
        # Mock the aiohttp response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        oauth = OAuthManager()
        result = await oauth.exchange_code_for_token(
            AuthProvider.GOOGLE,
            "test_code",
            "http://localhost/callback"
        )
        
        self.assertIn("access_token", result)
        self.assertEqual(result["access_token"], "test_access_token")
    
    @patch('production_auth_system.aiohttp.ClientSession')
    async def test_oauth_user_info(self, mock_session):
        """Test OAuth user info retrieval"""
        # Mock the aiohttp response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "email": "test@example.com",
            "name": "Test User",
            "id": "123456"
        }
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        oauth = OAuthManager()
        result = await oauth.get_user_info(
            AuthProvider.GOOGLE,
            "test_access_token"
        )
        
        self.assertEqual(result["email"], "test@example.com")
        self.assertEqual(result["name"], "Test User")
    
    def test_rate_limiter(self):
        """Test rate limiting"""
        rate_limiter = RateLimiter()
        user_id = "test_user_123"
        tier = RateLimitTier.FREE
        
        # Test within limits
        for i in range(5):  # FREE tier allows 10/minute
            allowed, rate_info = rate_limiter.check_rate_limit(user_id, tier)
            self.assertTrue(allowed)
            self.assertIn('minute', rate_info)
            self.assertIn('limits', rate_info)
        
        # Test rate limit configuration
        config = rate_limiter.rate_limits[RateLimitTier.FREE]
        self.assertEqual(config.requests_per_minute, 10)
        self.assertEqual(config.requests_per_hour, 100)
        self.assertEqual(config.requests_per_day, 1000)
    
    def test_auth_database(self):
        """Test database operations"""
        db = AuthDatabase(self.db_path)
        
        # Test user creation
        test_user = User(
            user_id="db_test_123",
            email="dbtest@example.com",
            username="dbtest",
            full_name="DB Test User",
            password_hash="hash123",
            role=UserRole.USER,
            provider=AuthProvider.LOCAL
        )
        
        user_id = db.create_user(test_user)
        self.assertEqual(user_id, test_user.user_id)
        
        # Test user retrieval
        retrieved_user = db.get_user_by_email("dbtest@example.com")
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.email, test_user.email)
        self.assertEqual(retrieved_user.role, test_user.role)
        
        retrieved_user_by_id = db.get_user_by_id(test_user.user_id)
        self.assertIsNotNone(retrieved_user_by_id)
        self.assertEqual(retrieved_user_by_id.user_id, test_user.user_id)
        
        # Test session creation
        test_session = Session(
            session_id="session_db_test",
            user_id=test_user.user_id,
            access_token="access_token_test",
            refresh_token="refresh_token_test",
            expires_at=datetime.now() + timedelta(hours=1),
            refresh_expires_at=datetime.now() + timedelta(days=30)
        )
        
        session_id = db.create_session(test_session)
        self.assertEqual(session_id, test_session.session_id)
        
        # Test session retrieval
        retrieved_session = db.get_session(test_session.session_id)
        self.assertIsNotNone(retrieved_session)
        self.assertEqual(retrieved_session.user_id, test_user.user_id)
        
        # Test API key creation
        test_api_key = APIKey(
            key_id="api_key_test",
            user_id=test_user.user_id,
            key_hash="key_hash_test",
            name="Test API Key",
            permissions=["read", "write"]
        )
        
        key_id = db.create_api_key(test_api_key)
        self.assertEqual(key_id, test_api_key.key_id)
        
        # Test audit logging
        db.log_auth_event(
            test_user.user_id, "test_action", "test_resource",
            "192.168.1.1", "Test Agent", True, "Test details"
        )
        
        # Verify audit log entry
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM auth_audit_log WHERE user_id = ?",
                (test_user.user_id,)
            )
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)
    
    async def test_user_registration(self):
        """Test user registration"""
        success, message, user = await self.auth_system.register_user(
            email=self.test_email,
            password=self.test_password,
            full_name="Test User"
        )
        
        self.assertTrue(success)
        self.assertIn("successfully", message.lower())
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.test_email)
        self.assertEqual(user.role, UserRole.USER)
        
        # Test duplicate registration
        success2, message2, user2 = await self.auth_system.register_user(
            email=self.test_email,
            password=self.test_password
        )
        
        self.assertFalse(success2)
        self.assertIn("already exists", message2.lower())
        self.assertIsNone(user2)
    
    async def test_user_authentication(self):
        """Test user authentication"""
        # First register a user
        await self.auth_system.register_user(**self.test_user_data)
        
        # Test successful authentication
        success, message, session = await self.auth_system.authenticate_user(
            email=self.test_email,
            password=self.test_password,
            ip_address="192.168.1.100",
            user_agent="Test Client"
        )
        
        self.assertTrue(success)
        self.assertIn("successful", message.lower())
        self.assertIsNotNone(session)
        self.assertEqual(session.ip_address, "192.168.1.100")
        self.assertEqual(session.user_agent, "Test Client")
        
        # Test invalid credentials
        success2, message2, session2 = await self.auth_system.authenticate_user(
            email=self.test_email,
            password="wrong_password"
        )
        
        self.assertFalse(success2)
        self.assertIn("invalid", message2.lower())
        self.assertIsNone(session2)
        
        # Test non-existent user
        success3, message3, session3 = await self.auth_system.authenticate_user(
            email="nonexistent@example.com",
            password=self.test_password
        )
        
        self.assertFalse(success3)
        self.assertIn("invalid", message3.lower())
        self.assertIsNone(session3)
    
    async def test_token_verification(self):
        """Test token verification"""
        # Register and authenticate user
        await self.auth_system.register_user(**self.test_user_data)
        success, message, session = await self.auth_system.authenticate_user(
            self.test_email, self.test_password
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(session)
        
        # Test token verification
        payload = self.auth_system.verify_access_token(session.access_token)
        self.assertIsNotNone(payload)
        self.assertIn('user_id', payload)
        self.assertIn('email', payload)
        self.assertEqual(payload['email'], self.test_email)
        
        # Test invalid token
        invalid_payload = self.auth_system.verify_access_token("invalid_token")
        self.assertIsNone(invalid_payload)
    
    async def test_session_refresh(self):
        """Test session refresh"""
        # Register and authenticate user
        await self.auth_system.register_user(**self.test_user_data)
        success, message, session = await self.auth_system.authenticate_user(
            self.test_email, self.test_password
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(session)
        
        # Test session refresh
        success2, message2, new_session = await self.auth_system.refresh_session(
            session.refresh_token
        )
        
        self.assertTrue(success2)
        self.assertIn("refreshed", message2.lower())
        self.assertIsNotNone(new_session)
        # Don't compare access tokens directly due to timestamp differences
        self.assertNotEqual(new_session.session_id, session.session_id)
        self.assertEqual(new_session.user_id, session.user_id)
        
        # Test invalid refresh token
        success3, message3, session3 = await self.auth_system.refresh_session(
            "invalid_refresh_token"
        )
        
        self.assertFalse(success3)
        self.assertIn("invalid", message3.lower())
        self.assertIsNone(session3)
    
    @patch('production_auth_system.aiohttp.ClientSession')
    async def test_oauth_login(self, mock_session):
        """Test OAuth login flow"""
        # Mock OAuth responses
        mock_token_response = AsyncMock()
        mock_token_response.json.return_value = {
            "access_token": "oauth_access_token",
            "token_type": "Bearer"
        }
        
        mock_user_response = AsyncMock()
        mock_user_response.json.return_value = {
            "email": "oauth@example.com",
            "name": "OAuth User",
            "id": "oauth_123"
        }
        
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_token_response
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_user_response
        
        # Test OAuth login
        success, message, session = await self.auth_system.oauth_login(
            AuthProvider.GOOGLE,
            "oauth_code",
            "http://localhost/callback",
            ip_address="192.168.1.100"
        )
        
        self.assertTrue(success)
        self.assertIn("successful", message.lower())
        self.assertIsNotNone(session)
        
        # Verify user was created
        user = self.auth_system.db.get_user_by_email("oauth@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.provider, AuthProvider.GOOGLE)
        self.assertTrue(user.is_verified)  # OAuth users are pre-verified
    
    async def test_api_key_management(self):
        """Test API key creation and management"""
        # Register user
        await self.auth_system.register_user(**self.test_user_data)
        user = self.auth_system.db.get_user_by_email(self.test_email)
        
        # Create API key
        success, message, api_key_value = await self.auth_system.create_api_key(
            user.user_id,
            "Test API Key",
            permissions=["read", "write"],
            expires_in_days=30
        )
        
        self.assertTrue(success)
        self.assertIn("created", message.lower())
        self.assertIsNotNone(api_key_value)
        self.assertIsInstance(api_key_value, str)
        self.assertGreater(len(api_key_value), 20)
    
    def test_role_enum(self):
        """Test user role enumeration"""
        roles = [
            UserRole.ADMIN,
            UserRole.MANAGER,
            UserRole.USER,
            UserRole.VIEWER,
            UserRole.API_CLIENT
        ]
        
        for role in roles:
            self.assertIsInstance(role.value, str)
    
    def test_auth_provider_enum(self):
        """Test authentication provider enumeration"""
        providers = [
            AuthProvider.LOCAL,
            AuthProvider.GOOGLE,
            AuthProvider.MICROSOFT,
            AuthProvider.GITHUB,
            AuthProvider.SAML,
            AuthProvider.API_KEY
        ]
        
        for provider in providers:
            self.assertIsInstance(provider.value, str)
    
    def test_rate_limit_tier_enum(self):
        """Test rate limit tier enumeration"""
        tiers = [
            RateLimitTier.FREE,
            RateLimitTier.BASIC,
            RateLimitTier.PREMIUM,
            RateLimitTier.ENTERPRISE,
            RateLimitTier.UNLIMITED
        ]
        
        for tier in tiers:
            self.assertIsInstance(tier.value, str)
    
    def test_system_configuration(self):
        """Test system configuration"""
        config = self.auth_system.config
        
        self.assertIn('session_duration', config)
        self.assertIn('refresh_duration', config)
        self.assertIn('require_email_verification', config)
        self.assertIn('enable_rate_limiting', config)
        self.assertIn('enable_audit_logging', config)
        self.assertIn('default_role', config)
        self.assertIn('default_rate_limit_tier', config)
        
        self.assertIsInstance(config['session_duration'], timedelta)
        self.assertIsInstance(config['refresh_duration'], timedelta)
        self.assertEqual(config['default_role'], UserRole.USER)
    
    def test_system_status(self):
        """Test system status reporting"""
        status = self.auth_system.get_auth_status()
        
        self.assertIn('system_status', status)
        self.assertIn('total_users', status)
        self.assertIn('active_sessions', status)
        self.assertIn('active_api_keys', status)
        self.assertIn('features', status)
        self.assertIn('rate_limiting_enabled', status)
        self.assertIn('audit_logging_enabled', status)
        
        self.assertEqual(status['system_status'], 'operational')
        self.assertIsInstance(status['total_users'], int)
        self.assertIsInstance(status['features'], dict)
    
    async def test_comprehensive_auth_flow(self):
        """Test complete authentication workflow"""
        # 1. Register user
        success, message, user = await self.auth_system.register_user(
            email="workflow@example.com",
            password="WorkflowPassword123!",
            full_name="Workflow User"
        )
        self.assertTrue(success)
        
        # 2. Authenticate user
        success, message, session = await self.auth_system.authenticate_user(
            email="workflow@example.com",
            password="WorkflowPassword123!",
            ip_address="192.168.1.100"
        )
        self.assertTrue(success)
        
        # 3. Verify token
        payload = self.auth_system.verify_access_token(session.access_token)
        self.assertIsNotNone(payload)
        
        # 4. Create API key
        success, message, api_key = await self.auth_system.create_api_key(
            user.user_id, "Workflow API Key"
        )
        self.assertTrue(success)
        
        # 5. Refresh session
        success, message, new_session = await self.auth_system.refresh_session(
            session.refresh_token
        )
        self.assertTrue(success)
        # Don't compare tokens directly as they have different timestamps
        self.assertNotEqual(new_session.session_id, session.session_id)
        self.assertEqual(new_session.user_id, session.user_id)
        
        # 6. Check rate limiting
        for i in range(3):
            allowed, rate_info = self.auth_system.rate_limiter.check_rate_limit(
                user.user_id, user.rate_limit_tier
            )
            self.assertTrue(allowed)
        
        print(f"✅ Complete authentication workflow tested successfully")


class TestSecurityFeatures(unittest.TestCase):
    """Test security-specific features"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_security.db")
        self.auth_system = ProductionAuthSystem(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_password_security(self):
        """Test password security features"""
        pm = PasswordManager()
        
        # Test strong password hashing
        password = "StrongPassword123!"
        hash1 = pm.hash_password(password)
        hash2 = pm.hash_password(password)
        
        # Different salts should produce different hashes
        self.assertNotEqual(hash1, hash2)
        
        # Both should verify correctly
        self.assertTrue(pm.verify_password(password, hash1))
        self.assertTrue(pm.verify_password(password, hash2))
        
        # Wrong password should fail
        self.assertFalse(pm.verify_password("WrongPassword", hash1))
    
    def test_token_security(self):
        """Test token security features"""
        tm = TokenManager("test_secret_key")
        
        test_user = User(
            user_id="security_test",
            email="security@example.com",
            role=UserRole.USER,
            provider=AuthProvider.LOCAL
        )
        
        # Generate token
        token = tm.generate_access_token(test_user)
        
        # Verify with correct secret
        payload = tm.verify_token(token, 'access')
        self.assertIsNotNone(payload)
        
        # Test with wrong secret
        tm_wrong = TokenManager("wrong_secret_key")
        payload_wrong = tm_wrong.verify_token(token, 'access')
        self.assertIsNone(payload_wrong)
    
    def test_session_security(self):
        """Test session security"""
        now = datetime.now()
        
        # Test expired session
        expired_session = Session(
            session_id="expired_test",
            user_id="user_test",
            access_token="token",
            refresh_token="refresh",
            expires_at=now - timedelta(seconds=1),
            refresh_expires_at=now + timedelta(days=30)
        )
        
        self.assertTrue(expired_session.is_expired())
        self.assertFalse(expired_session.is_refresh_expired())
        
        # Test refresh token expiry
        refresh_expired = Session(
            session_id="refresh_expired",
            user_id="user_test",
            access_token="token",
            refresh_token="refresh",
            expires_at=now + timedelta(hours=1),
            refresh_expires_at=now - timedelta(seconds=1)
        )
        
        self.assertFalse(refresh_expired.is_expired())
        self.assertTrue(refresh_expired.is_refresh_expired())
    
    def test_rate_limiting_security(self):
        """Test rate limiting as security measure"""
        rate_limiter = RateLimiter()
        user_id = "rate_test_user"
        
        # Test FREE tier limits
        free_config = rate_limiter.rate_limits[RateLimitTier.FREE]
        self.assertEqual(free_config.requests_per_minute, 10)
        
        # Simulate multiple requests
        allowed_count = 0
        for i in range(15):  # Try more than the limit
            allowed, rate_info = rate_limiter.check_rate_limit(user_id, RateLimitTier.FREE)
            if allowed:
                allowed_count += 1
        
        # Should respect the rate limit
        self.assertLessEqual(allowed_count, free_config.requests_per_minute)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Authentication System Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionAuthSystem))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSecurityFeatures))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


def run_async_tests():
    """Run async tests"""
    async def async_test_runner():
        # Create test instance
        test_instance = TestProductionAuthSystem()
        test_instance.setUp()
        
        try:
            # Run async tests
            await test_instance.test_user_registration()
            await test_instance.test_user_authentication()
            await test_instance.test_token_verification()
            await test_instance.test_session_refresh()
            await test_instance.test_oauth_login()
            await test_instance.test_api_key_management()
            await test_instance.test_comprehensive_auth_flow()
            
            print("✅ All async tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Async test failed: {e}")
            return False
        finally:
            test_instance.tearDown()
    
    return asyncio.run(async_test_runner())


if __name__ == "__main__":
    # Run sync tests
    sync_success = run_comprehensive_tests()
    
    # Run async tests
    async_success = run_async_tests()
    
    overall_success = sync_success and async_success
    print(f"\n{'✅' if overall_success else '❌'} Overall test result: {'PASSED' if overall_success else 'FAILED'}")
    
    exit(0 if overall_success else 1)