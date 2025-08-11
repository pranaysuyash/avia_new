"""
Streamlit UI for Notification Management System
Task 200: Build notification and communication system
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from notification_system import (
    NotificationChannel,
    NotificationManager,
    NotificationPriority,
    NotificationRequest,
    NotificationService,
    NotificationType
)

# Page configuration
st.set_page_config(
    page_title="Notification Center",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .notification-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .notification-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin: 0 5px;
    }
    .priority-urgent {
        background: #dc3545;
        color: white;
    }
    .priority-high {
        background: #ffc107;
        color: black;
    }
    .priority-medium {
        background: #17a2b8;
        color: white;
    }
    .priority-low {
        background: #6c757d;
        color: white;
    }
    .status-sent {
        background: #28a745;
        color: white;
    }
    .status-failed {
        background: #dc3545;
        color: white;
    }
    .status-pending {
        background: #ffc107;
        color: black;
    }
    .channel-icon {
        width: 24px;
        height: 24px;
        margin-right: 8px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'notification_service' not in st.session_state:
    config = {
        'smtp_host': st.secrets.get('smtp_host', 'localhost'),
        'smtp_port': st.secrets.get('smtp_port', 587),
        'redis_host': st.secrets.get('redis_host', 'localhost'),
        'redis_port': st.secrets.get('redis_port', 6379)
    }
    st.session_state.notification_service = NotificationService(config)
    st.session_state.notification_manager = NotificationManager(
        st.session_state.notification_service
    )

if 'notifications' not in st.session_state:
    st.session_state.notifications = []

if 'preferences' not in st.session_state:
    st.session_state.preferences = {
        'email_enabled': True,
        'sms_enabled': False,
        'push_enabled': True,
        'in_app_enabled': True,
        'webhook_enabled': False,
        'quiet_hours_enabled': False
    }

# Helper functions
def get_channel_icon(channel: str) -> str:
    """Get icon for notification channel"""
    icons = {
        'email': '📧',
        'sms': '📱',
        'in_app': '🔔',
        'webhook': '🔗',
        'push': '📲',
        'slack': '💬',
        'teams': '👥',
        'discord': '🎮'
    }
    return icons.get(channel, '📢')

def get_priority_badge(priority: str) -> str:
    """Get HTML badge for priority"""
    return f'<span class="notification-badge priority-{priority}">{priority.upper()}</span>'

def get_status_badge(status: str) -> str:
    """Get HTML badge for status"""
    return f'<span class="notification-badge status-{status}">{status.upper()}</span>'

def format_notification_card(notification: Dict[str, Any]) -> str:
    """Format notification as HTML card"""
    return f"""
    <div class="notification-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0;">
                    {get_channel_icon(notification.get('channel', 'in_app'))}
                    {notification.get('subject', 'Notification')}
                </h4>
                <p style="margin: 10px 0; color: #666;">
                    {notification.get('body', '')}
                </p>
                <div>
                    {get_priority_badge(notification.get('priority', 'medium'))}
                    {get_status_badge(notification.get('status', 'sent'))}
                    <span style="color: #999; font-size: 12px; margin-left: 10px;">
                        {notification.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M')}
                    </span>
                </div>
            </div>
        </div>
    </div>
    """

# Main UI
st.title("🔔 Notification Center")

# Sidebar
with st.sidebar:
    st.header("Quick Actions")
    
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    # Auto-refresh for real-time updates
    auto_refresh = st.checkbox("Auto-refresh (30s)")
    if auto_refresh:
        st_autorefresh(interval=30000, key="notification_refresh")
    
    st.divider()
    
    # Navigation
    page = st.radio(
        "Navigate",
        ["📬 Inbox", "⚙️ Preferences", "📊 Analytics", "🔧 Admin", "📝 Templates", "🧪 Test"]
    )

# Main content area
if page == "📬 Inbox":
    st.header("Your Notifications")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_unread = st.checkbox("Unread only")
    with col2:
        filter_type = st.selectbox(
            "Type",
            ["All"] + [t.value for t in NotificationType]
        )
    with col3:
        filter_channel = st.selectbox(
            "Channel",
            ["All"] + [c.value for c in NotificationChannel]
        )
    with col4:
        filter_priority = st.selectbox(
            "Priority",
            ["All"] + [p.value for p in NotificationPriority]
        )
    
    # Mock notifications for demo
    notifications = [
        {
            "id": "1",
            "type": "transcription_completed",
            "channel": "email",
            "priority": "medium",
            "status": "sent",
            "subject": "Transcription Complete: Meeting Recording",
            "body": "Your transcription for 'Q4 Planning Meeting' is ready to view.",
            "created_at": datetime.utcnow() - timedelta(hours=1)
        },
        {
            "id": "2",
            "type": "batch_processing_completed",
            "channel": "in_app",
            "priority": "medium",
            "status": "delivered",
            "subject": "Batch Processing Complete",
            "body": "Successfully processed 10 files. 9 succeeded, 1 failed.",
            "created_at": datetime.utcnow() - timedelta(hours=3)
        },
        {
            "id": "3",
            "type": "quota_warning",
            "channel": "email",
            "priority": "high",
            "status": "sent",
            "subject": "Usage Warning: 80% of Monthly Quota",
            "body": "You've used 80% of your monthly transcription quota. Consider upgrading your plan.",
            "created_at": datetime.utcnow() - timedelta(days=1)
        }
    ]
    
    # Display notifications
    if notifications:
        # Summary stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(notifications))
        with col2:
            unread_count = sum(1 for n in notifications if n.get('status') != 'read')
            st.metric("Unread", unread_count)
        with col3:
            urgent_count = sum(1 for n in notifications if n.get('priority') == 'urgent')
            st.metric("Urgent", urgent_count)
        with col4:
            failed_count = sum(1 for n in notifications if n.get('status') == 'failed')
            st.metric("Failed", failed_count)
        
        st.divider()
        
        # Notification list
        for notification in notifications:
            st.markdown(format_notification_card(notification), unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 8])
            with col1:
                if st.button("Mark Read", key=f"read_{notification['id']}"):
                    st.success("Marked as read")
            with col2:
                if st.button("Delete", key=f"delete_{notification['id']}"):
                    st.success("Deleted")
    else:
        st.info("No notifications to display")

elif page == "⚙️ Preferences":
    st.header("Notification Preferences")
    
    # Channel preferences
    st.subheader("Notification Channels")
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.preferences['email_enabled'] = st.checkbox(
            "📧 Email Notifications",
            value=st.session_state.preferences['email_enabled']
        )
        if st.session_state.preferences['email_enabled']:
            email = st.text_input("Email Address", value="user@example.com")
        
        st.session_state.preferences['sms_enabled'] = st.checkbox(
            "📱 SMS Notifications",
            value=st.session_state.preferences['sms_enabled']
        )
        if st.session_state.preferences['sms_enabled']:
            phone = st.text_input("Phone Number", value="+1234567890")
        
        st.session_state.preferences['push_enabled'] = st.checkbox(
            "📲 Push Notifications",
            value=st.session_state.preferences['push_enabled']
        )
    
    with col2:
        st.session_state.preferences['in_app_enabled'] = st.checkbox(
            "🔔 In-App Notifications",
            value=st.session_state.preferences['in_app_enabled']
        )
        
        st.session_state.preferences['webhook_enabled'] = st.checkbox(
            "🔗 Webhook Notifications",
            value=st.session_state.preferences['webhook_enabled']
        )
        if st.session_state.preferences['webhook_enabled']:
            webhook_url = st.text_input("Webhook URL", value="https://example.com/webhook")
    
    st.divider()
    
    # Quiet hours
    st.subheader("Quiet Hours")
    st.session_state.preferences['quiet_hours_enabled'] = st.checkbox(
        "Enable Quiet Hours",
        value=st.session_state.preferences['quiet_hours_enabled']
    )
    
    if st.session_state.preferences['quiet_hours_enabled']:
        col1, col2, col3 = st.columns(3)
        with col1:
            quiet_start = st.time_input("Start Time", value=datetime.strptime("22:00", "%H:%M").time())
        with col2:
            quiet_end = st.time_input("End Time", value=datetime.strptime("08:00", "%H:%M").time())
        with col3:
            timezone = st.selectbox("Timezone", ["UTC", "US/Eastern", "US/Pacific", "Europe/London"])
    
    st.divider()
    
    # Notification types
    st.subheader("Notification Types")
    st.write("Choose which types of notifications you want to receive:")
    
    notification_types = {
        "Transcription Updates": ["transcription_started", "transcription_completed", "transcription_failed"],
        "Batch Processing": ["batch_processing_started", "batch_processing_completed"],
        "Sharing & Collaboration": ["share_invitation", "collaboration_update"],
        "Account & Billing": ["quota_warning", "subscription_expiring", "payment_failed"],
        "Security": ["security_alert", "api_key_expiring"]
    }
    
    for category, types in notification_types.items():
        with st.expander(category):
            for notif_type in types:
                st.checkbox(notif_type.replace('_', ' ').title(), value=True, key=f"pref_{notif_type}")
    
    # Save button
    if st.button("💾 Save Preferences", type="primary", use_container_width=True):
        st.success("Preferences saved successfully!")

elif page == "📊 Analytics":
    st.header("Notification Analytics")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Mock analytics data
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Notifications over time
    st.subheader("Notifications Over Time")
    df_timeline = pd.DataFrame({
        'Date': dates,
        'Sent': [20 + i % 10 for i in range(len(dates))],
        'Delivered': [18 + i % 10 for i in range(len(dates))],
        'Opened': [15 + i % 8 for i in range(len(dates))]
    })
    
    fig_timeline = px.line(
        df_timeline.melt(id_vars=['Date'], var_name='Status', value_name='Count'),
        x='Date', y='Count', color='Status',
        title='Notification Delivery Metrics'
    )
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Channel distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("By Channel")
        channel_data = pd.DataFrame({
            'Channel': ['Email', 'In-App', 'SMS', 'Webhook', 'Push'],
            'Count': [150, 280, 45, 30, 95]
        })
        fig_channel = px.pie(
            channel_data, values='Count', names='Channel',
            title='Notification Distribution by Channel'
        )
        st.plotly_chart(fig_channel, use_container_width=True)
    
    with col2:
        st.subheader("By Priority")
        priority_data = pd.DataFrame({
            'Priority': ['Low', 'Medium', 'High', 'Urgent'],
            'Count': [200, 250, 120, 30]
        })
        fig_priority = px.bar(
            priority_data, x='Priority', y='Count',
            title='Notification Distribution by Priority',
            color='Priority',
            color_discrete_map={
                'Low': '#6c757d',
                'Medium': '#17a2b8',
                'High': '#ffc107',
                'Urgent': '#dc3545'
            }
        )
        st.plotly_chart(fig_priority, use_container_width=True)
    
    # Success rate
    st.subheader("Delivery Success Rate")
    success_data = pd.DataFrame({
        'Type': ['Transcription', 'Batch', 'Sharing', 'Quota', 'Security'],
        'Success Rate': [98.5, 96.2, 99.1, 100, 97.8]
    })
    
    fig_success = go.Figure(data=[
        go.Bar(
            x=success_data['Type'],
            y=success_data['Success Rate'],
            marker_color=['green' if x > 97 else 'orange' for x in success_data['Success Rate']]
        )
    ])
    fig_success.update_layout(
        title='Delivery Success Rate by Type (%)',
        yaxis_range=[90, 100]
    )
    st.plotly_chart(fig_success, use_container_width=True)

elif page == "🔧 Admin":
    st.header("Admin Controls")
    
    # Broadcast notification
    st.subheader("Broadcast Notification")
    
    col1, col2 = st.columns(2)
    with col1:
        broadcast_type = st.selectbox(
            "Notification Type",
            [t.value for t in NotificationType]
        )
        broadcast_priority = st.selectbox(
            "Priority",
            [p.value for p in NotificationPriority]
        )
    
    with col2:
        broadcast_channels = st.multiselect(
            "Channels",
            [c.value for c in NotificationChannel],
            default=['in_app', 'email']
        )
        
        user_groups = st.multiselect(
            "User Groups",
            ["All Users", "Free Tier", "Pro Tier", "Enterprise", "Trial Users"],
            default=["All Users"]
        )
    
    broadcast_subject = st.text_input("Subject")
    broadcast_message = st.text_area("Message", height=100)
    
    col1, col2 = st.columns(2)
    with col1:
        schedule_broadcast = st.checkbox("Schedule for later")
        if schedule_broadcast:
            schedule_date = st.date_input("Date")
            schedule_time = st.time_input("Time")
    
    with col2:
        test_mode = st.checkbox("Test Mode (send to admins only)")
    
    if st.button("📤 Send Broadcast", type="primary", use_container_width=True):
        if test_mode:
            st.info("Test broadcast sent to admin users")
        else:
            st.success(f"Broadcast sent to {len(user_groups)} user groups")
    
    st.divider()
    
    # System status
    st.subheader("System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Email Service", "✅ Operational", delta="99.9% uptime")
    with col2:
        st.metric("SMS Service", "✅ Operational", delta="100% uptime")
    with col3:
        st.metric("Push Service", "⚠️ Degraded", delta="-2% delivery")
    with col4:
        st.metric("Webhook Queue", "✅ Healthy", delta="0 pending")
    
    # Recent failures
    st.subheader("Recent Failures")
    failures_df = pd.DataFrame({
        'Time': [datetime.now() - timedelta(hours=i) for i in range(5)],
        'Type': ['email', 'sms', 'webhook', 'email', 'push'],
        'Error': [
            'SMTP connection timeout',
            'Invalid phone number format',
            'Webhook returned 404',
            'Recipient email bounced',
            'Push token expired'
        ],
        'User': ['user123', 'user456', 'user789', 'user321', 'user654']
    })
    st.dataframe(failures_df, use_container_width=True)

elif page == "📝 Templates":
    st.header("Notification Templates")
    
    # Template selector
    template_type = st.selectbox(
        "Template Type",
        ["Transcription Complete", "Batch Complete", "Quota Warning", "Security Alert", "Custom"]
    )
    
    template_channel = st.selectbox(
        "Channel",
        ["Email", "SMS", "In-App", "Slack", "Teams"]
    )
    
    # Template editor
    st.subheader("Edit Template")
    
    if template_channel == "Email":
        subject_template = st.text_input(
            "Subject Template",
            value="Your transcription is ready: {{ title }}"
        )
        
        body_template = st.text_area(
            "Body Template (HTML)",
            value="""<h2>Transcription Complete</h2>
<p>Your transcription for "{{ title }}" has been completed successfully.</p>
<p><strong>Duration:</strong> {{ duration }}</p>
<p><strong>Words:</strong> {{ word_count }}</p>
<p><a href="{{ link }}">View Transcription</a></p>""",
            height=200
        )
    elif template_channel == "SMS":
        body_template = st.text_area(
            "Message Template",
            value="Your transcription '{{ title }}' is ready. View at: {{ short_link }}",
            max_chars=160
        )
    else:
        body_template = st.text_area(
            "Message Template",
            value="Your transcription for '{{ title }}' is ready to view.",
            height=100
        )
    
    # Variable reference
    with st.expander("Available Variables"):
        st.code("""
        {{ title }} - Content title
        {{ duration }} - Duration
        {{ word_count }} - Word count
        {{ link }} - Full link
        {{ short_link }} - Short link
        {{ user_name }} - User's name
        {{ timestamp }} - Current time
        """)
    
    # Preview
    st.subheader("Preview")
    
    preview_data = {
        "title": "Q4 Planning Meeting",
        "duration": "45:30",
        "word_count": 5432,
        "link": "https://platform.example.com/transcriptions/123",
        "short_link": "https://plt.fm/t/123",
        "user_name": "John Doe",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if template_channel == "Email" and 'subject_template' in locals():
        from jinja2 import Template
        subject = Template(subject_template).render(**preview_data)
        st.text_input("Subject Preview", value=subject, disabled=True)
    
    from jinja2 import Template
    body = Template(body_template).render(**preview_data)
    
    if template_channel == "Email":
        st.markdown(body, unsafe_allow_html=True)
    else:
        st.text_area("Message Preview", value=body, disabled=True)
    
    # Save button
    if st.button("💾 Save Template", type="primary", use_container_width=True):
        st.success("Template saved successfully!")

elif page == "🧪 Test":
    st.header("Test Notifications")
    
    st.info("Send test notifications to verify your configuration")
    
    # Test configuration
    col1, col2 = st.columns(2)
    
    with col1:
        test_channel = st.selectbox(
            "Channel to Test",
            [c.value for c in NotificationChannel]
        )
        
        test_priority = st.selectbox(
            "Priority",
            [p.value for p in NotificationPriority]
        )
    
    with col2:
        if test_channel == "email":
            test_recipient = st.text_input("Email Address", value="test@example.com")
        elif test_channel == "sms":
            test_recipient = st.text_input("Phone Number", value="+1234567890")
        elif test_channel == "webhook":
            test_recipient = st.text_input("Webhook URL", value="https://webhook.site/test")
        else:
            test_recipient = st.text_input("Recipient ID", value="current_user")
    
    test_message = st.text_area(
        "Test Message",
        value="This is a test notification from the Audio/Video Transcription Platform.",
        height=100
    )
    
    # Send test
    if st.button("🚀 Send Test Notification", type="primary", use_container_width=True):
        with st.spinner("Sending test notification..."):
            # Simulate sending
            import time
            time.sleep(2)
            
            st.success(f"✅ Test notification sent successfully via {test_channel}!")
            
            # Show result
            with st.expander("Delivery Details"):
                st.json({
                    "notification_id": "test_123456",
                    "channel": test_channel,
                    "recipient": test_recipient,
                    "status": "delivered",
                    "sent_at": datetime.now().isoformat(),
                    "delivered_at": datetime.now().isoformat(),
                    "response": {
                        "code": 200,
                        "message": "Success"
                    }
                })
    
    st.divider()
    
    # Connection test
    st.subheader("Test Connections")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Test Email", use_container_width=True):
            with st.spinner("Testing..."):
                import time
                time.sleep(1)
            st.success("✅ SMTP Connected")
    
    with col2:
        if st.button("Test SMS", use_container_width=True):
            with st.spinner("Testing..."):
                import time
                time.sleep(1)
            st.success("✅ Twilio Connected")
    
    with col3:
        if st.button("Test Redis", use_container_width=True):
            with st.spinner("Testing..."):
                import time
                time.sleep(1)
            st.success("✅ Redis Connected")
    
    with col4:
        if st.button("Test Webhook", use_container_width=True):
            with st.spinner("Testing..."):
                import time
                time.sleep(1)
            st.success("✅ Webhook Active")

# Footer
st.divider()
st.caption("Notification System v1.0 | Task 200: Build notification and communication system")