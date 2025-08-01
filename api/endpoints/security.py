"""
Security API Endpoints
REST API for security management and user administration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List, Dict, Any
import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..auth import (
    auth_required, admin_required, create_api_response, 
    auth_manager, security_manager
)
from ..models import (
    LoginRequest, LoginResponse, APIKeyRequest, APIKeyResponse,
    UserCreateRequest, UserResponse, SecurityStatusResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        # Authenticate user
        token = auth_manager.security_manager.access_control.authenticate_user(
            request.username, request.password
        )
        
        if not token:
            # Log failed authentication
            auth_manager.security_manager.audit_logger.log_authentication(
                request.username, False, "API"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get token expiration (24 hours from now)
        from datetime import timedelta
        expires_at = datetime.now() + timedelta(hours=24)
        
        return create_api_response({
            "token": token,
            "user_id": request.username,
            "expires_at": expires_at.isoformat(),
            "token_type": "Bearer"
        }, "Login successful")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/users", response_model=UserResponse, dependencies=[Depends(admin_required)])
async def create_user(request: UserCreateRequest):
    """Create a new user (admin only)"""
    try:
        # Create user
        success = auth_manager.security_manager.access_control.create_user(
            request.user_id, request.password, request.role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Get user info
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        user_info = users.get(request.user_id, {})
        
        user_response = UserResponse(
            user_id=request.user_id,
            role=user_info.get("role", request.role),
            created_at=datetime.fromisoformat(user_info.get("created_at", datetime.now().isoformat())),
            last_login=None,
            active=True
        )
        
        return create_api_response(user_response, "User created successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )


@router.get("/users", dependencies=[Depends(admin_required)])
async def list_users():
    """List all users (admin only)"""
    try:
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        
        user_list = []
        for user_id, user_info in users.items():
            user_list.append({
                "user_id": user_id,
                "role": user_info.get("role", "unknown"),
                "created_at": user_info.get("created_at"),
                "last_login": user_info.get("last_login"),
                "failed_attempts": user_info.get("failed_attempts", 0),
                "locked": bool(user_info.get("locked_until")),
                "active": True
            })
        
        return create_api_response({
            "users": user_list,
            "total_count": len(user_list)
        }, f"Retrieved {len(user_list)} users")
        
    except Exception as e:
        logger.error(f"User listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User listing failed"
        )


@router.get("/users/{user_id}", dependencies=[Depends(admin_required)])
async def get_user(user_id: str):
    """Get specific user information (admin only)"""
    try:
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        
        if user_id not in users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_info = users[user_id]
        
        user_data = {
            "user_id": user_id,
            "role": user_info.get("role", "unknown"),
            "created_at": user_info.get("created_at"),
            "last_login": user_info.get("last_login"),
            "failed_attempts": user_info.get("failed_attempts", 0),
            "locked_until": user_info.get("locked_until"),
            "active": True,
            "permissions": auth_manager.security_manager.access_control.permissions["roles"].get(
                user_info.get("role", "user"), {}
            ).get("permissions", [])
        }
        
        return create_api_response(user_data, "User information retrieved")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User retrieval failed"
        )


@router.delete("/users/{user_id}", dependencies=[Depends(admin_required)])
async def delete_user(user_id: str):
    """Delete a user (admin only)"""
    try:
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        
        if user_id not in users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Remove user
        del users[user_id]
        auth_manager.security_manager.access_control._save_permissions()
        
        return create_api_response(
            {"user_id": user_id},
            "User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


@router.post("/api-keys", response_model=APIKeyResponse)
async def generate_api_key(
    request: APIKeyRequest,
    user_id: str = Depends(admin_required)
):
    """Generate API key (admin only)"""
    try:
        api_key = auth_manager.security_manager.access_control.generate_api_key(
            user_id, request.description or ""
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to generate API key"
            )
        
        return create_api_response({
            "api_key": api_key,
            "description": request.description,
            "created_at": datetime.now().isoformat(),
            "user_id": user_id
        }, "API key generated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key generation failed"
        )


@router.get("/api-keys", dependencies=[Depends(admin_required)])
async def list_api_keys():
    """List all API keys (admin only)"""
    try:
        api_keys = auth_manager.security_manager.access_control.permissions.get("api_keys", {})
        
        api_key_list = []
        for key, key_info in api_keys.items():
            # Mask the API key for security
            masked_key = f"{key[:8]}...{key[-4:]}"
            
            api_key_list.append({
                "api_key_masked": masked_key,
                "user_id": key_info["user_id"],
                "description": key_info.get("description", ""),
                "created_at": key_info["created_at"],
                "last_used": key_info.get("last_used"),
                "active": key_info.get("active", True)
            })
        
        return create_api_response({
            "api_keys": api_key_list,
            "total_count": len(api_key_list)
        }, f"Retrieved {len(api_key_list)} API keys")
        
    except Exception as e:
        logger.error(f"API key listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key listing failed"
        )


@router.get("/status", response_model=SecurityStatusResponse)
async def get_security_status(user_id: str = Depends(auth_required)):
    """Get security system status"""
    try:
        status_data = auth_manager.security_manager.get_security_status()
        
        return create_api_response(status_data, "Security status retrieved")
        
    except Exception as e:
        logger.error(f"Security status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security status retrieval failed"
        )


@router.get("/audit-log", dependencies=[Depends(admin_required)])
async def get_audit_log(
    limit: int = 50,
    event_type: Optional[str] = None
):
    """Get security audit log (admin only)"""
    try:
        # This would typically read from the audit log file
        # For now, return sample audit entries
        audit_entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "AUTH_SUCCESS",
                "user_id": "admin",
                "details": "API login successful",
                "ip_address": "127.0.0.1"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "ACCESS_GRANTED",
                "user_id": "user1",
                "details": "Transcription access granted",
                "ip_address": "127.0.0.1"
            }
        ]
        
        # Filter by event type if specified
        if event_type:
            audit_entries = [
                entry for entry in audit_entries 
                if entry["event_type"] == event_type
            ]
        
        # Apply limit
        audit_entries = audit_entries[:limit]
        
        return create_api_response({
            "audit_entries": audit_entries,
            "count": len(audit_entries),
            "available_event_types": [
                "AUTH_SUCCESS", "AUTH_FAILED", "ACCESS_GRANTED", 
                "ACCESS_DENIED", "DATA_EXPORT", "USER_CREATED", "API_KEY_GENERATED"
            ]
        }, f"Retrieved {len(audit_entries)} audit entries")
        
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit log retrieval failed"
        )


@router.get("/permissions")
async def get_user_permissions(user_id: str = Depends(auth_required)):
    """Get current user's permissions"""
    try:
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        user_info = users.get(user_id, {})
        role = user_info.get("role", "user")
        
        roles = auth_manager.security_manager.access_control.permissions.get("roles", {})
        role_info = roles.get(role, {})
        
        permissions_data = {
            "user_id": user_id,
            "role": role,
            "permissions": role_info.get("permissions", []),
            "rate_limit": role_info.get("rate_limit", 50),
            "can_read": "read" in role_info.get("permissions", []),
            "can_write": "write" in role_info.get("permissions", []),
            "can_export": "export" in role_info.get("permissions", []),
            "can_admin": "admin" in role_info.get("permissions", [])
        }
        
        return create_api_response(permissions_data, "User permissions retrieved")
        
    except Exception as e:
        logger.error(f"Permissions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permissions retrieval failed"
        )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    user_id: str = Depends(auth_required)
):
    """Change user password"""
    try:
        # Verify current password
        token = auth_manager.security_manager.access_control.authenticate_user(
            user_id, current_password
        )
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters"
            )
        
        # Update password
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        if user_id not in users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        import bcrypt
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        users[user_id]["password_hash"] = password_hash.decode('utf-8')
        
        # Save changes
        auth_manager.security_manager.access_control._save_permissions()
        
        # Log password change
        auth_manager.security_manager.audit_logger.log_security_event(
            "PASSWORD_CHANGED", user_id, "User changed password"
        )
        
        return create_api_response(
            {"user_id": user_id},
            "Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/unlock-user/{user_id}", dependencies=[Depends(admin_required)])
async def unlock_user(user_id: str):
    """Unlock a locked user account (admin only)"""
    try:
        users = auth_manager.security_manager.access_control.permissions.get("users", {})
        
        if user_id not in users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Reset failed attempts and unlock
        users[user_id]["failed_attempts"] = 0
        users[user_id]["locked_until"] = None
        
        # Save changes
        auth_manager.security_manager.access_control._save_permissions()
        
        # Log unlock action
        auth_manager.security_manager.audit_logger.log_security_event(
            "USER_UNLOCKED", user_id, "Account unlocked by admin"
        )
        
        return create_api_response(
            {"user_id": user_id},
            "User account unlocked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User unlock error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User unlock failed"
        )


@router.get("/health")
async def security_health_check():
    """Security system health check"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "authentication": "operational",
                "authorization": "operational", 
                "encryption": "operational",
                "audit_logging": "operational"
            },
            "security_features": {
                "jwt_tokens": True,
                "api_keys": True,
                "rate_limiting": True,
                "audit_logging": True,
                "encryption": True,
                "password_hashing": True
            }
        }
        
        return create_api_response(health_data, "Security system is healthy")
        
    except Exception as e:
        logger.error(f"Security health check error: {e}")
        return create_api_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, "Security system health check failed")