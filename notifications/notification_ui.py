"""
Notification UI components for Streamlit
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from database.models import Notification, User
from .notification_manager import NotificationManager
from .enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)


def render_notification_bell(
    notification_manager: NotificationManager,
    current_user: User
) -> None:
    """Render notification bell icon with unread count"""
    unread_count = notification_manager.get_unread_count(current_user.id)
    
    # Create columns for layout
    col1, col2 = st.columns([1, 10])
    
    with col1:
        if unread_count > 0:
            # Show bell with count
            if st.button(f"🔔 {unread_count}", key="notification_bell", help=f"{unread_count} unread notifications"):
                st.session_state.show_notifications = not st.session_state.get('show_notifications', False)
        else:
            # Show empty bell
            if st.button("🔔", key="notification_bell", help="No new notifications"):
                st.session_state.show_notifications = not st.session_state.get('show_notifications', False)


def render_notification_panel(
    notification_manager: NotificationManager,
    current_user: User
) -> None:
    """Render the notification panel"""
    st.markdown("### 🔔 Notifications")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Mark All Read"):
            count = notification_manager.mark_all_as_read(current_user.id)
            if count > 0:
                st.success(f"Marked {count} notifications as read")
                st.rerun()
    
    with col2:
        show_unread_only = st.checkbox("Unread only", value=True)
    
    # Get notifications
    notifications = notification_manager.get_notifications(
        user_id=current_user.id,
        unread_only=show_unread_only,
        limit=50
    )
    
    if not notifications:
        st.info("No notifications" if show_unread_only else "No unread notifications")
        return
    
    # Display notifications
    for notification in notifications:
        render_notification_item(notification, notification_manager)


def render_notification_item(
    notification: Notification,
    notification_manager: NotificationManager
) -> None:
    """Render a single notification"""
    # Create container with styling based on read status
    container_style = "background-color: #f0f8ff;" if not notification.is_read else ""
    
    with st.container():
        if not notification.is_read:
            st.markdown(
                f'<div style="{container_style} padding: 10px; border-radius: 5px; margin: 5px 0;">',
                unsafe_allow_html=True
            )
        
        col1, col2, col3 = st.columns([1, 6, 1])
        
        with col1:
            # Icon based on type
            icon = get_notification_icon(notification.type)
            st.write(icon)
        
        with col2:
            # Title and message
            st.markdown(f"**{notification.title}**")
            st.write(notification.message)
            
            # From user and time
            from_text = f"from {notification.from_user.username}" if notification.from_user else ""
            time_text = format_notification_time(notification.created_at)
            st.caption(f"{from_text} • {time_text}")
            
            # Link button if available
            if notification.link:
                if st.button("View", key=f"view_notif_{notification.id}"):
                    # Mark as read
                    notification_manager.mark_as_read(notification.id, notification.user_id)
                    # Navigate to link (in a real app, this would be a proper navigation)
                    st.session_state.notification_link = notification.link
                    st.rerun()
        
        with col3:
            # Action buttons
            if not notification.is_read:
                if st.button("✓", key=f"read_{notification.id}", help="Mark as read"):
                    notification_manager.mark_as_read(notification.id, notification.user_id)
                    st.rerun()
            
            if st.button("🗑️", key=f"archive_{notification.id}", help="Archive"):
                notification_manager.archive_notification(notification.id, notification.user_id)
                st.rerun()
        
        if not notification.is_read:
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()


def get_notification_icon(notification_type: str) -> str:
    """Get icon for notification type"""
    icons = {
        'mention': '💬',
        'annotation_reply': '↩️',
        'transcript_edit': '✏️',
        'share_access': '🔗',
        'new_annotation': '📝',
    }
    return icons.get(notification_type, '📬')


def format_notification_time(created_at: datetime) -> str:
    """Format notification time in a friendly way"""
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 7:
        return created_at.strftime("%b %d, %Y")
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def render_notification_preferences(
    notification_manager: NotificationManager,
    current_user: User
) -> None:
    """Render notification preferences settings"""
    st.markdown("### ⚙️ Notification Preferences")
    
    preferences = notification_manager.get_notification_preferences(current_user.id)
    
    st.write("Choose which notifications you want to receive:")
    
    # Notification types
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Activity Notifications**")
        mention_pref = st.checkbox(
            "Mentions (@username)",
            value=preferences.get('mention', True),
            help="When someone mentions you with @username"
        )
        reply_pref = st.checkbox(
            "Annotation replies",
            value=preferences.get('annotation_reply', True),
            help="When someone replies to your annotations"
        )
        edit_pref = st.checkbox(
            "Transcript edits",
            value=preferences.get('transcript_edit', True),
            help="When transcripts you're involved with are edited"
        )
    
    with col2:
        st.markdown("**Sharing Notifications**")
        share_pref = st.checkbox(
            "Share access",
            value=preferences.get('share_access', True),
            help="When someone shares a transcript with you"
        )
        new_annotation_pref = st.checkbox(
            "New annotations",
            value=preferences.get('new_annotation', False),
            help="When new annotations are added (can be noisy)"
        )
        email_pref = st.checkbox(
            "Email notifications",
            value=preferences.get('email_notifications', False),
            help="Send notifications to email (coming soon)",
            disabled=True
        )
    
    # Save button
    if st.button("Save Preferences", type="primary"):
        # In a real implementation, this would save to database
        st.success("Preferences saved!")
        
        # Show what would be saved
        new_prefs = {
            'mention': mention_pref,
            'annotation_reply': reply_pref,
            'transcript_edit': edit_pref,
            'share_access': share_pref,
            'new_annotation': new_annotation_pref,
            'email_notifications': email_pref
        }
        st.json(new_prefs)


def get_unread_count(
    notification_manager: NotificationManager,
    user_id: int
) -> int:
    """Get unread notification count for a user"""
    return notification_manager.get_unread_count(user_id)


def render_notification_summary(
    notification_manager: NotificationManager,
    current_user: User
) -> None:
    """Render a summary of recent notifications"""
    unread_count = notification_manager.get_unread_count(current_user.id)
    recent_notifications = notification_manager.get_notifications(
        user_id=current_user.id,
        limit=5
    )
    
    if unread_count > 0:
        st.info(f"You have {unread_count} unread notification{'s' if unread_count > 1 else ''}")
    
    if recent_notifications:
        with st.expander("Recent Notifications", expanded=unread_count > 0):
            for notif in recent_notifications[:3]:
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.write(get_notification_icon(notif.type))
                with col2:
                    if not notif.is_read:
                        st.markdown(f"**{notif.title}**")
                    else:
                        st.write(notif.title)
                    st.caption(format_notification_time(notif.created_at))
            
            if len(recent_notifications) > 3:
                st.caption(f"... and {len(recent_notifications) - 3} more")
            
            if st.button("View All Notifications"):
                st.session_state.show_notifications = True
                st.rerun()


def render_enhanced_notification_settings():
    """Render enhanced notification settings UI"""
    st.markdown("## 🔔 Advanced Notification Settings")
    
    # Get notification manager
    notification_manager = EnhancedNotificationManager()
    
    # Channel preferences
    st.markdown("### Channel Preferences")
    st.markdown("Choose how you want to receive notifications:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Essential Notifications**")
        email_enabled = st.checkbox("📧 Email", value=True, key="notif_email")
        in_app_enabled = st.checkbox("💬 In-App", value=True, key="notif_in_app")
        push_enabled = st.checkbox("📱 Push Notifications", value=True, key="notif_push")
    
    with col2:
        st.markdown("**Instant Notifications**")
        sms_enabled = st.checkbox("📱 SMS", value=False, key="notif_sms")
        slack_enabled = st.checkbox("💼 Slack", value=False, key="notif_slack")
        teams_enabled = st.checkbox("👥 Microsoft Teams", value=False, key="notif_teams")
    
    with col3:
        st.markdown("**Developer Tools**")
        webhook_enabled = st.checkbox("🔗 Webhooks", value=False, key="notif_webhook")
        discord_enabled = st.checkbox("🎮 Discord", value=False, key="notif_discord")
    
    # Save preferences button
    if st.button("💾 Save Preferences", type="primary", key="save_prefs"):
        preferences = {
            NotificationChannel.EMAIL: email_enabled,
            NotificationChannel.SMS: sms_enabled,
            NotificationChannel.WEBHOOK: webhook_enabled,
            NotificationChannel.IN_APP: in_app_enabled,
            NotificationChannel.PUSH: push_enabled,
            NotificationChannel.SLACK: slack_enabled,
            NotificationChannel.TEAMS: teams_enabled,
            NotificationChannel.DISCORD: discord_enabled,
        }
        
        # Save preferences
        user_id = str(st.session_state.get('user', {}).get('id', '1'))
        asyncio.run(notification_manager.update_user_preferences(user_id, preferences))
        st.success("✅ Notification preferences saved successfully!")
    
    # Integration settings
    st.markdown("### Integration Settings")
    
    with st.expander("📧 Email Settings"):
        email_address = st.text_input("Email Address", value=st.session_state.get('user', {}).get('email', ''))
        st.info("📌 We'll send important notifications to this email address.")
    
    with st.expander("📱 SMS Settings"):
        phone_number = st.text_input("Phone Number", placeholder="+1234567890")
        st.warning("⚠️ Standard SMS rates may apply.")
    
    with st.expander("🔗 Webhook Settings"):
        webhook_url = st.text_input("Webhook URL", placeholder="https://your-server.com/webhook")
        webhook_secret = st.text_input("Webhook Secret", type="password")
        st.code("""
# Example webhook payload:
{
    "event": "transcription.completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "transcript_id": "123",
        "file_name": "audio.mp3",
        "status": "completed"
    }
}
        """, language="json")
    
    with st.expander("💼 Slack Integration"):
        slack_webhook = st.text_input("Slack Webhook URL", placeholder="https://hooks.slack.com/services/...")
        st.markdown("[Create Slack Webhook →](https://api.slack.com/messaging/webhooks)")
    
    with st.expander("👥 Microsoft Teams Integration"):
        teams_webhook = st.text_input("Teams Webhook URL", placeholder="https://outlook.office.com/webhook/...")
        st.markdown("[Create Teams Webhook →](https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook)")
    
    with st.expander("🎮 Discord Integration"):
        discord_webhook = st.text_input("Discord Webhook URL", placeholder="https://discord.com/api/webhooks/...")
        st.markdown("[Create Discord Webhook →](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)")


def render_test_notifications():
    """Render test notification UI for demo purposes"""
    st.markdown("## 🧪 Test Notifications")
    
    st.info("Send test notifications to verify your settings are working correctly.")
    
    # Get notification manager
    manager = EnhancedNotificationManager()
    
    # Test notification form
    col1, col2 = st.columns(2)
    
    with col1:
        notification_type = st.selectbox(
            "Notification Type",
            [
                NotificationType.PROCESSING_COMPLETE,
                NotificationType.PROCESSING_FAILED,
                NotificationType.USAGE_LIMIT_WARNING,
                NotificationType.BATCH_COMPLETE,
                NotificationType.SYSTEM_UPDATE
            ],
            key="test_notif_type"
        )
        
        priority = st.selectbox(
            "Priority",
            [
                NotificationPriority.LOW,
                NotificationPriority.MEDIUM,
                NotificationPriority.HIGH,
                NotificationPriority.CRITICAL
            ],
            key="test_priority"
        )
    
    with col2:
        channels = st.multiselect(
            "Channels",
            [
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.IN_APP,
                NotificationChannel.WEBHOOK,
                NotificationChannel.SLACK,
                NotificationChannel.TEAMS,
                NotificationChannel.DISCORD
            ],
            default=[NotificationChannel.IN_APP],
            key="test_channels"
        )
    
    # Dynamic test data based on notification type
    test_data = {}
    
    if notification_type == NotificationType.PROCESSING_COMPLETE:
        test_data = {
            "user_name": st.session_state.get('user', {}).get('username', 'Test User'),
            "file_name": "test_audio.mp3",
            "duration": 180,
            "language": "English",
            "speaker_count": 2,
            "processing_time": 45,
            "transcript_url": "/transcript/test123",
            "transcript_id": "test123",
            "timestamp": datetime.utcnow().isoformat(),
            "download_url": "/api/download/test123",
            "short_url": "https://bit.ly/test123"
        }
    elif notification_type == NotificationType.PROCESSING_FAILED:
        test_data = {
            "user_name": st.session_state.get('user', {}).get('username', 'Test User'),
            "file_name": "test_audio.mp3",
            "error_message": "Audio quality too low for accurate transcription",
            "support_url": "/support"
        }
    elif notification_type == NotificationType.USAGE_LIMIT_WARNING:
        test_data = {
            "user_name": st.session_state.get('user', {}).get('username', 'Test User'),
            "usage_percentage": 85,
            "current_usage": 850,
            "limit": 1000,
            "unit": "minutes",
            "upgrade_url": "/pricing"
        }
    elif notification_type == NotificationType.BATCH_COMPLETE:
        test_data = {
            "user_name": st.session_state.get('user', {}).get('username', 'Test User'),
            "total_files": 10,
            "successful_files": 8,
            "failed_files": 2,
            "total_duration": "45 minutes",
            "batch_results_url": "/batch/results/test123"
        }
    else:
        test_data = {
            "user_name": st.session_state.get('user', {}).get('username', 'Test User'),
            "message": "This is a test notification"
        }
    
    # Send test notification
    if st.button("🚀 Send Test Notification", type="primary", key="send_test"):
        request = NotificationRequest(
            user_id=str(st.session_state.get('user', {}).get('id', '1')),
            type=notification_type,
            priority=priority,
            channels=channels,
            data=test_data
        )
        
        # Send notification asynchronously
        with st.spinner("Sending notification..."):
            results = asyncio.run(manager.send_notification(request))
        
        # Display results
        st.markdown("### Results")
        for channel, result in results.items():
            if result['status'] == 'success':
                st.success(f"✅ {channel}: {result['message']}")
            else:
                st.error(f"❌ {channel}: {result['message']}")


def render_in_app_notifications(enhanced_manager: EnhancedNotificationManager, user_id: str):
    """Render in-app notifications from Redis"""
    st.markdown("### 📬 In-App Notifications")
    
    # Get notifications from Redis
    notifications = asyncio.run(enhanced_manager.get_user_notifications(user_id, limit=20))
    
    if notifications:
        for notif in notifications:
            col1, col2 = st.columns([10, 1])
            
            with col1:
                # Icon based on priority
                icon = "🔴" if notif.get('priority') == 'critical' else "🟡" if notif.get('priority') == 'high' else "🔵"
                
                # Title and message
                title_style = "" if notif.get('read') else "font-weight: bold;"
                st.markdown(
                    f'<p style="{title_style}">{icon} {notif.get("title", "Notification")}</p>',
                    unsafe_allow_html=True
                )
                st.caption(notif.get("message", ""))
                
                # Timestamp
                timestamp = datetime.fromisoformat(notif.get('timestamp', datetime.utcnow().isoformat()))
                st.caption(format_notification_time(timestamp))
                
                # Action button
                action = notif.get('action')
                if action:
                    if st.button(action.get('label', 'View'), key=f"action_{notif.get('id')}"):
                        st.write(f"Navigate to: {action.get('url')}")
            
            with col2:
                if not notif.get('read'):
                    if st.button("✓", key=f"read_redis_{notif.get('id')}"):
                        asyncio.run(enhanced_manager.mark_notification_read(user_id, notif.get('id')))
                        st.rerun()
            
            st.divider()
    else:
        st.info("No in-app notifications")


def render_notification_dashboard():
    """Render comprehensive notification dashboard"""
    st.markdown("## 🔔 Notification Dashboard")
    
    # Initialize managers
    enhanced_manager = EnhancedNotificationManager()
    db_manager = NotificationManager(st.session_state.get('db_session'))
    user_id = str(st.session_state.get('user', {}).get('id', '1'))
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📥 All Notifications", "💬 In-App", "⚙️ Settings", "🧪 Test"])
    
    with tab1:
        # Database notifications
        render_notification_panel(db_manager, st.session_state.get('user'))
    
    with tab2:
        # Redis in-app notifications
        render_in_app_notifications(enhanced_manager, user_id)
    
    with tab3:
        # Enhanced settings
        render_enhanced_notification_settings()
    
    with tab4:
        # Test notifications
        render_test_notifications()