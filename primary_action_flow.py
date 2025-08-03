#!/usr/bin/env python3
"""
Primary Action Flow Module
Creates a clear, focused user journey for the main transcription task
"""

import streamlit as st
from typing import Optional, Dict, Any, Tuple
import tempfile
import os
from datetime import datetime


class PrimaryActionFlow:
    """Manages the primary user action flow with clear steps"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize action flow session state"""
        if 'action_step' not in st.session_state:
            st.session_state.action_step = 'upload'  # upload, configure, process, results
        if 'uploaded_file' not in st.session_state:
            st.session_state.uploaded_file = None
        if 'processing_config' not in st.session_state:
            st.session_state.processing_config = {}
        if 'processing_result' not in st.session_state:
            st.session_state.processing_result = None
    
    def render(self) -> None:
        """Render the primary action flow interface"""
        # Header with progress indicator
        self._render_progress_header()
        
        # Main content area
        if st.session_state.action_step == 'upload':
            self._render_upload_step()
        elif st.session_state.action_step == 'configure':
            self._render_configure_step()
        elif st.session_state.action_step == 'process':
            self._render_process_step()
        elif st.session_state.action_step == 'results':
            self._render_results_step()
    
    def _render_progress_header(self):
        """Render progress indicator showing current step"""
        steps = ['Upload', 'Configure', 'Process', 'Results']
        current_idx = ['upload', 'configure', 'process', 'results'].index(st.session_state.action_step)
        
        # Create progress bar
        progress_cols = st.columns(4)
        for idx, (col, step) in enumerate(zip(progress_cols, steps)):
            with col:
                if idx < current_idx:
                    st.markdown(f"✅ **{step}**")
                elif idx == current_idx:
                    st.markdown(f"📍 **{step}**")
                else:
                    st.markdown(f"⭕ {step}")
        
        st.markdown("---")
    
    def _render_upload_step(self):
        """Render file upload step"""
        st.header("📤 Upload Your File")
        st.markdown("Upload an audio or video file to transcribe")
        
        # Center the upload area
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # File uploader with drag & drop
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['mp3', 'wav', 'm4a', 'mp4', 'avi', 'mov'],
                help="Drag and drop or click to browse",
                key="primary_file_upload"
            )
            
            if uploaded_file:
                # Show file info
                file_info = self._get_file_info(uploaded_file)
                st.success(f"✅ File uploaded: {file_info['name']}")
                
                # Display file details
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Size", file_info['size'])
                with col_b:
                    st.metric("Type", file_info['type'])
                
                # Action buttons
                st.markdown("---")
                col_1, col_2 = st.columns(2)
                with col_1:
                    if st.button("⚡ Quick Process", use_container_width=True, type="primary"):
                        # Skip configuration, use defaults
                        st.session_state.uploaded_file = uploaded_file
                        st.session_state.processing_config = self._get_default_config()
                        st.session_state.action_step = 'process'
                        st.rerun()
                
                with col_2:
                    if st.button("⚙️ Configure", use_container_width=True):
                        st.session_state.uploaded_file = uploaded_file
                        st.session_state.action_step = 'configure'
                        st.rerun()
        
        # Show recent files if available
        self._render_recent_files()
    
    def _render_configure_step(self):
        """Render configuration step"""
        st.header("⚙️ Configure Processing")
        
        if not st.session_state.uploaded_file:
            st.error("No file uploaded")
            if st.button("← Back to Upload"):
                st.session_state.action_step = 'upload'
                st.rerun()
            return
        
        # Show file info at top
        file_info = self._get_file_info(st.session_state.uploaded_file)
        st.info(f"📄 Configuring: {file_info['name']}")
        
        # Configuration options in tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Basic", "🔧 Advanced", "🎨 Output"])
        
        with tab1:
            # Basic configuration
            processing_mode = st.radio(
                "Processing Mode",
                options=[
                    ("🚀 Fast - Quick results with basic analysis", "basic"),
                    ("🧠 Smart - AI-powered deep analysis", "advanced"),
                    ("👥 Multi-Speaker - Identify different speakers", "diarization")
                ],
                format_func=lambda x: x[0],
                key="config_mode"
            )
            st.session_state.processing_config['mode'] = processing_mode[1]
            
            # Language selection
            language = st.selectbox(
                "Language",
                ["Auto-detect", "English", "Spanish", "French", "German", "Italian"],
                key="config_language"
            )
            st.session_state.processing_config['language'] = language
        
        with tab2:
            # Advanced configuration
            st.markdown("### Audio Processing")
            
            col1, col2 = st.columns(2)
            with col1:
                enhance_audio = st.checkbox(
                    "🔊 Enhance Audio Quality",
                    value=True,
                    help="Apply noise reduction and enhancement"
                )
                st.session_state.processing_config['enhance_audio'] = enhance_audio
            
            with col2:
                confidence_threshold = st.slider(
                    "Confidence Threshold",
                    0.0, 1.0, 0.7,
                    help="Minimum confidence for entity extraction"
                )
                st.session_state.processing_config['confidence_threshold'] = confidence_threshold
            
            # Chunk settings
            st.markdown("### Processing Settings")
            chunk_duration = st.slider(
                "Chunk Duration (seconds)",
                10, 60, 30,
                help="Split long files into chunks"
            )
            st.session_state.processing_config['chunk_duration'] = chunk_duration
        
        with tab3:
            # Output configuration
            st.markdown("### Output Options")
            
            col1, col2 = st.columns(2)
            with col1:
                include_timestamps = st.checkbox(
                    "⏱️ Include Timestamps",
                    value=True
                )
                st.session_state.processing_config['include_timestamps'] = include_timestamps
                
                generate_summary = st.checkbox(
                    "📝 Generate Summary",
                    value=True
                )
                st.session_state.processing_config['generate_summary'] = generate_summary
            
            with col2:
                export_format = st.multiselect(
                    "Export Formats",
                    ["TXT", "JSON", "SRT", "VTT", "PDF"],
                    default=["TXT"]
                )
                st.session_state.processing_config['export_formats'] = export_format
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.action_step = 'upload'
                st.rerun()
        
        with col2:
            if st.button("🔄 Reset to Defaults", use_container_width=True):
                st.session_state.processing_config = self._get_default_config()
                st.rerun()
        
        with col3:
            if st.button("▶️ Start Processing", use_container_width=True, type="primary"):
                st.session_state.action_step = 'process'
                st.rerun()
    
    def _render_process_step(self):
        """Render processing step"""
        st.header("⚡ Processing Your File")
        
        if not st.session_state.uploaded_file:
            st.error("No file to process")
            if st.button("← Back to Upload"):
                st.session_state.action_step = 'upload'
                st.rerun()
            return
        
        # Show what's being processed
        file_info = self._get_file_info(st.session_state.uploaded_file)
        config = st.session_state.processing_config
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📄 File: {file_info['name']}")
        with col2:
            mode_display = {
                'basic': '🚀 Fast Mode',
                'advanced': '🧠 Smart Mode',
                'diarization': '👥 Multi-Speaker Mode'
            }
            st.info(f"Mode: {mode_display.get(config.get('mode', 'basic'))}")
        
        # Processing animation and status
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            
            # Simulate processing steps
            steps = [
                ("📤 Uploading file...", 0.1),
                ("🎵 Analyzing audio...", 0.3),
                ("🗣️ Transcribing speech...", 0.6),
                ("🔍 Extracting entities...", 0.8),
                ("✨ Finalizing results...", 1.0)
            ]
            
            for step_text, progress in steps:
                with status_container:
                    st.markdown(f"**Status:** {step_text}")
                progress_bar.progress(progress)
                
                # Here you would call actual processing functions
                # For now, we'll simulate with sleep
                import time
                time.sleep(0.5)
        
        # After processing completes
        st.success("✅ Processing complete!")
        
        # Auto-advance to results
        st.session_state.processing_result = {
            'transcription': 'Sample transcription text...',
            'entities': {'PERSON': ['John Doe'], 'ORG': ['Acme Corp']},
            'summary': 'This is a sample summary.',
            'confidence': 0.95
        }
        st.session_state.action_step = 'results'
        
        # Add small delay before rerun
        time.sleep(1)
        st.rerun()
    
    def _render_results_step(self):
        """Render results step"""
        st.header("📊 Results")
        
        if not st.session_state.processing_result:
            st.error("No results available")
            if st.button("← Start Over"):
                self.reset_flow()
                st.rerun()
            return
        
        result = st.session_state.processing_result
        
        # Results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Transcript", "🏷️ Entities", "📊 Insights", "💾 Export"])
        
        with tab1:
            # Transcript display
            st.markdown("### Transcription")
            st.text_area(
                "Full Transcript",
                result['transcription'],
                height=300,
                key="result_transcript"
            )
            
            # Confidence score
            st.metric("Confidence", f"{result['confidence']:.1%}")
        
        with tab2:
            # Entity display
            st.markdown("### Extracted Entities")
            
            if result['entities']:
                for entity_type, entities in result['entities'].items():
                    st.markdown(f"**{entity_type}**")
                    for entity in entities:
                        st.markdown(f"• {entity}")
            else:
                st.info("No entities found")
        
        with tab3:
            # Insights
            st.markdown("### Content Insights")
            
            if result.get('summary'):
                st.markdown("**Summary**")
                st.write(result['summary'])
            
            # Additional insights could go here
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Word Count", "150")
            with col2:
                st.metric("Duration", "2:30")
            with col3:
                st.metric("Entities Found", "5")
        
        with tab4:
            # Export options
            st.markdown("### Export Results")
            
            export_format = st.selectbox(
                "Choose Format",
                ["TXT", "JSON", "PDF", "SRT", "VTT"],
                key="export_format_select"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Download", use_container_width=True, type="primary"):
                    # Generate download
                    st.success("Download started!")
            
            with col2:
                if st.button("📧 Email Results", use_container_width=True):
                    st.info("Email feature coming soon!")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Process Another File", use_container_width=True):
                self.reset_flow()
                st.rerun()
        
        with col2:
            if st.button("📋 Save to Library", use_container_width=True):
                st.success("Saved to library!")
        
        with col3:
            if st.button("🔍 Advanced Analysis", use_container_width=True):
                st.info("Opening advanced analysis...")
    
    def _get_file_info(self, uploaded_file) -> Dict[str, str]:
        """Get formatted file information"""
        size_mb = uploaded_file.size / (1024 * 1024)
        return {
            'name': uploaded_file.name,
            'size': f"{size_mb:.1f} MB",
            'type': uploaded_file.type or 'Unknown'
        }
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default processing configuration"""
        return {
            'mode': 'basic',
            'language': 'Auto-detect',
            'enhance_audio': True,
            'confidence_threshold': 0.7,
            'chunk_duration': 30,
            'include_timestamps': True,
            'generate_summary': True,
            'export_formats': ['TXT']
        }
    
    def _render_recent_files(self):
        """Render recent files section"""
        if st.session_state.get('recent_files'):
            st.markdown("---")
            st.subheader("📁 Recent Files")
            
            for file in st.session_state.recent_files[-3:]:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(file['name'])
                with col2:
                    st.text(file['date'])
                with col3:
                    if st.button("Load", key=f"load_{file['id']}"):
                        # Load file logic
                        st.info(f"Loading {file['name']}...")
    
    def reset_flow(self):
        """Reset the action flow to start"""
        st.session_state.action_step = 'upload'
        st.session_state.uploaded_file = None
        st.session_state.processing_config = {}
        st.session_state.processing_result = None


# Convenience function to render the primary flow
def render_primary_action_flow():
    """Render the primary action flow interface"""
    flow = PrimaryActionFlow()
    flow.render()