"""
Authentication API Endpoints
Handles user authentication, registration, and API key management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
import os
import sys
import logging
from datetime import datetime, timedelta
import secrets

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import (
    APIAuthManager, api_key_required, jwt_required,
    auth_required, admin_required, create_api_response
)
from api.models import (
    LoginRequest, LoginResponse, APIKeyRequest, APIKeyResponse,
    UserCreateRequest, UserResponse
)

# Create auth manager instance
auth_manager = APIAuthManager()
from security_manager import SecurityManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security setup
security = HTTPBasic()
security_manager = SecurityManager()


@router.post("/register", response_model=UserResponse)
async def register_user(
    request: UserCreateRequest,
    current_user: str = Depends(admin_required)
):
    """Register a new user (Admin only)"""
    try:
        # Check if user already exists
        if security_manager.access_control.get_user_role(request.user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create user
        success = security_manager.access_control.create_user(
            request.user_id,
            request.password,
            request.role
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Log user creation
        security_manager.audit_logger.log_system_event(
            "user_created",
            f"User {request.user_id} created by {current_user}",
            {"created_by": current_user, "new_user": request.user_id, "role": request.role}
        )
        
        return UserResponse(
            user_id=request.user_id,
            role=request.role,
            created_at=datetime.now(),
            last_login=None,
            active=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and get JWT token"""
    try:
        # Authenticate user
        if not security_manager.access_control.authenticate_user(
            request.username, request.password
        ):
            # Log failed authentication
            security_manager.audit_logger.log_authentication(
                request.username, False, "API"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # Generate JWT token
        token = security_manager.access_control.generate_token(request.username)
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate authentication token"
            )
        
        # Log successful authentication
        security_manager.audit_logger.log_authentication(
            request.username, True, "API"
        )
        
        # Calculate expiration
        expires_at = datetime.now() + timedelta(hours=24)
        
        return create_api_response(
            LoginResponse(
                success=True,
                message="Login successful",
                token=token,
                user_id=request.username,
                expires_at=expires_at
            ),
            "Authentication successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(current_user: str = Depends(auth_required)):
    """Logout current user"""
    try:
        # In a production system, you would invalidate the token here
        # For now, we'll just log the logout
        security_manager.audit_logger.log_authentication(
            current_user, True, "API_LOGOUT"
        )
        
        return create_api_response(
            {"user_id": current_user},
            "Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/api-key", response_model=APIKeyResponse)
async def generate_api_key(
    request: APIKeyRequest,
    current_user: str = Depends(auth_required)
):
    """Generate a new API key for the current user"""
    try:
        # Generate API key
        api_key = security_manager.access_control.generate_api_key(
            current_user,
            description=request.description
        )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate API key"
            )
        
        # Log API key generation
        security_manager.audit_logger.log_system_event(
            "api_key_generated",
            f"API key generated for user {current_user}",
            {"user_id": current_user, "description": request.description}
        )
        
        return create_api_response(
            APIKeyResponse(
                success=True,
                message="API key generated successfully",
                api_key=api_key,
                description=request.description,
                created_at=datetime.now()
            ),
            "API key generated successfully. Store it securely as it won't be shown again."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key generation failed"
        )


@router.get("/api-keys")
async def list_api_keys(current_user: str = Depends(auth_required)):
    """List user's API keys (without the actual keys)"""
    try:
        # Get user's API keys
        user_keys = []
        
        # In production, this would query from database
        # For now, we'll return a placeholder response
        api_keys_info = security_manager.access_control.get_user_api_keys(current_user)
        
        return create_api_response({
            "api_keys": api_keys_info,
            "count": len(api_keys_info)
        }, "API keys retrieved")
        
    except Exception as e:
        logger.error(f"API key listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API keys"
        )


@router.delete("/api-key/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: str = Depends(auth_required)
):
    """Revoke an API key"""
    try:
        # Revoke API key
        success = security_manager.access_control.revoke_api_key(key_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found or not owned by user"
            )
        
        # Log API key revocation
        security_manager.audit_logger.log_system_event(
            "api_key_revoked",
            f"API key {key_id} revoked by user {current_user}",
            {"user_id": current_user, "key_id": key_id}
        )
        
        return create_api_response(
            {"key_id": key_id},
            "API key revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key revocation failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: str = Depends(auth_required)):
    """Get current user information"""
    try:
        # Get user info
        role = security_manager.access_control.get_user_role(current_user)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get last login from audit logs
        last_login = security_manager.audit_logger.get_last_login(current_user)
        
        return UserResponse(
            user_id=current_user,
            role=role,
            created_at=datetime.now() - timedelta(days=30),  # Placeholder
            last_login=last_login,
            active=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User info retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.put("/password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: str = Depends(auth_required)
):
    """Change user password"""
    try:
        # Verify old password
        if not security_manager.access_control.authenticate_user(
            current_user, old_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid current password"
            )
        
        # Update password
        success = security_manager.access_control.update_password(
            current_user, new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password"
            )
        
        # Log password change
        security_manager.audit_logger.log_system_event(
            "password_changed",
            f"Password changed for user {current_user}",
            {"user_id": current_user}
        )
        
        return create_api_response(
            {"user_id": current_user},
            "Password updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/verify")
async def verify_token(current_user: str = Depends(auth_required)):
    """Verify authentication token"""
    try:
        return create_api_response({
            "user_id": current_user,
            "valid": True,
            "timestamp": datetime.now().isoformat()
        }, "Token is valid")
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )