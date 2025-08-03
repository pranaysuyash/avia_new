#!/usr/bin/env python3
"""
Unified Processing Modes Module
Consolidates and simplifies various processing modes into a coherent system
"""

import streamlit as st
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """Simplified processing modes"""
    QUICK = "quick"          # Fast, basic processing
    STANDARD = "standard"    # Balanced quality/speed
    ADVANCED = "advanced"    # High quality, all features
    CUSTOM = "custom"        # User-defined settings


@dataclass
class ProcessingProfile:
    """Profile defining processing parameters"""
    name: str
    display_name: str
    description: str
    icon: str
    # Core settings
    transcription_model: str
    ner_mode: str
    # Features
    enable_diarization: bool = False
    enable_enhancement: bool = True
    enable_segmentation: bool = False
    enable_summary: bool = True
    enable_insights: bool = False
    # Quality settings
    confidence_threshold: float = 0.7
    chunk_duration: int = 30
    # Time estimate multiplier
    time_factor: float = 1.0


class UnifiedProcessingManager:
    """Manages unified processing modes and configurations"""
    
    # Define processing profiles
    PROFILES = {
        ProcessingMode.QUICK: ProcessingProfile(
            name="quick",
            display_name="Quick Process",
            description="Fast results with basic analysis",
            icon="🚀",
            transcription_model="base",
            ner_mode="basic",
            enable_diarization=False,
            enable_enhancement=False,
            enable_segmentation=False,
            enable_summary=False,
            enable_insights=False,
            confidence_threshold=0.6,
            chunk_duration=60,
            time_factor=0.5
        ),
        ProcessingMode.STANDARD: ProcessingProfile(
            name="standard",
            display_name="Standard Process",
            description="Balanced quality and speed",
            icon="⚡",
            transcription_model="medium",
            ner_mode="basic",
            enable_diarization=False,
            enable_enhancement=True,
            enable_segmentation=False,
            enable_summary=True,
            enable_insights=False,
            confidence_threshold=0.7,
            chunk_duration=30,
            time_factor=1.0
        ),
        ProcessingMode.ADVANCED: ProcessingProfile(
            name="advanced",
            display_name="Advanced Process",
            description="Maximum quality with all features",
            icon="🧠",
            transcription_model="large",
            ner_mode="advanced",
            enable_diarization=True,
            enable_enhancement=True,
            enable_segmentation=True,
            enable_summary=True,
            enable_insights=True,
            confidence_threshold=0.8,
            chunk_duration=20,
            time_factor=2.0
        )
    }
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize processing mode session state"""
        if 'processing_mode' not in st.session_state:
            st.session_state.processing_mode = ProcessingMode.STANDARD
        if 'custom_profile' not in st.session_state:
            st.session_state.custom_profile = None
    
    def render_mode_selector(self) -> ProcessingProfile:
        """Render processing mode selector and return selected profile"""
        st.markdown("### 🎯 Choose Processing Mode")
        
        # Mode selection with visual cards
        cols = st.columns(3)
        selected_mode = st.session_state.processing_mode
        
        for idx, (mode, profile) in enumerate(list(self.PROFILES.items())):
            with cols[idx]:
                # Card-style button
                card_style = "primary" if selected_mode == mode else "secondary"
                
                if st.button(
                    f"{profile.icon}\n**{profile.display_name}**\n{profile.description}",
                    key=f"mode_{mode.value}",
                    use_container_width=True,
                    type=card_style
                ):
                    st.session_state.processing_mode = mode
                    st.rerun()
                
                # Show key features
                with st.expander("Details", expanded=False):
                    self._render_profile_details(profile)
        
        # Custom mode option
        if st.checkbox("🎛️ Customize Settings", key="custom_mode_check"):
            st.session_state.processing_mode = ProcessingMode.CUSTOM
            profile = self._render_custom_settings()
        else:
            profile = self.PROFILES[st.session_state.processing_mode]
        
        # Show selected mode summary
        self._render_mode_summary(profile)
        
        return profile
    
    def _render_profile_details(self, profile: ProcessingProfile):
        """Render details of a processing profile"""
        st.markdown(f"**Model:** {profile.transcription_model}")
        st.markdown(f"**NER:** {profile.ner_mode}")
        
        # Features
        features = []
        if profile.enable_diarization:
            features.append("👥 Speaker Detection")
        if profile.enable_enhancement:
            features.append("🔊 Audio Enhancement")
        if profile.enable_summary:
            features.append("📝 Summary")
        if profile.enable_insights:
            features.append("💡 Insights")
        
        if features:
            st.markdown("**Features:** " + ", ".join(features))
        
        # Time estimate
        st.markdown(f"**Speed:** {'⚡' * int(3 / profile.time_factor)}")
    
    def _render_custom_settings(self) -> ProcessingProfile:
        """Render custom settings interface"""
        st.markdown("#### 🎛️ Custom Settings")
        
        # Base settings
        col1, col2 = st.columns(2)
        
        with col1:
            transcription_model = st.selectbox(
                "Transcription Model",
                ["base", "medium", "large"],
                index=1,
                help="Larger models are more accurate but slower"
            )
            
            ner_mode = st.selectbox(
                "Entity Extraction",
                ["basic", "advanced"],
                help="Advanced uses AI for better results"
            )
        
        with col2:
            confidence_threshold = st.slider(
                "Confidence Threshold",
                0.5, 1.0, 0.7, 0.05,
                help="Higher values = more accurate but fewer results"
            )
            
            chunk_duration = st.slider(
                "Chunk Duration (s)",
                10, 60, 30, 5,
                help="Smaller chunks = better accuracy but slower"
            )
        
        # Features
        st.markdown("#### Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            enable_diarization = st.checkbox(
                "👥 Speaker Detection",
                value=False,
                help="Identify different speakers"
            )
            enable_enhancement = st.checkbox(
                "🔊 Audio Enhancement",
                value=True,
                help="Improve audio quality"
            )
        
        with col2:
            enable_segmentation = st.checkbox(
                "✂️ Segmentation",
                value=False,
                help="Split into logical segments"
            )
            enable_summary = st.checkbox(
                "📝 Summary",
                value=True,
                help="Generate content summary"
            )
        
        with col3:
            enable_insights = st.checkbox(
                "💡 Insights",
                value=False,
                help="Extract key insights"
            )
        
        # Create custom profile
        custom_profile = ProcessingProfile(
            name="custom",
            display_name="Custom Settings",
            description="User-defined configuration",
            icon="🎛️",
            transcription_model=transcription_model,
            ner_mode=ner_mode,
            enable_diarization=enable_diarization,
            enable_enhancement=enable_enhancement,
            enable_segmentation=enable_segmentation,
            enable_summary=enable_summary,
            enable_insights=enable_insights,
            confidence_threshold=confidence_threshold,
            chunk_duration=chunk_duration,
            time_factor=1.5  # Custom is usually slower
        )
        
        st.session_state.custom_profile = custom_profile
        return custom_profile
    
    def _render_mode_summary(self, profile: ProcessingProfile):
        """Render summary of selected mode"""
        st.markdown("---")
        st.markdown(f"### {profile.icon} Selected: {profile.display_name}")
        
        # Show what will happen
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Processing Steps:**")
            steps = ["✅ Upload & Validate"]
            if profile.enable_enhancement:
                steps.append("✅ Enhance Audio")
            steps.append("✅ Transcribe")
            if profile.enable_diarization:
                steps.append("✅ Detect Speakers")
            steps.append("✅ Extract Entities")
            if profile.enable_summary:
                steps.append("✅ Generate Summary")
            if profile.enable_insights:
                steps.append("✅ Extract Insights")
            
            for step in steps:
                st.markdown(f"• {step}")
        
        with col2:
            st.markdown("**Quality Settings:**")
            st.markdown(f"• Model: {profile.transcription_model}")
            st.markdown(f"• NER: {profile.ner_mode}")
            st.markdown(f"• Confidence: {profile.confidence_threshold:.0%}")
            st.markdown(f"• Chunks: {profile.chunk_duration}s")
        
        with col3:
            st.markdown("**Time Estimate:**")
            # Estimate based on file size
            if st.session_state.get('uploaded_file'):
                file_size_mb = st.session_state.uploaded_file.size / (1024 * 1024)
                base_time = file_size_mb * 0.5  # 30 seconds per MB baseline
                estimated_time = base_time * profile.time_factor
                
                if estimated_time < 60:
                    st.markdown(f"⏱️ ~{int(estimated_time)} seconds")
                else:
                    st.markdown(f"⏱️ ~{int(estimated_time / 60)} minutes")
            else:
                st.markdown("⏱️ Upload file to see estimate")
    
    def get_processing_config(self, profile: ProcessingProfile) -> Dict[str, Any]:
        """Convert profile to processing configuration"""
        return {
            'mode': profile.name,
            'transcription': {
                'model': profile.transcription_model,
                'chunk_duration': profile.chunk_duration,
                'language': 'auto'  # Can be overridden
            },
            'ner': {
                'mode': profile.ner_mode,
                'confidence_threshold': profile.confidence_threshold
            },
            'features': {
                'diarization': profile.enable_diarization,
                'enhancement': profile.enable_enhancement,
                'segmentation': profile.enable_segmentation,
                'summary': profile.enable_summary,
                'insights': profile.enable_insights
            }
        }
    
    def render_quick_mode_toggle(self) -> ProcessingMode:
        """Render a quick mode toggle for sidebar"""
        mode = st.radio(
            "Processing Mode",
            options=[
                ProcessingMode.QUICK,
                ProcessingMode.STANDARD,
                ProcessingMode.ADVANCED
            ],
            format_func=lambda x: f"{self.PROFILES[x].icon} {self.PROFILES[x].display_name}",
            index=1,
            horizontal=True
        )
        st.session_state.processing_mode = mode
        return mode
    
    def estimate_processing_time(self, file_size_bytes: int, profile: ProcessingProfile) -> float:
        """Estimate processing time in seconds"""
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Base time calculation (varies by model)
        model_times = {
            'base': 0.3,    # 0.3 seconds per MB
            'medium': 0.5,  # 0.5 seconds per MB
            'large': 1.0    # 1.0 seconds per MB
        }
        
        base_time = file_size_mb * model_times.get(profile.transcription_model, 0.5)
        
        # Add time for features
        feature_time = 0
        if profile.enable_enhancement:
            feature_time += file_size_mb * 0.1
        if profile.enable_diarization:
            feature_time += file_size_mb * 0.3
        if profile.enable_summary:
            feature_time += 5  # Fixed time for summary
        if profile.enable_insights:
            feature_time += 10  # Fixed time for insights
        
        total_time = (base_time + feature_time) * profile.time_factor
        return max(5, total_time)  # Minimum 5 seconds


# Convenience functions
def get_processing_manager() -> UnifiedProcessingManager:
    """Get or create the processing manager instance"""
    if 'processing_manager' not in st.session_state:
        st.session_state.processing_manager = UnifiedProcessingManager()
    return st.session_state.processing_manager


def render_processing_mode_selector() -> ProcessingProfile:
    """Render processing mode selector and return selected profile"""
    manager = get_processing_manager()
    return manager.render_mode_selector()


def get_current_processing_config() -> Dict[str, Any]:
    """Get the current processing configuration"""
    manager = get_processing_manager()
    
    if st.session_state.processing_mode == ProcessingMode.CUSTOM:
        profile = st.session_state.custom_profile
    else:
        profile = manager.PROFILES[st.session_state.processing_mode]
    
    return manager.get_processing_config(profile)