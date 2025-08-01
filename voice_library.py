#!/usr/bin/env python3
"""
Voice Library Management Module
Manages TTS voice library with custom voices, presets, and voice profiles
"""

import streamlit as st
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import tempfile

logger = logging.getLogger(__name__)

@dataclass
class VoiceProfile:
    """Voice profile data structure"""
    id: str
    name: str
    description: str
    voice_id: str  # ElevenLabs voice ID
    settings: Dict[str, float]
    category: str
    is_custom: bool = False
    created_date: str = ""
    usage_count: int = 0
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()

@dataclass
class VoiceSettings:
    """Voice synthesis settings"""
    stability: float = 0.75
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True

class VoiceLibraryManager:
    """Manages voice library and TTS voice profiles"""
    
    def __init__(self):
        self.library_file = "voice_library.json"
        self.default_voices = self._get_default_voices()
    
    def _get_default_voices(self) -> List[VoiceProfile]:
        """Get default voice profiles"""
        return [
            VoiceProfile(
                id="professional_male",
                name="Professional Male",
                description="Clear, authoritative male voice for business content",
                voice_id="21m00Tcm4TlvDq8ikWAM",  # ElevenLabs default
                settings={"stability": 0.8, "similarity_boost": 0.7, "style": 0.0},
                category="Professional"
            ),
            VoiceProfile(
                id="professional_female",
                name="Professional Female",
                description="Clear, confident female voice for presentations",
                voice_id="EXAVITQu4vr4xnSDxMaL",  # ElevenLabs default
                settings={"stability": 0.8, "similarity_boost": 0.7, "style": 0.0},
                category="Professional"
            ),
            VoiceProfile(
                id="conversational_male",
                name="Conversational Male",
                description="Friendly, casual male voice for informal content",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                settings={"stability": 0.6, "similarity_boost": 0.8, "style": 0.2},
                category="Conversational"
            ),
            VoiceProfile(
                id="conversational_female",
                name="Conversational Female",
                description="Warm, approachable female voice for casual content",
                voice_id="EXAVITQu4vr4xnSDxMaL",
                settings={"stability": 0.6, "similarity_boost": 0.8, "style": 0.2},
                category="Conversational"
            ),
            VoiceProfile(
                id="narrative_male",
                name="Narrative Male",
                description="Engaging male voice for storytelling and narration",
                voice_id="21m00Tcm4TlvDq8ikWAM",
                settings={"stability": 0.7, "similarity_boost": 0.9, "style": 0.4},
                category="Narrative"
            ),
            VoiceProfile(
                id="narrative_female",
                name="Narrative Female",
                description="Expressive female voice for stories and audiobooks",
                voice_id="EXAVITQu4vr4xnSDxMaL",
                settings={"stability": 0.7, "similarity_boost": 0.9, "style": 0.4},
                category="Narrative"
            )
        ]
    
    def load_voice_library(self) -> List[VoiceProfile]:
        """Load voice library from file"""
        try:
            if os.path.exists(self.library_file):
                with open(self.library_file, 'r') as f:
                    data = json.load(f)
                    return [VoiceProfile(**voice) for voice in data.get('voices', [])]
            else:
                # Initialize with default voices
                self.save_voice_library(self.default_voices)
                return self.default_voices
        except Exception as e:
            logger.error(f"Failed to load voice library: {e}")
            return self.default_voices
    
    def save_voice_library(self, voices: List[VoiceProfile]):
        """Save voice library to file"""
        try:
            data = {
                'voices': [asdict(voice) for voice in voices],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.library_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save voice library: {e}")
    
    def add_voice_profile(self, voice: VoiceProfile) -> bool:
        """Add a new voice profile"""
        try:
            voices = self.load_voice_library()
            
            # Check for duplicate IDs
            if any(v.id == voice.id for v in voices):
                return False
            
            voices.append(voice)
            self.save_voice_library(voices)
            return True
        except Exception as e:
            logger.error(f"Failed to add voice profile: {e}")
            return False
    
    def update_voice_profile(self, voice_id: str, updated_voice: VoiceProfile) -> bool:
        """Update an existing voice profile"""
        try:
            voices = self.load_voice_library()
            
            for i, voice in enumerate(voices):
                if voice.id == voice_id:
                    voices[i] = updated_voice
                    self.save_voice_library(voices)
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Failed to update voice profile: {e}")
            return False
    
    def delete_voice_profile(self, voice_id: str) -> bool:
        """Delete a voice profile"""
        try:
            voices = self.load_voice_library()
            
            # Don't allow deletion of default voices
            default_ids = {v.id for v in self.default_voices}
            if voice_id in default_ids:
                return False
            
            voices = [v for v in voices if v.id != voice_id]
            self.save_voice_library(voices)
            return True
        except Exception as e:
            logger.error(f"Failed to delete voice profile: {e}")
            return False
    
    def get_voice_profile(self, voice_id: str) -> Optional[VoiceProfile]:
        """Get a specific voice profile"""
        voices = self.load_voice_library()
        return next((v for v in voices if v.id == voice_id), None)
    
    def increment_usage(self, voice_id: str):
        """Increment usage count for a voice"""
        try:
            voices = self.load_voice_library()
            
            for voice in voices:
                if voice.id == voice_id:
                    voice.usage_count += 1
                    break
            
            self.save_voice_library(voices)
        except Exception as e:
            logger.error(f"Failed to increment usage: {e}")
    
    def render_voice_library_ui(self):
        """Render voice library management UI"""
        st.header("🎤 Voice Library Management")
        
        # Load voices
        voices = self.load_voice_library()
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📚 Voice Library", "➕ Add Voice", "📊 Usage Stats"])
        
        with tab1:
            self.render_voice_list(voices)
        
        with tab2:
            self.render_add_voice_form()
        
        with tab3:
            self.render_usage_statistics(voices)
    
    def render_voice_list(self, voices: List[VoiceProfile]):
        """Render the list of available voices"""
        st.subheader("Available Voices")
        
        # Group voices by category
        categories = {}
        for voice in voices:
            if voice.category not in categories:
                categories[voice.category] = []
            categories[voice.category].append(voice)
        
        # Display voices by category
        for category, category_voices in categories.items():
            st.markdown(f"### {category}")
            
            for voice in category_voices:
                with st.expander(f"🎵 {voice.name}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {voice.description}")
                        st.write(f"**Voice ID:** {voice.voice_id}")
                        st.write(f"**Usage Count:** {voice.usage_count}")
                        
                        if voice.is_custom:
                            st.badge("Custom", type="secondary")
                        else:
                            st.badge("Default", type="primary")
                    
                    with col2:
                        st.write("**Settings:**")
                        st.write(f"• Stability: {voice.settings.get('stability', 0.75)}")
                        st.write(f"• Similarity Boost: {voice.settings.get('similarity_boost', 0.75)}")
                        st.write(f"• Style: {voice.settings.get('style', 0.0)}")
                    
                    with col3:
                        # Test voice button
                        if st.button(f"🔊 Test", key=f"test_{voice.id}"):
                            self.test_voice(voice)
                        
                        # Edit button (only for custom voices)
                        if voice.is_custom:
                            if st.button(f"✏️ Edit", key=f"edit_{voice.id}"):
                                st.session_state[f"editing_{voice.id}"] = True
                                st.rerun()
                        
                        # Delete button (only for custom voices)
                        if voice.is_custom:
                            if st.button(f"🗑️ Delete", key=f"delete_{voice.id}"):
                                if self.delete_voice_profile(voice.id):
                                    st.success(f"Deleted voice: {voice.name}")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete voice")
                    
                    # Edit form (if editing)
                    if st.session_state.get(f"editing_{voice.id}", False):
                        self.render_edit_voice_form(voice)
    
    def render_add_voice_form(self):
        """Render form to add new voice"""
        st.subheader("Add New Voice Profile")
        
        with st.form("add_voice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                voice_id = st.text_input(
                    "Voice ID*",
                    help="Unique identifier for this voice profile"
                )
                
                voice_name = st.text_input(
                    "Voice Name*",
                    help="Display name for this voice"
                )
                
                voice_description = st.text_area(
                    "Description*",
                    help="Description of this voice's characteristics"
                )
                
                elevenlabs_voice_id = st.text_input(
                    "ElevenLabs Voice ID*",
                    help="The actual voice ID from ElevenLabs"
                )
            
            with col2:
                category = st.selectbox(
                    "Category*",
                    ["Professional", "Conversational", "Narrative", "Educational", "Entertainment", "Custom"],
                    help="Category for organizing voices"
                )
                
                st.markdown("**Voice Settings:**")
                
                stability = st.slider(
                    "Stability",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.75,
                    step=0.05,
                    help="Higher values make voice more consistent but less expressive"
                )
                
                similarity_boost = st.slider(
                    "Similarity Boost",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.75,
                    step=0.05,
                    help="Higher values make voice more similar to original"
                )
                
                style = st.slider(
                    "Style",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.05,
                    help="Higher values add more style and emotion"
                )
            
            submitted = st.form_submit_button("➕ Add Voice Profile")
            
            if submitted:
                if not all([voice_id, voice_name, voice_description, elevenlabs_voice_id]):
                    st.error("Please fill in all required fields")
                else:
                    new_voice = VoiceProfile(
                        id=voice_id,
                        name=voice_name,
                        description=voice_description,
                        voice_id=elevenlabs_voice_id,
                        settings={
                            "stability": stability,
                            "similarity_boost": similarity_boost,
                            "style": style
                        },
                        category=category,
                        is_custom=True
                    )
                    
                    if self.add_voice_profile(new_voice):
                        st.success(f"Added voice profile: {voice_name}")
                        st.rerun()
                    else:
                        st.error("Failed to add voice profile. Voice ID may already exist.")
    
    def render_edit_voice_form(self, voice: VoiceProfile):
        """Render form to edit existing voice"""
        st.markdown("---")
        st.markdown(f"**Editing: {voice.name}**")
        
        with st.form(f"edit_voice_form_{voice.id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Voice Name", value=voice.name)
                new_description = st.text_area("Description", value=voice.description)
                new_voice_id = st.text_input("ElevenLabs Voice ID", value=voice.voice_id)
            
            with col2:
                new_category = st.selectbox(
                    "Category",
                    ["Professional", "Conversational", "Narrative", "Educational", "Entertainment", "Custom"],
                    index=["Professional", "Conversational", "Narrative", "Educational", "Entertainment", "Custom"].index(voice.category)
                )
                
                new_stability = st.slider(
                    "Stability",
                    min_value=0.0,
                    max_value=1.0,
                    value=voice.settings.get('stability', 0.75),
                    step=0.05
                )
                
                new_similarity_boost = st.slider(
                    "Similarity Boost",
                    min_value=0.0,
                    max_value=1.0,
                    value=voice.settings.get('similarity_boost', 0.75),
                    step=0.05
                )
                
                new_style = st.slider(
                    "Style",
                    min_value=0.0,
                    max_value=1.0,
                    value=voice.settings.get('style', 0.0),
                    step=0.05
                )
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                save_changes = st.form_submit_button("💾 Save Changes")
            
            with col_cancel:
                cancel_edit = st.form_submit_button("❌ Cancel")
            
            if save_changes:
                updated_voice = VoiceProfile(
                    id=voice.id,
                    name=new_name,
                    description=new_description,
                    voice_id=new_voice_id,
                    settings={
                        "stability": new_stability,
                        "similarity_boost": new_similarity_boost,
                        "style": new_style
                    },
                    category=new_category,
                    is_custom=voice.is_custom,
                    created_date=voice.created_date,
                    usage_count=voice.usage_count
                )
                
                if self.update_voice_profile(voice.id, updated_voice):
                    st.success("Voice profile updated successfully")
                    st.session_state[f"editing_{voice.id}"] = False
                    st.rerun()
                else:
                    st.error("Failed to update voice profile")
            
            if cancel_edit:
                st.session_state[f"editing_{voice.id}"] = False
                st.rerun()
    
    def render_usage_statistics(self, voices: List[VoiceProfile]):
        """Render voice usage statistics"""
        st.subheader("Voice Usage Statistics")
        
        if not voices:
            st.info("No voices available")
            return
        
        # Sort voices by usage count
        sorted_voices = sorted(voices, key=lambda v: v.usage_count, reverse=True)
        
        # Usage chart
        voice_names = [v.name for v in sorted_voices]
        usage_counts = [v.usage_count for v in sorted_voices]
        
        if any(count > 0 for count in usage_counts):
            import plotly.express as px
            
            fig = px.bar(
                x=voice_names,
                y=usage_counts,
                title="Voice Usage Statistics",
                labels={'x': 'Voice', 'y': 'Usage Count'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No usage data available yet")
        
        # Usage table
        st.markdown("### Detailed Usage")
        
        usage_data = []
        for voice in sorted_voices:
            usage_data.append({
                'Voice Name': voice.name,
                'Category': voice.category,
                'Usage Count': voice.usage_count,
                'Type': 'Custom' if voice.is_custom else 'Default',
                'Created': voice.created_date[:10] if voice.created_date else 'N/A'
            })
        
        import pandas as pd
        df = pd.DataFrame(usage_data)
        st.dataframe(df, use_container_width=True)
    
    def test_voice(self, voice: VoiceProfile):
        """Test a voice with sample text"""
        try:
            sample_text = "Hello! This is a test of the voice profile. How does it sound?"
            
            # Here you would integrate with the actual TTS system
            st.info(f"Testing voice: {voice.name}")
            st.write(f"Sample text: '{sample_text}'")
            st.write(f"Voice settings: {voice.settings}")
            
            # Increment usage count
            self.increment_usage(voice.id)
            
            # In a real implementation, you would:
            # 1. Call the TTS API with the voice settings
            # 2. Generate audio
            # 3. Play the audio in the UI
            
        except Exception as e:
            st.error(f"Failed to test voice: {e}")

# Global voice library manager instance
voice_library_manager = VoiceLibraryManager()