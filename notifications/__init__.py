"""
Enhanced Notification System

A comprehensive multi-channel notification system supporting:
- Email notifications with HTML templates
- SMS notifications via Twilio
- Webhook notifications for external integrations
- In-app real-time notifications via Redis
- Third-party integrations (Slack, Teams, Discord)
"""

# Original notification system for database-backed notifications
from .notification_manager import NotificationManager
from .notification_ui import (
    render_notification_bell,
    render_notification_panel,
    render_notification_preferences,
    get_unread_count,
    render_enhanced_notification_settings,
    render_test_notifications,
    render_notification_dashboard
)

# Enhanced notification system with multi-channel support
from .enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationConfig,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationTemplate
)

# API wrapper for easy integration
from . import api

__version__ = "1.0.0"

__all__ = [
    # Original system
    'NotificationManager',
    'render_notification_bell',
    'render_notification_panel',
    'render_notification_preferences',
    'get_unread_count',
    'render_enhanced_notification_settings',
    'render_test_notifications',
    'render_notification_dashboard',
    
    # Enhanced system
    "EnhancedNotificationManager",
    "NotificationRequest",
    "NotificationConfig",
    "NotificationType",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationTemplate",
    "api"
]