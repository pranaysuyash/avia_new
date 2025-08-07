"""
User Onboarding and Welcome Tour System
Provides guided experience for new users
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class OnboardingManager:
    """Manages user onboarding flow and welcome tours"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize onboarding session state"""
        if 'onboarding_completed' not in st.session_state:
            st.session_state.onboarding_completed = False
        if 'current_tour_step' not in st.session_state:
            st.session_state.current_tour_step = 0
        if 'show_welcome_tour' not in st.session_state:
            st.session_state.show_welcome_tour = False
        if 'onboarding_progress' not in st.session_state:
            st.session_state.onboarding_progress = {}
    
    def should_show_onboarding(self) -> bool:
        """Check if onboarding should be shown"""
        return (not st.session_state.onboarding_completed and 
                not st.session_state.get('skip_onboarding', False))
    
    def render_welcome_modal(self):
        """Render welcome modal for new users"""
        if not self.should_show_onboarding():
            return
        
        with st.container():
            st.markdown("""
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.7);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
            ">
                <div style="
                    background: white;
                    padding: 40px;
                    border-radius: 15px;
                    max-width: 600px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                ">
                    <h1>🎉 Welcome to Audio/Video Transcription AI!</h1>
                    <p style="font-size: 1.2em; color: #666; margin: 20px 0;">
                        Transform your audio and video content into searchable, actionable insights with AI-powered transcription and analysis.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Welcome content
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("# 🎉 Welcome!")
            st.markdown("""
            ### Get Started in 3 Easy Steps:
            
            1. **📁 Upload** your audio or video file
            2. **⚡ Process** with AI-powered transcription
            3. **📊 Analyze** and export your results
            
            ### What You Can Do:
            - 🎯 **Interactive Transcripts** - Click to jump to any part
            - 👥 **Speaker Identification** - Automatic speaker detection
            - 🔍 **Smart Search** - Find content instantly
            - 📥 **Multiple Exports** - TXT, PDF, SRT, VTT and more
            - 🤖 **AI Insights** - Get summaries and key points
            """)
            
            col_start, col_tour, col_skip = st.columns(3)
            
            with col_start:
                if st.button("🚀 Get Started", type="primary", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.session_state.onboarding_progress['started'] = datetime.now().isoformat()
                    st.rerun()
            
            with col_tour:
                if st.button("🎯 Take Tour", use_container_width=True):
                    st.session_state.show_welcome_tour = True
                    st.session_state.current_tour_step = 0
                    st.rerun()
            
            with col_skip:
                if st.button("⏭️ Skip", use_container_width=True):
                    st.session_state.skip_onboarding = True
                    st.rerun()
    
    def render_welcome_tour(self):
        """Render step-by-step welcome tour"""
        if not st.session_state.get('show_welcome_tour', False):
            return
        
        tour_steps = self.get_tour_steps()
        current_step = st.session_state.current_tour_step
        
        if current_step >= len(tour_steps):
            # Tour completed
            st.session_state.show_welcome_tour = False
            st.session_state.onboarding_completed = True
            st.session_state.onboarding_progress['tour_completed'] = datetime.now().isoformat()
            st.success("🎉 Welcome tour completed! You're ready to start transcribing.")
            return
        
        step = tour_steps[current_step]
        
        # Tour overlay
        with st.container():
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
                position: relative;
            ">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <h3>📍 Step {current_step + 1} of {len(tour_steps)}: {step['title']}</h3>
                    <div style="background: rgba(255,255,255,0.2); padding: 5px 15px; border-radius: 20px;">
                        {current_step + 1}/{len(tour_steps)}
                    </div>
                </div>
                <p style="margin: 15px 0;">{step['description']}</p>
                {step.get('tip', '')}
            </div>
            """, unsafe_allow_html=True)
        
        # Tour navigation
        col_prev, col_progress, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if current_step > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.current_tour_step -= 1
                    st.rerun()
            else:
                st.button("⬅️ Previous", disabled=True, use_container_width=True)
        
        with col_progress:
            progress = (current_step + 1) / len(tour_steps)
            st.progress(progress, f"Tour Progress: {progress:.0%}")
        
        with col_next:
            if st.button("➡️ Next", use_container_width=True):
                st.session_state.current_tour_step += 1
                st.rerun()
        
        # Skip tour option
        if st.button("⏭️ Skip Tour"):
            st.session_state.show_welcome_tour = False
            st.session_state.onboarding_completed = True
            st.rerun()
    
    def get_tour_steps(self) -> List[Dict[str, str]]:
        """Get tour steps configuration"""
        return [
            {
                'title': 'Upload Your Media',
                'description': 'Start by uploading an audio or video file using the file uploader below. We support MP3, WAV, MP4, and many other formats.',
                'tip': '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">💡 <strong>Tip:</strong> For best results, use clear audio with minimal background noise.</div>'
            },
            {
                'title': 'Choose Processing Mode',
                'description': 'Select between Basic Mode (fast, local processing) or Advanced Mode (AI-powered analysis with insights and summaries).',
                'tip': '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">💡 <strong>Tip:</strong> Advanced Mode provides speaker identification and AI insights.</div>'
            },
            {
                'title': 'Review Your Transcript',
                'description': 'Once processing is complete, you\'ll see your interactive transcript with clickable segments, speaker identification, and confidence scores.',
                'tip': '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">💡 <strong>Tip:</strong> Click on any timestamp to jump to that part of the audio.</div>'
            },
            {
                'title': 'Search and Edit',
                'description': 'Use the search bar to find specific content in your transcript. Enable Edit Mode to make corrections and improvements.',
                'tip': '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">💡 <strong>Tip:</strong> Your edits are saved automatically and highlighted with an orange border.</div>'
            },
            {
                'title': 'Export and Share',
                'description': 'Export your transcript in multiple formats including TXT, PDF, SRT subtitles, and more. Use the Quick Export buttons for instant downloads.',
                'tip': '<div style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; margin-top: 10px;">💡 <strong>Tip:</strong> SRT and VTT exports are perfect for adding subtitles to videos.</div>'
            }
        ]
    
    def render_help_tooltips(self):
        """Render contextual help tooltips"""
        if st.session_state.get('show_help_tooltips', True):
            with st.expander("💡 Quick Tips", expanded=False):
                st.markdown("""
                ### 🚀 Getting Better Results
                
                **Audio Quality Tips:**
                - Use high-quality audio files (44.1kHz or higher)
                - Minimize background noise
                - Ensure clear speech with good volume levels
                
                **Processing Tips:**
                - Basic Mode: Fast processing, works offline
                - Advanced Mode: AI insights, speaker detection, summaries
                - Longer files may take several minutes to process
                
                **Using Features:**
                - **Click-to-Play**: Click timestamps to jump to audio position
                - **Edit Mode**: Make corrections directly in the transcript
                - **Search**: Find specific words or phrases instantly
                - **Export**: Download in multiple formats for different uses
                """)
    
    def render_sample_media_section(self):
        """Render sample media files for testing"""
        with st.expander("🎬 Try Sample Files", expanded=False):
            st.markdown("### Test with Sample Audio/Video")
            st.markdown("Don't have a file ready? Try these sample files to explore the features:")
            
            samples = self.get_sample_files()
            
            for sample in samples:
                col_info, col_action = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"""
                    **{sample['name']}** ({sample['duration']})  
                    *{sample['description']}*
                    """)
                
                with col_action:
                    if st.button(f"📁 Use", key=f"sample_{sample['id']}"):
                        self.load_sample_file(sample)
    
    def get_sample_files(self) -> List[Dict[str, Any]]:
        """Get list of sample files for testing"""
        return [
            {
                'id': 'business_meeting',
                'name': 'Business Meeting',
                'duration': '2:30',
                'description': 'Multiple speakers discussing quarterly results',
                'file_path': 'test_data/audio/business_meeting.wav',
                'type': 'audio'
            },
            {
                'id': 'technical_interview',
                'name': 'Technical Interview',
                'duration': '1:45',
                'description': 'Job interview with technical questions',
                'file_path': 'test_data/audio/technical_interview.wav',
                'type': 'audio'
            },
            {
                'id': 'educational_lecture',
                'name': 'Educational Lecture',
                'duration': '3:15',
                'description': 'University lecture on machine learning',
                'file_path': 'test_data/audio/educational_lecture.wav',
                'type': 'audio'
            }
        ]
    
    def load_sample_file(self, sample: Dict[str, Any]):
        """Load a sample file for testing"""
        try:
            st.session_state.sample_file_selected = sample
            st.session_state.use_sample_file = True
            st.success(f"✅ Loaded sample: {sample['name']}")
            st.info("👆 Click 'Process Audio' above to transcribe this sample file.")
        except Exception as e:
            st.error(f"Failed to load sample file: {str(e)}")
            logger.error(f"Sample file loading error: {e}")
    
    def track_onboarding_progress(self, event: str, data: Optional[Dict] = None):
        """Track onboarding progress and user actions"""
        if 'onboarding_analytics' not in st.session_state:
            st.session_state.onboarding_analytics = []
        
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event': event,
            'data': data or {},
            'session_id': st.session_state.get('session_id', 'anonymous')
        }
        
        st.session_state.onboarding_analytics.append(event_data)
        logger.info(f"Onboarding event: {event}")
    
    def render_progress_indicator(self):
        """Show onboarding progress"""
        if st.session_state.get('onboarding_completed', False):
            return
        
        progress_items = [
            ('Welcome', st.session_state.get('onboarding_progress', {}).get('started')),
            ('First Upload', st.session_state.get('onboarding_progress', {}).get('first_upload')),
            ('First Transcription', st.session_state.get('onboarding_progress', {}).get('first_transcription')),
            ('First Export', st.session_state.get('onboarding_progress', {}).get('first_export'))
        ]
        
        completed = sum(1 for _, completed in progress_items if completed)
        total = len(progress_items)
        
        if completed > 0:
            with st.sidebar:
                st.markdown("### 🎯 Getting Started")
                progress = completed / total
                st.progress(progress, f"Progress: {completed}/{total}")
                
                for item, is_completed in progress_items:
                    icon = "✅" if is_completed else "⭕"
                    st.write(f"{icon} {item}")


def render_onboarding_ui():
    """Main function to render onboarding UI"""
    onboarding = OnboardingManager()
    
    # Show welcome modal for new users
    if onboarding.should_show_onboarding():
        onboarding.render_welcome_modal()
    
    # Show welcome tour if active
    onboarding.render_welcome_tour()
    
    # Show help tooltips
    onboarding.render_help_tooltips()
    
    # Show sample media section
    onboarding.render_sample_media_section()
    
    # Show progress indicator
    onboarding.render_progress_indicator()
    
    return onboarding


def create_sample_files():
    """Create sample audio files for testing (placeholder)"""
    import os
    from pathlib import Path
    
    sample_dir = Path("test_data/audio")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Create placeholder sample files (in real implementation, these would be actual audio files)
    samples = [
        "business_meeting.wav",
        "technical_interview.wav", 
        "educational_lecture.wav",
        "customer_service.wav",
        "medical_consultation.wav"
    ]
    
    for sample in samples:
        sample_path = sample_dir / sample
        if not sample_path.exists():
            # Create empty placeholder files
            sample_path.touch()
    
    logger.info(f"Created {len(samples)} sample file placeholders")


if __name__ == "__main__":
    # Create sample files
    create_sample_files()
    
    # Demo onboarding
    st.title("User Onboarding Demo")
    render_onboarding_ui()