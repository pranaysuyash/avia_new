"""
Demo application for the notification and communication system
"""

import streamlit as st
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

from notifications.notification_ui import render_notification_dashboard
from notifications.enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)
from database_config import SessionLocal

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Notification System Demo",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .notification-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state"""
    if 'user' not in st.session_state:
        st.session_state.user = {
            'id': 1,
            'username': 'demo_user',
            'email': 'demo@example.com',
            'full_name': 'Demo User'
        }
    
    if 'db_session' not in st.session_state:
        st.session_state.db_session = SessionLocal()

def send_sample_notification(notification_type: str):
    """Send a sample notification"""
    manager = EnhancedNotificationManager()
    
    # Prepare notification data based on type
    data = {}
    notif_type = NotificationType.PROCESSING_COMPLETE
    priority = NotificationPriority.MEDIUM
    
    if notification_type == "processing_complete":
        data = {
            "user_name": st.session_state.user['full_name'],
            "file_name": "sample_audio.mp3",
            "duration": 300,
            "language": "English",
            "speaker_count": 3,
            "processing_time": 60,
            "transcript_url": "/transcript/sample123",
            "transcript_id": "sample123",
            "timestamp": datetime.utcnow().isoformat(),
            "download_url": "/api/download/sample123",
            "short_url": "https://bit.ly/sample123"
        }
        notif_type = NotificationType.PROCESSING_COMPLETE
    
    elif notification_type == "processing_failed":
        data = {
            "user_name": st.session_state.user['full_name'],
            "file_name": "failed_audio.mp3",
            "error_message": "Audio file corrupted or unsupported format",
            "support_url": "/support"
        }
        notif_type = NotificationType.PROCESSING_FAILED
        priority = NotificationPriority.HIGH
    
    elif notification_type == "usage_warning":
        data = {
            "user_name": st.session_state.user['full_name'],
            "usage_percentage": 90,
            "current_usage": 900,
            "limit": 1000,
            "unit": "minutes",
            "upgrade_url": "/pricing"
        }
        notif_type = NotificationType.USAGE_LIMIT_WARNING
        priority = NotificationPriority.HIGH
    
    elif notification_type == "batch_complete":
        data = {
            "user_name": st.session_state.user['full_name'],
            "total_files": 25,
            "successful_files": 23,
            "failed_files": 2,
            "total_duration": "2 hours 15 minutes",
            "batch_results_url": "/batch/results/batch456"
        }
        notif_type = NotificationType.BATCH_COMPLETE
    
    # Create notification request
    request = NotificationRequest(
        user_id=str(st.session_state.user['id']),
        type=notif_type,
        priority=priority,
        channels=[NotificationChannel.IN_APP],  # Use in-app for demo
        data=data
    )
    
    # Send notification
    results = asyncio.run(manager.send_notification(request))
    return results

def main():
    """Main application"""
    init_session_state()
    
    st.title("🔔 Notification & Communication System Demo")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 Quick Actions")
        
        st.markdown("### Send Sample Notifications")
        
        if st.button("✅ Processing Complete", use_container_width=True):
            results = send_sample_notification("processing_complete")
            st.success("Sent processing complete notification!")
        
        if st.button("❌ Processing Failed", use_container_width=True):
            results = send_sample_notification("processing_failed")
            st.error("Sent processing failed notification!")
        
        if st.button("⚠️ Usage Warning", use_container_width=True):
            results = send_sample_notification("usage_warning")
            st.warning("Sent usage warning notification!")
        
        if st.button("📦 Batch Complete", use_container_width=True):
            results = send_sample_notification("batch_complete")
            st.info("Sent batch complete notification!")
        
        st.divider()
        
        st.markdown("### 📊 System Info")
        
        # Check service status
        manager = EnhancedNotificationManager()
        
        col1, col2 = st.columns(2)
        with col1:
            if manager.redis_client:
                st.success("Redis: ✅")
            else:
                st.error("Redis: ❌")
            
            if manager.twilio_client:
                st.success("SMS: ✅")
            else:
                st.warning("SMS: ⚠️")
        
        with col2:
            if manager.config.smtp_username:
                st.success("Email: ✅")
            else:
                st.warning("Email: ⚠️")
            
            if manager.sns_client:
                st.success("SNS: ✅")
            else:
                st.warning("SNS: ⚠️")
        
        st.divider()
        
        st.markdown("### 🔧 Configuration")
        
        with st.expander("Environment Variables"):
            st.code(f"""
SMTP_HOST={os.getenv('SMTP_HOST', 'Not set')}
SMTP_USERNAME={os.getenv('SMTP_USERNAME', 'Not set')}
TWILIO_ACCOUNT_SID={os.getenv('TWILIO_ACCOUNT_SID', 'Not set')}
REDIS_URL={os.getenv('REDIS_URL', 'redis://localhost:6379')}
            """)
    
    # Main content
    st.markdown("""
    This demo showcases the comprehensive notification and communication system with support for:
    
    - 📧 **Email Notifications** - Send rich HTML emails with customizable templates
    - 📱 **SMS Notifications** - Instant text messages via Twilio
    - 🔗 **Webhooks** - Real-time notifications to external systems
    - 💬 **In-App Notifications** - Real-time updates via Redis and WebSockets
    - 💼 **Slack Integration** - Team notifications
    - 👥 **Microsoft Teams** - Corporate communication
    - 🎮 **Discord Integration** - Community notifications
    """)
    
    # Render notification dashboard
    render_notification_dashboard()
    
    # Feature highlights
    with st.expander("🌟 Key Features"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Multi-Channel Support**
            - Email with HTML templates
            - SMS via Twilio
            - Webhooks for integrations
            - In-app real-time notifications
            - Slack, Teams, Discord
            """)
        
        with col2:
            st.markdown("""
            **Smart Routing**
            - Priority-based delivery
            - User preference management
            - Channel fallback support
            - Retry mechanisms
            - Rate limiting
            """)
        
        with col3:
            st.markdown("""
            **Developer Friendly**
            - RESTful API endpoints
            - WebSocket support
            - Webhook payloads
            - SDK libraries
            - Comprehensive docs
            """)
    
    # Code examples
    with st.expander("💻 Code Examples"):
        st.markdown("### Sending a Notification")
        st.code("""
# Python example
from notifications.enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationPriority
)

manager = EnhancedNotificationManager()

request = NotificationRequest(
    user_id="123",
    type=NotificationType.PROCESSING_COMPLETE,
    priority=NotificationPriority.HIGH,
    channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
    data={
        "file_name": "audio.mp3",
        "duration": 180,
        "transcript_url": "/transcript/abc123"
    }
)

results = await manager.send_notification(request)
        """, language="python")
        
        st.markdown("### Webhook Integration")
        st.code("""
// JavaScript webhook handler
app.post('/webhook', (req, res) => {
    const { event, timestamp, data } = req.body;
    
    if (event === 'transcription.completed') {
        console.log(`Transcription ${data.transcript_id} completed`);
        // Handle the notification
    }
    
    res.status(200).send('OK');
});
        """, language="javascript")

if __name__ == "__main__":
    main()