"""
Notification System API Endpoints
Provides REST API interface for the Notification System
"""

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
import uuid
import logging
import json
from enum import Enum

from api.auth_middleware import get_current_user
from api.middleware.audit_logging import audit_log
from database.connection import get_db
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications")

# In-memory storage (replace with database in production)
notifications_store = {}
user_preferences = {}
active_connections: Dict[str, WebSocket] = {}

# Enums
class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_UPDATE = "task_update"
    SYSTEM = "system"
    COLLABORATION = "collaboration"
    SECURITY = "security"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

# Pydantic models
class NotificationCreate(BaseModel):
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(NotificationType.INFO, description="Notification type")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Priority level")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    action_url: Optional[str] = Field(None, description="URL for action button")
    action_text: Optional[str] = Field(None, description="Text for action button")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    channels: List[DeliveryChannel] = Field(default_factory=lambda: [DeliveryChannel.IN_APP])
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Analysis Complete",
                "message": "Your document analysis has finished processing",
                "type": "success",
                "priority": "medium",
                "data": {"task_id": "123", "document_name": "report.pdf"},
                "action_url": "/analysis/123",
                "action_text": "View Results",
                "channels": ["in_app", "email"]
            }
        }

class BulkNotificationCreate(BaseModel):
    user_ids: List[str] = Field(..., description="List of user IDs to notify")
    notification: NotificationCreate = Field(..., description="Notification to send")
    personalize: bool = Field(False, description="Whether to personalize messages")
    personalization_data: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Per-user personalization data")

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    data: Optional[Dict[str, Any]]
    action_url: Optional[str]
    action_text: Optional[str]
    read: bool
    read_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    channels: List[DeliveryChannel]

class NotificationPreferences(BaseModel):
    email_enabled: bool = Field(True, description="Enable email notifications")
    sms_enabled: bool = Field(False, description="Enable SMS notifications")
    push_enabled: bool = Field(True, description="Enable push notifications")
    in_app_enabled: bool = Field(True, description="Enable in-app notifications")
    quiet_hours_enabled: bool = Field(False, description="Enable quiet hours")
    quiet_hours_start: Optional[str] = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Quiet hours end time (HH:MM)")
    notification_types: Dict[str, bool] = Field(
        default_factory=lambda: {
            "info": True,
            "success": True,
            "warning": True,
            "error": True,
            "task_update": True,
            "system": True,
            "collaboration": True,
            "security": True
        },
        description="Enabled notification types"
    )
    priority_threshold: NotificationPriority = Field(
        NotificationPriority.LOW,
        description="Minimum priority to receive"
    )

class NotificationStats(BaseModel):
    total: int
    unread: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    last_7_days: List[Dict[str, Any]]

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new notification for the current user
    """
    try:
        user_id = current_user.get("user_id")
        notification_id = str(uuid.uuid4())
        
        # Create notification
        notification_data = {
            "id": notification_id,
            "user_id": user_id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "priority": notification.priority,
            "data": notification.data,
            "action_url": notification.action_url,
            "action_text": notification.action_text,
            "read": False,
            "read_at": None,
            "created_at": datetime.now(),
            "expires_at": notification.expires_at,
            "channels": notification.channels
        }
        
        # Store notification
        if user_id not in notifications_store:
            notifications_store[user_id] = []
        notifications_store[user_id].append(notification_data)
        
        # Send real-time notification if user is connected
        await send_realtime_notification(user_id, notification_data)
        
        # Process other delivery channels
        await process_delivery_channels(user_id, notification_data)
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="notification_created",
            details={"notification_id": notification_id, "type": notification.type}
        )
        
        return NotificationResponse(**notification_data)
        
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk", response_model=Dict[str, Any])
async def create_bulk_notifications(
    bulk_request: BulkNotificationCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send notifications to multiple users
    """
    try:
        # Check admin permission
        if not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        created_count = 0
        failed_users = []
        
        for user_id in bulk_request.user_ids:
            try:
                notification_data = bulk_request.notification.dict()
                
                # Apply personalization if enabled
                if bulk_request.personalize and bulk_request.personalization_data:
                    user_data = bulk_request.personalization_data.get(user_id, {})
                    notification_data["message"] = notification_data["message"].format(**user_data)
                    if notification_data.get("data"):
                        notification_data["data"].update(user_data)
                
                # Create notification for user
                notification_id = str(uuid.uuid4())
                notification_record = {
                    "id": notification_id,
                    "user_id": user_id,
                    **notification_data,
                    "read": False,
                    "read_at": None,
                    "created_at": datetime.now()
                }
                
                if user_id not in notifications_store:
                    notifications_store[user_id] = []
                notifications_store[user_id].append(notification_record)
                
                # Send real-time notification
                await send_realtime_notification(user_id, notification_record)
                
                created_count += 1
                
            except Exception as e:
                logger.error(f"Failed to create notification for user {user_id}: {e}")
                failed_users.append(user_id)
        
        return {
            "success": True,
            "created_count": created_count,
            "failed_users": failed_users,
            "total_users": len(bulk_request.user_ids)
        }
        
    except Exception as e:
        logger.error(f"Bulk notification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    type_filter: Optional[NotificationType] = Query(None),
    priority_filter: Optional[NotificationPriority] = Query(None),
    current_user=Depends(get_current_user)
):
    """
    Get notifications for the current user
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        # Apply filters
        filtered = user_notifications
        
        if unread_only:
            filtered = [n for n in filtered if not n["read"]]
        
        if type_filter:
            filtered = [n for n in filtered if n["type"] == type_filter]
        
        if priority_filter:
            filtered = [n for n in filtered if n["priority"] == priority_filter]
        
        # Remove expired notifications
        now = datetime.now()
        filtered = [n for n in filtered if not n.get("expires_at") or n["expires_at"] > now]
        
        # Sort by created_at descending
        filtered.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Paginate
        paginated = filtered[skip:skip + limit]
        
        return [NotificationResponse(**n) for n in paginated]
        
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count", response_model=Dict[str, int])
async def get_unread_count(
    current_user=Depends(get_current_user)
):
    """
    Get count of unread notifications
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        # Count unread, non-expired notifications
        now = datetime.now()
        unread_count = sum(
            1 for n in user_notifications 
            if not n["read"] and (not n.get("expires_at") or n["expires_at"] > now)
        )
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"Failed to get unread count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user=Depends(get_current_user)
):
    """
    Mark a notification as read
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        notification = next((n for n in user_notifications if n["id"] == notification_id), None)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification["read"] = True
        notification["read_at"] = datetime.now()
        
        return {"success": True, "read_at": notification["read_at"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mark-all-read")
async def mark_all_as_read(
    current_user=Depends(get_current_user)
):
    """
    Mark all notifications as read
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        read_at = datetime.now()
        count = 0
        
        for notification in user_notifications:
            if not notification["read"]:
                notification["read"] = True
                notification["read_at"] = read_at
                count += 1
        
        return {"success": True, "marked_count": count}
        
    except Exception as e:
        logger.error(f"Failed to mark all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user=Depends(get_current_user)
):
    """
    Delete a notification
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        initial_count = len(user_notifications)
        notifications_store[user_id] = [n for n in user_notifications if n["id"] != notification_id]
        
        if len(notifications_store[user_id]) == initial_count:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear-all")
async def clear_all_notifications(
    current_user=Depends(get_current_user)
):
    """
    Clear all notifications for the current user
    """
    try:
        user_id = current_user.get("user_id")
        count = len(notifications_store.get(user_id, []))
        notifications_store[user_id] = []
        
        return {"success": True, "cleared_count": count}
        
    except Exception as e:
        logger.error(f"Failed to clear notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preferences", response_model=NotificationPreferences)
async def get_preferences(
    current_user=Depends(get_current_user)
):
    """
    Get notification preferences for the current user
    """
    try:
        user_id = current_user.get("user_id")
        
        # Get stored preferences or return defaults
        if user_id in user_preferences:
            return NotificationPreferences(**user_preferences[user_id])
        else:
            return NotificationPreferences()
        
    except Exception as e:
        logger.error(f"Failed to get preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences", response_model=NotificationPreferences)
async def update_preferences(
    preferences: NotificationPreferences,
    current_user=Depends(get_current_user)
):
    """
    Update notification preferences
    """
    try:
        user_id = current_user.get("user_id")
        
        # Store preferences
        user_preferences[user_id] = preferences.dict()
        
        # Audit log
        await audit_log(
            user_id=user_id,
            action="notification_preferences_updated",
            details={"preferences": preferences.dict()}
        )
        
        return preferences
        
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user=Depends(get_current_user)
):
    """
    Get notification statistics
    """
    try:
        user_id = current_user.get("user_id")
        user_notifications = notifications_store.get(user_id, [])
        
        # Basic counts
        total = len(user_notifications)
        unread = sum(1 for n in user_notifications if not n["read"])
        
        # Count by type
        by_type = {}
        for notification in user_notifications:
            notification_type = notification["type"]
            by_type[notification_type] = by_type.get(notification_type, 0) + 1
        
        # Count by priority
        by_priority = {}
        for notification in user_notifications:
            priority = notification["priority"]
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        # Last 7 days trend
        now = datetime.now()
        last_7_days = []
        
        for i in range(7):
            date = now - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            count = sum(
                1 for n in user_notifications
                if n["created_at"].date() == date.date()
            )
            last_7_days.append({
                "date": date_str,
                "count": count
            })
        
        last_7_days.reverse()
        
        return NotificationStats(
            total=total,
            unread=unread,
            by_type=by_type,
            by_priority=by_priority,
            last_7_days=last_7_days
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_notification(
    type: NotificationType = Query(NotificationType.INFO),
    current_user=Depends(get_current_user)
):
    """
    Send a test notification
    """
    try:
        test_notification = NotificationCreate(
            title="Test Notification",
            message=f"This is a test {type} notification sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            type=type,
            priority=NotificationPriority.MEDIUM,
            data={"test": True, "timestamp": datetime.now().isoformat()},
            action_url="/notifications",
            action_text="View All"
        )
        
        result = await create_notification(test_notification, current_user, None)
        
        return {"success": True, "notification": result}
        
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time notifications
@router.websocket("/ws")
async def notification_websocket(
    websocket: WebSocket,
    token: str = Query(...)
):
    """
    WebSocket endpoint for real-time notifications
    """
    # Validate token and get user
    try:
        # TODO: Implement proper token validation
        user_id = "test_user"  # Extract from token
        
        await websocket.accept()
        active_connections[user_id] = websocket
        
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to notification service"
        })
        
        try:
            while True:
                # Keep connection alive
                data = await websocket.receive_text()
                
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                    
        except WebSocketDisconnect:
            del active_connections[user_id]
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Helper functions
async def send_realtime_notification(user_id: str, notification: Dict[str, Any]):
    """
    Send notification through WebSocket if user is connected
    """
    if user_id in active_connections:
        try:
            await active_connections[user_id].send_json({
                "type": "notification",
                "data": {
                    "id": notification["id"],
                    "title": notification["title"],
                    "message": notification["message"],
                    "type": notification["type"],
                    "priority": notification["priority"],
                    "timestamp": notification["created_at"].isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
            # Remove dead connection
            del active_connections[user_id]

async def process_delivery_channels(user_id: str, notification: Dict[str, Any]):
    """
    Process notification delivery through various channels
    """
    preferences = user_preferences.get(user_id, NotificationPreferences().dict())
    
    for channel in notification["channels"]:
        if channel == DeliveryChannel.EMAIL and preferences.get("email_enabled", True):
            # TODO: Send email notification
            pass
        elif channel == DeliveryChannel.SMS and preferences.get("sms_enabled", False):
            # TODO: Send SMS notification
            pass
        elif channel == DeliveryChannel.PUSH and preferences.get("push_enabled", True):
            # TODO: Send push notification
            pass
        elif channel == DeliveryChannel.WEBHOOK:
            # TODO: Send webhook notification
            pass

def check_quiet_hours(user_id: str) -> bool:
    """
    Check if current time is within user's quiet hours
    """
    preferences = user_preferences.get(user_id, {})
    
    if not preferences.get("quiet_hours_enabled"):
        return False
    
    start_time = preferences.get("quiet_hours_start")
    end_time = preferences.get("quiet_hours_end")
    
    if not start_time or not end_time:
        return False
    
    # TODO: Implement quiet hours logic
    return False

@router.get("/health")
async def health_check():
    """
    Health check for notification service
    """
    return {
        "status": "healthy",
        "service": "notifications",
        "active_connections": len(active_connections),
        "total_notifications": sum(len(notifs) for notifs in notifications_store.values()),
        "timestamp": datetime.now().isoformat()
    }