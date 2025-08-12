"""
Simple test suite for enhanced authentication system
Tests core functionality without pytest dependencies
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the auth components
from api.auth import (
    auth_service,
    Permission,
    MFAMethod,
    SSOProvider,
    auth_router,
    sso_router
)
from api.database import Base, User, UserRole
from api.database import Session as UserSession

class TestEnhancedAuth:
    """Test the enhanced authentication system"""
    
    def __init__(self):
        # Setup test database
        self.engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
        self.tests_passed = 0
        self.tests_failed = 0
    
    def setup_test_db(self):
        """Setup fresh test database"""
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_db_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def create_test_user(self, db, email="test@example.com", username="testuser"):
        """Create a test user with unique identifiers"""
        import time
        timestamp = str(int(time.time() * 1000))  # millisecond timestamp
        
        user = User(
            email=f"{timestamp}_{email}",
            username=f"{timestamp}_{username}",
            password_hash=auth_service.get_password_hash("testpassword"),
            full_name="Test User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def assert_equal(self, actual, expected, test_name):
        """Simple assertion helper"""
        if actual == expected:
            print(f"   ✅ {test_name}: PASSED")
            self.tests_passed += 1
        else:
            print(f"   ❌ {test_name}: FAILED - Expected {expected}, got {actual}")
            self.tests_failed += 1
    
    def assert_true(self, condition, test_name):
        """Assert condition is true"""
        if condition:
            print(f"   ✅ {test_name}: PASSED")
            self.tests_passed += 1
        else:
            print(f"   ❌ {test_name}: FAILED - Condition was False")
            self.tests_failed += 1
    
    def assert_false(self, condition, test_name):
        """Assert condition is false"""
        if not condition:
            print(f"   ✅ {test_name}: PASSED")
            self.tests_passed += 1
        else:
            print(f"   ❌ {test_name}: FAILED - Condition was True")
            self.tests_failed += 1
    
    def assert_not_none(self, value, test_name):
        """Assert value is not None"""
        if value is not None:
            print(f"   ✅ {test_name}: PASSED")
            self.tests_passed += 1
        else:
            print(f"   ❌ {test_name}: FAILED - Value was None")
            self.tests_failed += 1
    
    def assert_none(self, value, test_name):
        """Assert value is None"""
        if value is None:
            print(f"   ✅ {test_name}: PASSED")
            self.tests_passed += 1
        else:
            print(f"   ❌ {test_name}: FAILED - Value was not None: {value}")
            self.tests_failed += 1
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        print("\n🔐 Testing Password Hashing...")
        
        password = "testpassword123"
        hashed = auth_service.get_password_hash(password)
        
        self.assert_true(hashed != password, "Password is hashed")
        self.assert_true(auth_service.verify_password(password, hashed), "Correct password verification")
        self.assert_false(auth_service.verify_password("wrongpassword", hashed), "Wrong password rejection")
    
    def test_jwt_tokens(self):
        """Test JWT token creation and validation"""
        print("\n🎫 Testing JWT Tokens...")
        
        user_id = 123
        permissions = ["user:read", "transcript:write"]
        session_id = "test_session_123"
        
        # Create access token
        access_token = auth_service.create_access_token(
            user_id=user_id,
            permissions=permissions,
            session_id=session_id
        )
        
        self.assert_not_none(access_token, "Access token created")
        
        # Decode and validate token
        payload = auth_service.decode_token(access_token, "access")
        self.assert_not_none(payload, "Token decoded successfully")
        
        if payload:
            self.assert_equal(payload["sub"], str(user_id), "User ID in token")
            self.assert_equal(payload["permissions"], permissions, "Permissions in token")
            self.assert_equal(payload["session_id"], session_id, "Session ID in token")
            self.assert_equal(payload["type"], "access", "Token type")
        
        # Test refresh token
        refresh_token = auth_service.create_refresh_token(user_id, session_id)
        self.assert_not_none(refresh_token, "Refresh token created")
        
        refresh_payload = auth_service.decode_token(refresh_token, "refresh")
        self.assert_not_none(refresh_payload, "Refresh token decoded")
        
        if refresh_payload:
            self.assert_equal(refresh_payload["sub"], str(user_id), "User ID in refresh token")
            self.assert_equal(refresh_payload["session_id"], session_id, "Session ID in refresh token")
            self.assert_equal(refresh_payload["type"], "refresh", "Refresh token type")
    
    def test_user_authentication(self):
        """Test user authentication"""
        print("\n👤 Testing User Authentication...")
        
        self.setup_test_db()
        db = self.get_db_session()
        
        try:
            test_user = self.create_test_user(db)
            
            # Valid credentials
            authenticated_user = auth_service.authenticate_user(
                db, test_user.email, "testpassword"
            )
            self.assert_not_none(authenticated_user, "Valid credentials authentication")
            
            if authenticated_user:
                self.assert_equal(authenticated_user.id, test_user.id, "Authenticated user ID matches")
            
            # Invalid email
            invalid_user = auth_service.authenticate_user(
                db, "wrong@example.com", "testpassword"
            )
            self.assert_none(invalid_user, "Invalid email rejection")
            
            # Invalid password
            invalid_pass = auth_service.authenticate_user(
                db, test_user.email, "wrongpassword"
            )
            self.assert_none(invalid_pass, "Invalid password rejection")
            
        finally:
            db.close()
    
    def test_permissions(self):
        """Test permission system"""
        print("\n🔑 Testing Permission System...")
        
        db = self.get_db_session()
        
        try:
            test_user = self.create_test_user(db)
            permissions = auth_service.get_user_permissions(test_user)
            
            # Check basic permissions
            self.assert_true(
                auth_service.has_permission(permissions, Permission.USER_READ),
                "User has USER_READ permission"
            )
            
            self.assert_false(
                auth_service.has_permission(permissions, Permission.ADMIN_WRITE),
                "User doesn't have ADMIN_WRITE permission"
            )
            
            # Test multiple permission checking
            self.assert_true(
                auth_service.has_any_permission(
                    permissions, [Permission.USER_READ, Permission.ADMIN_WRITE]
                ),
                "User has any of specified permissions"
            )
            
            self.assert_true(
                auth_service.has_all_permissions(
                    permissions, [Permission.USER_READ, Permission.TRANSCRIPT_READ]
                ),
                "User has all basic permissions"
            )
            
            self.assert_false(
                auth_service.has_all_permissions(
                    permissions, [Permission.USER_READ, Permission.ADMIN_WRITE]
                ),
                "User doesn't have all admin permissions"
            )
            
        finally:
            db.close()
    
    def test_session_management(self):
        """Test session management"""
        print("\n📱 Testing Session Management...")
        
        self.setup_test_db()
        db = self.get_db_session()
        
        try:
            test_user = self.create_test_user(db)
            ip_address = "192.168.1.1"
            user_agent = "Test Browser"
            
            # Create session
            session = auth_service.create_user_session(
                db, test_user, ip_address, user_agent
            )
            
            self.assert_equal(session.user_id, test_user.id, "Session user ID")
            self.assert_equal(session.ip_address, ip_address, "Session IP address")
            self.assert_equal(session.user_agent, user_agent, "Session user agent")
            self.assert_true(session.is_active, "Session is active")
            
            # Invalidate session
            success = auth_service.invalidate_session(db, session.session_id)
            self.assert_true(success, "Session invalidation success")
            
            # Check session is invalidated
            db.refresh(session)
            self.assert_false(session.is_active, "Session is inactive after invalidation")
            
        finally:
            db.close()
    
    def test_mfa_setup(self):
        """Test MFA setup"""
        print("\n🔐 Testing MFA Setup...")
        
        db = self.get_db_session()
        
        try:
            test_user = self.create_test_user(db)
            
            # Setup TOTP MFA
            mfa_setup = auth_service.setup_totp_mfa(test_user)
            
            self.assert_equal(mfa_setup.method, MFAMethod.TOTP, "MFA method is TOTP")
            self.assert_not_none(mfa_setup.secret, "MFA secret generated")
            self.assert_not_none(mfa_setup.qr_code, "QR code generated")
            self.assert_true(
                mfa_setup.qr_code.startswith("data:image/png;base64,"),
                "QR code is base64 PNG"
            )
            
            # Test backup codes
            backup_codes = auth_service.generate_backup_codes(10)
            self.assert_equal(len(backup_codes), 10, "Correct number of backup codes")
            self.assert_true(
                all(len(code) == 8 for code in backup_codes),
                "All backup codes are 8 characters"
            )
            
        finally:
            db.close()
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🌐 Testing API Endpoints...")
        
        # Create test app
        app = FastAPI()
        app.include_router(auth_router)
        app.include_router(sso_router)
        
        # Override database dependency
        from api.database import get_db
        
        def override_get_db():
            try:
                db = self.SessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Setup fresh database
        self.setup_test_db()
        
        client = TestClient(app)
        
        # Test registration with unique data
        import time
        timestamp = str(int(time.time() * 1000))
        register_data = {
            "email": f"apitest_{timestamp}@example.com",
            "password": "ApiTestPassword123",
            "username": f"apitest_{timestamp}",
            "full_name": "API Test User"
        }
        
        try:
            response = client.post("/api/auth/register", json=register_data)
            self.assert_equal(response.status_code, 201, "Registration status code")
            
            if response.status_code == 201:
                data = response.json()
                self.assert_equal(data["user"]["email"], register_data["email"], "Registration email")
                self.assert_true("tokens" in data, "Registration returns tokens")
                
                # Test login
                login_data = {
                    "email": register_data["email"],
                    "password": "ApiTestPassword123"
                }
                
                login_response = client.post("/api/auth/login", json=login_data)
                self.assert_equal(login_response.status_code, 200, "Login status code")
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    access_token = login_data['tokens']['access_token']
                    
                    # Test protected endpoint
                    headers = {"Authorization": f"Bearer {access_token}"}
                    profile_response = client.get("/api/auth/profile", headers=headers)
                    self.assert_equal(profile_response.status_code, 200, "Profile access status")
                    
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        self.assert_equal(profile['email'], register_data["email"], "Profile email")
        
        except Exception as e:
            print(f"   ❌ API endpoint test failed: {str(e)}")
            self.tests_failed += 1
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Enhanced Authentication System - Simple Test Suite")
        print("=" * 70)
        
        try:
            self.test_password_hashing()
            self.test_jwt_tokens()
            self.test_user_authentication()
            self.test_permissions()
            self.test_session_management()
            self.test_mfa_setup()
            self.test_api_endpoints()
            
            print("\n" + "=" * 70)
            print(f"📊 Test Results: {self.tests_passed} passed, {self.tests_failed} failed")
            
            if self.tests_failed == 0:
                print("✅ All tests passed! Authentication system is working correctly.")
                
                print(f"\n🎯 Verified Features:")
                print("   ✅ Password hashing and verification")
                print("   ✅ JWT token creation and validation")
                print("   ✅ User authentication")
                print("   ✅ Role-based permission system")
                print("   ✅ Session management")
                print("   ✅ Multi-factor authentication setup")
                print("   ✅ API endpoint functionality")
                
                return True
            else:
                print(f"❌ {self.tests_failed} tests failed. Please check the implementation.")
                return False
                
        except Exception as e:
            print(f"\n❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            try:
                if os.path.exists("./test_auth.db"):
                    os.remove("./test_auth.db")
            except:
                pass

def main():
    """Run the test suite"""
    tester = TestEnhancedAuth()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())