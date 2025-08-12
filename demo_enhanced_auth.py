"""
Demo script showcasing the Enhanced Authentication and Authorization System
"""

import asyncio
import sys
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the enhanced auth system
from api.auth import (
    auth_service,
    auth_router,
    sso_router,
    Permission,
    MFAMethod,
    SSOProvider
)

def create_demo_app():
    """Create a demo FastAPI app with enhanced auth"""
    app = FastAPI(
        title="Enhanced Auth Demo",
        description="Demo of comprehensive authentication system",
        version="1.0.0"
    )
    
    # Include auth routers
    app.include_router(auth_router)
    app.include_router(sso_router)
    
    return app

async def demo_auth_service():
    """Demonstrate the core authentication service"""
    print("🔐 Enhanced Authentication Service Demo")
    print("=" * 50)
    
    # Password hashing
    print("\n1. Password Security:")
    password = "SecurePassword123!"
    hashed = auth_service.get_password_hash(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    print(f"   Verification: {auth_service.verify_password(password, hashed)}")
    
    # JWT tokens
    print("\n2. JWT Token System:")
    permissions = [Permission.USER_READ.value, Permission.TRANSCRIPT_WRITE.value]
    access_token = auth_service.create_access_token(
        user_id=123,
        permissions=permissions,
        session_id="demo_session_123"
    )
    print(f"   Access token created: {len(access_token)} characters")
    
    # Decode token
    payload = auth_service.decode_token(access_token)
    print(f"   Token payload: user_id={payload['sub']}, permissions={len(payload['permissions'])}")
    
    # Refresh token
    refresh_token = auth_service.create_refresh_token(123, "demo_session_123")
    print(f"   Refresh token created: {len(refresh_token)} characters")
    
    # Permission system
    print("\n3. Permission System:")
    user_permissions = [Permission.USER_READ.value, Permission.TRANSCRIPT_READ.value]
    
    print(f"   User permissions: {user_permissions}")
    print(f"   Has USER_READ: {auth_service.has_permission(user_permissions, Permission.USER_READ)}")
    print(f"   Has ADMIN_WRITE: {auth_service.has_permission(user_permissions, Permission.ADMIN_WRITE)}")
    
    required_perms = [Permission.USER_READ, Permission.TRANSCRIPT_READ]
    print(f"   Has all required: {auth_service.has_all_permissions(user_permissions, required_perms)}")
    
    # MFA setup
    print("\n4. Multi-Factor Authentication:")
    from api.database import User, UserRole
    
    # Create mock user for MFA demo
    mock_user = User()
    mock_user.email = "demo@example.com"
    mock_user.role = UserRole.USER
    
    mfa_setup = auth_service.setup_totp_mfa(mock_user)
    print(f"   MFA method: {mfa_setup.method}")
    print(f"   Secret generated: {len(mfa_setup.secret)} characters")
    print(f"   QR code available: {'Yes' if mfa_setup.qr_code else 'No'}")
    
    # Backup codes
    backup_codes = auth_service.generate_backup_codes()
    print(f"   Backup codes generated: {len(backup_codes)} codes")
    print(f"   Sample backup code: {backup_codes[0]}")

def demo_api_endpoints():
    """Demonstrate API endpoints"""
    print("\n🌐 API Endpoints Demo")
    print("=" * 50)
    
    app = create_demo_app()
    client = TestClient(app)
    
    print("\n1. Available Endpoints:")
    
    # Test SSO providers endpoint
    response = client.get("/api/auth/sso/providers")
    if response.status_code == 200:
        providers = response.json()["providers"]
        print(f"   ✅ SSO Providers: {len(providers)} available")
        for provider in providers:
            status = "✅" if provider["enabled"] else "❌"
            print(f"      {status} {provider['name']}: {provider['description']}")
    
    # Test registration endpoint structure
    print(f"\n2. Authentication Endpoints:")
    print(f"   📝 POST /api/auth/register - User registration")
    print(f"   🔑 POST /api/auth/login - User login")
    print(f"   🔄 POST /api/auth/refresh - Token refresh")
    print(f"   🚪 POST /api/auth/logout - User logout")
    print(f"   👤 GET /api/auth/profile - User profile")
    print(f"   🔒 POST /api/auth/change-password - Password change")
    
    print(f"\n3. MFA Endpoints:")
    print(f"   📱 POST /api/auth/mfa/setup - Setup MFA")
    print(f"   ✅ POST /api/auth/mfa/verify - Verify MFA")
    print(f"   ❌ DELETE /api/auth/mfa - Disable MFA")
    
    print(f"\n4. SSO Endpoints:")
    print(f"   🌐 GET /api/auth/sso/providers - Available providers")
    print(f"   🔗 GET /api/auth/sso/{{provider}}/authorize - Start OAuth flow")
    print(f"   ✅ GET /api/auth/sso/{{provider}}/callback - OAuth callback")
    print(f"   🔗 POST /api/auth/sso/{{provider}}/link - Link SSO account")
    
    print(f"\n5. Admin Endpoints:")
    print(f"   👥 GET /api/auth/users - List users (admin)")
    print(f"   🎭 PUT /api/auth/users/{{id}}/role - Update user role")
    print(f"   🔄 PUT /api/auth/users/{{id}}/status - Update user status")

def demo_security_features():
    """Demonstrate security features"""
    print("\n🛡️ Security Features Demo")
    print("=" * 50)
    
    print("\n1. Role-Based Access Control (RBAC):")
    from api.database import UserRole
    from api.auth.enhanced_auth import ROLE_PERMISSIONS
    
    for role, permissions in ROLE_PERMISSIONS.items():
        print(f"   {role.value.upper()}:")
        print(f"      - {len(permissions)} permissions")
        print(f"      - Can read users: {Permission.USER_READ in permissions}")
        print(f"      - Can manage system: {Permission.SYSTEM_MANAGE in permissions}")
    
    print("\n2. Session Management:")
    print("   ✅ Unique session IDs for each login")
    print("   ✅ IP address and user agent tracking")
    print("   ✅ Session expiration and cleanup")
    print("   ✅ Multi-device session management")
    print("   ✅ Session invalidation on logout")
    
    print("\n3. Multi-Factor Authentication:")
    print("   📱 TOTP (Time-based One-Time Password)")
    print("   📧 Email-based verification")
    print("   📱 SMS-based verification")
    print("   🔑 Backup codes for recovery")
    print("   🔒 QR code generation for authenticator apps")
    
    print("\n4. Single Sign-On (SSO):")
    print("   🌐 Google OAuth2 integration")
    print("   🏢 Microsoft Azure AD integration")
    print("   🔐 Okta enterprise SSO")
    print("   📋 SAML 2.0 support (enterprise)")
    print("   🔗 Account linking capabilities")
    
    print("\n5. Security Best Practices:")
    print("   🔒 Bcrypt password hashing")
    print("   🎫 JWT tokens with expiration")
    print("   🔄 Refresh token rotation")
    print("   🛡️ CSRF protection with state parameters")
    print("   ⏱️ Rate limiting per user/IP")
    print("   📝 Comprehensive audit logging")

def demo_integration_examples():
    """Show integration examples"""
    print("\n🔧 Integration Examples")
    print("=" * 50)
    
    print("\n1. FastAPI Dependency Usage:")
    print("""
    from api.auth import get_current_user, require_permissions, Permission
    
    @app.get("/protected")
    async def protected_endpoint(
        current_user = Depends(get_current_user)
    ):
        return {"user": current_user.email}
    
    @app.post("/admin-only")
    async def admin_endpoint(
        user = Depends(require_permissions(Permission.ADMIN_WRITE))
    ):
        return {"message": "Admin access granted"}
    """)
    
    print("\n2. Frontend Integration:")
    print("""
    // Login request
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email: 'user@example.com',
            password: 'password123'
        })
    });
    
    const data = await response.json();
    localStorage.setItem('access_token', data.tokens.access_token);
    """)
    
    print("\n3. SSO Integration:")
    print("""
    // Start Google OAuth flow
    const authUrl = await fetch('/api/auth/sso/google/authorize?redirect_uri=...');
    window.location.href = authUrl.authorization_url;
    
    // Handle callback
    const callback = await fetch('/api/auth/sso/google/callback?code=...&state=...');
    const tokens = await callback.json();
    """)

async def main():
    """Run all demos"""
    print("🚀 Enhanced Authentication & Authorization System Demo")
    print("=" * 80)
    
    try:
        # Run demos
        await demo_auth_service()
        demo_api_endpoints()
        demo_security_features()
        demo_integration_examples()
        
        print("\n" + "=" * 80)
        print("✅ Enhanced Authentication System Demo Complete!")
        print("=" * 80)
        
        print(f"\n🎯 Key Features Demonstrated:")
        features = [
            "✅ JWT-based authentication with refresh tokens",
            "✅ Role-based access control (RBAC) with granular permissions",
            "✅ Multi-factor authentication (TOTP, SMS, Email)",
            "✅ Single Sign-On (Google, Microsoft, Okta, SAML)",
            "✅ Session management with device tracking",
            "✅ Password security with bcrypt hashing",
            "✅ Comprehensive API endpoints",
            "✅ Security best practices implementation",
            "✅ Easy FastAPI integration",
            "✅ Enterprise-ready features"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        print(f"\n🔗 Next Steps:")
        print("   1. Integrate with your FastAPI application")
        print("   2. Configure SSO providers (Google, Microsoft, etc.)")
        print("   3. Set up MFA for enhanced security")
        print("   4. Customize permissions for your use case")
        print("   5. Add frontend integration")
        
        print(f"\n📚 Available Endpoints:")
        print("   - Authentication: /api/auth/*")
        print("   - SSO: /api/auth/sso/*")
        print("   - Documentation: /docs (when integrated)")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())