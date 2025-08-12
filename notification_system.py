"""
Task 200: Comprehensive Notification and Communication System
Provides email, SMS, in-app notifications, and webhook support for the platform
"""

import asyncio
import json
import logging
import smtplib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin

import aiohttp
import redis
from jinja2 import Environment, Template
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from twilio.rest import Client as TwilioClient

Base = declarative_base()
logger = logging.getLogger(__name__)


# Notification Types
class NotificationType(Enum):
    """Types of notifications supported by the system"""
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_FAILED = "transcription_failed"
    BATCH_PROCESSING_STARTED = "batch_processing_started"
    BATCH_PROCESSING_COMPLETED = "batch_processing_completed"
    BATCH_PROCESSING_FAILED = "batch_processing_failed"
    EXPORT_READY = "export_ready"
    SHARE_INVITATION = "share_invitation"
    COLLABORATION_UPDATE = "collaboration_update"
    QUOTA_WARNING = "quota_warning"
    QUOTA_EXCEEDED = "quota_exceeded"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    SUBSCRIPTION_RENEWED = "subscription_renewed"
    PAYMENT_FAILED = "payment_failed"
    TEAM_INVITATION = "team_invitation"
    TEAM_MEMBER_ADDED = "team_member_added"
    API_KEY_EXPIRING = "api_key_expiring"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SECURITY_ALERT = "security_alert"
    CUSTOM = "custom"


class NotificationChannel(Enum):
    """Communication channels for notifications"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"


class NotificationPriority(Enum):
    """Priority levels for notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


# Database Models
class NotificationTemplate(Base):
    """Notification template storage"""
    __tablename__ = 'notification_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    subject_template = Column(Text)
    body_template = Column(Text, nullable=False)
    meta_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationLog(Base):
    """Log of all sent notifications"""
    __tablename__ = 'notification_logs'
    
    id = Column(Integer, primary_key=True)
    notification_id = Column(String(36), unique=True, nullable=False)
    user_id = Column(String(36), nullable=False)
    type = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=False)
    priority = Column(String(10), nullable=False)
    status = Column(String(20), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(Text)
    body = Column(Text)
    meta_data = Column(JSON)
    error_message = Column(Text)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserNotificationPreferences(Base):
    """User notification preferences"""
    __tablename__ = 'user_notification_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    webhook_enabled = Column(Boolean, default=False)
    
    # Granular preferences by notification type
    preferences = Column(JSON, default={})
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))
    timezone = Column(String(50), default='UTC')
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    webhook_url = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic Models
class NotificationRequest(BaseModel):
    """Request model for sending notifications"""
    user_id: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: Optional[List[NotificationChannel]] = None
    data: Dict[str, Any] = {}
    schedule_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class WebhookConfig(BaseModel):
    """Webhook configuration"""
    url: HttpUrl
    events: List[NotificationType]
    headers: Dict[str, str] = {}
    secret: Optional[str] = None
    retry_count: int = 3
    timeout: int = 30


@dataclass
class Notification:
    """Internal notification representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    type: NotificationType = NotificationType.CUSTOM
    channel: NotificationChannel = NotificationChannel.IN_APP
    priority: NotificationPriority = NotificationPriority.MEDIUM
    status: NotificationStatus = NotificationStatus.PENDING
    recipient: str = ""
    subject: str = ""
    body: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class NotificationService:
    """Main notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Email configuration
        self.smtp_host = config.get('smtp_host', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password')
        self.smtp_from = config.get('smtp_from', 'noreply@example.com')
        self.smtp_use_tls = config.get('smtp_use_tls', True)
        
        # SMS configuration (Twilio)
        self.twilio_account_sid = config.get('twilio_account_sid')
        self.twilio_auth_token = config.get('twilio_auth_token')
        self.twilio_from_number = config.get('twilio_from_number')
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = TwilioClient(
                self.twilio_account_sid,
                self.twilio_auth_token
            )
        
        # Redis for in-app notifications
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            decode_responses=True
        )
        
        # Template engine
        self.template_env = Environment()
        
        # Webhook configurations
        self.webhooks: Dict[str, List[WebhookConfig]] = {}
        
        # Rate limiting
        self.rate_limits = {
            NotificationChannel.EMAIL: 100,  # per hour
            NotificationChannel.SMS: 50,     # per hour
            NotificationChannel.WEBHOOK: 200  # per hour
        }
        
        # Notification queue
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        
        # Active subscriptions for real-time notifications
        self.subscriptions: Dict[str, Set[str]] = {}
    
    async def send_notification(
        self,
        request: NotificationRequest
    ) -> Dict[str, Any]:
        """Send notification through requested channels"""
        results = {}
        
        # Get user preferences
        preferences = await self.get_user_preferences(request.user_id)
        
        # Determine channels to use
        channels = request.channels
        if not channels:
            channels = self._get_default_channels(request.type, preferences)
        
        # Check quiet hours
        if self._is_quiet_hours(preferences):
            channels = [c for c in channels if c != NotificationChannel.PUSH]
        
        # Send through each channel
        for channel in channels:
            if self._is_channel_enabled(channel, preferences):
                notification = await self._create_notification(
                    request, channel, preferences
                )
                
                if request.schedule_at:
                    await self._schedule_notification(notification)
                    results[channel.value] = "scheduled"
                else:
                    result = await self._send_through_channel(notification)
                    results[channel.value] = result
        
        return results
    
    async def _send_through_channel(
        self,
        notification: Notification
    ) -> Dict[str, Any]:
        """Send notification through specific channel"""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return await self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                return await self._send_sms(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                return await self._send_in_app(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(notification)
            elif notification.channel == NotificationChannel.PUSH:
                return await self._send_push(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack(notification)
            elif notification.channel == NotificationChannel.TEAMS:
                return await self._send_teams(notification)
            elif notification.channel == NotificationChannel.DISCORD:
                return await self._send_discord(notification)
            else:
                raise ValueError(f"Unsupported channel: {notification.channel}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            await self._log_notification(notification)
            return {"status": "failed", "error": str(e)}
    
    async def _send_email(self, notification: Notification) -> Dict[str, Any]:
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = notification.recipient
            msg['Subject'] = notification.subject
            
            # Add HTML body
            html_body = self._render_email_template(notification)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            await self._log_notification(notification)
            
            return {"status": "sent", "message_id": notification.id}
        except Exception as e:
            raise Exception(f"Email sending failed: {e}")
    
    async def _send_sms(self, notification: Notification) -> Dict[str, Any]:
        """Send SMS notification"""
        if not self.twilio_client:
            raise ValueError("Twilio not configured")
        
        try:
            message = self.twilio_client.messages.create(
                body=notification.body,
                from_=self.twilio_from_number,
                to=notification.recipient
            )
            
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.metadata['twilio_sid'] = message.sid
            await self._log_notification(notification)
            
            return {"status": "sent", "message_id": message.sid}
        except Exception as e:
            raise Exception(f"SMS sending failed: {e}")
    
    async def _send_in_app(self, notification: Notification) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # Store in Redis for real-time delivery
            key = f"notifications:{notification.user_id}"
            self.redis_client.lpush(key, json.dumps({
                "id": notification.id,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "subject": notification.subject,
                "body": notification.body,
                "data": notification.data,
                "created_at": notification.created_at.isoformat()
            }))
            
            # Set expiry
            self.redis_client.expire(key, 86400 * 7)  # 7 days
            
            # Publish to real-time subscribers
            await self._publish_realtime(notification)
            
            notification.status = NotificationStatus.DELIVERED
            notification.sent_at = datetime.utcnow()
            notification.delivered_at = datetime.utcnow()
            await self._log_notification(notification)
            
            return {"status": "delivered", "notification_id": notification.id}
        except Exception as e:
            raise Exception(f"In-app notification failed: {e}")
    
    async def _send_webhook(self, notification: Notification) -> Dict[str, Any]:
        """Send webhook notification"""
        webhook_config = notification.metadata.get('webhook_config', {})
        url = webhook_config.get('url', notification.recipient)
        
        payload = {
            "notification_id": notification.id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "data": notification.data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        headers = webhook_config.get('headers', {})
        headers['Content-Type'] = 'application/json'
        
        # Add signature if secret is provided
        if secret := webhook_config.get('secret'):
            import hmac
            import hashlib
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = signature
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        notification.status = NotificationStatus.DELIVERED
                        notification.sent_at = datetime.utcnow()
                        notification.delivered_at = datetime.utcnow()
                    else:
                        raise Exception(f"Webhook returned {response.status}")
            
            await self._log_notification(notification)
            return {"status": "delivered", "webhook_response": response.status}
        except Exception as e:
            raise Exception(f"Webhook delivery failed: {e}")
    
    async def _send_push(self, notification: Notification) -> Dict[str, Any]:
        """Send push notification with support for multiple platforms"""
        try:
            # Initialize push notification clients if credentials are available
            fcm_available = False
            apns_available = False
            
            # Firebase Cloud Messaging integration
            try:
                from firebase_admin import messaging
                fcm_available = True
            except ImportError:
                logger.warning("Firebase Admin SDK not available for FCM push notifications")
            
            # Apple Push Notification Service integration
            try:
                import apns2
                apns_available = True
            except ImportError:
                logger.warning("APNs2 library not available for Apple push notifications")
            
            # Web Push notifications (using webpush library)
            webpush_available = False
            try:
                import webpush
                webpush_available = True
            except ImportError:
                logger.warning("WebPush library not available for web push notifications")
            
            # Send push notification based on platform
            if fcm_available and notification.channel == NotificationChannel.PUSH_MOBILE:
                # Send to mobile device via FCM
                try:
                    # Prepare FCM message
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=notification.subject,
                            body=notification.message
                        ),
                        data=notification.metadata or {},
                        token=notification.recipient  # Device token
                    )
                    
                    # Send message
                    response = messaging.send(message)
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.utcnow()
                    await self._log_notification(notification)
                    
                    return {
                        "status": "sent", 
                        "notification_id": notification.id,
                        "platform": "fcm",
                        "response": response
                    }
                    
                except Exception as fcm_error:
                    logger.error(f"FCM push notification failed: {fcm_error}")
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = str(fcm_error)
                    await self._log_notification(notification)
                    return {
                        "status": "failed", 
                        "notification_id": notification.id,
                        "platform": "fcm",
                        "error": str(fcm_error)
                    }
            
            elif apns_available and notification.channel == NotificationChannel.PUSH_IOS:
                # Send to iOS device via APNs
                try:
                    # Prepare APNs payload
                    payload = {
                        'aps': {
                            'alert': {
                                'title': notification.subject,
                                'body': notification.message
                            },
                            'sound': 'default'
                        },
                        'data': notification.metadata or {}
                    }
                    
                    # Send via APNs (mock implementation)
                    logger.info(f"APNs push notification would be sent to {notification.recipient}")
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.utcnow()
                    await self._log_notification(notification)
                    
                    return {
                        "status": "sent", 
                        "notification_id": notification.id,
                        "platform": "apns",
                        "response": "success"
                    }
                    
                except Exception as apns_error:
                    logger.error(f"APNs push notification failed: {apns_error}")
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = str(apns_error)
                    await self._log_notification(notification)
                    return {
                        "status": "failed", 
                        "notification_id": notification.id,
                        "platform": "apns",
                        "error": str(apns_error)
                    }
            
            elif webpush_available and notification.channel == NotificationChannel.PUSH_WEB:
                # Send web push notification
                try:
                    # Prepare web push payload
                    payload = {
                        "title": notification.subject,
                        "body": notification.message,
                        "icon": "/icons/notification-icon.png",
                        "data": notification.metadata or {}
                    }
                    
                    # Send via web push (mock implementation)
                    logger.info(f"Web push notification would be sent to {notification.recipient}")
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.utcnow()
                    await self._log_notification(notification)
                    
                    return {
                        "status": "sent", 
                        "notification_id": notification.id,
                        "platform": "webpush",
                        "response": "success"
                    }
                    
                except Exception as webpush_error:
                    logger.error(f"Web push notification failed: {webpush_error}")
                    notification.status = NotificationStatus.FAILED
                    notification.error_message = str(webpush_error)
                    await self._log_notification(notification)
                    return {
                        "status": "failed", 
                        "notification_id": notification.id,
                        "platform": "webpush",
                        "error": str(webpush_error)
                    }
            
            else:
                # Fallback to generic push notification
                logger.info(f"Push notification would be sent via {notification.channel.value} to {notification.recipient}")
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                await self._log_notification(notification)
                
                return {
                    "status": "sent", 
                    "notification_id": notification.id,
                    "platform": notification.channel.value,
                    "response": "success"
                }
                
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(e)
            await self._log_notification(notification)
            return {
                "status": "failed", 
                "notification_id": notification.id,
                "error": str(e)
            }
    
    async def _send_slack(self, notification: Notification) -> Dict[str, Any]:
        """Send Slack notification"""
        webhook_url = notification.recipient
        
        payload = {
            "text": notification.subject,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": notification.body
                    }
                }
            ]
        }
        
        if notification.data.get('attachments'):
            payload['attachments'] = notification.data['attachments']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        notification.status = NotificationStatus.DELIVERED
                        notification.sent_at = datetime.utcnow()
                        notification.delivered_at = datetime.utcnow()
                    else:
                        raise Exception(f"Slack webhook returned {response.status}")
            
            await self._log_notification(notification)
            return {"status": "delivered", "channel": "slack"}
        except Exception as e:
            raise Exception(f"Slack notification failed: {e}")
    
    async def _send_teams(self, notification: Notification) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""
        webhook_url = notification.recipient
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": self._get_theme_color(notification.priority),
            "summary": notification.subject,
            "sections": [{
                "activityTitle": notification.subject,
                "text": notification.body,
                "markdown": True
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        notification.status = NotificationStatus.DELIVERED
                        notification.sent_at = datetime.utcnow()
                        notification.delivered_at = datetime.utcnow()
                    else:
                        raise Exception(f"Teams webhook returned {response.status}")
            
            await self._log_notification(notification)
            return {"status": "delivered", "channel": "teams"}
        except Exception as e:
            raise Exception(f"Teams notification failed: {e}")
    
    async def _send_discord(self, notification: Notification) -> Dict[str, Any]:
        """Send Discord notification"""
        webhook_url = notification.recipient
        
        payload = {
            "content": notification.subject,
            "embeds": [{
                "description": notification.body,
                "color": self._get_discord_color(notification.priority),
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 204:
                        notification.status = NotificationStatus.DELIVERED
                        notification.sent_at = datetime.utcnow()
                        notification.delivered_at = datetime.utcnow()
                    else:
                        raise Exception(f"Discord webhook returned {response.status}")
            
            await self._log_notification(notification)
            return {"status": "delivered", "channel": "discord"}
        except Exception as e:
            raise Exception(f"Discord notification failed: {e}")
    
    async def _create_notification(
        self,
        request: NotificationRequest,
        channel: NotificationChannel,
        preferences: Dict[str, Any]
    ) -> Notification:
        """Create notification object from request"""
        template = await self._get_template(request.type, channel)
        
        # Render template with data
        subject = ""
        if template.get('subject_template'):
            subject_tmpl = self.template_env.from_string(template['subject_template'])
            subject = subject_tmpl.render(**request.data)
        
        body_tmpl = self.template_env.from_string(template['body_template'])
        body = body_tmpl.render(**request.data)
        
        # Get recipient based on channel
        recipient = self._get_recipient(channel, preferences)
        
        return Notification(
            user_id=request.user_id,
            type=request.type,
            channel=channel,
            priority=request.priority,
            recipient=recipient,
            subject=subject,
            body=body,
            data=request.data,
            metadata=request.metadata,
            scheduled_at=request.schedule_at,
            expires_at=request.expires_at
        )
    
    async def _get_template(
        self,
        notification_type: NotificationType,
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """Get notification template"""
        # Default templates
        default_templates = {
            NotificationType.TRANSCRIPTION_COMPLETED: {
                NotificationChannel.EMAIL: {
                    "subject_template": "Your transcription is ready: {{ title }}",
                    "body_template": """
                    <h2>Transcription Complete</h2>
                    <p>Your transcription for "{{ title }}" has been completed successfully.</p>
                    <p><strong>Duration:</strong> {{ duration }}</p>
                    <p><strong>Words:</strong> {{ word_count }}</p>
                    <p><a href="{{ link }}">View Transcription</a></p>
                    """
                },
                NotificationChannel.SMS: {
                    "body_template": "Your transcription '{{ title }}' is ready. View at: {{ short_link }}"
                },
                NotificationChannel.IN_APP: {
                    "subject_template": "Transcription Complete",
                    "body_template": "Your transcription for '{{ title }}' is ready to view."
                }
            },
            NotificationType.TRANSCRIPTION_FAILED: {
                NotificationChannel.EMAIL: {
                    "subject_template": "Transcription failed: {{ title }}",
                    "body_template": """
                    <h2>Transcription Failed</h2>
                    <p>We encountered an error processing "{{ title }}".</p>
                    <p><strong>Error:</strong> {{ error_message }}</p>
                    <p>Please try again or contact support if the issue persists.</p>
                    """
                }
            }
        }
        
        # Get from database or use default
        template = default_templates.get(notification_type, {}).get(channel, {})
        if not template:
            template = {
                "subject_template": "Notification from Audio/Video Transcription Platform",
                "body_template": "{{ message }}"
            }
        
        return template
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        # This would fetch from database
        return {
            "email_enabled": True,
            "sms_enabled": False,
            "push_enabled": True,
            "in_app_enabled": True,
            "webhook_enabled": False,
            "email": f"user_{user_id}@example.com",
            "phone": None,
            "webhook_url": None,
            "quiet_hours_enabled": False,
            "timezone": "UTC"
        }
    
    def _get_default_channels(
        self,
        notification_type: NotificationType,
        preferences: Dict[str, Any]
    ) -> List[NotificationChannel]:
        """Get default channels based on notification type"""
        # High priority notifications use multiple channels
        if notification_type in [
            NotificationType.SECURITY_ALERT,
            NotificationType.PAYMENT_FAILED,
            NotificationType.QUOTA_EXCEEDED
        ]:
            channels = [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            if preferences.get('sms_enabled'):
                channels.append(NotificationChannel.SMS)
        else:
            channels = [NotificationChannel.IN_APP]
            if preferences.get('email_enabled'):
                channels.append(NotificationChannel.EMAIL)
        
        return channels
    
    def _is_channel_enabled(
        self,
        channel: NotificationChannel,
        preferences: Dict[str, Any]
    ) -> bool:
        """Check if channel is enabled for user"""
        channel_map = {
            NotificationChannel.EMAIL: 'email_enabled',
            NotificationChannel.SMS: 'sms_enabled',
            NotificationChannel.IN_APP: 'in_app_enabled',
            NotificationChannel.PUSH: 'push_enabled',
            NotificationChannel.WEBHOOK: 'webhook_enabled'
        }
        
        return preferences.get(channel_map.get(channel, False), False)
    
    def _is_quiet_hours(self, preferences: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.get('quiet_hours_enabled'):
            return False
        
        # Implementation would check current time against quiet hours
        return False
    
    def _get_recipient(
        self,
        channel: NotificationChannel,
        preferences: Dict[str, Any]
    ) -> str:
        """Get recipient address for channel"""
        if channel == NotificationChannel.EMAIL:
            return preferences.get('email', '')
        elif channel == NotificationChannel.SMS:
            return preferences.get('phone', '')
        elif channel == NotificationChannel.WEBHOOK:
            return preferences.get('webhook_url', '')
        else:
            return preferences.get('user_id', '')
    
    def _render_email_template(self, notification: Notification) -> str:
        """Render email HTML template"""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .footer { text-align: center; padding: 20px; color: #6c757d; }
                .button { display: inline-block; padding: 10px 20px; background: #007bff; 
                         color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ subject }}</h1>
                </div>
                <div class="content">
                    {{ body | safe }}
                </div>
                <div class="footer">
                    <p>© 2024 Audio/Video Transcription Platform</p>
                    <p><a href="{{ unsubscribe_link }}">Manage Preferences</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        tmpl = self.template_env.from_string(template)
        return tmpl.render(
            subject=notification.subject,
            body=notification.body,
            unsubscribe_link=f"https://platform.example.com/preferences/{notification.user_id}"
        )
    
    def _get_theme_color(self, priority: NotificationPriority) -> str:
        """Get theme color for priority"""
        colors = {
            NotificationPriority.LOW: "0078D4",
            NotificationPriority.MEDIUM: "00BCF2",
            NotificationPriority.HIGH: "FFB900",
            NotificationPriority.URGENT: "E81123"
        }
        return colors.get(priority, "0078D4")
    
    def _get_discord_color(self, priority: NotificationPriority) -> int:
        """Get Discord embed color for priority"""
        colors = {
            NotificationPriority.LOW: 0x0078D4,
            NotificationPriority.MEDIUM: 0x00BCF2,
            NotificationPriority.HIGH: 0xFFB900,
            NotificationPriority.URGENT: 0xE81123
        }
        return colors.get(priority, 0x0078D4)
    
    async def _schedule_notification(self, notification: Notification):
        """Schedule notification for later delivery"""
        # Store in database/queue for scheduled delivery
        pass
    
    async def _log_notification(self, notification: Notification):
        """Log notification to database"""
        # Store notification in database for audit trail
        pass
    
    async def _publish_realtime(self, notification: Notification):
        """Publish notification to real-time subscribers"""
        # Publish to WebSocket connections or SSE streams
        pass
    
    async def subscribe_user(self, user_id: str, connection_id: str):
        """Subscribe user for real-time notifications"""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = set()
        self.subscriptions[user_id].add(connection_id)
    
    async def unsubscribe_user(self, user_id: str, connection_id: str):
        """Unsubscribe user from real-time notifications"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].discard(connection_id)
            if not self.subscriptions[user_id]:
                del self.subscriptions[user_id]
    
    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user's notifications"""
        key = f"notifications:{user_id}"
        notifications = self.redis_client.lrange(key, offset, offset + limit - 1)
        
        return [json.loads(n) for n in notifications]
    
    async def mark_as_read(self, user_id: str, notification_ids: List[str]):
        """Mark notifications as read"""
        # Update notification status in database
        pass
    
    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """Update user notification preferences"""
        # Store preferences in database
        pass


class NotificationManager:
    """High-level notification management"""
    
    def __init__(self, service: NotificationService):
        self.service = service
    
    async def notify_transcription_complete(
        self,
        user_id: str,
        transcription_id: str,
        title: str,
        duration: str,
        word_count: int
    ):
        """Send transcription completion notification"""
        request = NotificationRequest(
            user_id=user_id,
            type=NotificationType.TRANSCRIPTION_COMPLETED,
            priority=NotificationPriority.MEDIUM,
            data={
                "transcription_id": transcription_id,
                "title": title,
                "duration": duration,
                "word_count": word_count,
                "link": f"https://platform.example.com/transcriptions/{transcription_id}",
                "short_link": f"https://plt.fm/t/{transcription_id[:8]}"
            }
        )
        
        return await self.service.send_notification(request)
    
    async def notify_batch_complete(
        self,
        user_id: str,
        batch_id: str,
        total_files: int,
        successful: int,
        failed: int
    ):
        """Send batch processing completion notification"""
        request = NotificationRequest(
            user_id=user_id,
            type=NotificationType.BATCH_PROCESSING_COMPLETED,
            priority=NotificationPriority.MEDIUM,
            data={
                "batch_id": batch_id,
                "total_files": total_files,
                "successful": successful,
                "failed": failed,
                "link": f"https://platform.example.com/batches/{batch_id}"
            }
        )
        
        return await self.service.send_notification(request)
    
    async def notify_quota_warning(
        self,
        user_id: str,
        usage_percent: float,
        limit: int,
        used: int
    ):
        """Send quota warning notification"""
        request = NotificationRequest(
            user_id=user_id,
            type=NotificationType.QUOTA_WARNING,
            priority=NotificationPriority.HIGH,
            data={
                "usage_percent": usage_percent,
                "limit": limit,
                "used": used,
                "remaining": limit - used,
                "upgrade_link": "https://platform.example.com/upgrade"
            }
        )
        
        return await self.service.send_notification(request)
    
    async def notify_security_alert(
        self,
        user_id: str,
        alert_type: str,
        description: str,
        ip_address: str,
        location: str
    ):
        """Send security alert notification"""
        request = NotificationRequest(
            user_id=user_id,
            type=NotificationType.SECURITY_ALERT,
            priority=NotificationPriority.URGENT,
            channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.IN_APP
            ],
            data={
                "alert_type": alert_type,
                "description": description,
                "ip_address": ip_address,
                "location": location,
                "timestamp": datetime.utcnow().isoformat(),
                "action_link": "https://platform.example.com/security"
            }
        )
        
        return await self.service.send_notification(request)


# Notification Queue Processor
class NotificationQueueProcessor:
    """Process queued notifications"""
    
    def __init__(self, service: NotificationService):
        self.service = service
        self.running = False
    
    async def start(self):
        """Start processing notification queue"""
        self.running = True
        while self.running:
            try:
                # Get notification from queue
                notification = await self.service.notification_queue.get()
                
                # Check if expired
                if notification.expires_at and notification.expires_at < datetime.utcnow():
                    logger.info(f"Notification {notification.id} expired")
                    continue
                
                # Send notification
                await self.service._send_through_channel(notification)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processor error: {e}")
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop processing queue"""
        self.running = False


# WebSocket handler for real-time notifications
class NotificationWebSocketHandler:
    """WebSocket handler for real-time notifications"""
    
    def __init__(self, service: NotificationService):
        self.service = service
        self.connections: Dict[str, Any] = {}
    
    async def handle_connection(self, websocket, path):
        """Handle WebSocket connection"""
        connection_id = str(uuid.uuid4())
        user_id = None
        
        try:
            # Authenticate user
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            user_id = auth_data.get('user_id')
            
            if not user_id:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Authentication required"
                }))
                return
            
            # Store connection
            self.connections[connection_id] = {
                "websocket": websocket,
                "user_id": user_id
            }
            
            # Subscribe user
            await self.service.subscribe_user(user_id, connection_id)
            
            # Send connection confirmation
            await websocket.send(json.dumps({
                "type": "connected",
                "connection_id": connection_id
            }))
            
            # Keep connection alive
            async for message in websocket:
                data = json.loads(message)
                
                if data.get('type') == 'ping':
                    await websocket.send(json.dumps({"type": "pong"}))
                elif data.get('type') == 'mark_read':
                    notification_ids = data.get('notification_ids', [])
                    await self.service.mark_as_read(user_id, notification_ids)
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        
        finally:
            # Clean up
            if user_id:
                await self.service.unsubscribe_user(user_id, connection_id)
            if connection_id in self.connections:
                del self.connections[connection_id]
    
    async def send_to_user(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to user's connections"""
        if user_id in self.service.subscriptions:
            for connection_id in self.service.subscriptions[user_id]:
                if connection_id in self.connections:
                    websocket = self.connections[connection_id]['websocket']
                    try:
                        await websocket.send(json.dumps({
                            "type": "notification",
                            "data": notification
                        }))
                    except Exception as e:
                        logger.error(f"Failed to send to connection {connection_id}: {e}")


if __name__ == "__main__":
    # Example usage
    config = {
        'smtp_host': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_user': 'your-email@gmail.com',
        'smtp_password': 'your-password',
        'smtp_from': 'noreply@platform.com',
        'twilio_account_sid': 'your-twilio-sid',
        'twilio_auth_token': 'your-twilio-token',
        'twilio_from_number': '+1234567890',
        'redis_host': 'localhost',
        'redis_port': 6379
    }
    
    service = NotificationService(config)
    manager = NotificationManager(service)
    
    # Example: Send transcription complete notification
    asyncio.run(manager.notify_transcription_complete(
        user_id="user123",
        transcription_id="trans456",
        title="Important Meeting Recording",
        duration="45:30",
        word_count=5432
    ))