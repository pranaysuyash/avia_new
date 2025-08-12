"""
Single Sign-On (SSO) Integration
Supports Google, Microsoft, OKTA, and SAML providers
"""

import os
import secrets
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from api.database import User, UserRole
from .enhanced_auth import auth_service, SSOProvider

# SSO Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
OKTA_DOMAIN = os.getenv("OKTA_DOMAIN")
OKTA_CLIENT_ID = os.getenv("OKTA_CLIENT_ID")
OKTA_CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")

# Base URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MICROSOFT_USER_INFO_URL = "https://graph.microsoft.com/v1.0/me"

class SSOUserInfo(BaseModel):
    """SSO user information"""
    email: EmailStr
    name: str
    provider: SSOProvider
    provider_id: str
    avatar_url: Optional[str] = None
    verified: bool = True

class SSOState(BaseModel):
    """SSO state for OAuth flow"""
    provider: SSOProvider
    redirect_uri: str
    state: str
    created_at: datetime

class SSOService:
    """SSO integration service"""
    
    def __init__(self):
        self.states = {}  # In production, use Redis
    
    def generate_state(self, provider: SSOProvider, redirect_uri: str) -> str:
        """Generate and store OAuth state"""
        state = secrets.token_urlsafe(32)
        
        self.states[state] = SSOState(
            provider=provider,
            redirect_uri=redirect_uri,
            state=state,
            created_at=datetime.utcnow()
        )
        
        return state
    
    def validate_state(self, state: str) -> Optional[SSOState]:
        """Validate OAuth state"""
        sso_state = self.states.get(state)
        if not sso_state:
            return None
        
        # Check if state is expired (5 minutes)
        if datetime.utcnow() - sso_state.created_at > timedelta(minutes=5):
            del self.states[state]
            return None
        
        return sso_state
    
    def get_authorization_url(
        self, 
        provider: SSOProvider, 
        redirect_uri: str,
        scopes: Optional[List[str]] = None
    ) -> str:
        """Get OAuth authorization URL"""
        
        state = self.generate_state(provider, redirect_uri)
        
        if provider == SSOProvider.GOOGLE:
            params = {
                "client_id": GOOGLE_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes or ["openid", "email", "profile"]),
                "response_type": "code",
                "state": state,
                "access_type": "offline",
                "prompt": "consent"
            }
            return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        
        elif provider == SSOProvider.MICROSOFT:
            params = {
                "client_id": MICROSOFT_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes or ["openid", "email", "profile"]),
                "response_type": "code",
                "state": state,
                "response_mode": "query"
            }
            return f"{MICROSOFT_AUTH_URL}?{urlencode(params)}"
        
        elif provider == SSOProvider.OKTA:
            params = {
                "client_id": OKTA_CLIENT_ID,
                "redirect_uri": redirect_uri,
                "scope": " ".join(scopes or ["openid", "email", "profile"]),
                "response_type": "code",
                "state": state
            }
            return f"https://{OKTA_DOMAIN}/oauth2/v1/authorize?{urlencode(params)}"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO provider {provider} not supported"
            )
    
    async def exchange_code_for_token(
        self, 
        provider: SSOProvider, 
        code: str, 
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        
        async with httpx.AsyncClient() as client:
            if provider == SSOProvider.GOOGLE:
                data = {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
                
                response = await client.post(GOOGLE_TOKEN_URL, data=data)
                
            elif provider == SSOProvider.MICROSOFT:
                data = {
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
                
                response = await client.post(MICROSOFT_TOKEN_URL, data=data)
                
            elif provider == SSOProvider.OKTA:
                data = {
                    "client_id": OKTA_CLIENT_ID,
                    "client_secret": OKTA_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
                
                response = await client.post(
                    f"https://{OKTA_DOMAIN}/oauth2/v1/token",
                    data=data
                )
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SSO provider {provider} not supported"
                )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    async def get_user_info(
        self, 
        provider: SSOProvider, 
        access_token: str
    ) -> SSOUserInfo:
        """Get user information from SSO provider"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            if provider == SSOProvider.GOOGLE:
                response = await client.get(GOOGLE_USER_INFO_URL, headers=headers)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to get user info from Google"
                    )
                
                data = response.json()
                return SSOUserInfo(
                    email=data["email"],
                    name=data["name"],
                    provider=SSOProvider.GOOGLE,
                    provider_id=data["id"],
                    avatar_url=data.get("picture"),
                    verified=data.get("verified_email", True)
                )
            
            elif provider == SSOProvider.MICROSOFT:
                response = await client.get(MICROSOFT_USER_INFO_URL, headers=headers)
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to get user info from Microsoft"
                    )
                
                data = response.json()
                return SSOUserInfo(
                    email=data["mail"] or data["userPrincipalName"],
                    name=data["displayName"],
                    provider=SSOProvider.MICROSOFT,
                    provider_id=data["id"],
                    verified=True
                )
            
            elif provider == SSOProvider.OKTA:
                response = await client.get(
                    f"https://{OKTA_DOMAIN}/oauth2/v1/userinfo",
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to get user info from Okta"
                    )
                
                data = response.json()
                return SSOUserInfo(
                    email=data["email"],
                    name=data["name"],
                    provider=SSOProvider.OKTA,
                    provider_id=data["sub"],
                    verified=data.get("email_verified", True)
                )
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SSO provider {provider} not supported"
                )
    
    def find_or_create_user(
        self, 
        db: Session, 
        sso_user: SSOUserInfo
    ) -> User:
        """Find existing user or create new one from SSO info"""
        
        # Try to find existing user by email
        user = db.query(User).filter(User.email == sso_user.email).first()
        
        if user:
            # Update user info if needed
            if not user.full_name and sso_user.name:
                user.full_name = sso_user.name
            
            if not user.is_verified and sso_user.verified:
                user.is_verified = True
            
            user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            return user
        
        # Create new user
        username = sso_user.email.split("@")[0]
        
        # Ensure username is unique
        counter = 1
        original_username = username
        while db.query(User).filter(User.username == username).first():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User(
            email=sso_user.email,
            username=username,
            password_hash="",  # No password for SSO users
            full_name=sso_user.name,
            role=UserRole.USER,
            is_active=True,
            is_verified=sso_user.verified
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    async def authenticate_with_sso(
        self,
        db: Session,
        provider: SSOProvider,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Complete SSO authentication flow"""
        
        # Validate state
        sso_state = self.validate_state(state)
        if not sso_state or sso_state.provider != provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state"
            )
        
        # Exchange code for token
        token_data = await self.exchange_code_for_token(provider, code, redirect_uri)
        access_token = token_data["access_token"]
        
        # Get user info
        sso_user = await self.get_user_info(provider, access_token)
        
        # Find or create user
        user = self.find_or_create_user(db, sso_user)
        
        # Clean up state
        del self.states[state]
        
        return {
            "user": user,
            "sso_user": sso_user,
            "token_data": token_data
        }

# Global SSO service instance
sso_service = SSOService()