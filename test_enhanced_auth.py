"""
Comprehensive test suite for enhanced authentication system
Tests JWT, RBAC, MFA, and SSO functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch, AsyncMock

# Import the auth components
from api.auth import (
    auth_service,
    Permission,
    MFAMethod,
    SSOProvider,
    auth_router,
    sso_router,
    get_current_user,
    require_permissions,
    AuthenticationError,
    AuthorizationError
)
from api.database import Base, User, UserRole
from api.database import Session as UserSession

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test app
app = FastAPI()
app.include_router(auth_router)
app.include_router(sso_router)

# Override database dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

from api.database import get_db
app.dependency_overrides[get_db] = override_get_db

class TestEnhancedAuthService:
    """Test the enhanced authentication service"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def db_session(self):
        """Get database session"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def test_user(self, db_session):
        """Create test user"""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash=auth_service.get_password_hash("testpassword"),
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = auth_service.get_password_hash(password)
        
        assert hashed != password
        assert auth_service.verify_password(password, hashed)
        assert not auth_service.verify_password("wrongpassword", hashed)
    
    def test_jwt_token_creation_and_validation(self):
        """Test JWT token creation and validation"""
        user_id = 123
        permissions = ["user:read", "transcript:write"]
        session_id = "test_session_123"
        
        # Create access token
        access_token = auth_service.create_access_token(
            user_id=user_id,
            permissions=permissions,
            session_id=session_id
        )
        
        assert access_token is not None
        
        # Decode and validate token
        payload = auth_service.decode_token(access_token, "access")
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["permissions"] == permissions
        assert payload["session_id"] == session_id
        assert payload["type"] == "access"
    
    def test_refresh_token_creation_and_validation(self):
        """Test refresh token creation and validation"""
        user_id = 123
        session_id = "test_session_123"
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(user_id, session_id)
        
        assert refresh_token is not None
        
        # Decode and validate token
        payload = auth_service.decode_token(refresh_token, "refresh")
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["session_id"] == session_id
        assert payload["type"] == "refresh"
    
    def test_user_authentication(self, db_session, test_user):
        """Test user authentication"""
        # Valid credentials
        authenticated_user = auth_service.authenticate_user(
            db_session, "test@example.com", "testpassword"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        
        # Invalid email
        assert auth_service.authenticate_user(
            db_session, "wrong@example.com", "testpassword"
        ) is None
        
        # Invalid password
        assert auth_service.authenticate_user(
            db_session, "test@example.com", "wrongpassword"
        ) is None
    
    def test_user_permissions(self, test_user):
        """Test user permission system"""
        permissions = auth_service.get_user_permissions(test_user)
        
        # User role should have specific permissions
        expected_permissions = [perm.value for perm in [
            Permission.USER_READ,
            Permission.TRANSCRIPT_READ,
            Permission.TRANSCRIPT_WRITE,
            Permission.TRANSCRIPT_SHARE,
            Permission.TEAM_READ,
            Permission.API_READ
        ]]
        
        assert all(perm in permissions for perm in expected_permissions)
        
        # Test permission checking
        assert auth_service.has_permission(permissions, Permission.USER_READ)
        assert not auth_service.has_permission(permissions, Permission.ADMIN_WRITE)
        
        # Test multiple permission checking
        assert auth_service.has_any_permission(
            permissions, [Permission.USER_READ, Permission.ADMIN_WRITE]
        )
        assert auth_service.has_all_permissions(
            permissions, [Permission.USER_READ, Permission.TRANSCRIPT_READ]
        )
        assert not auth_service.has_all_permissions(
            permissions, [Permission.USER_READ, Permission.ADMIN_WRITE]
        )
    
    def test_session_management(self, db_session, test_user):
        """Test user session management"""
        ip_address = "192.168.1.1"
        user_agent = "Test Browser"
        
        # Create session
        session = auth_service.create_user_session(
            db_session, test_user, ip_address, user_agent
        )
        
        assert session.user_id == test_user.id
        assert session.ip_address == ip_address
        assert session.user_agent == user_agent
        assert session.is_active is True
        
        # Invalidate session
        success = auth_service.invalidate_session(db_session, session.session_id)
        assert success is True
        
        # Check session is invalidated
        db_session.refresh(session)
        assert session.is_active is False
    
    def test_token_creation_flow(self, db_session, test_user):
        """Test complete token creation flow"""
        ip_address = "192.168.1.1"
        user_agent = "Test Browser"
        
        tokens = auth_service.create_tokens(db_session, test_user, ip_address, user_agent)
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0
        assert len(tokens.permissions) > 0
        
        # Verify access token
        access_payload = auth_service.decode_token(tokens.access_token, "access")
        assert access_payload["sub"] == str(test_user.id)
        
        # Verify refresh token
        refresh_payload = auth_service.decode_token(tokens.refresh_token, "refresh")
        assert refresh_payload["sub"] == str(test_user.id)
    
    def test_token_refresh(self, db_session, test_user):
        """Test token refresh functionality"""
        ip_address = "192.168.1.1"
        user_agent = "Test Browser"
        
        # Create initial tokens
        initial_tokens = auth_service.create_tokens(db_session, test_user, ip_address, user_agent)
        
        # Refresh tokens
        refreshed_tokens = auth_service.refresh_access_token(
            db_session, initial_tokens.refresh_token
        )
        
        assert refreshed_tokens is not None
        assert refreshed_tokens.access_token != initial_tokens.access_token
        assert refreshed_tokens.refresh_token == initial_tokens.refresh_token
    
    def test_mfa_setup(self, test_user):
        """Test MFA setup"""
        mfa_setup = auth_service.setup_totp_mfa(test_user)
        
        assert mfa_setup.method == MFAMethod.TOTP
        assert mfa_setup.secret is not None
        assert mfa_setup.qr_code is not None
        assert mfa_setup.qr_code.startswith("data:image/png;base64,")
    
    def test_backup_codes_generation(self):
        """Test backup codes generation"""
        backup_codes = auth_service.generate_backup_codes(10)
        
        assert len(backup_codes) == 10
        assert all(len(code) == 8 for code in backup_codes)  # 4 hex chars = 8 uppercase chars
        assert all(code.isupper() for code in backup_codes)

class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture
    def client(self):
        """Get test client"""
        return TestClient(app)
    
    def test_user_registration(self, client):
        """Test user registration endpoint"""
        user_data = {
            "email": "newuser@example.com",
            "password": "NewPassword123",
            "username": "newuser",
            "full_name": "New User"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == user_data["email"]
    
    def test_user_registration_duplicate_email(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "password": "Password123",
            "username": "user1",
            "full_name": "User One"
        }
        
        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Second registration with same email
        user_data["username"] = "user2"
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]
    
    def test_user_login(self, client):
        """Test user login endpoint"""
        # First register a user
        user_data = {
            "email": "logintest@example.com",
            "password": "LoginPassword123",
            "username": "logintest",
            "full_name": "Login Test"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Now login
        login_data = {
            "email": "logintest@example.com",
            "password": "LoginPassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Login successful"
        assert "user" in data
        assert "tokens" in data
    
    def test_user_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_token_refresh(self, client):
        """Test token refresh endpoint"""
        # Register and login
        user_data = {
            "email": "refreshtest@example.com",
            "password": "RefreshPassword123",
            "username": "refreshtest"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        tokens = register_response.json()["tokens"]
        
        # Refresh token
        refresh_data = {"refresh_token": tokens["refresh_token"]}
        response = client.post("/api/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != tokens["access_token"]
    
    def test_get_profile(self, client):
        """Test get user profile endpoint"""
        # Register user
        user_data = {
            "email": "profile@example.com",
            "password": "ProfilePassword123",
            "username": "profileuser",
            "full_name": "Profile User"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        access_token = register_response.json()["tokens"]["access_token"]
        
        # Get profile
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/api/auth/profile", headers=headers)
        
        assert response.status_code == 200
        profile = response.json()
        assert profile["email"] == user_data["email"]
        assert profile["username"] == user_data["username"]
        assert profile["full_name"] == user_data["full_name"]
    
    def test_change_password(self, client):
        """Test change password endpoint"""
        # Register user
        user_data = {
            "email": "changepass@example.com",
            "password": "OldPassword123",
            "username": "changepassuser"
        }
        register_response = client.post("/api/auth/register", json=user_data)
        access_token = register_response.json()["tokens"]["access_token"]
        
        # Change password
        password_data = {
            "current_password": "OldPassword123",
            "new_password": "NewPassword456"
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post("/api/auth/change-password", json=password_data, headers=headers)
        
        assert response.status_code == 200
        assert "Password changed successfully" in response.json()["message"]
    
    def test_unauthorized_access(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/auth/profile")
        assert response.status_code == 403  # No Authorization header

class TestPermissionSystem:
    """Test the permission and authorization system"""
    
    def test_permission_enum_values(self):
        """Test permission enum values"""
        assert Permission.USER_READ.value == "user:read"
        assert Permission.TRANSCRIPT_WRITE.value == "transcript:write"
        assert Permission.ADMIN_WRITE.value == "admin:write"
    
    def test_role_permissions_mapping(self):
        """Test role to permissions mapping"""
        from api.auth.enhanced_auth import ROLE_PERMISSIONS
        
        # User role permissions
        user_perms = ROLE_PERMISSIONS[UserRole.USER]
        assert Permission.USER_READ in user_perms
        assert Permission.TRANSCRIPT_READ in user_perms
        assert Permission.ADMIN_WRITE not in user_perms
        
        # Admin role permissions
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        assert Permission.USER_READ in admin_perms
        assert Permission.ADMIN_WRITE in admin_perms
        assert Permission.SYSTEM_MANAGE in admin_perms
        
        # Viewer role permissions
        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        assert Permission.USER_READ in viewer_perms
        assert Permission.TRANSCRIPT_READ in viewer_perms
        assert Permission.TRANSCRIPT_WRITE not in viewer_perms

@pytest.mark.asyncio
class TestSSOIntegration:
    """Test SSO integration functionality"""
    
    def test_sso_provider_enum(self):
        """Test SSO provider enum"""
        assert SSOProvider.GOOGLE.value == "google"
        assert SSOProvider.MICROSOFT.value == "microsoft"
        assert SSOProvider.OKTA.value == "okta"
        assert SSOProvider.SAML.value == "saml"
    
    @patch('api.auth.sso.httpx.AsyncClient')
    async def test_sso_token_exchange(self, mock_client):
        """Test SSO token exchange"""
        from api.auth.sso import sso_service
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test token exchange
        result = await sso_service.exchange_code_for_token(
            SSOProvider.GOOGLE, "mock_code", "http://localhost/callback"
        )
        
        assert result["access_token"] == "mock_access_token"
    
    @patch('api.auth.sso.httpx.AsyncClient')
    async def test_sso_user_info_google(self, mock_client):
        """Test getting user info from Google"""
        from api.auth.sso import sso_service
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "google_user_123",
            "email": "user@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "verified_email": True
        }
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Test user info retrieval
        user_info = await sso_service.get_user_info(SSOProvider.GOOGLE, "mock_token")
        
        assert user_info.email == "user@gmail.com"
        assert user_info.name == "Test User"
        assert user_info.provider == SSOProvider.GOOGLE
        assert user_info.provider_id == "google_user_123"
        assert user_info.verified is True

def test_rate_limiting():
    """Test rate limiting functionality"""
    from api.auth.dependencies import RateLimiter
    
    rate_limiter = RateLimiter(requests_per_minute=2)
    
    # This is a simplified test - in practice you'd test with actual requests
    assert rate_limiter.requests_per_minute == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])