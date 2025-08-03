#!/usr/bin/env python3
"""
Developer API Endpoints
Manage API keys, webhooks, and developer resources
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, HttpUrl

from database.connection import get_db
from database.models import User
from database.api_models import APIKeyScope, WebhookStatus
from api.auth_routes_enhanced import get_current_user
from services.api_key_service import APIKeyService
from services.webhook_service import WebhookService
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/developers", tags=["developers"])

# Request/Response Models

class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: List[str] = Field(default_factory=lambda: ["transcripts:read"])
    rate_limits: Optional[Dict[str, int]] = None
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None

class APIKeyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limits: Optional[Dict[str, int]] = None
    allowed_ips: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    description: Optional[str]
    scopes: List[str]
    status: str
    last_used_at: Optional[str]
    usage_count: int
    expires_at: Optional[str]
    created_at: str

class APIKeyCreateResponse(APIKeyResponse):
    key: str  # Full key, only shown once

class WebhookCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    api_key_id: Optional[int] = None
    custom_headers: Optional[Dict[str, str]] = None
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(30, ge=5, le=120)

class WebhookUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    status: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=120)

class WebhookResponse(BaseModel):
    id: int
    name: str
    url: str
    events: List[str]
    status: str
    last_triggered_at: Optional[str]
    success_count: int
    failure_count: int
    created_at: str

# API Key Endpoints

@router.post("/keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    # Check subscription limits
    from services.subscription_service import SubscriptionService
    subscription_service = SubscriptionService(lambda: db)
    
    allowed, message, _ = subscription_service.check_usage_limit(
        user_id=current_user.id,
        usage_type='api_keys',
        amount=1
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=message
        )
    
    # Validate scopes
    valid_scopes = [scope.value for scope in APIKeyScope]
    invalid_scopes = [s for s in request.scopes if s not in valid_scopes]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
        )
    
    # Create API key
    api_key_service = APIKeyService(db)
    
    try:
        result = api_key_service.create_api_key(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            rate_limits=request.rate_limits,
            expires_in_days=request.expires_in_days,
            allowed_ips=request.allowed_ips,
            allowed_origins=request.allowed_origins
        )
        
        # Track usage
        subscription_service.track_usage(
            user_id=current_user.id,
            usage_type='api_keys',
            amount=1,
            resource_id=str(result['id'])
        )
        
        return APIKeyCreateResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )

@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    include_revoked: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's API keys"""
    api_key_service = APIKeyService(db)
    
    keys = api_key_service.list_api_keys(
        user_id=current_user.id,
        include_revoked=include_revoked
    )
    
    return [APIKeyResponse(**key) for key in keys]

@router.get("/keys/{key_id}")
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API key details including usage statistics"""
    api_key_service = APIKeyService(db)
    
    key_data = api_key_service.get_api_key(
        key_id=key_id,
        user_id=current_user.id
    )
    
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return key_data

@router.put("/keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    request: APIKeyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update API key settings"""
    api_key_service = APIKeyService(db)
    
    # Validate scopes if provided
    if request.scopes:
        valid_scopes = [scope.value for scope in APIKeyScope]
        invalid_scopes = [s for s in request.scopes if s not in valid_scopes]
        if invalid_scopes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scopes: {', '.join(invalid_scopes)}"
            )
    
    success = api_key_service.update_api_key(
        key_id=key_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        scopes=request.scopes,
        rate_limits=request.rate_limits,
        allowed_ips=request.allowed_ips,
        allowed_origins=request.allowed_origins
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Get updated key
    key_data = api_key_service.get_api_key(key_id, current_user.id)
    return APIKeyResponse(**key_data)

@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    api_key_service = APIKeyService(db)
    
    success = api_key_service.revoke_api_key(
        key_id=key_id,
        user_id=current_user.id,
        reason=reason
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}

@router.post("/keys/{key_id}/regenerate", response_model=APIKeyCreateResponse)
async def regenerate_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate an API key (revoke old, create new with same settings)"""
    api_key_service = APIKeyService(db)
    
    # Get existing key
    existing_key = api_key_service.get_api_key(key_id, current_user.id)
    if not existing_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Revoke old key
    api_key_service.revoke_api_key(key_id, current_user.id, "Regenerated")
    
    # Create new key with same settings
    try:
        result = api_key_service.create_api_key(
            user_id=current_user.id,
            name=existing_key['name'] + " (regenerated)",
            description=existing_key['description'],
            scopes=existing_key['scopes'],
            rate_limits=existing_key['rate_limits'],
            allowed_ips=existing_key['allowed_ips'],
            allowed_origins=existing_key['allowed_origins']
        )
        
        return APIKeyCreateResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to regenerate API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API key"
        )

# Webhook Endpoints

@router.post("/webhooks", response_model=WebhookResponse)
async def create_webhook(
    request: WebhookCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new webhook"""
    webhook_service = WebhookService(db)
    
    # Validate events
    valid_events = webhook_service.get_valid_events()
    invalid_events = [e for e in request.events if e not in valid_events]
    if invalid_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid events: {', '.join(invalid_events)}"
        )
    
    try:
        webhook = webhook_service.create_webhook(
            user_id=current_user.id,
            name=request.name,
            url=str(request.url),
            events=request.events,
            secret=request.secret,
            api_key_id=request.api_key_id,
            custom_headers=request.custom_headers,
            max_retries=request.max_retries,
            timeout_seconds=request.timeout_seconds
        )
        
        return WebhookResponse(
            id=webhook['id'],
            name=webhook['name'],
            url=webhook['url'],
            events=webhook['events'],
            status=webhook['status'],
            last_triggered_at=webhook.get('last_triggered_at'),
            success_count=webhook['success_count'],
            failure_count=webhook['failure_count'],
            created_at=webhook['created_at']
        )
        
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook"
        )

@router.get("/webhooks", response_model=List[WebhookResponse])
async def list_webhooks(
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's webhooks"""
    webhook_service = WebhookService(db)
    
    webhooks = webhook_service.list_webhooks(
        user_id=current_user.id,
        include_inactive=include_inactive
    )
    
    return [
        WebhookResponse(
            id=w['id'],
            name=w['name'],
            url=w['url'],
            events=w['events'],
            status=w['status'],
            last_triggered_at=w.get('last_triggered_at'),
            success_count=w['success_count'],
            failure_count=w['failure_count'],
            created_at=w['created_at']
        )
        for w in webhooks
    ]

@router.get("/webhooks/{webhook_id}")
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get webhook details including recent logs"""
    webhook_service = WebhookService(db)
    
    webhook = webhook_service.get_webhook(
        webhook_id=webhook_id,
        user_id=current_user.id
    )
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return webhook

@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    request: WebhookUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update webhook settings"""
    webhook_service = WebhookService(db)
    
    # Validate events if provided
    if request.events:
        valid_events = webhook_service.get_valid_events()
        invalid_events = [e for e in request.events if e not in valid_events]
        if invalid_events:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid events: {', '.join(invalid_events)}"
            )
    
    success = webhook_service.update_webhook(
        webhook_id=webhook_id,
        user_id=current_user.id,
        name=request.name,
        url=str(request.url) if request.url else None,
        events=request.events,
        status=request.status,
        custom_headers=request.custom_headers,
        max_retries=request.max_retries,
        timeout_seconds=request.timeout_seconds
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    # Get updated webhook
    webhook = webhook_service.get_webhook(webhook_id, current_user.id)
    
    return WebhookResponse(
        id=webhook['id'],
        name=webhook['name'],
        url=webhook['url'],
        events=webhook['events'],
        status=webhook['status'],
        last_triggered_at=webhook.get('last_triggered_at'),
        success_count=webhook['success_count'],
        failure_count=webhook['failure_count'],
        created_at=webhook['created_at']
    )

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a webhook"""
    webhook_service = WebhookService(db)
    
    success = webhook_service.delete_webhook(
        webhook_id=webhook_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    return {"message": "Webhook deleted successfully"}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test event to webhook"""
    webhook_service = WebhookService(db)
    
    # Send test event
    success = await webhook_service.send_test_event(
        webhook_id=webhook_id,
        user_id=current_user.id
    )
    
    if success is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test event delivery failed"
        )
    
    return {"message": "Test event sent successfully"}

# Documentation endpoints

@router.get("/docs")
async def get_api_documentation():
    """Get API documentation"""
    return {
        "version": "1.0.0",
        "base_url": "https://api.example.com/v1",
        "authentication": {
            "type": "Bearer",
            "header": "Authorization",
            "format": "Bearer YOUR_API_KEY"
        },
        "rate_limits": {
            "default": {
                "per_minute": 60,
                "per_hour": 1000,
                "per_day": 10000
            }
        },
        "scopes": [
            {
                "name": scope.value,
                "description": scope.value.replace(':', ' ').title()
            }
            for scope in APIKeyScope
        ],
        "endpoints": {
            "transcripts": "/transcripts",
            "analytics": "/analytics",
            "teams": "/teams",
            "webhooks": "/developers/webhooks"
        }
    }

@router.get("/events")
async def get_webhook_events():
    """Get available webhook events"""
    webhook_service = WebhookService(get_db())
    
    return {
        "events": webhook_service.get_valid_events(),
        "categories": {
            "transcripts": [
                "transcript.created",
                "transcript.updated",
                "transcript.deleted",
                "transcript.completed"
            ],
            "teams": [
                "team.member.added",
                "team.member.removed",
                "team.updated"
            ],
            "usage": [
                "usage.limit.warning",
                "usage.limit.exceeded"
            ]
        }
    }