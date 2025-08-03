#!/usr/bin/env python3
"""
Refactored Sidebar Module
Organizes sidebar content into logical groups with better hierarchy
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple
from config import Config


class SidebarManager:
    """Manages sidebar organization and state"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize sidebar-related session state"""
        if 'sidebar_mode' not in st.session_state:
            st.session_state.sidebar_mode = 'simple'  # simple or advanced
        if 'active_features' not in st.session_state:
            st.session_state.active_features = set()
    
    def render(self, api_status: Dict[str, bool], theme_manager: Any):
        """Render the organized sidebar"""
        # Theme selector at top
        theme_manager.render_theme_selector()
        
        # App title and mode switcher
        st.sidebar.title("Transcribe AI")
        
        # Simple/Advanced mode toggle
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("✨ Simple", 
                        use_container_width=True,
                        type="primary" if st.session_state.sidebar_mode == 'simple' else "secondary"):
                st.session_state.sidebar_mode = 'simple'
        with col2:
            if st.button("⚙️ Advanced", 
                        use_container_width=True,
                        type="primary" if st.session_state.sidebar_mode == 'advanced' else "secondary"):
                st.session_state.sidebar_mode = 'advanced'
        
        st.sidebar.markdown("---")
        
        if st.session_state.sidebar_mode == 'simple':
            self._render_simple_mode(api_status)
        else:
            self._render_advanced_mode(api_status)
        
        # Always show help at bottom
        self._render_help_section()
    
    def _render_simple_mode(self, api_status: Dict[str, bool]):
        """Render simplified sidebar for basic users"""
        # Essential options only
        st.sidebar.subheader("🎯 Quick Start")
        
        # Analysis mode - simplified
        analysis_mode = st.sidebar.radio(
            "Choose Processing Type",
            ["🚀 Fast (Basic)", "🧠 Smart (AI-Powered)", "👥 Multi-Speaker"],
            help="Select how to process your audio",
            key="simple_analysis_mode"
        )
        
        # Map to actual modes
        mode_mapping = {
            "🚀 Fast (Basic)": "Basic (spaCy)",
            "🧠 Smart (AI-Powered)": "Advanced (OpenAI)",
            "👥 Multi-Speaker": "Advanced+ (Speaker Diarization)"
        }
        st.session_state.analysis_mode = mode_mapping[analysis_mode]
        
        # Show API status only if needed
        if "Smart" in analysis_mode or "Multi" in analysis_mode:
            if not api_status["openai"]:
                st.sidebar.warning("⚠️ Requires OpenAI API key")
                with st.sidebar.expander("How to setup"):
                    st.markdown("""
                    1. Get API key from [OpenAI](https://platform.openai.com/)
                    2. Add to `.env` file:
                    ```
                    OPENAI_API_KEY=your-key-here
                    ```
                    3. Restart the app
                    """)
        
        # Audio quality option
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎵 Audio Options")
        
        audio_quality = st.sidebar.select_slider(
            "Processing Quality",
            options=["Fast", "Balanced", "High Quality"],
            value="Balanced",
            help="Higher quality takes longer but gives better results"
        )
        st.session_state.audio_quality = audio_quality
        
        # Single checkbox for batch mode
        if st.sidebar.checkbox("📦 Process Multiple Files", key="simple_batch"):
            st.session_state.active_features.add('batch')
        else:
            st.session_state.active_features.discard('batch')
    
    def _render_advanced_mode(self, api_status: Dict[str, bool]):
        """Render full sidebar for power users"""
        # API Status
        self._render_api_status_compact(api_status)
        
        # Core Settings
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Core Settings")
        
        # Analysis mode with full options
        st.session_state.analysis_mode = st.sidebar.selectbox(
            "Analysis Mode",
            ["Basic (spaCy)", "Advanced (OpenAI)", "Advanced+ (Speaker Diarization)"],
            help="Choose your processing engine"
        )
        
        # Features - organized into logical groups
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔧 Features")
        
        # Use tabs for feature categories
        tab1, tab2, tab3 = st.sidebar.tabs(["Process", "Search", "Export"])
        
        with tab1:
            self._render_processing_features()
        
        with tab2:
            self._render_search_features()
        
        with tab3:
            self._render_export_features()
        
        # Advanced Settings (collapsed by default)
        st.sidebar.markdown("---")
        with st.sidebar.expander("🔬 Advanced Settings"):
            self._render_advanced_settings()
        
        # Integrations (only if available)
        if self._check_integrations_available():
            st.sidebar.markdown("---")
            with st.sidebar.expander("🔗 Integrations"):
                self._render_integrations()
    
    def _render_api_status_compact(self, api_status: Dict[str, bool]):
        """Render compact API status"""
        status_icons = []
        if api_status.get("openai"):
            status_icons.append("✅ OpenAI")
        else:
            status_icons.append("❌ OpenAI")
        
        if api_status.get("elevenlabs"):
            status_icons.append("✅ ElevenLabs")
        else:
            status_icons.append("⚠️ ElevenLabs")
        
        st.sidebar.caption("API Status: " + " | ".join(status_icons))
    
    def _render_processing_features(self):
        """Render processing-related features"""
        if st.checkbox("📦 Batch Processing", key="adv_batch"):
            st.session_state.active_features.add('batch')
        else:
            st.session_state.active_features.discard('batch')
        
        if st.checkbox("🎛️ Audio Enhancement", key="adv_enhance"):
            st.session_state.active_features.add('enhance_audio')
        else:
            st.session_state.active_features.discard('enhance_audio')
        
        if st.checkbox("✂️ Audio Segmentation", key="adv_segment"):
            st.session_state.active_features.add('segment_audio')
        else:
            st.session_state.active_features.discard('segment_audio')
        
        if st.checkbox("🔊 Real-time Processing", key="adv_realtime"):
            st.session_state.active_features.add('realtime')
        else:
            st.session_state.active_features.discard('realtime')
    
    def _render_search_features(self):
        """Render search-related features"""
        if st.checkbox("🔍 Advanced Search", key="adv_search"):
            st.session_state.active_features.add('search')
        else:
            st.session_state.active_features.discard('search')
        
        if st.checkbox("🧠 Semantic Search", key="adv_semantic"):
            st.session_state.active_features.add('semantic_search')
        else:
            st.session_state.active_features.discard('semantic_search')
        
        if st.checkbox("📊 Analytics", key="adv_analytics"):
            st.session_state.active_features.add('analytics')
        else:
            st.session_state.active_features.discard('analytics')
    
    def _render_export_features(self):
        """Render export-related features"""
        if st.checkbox("📄 Advanced Export", key="adv_export"):
            st.session_state.active_features.add('export')
        else:
            st.session_state.active_features.discard('export')
        
        if st.checkbox("📋 Templates", key="adv_templates"):
            st.session_state.active_features.add('templates')
        else:
            st.session_state.active_features.discard('templates')
        
        if st.checkbox("🎤 Voice Library", key="adv_voice"):
            st.session_state.active_features.add('voice_library')
        else:
            st.session_state.active_features.discard('voice_library')
    
    def _render_advanced_settings(self):
        """Render advanced settings"""
        # Transcription settings
        st.markdown("**Transcription Settings**")
        
        chunk_duration = st.slider(
            "Chunk Duration (seconds)",
            min_value=10,
            max_value=60,
            value=30,
            key="chunk_duration"
        )
        
        language = st.selectbox(
            "Language",
            ["Auto-detect", "English", "Spanish", "French", "German", "Italian"],
            key="transcription_language"
        )
        
        # NER settings
        st.markdown("**Entity Extraction**")
        
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="ner_confidence"
        )
        
        # Admin features
        if st.checkbox("👨‍💼 Admin Mode", key="admin_mode"):
            st.session_state.active_features.add('admin')
        else:
            st.session_state.active_features.discard('admin')
    
    def _render_integrations(self):
        """Render integration options"""
        if st.checkbox("🔗 Webhooks"):
            st.session_state.active_features.add('webhooks')
        else:
            st.session_state.active_features.discard('webhooks')
        
        if st.checkbox("☁️ Cloud Storage"):
            st.session_state.active_features.add('cloud_storage')
        else:
            st.session_state.active_features.discard('cloud_storage')
        
        if st.checkbox("🔌 Plugins"):
            st.session_state.active_features.add('plugins')
        else:
            st.session_state.active_features.discard('plugins')
    
    def _render_help_section(self):
        """Render help section at bottom"""
        st.sidebar.markdown("---")
        with st.sidebar.expander("💡 Help", expanded=False):
            if st.session_state.sidebar_mode == 'simple':
                st.markdown("""
                **Quick Tips:**
                • Upload audio or video files
                • Choose processing type
                • Click "Process" to start
                
                **Need more options?**
                Switch to Advanced mode above
                """)
            else:
                st.markdown(f"""
                **File Limits:**
                • Max size: {Config.MAX_FILE_SIZE_MB}MB
                • Formats: MP3, WAV, M4A, MP4, AVI, MOV
                
                **Tips:**
                • Use tabs to find features
                • Hover over (?) for help
                • Check API status above
                
                [📖 Documentation](https://docs.example.com)
                """)
    
    def _check_integrations_available(self) -> bool:
        """Check if integration modules are available"""
        try:
            import integrations
            return True
        except ImportError:
            return False
    
    def get_active_mode(self) -> str:
        """Get the current analysis mode"""
        return st.session_state.get('analysis_mode', 'Basic (spaCy)')
    
    def get_active_features(self) -> set:
        """Get the set of active features"""
        return st.session_state.get('active_features', set())
    
    def is_feature_active(self, feature: str) -> bool:
        """Check if a specific feature is active"""
        return feature in self.get_active_features()


# Convenience function for backward compatibility
def render_sidebar(api_status: Dict[str, bool], theme_manager: Any) -> Tuple[str, set]:
    """
    Render sidebar and return active mode and features
    
    Returns:
        Tuple of (analysis_mode, active_features)
    """
    sidebar = SidebarManager()
    sidebar.render(api_status, theme_manager)
    return sidebar.get_active_mode(), sidebar.get_active_features()