#!/usr/bin/env python3
"""
API Models
Database models for API keys and developer platform
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets
import hashlib
import enum

from database.base import Base

class APIKeyStatus(str, enum.Enum):
    """API key status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"

class APIKeyScope(str, enum.Enum):
    """API key scopes/permissions"""
    TRANSCRIPTS_READ = "transcripts:read"
    TRANSCRIPTS_WRITE = "transcripts:write"
    TRANSCRIPTS_DELETE = "transcripts:delete"
    ANALYTICS_READ = "analytics:read"
    TEAMS_READ = "teams:read"
    TEAMS_WRITE = "teams:write"
    WEBHOOKS_WRITE = "webhooks:write"
    ACCOUNT_READ = "account:read"

class WebhookStatus(str, enum.Enum):
    """Webhook status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"

class APIKey(Base):
    """API key for developer access"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    key_hash = Column(String(255), unique=True, nullable=False)  # SHA256 hash of full key
    description = Column(Text)
    scopes = Column(JSON, default=list)  # List of APIKeyScope values
    status = Column(Enum(APIKeyStatus), default=APIKeyStatus.ACTIVE)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    rate_limit_per_day = Column(Integer, default=10000)
    
    # IP restrictions
    allowed_ips = Column(JSON, default=list)  # Empty = all IPs allowed
    allowed_origins = Column(JSON, default=list)  # CORS origins
    
    # Metadata
    last_used_at = Column(DateTime)
    last_used_ip = Column(String(45))
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime)  # Optional expiration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    usage_logs = relationship("APIKeyUsage", back_populates="api_key", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="api_key", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_key_user', 'user_id'),
        Index('idx_api_key_prefix', 'key_prefix'),
        Index('idx_api_key_status', 'status'),
    )
    
    @staticmethod
    def generate_key() -> tuple[str, str]:
        """Generate a new API key
        Returns: (full_key, key_hash)
        """
        # Generate 32 bytes of random data
        raw_key = secrets.token_bytes(32)
        
        # Create the key in format: sk_live_<base64>
        import base64
        key_suffix = base64.urlsafe_b64encode(raw_key).decode('utf-8').rstrip('=')
        full_key = f"sk_live_{key_suffix}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, key_hash
    
    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for comparison"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def has_scope(self, scope: str) -> bool:
        """Check if API key has a specific scope"""
        return scope in self.scopes
    
    def is_valid(self) -> bool:
        """Check if API key is valid"""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True

class APIKeyUsage(Base):
    """API key usage tracking"""
    __tablename__ = 'api_key_usage'
    
    id = Column(Integer, primary_key=True)
    api_key_id = Column(Integer, ForeignKey('api_keys.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100))
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_usage_key_time', 'api_key_id', 'timestamp'),
        Index('idx_api_usage_endpoint', 'endpoint'),
    )

class Webhook(Base):
    """Webhook configuration"""
    __tablename__ = 'webhooks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    api_key_id = Column(Integer, ForeignKey('api_keys.id'))
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))  # For signature verification
    events = Column(JSON, default=list)  # List of event types
    status = Column(Enum(WebhookStatus), default=WebhookStatus.ACTIVE)
    
    # Retry configuration
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    timeout_seconds = Column(Integer, default=30)
    
    # Headers to include
    custom_headers = Column(JSON, default=dict)
    
    # Statistics
    last_triggered_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_failure_at = Column(DateTime)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="webhooks")
    api_key = relationship("APIKey", back_populates="webhooks")
    logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_user', 'user_id'),
        Index('idx_webhook_status', 'status'),
    )
    
    @staticmethod
    def generate_secret() -> str:
        """Generate webhook secret for signature verification"""
        return secrets.token_urlsafe(32)
    
    def compute_signature(self, payload: str) -> str:
        """Compute HMAC signature for payload"""
        import hmac
        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

class WebhookLog(Base):
    """Webhook delivery logs"""
    __tablename__ = 'webhook_logs'
    
    id = Column(Integer, primary_key=True)
    webhook_id = Column(Integer, ForeignKey('webhooks.id'), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_id = Column(String(100))
    payload = Column(JSON)
    
    # Delivery info
    attempt_number = Column(Integer, default=1)
    status_code = Column(Integer)
    response_body = Column(Text)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    delivered_at = Column(DateTime, default=datetime.utcnow)
    next_retry_at = Column(DateTime)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_log_webhook', 'webhook_id'),
        Index('idx_webhook_log_time', 'delivered_at'),
        Index('idx_webhook_log_event', 'event_type'),
    )

class DeveloperApp(Base):
    """OAuth2 applications for third-party integrations"""
    __tablename__ = 'developer_apps'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # OAuth2 credentials
    client_id = Column(String(255), unique=True, nullable=False)
    client_secret_hash = Column(String(255), nullable=False)
    
    # OAuth2 configuration
    redirect_uris = Column(JSON, default=list)
    allowed_scopes = Column(JSON, default=list)
    grant_types = Column(JSON, default=lambda: ['authorization_code', 'refresh_token'])
    
    # App info
    website_url = Column(String(500))
    privacy_policy_url = Column(String(500))
    terms_url = Column(String(500))
    logo_url = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="developer_apps")
    
    @staticmethod
    def generate_client_credentials() -> tuple[str, str]:
        """Generate client ID and secret"""
        client_id = f"app_{secrets.token_urlsafe(32)}"
        client_secret = secrets.token_urlsafe(48)
        client_secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
        
        return client_id, client_secret, client_secret_hash