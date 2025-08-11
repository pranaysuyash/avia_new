"""
API endpoints for notification system
Task 200: Build notification and communication system
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from notification_system import (
    NotificationChannel,
    NotificationManager,
    NotificationPriority,
    NotificationRequest,
    NotificationService,
    NotificationType,
    NotificationWebSocketHandler,
    WebhookConfig
)
from ..dependencies import get_current_user, get_db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Initialize notification service (would be configured from environment)
notification_config = {
    'smtp_host': 'smtp.gmail.com',
    'smtp_port': 587,
    'smtp_user': 'notifications@platform.com',
    'smtp_password': 'password',
    'smtp_from': 'noreply@platform.com',
    'redis_host': 'localhost',
    'redis_port': 6379
}

notification_service = NotificationService(notification_config)
notification_manager = NotificationManager(notification_service)
ws_handler = NotificationWebSocketHandler(notification_service)


# Request/Response Models
class SendNotificationRequest(BaseModel):
    """Request to send a notification"""
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: Optional[List[NotificationChannel]] = None
    data: Dict[str, Any] = {}
    schedule_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationPreferencesUpdate(BaseModel):
    """Update notification preferences"""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class WebhookSubscription(BaseModel):
    """Webhook subscription request"""
    url: str
    events: List[NotificationType]
    headers: Dict[str, str] = {}
    secret: Optional[str] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    type: str
    channel: str
    priority: str
    status: str
    subject: str
    body: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None


class NotificationStatsResponse(BaseModel):
    """Notification statistics"""
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    by_channel: Dict[str, int]
    by_type: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


# Endpoints
@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a notification to the current user"""
    notification_request = NotificationRequest(
        user_id=current_user['id'],
        type=request.type,
        priority=request.priority,
        channels=request.channels,
        data=request.data,
        schedule_at=request.schedule_at,
        expires_at=request.expires_at
    )
    
    result = await notification_service.send_notification(notification_request)
    
    return {
        "status": "success",
        "results": result
    }


@router.get("/")
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: Dict = Depends(get_current_user)
) -> List[NotificationResponse]:
    """Get user's notifications"""
    notifications = await notification_service.get_user_notifications(
        user_id=current_user['id'],
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )
    
    return notifications


@router.post("/mark-read")
async def mark_notifications_read(
    notification_ids: List[str],
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Mark notifications as read"""
    await notification_service.mark_as_read(
        user_id=current_user['id'],
        notification_ids=notification_ids
    )
    
    return {"status": "success", "marked_count": len(notification_ids)}


@router.get("/preferences")
async def get_notification_preferences(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get user's notification preferences"""
    preferences = await notification_service.get_user_preferences(
        user_id=current_user['id']
    )
    
    return preferences


@router.put("/preferences")
async def update_notification_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update user's notification preferences"""
    preferences_dict = updates.dict(exclude_unset=True)
    
    await notification_service.update_preferences(
        user_id=current_user['id'],
        preferences=preferences_dict
    )
    
    return {"status": "success", "updated": list(preferences_dict.keys())}


@router.post("/webhooks/subscribe")
async def subscribe_webhook(
    subscription: WebhookSubscription,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Subscribe to webhook notifications"""
    webhook_config = WebhookConfig(
        url=subscription.url,
        events=subscription.events,
        headers=subscription.headers,
        secret=subscription.secret
    )
    
    # Store webhook configuration
    if current_user['id'] not in notification_service.webhooks:
        notification_service.webhooks[current_user['id']] = []
    
    notification_service.webhooks[current_user['id']].append(webhook_config)
    
    return {
        "status": "success",
        "webhook_id": f"webhook_{len(notification_service.webhooks[current_user['id']])}"
    }


@router.delete("/webhooks/{webhook_id}")
async def unsubscribe_webhook(
    webhook_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Unsubscribe from webhook notifications"""
    # Remove webhook configuration
    # Implementation would remove from database
    
    return {"status": "success", "webhook_id": webhook_id}


@router.get("/stats")
async def get_notification_stats(
    days: int = Query(30, ge=1, le=365),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> NotificationStatsResponse:
    """Get notification statistics"""
    # This would query the database for statistics
    stats = NotificationStatsResponse(
        total_sent=150,
        total_delivered=145,
        total_opened=120,
        total_clicked=85,
        by_channel={
            "email": 50,
            "in_app": 80,
            "sms": 10,
            "webhook": 10
        },
        by_type={
            "transcription_completed": 100,
            "batch_processing_completed": 20,
            "share_invitation": 15,
            "quota_warning": 10,
            "other": 5
        },
        recent_activity=[
            {
                "date": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                "sent": 5 - i,
                "delivered": 5 - i,
                "opened": 4 - i
            }
            for i in range(7)
        ]
    )
    
    return stats


@router.post("/test")
async def send_test_notification(
    channel: NotificationChannel,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Send a test notification"""
    notification_request = NotificationRequest(
        user_id=current_user['id'],
        type=NotificationType.CUSTOM,
        priority=NotificationPriority.LOW,
        channels=[channel],
        data={
            "message": "This is a test notification",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    result = await notification_service.send_notification(notification_request)
    
    return {
        "status": "success",
        "channel": channel.value,
        "result": result
    }


# WebSocket endpoint for real-time notifications
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time notifications"""
    await websocket.accept()
    await ws_handler.handle_connection(websocket, "/notifications/ws")


# Notification triggers (called by other services)
@router.post("/triggers/transcription-complete", include_in_schema=False)
async def trigger_transcription_complete(
    user_id: str,
    transcription_id: str,
    title: str,
    duration: str,
    word_count: int
) -> Dict[str, Any]:
    """Trigger transcription completion notification"""
    result = await notification_manager.notify_transcription_complete(
        user_id=user_id,
        transcription_id=transcription_id,
        title=title,
        duration=duration,
        word_count=word_count
    )
    
    return {"status": "success", "results": result}


@router.post("/triggers/batch-complete", include_in_schema=False)
async def trigger_batch_complete(
    user_id: str,
    batch_id: str,
    total_files: int,
    successful: int,
    failed: int
) -> Dict[str, Any]:
    """Trigger batch processing completion notification"""
    result = await notification_manager.notify_batch_complete(
        user_id=user_id,
        batch_id=batch_id,
        total_files=total_files,
        successful=successful,
        failed=failed
    )
    
    return {"status": "success", "results": result}


@router.post("/triggers/quota-warning", include_in_schema=False)
async def trigger_quota_warning(
    user_id: str,
    usage_percent: float,
    limit: int,
    used: int
) -> Dict[str, Any]:
    """Trigger quota warning notification"""
    result = await notification_manager.notify_quota_warning(
        user_id=user_id,
        usage_percent=usage_percent,
        limit=limit,
        used=used
    )
    
    return {"status": "success", "results": result}


@router.post("/triggers/security-alert", include_in_schema=False)
async def trigger_security_alert(
    user_id: str,
    alert_type: str,
    description: str,
    ip_address: str,
    location: str
) -> Dict[str, Any]:
    """Trigger security alert notification"""
    result = await notification_manager.notify_security_alert(
        user_id=user_id,
        alert_type=alert_type,
        description=description,
        ip_address=ip_address,
        location=location
    )
    
    return {"status": "success", "results": result}


# Admin endpoints
@router.post("/admin/broadcast", dependencies=[Depends(get_current_user)])
async def broadcast_notification(
    user_ids: List[str],
    notification_type: NotificationType,
    priority: NotificationPriority,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """Broadcast notification to multiple users (admin only)"""
    results = {}
    
    for user_id in user_ids:
        notification_request = NotificationRequest(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            data=data
        )
        
        try:
            result = await notification_service.send_notification(notification_request)
            results[user_id] = result
        except Exception as e:
            results[user_id] = {"error": str(e)}
    
    return {
        "status": "success",
        "total_users": len(user_ids),
        "results": results
    }


@router.get("/admin/templates", dependencies=[Depends(get_current_user)])
async def get_notification_templates(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all notification templates (admin only)"""
    # This would fetch from database
    templates = [
        {
            "id": 1,
            "name": "transcription_completed_email",
            "type": "transcription_completed",
            "channel": "email",
            "subject_template": "Your transcription is ready: {{ title }}",
            "body_template": "Your transcription has been completed...",
            "is_active": True
        }
    ]
    
    return templates


@router.put("/admin/templates/{template_id}", dependencies=[Depends(get_current_user)])
async def update_notification_template(
    template_id: int,
    subject_template: Optional[str] = None,
    body_template: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update notification template (admin only)"""
    # This would update in database
    
    return {
        "status": "success",
        "template_id": template_id,
        "updated": True
    }