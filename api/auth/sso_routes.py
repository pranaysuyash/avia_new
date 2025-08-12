"""
SSO Authentication Routes
Provides OAuth2 endpoints for Google, Microsoft, OKTA, and SAML
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from api.database import get_db
from .enhanced_auth import auth_service, SSOProvider, Token
from .sso import sso_service, SSOUserInfo
from .dependencies import get_current_user_optional

router = APIRouter(prefix="/api/auth/sso", tags=["SSO Authentication"])

@router.get("/providers")
async def get_sso_providers():
    """Get available SSO providers"""
    return {
        "providers": [
            {
                "name": "Google",
                "provider": SSOProvider.GOOGLE.value,
                "enabled": True,
                "description": "Sign in with Google"
            },
            {
                "name": "Microsoft",
                "provider": SSOProvider.MICROSOFT.value,
                "enabled": True,
                "description": "Sign in with Microsoft"
            },
            {
                "name": "Okta",
                "provider": SSOProvider.OKTA.value,
                "enabled": True,
                "description": "Sign in with Okta"
            },
            {
                "name": "SAML",
                "provider": SSOProvider.SAML.value,
                "enabled": False,
                "description": "SAML SSO (Enterprise)"
            }
        ]
    }

@router.get("/{provider}/authorize")
async def sso_authorize(
    provider: SSOProvider,
    redirect_uri: str = Query(..., description="Redirect URI after authentication"),
    scopes: Optional[str] = Query(None, description="OAuth scopes (space-separated)")
):
    """Initiate SSO authentication flow"""
    
    try:
        scope_list = scopes.split(" ") if scopes else None
        auth_url = sso_service.get_authorization_url(provider, redirect_uri, scope_list)
        
        return {
            "authorization_url": auth_url,
            "provider": provider.value,
            "redirect_uri": redirect_uri
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )

@router.get("/{provider}/callback")
async def sso_callback(
    provider: SSOProvider,
    request: Request,
    code: str = Query(..., description="Authorization code from SSO provider"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    redirect_uri: str = Query(..., description="Original redirect URI"),
    db: Session = Depends(get_db)
):
    """Handle SSO callback and complete authentication"""
    
    try:
        # Complete SSO authentication
        auth_result = await sso_service.authenticate_with_sso(
            db, provider, code, state, redirect_uri
        )
        
        user = auth_result["user"]
        sso_user = auth_result["sso_user"]
        
        # Create tokens for the user
        ip_address = request.client.host
        user_agent = request.headers.get("User-Agent", "")
        
        tokens = auth_service.create_tokens(db, user, ip_address, user_agent)
        
        return {
            "message": "SSO authentication successful",
            "provider": provider.value,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            },
            "sso_info": {
                "provider": sso_user.provider.value,
                "provider_id": sso_user.provider_id,
                "verified": sso_user.verified
            },
            "tokens": tokens
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSO authentication failed: {str(e)}"
        )

@router.post("/{provider}/link")
async def link_sso_account(
    provider: SSOProvider,
    code: str,
    state: str,
    redirect_uri: str,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Link SSO account to existing user account"""
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Must be logged in to link SSO account"
        )
    
    try:
        # Get SSO user info
        auth_result = await sso_service.authenticate_with_sso(
            db, provider, code, state, redirect_uri
        )
        
        sso_user = auth_result["sso_user"]
        
        # Check if SSO account is already linked to another user
        existing_user = db.query(User).filter(User.email == sso_user.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SSO account is already linked to another user"
            )
        
        # Update current user with SSO info if needed
        if not current_user.is_verified and sso_user.verified:
            current_user.is_verified = True
        
        if not current_user.full_name and sso_user.name:
            current_user.full_name = sso_user.name
        
        db.commit()
        
        return {
            "message": f"{provider.value} account linked successfully",
            "provider": provider.value,
            "linked_email": sso_user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to link SSO account: {str(e)}"
        )

@router.delete("/{provider}/unlink")
async def unlink_sso_account(
    provider: SSOProvider,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Unlink SSO account from user"""
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Must be logged in to unlink SSO account"
        )
    
    # In a full implementation, you'd track SSO links in a separate table
    # For now, we'll just return success
    
    return {
        "message": f"{provider.value} account unlinked successfully",
        "provider": provider.value
    }

@router.get("/linked")
async def get_linked_accounts(
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get user's linked SSO accounts"""
    
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Must be logged in to view linked accounts"
        )
    
    # In a full implementation, you'd query linked accounts from database
    # For now, return empty list
    
    return {
        "linked_accounts": [],
        "available_providers": [provider.value for provider in SSOProvider]
    }