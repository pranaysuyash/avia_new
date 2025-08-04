"""
Enhanced Notification Manager with Email, SMS, Webhook, and Push Notification Support
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import boto3
from twilio.rest import Client as TwilioClient
from jinja2 import Template
import redis
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from sqlalchemy.orm import Session

from database.models import User, Notification
from database_config import get_db

# Configure logging
logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Types of notifications"""
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_STARTED = "processing_started"
    SYSTEM_UPDATE = "system_update"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    USAGE_LIMIT_WARNING = "usage_limit_warning"
    TEAM_INVITATION = "team_invitation"
    SHARE_NOTIFICATION = "share_notification"
    CRITICAL_ALERT = "critical_alert"
    BATCH_COMPLETE = "batch_complete"
    TRANSCRIPT_READY = "transcript_ready"
    EXPORT_READY = "export_ready"

class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"

class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationTemplate(BaseModel):
    """Notification template model"""
    type: NotificationType
    channel: NotificationChannel
    subject: Optional[str] = None
    template: str
    variables: List[str] = []

class NotificationRequest(BaseModel):
    """Notification request model"""
    user_id: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    channels: Optional[List[NotificationChannel]] = None
    data: Dict[str, Any] = {}
    retry_count: int = 3
    schedule_time: Optional[datetime] = None

class NotificationConfig(BaseModel):
    """Notification configuration"""
    # Email settings
    smtp_host: str = Field(default_factory=lambda: os.getenv("SMTP_HOST", "smtp.gmail.com"))
    smtp_port: int = Field(default_factory=lambda: int(os.getenv("SMTP_PORT", "587")))
    smtp_username: str = Field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    smtp_password: str = Field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    email_from: str = Field(default_factory=lambda: os.getenv("EMAIL_FROM", "noreply@transcription-platform.com"))
    email_from_name: str = Field(default_factory=lambda: os.getenv("EMAIL_FROM_NAME", "Transcription Platform"))
    
    # SMS settings (Twilio)
    twilio_account_sid: str = Field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = Field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
    twilio_phone_number: str = Field(default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", ""))
    
    # AWS SNS settings
    aws_access_key_id: str = Field(default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID", ""))
    aws_secret_access_key: str = Field(default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY", ""))
    aws_region: str = Field(default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"))
    
    # Redis settings for in-app notifications
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    
    # Webhook settings
    webhook_timeout: int = 30
    webhook_retry_delay: int = 5

class EnhancedNotificationManager:
    """Enhanced notification manager with multi-channel support"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self.redis_client = None
        self.templates = self._load_templates()
        
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(self.config.redis_url)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize SMS clients
        if self.config.twilio_account_sid and self.config.twilio_auth_token:
            try:
                self.twilio_client = TwilioClient(
                    self.config.twilio_account_sid,
                    self.config.twilio_auth_token
                )
            except Exception as e:
                logger.warning(f"Twilio initialization failed: {e}")
                self.twilio_client = None
        else:
            self.twilio_client = None
            
        # Initialize AWS SNS client
        if self.config.aws_access_key_id and self.config.aws_secret_access_key:
            try:
                self.sns_client = boto3.client(
                    'sns',
                    aws_access_key_id=self.config.aws_access_key_id,
                    aws_secret_access_key=self.config.aws_secret_access_key,
                    region_name=self.config.aws_region
                )
            except Exception as e:
                logger.warning(f"AWS SNS initialization failed: {e}")
                self.sns_client = None
        else:
            self.sns_client = None
    
    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        templates = {
            # Email templates
            f"{NotificationType.PROCESSING_COMPLETE}_{NotificationChannel.EMAIL}": NotificationTemplate(
                type=NotificationType.PROCESSING_COMPLETE,
                channel=NotificationChannel.EMAIL,
                subject="Your transcription is ready!",
                template="""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #333;">Transcription Complete</h2>
                            <p>Hi {{user_name}},</p>
                            <p>Your transcription for <strong>{{file_name}}</strong> has been completed successfully.</p>
                            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #555; margin-top: 0;">Details:</h3>
                                <ul style="list-style: none; padding: 0;">
                                    <li>📄 <strong>File:</strong> {{file_name}}</li>
                                    <li>⏱️ <strong>Duration:</strong> {{duration}} seconds</li>
                                    <li>🌐 <strong>Language:</strong> {{language}}</li>
                                    <li>👥 <strong>Speakers detected:</strong> {{speaker_count}}</li>
                                    <li>⚡ <strong>Processing time:</strong> {{processing_time}} seconds</li>
                                </ul>
                            </div>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{transcript_url}}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Transcript</a>
                            </div>
                            <p style="color: #666; font-size: 14px;">Best regards,<br>The Transcription Platform Team</p>
                        </div>
                    </body>
                    </html>
                """,
                variables=["user_name", "file_name", "duration", "language", "speaker_count", "processing_time", "transcript_url"]
            ),
            
            # SMS templates
            f"{NotificationType.PROCESSING_COMPLETE}_{NotificationChannel.SMS}": NotificationTemplate(
                type=NotificationType.PROCESSING_COMPLETE,
                channel=NotificationChannel.SMS,
                template="Your transcription for {{file_name}} is ready! View it at: {{short_url}}",
                variables=["file_name", "short_url"]
            ),
            
            # Webhook templates
            f"{NotificationType.PROCESSING_COMPLETE}_{NotificationChannel.WEBHOOK}": NotificationTemplate(
                type=NotificationType.PROCESSING_COMPLETE,
                channel=NotificationChannel.WEBHOOK,
                template=json.dumps({
                    "event": "transcription.completed",
                    "timestamp": "{{timestamp}}",
                    "data": {
                        "transcript_id": "{{transcript_id}}",
                        "file_name": "{{file_name}}",
                        "duration": "{{duration}}",
                        "language": "{{language}}",
                        "status": "completed",
                        "download_url": "{{download_url}}"
                    }
                }),
                variables=["timestamp", "transcript_id", "file_name", "duration", "language", "download_url"]
            ),
            
            # In-app notification templates
            f"{NotificationType.PROCESSING_COMPLETE}_{NotificationChannel.IN_APP}": NotificationTemplate(
                type=NotificationType.PROCESSING_COMPLETE,
                channel=NotificationChannel.IN_APP,
                template=json.dumps({
                    "title": "Transcription Complete",
                    "message": "Your transcription for {{file_name}} is ready!",
                    "icon": "success",
                    "action": {
                        "label": "View Transcript",
                        "url": "{{transcript_url}}"
                    }
                }),
                variables=["file_name", "transcript_url"]
            ),
            
            # Processing failed templates
            f"{NotificationType.PROCESSING_FAILED}_{NotificationChannel.EMAIL}": NotificationTemplate(
                type=NotificationType.PROCESSING_FAILED,
                channel=NotificationChannel.EMAIL,
                subject="Transcription processing failed",
                template="""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #dc3545;">Processing Failed</h2>
                            <p>Hi {{user_name}},</p>
                            <p>Unfortunately, we encountered an error while processing your file <strong>{{file_name}}</strong>.</p>
                            <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <strong>Error details:</strong>
                                <p style="margin: 10px 0;">{{error_message}}</p>
                            </div>
                            <p>Please try again or contact support if the issue persists.</p>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{support_url}}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Contact Support</a>
                            </div>
                            <p style="color: #666; font-size: 14px;">Best regards,<br>The Transcription Platform Team</p>
                        </div>
                    </body>
                    </html>
                """,
                variables=["user_name", "file_name", "error_message", "support_url"]
            ),
            
            # Usage limit warning templates
            f"{NotificationType.USAGE_LIMIT_WARNING}_{NotificationChannel.EMAIL}": NotificationTemplate(
                type=NotificationType.USAGE_LIMIT_WARNING,
                channel=NotificationChannel.EMAIL,
                subject="Usage limit warning - {{usage_percentage}}% used",
                template="""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #ff6b6b;">Usage Limit Warning</h2>
                            <p>Hi {{user_name}},</p>
                            <p>You've used <strong>{{usage_percentage}}%</strong> of your monthly quota.</p>
                            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #856404; margin-top: 0;">Current Usage</h3>
                                <div style="background-color: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden;">
                                    <div style="background-color: #ffc107; height: 100%; width: {{usage_percentage}}%;"></div>
                                </div>
                                <p style="margin-top: 10px;"><strong>{{current_usage}}</strong> / {{limit}} {{unit}}</p>
                            </div>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{upgrade_url}}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">Upgrade Plan</a>
                            </div>
                            <p style="color: #666; font-size: 14px;">Best regards,<br>The Transcription Platform Team</p>
                        </div>
                    </body>
                    </html>
                """,
                variables=["user_name", "usage_percentage", "current_usage", "limit", "unit", "upgrade_url"]
            ),
            
            # Batch complete templates
            f"{NotificationType.BATCH_COMPLETE}_{NotificationChannel.EMAIL}": NotificationTemplate(
                type=NotificationType.BATCH_COMPLETE,
                channel=NotificationChannel.EMAIL,
                subject="Batch processing complete - {{total_files}} files",
                template="""
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #28a745;">Batch Processing Complete</h2>
                            <p>Hi {{user_name}},</p>
                            <p>Your batch processing job has been completed.</p>
                            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 20px 0;">
                                <h3 style="color: #555; margin-top: 0;">Summary:</h3>
                                <ul style="list-style: none; padding: 0;">
                                    <li>📁 <strong>Total files:</strong> {{total_files}}</li>
                                    <li>✅ <strong>Successful:</strong> {{successful_files}}</li>
                                    <li>❌ <strong>Failed:</strong> {{failed_files}}</li>
                                    <li>⏱️ <strong>Total duration:</strong> {{total_duration}}</li>
                                </ul>
                            </div>
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{{batch_results_url}}" style="background-color: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">View Results</a>
                            </div>
                            <p style="color: #666; font-size: 14px;">Best regards,<br>The Transcription Platform Team</p>
                        </div>
                    </body>
                    </html>
                """,
                variables=["user_name", "total_files", "successful_files", "failed_files", "total_duration", "batch_results_url"]
            ),
        }
        
        return templates
    
    async def send_notification(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send notification through specified channels"""
        results = {}
        
        # Get user preferences
        user_prefs = await self._get_user_preferences(request.user_id)
        
        # Determine channels to use
        channels = request.channels or self._get_default_channels(request.type, request.priority)
        
        # Filter channels based on user preferences
        channels = [ch for ch in channels if user_prefs.get(ch, True)]
        
        # Send through each channel
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                tasks.append(self._send_email(request))
            elif channel == NotificationChannel.SMS:
                tasks.append(self._send_sms(request))
            elif channel == NotificationChannel.WEBHOOK:
                tasks.append(self._send_webhook(request))
            elif channel == NotificationChannel.IN_APP:
                tasks.append(self._send_in_app(request))
            elif channel == NotificationChannel.SLACK:
                tasks.append(self._send_slack(request))
            elif channel == NotificationChannel.TEAMS:
                tasks.append(self._send_teams(request))
            elif channel == NotificationChannel.DISCORD:
                tasks.append(self._send_discord(request))
        
        # Execute all notifications concurrently
        if tasks:
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            for i, channel in enumerate(channels):
                if isinstance(results_list[i], Exception):
                    results[channel] = {"status": "error", "message": str(results_list[i])}
                else:
                    results[channel] = results_list[i]
                    # Log notification
                    await self._log_notification(request, channel, results[channel])
        
        return results
    
    async def _send_email(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Get user email
            user = await self._get_user(request.user_id)
            if not user or not user.email:
                return {"status": "error", "message": "User email not found"}
            
            # Get template
            template_key = f"{request.type}_{NotificationChannel.EMAIL}"
            template = self.templates.get(template_key)
            if not template:
                return {"status": "error", "message": "Template not found"}
            
            # Render template
            subject = Template(template.subject).render(**request.data) if template.subject else "Notification"
            body = Template(template.template).render(**request.data)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.config.email_from_name, self.config.email_from))
            msg['To'] = user.email
            
            # Add HTML part
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            return {"status": "success", "message": "Email sent successfully"}
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_sms(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            if not self.twilio_client:
                return {"status": "error", "message": "SMS service not configured"}
            
            # Get user phone
            user = await self._get_user(request.user_id)
            if not user or not hasattr(user, 'phone_number') or not user.phone_number:
                return {"status": "error", "message": "User phone number not found"}
            
            # Get template
            template_key = f"{request.type}_{NotificationChannel.SMS}"
            template = self.templates.get(template_key)
            if not template:
                return {"status": "error", "message": "Template not found"}
            
            # Render template
            message = Template(template.template).render(**request.data)
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.config.twilio_phone_number,
                to=user.phone_number
            )
            
            return {"status": "success", "message": "SMS sent successfully", "sid": message.sid}
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_webhook(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            # Get user webhook URL
            user = await self._get_user(request.user_id)
            webhook_url = getattr(user, 'webhook_url', None)
            
            if not webhook_url:
                return {"status": "error", "message": "Webhook URL not configured"}
            
            # Get template
            template_key = f"{request.type}_{NotificationChannel.WEBHOOK}"
            template = self.templates.get(template_key)
            if not template:
                return {"status": "error", "message": "Template not found"}
            
            # Render payload
            payload_str = Template(template.template).render(**request.data)
            payload = json.loads(payload_str)
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.webhook_timeout)
                ) as response:
                    if response.status == 200:
                        return {"status": "success", "message": "Webhook sent successfully"}
                    else:
                        return {
                            "status": "error",
                            "message": f"Webhook failed with status {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"Webhook send error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_in_app(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            if not self.redis_client:
                return {"status": "error", "message": "Redis not available"}
            
            # Get template
            template_key = f"{request.type}_{NotificationChannel.IN_APP}"
            template = self.templates.get(template_key)
            if not template:
                return {"status": "error", "message": "Template not found"}
            
            # Render notification
            notification_str = Template(template.template).render(**request.data)
            notification = json.loads(notification_str)
            
            # Add metadata
            notification.update({
                "id": f"notif_{datetime.utcnow().timestamp()}",
                "user_id": request.user_id,
                "type": request.type,
                "priority": request.priority,
                "timestamp": datetime.utcnow().isoformat(),
                "read": False
            })
            
            # Store in Redis
            key = f"notifications:{request.user_id}"
            self.redis_client.lpush(key, json.dumps(notification))
            self.redis_client.ltrim(key, 0, 99)  # Keep last 100 notifications
            
            # Publish to WebSocket channel
            channel = f"user:{request.user_id}:notifications"
            self.redis_client.publish(channel, json.dumps(notification))
            
            return {"status": "success", "message": "In-app notification sent"}
            
        except Exception as e:
            logger.error(f"In-app notification error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_slack(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            # Get user's Slack webhook URL
            user = await self._get_user(request.user_id)
            slack_webhook = getattr(user, 'slack_webhook_url', None)
            
            if not slack_webhook:
                return {"status": "error", "message": "Slack webhook not configured"}
            
            # Build Slack message
            message = {
                "text": f"Notification: {request.type}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self._format_slack_message(request)
                        }
                    }
                ]
            }
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook, json=message) as response:
                    if response.status == 200:
                        return {"status": "success", "message": "Slack notification sent"}
                    else:
                        return {"status": "error", "message": f"Slack API error: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_teams(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""
        try:
            # Get user's Teams webhook URL
            user = await self._get_user(request.user_id)
            teams_webhook = getattr(user, 'teams_webhook_url', None)
            
            if not teams_webhook:
                return {"status": "error", "message": "Teams webhook not configured"}
            
            # Build Teams message card
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "themeColor": self._get_theme_color(request.priority),
                "summary": f"Notification: {request.type}",
                "sections": [{
                    "activityTitle": "Transcription Platform Notification",
                    "facts": self._format_teams_facts(request),
                    "markdown": True
                }]
            }
            
            # Send to Teams
            async with aiohttp.ClientSession() as session:
                async with session.post(teams_webhook, json=card) as response:
                    if response.status == 200:
                        return {"status": "success", "message": "Teams notification sent"}
                    else:
                        return {"status": "error", "message": f"Teams API error: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Teams notification error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _send_discord(self, request: NotificationRequest) -> Dict[str, Any]:
        """Send Discord notification"""
        try:
            # Get user's Discord webhook URL
            user = await self._get_user(request.user_id)
            discord_webhook = getattr(user, 'discord_webhook_url', None)
            
            if not discord_webhook:
                return {"status": "error", "message": "Discord webhook not configured"}
            
            # Build Discord embed
            embed = {
                "embeds": [{
                    "title": f"Notification: {request.type.value.replace('_', ' ').title()}",
                    "description": self._format_discord_message(request),
                    "color": self._get_discord_color(request.priority),
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "Transcription Platform"
                    }
                }]
            }
            
            # Send to Discord
            async with aiohttp.ClientSession() as session:
                async with session.post(discord_webhook, json=embed) as response:
                    if response.status == 204:
                        return {"status": "success", "message": "Discord notification sent"}
                    else:
                        return {"status": "error", "message": f"Discord API error: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's in-app notifications"""
        try:
            if not self.redis_client:
                return []
            
            key = f"notifications:{user_id}"
            notifications = self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(n) for n in notifications]
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    async def mark_notification_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            if not self.redis_client:
                return False
            
            key = f"notifications:{user_id}"
            notifications = self.redis_client.lrange(key, 0, -1)
            
            for i, notif_str in enumerate(notifications):
                notif = json.loads(notif_str)
                if notif.get('id') == notification_id:
                    notif['read'] = True
                    self.redis_client.lset(key, i, json.dumps(notif))
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[NotificationChannel, bool]
    ) -> bool:
        """Update user notification preferences"""
        try:
            db = next(get_db())
            
            # This would typically update a NotificationPreference table
            # For now, store in user's metadata or settings
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                # Store preferences in user's settings or metadata field
                # user.notification_preferences = preferences
                db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False
        finally:
            db.close()
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user from database"""
        try:
            db = next(get_db())
            return db.query(User).filter_by(id=user_id).first()
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
        finally:
            db.close()
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, bool]:
        """Get user notification preferences"""
        try:
            db = next(get_db())
            # This would typically query a NotificationPreference table
            # For now, return default preferences
            return {
                NotificationChannel.EMAIL: True,
                NotificationChannel.SMS: False,  # Opt-in
                NotificationChannel.WEBHOOK: False,  # Opt-in
                NotificationChannel.IN_APP: True,
                NotificationChannel.PUSH: True,
                NotificationChannel.SLACK: False,  # Opt-in
                NotificationChannel.TEAMS: False,  # Opt-in
                NotificationChannel.DISCORD: False,  # Opt-in
            }
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}
        finally:
            db.close()
    
    def _get_default_channels(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority
    ) -> List[NotificationChannel]:
        """Get default channels based on notification type and priority"""
        # Critical notifications use all available channels
        if priority == NotificationPriority.CRITICAL:
            return [
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.IN_APP,
                NotificationChannel.PUSH
            ]
        
        # High priority uses email and in-app
        elif priority == NotificationPriority.HIGH:
            return [NotificationChannel.EMAIL, NotificationChannel.IN_APP]
        
        # Medium priority uses in-app
        elif priority == NotificationPriority.MEDIUM:
            return [NotificationChannel.IN_APP]
        
        # Low priority uses in-app only
        else:
            return [NotificationChannel.IN_APP]
    
    async def _log_notification(
        self,
        request: NotificationRequest,
        channel: NotificationChannel,
        result: Dict[str, Any]
    ) -> None:
        """Log notification to database"""
        try:
            db = next(get_db())
            
            # Create notification record
            notification = Notification(
                user_id=int(request.user_id) if request.user_id.isdigit() else None,
                type=request.type,
                title=f"{request.type.value.replace('_', ' ').title()}",
                message=json.dumps(request.data),
                related_type=channel,
                link=request.data.get('transcript_url', '')
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
        finally:
            db.close()
    
    def _format_slack_message(self, request: NotificationRequest) -> str:
        """Format message for Slack"""
        if request.type == NotificationType.PROCESSING_COMPLETE:
            return f"✅ *Transcription Complete*\nFile: {request.data.get('file_name', 'Unknown')}\n<{request.data.get('transcript_url', '#')}|View Transcript>"
        elif request.type == NotificationType.PROCESSING_FAILED:
            return f"❌ *Processing Failed*\nFile: {request.data.get('file_name', 'Unknown')}\nError: {request.data.get('error_message', 'Unknown error')}"
        else:
            return f"📢 *{request.type.value.replace('_', ' ').title()}*"
    
    def _format_teams_facts(self, request: NotificationRequest) -> List[Dict[str, str]]:
        """Format facts for Teams message card"""
        facts = []
        
        if request.type == NotificationType.PROCESSING_COMPLETE:
            facts = [
                {"name": "File", "value": request.data.get('file_name', 'Unknown')},
                {"name": "Duration", "value": f"{request.data.get('duration', 0)} seconds"},
                {"name": "Status", "value": "✅ Complete"}
            ]
        elif request.type == NotificationType.PROCESSING_FAILED:
            facts = [
                {"name": "File", "value": request.data.get('file_name', 'Unknown')},
                {"name": "Status", "value": "❌ Failed"},
                {"name": "Error", "value": request.data.get('error_message', 'Unknown error')}
            ]
        
        return facts
    
    def _format_discord_message(self, request: NotificationRequest) -> str:
        """Format message for Discord"""
        if request.type == NotificationType.PROCESSING_COMPLETE:
            return f"**File:** {request.data.get('file_name', 'Unknown')}\n**Status:** Complete ✅\n[View Transcript]({request.data.get('transcript_url', '#')})"
        elif request.type == NotificationType.PROCESSING_FAILED:
            return f"**File:** {request.data.get('file_name', 'Unknown')}\n**Status:** Failed ❌\n**Error:** {request.data.get('error_message', 'Unknown error')}"
        else:
            return request.data.get('message', 'New notification')
    
    def _get_theme_color(self, priority: NotificationPriority) -> str:
        """Get theme color for Teams based on priority"""
        colors = {
            NotificationPriority.LOW: "0078D4",      # Blue
            NotificationPriority.MEDIUM: "FFB900",   # Yellow
            NotificationPriority.HIGH: "FF8C00",     # Orange
            NotificationPriority.CRITICAL: "E81123"  # Red
        }
        return colors.get(priority, "0078D4")
    
    def _get_discord_color(self, priority: NotificationPriority) -> int:
        """Get color for Discord embed based on priority"""
        colors = {
            NotificationPriority.LOW: 0x0078D4,      # Blue
            NotificationPriority.MEDIUM: 0xFFB900,   # Yellow
            NotificationPriority.HIGH: 0xFF8C00,     # Orange
            NotificationPriority.CRITICAL: 0xE81123  # Red
        }
        return colors.get(priority, 0x0078D4)


# Singleton instance
enhanced_notification_manager = EnhancedNotificationManager()