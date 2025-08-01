"""
Collaboration UI Components
Streamlit UI for real-time collaboration features
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Try to import WebSocket client
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets not available. Install with: pip install websockets")

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    logger.warning("socketio not available. Install with: pip install python-socketio")


class CollaborationUI:
    """UI components for real-time collaboration"""
    
    @staticmethod
    def render_collaboration_panel(transcript_id: str, user_id: str):
        """Render the collaboration panel"""
        st.markdown("### 👥 Real-time Collaboration")
        
        # Check if WebSocket libraries are available
        if not (WEBSOCKETS_AVAILABLE or SOCKETIO_AVAILABLE):
            st.warning("Real-time collaboration requires WebSocket libraries. Install with: `pip install websockets python-socketio`")
            return
        
        # Collaboration controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Collaboration Session", use_container_width=True):
                st.session_state.start_collaboration = True
        
        with col2:
            if st.button("🔗 Join Existing Session", use_container_width=True):
                st.session_state.join_collaboration = True
        
        with col3:
            if st.button("📊 View Active Sessions", use_container_width=True):
                st.session_state.view_sessions = True
        
        # Handle collaboration actions
        if st.session_state.get('start_collaboration'):
            CollaborationUI._render_start_session(transcript_id, user_id)
        
        elif st.session_state.get('join_collaboration'):
            CollaborationUI._render_join_session(user_id)
        
        elif st.session_state.get('view_sessions'):
            CollaborationUI._render_active_sessions(user_id)
        
        # Show active collaboration if in session
        if st.session_state.get('active_collaboration'):
            CollaborationUI._render_active_collaboration()
    
    @staticmethod
    def _render_start_session(transcript_id: str, user_id: str):
        """Render start session interface"""
        st.markdown("#### Start New Collaboration Session")
        
        with st.form("start_session_form"):
            session_name = st.text_input(
                "Session Name",
                value=f"Session for {transcript_id[:8]}",
                help="Give your session a descriptive name"
            )
            
            max_users = st.slider(
                "Maximum Users",
                min_value=2,
                max_value=20,
                value=10,
                help="Maximum number of simultaneous users"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                allow_anonymous = st.checkbox(
                    "Allow Anonymous Users",
                    value=False,
                    help="Allow users without accounts to join"
                )
            
            with col2:
                enable_comments = st.checkbox(
                    "Enable Comments",
                    value=True,
                    help="Allow users to add comments"
                )
            
            advanced_settings = st.expander("Advanced Settings")
            with advanced_settings:
                auto_save = st.checkbox("Auto-save Changes", value=True)
                save_interval = st.number_input(
                    "Save Interval (seconds)",
                    min_value=10,
                    max_value=300,
                    value=30,
                    disabled=not auto_save
                )
                show_cursors = st.checkbox("Show User Cursors", value=True)
                show_typing = st.checkbox("Show Typing Indicators", value=True)
                enable_versions = st.checkbox("Enable Version Control", value=True)
            
            if st.form_submit_button("Start Session", type="primary", use_container_width=True):
                # Create session configuration
                settings = {
                    "session_name": session_name,
                    "max_users": max_users,
                    "allow_anonymous": allow_anonymous,
                    "enable_comments": enable_comments,
                    "auto_save": auto_save,
                    "save_interval": save_interval,
                    "show_cursors": show_cursors,
                    "show_typing_indicators": show_typing,
                    "enable_version_control": enable_versions
                }
                
                # Store in session state
                st.session_state.collaboration_settings = settings
                st.session_state.active_collaboration = {
                    "transcript_id": transcript_id,
                    "user_id": user_id,
                    "is_host": True,
                    "settings": settings
                }
                
                st.success(f"✅ Started collaboration session: {session_name}")
                st.session_state.start_collaboration = False
                st.rerun()
    
    @staticmethod
    def _render_join_session(user_id: str):
        """Render join session interface"""
        st.markdown("#### Join Collaboration Session")
        
        with st.form("join_session_form"):
            session_code = st.text_input(
                "Session Code",
                placeholder="Enter the session code or link",
                help="Get this from the session host"
            )
            
            display_name = st.text_input(
                "Your Display Name",
                value=user_id,
                help="How you'll appear to other collaborators"
            )
            
            if st.form_submit_button("Join Session", type="primary", use_container_width=True):
                if session_code:
                    # Store join info
                    st.session_state.active_collaboration = {
                        "session_code": session_code,
                        "user_id": user_id,
                        "display_name": display_name,
                        "is_host": False
                    }
                    
                    st.success(f"✅ Joining session: {session_code}")
                    st.session_state.join_collaboration = False
                    st.rerun()
                else:
                    st.error("Please enter a session code")
    
    @staticmethod
    def _render_active_sessions(user_id: str):
        """Render active sessions list"""
        st.markdown("#### Active Collaboration Sessions")
        
        # Mock data for demonstration
        sessions = [
            {
                "session_id": "collab_123_abc",
                "name": "Marketing Transcript Review",
                "host": "John Doe",
                "users": 3,
                "max_users": 10,
                "created": "10 minutes ago"
            },
            {
                "session_id": "collab_456_def",
                "name": "Customer Interview Analysis",
                "host": "Jane Smith",
                "users": 5,
                "max_users": 8,
                "created": "1 hour ago"
            }
        ]
        
        if sessions:
            for session in sessions:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{session['name']}**")
                        st.caption(f"Host: {session['host']} • Created {session['created']}")
                    
                    with col2:
                        st.metric("Users", f"{session['users']}/{session['max_users']}")
                    
                    with col3:
                        if st.button("Join", key=f"join_{session['session_id']}", use_container_width=True):
                            st.session_state.active_collaboration = {
                                "session_id": session['session_id'],
                                "session_name": session['name'],
                                "user_id": user_id,
                                "is_host": False
                            }
                            st.session_state.view_sessions = False
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No active sessions available. Start a new session to begin collaborating!")
        
        if st.button("← Back", use_container_width=True):
            st.session_state.view_sessions = False
            st.rerun()
    
    @staticmethod
    def _render_active_collaboration():
        """Render active collaboration interface"""
        collab = st.session_state.active_collaboration
        
        # Collaboration header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### 🔴 Live: {collab.get('session_name', 'Collaboration Session')}")
        
        with col2:
            if st.button("⚙️ Settings"):
                st.session_state.show_collab_settings = not st.session_state.get('show_collab_settings', False)
        
        with col3:
            if st.button("🚪 Leave Session", type="secondary"):
                st.session_state.active_collaboration = None
                st.rerun()
        
        # Show settings if toggled
        if st.session_state.get('show_collab_settings'):
            CollaborationUI._render_collaboration_settings(collab)
        
        # Main collaboration area
        tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "💬 Comments", "📝 Versions", "📊 Activity"])
        
        with tab1:
            CollaborationUI._render_active_users()
        
        with tab2:
            CollaborationUI._render_comments()
        
        with tab3:
            CollaborationUI._render_versions()
        
        with tab4:
            CollaborationUI._render_activity_log()
        
        # Live indicators
        CollaborationUI._render_live_indicators()
    
    @staticmethod
    def _render_active_users():
        """Render active users list"""
        st.markdown("#### Active Collaborators")
        
        # Mock users
        users = [
            {"name": "You", "color": "#007bff", "status": "editing", "cursor": 1250},
            {"name": "Alice", "color": "#28a745", "status": "viewing", "cursor": 890},
            {"name": "Bob", "color": "#dc3545", "status": "commenting", "cursor": 2100}
        ]
        
        for user in users:
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.markdown(
                    f"<span style='color: {user['color']}'>●</span> **{user['name']}**",
                    unsafe_allow_html=True
                )
            
            with col2:
                st.caption(f"Status: {user['status']}")
            
            with col3:
                st.caption(f"Position: {user['cursor']}")
    
    @staticmethod
    def _render_comments():
        """Render comments interface"""
        st.markdown("#### Comments & Discussions")
        
        # Add comment form
        with st.form("add_comment_form", clear_on_submit=True):
            comment_text = st.text_area(
                "Add a comment",
                placeholder="Type your comment here...",
                height=80
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                comment_position = st.number_input(
                    "Position in transcript",
                    min_value=0,
                    value=0,
                    help="Character position in the transcript"
                )
            
            with col2:
                if st.form_submit_button("Post Comment", type="primary", use_container_width=True):
                    if comment_text:
                        st.success("Comment posted!")
        
        # Display comments
        st.markdown("##### Recent Comments")
        
        comments = [
            {
                "author": "Alice",
                "text": "This section needs clarification about the pricing model.",
                "position": 1250,
                "time": "5 minutes ago",
                "resolved": False
            },
            {
                "author": "Bob",
                "text": "Great insights on customer feedback here!",
                "position": 2890,
                "time": "12 minutes ago",
                "resolved": True
            }
        ]
        
        for i, comment in enumerate(comments):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{comment['author']}** • {comment['time']}")
                    st.write(comment['text'])
                    st.caption(f"Position: {comment['position']}")
                
                with col2:
                    if comment['resolved']:
                        st.success("✓ Resolved")
                    else:
                        if st.button("Resolve", key=f"resolve_{i}", use_container_width=True):
                            st.success("Resolved!")
                            st.rerun()
                
                st.divider()
    
    @staticmethod
    def _render_versions():
        """Render version control interface"""
        st.markdown("#### Version History")
        
        # Create version button
        if st.button("📸 Create Version Snapshot", type="primary", use_container_width=True):
            with st.form("create_version_form"):
                version_name = st.text_input(
                    "Version Name",
                    value=f"Version {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
                description = st.text_area(
                    "Description",
                    placeholder="Describe the changes in this version..."
                )
                
                if st.form_submit_button("Create Version"):
                    st.success(f"Version '{version_name}' created!")
        
        # Version history
        versions = [
            {
                "name": "Version 2024-01-15 14:30",
                "author": "You",
                "description": "Added speaker identification and timestamps",
                "time": "2 hours ago"
            },
            {
                "name": "Initial Import",
                "author": "System",
                "description": "Original transcript from audio file",
                "time": "3 hours ago"
            }
        ]
        
        for version in versions:
            with st.expander(f"📄 {version['name']}"):
                st.write(f"**Created by:** {version['author']}")
                st.write(f"**When:** {version['time']}")
                st.write(f"**Description:** {version['description']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.button("View", key=f"view_{version['name']}", use_container_width=True)
                with col2:
                    st.button("Restore", key=f"restore_{version['name']}", use_container_width=True)
    
    @staticmethod
    def _render_activity_log():
        """Render activity log"""
        st.markdown("#### Recent Activity")
        
        activities = [
            {"user": "Alice", "action": "edited transcript", "detail": "Lines 45-52", "time": "2 min ago"},
            {"user": "Bob", "action": "added comment", "detail": "Position 1250", "time": "5 min ago"},
            {"user": "You", "action": "created version", "detail": "Version 2.1", "time": "10 min ago"},
            {"user": "Alice", "action": "joined session", "detail": "", "time": "15 min ago"}
        ]
        
        for activity in activities:
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.markdown(f"**{activity['user']}**")
            
            with col2:
                detail = f" - {activity['detail']}" if activity['detail'] else ""
                st.write(f"{activity['action']}{detail}")
            
            with col3:
                st.caption(activity['time'])
            
            st.divider()
    
    @staticmethod
    def _render_live_indicators():
        """Render live collaboration indicators"""
        # Live status in sidebar
        with st.sidebar:
            st.markdown("### 🔴 Live Status")
            
            # Connection status
            st.success("✅ Connected to collaboration server")
            
            # Active users count
            st.metric("Active Users", "3", "+1")
            
            # Typing indicators
            st.markdown("#### Who's typing...")
            st.info("🖊️ Alice is typing...")
            
            # Recent saves
            st.markdown("#### Auto-save")
            st.success("✓ Last saved: 30 seconds ago")
    
    @staticmethod
    def _render_collaboration_settings(collab: Dict):
        """Render collaboration settings"""
        with st.expander("Collaboration Settings", expanded=True):
            settings = collab.get('settings', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.checkbox(
                    "Auto-save Changes",
                    value=settings.get('auto_save', True),
                    key="collab_auto_save"
                )
                
                st.checkbox(
                    "Show User Cursors",
                    value=settings.get('show_cursors', True),
                    key="collab_show_cursors"
                )
                
                st.checkbox(
                    "Enable Comments",
                    value=settings.get('enable_comments', True),
                    key="collab_comments"
                )
            
            with col2:
                st.checkbox(
                    "Show Typing Indicators",
                    value=settings.get('show_typing_indicators', True),
                    key="collab_typing"
                )
                
                st.checkbox(
                    "Enable Version Control",
                    value=settings.get('enable_version_control', True),
                    key="collab_versions"
                )
                
                st.number_input(
                    "Max Users",
                    value=settings.get('max_users', 10),
                    min_value=2,
                    max_value=50,
                    key="collab_max_users"
                )
            
            if st.button("Save Settings", use_container_width=True):
                st.success("Settings updated!")
                st.session_state.show_collab_settings = False
                st.rerun()
    
    @staticmethod
    def render_live_transcription_panel():
        """Render live transcription interface"""
        st.markdown("### 🎙️ Live Transcription")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🔴 Start Live Transcription", type="primary", use_container_width=True):
                st.session_state.live_transcription_active = True
        
        with col2:
            if st.button("⚙️ Audio Settings"):
                st.session_state.show_audio_settings = not st.session_state.get('show_audio_settings', False)
        
        if st.session_state.get('show_audio_settings'):
            with st.expander("Audio Settings", expanded=True):
                st.selectbox(
                    "Microphone",
                    ["Default Microphone", "USB Microphone", "Bluetooth Headset"],
                    key="audio_input_device"
                )
                
                st.selectbox(
                    "Language",
                    ["English", "Spanish", "French", "German", "Japanese"],
                    key="live_language"
                )
                
                st.checkbox("Enable noise cancellation", value=True, key="noise_cancel")
                st.checkbox("Show confidence scores", value=False, key="show_confidence")
        
        if st.session_state.get('live_transcription_active'):
            # Live transcription display
            st.markdown("#### 🔴 Recording...")
            
            # Waveform visualization placeholder
            st.markdown(
                """
                <div style='background: #f0f2f6; height: 100px; border-radius: 10px; 
                display: flex; align-items: center; justify-content: center;'>
                    <span style='color: #666;'>🎵 Audio waveform visualization</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Live transcript
            st.markdown("#### Live Transcript")
            
            live_container = st.container()
            with live_container:
                st.info("🎤 Speaker 1: ...and that's why we need to focus on customer retention...")
                st.success("✅ Speaker 1: The new feature has increased engagement by 40%.")
                st.warning("🎤 Speaker 2: [Transcribing...] I think we should also consider...")
            
            # Controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.live_transcription_paused = True
            
            with col2:
                if st.button("🔄 Restart", use_container_width=True):
                    st.info("Restarting transcription...")
            
            with col3:
                if st.button("⏹️ Stop", type="secondary", use_container_width=True):
                    st.session_state.live_transcription_active = False
                    st.success("Live transcription stopped and saved!")
                    st.rerun()


# Integration with main app
def add_collaboration_features():
    """Add collaboration features to the main app"""
    if 'show_collaboration' not in st.session_state:
        st.session_state.show_collaboration = False
    
    # Add collaboration button to sidebar
    with st.sidebar:
        if st.button("👥 Collaboration", use_container_width=True):
            st.session_state.show_collaboration = not st.session_state.show_collaboration
    
    # Show collaboration panel if enabled
    if st.session_state.show_collaboration:
        with st.container():
            st.markdown("---")
            
            # Get current user and transcript info
            user_id = st.session_state.get('user_id', 'default_user')
            transcript_id = st.session_state.get('current_transcript_id', 'transcript_001')
            
            # Render collaboration UI
            CollaborationUI.render_collaboration_panel(transcript_id, user_id)
            
            # Render live transcription if no active collaboration
            if not st.session_state.get('active_collaboration'):
                st.markdown("---")
                CollaborationUI.render_live_transcription_panel()


# Example usage
if __name__ == "__main__":
    st.set_page_config(
        page_title="Collaboration Demo",
        page_icon="👥",
        layout="wide"
    )
    
    st.title("Real-time Collaboration Demo")
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "demo_user"
    
    if 'current_transcript_id' not in st.session_state:
        st.session_state.current_transcript_id = "demo_transcript_123"
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## Transcript Content")
        st.text_area(
            "Edit transcript collaboratively",
            value="This is a sample transcript that can be edited in real-time by multiple users...",
            height=400,
            key="transcript_editor"
        )
    
    with col2:
        # Render collaboration panel
        CollaborationUI.render_collaboration_panel(
            st.session_state.current_transcript_id,
            st.session_state.user_id
        )
    
    # Show live transcription option
    st.markdown("---")
    CollaborationUI.render_live_transcription_panel()