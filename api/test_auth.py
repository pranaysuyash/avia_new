"""
Test Authentication Endpoints
Run with: python -m pytest api/test_auth.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.database import Base, get_db
from api.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

# Test data
test_user = {
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
}

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_register_user(self):
        """Test user registration"""
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 201
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        assert "user" in data
        user = data["user"]
        assert user["email"] == test_user["email"]
        assert user["name"] == test_user["name"]
        assert user["role"] == "user"
        assert "id" in user
        assert "created_at" in user
    
    def test_register_duplicate_user(self):
        """Test registering duplicate user"""
        # First registration
        client.post("/api/auth/register", json=test_user)
        
        # Try to register again
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"
    
    def test_login_success(self):
        """Test successful login"""
        # Register user first
        client.post("/api/auth/register", json=test_user)
        
        # Login
        response = client.post(
            "/api/auth/login",
            data={
                "username": test_user["email"],  # OAuth2 uses 'username' field
                "password": test_user["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check tokens
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Check user data
        assert data["user"]["email"] == test_user["email"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"
    
    def test_get_profile(self):
        """Test getting user profile"""
        # Register and login
        register_response = client.post("/api/auth/register", json=test_user)
        token = register_response.json()["access_token"]
        
        # Get profile
        response = client.get(
            "/api/users/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        profile = response.json()
        assert profile["email"] == test_user["email"]
        assert profile["name"] == test_user["name"]
    
    def test_get_profile_unauthorized(self):
        """Test getting profile without auth"""
        response = client.get("/api/users/profile")
        assert response.status_code == 401
    
    def test_update_profile(self):
        """Test updating user profile"""
        # Register and login
        register_response = client.post("/api/auth/register", json=test_user)
        token = register_response.json()["access_token"]
        
        # Update profile
        new_name = "Updated Name"
        response = client.put(
            "/api/users/profile",
            params={"name": new_name},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        profile = response.json()
        assert profile["name"] == new_name
    
    def test_logout(self):
        """Test logout"""
        # Register and login
        register_response = client.post("/api/auth/register", json=test_user)
        token = register_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
    
    def test_create_api_key(self):
        """Test creating API key"""
        # Register and login
        register_response = client.post("/api/auth/register", json=test_user)
        token = register_response.json()["access_token"]
        
        # Create API key
        response = client.post(
            "/api/users/api-keys",
            json={"name": "Test API Key"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        
        api_key_data = response.json()
        assert "key" in api_key_data
        assert api_key_data["name"] == "Test API Key"
        assert "id" in api_key_data
        assert "created_at" in api_key_data
    
    def test_list_api_keys(self):
        """Test listing API keys"""
        # Register and login
        register_response = client.post("/api/auth/register", json=test_user)
        token = register_response.json()["access_token"]
        
        # Create an API key
        client.post(
            "/api/users/api-keys",
            json={"name": "Test Key"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # List API keys
        response = client.get(
            "/api/users/api-keys",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        keys = response.json()
        assert len(keys) == 1
        assert keys[0]["name"] == "Test Key"
        assert "key" not in keys[0]  # Should not expose the actual key

if __name__ == "__main__":
    pytest.main([__file__, "-v"])