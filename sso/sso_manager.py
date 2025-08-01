"""
SSO management system for enterprise authentication
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import jwt
import secrets

logger = logging.getLogger(__name__)


class SSOProviderType(Enum):
    """Types of SSO providers"""
    OAUTH2 = "oauth2"
    SAML = "saml"
    OIDC = "oidc"
    LDAP = "ldap"


@dataclass
class SSOUser:
    """SSO user information"""
    id: str
    email: str
    name: str
    username: Optional[str] = None
    groups: List[str] = None
    attributes: Dict[str, Any] = None
    provider: Optional[str] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.attributes is None:
            self.attributes = {}


@dataclass
class SSOSession:
    """SSO session information"""
    session_id: str
    user: SSOUser
    provider: str
    created_at: datetime
    expires_at: datetime
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at


class SSOProvider(ABC):
    """Abstract base class for SSO providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_id = config.get('provider_id')
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    def get_provider_type(self) -> SSOProviderType:
        """Get the provider type"""
        pass
    
    @abstractmethod
    async def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Get authorization URL for user login"""
        pass
    
    @abstractmethod
    async def handle_callback(
        self,
        code: str,
        state: str,
        redirect_uri: str
    ) -> SSOUser:
        """Handle authentication callback"""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> SSOUser:
        """Get user information from access token"""
        pass
    
    @abstractmethod
    async def logout(self, session: SSOSession) -> bool:
        """Logout user from SSO provider"""
        pass


class SSOManager:
    """Manages SSO providers and sessions"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.providers: Dict[str, SSOProvider] = {}
        self.sessions: Dict[str, SSOSession] = {}
        self.pending_states: Dict[str, Dict[str, Any]] = {}
        
        logger.info("SSO manager initialized")
    
    def add_provider(self, provider_id: str, provider: SSOProvider):
        """Add an SSO provider"""
        self.providers[provider_id] = provider
        logger.info(f"Added SSO provider: {provider_id}")
    
    def remove_provider(self, provider_id: str):
        """Remove an SSO provider"""
        if provider_id in self.providers:
            del self.providers[provider_id]
            logger.info(f"Removed SSO provider: {provider_id}")
    
    def get_provider(self, provider_id: str) -> Optional[SSOProvider]:
        """Get an SSO provider"""
        return self.providers.get(provider_id)
    
    def list_providers(self, enabled_only: bool = True) -> List[tuple[str, SSOProvider]]:
        """List SSO providers"""
        providers = []
        for provider_id, provider in self.providers.items():
            if not enabled_only or provider.enabled:
                providers.append((provider_id, provider))
        return providers
    
    async def initiate_login(
        self,
        provider_id: str,
        redirect_uri: str,
        user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Initiate SSO login process"""
        
        provider = self.providers.get(provider_id)
        if not provider:
            raise ValueError(f"SSO provider not found: {provider_id}")
        
        if not provider.enabled:
            raise ValueError(f"SSO provider disabled: {provider_id}")
        
        # Generate state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state information
        self.pending_states[state] = {
            'provider_id': provider_id,
            'redirect_uri': redirect_uri,
            'user_data': user_data or {},
            'created_at': datetime.utcnow()
        }
        
        # Get authorization URL
        auth_url = await provider.get_authorization_url(state, redirect_uri)
        
        logger.info(f"Initiated SSO login for provider {provider_id}")
        return auth_url
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        redirect_uri: str
    ) -> SSOSession:
        """Handle SSO callback"""
        
        # Validate state
        state_info = self.pending_states.get(state)
        if not state_info:
            raise ValueError("Invalid or expired state parameter")
        
        # Check state expiration (5 minutes)
        if datetime.utcnow() - state_info['created_at'] > timedelta(minutes=5):
            del self.pending_states[state]
            raise ValueError("State parameter expired")
        
        provider_id = state_info['provider_id']
        provider = self.providers.get(provider_id)
        if not provider:
            raise ValueError(f"SSO provider not found: {provider_id}")
        
        try:
            # Handle callback with provider
            user = await provider.handle_callback(code, state, redirect_uri)
            
            # Create session
            session = self.create_session(user, provider_id)
            
            # Clean up state
            del self.pending_states[state]
            
            logger.info(f"SSO login successful for user {user.email} via {provider_id}")
            return session
            
        except Exception as e:
            # Clean up state on error
            if state in self.pending_states:
                del self.pending_states[state]
            logger.error(f"SSO callback error for provider {provider_id}: {e}")
            raise
    
    def create_session(
        self,
        user: SSOUser,
        provider_id: str,
        duration_hours: int = 24
    ) -> SSOSession:
        """Create an SSO session"""
        
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        session = SSOSession(
            session_id=session_id,
            user=user,
            provider=provider_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"Created SSO session for user {user.email}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SSOSession]:
        """Get an SSO session"""
        session = self.sessions.get(session_id)
        
        if session and session.is_expired():
            # Remove expired session
            del self.sessions[session_id]
            return None
        
        return session
    
    def validate_session(self, session_id: str) -> bool:
        """Validate an SSO session"""
        session = self.get_session(session_id)
        return session is not None
    
    async def refresh_session(self, session_id: str) -> Optional[SSOSession]:
        """Refresh an SSO session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        provider = self.providers.get(session.provider)
        if not provider:
            return None
        
        try:
            if session.refresh_token:
                # Try to refresh token
                token_data = await provider.refresh_token(session.refresh_token)
                session.access_token = token_data.get('access_token')
                session.refresh_token = token_data.get('refresh_token', session.refresh_token)
                session.expires_at = datetime.utcnow() + timedelta(
                    seconds=token_data.get('expires_in', 3600)
                )
                
                logger.info(f"Refreshed SSO session for user {session.user.email}")
                return session
            else:
                # No refresh token, session cannot be refreshed
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing SSO session: {e}")
            return None
    
    async def logout(self, session_id: str) -> bool:
        """Logout from SSO session"""
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        provider = self.providers.get(session.provider)
        if provider:
            try:
                await provider.logout(session)
            except Exception as e:
                logger.warning(f"Error during SSO logout: {e}")
        
        # Remove session
        del self.sessions[session_id]
        
        logger.info(f"Logged out SSO session for user {session.user.email}")
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired SSO sessions")
    
    def cleanup_expired_states(self):
        """Clean up expired pending states"""
        expired_states = [
            state for state, info in self.pending_states.items()
            if datetime.utcnow() - info['created_at'] > timedelta(minutes=5)
        ]
        
        for state in expired_states:
            del self.pending_states[state]
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired pending states")
    
    def generate_jwt_token(self, user: SSOUser, expires_in: int = 3600) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'groups': user.groups,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SSO system statistics"""
        active_sessions = len([s for s in self.sessions.values() if not s.is_expired()])
        
        provider_stats = {}
        for provider_id, provider in self.providers.items():
            provider_stats[provider_id] = {
                'type': provider.get_provider_type().value,
                'enabled': provider.enabled
            }
        
        return {
            'total_providers': len(self.providers),
            'enabled_providers': len([p for p in self.providers.values() if p.enabled]),
            'active_sessions': active_sessions,
            'total_sessions': len(self.sessions),
            'pending_states': len(self.pending_states),
            'providers': provider_stats
        }


# Global SSO manager instance (initialized with app secret key)
sso_manager = None

def initialize_sso_manager(secret_key: str) -> SSOManager:
    """Initialize global SSO manager"""
    global sso_manager
    sso_manager = SSOManager(secret_key)
    return sso_manager