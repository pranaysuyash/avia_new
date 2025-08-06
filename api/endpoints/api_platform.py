"""
API Platform and Developer Portal Endpoints

Endpoints for API keys, webhooks, documentation, and developer resources
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, HttpUrl
import uuid
import secrets
import hashlib
import hmac

from database.connection import get_db
from api.dependencies import get_current_user
from database.models_extended import APIKey, APIUsageLog, Webhook
from notifications.notification_manager import NotificationManager as NotificationService
from auth.email_service import EmailService

router = APIRouter(prefix="/api/v1/developer", tags=["Developer Portal"])

# Request/Response Models
class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str]
    scopes: List[str]
    rate_limit: Optional[int] = 1000
    expires_in_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    key_id: str
    key: str  # Only returned on creation
    name: str
    scopes: List[str]
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime]

class WebhookCreate(BaseModel):
    url: HttpUrl
    events: List[str]
    description: Optional[str]
    headers: Optional[Dict[str, str]] = {}

class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl]
    events: Optional[List[str]]
    is_active: Optional[bool]

class WebhookTest(BaseModel):
    event_type: str
    payload: Dict[str, Any]

class SDKInfo(BaseModel):
    language: str
    version: str
    download_url: str
    documentation_url: str
    examples_url: str
    last_updated: datetime

# API Key Management
@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_config: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new API key"""
    # Generate secure API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Calculate expiration
    expires_at = None
    if key_config.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_config.expires_in_days)
    
    # Create key record
    db_key = APIKey(
        id=str(uuid.uuid4()),
        key_hash=key_hash,
        name=key_config.name,
        description=key_config.description,
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        scopes=key_config.scopes,
        rate_limit=key_config.rate_limit,
        expires_at=expires_at
    )
    
    db.add(db_key)
    db.commit()
    
    # Send email with API key
    email_service = EmailService()
    await email_service.send_template_email(
        to=current_user["email"],
        template="api_key_created",
        data={
            "key_name": key_config.name,
            "api_key": api_key,
            "scopes": key_config.scopes
        }
    )
    
    return APIKeyResponse(
        key_id=db_key.id,
        key=api_key,  # Only shown once
        name=db_key.name,
        scopes=db_key.scopes,
        rate_limit=db_key.rate_limit,
        created_at=db_key.created_at,
        expires_at=db_key.expires_at
    )

@router.get("/api-keys")
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's API keys"""
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user["id"],
        APIKey.is_active == True
    ).order_by(APIKey.created_at.desc()).all()
    
    # Don't return the actual keys, just metadata
    return [{
        "key_id": key.id,
        "name": key.name,
        "description": key.description,
        "scopes": key.scopes,
        "rate_limit": key.rate_limit,
        "last_used_at": key.last_used_at,
        "created_at": key.created_at,
        "expires_at": key.expires_at
    } for key in keys]

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke API key"""
    key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user["id"]
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = False
    key.revoked_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "revoked", "key_id": key_id}

@router.post("/api-keys/{key_id}/regenerate")
async def regenerate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate API key"""
    # Revoke old key
    old_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user["id"]
    ).first()
    
    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    old_key.is_active = False
    old_key.revoked_at = datetime.utcnow()
    
    # Create new key with same config
    new_api_key = f"sk_{secrets.token_urlsafe(32)}"
    new_key_hash = hashlib.sha256(new_api_key.encode()).hexdigest()
    
    new_key = APIKey(
        id=str(uuid.uuid4()),
        key_hash=new_key_hash,
        name=old_key.name,
        description=old_key.description,
        user_id=current_user["id"],
        organization_id=current_user.get("organization_id"),
        scopes=old_key.scopes,
        rate_limit=old_key.rate_limit,
        expires_at=old_key.expires_at
    )
    
    db.add(new_key)
    db.commit()
    
    return {
        "key_id": new_key.id,
        "key": new_api_key,
        "message": "API key regenerated successfully"
    }

# Webhook Management
@router.post("/webhooks")
async def create_webhook(
    webhook: WebhookCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create webhook endpoint"""
    # Generate webhook secret for signature verification
    webhook_secret = secrets.token_urlsafe(32)
    
    db_webhook = Webhook(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        url=str(webhook.url),
        events=webhook.events,
        secret=webhook_secret
    )
    
    db.add(db_webhook)
    db.commit()
    
    return {
        "webhook_id": db_webhook.id,
        "url": db_webhook.url,
        "events": db_webhook.events,
        "secret": webhook_secret,  # Only shown once
        "created_at": db_webhook.created_at
    }

@router.get("/webhooks")
async def list_webhooks(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's webhooks"""
    webhooks = db.query(Webhook).filter(
        Webhook.user_id == current_user["id"]
    ).order_by(Webhook.created_at.desc()).all()
    
    return [{
        "webhook_id": wh.id,
        "url": wh.url,
        "events": wh.events,
        "is_active": wh.is_active,
        "last_triggered_at": wh.last_triggered_at,
        "failure_count": wh.failure_count,
        "created_at": wh.created_at
    } for wh in webhooks]

@router.put("/webhooks/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    update: WebhookUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update webhook configuration"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user["id"]
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Update fields
    if update.url:
        webhook.url = str(update.url)
    if update.events is not None:
        webhook.events = update.events
    if update.is_active is not None:
        webhook.is_active = update.is_active
    
    webhook.updated_at = datetime.utcnow()
    
    db.commit()
    
    return webhook

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete webhook"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user["id"]
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    
    return {"status": "deleted", "webhook_id": webhook_id}

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    test_data: WebhookTest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test webhook with sample payload"""
    webhook = db.query(Webhook).filter(
        Webhook.id == webhook_id,
        Webhook.user_id == current_user["id"]
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Send test webhook
    from services.webhook_service import WebhookService
    webhook_service = WebhookService()
    
    result = await webhook_service.send_webhook(
        webhook,
        test_data.event_type,
        test_data.payload,
        is_test=True
    )
    
    return {
        "status": "sent",
        "response_status": result.get("status_code"),
        "response_time_ms": result.get("response_time_ms")
    }

# API Usage and Analytics
@router.get("/usage")
async def get_api_usage(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    group_by: str = Query("day", pattern="^(hour|day|week|month)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API usage statistics"""
    # Default to last 30 days
    if not date_from:
        date_from = datetime.utcnow() - timedelta(days=30)
    if not date_to:
        date_to = datetime.utcnow()
    
    # Get user's API keys
    user_keys = db.query(APIKey.id).filter(
        APIKey.user_id == current_user["id"]
    ).subquery()
    
    # Get usage logs
    logs = db.query(APIUsageLog).filter(
        APIUsageLog.api_key_id.in_(user_keys),
        APIUsageLog.timestamp.between(date_from, date_to)
    ).all()
    
    # Aggregate by time period
    usage_by_period = {}
    endpoint_stats = {}
    total_requests = len(logs)
    total_errors = len([l for l in logs if l.status_code >= 400])
    
    for log in logs:
        # Group by period
        if group_by == "hour":
            period = log.timestamp.strftime("%Y-%m-%d %H:00")
        elif group_by == "day":
            period = log.timestamp.strftime("%Y-%m-%d")
        elif group_by == "week":
            period = log.timestamp.strftime("%Y-W%W")
        else:  # month
            period = log.timestamp.strftime("%Y-%m")
        
        if period not in usage_by_period:
            usage_by_period[period] = {
                "requests": 0,
                "errors": 0,
                "avg_response_time": []
            }
        
        usage_by_period[period]["requests"] += 1
        if log.status_code >= 400:
            usage_by_period[period]["errors"] += 1
        usage_by_period[period]["avg_response_time"].append(log.response_time_ms)
        
        # Endpoint statistics
        endpoint = f"{log.method} {log.endpoint}"
        if endpoint not in endpoint_stats:
            endpoint_stats[endpoint] = {
                "count": 0,
                "errors": 0,
                "avg_response_time": []
            }
        
        endpoint_stats[endpoint]["count"] += 1
        if log.status_code >= 400:
            endpoint_stats[endpoint]["errors"] += 1
        endpoint_stats[endpoint]["avg_response_time"].append(log.response_time_ms)
    
    # Calculate averages
    for period_data in usage_by_period.values():
        if period_data["avg_response_time"]:
            period_data["avg_response_time"] = sum(period_data["avg_response_time"]) / len(period_data["avg_response_time"])
        else:
            period_data["avg_response_time"] = 0
    
    for endpoint_data in endpoint_stats.values():
        if endpoint_data["avg_response_time"]:
            endpoint_data["avg_response_time"] = sum(endpoint_data["avg_response_time"]) / len(endpoint_data["avg_response_time"])
        else:
            endpoint_data["avg_response_time"] = 0
    
    return {
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate": (total_errors / total_requests * 100) if total_requests else 0,
        "usage_by_period": usage_by_period,
        "top_endpoints": dict(sorted(
            endpoint_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10])
    }

@router.get("/usage/quota")
async def get_usage_quota(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current usage against quotas"""
    # Get user's subscription/plan limits
    # For now, using default limits
    
    # Count requests in current period (hourly)
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    user_keys = db.query(APIKey.id).filter(
        APIKey.user_id == current_user["id"],
        APIKey.is_active == True
    ).subquery()
    
    hourly_requests = db.query(APIUsageLog).filter(
        APIUsageLog.api_key_id.in_(user_keys),
        APIUsageLog.timestamp >= current_hour
    ).count()
    
    # Get rate limits
    active_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user["id"],
        APIKey.is_active == True
    ).all()
    
    max_rate_limit = max([k.rate_limit for k in active_keys]) if active_keys else 1000
    
    return {
        "current_usage": hourly_requests,
        "hourly_limit": max_rate_limit,
        "usage_percentage": (hourly_requests / max_rate_limit * 100) if max_rate_limit else 0,
        "reset_at": current_hour + timedelta(hours=1)
    }

# SDK and Documentation
@router.get("/sdks")
async def list_sdks():
    """List available SDKs"""
    sdks = [
        SDKInfo(
            language="Python",
            version="1.2.0",
            download_url="https://pypi.org/project/transcription-api/",
            documentation_url="/docs/sdk/python",
            examples_url="https://github.com/example/python-sdk/examples",
            last_updated=datetime(2024, 1, 15)
        ),
        SDKInfo(
            language="JavaScript/TypeScript",
            version="1.2.0",
            download_url="https://www.npmjs.com/package/@transcription/api",
            documentation_url="/docs/sdk/javascript",
            examples_url="https://github.com/example/js-sdk/examples",
            last_updated=datetime(2024, 1, 15)
        ),
        SDKInfo(
            language="Go",
            version="1.1.0",
            download_url="https://pkg.go.dev/github.com/example/transcription-go",
            documentation_url="/docs/sdk/go",
            examples_url="https://github.com/example/go-sdk/examples",
            last_updated=datetime(2024, 1, 10)
        ),
        SDKInfo(
            language="Java",
            version="1.0.0",
            download_url="https://mvnrepository.com/artifact/com.example/transcription-api",
            documentation_url="/docs/sdk/java",
            examples_url="https://github.com/example/java-sdk/examples",
            last_updated=datetime(2024, 1, 5)
        )
    ]
    
    return sdks

@router.get("/openapi")
async def get_openapi_spec():
    """Get OpenAPI specification"""
    # Return the OpenAPI spec for API documentation
    from main import app
    return app.openapi()

@router.get("/postman-collection")
async def get_postman_collection():
    """Get Postman collection for API testing"""
    # Generate Postman collection from OpenAPI spec
    collection = {
        "info": {
            "name": "Transcription API",
            "description": "API collection for audio/video transcription service",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            # ... generate from OpenAPI spec
        ]
    }
    
    return collection

# Code Examples
@router.get("/examples/{language}")
async def get_code_examples(
    language: str,
    operation: Optional[str] = None
):
    """Get code examples for specific language"""
    examples = {
        "python": {
            "authentication": """
import requests

API_KEY = 'your_api_key_here'
headers = {'Authorization': f'Bearer {API_KEY}'}

response = requests.get('https://api.example.com/v1/transcripts', headers=headers)
print(response.json())
""",
            "create_transcription": """
import requests

API_KEY = 'your_api_key_here'
headers = {'Authorization': f'Bearer {API_KEY}'}

with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    data = {'language': 'en', 'speaker_detection': True}
    response = requests.post(
        'https://api.example.com/v1/transcriptions',
        headers=headers,
        files=files,
        data=data
    )
    
print(response.json())
""",
            "webhook_handling": """
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = 'your_webhook_secret'

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    body = request.get_data()
    
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        return 'Invalid signature', 401
    
    # Process webhook
    data = request.json
    print(f"Received {data['event']} event")
    
    return 'OK', 200
"""
        },
        "javascript": {
            # ... JavaScript examples
        }
    }
    
    if language not in examples:
        raise HTTPException(status_code=404, detail="Language not supported")
    
    if operation:
        if operation not in examples[language]:
            raise HTTPException(status_code=404, detail="Example not found")
        return {
            "language": language,
            "operation": operation,
            "code": examples[language][operation]
        }
    
    return {
        "language": language,
        "examples": list(examples[language].keys())
    }

# Rate Limit Testing
@router.get("/rate-limit-test")
async def test_rate_limits(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    """Test endpoint to check rate limiting"""
    # This endpoint helps developers test their rate limit handling
    
    # Get API key
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    api_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get current usage
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    hourly_requests = db.query(APIUsageLog).filter(
        APIUsageLog.api_key_id == api_key.id,
        APIUsageLog.timestamp >= current_hour
    ).count()
    
    remaining = max(0, api_key.rate_limit - hourly_requests)
    
    return {
        "rate_limit": api_key.rate_limit,
        "remaining": remaining,
        "reset_at": current_hour + timedelta(hours=1),
        "current_usage": hourly_requests
    }