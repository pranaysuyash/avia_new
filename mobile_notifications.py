"""
Mobile Push Notifications System
Handles push notifications for React Native mobile app
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    """Push notification payload structure"""
    title: str
    body: str
    data: Dict[str, Any] = None
    badge: int = None
    sound: str = "default"
    category: str = "general"
    priority: str = "normal"  # normal, high
    ttl: int = 3600  # Time to live in seconds


@dataclass
class PushNotificationConfig:
    """Configuration for push notification services"""
    service: str  # 'firebase', 'apns', 'expo'
    api_key: Optional[str] = None
    server_key: Optional[str] = None
    app_id: Optional[str] = None
    project_id: Optional[str] = None


class MobilePushNotificationManager:
    """Manages push notifications for mobile app users"""
    
    def __init__(self, config: PushNotificationConfig):
        self.config = config
        self.session = None
    
    async def initialize(self):
        """Initialize HTTP session for notifications"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def send_notification(self, 
                              device_tokens: List[str], 
                              payload: NotificationPayload) -> Dict[str, Any]:
        """
        Send push notification to device tokens
        
        Args:
            device_tokens: List of device push tokens
            payload: Notification payload
            
        Returns:
            Dict with success/failure results
        """
        if self.config.service == 'firebase':
            return await self._send_firebase_notification(device_tokens, payload)
        elif self.config.service == 'expo':
            return await self._send_expo_notification(device_tokens, payload)
        else:
            logger.error(f"Unsupported notification service: {self.config.service}")
            return {"success": False, "error": "Unsupported service"}
    
    async def _send_firebase_notification(self, 
                                        device_tokens: List[str], 
                                        payload: NotificationPayload) -> Dict[str, Any]:
        """Send notification via Firebase Cloud Messaging"""
        if not self.config.server_key:
            return {"success": False, "error": "Firebase server key not configured"}
        
        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Authorization": f"key={self.config.server_key}",
            "Content-Type": "application/json"
        }
        
        results = []
        
        for token in device_tokens:
            fcm_payload = {
                "to": token,
                "notification": {
                    "title": payload.title,
                    "body": payload.body,
                    "sound": payload.sound,
                    "badge": payload.badge
                },
                "data": payload.data or {},
                "priority": "high" if payload.priority == "high" else "normal",
                "time_to_live": payload.ttl
            }
            
            try:
                async with self.session.post(url, headers=headers, json=fcm_payload) as response:
                    result = await response.json()
                    results.append({
                        "token": token[:20] + "...",  # Truncate for privacy
                        "success": response.status == 200,
                        "response": result
                    })
            except Exception as e:
                results.append({
                    "token": token[:20] + "...",
                    "success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "sent": success_count,
            "failed": len(results) - success_count,
            "results": results
        }
    
    async def _send_expo_notification(self, 
                                    device_tokens: List[str], 
                                    payload: NotificationPayload) -> Dict[str, Any]:
        """Send notification via Expo Push API"""
        url = "https://exp.host/--/api/v2/push/send"
        headers = {
            "Accept": "application/json",
            "Accept-encoding": "gzip, deflate",
            "Content-Type": "application/json"
        }
        
        # Build Expo push messages
        messages = []
        for token in device_tokens:
            messages.append({
                "to": token,
                "sound": payload.sound,
                "title": payload.title,
                "body": payload.body,
                "data": payload.data or {},
                "badge": payload.badge,
                "priority": payload.priority,
                "ttl": payload.ttl,
                "channelId": payload.category
            })
        
        try:
            async with self.session.post(url, headers=headers, json=messages) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {
                        "success": True,
                        "sent": len(messages),
                        "tickets": result.get("data", [])
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("message", "Unknown error")
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class TranscriptionNotificationService:
    """Service for transcription-related push notifications"""
    
    def __init__(self, push_manager: MobilePushNotificationManager):
        self.push_manager = push_manager
    
    async def notify_transcription_complete(self, 
                                          user_id: str, 
                                          file_name: str, 
                                          duration: float,
                                          device_tokens: List[str]):
        """Notify user when transcription is complete"""
        payload = NotificationPayload(
            title="Transcription Complete! 🎉",
            body=f"Your audio '{file_name}' ({duration:.1f}s) has been transcribed successfully.",
            data={
                "type": "transcription_complete",
                "user_id": user_id,
                "file_name": file_name,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            },
            category="transcription",
            priority="high",
            badge=1
        )
        
        return await self.push_manager.send_notification(device_tokens, payload)
    
    async def notify_transcription_failed(self, 
                                        user_id: str, 
                                        file_name: str, 
                                        error: str,
                                        device_tokens: List[str]):
        """Notify user when transcription fails"""
        payload = NotificationPayload(
            title="Transcription Failed ❌",
            body=f"Failed to transcribe '{file_name}'. Please try again.",
            data={
                "type": "transcription_failed",
                "user_id": user_id,
                "file_name": file_name,
                "error": error,
                "timestamp": datetime.now().isoformat()
            },
            category="transcription",
            priority="high",
            badge=1
        )
        
        return await self.push_manager.send_notification(device_tokens, payload)
    
    async def notify_large_file_processing(self, 
                                         user_id: str, 
                                         file_name: str, 
                                         estimated_time: int,
                                         device_tokens: List[str]):
        """Notify user about long processing time for large files"""
        payload = NotificationPayload(
            title="Processing Large File ⏳",
            body=f"'{file_name}' is being processed. Estimated time: {estimated_time} minutes.",
            data={
                "type": "processing_started",
                "user_id": user_id,
                "file_name": file_name,
                "estimated_time": estimated_time,
                "timestamp": datetime.now().isoformat()
            },
            category="processing",
            priority="normal"
        )
        
        return await self.push_manager.send_notification(device_tokens, payload)
    
    async def notify_quota_warning(self, 
                                 user_id: str, 
                                 usage_percentage: float,
                                 device_tokens: List[str]):
        """Notify user about approaching quota limits"""
        payload = NotificationPayload(
            title="Usage Limit Warning ⚠️",
            body=f"You've used {usage_percentage:.0f}% of your monthly quota. Consider upgrading.",
            data={
                "type": "quota_warning",
                "user_id": user_id,
                "usage_percentage": usage_percentage,
                "timestamp": datetime.now().isoformat()
            },
            category="account",
            priority="normal",
            badge=1
        )
        
        return await self.push_manager.send_notification(device_tokens, payload)
    
    async def notify_sharing_update(self, 
                                  user_id: str, 
                                  shared_by: str, 
                                  file_name: str,
                                  device_tokens: List[str]):
        """Notify user when someone shares a transcript with them"""
        payload = NotificationPayload(
            title="New Shared Transcript 📄",
            body=f"{shared_by} shared '{file_name}' with you.",
            data={
                "type": "sharing_notification",
                "user_id": user_id,
                "shared_by": shared_by,
                "file_name": file_name,
                "timestamp": datetime.now().isoformat()
            },
            category="sharing",
            priority="normal",
            badge=1
        )
        
        return await self.push_manager.send_notification(device_tokens, payload)


class NotificationScheduler:
    """Schedules and manages notification delivery"""
    
    def __init__(self, notification_service: TranscriptionNotificationService):
        self.notification_service = notification_service
        self.scheduled_notifications = []
    
    def schedule_notification(self, 
                            delay_minutes: int, 
                            notification_type: str, 
                            **kwargs):
        """Schedule a notification to be sent after a delay"""
        send_time = datetime.now() + timedelta(minutes=delay_minutes)
        
        scheduled = {
            "id": f"{notification_type}_{datetime.now().timestamp()}",
            "type": notification_type,
            "send_time": send_time,
            "kwargs": kwargs
        }
        
        self.scheduled_notifications.append(scheduled)
        logger.info(f"Scheduled {notification_type} notification for {send_time}")
    
    async def process_scheduled_notifications(self):
        """Process and send scheduled notifications"""
        now = datetime.now()
        ready_notifications = []
        
        # Find notifications ready to send
        for notification in self.scheduled_notifications:
            if notification["send_time"] <= now:
                ready_notifications.append(notification)
        
        # Send ready notifications
        for notification in ready_notifications:
            try:
                await self._send_scheduled_notification(notification)
                self.scheduled_notifications.remove(notification)
            except Exception as e:
                logger.error(f"Failed to send scheduled notification: {e}")
    
    async def _send_scheduled_notification(self, notification: Dict[str, Any]):
        """Send a scheduled notification"""
        notification_type = notification["type"]
        kwargs = notification["kwargs"]
        
        if notification_type == "transcription_complete":
            await self.notification_service.notify_transcription_complete(**kwargs)
        elif notification_type == "quota_warning":
            await self.notification_service.notify_quota_warning(**kwargs)
        # Add more notification types as needed
        
        logger.info(f"Sent scheduled notification: {notification_type}")


# Device token management
class DeviceTokenManager:
    """Manages device tokens for push notifications"""
    
    def __init__(self):
        self.tokens_storage = {}  # In production, use database
    
    def register_token(self, user_id: str, device_token: str, platform: str):
        """Register device token for user"""
        if user_id not in self.tokens_storage:
            self.tokens_storage[user_id] = []
        
        # Avoid duplicates
        token_info = {"token": device_token, "platform": platform, "registered": datetime.now()}
        
        # Remove existing token if it exists
        self.tokens_storage[user_id] = [
            t for t in self.tokens_storage[user_id] if t["token"] != device_token
        ]
        
        # Add new/updated token
        self.tokens_storage[user_id].append(token_info)
        logger.info(f"Registered push token for user {user_id} on {platform}")
    
    def get_user_tokens(self, user_id: str) -> List[str]:
        """Get all active tokens for user"""
        if user_id in self.tokens_storage:
            return [t["token"] for t in self.tokens_storage[user_id]]
        return []
    
    def remove_token(self, user_id: str, device_token: str):
        """Remove device token"""
        if user_id in self.tokens_storage:
            self.tokens_storage[user_id] = [
                t for t in self.tokens_storage[user_id] if t["token"] != device_token
            ]
            logger.info(f"Removed push token for user {user_id}")


# Usage example and integration functions
async def setup_mobile_notifications(config: Dict[str, Any]) -> TranscriptionNotificationService:
    """Setup mobile notifications with configuration"""
    push_config = PushNotificationConfig(
        service=config.get("service", "expo"),
        api_key=config.get("api_key"),
        server_key=config.get("server_key"),
        app_id=config.get("app_id"),
        project_id=config.get("project_id")
    )
    
    push_manager = MobilePushNotificationManager(push_config)
    await push_manager.initialize()
    
    notification_service = TranscriptionNotificationService(push_manager)
    return notification_service


def create_notification_templates() -> Dict[str, Dict[str, str]]:
    """Create predefined notification templates"""
    return {
        "transcription_complete": {
            "title": "Transcription Complete! 🎉",
            "body": "Your audio has been transcribed successfully.",
            "category": "transcription"
        },
        "transcription_failed": {
            "title": "Transcription Failed ❌", 
            "body": "There was an error processing your audio.",
            "category": "transcription"
        },
        "quota_warning": {
            "title": "Usage Limit Warning ⚠️",
            "body": "You're approaching your monthly quota.",
            "category": "account"
        },
        "processing_started": {
            "title": "Processing Large File ⏳",
            "body": "Your file is being processed...",
            "category": "processing"
        },
        "share_received": {
            "title": "New Shared Transcript 📄",
            "body": "Someone shared a transcript with you.",
            "category": "sharing"
        }
    }


if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    async def demo():
        config = {
            "service": "expo",
            "api_key": "demo_key"
        }
        
        service = await setup_mobile_notifications(config)
        
        # Example notification
        tokens = ["ExponentPushToken[demo_token]"]
        await service.notify_transcription_complete(
            user_id="user123",
            file_name="meeting_recording.mp3", 
            duration=120.5,
            device_tokens=tokens
        )
        
        await service.push_manager.close()
    
    # Run demo
    # asyncio.run(demo())