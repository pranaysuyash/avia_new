"""
Example integration of notification system with main application
"""

import streamlit as st
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Import notification API
from notifications import api as notify_api
from notifications.enhanced_notification_manager import NotificationPriority

# Load environment variables
load_dotenv()

def integrate_with_stt():
    """Example: Integrate notifications with speech-to-text processing"""
    
    st.markdown("### STT Integration Example")
    
    with st.expander("View Code"):
        st.code('''
# In your stt.py file, add these imports:
from notifications import api as notify_api
import time

# Modify your transcribe function:
async def transcribe_audio_with_notifications(file_path, user_id):
    """Transcribe audio with notification support"""
    try:
        # Send processing started notification (optional)
        await notify_api.send_in_app(
            user_id=user_id,
            title="Processing Started",
            message=f"Transcribing {os.path.basename(file_path)}..."
        )
        
        # Start timer
        start_time = time.time()
        
        # Your existing transcription code
        transcript = await transcribe_audio(file_path)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Save transcript
        transcript_id = save_transcript_to_db(transcript)
        
        # Send success notification
        await notify_api.notify_processing_complete(
            user_id=user_id,
            file_name=os.path.basename(file_path),
            transcript_id=transcript_id,
            duration=get_audio_duration(file_path),
            language=transcript.get('language', 'Unknown'),
            speaker_count=len(transcript.get('speakers', [])),
            processing_time=processing_time
        )
        
        return transcript
        
    except Exception as e:
        # Send failure notification
        await notify_api.notify_processing_failed(
            user_id=user_id,
            file_name=os.path.basename(file_path),
            error_message=str(e)
        )
        raise
        ''', language='python')

def integrate_with_batch_processing():
    """Example: Integrate with batch processing"""
    
    st.markdown("### Batch Processing Integration")
    
    with st.expander("View Code"):
        st.code('''
# In your batch processing module:
from notifications import api as notify_api
import asyncio

class BatchProcessor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.results = {"success": 0, "failed": 0}
    
    async def process_batch(self, batch_id, file_list):
        """Process multiple files with notifications"""
        start_time = time.time()
        
        # Send batch started notification
        await notify_api.send_in_app(
            user_id=self.user_id,
            title="Batch Processing Started",
            message=f"Processing {len(file_list)} files...",
            action_url=f"/batch/{batch_id}"
        )
        
        # Process files
        for file_path in file_list:
            try:
                await self.process_single_file(file_path)
                self.results["success"] += 1
            except Exception as e:
                self.results["failed"] += 1
                # Optionally notify for each failure
                if self.results["failed"] <= 3:  # Limit notifications
                    await notify_api.send_in_app(
                        user_id=self.user_id,
                        title="File Processing Failed",
                        message=f"{os.path.basename(file_path)}: {str(e)}"
                    )
        
        # Calculate duration
        duration = time.time() - start_time
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        duration_str = f"{hours} hours {minutes} minutes" if hours else f"{minutes} minutes"
        
        # Send completion notification
        await notify_api.notify_batch_complete(
            user_id=self.user_id,
            total_files=len(file_list),
            successful_files=self.results["success"],
            failed_files=self.results["failed"],
            batch_id=batch_id,
            total_duration=duration_str
        )
        ''', language='python')

def integrate_with_usage_tracking():
    """Example: Integrate with usage tracking"""
    
    st.markdown("### Usage Tracking Integration")
    
    with st.expander("View Code"):
        st.code('''
# In your usage tracking module:
from notifications import api as notify_api

class UsageTracker:
    def __init__(self, db_session):
        self.db = db_session
    
    async def check_usage_limits(self, user_id):
        """Check user usage and send warnings"""
        user = self.db.query(User).filter_by(id=user_id).first()
        
        # Calculate usage percentage
        usage_percentage = (user.minutes_used / user.minutes_limit) * 100
        
        # Send warnings at different thresholds
        if usage_percentage >= 90 and not user.notified_90:
            await notify_api.notify_usage_limit_warning(
                user_id=str(user_id),
                usage_percentage=usage_percentage,
                current_usage=user.minutes_used,
                limit=user.minutes_limit,
                unit="minutes",
                priority=NotificationPriority.HIGH
            )
            user.notified_90 = True
            self.db.commit()
            
        elif usage_percentage >= 75 and not user.notified_75:
            await notify_api.notify_usage_limit_warning(
                user_id=str(user_id),
                usage_percentage=usage_percentage,
                current_usage=user.minutes_used,
                limit=user.minutes_limit,
                unit="minutes",
                priority=NotificationPriority.MEDIUM
            )
            user.notified_75 = True
            self.db.commit()
    
    async def after_processing(self, user_id, duration_seconds):
        """Update usage and check limits after processing"""
        user = self.db.query(User).filter_by(id=user_id).first()
        user.minutes_used += duration_seconds / 60
        self.db.commit()
        
        # Check if we need to send usage warnings
        await self.check_usage_limits(user_id)
        ''', language='python')

def integrate_with_export():
    """Example: Integrate with export functionality"""
    
    st.markdown("### Export Integration")
    
    with st.expander("View Code"):
        st.code('''
# In your export module:
from notifications import api as notify_api
import asyncio

class ExportManager:
    async def export_transcript(self, transcript_id, format, user_id):
        """Export transcript with notifications"""
        try:
            # Start export
            export_id = generate_export_id()
            
            # Send in-app notification that export started
            await notify_api.send_in_app(
                user_id=user_id,
                title="Export Started",
                message=f"Generating {format.upper()} export..."
            )
            
            # Perform export (this might take time for large files)
            file_path = await self.generate_export(transcript_id, format)
            file_size = os.path.getsize(file_path)
            
            # Send completion notification
            await notify_api.notify_export_ready(
                user_id=user_id,
                export_id=export_id,
                file_name=os.path.basename(file_path),
                export_format=format.upper(),
                file_size=file_size
            )
            
            return export_id
            
        except Exception as e:
            await notify_api.send_in_app(
                user_id=user_id,
                title="Export Failed",
                message=f"Failed to export {format.upper()}: {str(e)}"
            )
            raise
        ''', language='python')

def integrate_with_realtime():
    """Example: Real-time notification updates"""
    
    st.markdown("### Real-time Updates")
    
    with st.expander("View Code"):
        st.code('''
# In your Streamlit app:
import streamlit as st
from notifications import api as notify_api

# Add to your app's sidebar or header
async def display_notifications():
    """Display real-time notifications"""
    if 'user' in st.session_state:
        user_id = str(st.session_state.user['id'])
        
        # Get recent notifications
        notifications = await notify_api.get_user_notifications(
            user_id=user_id,
            limit=10
        )
        
        # Count unread
        unread_count = sum(1 for n in notifications if not n.get('read'))
        
        # Display bell icon with count
        col1, col2 = st.columns([1, 10])
        with col1:
            if unread_count > 0:
                st.button(f"🔔 {unread_count}")
            else:
                st.button("🔔")
        
        # Show notifications in expander
        with st.expander("Notifications", expanded=unread_count > 0):
            for notif in notifications[:5]:
                # Display notification
                if not notif.get('read'):
                    st.markdown(f"**{notif['title']}**")
                else:
                    st.write(notif['title'])
                
                st.caption(notif['message'])
                
                # Mark as read button
                if not notif.get('read'):
                    if st.button("Mark as read", key=f"read_{notif['id']}"):
                        await notify_api.mark_notification_read(
                            user_id, notif['id']
                        )
                        st.rerun()

# Add to your main app
if __name__ == "__main__":
    st.title("My App")
    
    # Display notifications in sidebar
    with st.sidebar:
        asyncio.run(display_notifications())
    
    # Your app content...
        ''', language='python')

def main():
    st.title("📚 Notification System Integration Guide")
    
    st.markdown("""
    This guide shows how to integrate the notification system with various parts of your application.
    
    ## Key Integration Points
    
    1. **Speech-to-Text Processing** - Notify when transcription completes or fails
    2. **Batch Processing** - Update users on batch job progress
    3. **Usage Tracking** - Warn users approaching limits
    4. **Export Generation** - Notify when exports are ready
    5. **Real-time Updates** - Show notifications in the UI
    """)
    
    # Integration examples
    integrate_with_stt()
    integrate_with_batch_processing()
    integrate_with_usage_tracking()
    integrate_with_export()
    integrate_with_realtime()
    
    # Best practices
    st.markdown("## 🎯 Best Practices")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Do's ✅
        - Send notifications for important events
        - Use appropriate priority levels
        - Include actionable information
        - Respect user preferences
        - Handle errors gracefully
        - Test notification delivery
        """)
    
    with col2:
        st.markdown("""
        ### Don'ts ❌
        - Don't spam users with too many notifications
        - Don't send sensitive data in notifications
        - Don't ignore delivery failures
        - Don't hardcode user IDs
        - Don't send duplicate notifications
        - Don't forget to validate data
        """)
    
    # Configuration checklist
    st.markdown("## ✅ Configuration Checklist")
    
    st.markdown("""
    Before going to production:
    
    - [ ] Configure SMTP settings for email
    - [ ] Set up Twilio for SMS (optional)
    - [ ] Configure Redis for in-app notifications
    - [ ] Set up webhook endpoints (optional)
    - [ ] Configure third-party integrations (Slack/Teams/Discord)
    - [ ] Test all notification channels
    - [ ] Set up monitoring and alerts
    - [ ] Document user preferences
    - [ ] Create notification templates
    - [ ] Test error scenarios
    """)

if __name__ == "__main__":
    main()