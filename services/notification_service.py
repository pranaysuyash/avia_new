"""
Notification Service
Adapter for the comprehensive notification system
"""

from notification_system import NotificationService as ComprehensiveNotificationService
from notification_system import NotificationType, NotificationChannel
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service adapter for support ticket notifications
    Provides the interface expected by support_service.py
    """
    
    def __init__(self, db=None):
        """Initialize notification service with database connection"""
        self.db = db
        
        # Initialize the comprehensive notification service
        # Using basic configuration for now
        config = {
            'smtp_host': 'localhost',
            'smtp_port': 587,
            'smtp_user': None,
            'smtp_password': None,
        }
        self.notification_service = ComprehensiveNotificationService(config)
    
    async def send_notification(self, user_id: int, title: str, message: str, 
                               notification_type: str = "support_ticket", **kwargs):
        """
        Send notification to a specific user
        
        Args:
            user_id: ID of the user to notify
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            **kwargs: Additional notification parameters
        """
        try:
            # Create notification data
            notification_data = {
                'user_id': user_id,
                'title': title,
                'message': message,
                'type': notification_type,
                'channels': [NotificationChannel.IN_APP],  # Default to in-app
                **kwargs
            }
            
            # Send via comprehensive notification service
            await self.notification_service.send_notification(
                notification_type=NotificationType.COLLABORATION_UPDATE,  # Generic type
                user_id=user_id,
                data=notification_data
            )
            
            logger.info(f"Sent notification to user {user_id}: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
    
    async def notify_team(self, team: str, title: str, message: str, **kwargs):
        """
        Send notification to a team
        
        Args:
            team: Team identifier (e.g., "support_managers")
            title: Notification title
            message: Notification message
            **kwargs: Additional notification parameters
        """
        try:
            # For now, log the team notification
            # In a full implementation, this would look up team members and notify them
            logger.info(f"Team notification for {team}: {title} - {message}")
            
            # TODO: Implement actual team lookup and notification
            # This would involve:
            # 1. Query database for team members
            # 2. Send individual notifications to each member
            
        except Exception as e:
            logger.error(f"Failed to notify team {team}: {e}")
    
    async def send_email_notification(self, email: str, title: str, message: str, **kwargs):
        """
        Send email notification
        
        Args:
            email: Recipient email address
            title: Email subject
            message: Email content
            **kwargs: Additional email parameters
        """
        try:
            # Use comprehensive notification service for email
            notification_data = {
                'email': email,
                'subject': title,
                'message': message,
                **kwargs
            }
            
            await self.notification_service.send_email(
                to_email=email,
                subject=title,
                content=message
            )
            
            logger.info(f"Sent email notification to {email}: {title}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")