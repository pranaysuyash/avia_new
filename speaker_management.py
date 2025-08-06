"""
Speaker Management Interface
Allows users to rename speakers and manage speaker identities
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class SpeakerManager:
    """Manages speaker names and identities"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state for speaker management"""
        if 'speaker_names' not in st.session_state:
            st.session_state.speaker_names = {}
        if 'speaker_colors' not in st.session_state:
            st.session_state.speaker_colors = {}
        if 'show_speaker_manager' not in st.session_state:
            st.session_state.show_speaker_manager = False
    
    def render_speaker_management_ui(self, segments: List[Dict[str, Any]]):
        """Render speaker management interface"""
        # Extract unique speakers from segments
        speakers = self.extract_speakers_from_segments(segments)
        
        if not speakers:
            st.info("No speakers detected in the transcript")
            return
        
        # Speaker management header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("### 👥 Speaker Management")
        
        with col2:
            if st.button("✏️ Edit Names", help="Edit speaker names"):
                st.session_state.show_speaker_manager = True
                st.rerun()
        
        with col3:
            if st.button("🔄 Reset", help="Reset to default speaker names"):
                self.reset_speaker_names()
                st.rerun()
        
        # Display current speaker mapping
        self.render_speaker_overview(speakers)
        
        # Speaker editing modal
        if st.session_state.get('show_speaker_manager', False):
            self.render_speaker_editing_modal(speakers)
    
    def extract_speakers_from_segments(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Extract unique speaker identifiers from segments"""
        speakers = set()
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            speakers.add(speaker)
        return sorted(list(speakers))
    
    def render_speaker_overview(self, speakers: List[str]):
        """Render overview of current speakers"""
        st.markdown("#### Current Speakers")
        
        # Display speakers in a grid
        num_cols = min(3, len(speakers))
        if num_cols > 0:
            cols = st.columns(num_cols)
            
            for i, speaker in enumerate(speakers):
                with cols[i % num_cols]:
                    display_name = self.get_display_name(speaker)
                    color = self.get_speaker_color(speaker)
                    
                    # Speaker card
                    st.markdown(
                        f"""
                        <div style="
                            padding: 10px;
                            border-radius: 8px;
                            border: 2px solid {color};
                            background-color: {color}20;
                            text-align: center;
                            margin: 5px 0;
                        ">
                            <strong>{display_name}</strong><br>
                            <small style="color: #666;">({speaker})</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    def render_speaker_editing_modal(self, speakers: List[str]):
        """Render modal for editing speaker names and colors"""
        st.markdown("---")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### ✏️ Edit Speaker Names")
                
                # Edit each speaker
                for speaker in speakers:
                    st.markdown(f"**{speaker}:**")
                    
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        # Speaker name input
                        current_name = self.get_display_name(speaker)
                        new_name = st.text_input(
                            "Display Name",
                            value=current_name,
                            key=f"speaker_name_{speaker}",
                            label_visibility="collapsed",
                            placeholder="Enter custom name..."
                        )
                        
                        if new_name != current_name:
                            st.session_state.speaker_names[speaker] = new_name
                    
                    with col_b:
                        # Color picker
                        current_color = self.get_speaker_color(speaker)
                        new_color = st.color_picker(
                            "Color",
                            value=current_color,
                            key=f"speaker_color_{speaker}",
                            label_visibility="collapsed"
                        )
                        
                        if new_color != current_color:
                            st.session_state.speaker_colors[speaker] = new_color
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                
                # Action buttons
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                        st.success("Speaker names updated!")
                        st.session_state.show_speaker_manager = False
                        st.rerun()
                
                with col_cancel:
                    if st.button("❌ Cancel", use_container_width=True):
                        st.session_state.show_speaker_manager = False
                        st.rerun()
    
    def get_display_name(self, speaker: str) -> str:
        """Get display name for a speaker"""
        return st.session_state.speaker_names.get(speaker, speaker)
    
    def get_speaker_color(self, speaker: str) -> str:
        """Get color for a speaker"""
        default_colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", 
            "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"
        ]
        
        if speaker in st.session_state.speaker_colors:
            return st.session_state.speaker_colors[speaker]
        
        # Assign default color based on speaker hash
        color_index = hash(speaker) % len(default_colors)
        color = default_colors[color_index]
        st.session_state.speaker_colors[speaker] = color
        return color
    
    def reset_speaker_names(self):
        """Reset speaker names to defaults"""
        st.session_state.speaker_names = {}
        st.session_state.speaker_colors = {}
        st.success("Speaker names reset to defaults")
    
    def export_speaker_mapping(self) -> str:
        """Export speaker mapping as JSON"""
        mapping = {
            "speaker_names": st.session_state.speaker_names,
            "speaker_colors": st.session_state.speaker_colors
        }
        return json.dumps(mapping, indent=2)
    
    def import_speaker_mapping(self, mapping_json: str):
        """Import speaker mapping from JSON"""
        try:
            mapping = json.loads(mapping_json)
            st.session_state.speaker_names = mapping.get("speaker_names", {})
            st.session_state.speaker_colors = mapping.get("speaker_colors", {})
            st.success("Speaker mapping imported successfully!")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            st.error(f"Import failed: {str(e)}")


def render_speaker_management_sidebar():
    """Render speaker management in sidebar"""
    with st.sidebar:
        st.markdown("### 👥 Speaker Management")
        
        speaker_manager = SpeakerManager()
        
        # Quick speaker name inputs
        if 'speaker_names' in st.session_state and st.session_state.speaker_names:
            st.markdown("**Quick Rename:**")
            for original, display in st.session_state.speaker_names.items():
                new_name = st.text_input(
                    f"{original}:",
                    value=display,
                    key=f"sidebar_speaker_{original}"
                )
                if new_name != display:
                    st.session_state.speaker_names[original] = new_name
        
        # Export/Import speaker mapping
        if st.button("📥 Export Mapping"):
            mapping = speaker_manager.export_speaker_mapping()
            st.download_button(
                "💾 Download Mapping",
                data=mapping,
                file_name="speaker_mapping.json",
                mime="application/json"
            )
        
        uploaded_mapping = st.file_uploader(
            "📤 Import Mapping",
            type="json",
            help="Upload previously exported speaker mapping"
        )
        
        if uploaded_mapping:
            mapping_content = uploaded_mapping.read().decode('utf-8')
            speaker_manager.import_speaker_mapping(mapping_content)


def apply_speaker_names_to_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply custom speaker names to segments"""
    if 'speaker_names' not in st.session_state:
        return segments
    
    updated_segments = []
    for segment in segments:
        updated_segment = segment.copy()
        original_speaker = segment.get('speaker', 'Unknown')
        display_name = st.session_state.speaker_names.get(original_speaker, original_speaker)
        updated_segment['display_speaker'] = display_name
        updated_segments.append(updated_segment)
    
    return updated_segments


def render_speaker_statistics(segments: List[Dict[str, Any]]):
    """Render speaker statistics"""
    if not segments:
        return
    
    # Calculate speaking time for each speaker
    speaker_times = {}
    for segment in segments:
        speaker = segment.get('speaker', 'Unknown')
        duration = segment.get('end_time', 0) - segment.get('start_time', 0)
        speaker_times[speaker] = speaker_times.get(speaker, 0) + duration
    
    if not speaker_times:
        return
    
    st.markdown("### 📊 Speaker Statistics")
    
    # Display statistics
    total_time = sum(speaker_times.values())
    
    for speaker, time in sorted(speaker_times.items(), key=lambda x: x[1], reverse=True):
        display_name = st.session_state.speaker_names.get(speaker, speaker)
        percentage = (time / total_time) * 100 if total_time > 0 else 0
        color = st.session_state.speaker_colors.get(speaker, "#666666")
        
        # Progress bar
        st.markdown(f"**{display_name}** ({time:.1f}s - {percentage:.1f}%)")
        st.progress(percentage / 100)
        
        # Colored bar alternative
        st.markdown(
            f"""
            <div style="
                width: 100%;
                height: 20px;
                background-color: #f0f0f0;
                border-radius: 10px;
                margin: 5px 0;
            ">
                <div style="
                    width: {percentage}%;
                    height: 20px;
                    background-color: {color};
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                ">
                    {percentage:.0f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )