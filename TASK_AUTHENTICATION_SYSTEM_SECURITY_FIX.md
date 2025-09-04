# Task: Authentication System Security Fix

## Task Overview
Fix critical security vulnerabilities in the authentication system where mock implementations bypass real security checks.

## Intent Analysis
- **Problem**: Mock authentication implementations allow unauthorized access to protected endpoints
- **User Impact**: Critical - Complete bypass of all security controls
- **Business Impact**: Critical - Security breach risk, non-compliance with security standards
- **Technical Effort**: Low-Medium - Replacing mock implementations with real auth
- **Strategic Importance**: Critical - Foundation for all other security features

## Subtasks

### 1. Fix Mock Authentication in `api/api_main.py`
**File**: `/Users/pranay/Projects/LLM/video/ner/api/api_main.py`
**Issue**: Local mock implementation of `get_current_user()` that always returns same user data
**Current Code**:
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> Dict[str, Any]:
    """Get current user from authentication credentials"""
    # In a real implementation, this would:
    # 1. Validate the token/API key
    # 2. Retrieve user information from database
    # 3. Return user details
    
    return {
        "user_id": "user_123",
        "username": "test_user",
        "email": "test@example.com",
        "role": "user"
    }
```

**Requirements**:
- Remove mock implementation
- Import real authentication from `api.auth`
- Ensure all endpoints use real authentication
- Update endpoint dependencies from `Dict[str, Any]` to proper `User` model

### 2. Fix Mock Authentication Wrappers in `api/dependencies.py`
**File**: `/Users/pranay/Projects/LLM/video/ner/api/dependencies.py`
**Issue**: Mock implementations of `get_current_active_user` and `get_admin_user`
**Current Code**:
```python
def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get current admin user"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

**Requirements**:
- Remove mock implementations
- Import real authentication functions from `api.auth`
- Use proper `User` model instead of `Dict[str, Any]`
- Ensure correct dependency chaining

### 3. Update Affected Endpoints
**Files**: 
- `/Users/pranay/Projects/LLM/video/ner/api/api_main.py` (multiple endpoints)
**Issue**: Endpoints using mock authentication dependencies
**Affected Endpoints**:
- POST `/upload` (line 282)
- POST `/batch-upload` (line 332)
- POST `/batch-process` (line 376)
- GET `/download/{file_id}` (line 418)

**Requirements**:
- Update dependency from `current_user: dict = Depends(get_current_user)` to proper auth
- Ensure correct parameter types (`User` model instead of `dict`)
- Verify all authentication checks work correctly

## Acceptance Criteria
1. All endpoints reject unauthenticated requests with 401 Unauthorized
2. Inactive users receive 403 Forbidden
3. Admin-only endpoints reject non-admin users with 403 Forbidden
4. Valid authenticated requests work correctly
5. No mock implementations remain in authentication flow
6. All existing tests pass or are updated appropriately

## Implementation Notes
- Reference `api/endpoints/upload.py` for correct authentication implementation pattern
- Ensure backward compatibility where possible
- Add comprehensive test coverage for authentication scenarios
- Document any breaking changes in API behavior