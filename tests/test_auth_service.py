"""
Unit tests for JWT authentication service
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import jwt

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth_service import (
    AuthService,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password,
    generate_api_key,
    hash_api_key
)


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_get_password_hash(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        assert hashed.startswith('$2b$')  # bcrypt prefix
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) == False
    
    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True


class TestTokenCreation:
    """Test token creation functions"""
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_create_access_token(self):
        """Test access token creation"""
        data = {'user_id': 123, 'username': 'testuser'}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Decode and verify
        decoded = jwt.decode(token, 'test-secret-key', algorithms=['HS256'])
        assert decoded['user_id'] == 123
        assert decoded['username'] == 'testuser'
        assert 'exp' in decoded
        assert decoded['type'] == 'access'
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {'user_id': 123, 'username': 'testuser'}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        
        # Decode and verify
        decoded = jwt.decode(token, 'test-secret-key', algorithms=['HS256'])
        assert decoded['user_id'] == 123
        assert decoded['username'] == 'testuser'
        assert 'exp' in decoded
        assert decoded['type'] == 'refresh'
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_token_expiration_times(self):
        """Test that refresh tokens have longer expiration"""
        data = {'user_id': 123}
        
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)
        
        access_decoded = jwt.decode(access_token, 'test-secret-key', algorithms=['HS256'])
        refresh_decoded = jwt.decode(refresh_token, 'test-secret-key', algorithms=['HS256'])
        
        # Refresh token should expire later than access token
        assert refresh_decoded['exp'] > access_decoded['exp']


class TestTokenVerification:
    """Test token verification"""
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        data = {'user_id': 123, 'username': 'testuser'}
        token = create_access_token(data)
        
        is_valid, payload = verify_token(token)
        
        assert is_valid == True
        assert payload['user_id'] == 123
        assert payload['username'] == 'testuser'
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        is_valid, error = verify_token('invalid.token.here')
        
        assert is_valid == False
        assert error is not None
        assert isinstance(error, str)
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_verify_expired_token(self):
        """Test verifying an expired token"""
        # Create token that expires immediately
        data = {'user_id': 123}
        expires_delta = timedelta(seconds=-1)  # Already expired
        
        payload = data.copy()
        expire = datetime.utcnow() + expires_delta
        payload.update({'exp': expire, 'type': 'access'})
        
        token = jwt.encode(payload, 'test-secret-key', algorithm='HS256')
        
        is_valid, error = verify_token(token)
        
        assert is_valid == False
        assert 'expired' in error.lower()
    
    @patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'})
    def test_verify_wrong_secret(self):
        """Test verifying token with wrong secret"""
        data = {'user_id': 123}
        token = create_access_token(data)
        
        # Try to verify with wrong secret
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'wrong-secret'}):
            is_valid, error = verify_token(token)
        
        assert is_valid == False
        assert error is not None


class TestAPIKeyFunctions:
    """Test API key generation and hashing"""
    
    def test_generate_api_key(self):
        """Test API key generation"""
        key = generate_api_key()
        
        assert isinstance(key, str)
        assert len(key) == 32  # 32 character hex string
        assert all(c in '0123456789abcdef' for c in key)
    
    def test_generate_unique_api_keys(self):
        """Test that generated keys are unique"""
        keys = [generate_api_key() for _ in range(100)]
        
        # All keys should be unique
        assert len(keys) == len(set(keys))
    
    def test_hash_api_key(self):
        """Test API key hashing"""
        key = "test-api-key-12345"
        hashed = hash_api_key(key)
        
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA-256 produces 64 character hex
        assert hashed != key
    
    def test_hash_api_key_consistency(self):
        """Test that same key produces same hash"""
        key = "test-api-key-12345"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        
        assert hash1 == hash2


class TestAuthService:
    """Test AuthService class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def auth_service(self, mock_db):
        """Create AuthService instance with mock DB"""
        return AuthService(mock_db)
    
    def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration"""
        # Mock database queries
        mock_db.query().filter().first.return_value = None  # No existing user
        
        success, message, user_data = auth_service.register_user(
            username="newuser",
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User"
        )
        
        assert success == True
        assert message == "User registered successfully"
        assert user_data is not None
        assert user_data['username'] == "newuser"
        assert user_data['email'] == "newuser@example.com"
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_register_user_duplicate_username(self, auth_service, mock_db):
        """Test registration with duplicate username"""
        # Mock existing user
        existing_user = Mock()
        mock_db.query().filter().first.return_value = existing_user
        
        success, message, user_data = auth_service.register_user(
            username="existinguser",
            email="new@example.com",
            password="SecurePass123!"
        )
        
        assert success == False
        assert "already exists" in message
        assert user_data is None
        
        # Should not commit
        mock_db.commit.assert_not_called()
    
    def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication"""
        # Mock user
        mock_user = Mock()
        mock_user.id = 123
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.password_hash = get_password_hash("TestPass123!")
        mock_user.is_active = True
        mock_user.failed_login_attempts = 0
        
        # Configure query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        success, message, tokens = auth_service.authenticate_user(
            username_or_email="testuser",
            password="TestPass123!",
            ip_address="127.0.0.1"
        )
        
        assert success == True
        assert message == "Authentication successful"
        assert tokens is not None
        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['token_type'] == 'bearer'
    
    def test_authenticate_user_wrong_password(self, auth_service, mock_db):
        """Test authentication with wrong password"""
        # Mock user
        mock_user = Mock()
        mock_user.password_hash = get_password_hash("CorrectPass123!")
        mock_user.is_active = True
        mock_user.failed_login_attempts = 0
        
        # Configure query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        success, message, tokens = auth_service.authenticate_user(
            username_or_email="testuser",
            password="WrongPass123!"
        )
        
        assert success == False
        assert "Invalid credentials" in message
        assert tokens is None
        
        # Should increment failed attempts
        assert mock_user.failed_login_attempts == 1
    
    def test_authenticate_user_account_locked(self, auth_service, mock_db):
        """Test authentication with locked account"""
        # Mock locked user
        mock_user = Mock()
        mock_user.password_hash = get_password_hash("TestPass123!")
        mock_user.is_active = True
        mock_user.failed_login_attempts = 5  # Max attempts reached
        
        # Configure query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        success, message, tokens = auth_service.authenticate_user(
            username_or_email="testuser",
            password="TestPass123!"
        )
        
        assert success == False
        assert "locked" in message.lower()
        assert tokens is None
    
    def test_refresh_access_token_success(self, auth_service, mock_db):
        """Test successful token refresh"""
        # Create a valid refresh token
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-secret-key'}):
            refresh_token = create_refresh_token({'user_id': 123})
            
            # Mock user and session
            mock_user = Mock()
            mock_user.id = 123
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.is_active = True
            
            mock_session = Mock()
            mock_session.refresh_token = refresh_token
            mock_session.expires_at = datetime.utcnow() + timedelta(days=1)
            mock_session.user = mock_user
            
            # Configure query chain
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_session
            mock_db.query.return_value = mock_query
            
            success, message, new_token = auth_service.refresh_access_token(refresh_token)
            
            assert success == True
            assert message == "Token refreshed successfully"
            assert new_token is not None
            assert isinstance(new_token, str)
    
    def test_create_api_key_success(self, auth_service, mock_db):
        """Test API key creation"""
        # Mock user
        mock_user = Mock()
        mock_user.id = 123
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        success, message, key_data = auth_service.create_api_key(
            user_id=123,
            name="Test API Key"
        )
        
        assert success == True
        assert message == "API key created successfully"
        assert key_data is not None
        assert 'key' in key_data
        assert 'key_id' in key_data
        assert key_data['name'] == "Test API Key"
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_verify_api_key_success(self, auth_service, mock_db):
        """Test API key verification"""
        api_key = "test-api-key-12345"
        hashed_key = hash_api_key(api_key)
        
        # Mock API key record
        mock_api_key = Mock()
        mock_api_key.is_active = True
        mock_api_key.expires_at = None
        mock_api_key.user_id = 123
        mock_api_key.user = Mock(is_active=True)
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_api_key
        mock_db.query.return_value = mock_query
        
        is_valid, user_id = auth_service.verify_api_key(api_key)
        
        assert is_valid == True
        assert user_id == 123
        
        # Should update last used timestamp
        assert mock_api_key.last_used_at is not None
        mock_db.commit.assert_called_once()
    
    def test_logout_user_success(self, auth_service, mock_db):
        """Test user logout"""
        token = "test-token"
        
        # Mock session
        mock_session = Mock()
        mock_session.is_active = True
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_session
        mock_db.query.return_value = mock_query
        
        success = auth_service.logout_user(token)
        
        assert success == True
        assert mock_session.is_active == False
        assert mock_session.revoked_at is not None
        mock_db.commit.assert_called_once()


class TestAuthServiceEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def auth_service(self, mock_db):
        """Create AuthService instance with mock DB"""
        return AuthService(mock_db)
    
    def test_register_with_weak_password(self, auth_service, mock_db):
        """Test registration with weak password"""
        mock_db.query().filter().first.return_value = None
        
        success, message, user_data = auth_service.register_user(
            username="newuser",
            email="new@example.com",
            password="weak"  # Too short
        )
        
        assert success == False
        assert "at least 8 characters" in message.lower()
        assert user_data is None
    
    def test_register_with_invalid_email(self, auth_service, mock_db):
        """Test registration with invalid email"""
        mock_db.query().filter().first.return_value = None
        
        success, message, user_data = auth_service.register_user(
            username="newuser",
            email="invalid-email",  # Invalid format
            password="SecurePass123!"
        )
        
        assert success == False
        assert "valid email" in message.lower()
        assert user_data is None
    
    def test_authenticate_nonexistent_user(self, auth_service, mock_db):
        """Test authentication with non-existent user"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        success, message, tokens = auth_service.authenticate_user(
            username_or_email="nonexistent",
            password="AnyPass123!"
        )
        
        assert success == False
        assert "Invalid credentials" in message
        assert tokens is None
    
    def test_database_error_handling(self, auth_service, mock_db):
        """Test handling of database errors"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection error")
        
        success, message, user_data = auth_service.register_user(
            username="newuser",
            email="new@example.com",
            password="SecurePass123!"
        )
        
        assert success == False
        assert "error occurred" in message.lower()
        assert user_data is None
        
        # Should rollback on error
        mock_db.rollback.assert_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])