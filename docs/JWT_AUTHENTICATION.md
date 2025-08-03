# JWT Authentication Implementation

## Overview

This document describes the JWT (JSON Web Token) authentication system implemented for the Audio/Video Transcription API. The system provides secure user authentication, session management, and API key support with full PostgreSQL integration.

## Architecture

### Components

1. **JWT Authentication Service** (`api/auth_service.py`)
   - User registration and login
   - Token generation and validation
   - Session management
   - API key management
   - Password hashing with bcrypt

2. **Authentication Endpoints** (`api/endpoints/auth_endpoints.py`)
   - `/api/auth/register` - User registration
   - `/api/auth/login` - User login
   - `/api/auth/logout` - User logout
   - `/api/auth/refresh` - Token refresh
   - `/api/auth/me` - Get current user
   - `/api/auth/api-keys` - API key management

3. **Authentication Middleware** (`api/auth_middleware.py`)
   - Request authentication
   - Role-based access control
   - Permission checking
   - Support for both JWT tokens and API keys

## Features

### User Management
- User registration with email validation
- Secure password storage using bcrypt
- User profiles with roles and permissions
- Email verification support
- Account activation/deactivation

### Token Management
- Access tokens (24-hour expiry)
- Refresh tokens (30-day expiry)
- Token blacklisting on logout
- Automatic session cleanup

### API Key Support
- Generate long-lived API keys
- Key permissions and scoping
- Usage tracking and rate limiting
- Key revocation

### Security Features
- Password hashing with bcrypt
- JWT tokens with configurable expiry
- Session tracking with IP and user agent
- Rate limiting per user role
- Audit logging for security events

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token TEXT NOT NULL,
    refresh_token TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP
);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions JSONB,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    total_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage

### 1. User Registration

```python
POST /api/auth/register
Content-Type: application/json

{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123",
    "full_name": "John Doe"
}

Response:
{
    "success": true,
    "message": "Registration successful",
    "data": {
        "id": 1,
        "email": "user@example.com",
        "username": "johndoe",
        "role": "user"
    }
}
```

### 2. User Login

```python
POST /api/auth/login
Content-Type: application/json

{
    "username_or_email": "johndoe",
    "password": "securepassword123"
}

Response:
{
    "success": true,
    "message": "Authentication successful",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "id": 1,
            "username": "johndoe",
            "email": "user@example.com",
            "role": "user"
        }
    }
}
```

### 3. Using Authentication in Requests

```python
GET /api/transcription/list
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

# Or using API key
GET /api/transcription/list
X-API-Key: pk_1234567890abcdef...
```

### 4. Refreshing Tokens

```python
POST /api/auth/refresh
Content-Type: application/json

{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
    "success": true,
    "message": "Token refreshed",
    "data": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "token_type": "bearer",
        "expires_in": 86400
    }
}
```

## Protecting Endpoints

### Using Dependency Injection

```python
from api.auth_middleware import get_current_active_user, require_admin

@router.get("/protected")
async def protected_endpoint(current_user: dict = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user['username']}"}

@router.post("/admin-only")
async def admin_endpoint(current_user: dict = Depends(require_admin)):
    return {"message": "Admin access granted"}
```

### Role-Based Access Control

```python
from api.auth_middleware import RoleChecker

require_premium = RoleChecker(['admin', 'premium'])

@router.get("/premium-content")
async def premium_endpoint(current_user: dict = Depends(require_premium)):
    return {"message": "Premium content"}
```

### Permission-Based Access

```python
from api.auth_middleware import PermissionChecker

require_export = PermissionChecker(['export'])

@router.post("/export")
async def export_endpoint(current_user: dict = Depends(require_export)):
    return {"message": "Export permitted"}
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Security
BCRYPT_ROUNDS=12
SESSION_CLEANUP_INTERVAL_HOURS=6
```

### Customizing Token Expiry

```python
# In api/auth_service.py
self.access_token_expire = timedelta(
    hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_HOURS', 24))
)
self.refresh_token_expire = timedelta(
    days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', 30))
)
```

## Testing

### Run Authentication Tests

```bash
# Run the test script
python test_jwt_auth.py

# Expected output:
# ✅ Registration successful
# ✅ Login successful
# ✅ Authentication successful
# ✅ Token refresh successful
# ✅ API key created successfully
# ✅ Successfully accessed protected endpoint
# ✅ Logout successful
# ✅ Token correctly invalidated
```

### Manual Testing with cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser","password":"testpass123"}'

# Use token
curl -X GET http://localhost:8000/api/transcription/list \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Security Best Practices

1. **Token Storage**
   - Store tokens in secure HTTP-only cookies or secure storage
   - Never store tokens in localStorage for production
   - Clear tokens on logout

2. **Password Requirements**
   - Minimum 6 characters (configurable)
   - Consider adding complexity requirements
   - Implement password history

3. **Session Management**
   - Track active sessions per user
   - Allow users to view/revoke sessions
   - Implement session timeout

4. **API Key Security**
   - Only show full API key once on creation
   - Store only hashed versions
   - Implement key rotation

5. **Rate Limiting**
   - Implement per-user rate limits
   - Different limits for different roles
   - Track and alert on suspicious activity

## Troubleshooting

### Common Issues

1. **"Invalid token" errors**
   - Check token expiry
   - Verify JWT_SECRET_KEY is consistent
   - Ensure Bearer prefix in Authorization header

2. **"User not found" errors**
   - Verify database connection
   - Check user exists and is active
   - Ensure session is not expired

3. **CORS errors**
   - Configure CORS middleware properly
   - Add frontend domain to allowed origins
   - Check preflight request handling

### Debug Mode

Enable debug logging:

```python
# In api/auth_service.py
logger.setLevel(logging.DEBUG)

# View detailed token validation
logger.debug(f"Token payload: {payload}")
logger.debug(f"Session found: {session}")
```

## Migration from Previous Auth

If migrating from file-based authentication:

1. Export existing users
2. Hash passwords with bcrypt
3. Import into PostgreSQL
4. Generate sessions for active users
5. Notify users of required re-login

## Future Enhancements

- [ ] OAuth2/OIDC support
- [ ] Multi-factor authentication
- [ ] Biometric authentication
- [ ] Single Sign-On (SSO)
- [ ] Password reset flow
- [ ] Email verification
- [ ] Account lockout policies
- [ ] Audit trail improvements