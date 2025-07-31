"""
Notification UI components for Streamlit
"""

import streamlit as st
from datetime import datetime
from typing import List, Optional, Dict, Any
from database.models import Notification, User
from .notification_manager import NotificationManager


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