"""
Enhanced Progress Indicators with Real-time Feedback
Provides improved user experience during long operations
"""

import streamlit as st
import time
import logging
import threading
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class ProgressStep:
    """Enhanced processing step with more detail"""
    name: str
    description: str
    weight: float = 1.0
    estimated_duration: float = 10.0
    icon: str = "⏳"
    tips: List[str] = None
    
    def __post_init__(self):
        if self.tips is None:
            self.tips = []


class EnhancedProgressTracker:
    """Enhanced progress tracker with better UX"""
    
    def __init__(self, steps: List[ProgressStep], show_tips: bool = True):
        self.steps = steps
        self.current_step = 0
        self.current_progress = 0.0
        self.start_time = time.time()
        self.show_tips = show_tips
        self.total_weight = sum(step.weight for step in steps)
        
        # UI components
        self.main_progress = None
        self.step_progress = None
        self.status_container = None
        self.tips_container = None
        self.eta_container = None
        
        # State tracking
        self.step_start_times = {}
        self.completed_steps = set()
        self.is_cancelled = False
    
    def initialize_ui(self, title: str = "Processing..."):
        """Initialize the progress UI"""
        st.markdown(f"### {title}")
        
        # Main progress bar
        col1, col2 = st.columns([4, 1])
        
        with col1:
            self.main_progress = st.progress(0.0, "Starting...")
        
        with col2:
            self.eta_container = st.empty()
        
        # Current step progress
        self.step_progress = st.progress(0.0, "Initializing...")
        
        # Status information
        self.status_container = st.container()
        
        # Tips and helpful information
        if self.show_tips:
            self.tips_container = st.container()
            self._show_initial_tips()
        
        # Cancellation button
        col_cancel, col_space = st.columns([1, 3])
        with col_cancel:
            if st.button("❌ Cancel", key="cancel_processing"):
                self.is_cancelled = True
                st.warning("Cancelling operation...")
    
    def update_step(self, step_index: int, progress: float = 0.0, message: str = ""):
        """Update progress for a specific step"""
        if self.is_cancelled:
            return False
        
        self.current_step = step_index
        self.current_progress = progress
        
        # Calculate overall progress
        completed_weight = sum(self.steps[i].weight for i in range(step_index))
        current_step_weight = self.steps[step_index].weight * (progress / 100.0)
        total_progress = (completed_weight + current_step_weight) / self.total_weight
        
        # Update main progress bar
        if self.main_progress:
            step_name = self.steps[step_index].name
            overall_message = f"{step_name} ({step_index + 1}/{len(self.steps)})"
            self.main_progress.progress(total_progress, overall_message)
        
        # Update step progress bar
        if self.step_progress:
            step_message = message or self.steps[step_index].description
            self.step_progress.progress(progress / 100.0, f"{self.steps[step_index].icon} {step_message}")
        
        # Update ETA
        self._update_eta(total_progress)
        
        # Update status information
        self._update_status_info(step_index, progress, message)
        
        # Show tips for current step
        if self.show_tips:
            self._show_step_tips(step_index)
        
        return True
    
    def complete_step(self, step_index: int, message: str = "Completed"):
        """Mark a step as completed"""
        if step_index not in self.completed_steps:
            self.completed_steps.add(step_index)
            
        self.update_step(step_index, 100.0, f"✅ {message}")
        
        # Brief pause to show completion
        time.sleep(0.5)
    
    def finish(self, success: bool = True, message: str = ""):
        """Finish the progress tracking"""
        if success:
            if self.main_progress:
                self.main_progress.progress(1.0, "✅ Complete!")
            if self.step_progress:
                self.step_progress.progress(1.0, "✅ All steps completed")
            
            total_time = time.time() - self.start_time
            if self.eta_container:
                self.eta_container.success(f"✅ Completed in {total_time:.1f}s")
            
            if message:
                st.success(message)
        else:
            if self.main_progress:
                self.main_progress.progress(0.0, "❌ Failed")
            if self.step_progress:
                self.step_progress.progress(0.0, "❌ Operation failed")
            
            if self.eta_container:
                self.eta_container.error("❌ Failed")
            
            if message:
                st.error(message)
    
    def _update_eta(self, progress: float):
        """Update estimated time remaining"""
        if not self.eta_container or progress <= 0:
            return
        
        elapsed = time.time() - self.start_time
        if progress > 0.1:  # Only calculate ETA after 10% progress
            estimated_total = elapsed / progress
            eta = estimated_total - elapsed
            
            if eta > 60:
                eta_text = f"~{int(eta // 60)}m {int(eta % 60)}s"
            else:
                eta_text = f"~{int(eta)}s"
            
            self.eta_container.info(f"ETA: {eta_text}")
    
    def _update_status_info(self, step_index: int, progress: float, message: str):
        """Update detailed status information"""
        if not self.status_container:
            return
        
        with self.status_container:
            step = self.steps[step_index]
            
            # Create status display
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**Current:** {step.name}")
                if message:
                    st.caption(message)
            
            with col2:
                st.metric("Step Progress", f"{progress:.1f}%")
            
            with col3:
                completed = len(self.completed_steps)
                st.metric("Completed Steps", f"{completed}/{len(self.steps)}")
    
    def _show_initial_tips(self):
        """Show general tips at the start"""
        if not self.tips_container:
            return
        
        with self.tips_container:
            with st.expander("💡 Processing Tips", expanded=True):
                st.info(
                    "**While processing:**\n"
                    "• Keep this tab open for best results\n"
                    "• Larger files take longer to process\n" 
                    "• You can cancel anytime with the Cancel button\n"
                    "• Check the tips for each step below"
                )
    
    def _show_step_tips(self, step_index: int):
        """Show tips for the current step"""
        if not self.tips_container or not self.show_tips:
            return
        
        step = self.steps[step_index]
        if not step.tips:
            return
        
        with self.tips_container:
            with st.expander(f"💡 {step.name} Tips", expanded=False):
                for tip in step.tips:
                    st.markdown(f"• {tip}")


def create_transcription_progress_steps() -> List[ProgressStep]:
    """Create progress steps for transcription process"""
    return [
        ProgressStep(
            name="File Upload & Validation",
            description="Validating and preparing your audio file...",
            weight=1.0,
            estimated_duration=5.0,
            icon="📁",
            tips=[
                "Supported formats: MP3, WAV, MP4, M4A",
                "Larger files take longer to validate",
                "Check file format if this step takes too long"
            ]
        ),
        ProgressStep(
            name="Audio Processing",
            description="Converting and optimizing audio for transcription...",
            weight=2.0,
            estimated_duration=15.0,
            icon="🎵",
            tips=[
                "Audio is being optimized for best transcription quality",
                "This step improves accuracy significantly",
                "Processing time depends on audio length"
            ]
        ),
        ProgressStep(
            name="Speech Recognition",
            description="Converting speech to text using AI...",
            weight=5.0,
            estimated_duration=30.0,
            icon="🎤",
            tips=[
                "Using advanced AI models for high accuracy",
                "Longer audio files will take more time",
                "Quality depends on audio clarity and language",
                "Multiple speakers may extend processing time"
            ]
        ),
        ProgressStep(
            name="Text Processing",
            description="Cleaning and formatting transcript...",
            weight=1.0,
            estimated_duration=5.0,
            icon="📝",
            tips=[
                "Adding punctuation and proper formatting",
                "Identifying sentence boundaries",
                "Preparing text for entity extraction"
            ]
        ),
        ProgressStep(
            name="Entity Extraction",
            description="Identifying people, places, and organizations...",
            weight=2.0,
            estimated_duration=10.0,
            icon="🏷️",
            tips=[
                "Finding names, locations, and entities in your text",
                "Results depend on context and domain",
                "Advanced mode provides more detailed analysis"
            ]
        ),
        ProgressStep(
            name="Final Processing",
            description="Generating summary and preparing results...",
            weight=1.5,
            estimated_duration=8.0,
            icon="✨",
            tips=[
                "Creating AI-powered summary",
                "Organizing all results for display",
                "Almost done!"
            ]
        )
    ]


def create_export_progress_steps() -> List[ProgressStep]:
    """Create progress steps for export process"""
    return [
        ProgressStep(
            name="Preparing Data",
            description="Collecting transcript and analysis data...",
            weight=1.0,
            estimated_duration=3.0,
            icon="📊",
            tips=[
                "Gathering all transcript and entity data",
                "Preparing data for export format"
            ]
        ),
        ProgressStep(
            name="Format Conversion",
            description="Converting to requested format...",
            weight=3.0,
            estimated_duration=10.0,
            icon="🔄",
            tips=[
                "Converting data to your chosen format",
                "Complex formats like PDF take longer",
                "Including visualizations if requested"
            ]
        ),
        ProgressStep(
            name="Finalizing Export",
            description="Packaging your export file...",
            weight=1.0,
            estimated_duration=3.0,
            icon="📦",
            tips=[
                "Creating final export package",
                "Adding metadata and formatting",
                "Preparing download"
            ]
        )
    ]


@contextmanager
def progress_context(steps: List[ProgressStep], title: str = "Processing...", show_tips: bool = True):
    """Context manager for easy progress tracking"""
    tracker = EnhancedProgressTracker(steps, show_tips)
    tracker.initialize_ui(title)
    
    try:
        yield tracker
        tracker.finish(success=True, message="Operation completed successfully!")
    except Exception as e:
        tracker.finish(success=False, message=f"Operation failed: {str(e)}")
        raise
    except KeyboardInterrupt:
        tracker.finish(success=False, message="Operation cancelled by user")
        raise


def show_processing_animation(message: str = "Processing...", duration: float = 2.0):
    """Show a simple processing animation"""
    animation_placeholder = st.empty()
    
    frames = ["⏳", "⌛", "⏳", "⌛"]
    frame_duration = duration / (len(frames) * 3)  # Repeat animation 3 times
    
    for _ in range(3):  # Repeat 3 times
        for frame in frames:
            animation_placeholder.markdown(f"{frame} {message}")
            time.sleep(frame_duration)
    
    animation_placeholder.empty()


def show_completion_celebration():
    """Show a celebration animation when processing completes"""
    celebration = st.empty()
    
    # Show celebration
    celebration.markdown("# 🎉 Processing Complete! 🎉")
    time.sleep(1)
    
    celebration.markdown("### ✅ Your transcript is ready!")
    time.sleep(1)
    
    celebration.empty()


# Example usage functions
def demo_transcription_progress():
    """Demo function to show transcription progress"""
    steps = create_transcription_progress_steps()
    
    with progress_context(steps, "Transcribing Your Audio", show_tips=True) as tracker:
        for i, step in enumerate(steps):
            # Simulate step processing
            for progress in range(0, 101, 10):
                if not tracker.update_step(i, progress, f"Processing... {progress}%"):
                    return  # User cancelled
                time.sleep(0.2)  # Simulate work
            
            tracker.complete_step(i)
        
        # Show celebration
        show_completion_celebration()


def demo_export_progress():
    """Demo function to show export progress"""
    steps = create_export_progress_steps()
    
    with progress_context(steps, "Exporting Your Data", show_tips=False) as tracker:
        for i, step in enumerate(steps):
            # Simulate processing
            for progress in range(0, 101, 25):
                if not tracker.update_step(i, progress):
                    return
                time.sleep(0.3)
            
            tracker.complete_step(i)


if __name__ == "__main__":
    st.title("Enhanced Progress Demo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Demo Transcription Progress"):
            demo_transcription_progress()
    
    with col2:
        if st.button("Demo Export Progress"):
            demo_export_progress()