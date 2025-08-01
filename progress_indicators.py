#!/usr/bin/env python3
"""
Enhanced Progress Indicators for Audio/Video Transcription App
Provides detailed progress tracking and user feedback during processing
"""

import streamlit as st
import time
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProcessingStep:
    """Represents a single processing step"""
    name: str
    description: str
    weight: int = 1  # Relative weight for progress calculation
    estimated_duration: float = 0.0  # Estimated duration in seconds
    
class ProgressTracker:
    """Enhanced progress tracking with detailed feedback"""
    
    def __init__(self, steps: List[ProcessingStep]):
        self.steps = steps
        self.current_step_index = 0
        self.current_step_progress = 0
        self.start_time = time.time()
        self.step_start_time = time.time()
        self.total_weight = sum(step.weight for step in steps)
        
        # Streamlit components
        self.progress_bar = None
        self.status_text = None
        self.details_container = None
        self.time_info = None
        
    def initialize_ui(self):
        """Initialize Streamlit UI components"""
        # Main progress bar
        self.progress_bar = st.progress(0)
        
        # Status text
        self.status_text = st.empty()
        
        # Details container
        self.details_container = st.container()
        
        with self.details_container:
            col1, col2, col3 = st.columns(3)
            with col1:
                self.time_info = st.empty()
            with col2:
                self.step_info = st.empty()
            with col3:
                self.eta_info = st.empty()
    
    def update(self, step_progress: int = None, message: str = None):
        """Update progress for current step"""
        if step_progress is not None:
            self.current_step_progress = max(0, min(100, step_progress))
        
        # Calculate overall progress
        completed_weight = sum(self.steps[i].weight for i in range(self.current_step_index))
        current_step_weight = self.steps[self.current_step_index].weight
        current_contribution = (self.current_step_progress / 100) * current_step_weight
        
        overall_progress = (completed_weight + current_contribution) / self.total_weight
        overall_percentage = int(overall_progress * 100)
        
        # Update UI components
        if self.progress_bar:
            self.progress_bar.progress(overall_percentage)
        
        # Update status text
        current_step = self.steps[self.current_step_index]
        status_message = message or current_step.description
        
        if self.status_text:
            self.status_text.text(f"🔄 {status_message} ({overall_percentage}%)")
        
        # Update time information
        elapsed_time = time.time() - self.start_time
        step_elapsed = time.time() - self.step_start_time
        
        if self.time_info:
            self.time_info.metric(
                "Elapsed Time", 
                f"{elapsed_time:.1f}s",
                delta=f"Step: {step_elapsed:.1f}s"
            )
        
        if self.step_info:
            self.step_info.metric(
                "Current Step",
                f"{self.current_step_index + 1}/{len(self.steps)}",
                delta=current_step.name
            )
        
        # Calculate and display ETA
        if overall_progress > 0.1:  # Only show ETA after 10% completion
            estimated_total_time = elapsed_time / overall_progress
            eta_seconds = estimated_total_time - elapsed_time
            
            if self.eta_info and eta_seconds > 0:
                self.eta_info.metric(
                    "ETA",
                    f"{eta_seconds:.0f}s",
                    delta="remaining"
                )
    
    def next_step(self, message: str = None):
        """Move to the next processing step"""
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.current_step_progress = 0
            self.step_start_time = time.time()
            
            step = self.steps[self.current_step_index]
            logger.info(f"Starting step {self.current_step_index + 1}: {step.name}")
            
            self.update(0, message)
    
    def complete(self, success_message: str = "Processing completed successfully!"):
        """Mark processing as complete"""
        self.current_step_progress = 100
        self.update(100)
        
        if self.progress_bar:
            self.progress_bar.progress(100)
        
        if self.status_text:
            self.status_text.text(f"✅ {success_message}")
        
        total_time = time.time() - self.start_time
        logger.info(f"Processing completed in {total_time:.2f} seconds")
        
        # Show completion summary
        if self.details_container:
            with self.details_container:
                st.success(f"🎉 {success_message}")
                st.info(f"⏱️ Total processing time: {total_time:.1f} seconds")
    
    def cleanup(self):
        """Clean up UI components"""
        try:
            if self.progress_bar:
                self.progress_bar.empty()
            if self.status_text:
                self.status_text.empty()
            if self.time_info:
                self.time_info.empty()
            if self.step_info:
                self.step_info.empty()
            if self.eta_info:
                self.eta_info.empty()
        except Exception as e:
            logger.warning(f"Error cleaning up progress indicators: {e}")

@contextmanager
def progress_context(steps: List[ProcessingStep]):
    """Context manager for progress tracking"""
    tracker = ProgressTracker(steps)
    tracker.initialize_ui()
    
    try:
        yield tracker
    finally:
        # Clean up after a short delay to show completion
        time.sleep(1)
        tracker.cleanup()

def create_processing_steps() -> List[ProcessingStep]:
    """Create standard processing steps for audio transcription"""
    return [
        ProcessingStep(
            name="File Validation",
            description="Validating uploaded file...",
            weight=1,
            estimated_duration=2.0
        ),
        ProcessingStep(
            name="Media Processing",
            description="Processing media file...",
            weight=2,
            estimated_duration=5.0
        ),
        ProcessingStep(
            name="Audio Transcription",
            description="Transcribing audio to text...",
            weight=4,
            estimated_duration=15.0
        ),
        ProcessingStep(
            name="Entity Extraction",
            description="Extracting entities and analyzing content...",
            weight=2,
            estimated_duration=8.0
        ),
        ProcessingStep(
            name="Finalizing Results",
            description="Preparing results for display...",
            weight=1,
            estimated_duration=2.0
        )
    ]

def show_file_validation_feedback(file_info: Dict[str, Any], max_size_mb: int = 2048):
    """Show file validation feedback (only warnings/errors)"""
    
    # File size validation
    size_mb = file_info.get('size_mb', 0)
    duration = file_info.get('duration', 0)
    
    # Only show warnings or errors, not duplicate metrics
    if size_mb > max_size_mb:
        st.error(f"❌ File size ({size_mb:.1f} MB) exceeds the maximum limit of {max_size_mb} MB")
        st.info("💡 **Suggestions:**")
        st.write("• Compress the file using audio/video editing software")
        st.write("• Upload a shorter segment of the content")
        st.write("• Convert to a more efficient format (e.g., MP3)")
        return False
    
    if duration > 3600:  # 1 hour
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        duration_str = f"{minutes}m {seconds}s"
        st.warning(f"⚠️ Long file detected ({duration_str})")
        st.info("💡 **Note:** Processing may take several minutes for long files")
    
    return True

def show_processing_tips():
    """Show helpful tips during processing"""
    with st.expander("💡 Processing Tips", expanded=False):
        st.markdown("""
        **While your file is being processed:**
        
        🎵 **Audio Quality Tips:**
        - Clear audio with minimal background noise produces better transcripts
        - Mono audio files process faster than stereo
        - 16kHz sample rate is optimal for speech recognition
        
        🤖 **Analysis Modes:**
        - **Basic Mode:** Fast local processing, works offline
        - **Advanced Mode:** AI-powered analysis with summaries and insights
        
        ⏱️ **Processing Time:**
        - Small files (< 5 MB): 30-60 seconds
        - Medium files (5-25 MB): 1-3 minutes  
        - Large files (25-100 MB): 3-10 minutes
        - Very large files (100MB-2GB): 10-60+ minutes
        
        🔄 **What's Happening:**
        1. File validation and format conversion
        2. Audio extraction (for video files)
        3. Speech-to-text transcription
        4. Entity extraction and analysis
        5. Results formatting and display
        """)

def show_loading_animation(message: str = "Processing..."):
    """Show a simple loading animation"""
    placeholder = st.empty()
    
    animation_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    for i in range(10):  # Show for about 1 second
        char = animation_chars[i % len(animation_chars)]
        placeholder.text(f"{char} {message}")
        time.sleep(0.1)
    
    placeholder.empty()

def create_admin_processing_steps() -> List[ProcessingStep]:
    """Create processing steps for admin content generation"""
    return [
        ProcessingStep(
            name="Script Generation",
            description="Generating script with AI...",
            weight=3,
            estimated_duration=10.0
        ),
        ProcessingStep(
            name="Text-to-Speech",
            description="Converting text to speech...",
            weight=2,
            estimated_duration=8.0
        ),
        ProcessingStep(
            name="Audio Processing",
            description="Processing generated audio...",
            weight=1,
            estimated_duration=3.0
        )
    ]