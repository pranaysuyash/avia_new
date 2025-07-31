#!/usr/bin/env python3
"""
Session State Management for Audio/Video Transcription App
Handles Streamlit session state with better organization and persistence
"""

import streamlit as st
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProcessingState:
    """State for current processing operation"""
    is_processing: bool = False
    current_step: str = ""
    progress: int = 0
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None
    
    def start_processing(self, step: str = "Starting..."):
        """Start a new processing operation"""
        self.is_processing = True
        self.current_step = step
        self.progress = 0
        self.start_time = time.time()
        self.estimated_completion = None
    
    def update_progress(self, progress: int, step: str = None):
        """Update processing progress"""
        self.progress = max(0, min(100, progress))
        if step:
            self.current_step = step
        
        # Estimate completion time based on current progress
        if self.start_time and self.progress > 0:
            elapsed = time.time() - self.start_time
            total_estimated = elapsed * (100 / self.progress)
            self.estimated_completion = self.start_time + total_estimated
    
    def complete_processing(self):
        """Mark processing as complete"""
        self.is_processing = False
        self.current_step = "Complete"
        self.progress = 100
        self.estimated_completion = None

@dataclass
class TranscriptionResults:
    """Results from transcription and analysis"""
    transcript: str = ""
    entities: Dict[str, Any] = None
    summary: str = ""
    confidence: float = 0.0
    processing_time: float = 0.0
    model_used: str = ""
    language: str = "en"
    word_count: int = 0
    entity_confidence: Dict[str, Any] = None
    sentiment: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.entity_confidence is None:
            self.entity_confidence = {}
        if self.sentiment is None:
            self.sentiment = {}

@dataclass
class AdvancedTranscriptionState:
    """State for advanced transcription features"""
    advanced_result: Any = None  # AdvancedTranscriptionResult
    detected_languages: list = None
    selected_language: str = None
    processing_options: Dict[str, Any] = None
    speaker_statistics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.detected_languages is None:
            self.detected_languages = []
        if self.processing_options is None:
            self.processing_options = {}
        if self.speaker_statistics is None:
            self.speaker_statistics = {}

@dataclass
class FileInfo:
    """Information about uploaded/processed files"""
    name: str = ""
    size_bytes: int = 0
    size_mb: float = 0.0
    duration: float = 0.0
    format: str = ""
    upload_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.upload_time is None:
            self.upload_time = datetime.now()

@dataclass
class UserPreferences:
    """User preferences and settings"""
    preferred_analysis_mode: str = "Basic (spaCy)"
    show_line_numbers: bool = False
    show_confidence_scores: bool = True
    auto_clear_results: bool = False
    theme: str = "light"
    responsive_design: bool = True
    animations_enabled: bool = True
    drag_drop_enabled: bool = True
    
class SessionManager:
    """Manages Streamlit session state with enhanced functionality"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize all session state variables with proper defaults"""
        
        # Processing state
        if 'processing_state' not in st.session_state:
            st.session_state.processing_state = ProcessingState()
        
        # Results
        if 'transcription_results' not in st.session_state:
            st.session_state.transcription_results = TranscriptionResults()
        
        # Advanced transcription state
        if 'advanced_transcription_state' not in st.session_state:
            st.session_state.advanced_transcription_state = AdvancedTranscriptionState()
        
        # File information
        if 'current_file_info' not in st.session_state:
            st.session_state.current_file_info = FileInfo()
        
        # User preferences
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = UserPreferences()
        
        # Error handling
        if 'error_message' not in st.session_state:
            st.session_state.error_message = ""
        if 'error_object' not in st.session_state:
            st.session_state.error_object = None
        
        # Admin panel state - preserve across mode switches
        if 'admin_state' not in st.session_state:
            st.session_state.admin_state = {
                'generated_script': "",
                'generated_audio_path': "",
                'admin_error': "",
                'last_prompt': "",
                'last_format': "monologue",
                'last_style': "conversational",
                'last_voice_preset': "professional"
            }
        
        # Processing history (keep last 5 operations)
        if 'processing_history' not in st.session_state:
            st.session_state.processing_history = []
        
        # Batch processing state
        if 'batch_jobs' not in st.session_state:
            st.session_state.batch_jobs = {}
        
        # File management state
        if 'file_management' not in st.session_state:
            st.session_state.file_management = {
                'uploaded_files': [],
                'processed_files': [],
                'temp_files': [],
                'export_history': []
            }
        
        # UI state
        if 'ui_state' not in st.session_state:
            st.session_state.ui_state = {
                'sidebar_expanded': True,
                'show_advanced_options': False,
                'current_tab': 0
            }
        
        logger.debug("Session state initialized")
    
    def start_processing(self, step: str = "Starting processing..."):
        """Start a new processing operation"""
        st.session_state.processing_state.start_processing(step)
        logger.info(f"Processing started: {step}")
    
    def update_progress(self, progress: int, step: str = None):
        """Update processing progress"""
        st.session_state.processing_state.update_progress(progress, step)
        if step:
            logger.debug(f"Progress update: {progress}% - {step}")
    
    def complete_processing(self, results: TranscriptionResults = None):
        """Complete processing and store results"""
        st.session_state.processing_state.complete_processing()
        
        if results:
            st.session_state.transcription_results = results
            
            # Add to processing history
            history_entry = {
                'timestamp': datetime.now(),
                'file_name': st.session_state.current_file_info.name,
                'word_count': results.word_count,
                'processing_time': results.processing_time,
                'model_used': results.model_used
            }
            
            st.session_state.processing_history.insert(0, history_entry)
            # Keep only last 5 entries
            st.session_state.processing_history = st.session_state.processing_history[:5]
        
        logger.info("Processing completed successfully")
    
    def set_error(self, error_message: str, error_object: Any = None):
        """Set error state"""
        st.session_state.error_message = error_message
        st.session_state.error_object = error_object
        st.session_state.processing_state.is_processing = False
        logger.error(f"Error set: {error_message}")
    
    def clear_error(self):
        """Clear error state"""
        st.session_state.error_message = ""
        st.session_state.error_object = None
    
    def clear_results(self):
        """Clear all processing results"""
        st.session_state.transcription_results = TranscriptionResults()
        st.session_state.advanced_transcription_state = AdvancedTranscriptionState()
        st.session_state.processing_state = ProcessingState()
        st.session_state.current_file_info = FileInfo()
        self.clear_error()
        logger.info("Results cleared")
    
    def update_file_info(self, name: str, size_bytes: int, duration: float = 0.0, format: str = ""):
        """Update current file information"""
        st.session_state.current_file_info = FileInfo(
            name=name,
            size_bytes=size_bytes,
            size_mb=size_bytes / (1024 * 1024),
            duration=duration,
            format=format
        )
        logger.debug(f"File info updated: {name} ({size_bytes} bytes)")
    
    def get_processing_state(self) -> ProcessingState:
        """Get current processing state"""
        return st.session_state.processing_state
    
    def get_results(self) -> TranscriptionResults:
        """Get current transcription results"""
        return st.session_state.transcription_results
    
    def get_file_info(self) -> FileInfo:
        """Get current file information"""
        return st.session_state.current_file_info
    
    def get_preferences(self) -> UserPreferences:
        """Get user preferences"""
        return st.session_state.user_preferences
    
    def update_preference(self, key: str, value: Any):
        """Update a user preference"""
        if hasattr(st.session_state.user_preferences, key):
            setattr(st.session_state.user_preferences, key, value)
            logger.debug(f"Preference updated: {key} = {value}")
    
    def get_processing_history(self) -> list:
        """Get processing history"""
        return st.session_state.processing_history
    
    def is_processing(self) -> bool:
        """Check if currently processing"""
        return st.session_state.processing_state.is_processing
    
    def has_results(self) -> bool:
        """Check if there are processing results"""
        return bool(st.session_state.transcription_results.transcript)
    
    def has_error(self) -> bool:
        """Check if there's an error"""
        return bool(st.session_state.error_message)
    
    def clear_admin_state(self):
        """Clear only admin panel state while preserving main results"""
        st.session_state.admin_state = {
            'generated_script': "",
            'generated_audio_path': "",
            'admin_error': "",
            'last_prompt': "",
            'last_format': "monologue",
            'last_style': "conversational",
            'last_voice_preset': "professional"
        }
        logger.info("Admin state cleared")
    
    def has_admin_content(self) -> bool:
        """Check if there's any admin-generated content"""
        admin_state = st.session_state.admin_state
        return bool(admin_state.get('generated_script') or admin_state.get('generated_audio_path'))
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session state"""
        return {
            'is_processing': self.is_processing(),
            'has_results': self.has_results(),
            'has_error': self.has_error(),
            'current_file': st.session_state.current_file_info.name,
            'processing_history_count': len(st.session_state.processing_history),
            'preferences': asdict(st.session_state.user_preferences),
            'has_admin_content': self.has_admin_content()
        }
    
    def get_theme(self) -> str:
        """Get current theme"""
        return st.session_state.user_preferences.theme
    
    def set_theme(self, theme: str):
        """Set theme and persist preference"""
        if theme in ['light', 'dark']:
            st.session_state.user_preferences.theme = theme
            # Also store in session state for immediate access
            st.session_state.ui_theme = theme
            logger.info(f"Theme changed to: {theme}")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current_theme = self.get_theme()
        new_theme = "dark" if current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme
    
    def is_mobile_device(self) -> bool:
        """Check if user is on mobile device (basic detection)"""
        # This is a simple check - in a real app you might use JavaScript
        return st.session_state.get('is_mobile', False)
    
    def set_mobile_device(self, is_mobile: bool):
        """Set mobile device flag"""
        st.session_state.is_mobile = is_mobile
    
    def store_advanced_results(self, advanced_result: Any, detected_languages: list = None):
        """Store advanced transcription results"""
        st.session_state.advanced_transcription_state.advanced_result = advanced_result
        if detected_languages:
            st.session_state.advanced_transcription_state.detected_languages = detected_languages
        
        # Also update basic results for compatibility
        if hasattr(advanced_result, 'text'):
            basic_results = TranscriptionResults(
                transcript=advanced_result.text,
                confidence=advanced_result.confidence,
                processing_time=advanced_result.processing_time,
                model_used=advanced_result.model_used,
                language=advanced_result.language,
                word_count=len(advanced_result.text.split()) if advanced_result.text else 0
            )
            st.session_state.transcription_results = basic_results
        
        logger.info("Advanced transcription results stored")
    
    def get_advanced_results(self) -> Any:
        """Get advanced transcription results"""
        return st.session_state.advanced_transcription_state.advanced_result
    
    def has_advanced_results(self) -> bool:
        """Check if there are advanced transcription results"""
        return st.session_state.advanced_transcription_state.advanced_result is not None
    
    def get_detected_languages(self) -> list:
        """Get detected languages"""
        return st.session_state.advanced_transcription_state.detected_languages
    
    def set_selected_language(self, language: str):
        """Set selected language for transcription"""
        st.session_state.advanced_transcription_state.selected_language = language
    
    def get_selected_language(self) -> str:
        """Get selected language"""
        return st.session_state.advanced_transcription_state.selected_language
    
    def update_processing_options(self, options: Dict[str, Any]):
        """Update processing options"""
        st.session_state.advanced_transcription_state.processing_options.update(options)
    
    def get_processing_options(self) -> Dict[str, Any]:
        """Get processing options"""
        return st.session_state.advanced_transcription_state.processing_options
    
    def add_batch_job(self, job_id: str, job_config: Dict[str, Any]):
        """Add a batch job to session state"""
        st.session_state.batch_jobs[job_id] = job_config
        logger.info(f"Added batch job {job_id} to session state")
    
    def get_batch_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job configuration"""
        return st.session_state.batch_jobs.get(job_id)
    
    def remove_batch_job(self, job_id: str):
        """Remove batch job from session state"""
        if job_id in st.session_state.batch_jobs:
            del st.session_state.batch_jobs[job_id]
            logger.info(f"Removed batch job {job_id} from session state")
    
    def get_all_batch_jobs(self) -> Dict[str, Any]:
        """Get all batch jobs"""
        return st.session_state.batch_jobs
    
    def add_file_to_management(self, file_type: str, file_info: Dict[str, Any]):
        """Add file to file management system"""
        if file_type in st.session_state.file_management:
            st.session_state.file_management[file_type].append({
                **file_info,
                'timestamp': datetime.now().isoformat()
            })
            # Keep only last 50 entries per type
            st.session_state.file_management[file_type] = st.session_state.file_management[file_type][-50:]
    
    def get_file_management_history(self, file_type: str = None) -> Dict[str, Any]:
        """Get file management history"""
        if file_type:
            return st.session_state.file_management.get(file_type, [])
        return st.session_state.file_management
    
    def clear_batch_state(self):
        """Clear all batch processing state"""
        st.session_state.batch_jobs = {}
        st.session_state.file_management = {
            'uploaded_files': [],
            'processed_files': [],
            'temp_files': [],
            'export_history': []
        }
        logger.info("Batch processing state cleared")

# Global session manager instance
session_manager = SessionManager()