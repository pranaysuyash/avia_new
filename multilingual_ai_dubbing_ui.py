"""
Streamlit UI for Multilingual AI Dubbing System
Provides interface for voice cloning, lip-sync generation, and quality control
"""

import streamlit as st
import asyncio
import os
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import time

# Import the main dubbing system
from multilingual_ai_dubbing_system import (
    MultilingualAIDubbingSystem,
    VoiceProfile,
    SpeakerMapping,
    LipSyncConfig,
    DubbingJob,
    create_default_config
)

# Configure Streamlit page
st.set_page_config(
    page_title="Multilingual AI Dubbing Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3498db;
        margin: 0.5rem 0;
    }
    
    .voice-profile-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .quality-indicator {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        font-size: 0.8rem;
    }
    
    .quality-excellent { background-color: #d4edda; color: #155724; }
    .quality-good { background-color: #d1ecf1; color: #0c5460; }
    .quality-fair { background-color: #fff3cd; color: #856404; }
    .quality-poor { background-color: #f8d7da; color: #721c24; }
    
    .stProgress > div > div > div > div {
        background-color: #3498db;
    }
</style>
""", unsafe_allow_html=True)

class MultilingualDubbingUI:
    """Main UI class for the dubbing system"""
    
    def __init__(self):
        self.config = create_default_config()
        self.dubbing_system = None
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'dubbing_system' not in st.session_state:
            st.session_state.dubbing_system = None
        
        if 'active_jobs' not in st.session_state:
            st.session_state.active_jobs = {}
        
        if 'voice_profiles' not in st.session_state:
            st.session_state.voice_profiles = {}
        
        if 'speaker_mappings' not in st.session_state:
            st.session_state.speaker_mappings = {}
        
        if 'current_job_id' not in st.session_state:
            st.session_state.current_job_id = None
    
    def render_main_interface(self):
        """Render the main interface"""
        st.markdown('<div class="main-header">🎬 Multilingual AI Dubbing Studio</div>', 
                   unsafe_allow_html=True)
        
        # Sidebar configuration
        self.render_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎥 Video Dubbing", 
            "🎤 Voice Profiles", 
            "👥 Speaker Management",
            "📊 Quality Control",
            "⚙️ System Status"
        ])
        
        with tab1:
            self.render_video_dubbing_tab()
        
        with tab2:
            self.render_voice_profiles_tab()
        
        with tab3:
            self.render_speaker_management_tab()
        
        with tab4:
            self.render_quality_control_tab()
        
        with tab5:
            self.render_system_status_tab()
    
    def render_sidebar(self):
        """Render sidebar configuration"""
        st.sidebar.markdown("### 🔧 System Configuration")
        
        # API Keys
        st.sidebar.markdown("#### API Keys")
        elevenlabs_key = st.sidebar.text_input(
            "ElevenLabs API Key", 
            type="password",
            value=self.config.get("elevenlabs_api_key", "")
        )
        
        openai_key = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password",
            value=self.config.get("openai_api_key", "")
        )
        
        # Model Selection
        st.sidebar.markdown("#### Model Configuration")
        
        use_coqui = st.sidebar.checkbox("Use Coqui TTS", value=True)
        use_musetalk = st.sidebar.checkbox("Use MuseTalk", value=True)
        use_wav2lip = st.sidebar.checkbox("Use Wav2Lip", value=True)
        use_float = st.sidebar.checkbox("Use FLOAT", value=False)
        
        # Performance Settings
        st.sidebar.markdown("#### Performance Settings")
        max_workers = st.sidebar.slider("Max Workers", 1, 8, 4)
        enable_real_time = st.sidebar.checkbox("Enable Real-time Processing", value=False)
        
        # Update configuration
        self.config.update({
            "elevenlabs_api_key": elevenlabs_key,
            "openai_api_key": openai_key,
            "use_coqui_tts": use_coqui,
            "use_musetalk": use_musetalk,
            "use_wav2lip": use_wav2lip,
            "use_float": use_float,
            "max_workers": max_workers,
            "enable_real_time": enable_real_time
        })
        
        # Initialize system button
        if st.sidebar.button("🚀 Initialize System", type="primary"):
            with st.spinner("Initializing dubbing system..."):
                try:
                    st.session_state.dubbing_system = MultilingualAIDubbingSystem(self.config)
                    st.sidebar.success("System initialized successfully!")
                except Exception as e:
                    st.sidebar.error(f"Initialization failed: {e}")
    
    def render_video_dubbing_tab(self):
        """Render video dubbing interface"""
        st.markdown('<div class="section-header">🎥 Video Dubbing</div>', 
                   unsafe_allow_html=True)
        
        if not st.session_state.dubbing_system:
            st.warning("Please initialize the system first using the sidebar.")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Video upload
            st.markdown("#### Upload Video")
            uploaded_video = st.file_uploader(
                "Choose a video file",
                type=['mp4', 'avi', 'mov', 'mkv'],
                help="Upload the video you want to dub"
            )
            
            if uploaded_video:
                # Save uploaded file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(uploaded_video.read())
                    video_path = tmp_file.name
                
                # Display video
                st.video(video_path)
                
                # Language selection
                col1_1, col1_2 = st.columns(2)
                
                with col1_1:
                    source_language = st.selectbox(
                        "Source Language",
                        ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                        help="Language of the original video"
                    )
                
                with col1_2:
                    target_language = st.selectbox(
                        "Target Language",
                        ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                        help="Language to dub the video into"
                    )
                
                # Lip-sync configuration
                st.markdown("#### Lip-Sync Configuration")
                
                col2_1, col2_2, col2_3 = st.columns(3)
                
                with col2_1:
                    model_type = st.selectbox(
                        "Lip-Sync Model",
                        ["musetalk", "wav2lip", "float"],
                        help="Choose the lip-sync generation model"
                    )
                
                with col2_2:
                    quality_level = st.selectbox(
                        "Quality Level",
                        ["low", "medium", "high", "ultra"],
                        index=2,
                        help="Higher quality takes longer to process"
                    )
                
                with col2_3:
                    fps = st.number_input(
                        "Output FPS",
                        min_value=15,
                        max_value=60,
                        value=30,
                        help="Frames per second for output video"
                    )
                
                # Advanced options
                with st.expander("🔧 Advanced Options"):
                    face_enhancement = st.checkbox("Face Enhancement", value=True)
                    temporal_consistency = st.checkbox("Temporal Consistency", value=True)
                    emotion_preservation = st.checkbox("Emotion Preservation", value=True)
                    
                    resolution = st.selectbox(
                        "Output Resolution",
                        ["1920x1080", "1280x720", "854x480"],
                        help="Output video resolution"
                    )
                    
                    output_formats = st.multiselect(
                        "Output Formats",
                        ["mp4", "avi", "mov"],
                        default=["mp4"],
                        help="Choose output video formats"
                    )
                
                # Start dubbing button
                if st.button("🎬 Start Dubbing", type="primary"):
                    self.start_dubbing_job(
                        video_path, source_language, target_language,
                        model_type, quality_level, fps, face_enhancement,
                        temporal_consistency, emotion_preservation,
                        resolution, output_formats
                    )
        
        with col2:
            # Job status
            st.markdown("#### Current Jobs")
            self.render_job_status_panel()
    
    def start_dubbing_job(self, video_path: str, source_language: str, 
                         target_language: str, model_type: str, quality_level: str,
                         fps: int, face_enhancement: bool, temporal_consistency: bool,
                         emotion_preservation: bool, resolution: str, output_formats: List[str]):
        """Start a new dubbing job"""
        try:
            # Create lip-sync configuration
            width, height = map(int, resolution.split('x'))
            lip_sync_config = LipSyncConfig(
                model_type=model_type,
                quality_level=quality_level,
                fps=fps,
                resolution=(width, height),
                face_enhancement=face_enhancement,
                temporal_consistency=temporal_consistency,
                emotion_preservation=emotion_preservation
            )
            
            # Create dubbing job
            job = asyncio.run(
                st.session_state.dubbing_system.create_dubbing_job(
                    video_path=video_path,
                    target_language=target_language,
                    source_language=source_language,
                    lip_sync_config=lip_sync_config,
                    output_formats=output_formats
                )
            )
            
            st.session_state.active_jobs[job.job_id] = job
            st.session_state.current_job_id = job.job_id
            
            st.success(f"Dubbing job started! Job ID: {job.job_id}")
            
            # Start processing in background
            self.process_job_async(job)
            
        except Exception as e:
            st.error(f"Failed to start dubbing job: {e}")
    
    def process_job_async(self, job: DubbingJob):
        """Process job asynchronously"""
        try:
            # This would typically be run in a separate thread or process
            # For demo purposes, we'll simulate the process
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate processing steps
            steps = [
                "Extracting audio...",
                "Identifying speakers...",
                "Transcribing content...",
                "Translating text...",
                "Creating voice mappings...",
                "Generating dubbed audio...",
                "Creating lip-sync video...",
                "Quality assessment...",
                "Finalizing output..."
            ]
            
            for i, step in enumerate(steps):
                status_text.text(step)
                progress = (i + 1) / len(steps)
                progress_bar.progress(progress)
                job.progress = progress * 100
                time.sleep(2)  # Simulate processing time
            
            job.status = "completed"
            status_text.text("✅ Dubbing completed successfully!")
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            st.error(f"Job processing failed: {e}")
    
    def render_job_status_panel(self):
        """Render job status panel"""
        if not st.session_state.active_jobs:
            st.info("No active jobs")
            return
        
        for job_id, job in st.session_state.active_jobs.items():
            with st.container():
                st.markdown(f"**Job:** `{job_id[:8]}...`")
                
                # Status indicator
                status_color = {
                    "pending": "🟡",
                    "processing": "🔵", 
                    "completed": "🟢",
                    "failed": "🔴"
                }
                
                st.markdown(f"**Status:** {status_color.get(job.status, '⚪')} {job.status.title()}")
                
                # Progress bar
                if job.status == "processing":
                    st.progress(job.progress / 100.0)
                    st.text(f"Progress: {job.progress:.1f}%")
                
                # Error message
                if job.error_message:
                    st.error(job.error_message)
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📊 Details", key=f"details_{job_id}"):
                        self.show_job_details(job)
                
                with col2:
                    if job.status == "completed":
                        if st.button(f"⬇️ Download", key=f"download_{job_id}"):
                            self.download_job_results(job)
                
                st.markdown("---")
    
    def show_job_details(self, job: DubbingJob):
        """Show detailed job information"""
        st.markdown(f"### Job Details: {job.job_id}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configuration:**")
            st.json({
                "source_language": job.source_language,
                "target_language": job.target_language,
                "model_type": job.lip_sync_config.model_type,
                "quality_level": job.lip_sync_config.quality_level,
                "fps": job.lip_sync_config.fps,
                "resolution": job.lip_sync_config.resolution
            })
        
        with col2:
            st.markdown("**Status:**")
            st.json({
                "status": job.status,
                "progress": f"{job.progress:.1f}%",
                "created_at": job.created_at.isoformat(),
                "error_message": job.error_message
            })
    
    def download_job_results(self, job: DubbingJob):
        """Download job results"""
        st.info("Download functionality would be implemented here")
        # In a real implementation, this would provide download links
        # for the generated video files
    
    def render_voice_profiles_tab(self):
        """Render voice profiles management"""
        st.markdown('<div class="section-header">🎤 Voice Profiles</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Create New Voice Profile")
            
            # Voice profile creation form
            with st.form("voice_profile_form"):
                profile_name = st.text_input("Profile Name")
                language = st.selectbox(
                    "Language",
                    ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                )
                gender = st.selectbox("Gender", ["male", "female", "other"])
                age_range = st.selectbox(
                    "Age Range", 
                    ["child", "teen", "young_adult", "adult", "senior"]
                )
                
                # Voice samples upload
                st.markdown("**Voice Samples:**")
                voice_samples = st.file_uploader(
                    "Upload voice samples (WAV files)",
                    type=['wav', 'mp3'],
                    accept_multiple_files=True,
                    help="Upload 3-5 high-quality voice samples (10-30 seconds each)"
                )
                
                submitted = st.form_submit_button("Create Profile")
                
                if submitted and profile_name and voice_samples:
                    self.create_voice_profile(
                        profile_name, language, gender, age_range, voice_samples
                    )
        
        with col2:
            st.markdown("#### Existing Voice Profiles")
            self.render_voice_profiles_list()
    
    def create_voice_profile(self, name: str, language: str, gender: str, 
                           age_range: str, voice_samples):
        """Create a new voice profile"""
        try:
            # Save voice samples
            sample_paths = []
            for sample in voice_samples:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    tmp_file.write(sample.read())
                    sample_paths.append(tmp_file.name)
            
            # Create voice profile
            metadata = {
                "name": name,
                "language": language,
                "gender": gender,
                "age_range": age_range
            }
            
            if st.session_state.dubbing_system:
                profile = asyncio.run(
                    st.session_state.dubbing_system.voice_cloning_engine.create_voice_profile(
                        sample_paths, metadata
                    )
                )
                
                st.session_state.voice_profiles[profile.voice_id] = profile
                st.success(f"Voice profile '{name}' created successfully!")
            else:
                st.error("Please initialize the system first")
                
        except Exception as e:
            st.error(f"Failed to create voice profile: {e}")
    
    def render_voice_profiles_list(self):
        """Render list of existing voice profiles"""
        if not st.session_state.voice_profiles:
            st.info("No voice profiles created yet")
            return
        
        for profile_id, profile in st.session_state.voice_profiles.items():
            with st.container():
                st.markdown(f'<div class="voice-profile-card">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{profile.name}**")
                    st.text(f"Language: {profile.language}")
                    st.text(f"Gender: {profile.gender}")
                    st.text(f"Age: {profile.age_range}")
                
                with col2:
                    # Quality indicator
                    quality_class = self.get_quality_class(profile.quality_score)
                    st.markdown(
                        f'<span class="quality-indicator {quality_class}">'
                        f'Quality: {profile.quality_score:.2f}</span>',
                        unsafe_allow_html=True
                    )
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{profile_id}"):
                        del st.session_state.voice_profiles[profile_id]
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    def get_quality_class(self, score: float) -> str:
        """Get CSS class for quality score"""
        if score >= 0.9:
            return "quality-excellent"
        elif score >= 0.8:
            return "quality-good"
        elif score >= 0.7:
            return "quality-fair"
        else:
            return "quality-poor"
    
    def render_speaker_management_tab(self):
        """Render speaker management interface"""
        st.markdown('<div class="section-header">👥 Speaker Management</div>', 
                   unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Speaker Identification")
            
            # Audio upload for speaker analysis
            uploaded_audio = st.file_uploader(
                "Upload audio for speaker analysis",
                type=['wav', 'mp3', 'mp4'],
                help="Upload audio/video file to identify speakers"
            )
            
            if uploaded_audio and st.button("🔍 Analyze Speakers"):
                self.analyze_speakers(uploaded_audio)
        
        with col2:
            st.markdown("#### Speaker Mappings")
            self.render_speaker_mappings()
    
    def analyze_speakers(self, audio_file):
        """Analyze speakers in uploaded audio"""
        try:
            # Save uploaded file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_file.read())
                audio_path = tmp_file.name
            
            if st.session_state.dubbing_system:
                with st.spinner("Analyzing speakers..."):
                    speakers = asyncio.run(
                        st.session_state.dubbing_system.multi_speaker_manager.identify_speakers(
                            audio_path
                        )
                    )
                
                st.success(f"Found {len(speakers)} speakers")
                
                # Display speaker information
                for speaker in speakers:
                    with st.expander(f"Speaker {speaker['speaker_id']}"):
                        st.json(speaker)
            else:
                st.error("Please initialize the system first")
                
        except Exception as e:
            st.error(f"Speaker analysis failed: {e}")
    
    def render_speaker_mappings(self):
        """Render speaker mapping interface"""
        if not st.session_state.speaker_mappings:
            st.info("No speaker mappings created yet")
            return
        
        for mapping_id, mapping in st.session_state.speaker_mappings.items():
            with st.container():
                st.markdown(f"**Mapping:** {mapping_id}")
                st.text(f"Original: {mapping.original_speaker_id}")
                st.text(f"Target: {mapping.target_voice_profile.name}")
                st.text(f"Consistency: {mapping.consistency_score:.2f}")
                st.markdown("---")
    
    def render_quality_control_tab(self):
        """Render quality control interface"""
        st.markdown('<div class="section-header">📊 Quality Control</div>', 
                   unsafe_allow_html=True)
        
        if not st.session_state.active_jobs:
            st.info("No jobs available for quality assessment")
            return
        
        # Job selection for quality review
        job_ids = list(st.session_state.active_jobs.keys())
        selected_job_id = st.selectbox(
            "Select job for quality review",
            job_ids,
            format_func=lambda x: f"{x[:8]}... ({st.session_state.active_jobs[x].status})"
        )
        
        if selected_job_id:
            job = st.session_state.active_jobs[selected_job_id]
            
            if job.status == "completed":
                self.render_quality_metrics(job)
            else:
                st.info(f"Job is {job.status}. Quality metrics available after completion.")
    
    def render_quality_metrics(self, job: DubbingJob):
        """Render quality metrics for a completed job"""
        # Simulate quality metrics
        quality_metrics = {
            "lip_sync_accuracy": 0.85,
            "voice_quality": 0.92,
            "visual_quality": 0.88,
            "temporal_consistency": 0.90,
            "overall_score": 0.89
        }
        
        # Quality metrics display
        col1, col2, col3, col4, col5 = st.columns(5)
        
        metrics = [
            ("Lip-Sync", quality_metrics["lip_sync_accuracy"]),
            ("Voice", quality_metrics["voice_quality"]),
            ("Visual", quality_metrics["visual_quality"]),
            ("Temporal", quality_metrics["temporal_consistency"]),
            ("Overall", quality_metrics["overall_score"])
        ]
        
        for col, (name, score) in zip([col1, col2, col3, col4, col5], metrics):
            with col:
                st.metric(
                    name,
                    f"{score:.2f}",
                    delta=f"{(score - 0.8):.2f}" if score > 0.8 else None
                )
        
        # Quality visualization
        st.markdown("#### Quality Breakdown")
        
        fig = go.Figure(data=go.Scatterpolar(
            r=list(quality_metrics.values()),
            theta=list(quality_metrics.keys()),
            fill='toself',
            name='Quality Metrics'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=False,
            title="Quality Assessment Radar Chart"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Manual correction tools
        st.markdown("#### Manual Corrections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 Apply Lip-Sync Corrections"):
                st.info("Lip-sync correction would be applied here")
        
        with col2:
            if st.button("🎨 Enhance Video Quality"):
                st.info("Video enhancement would be applied here")
    
    def render_system_status_tab(self):
        """Render system status and monitoring"""
        st.markdown('<div class="section-header">⚙️ System Status</div>', 
                   unsafe_allow_html=True)
        
        # System information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### System Health")
            st.success("🟢 System Online")
            st.info(f"Active Jobs: {len(st.session_state.active_jobs)}")
            st.info(f"Voice Profiles: {len(st.session_state.voice_profiles)}")
        
        with col2:
            st.markdown("#### Model Status")
            models = ["Coqui TTS", "MuseTalk", "Wav2Lip", "WhisperX"]
            for model in models:
                status = "🟢 Ready" if st.session_state.dubbing_system else "🔴 Not Initialized"
                st.text(f"{model}: {status}")
        
        with col3:
            st.markdown("#### Resource Usage")
            # Simulate resource usage
            st.progress(0.65, text="GPU Memory: 65%")
            st.progress(0.45, text="CPU Usage: 45%")
            st.progress(0.30, text="RAM Usage: 30%")
        
        # Configuration display
        st.markdown("#### Current Configuration")
        st.json(self.config)
        
        # Logs (simulated)
        st.markdown("#### Recent Logs")
        logs = [
            f"{datetime.now().strftime('%H:%M:%S')} - System initialized successfully",
            f"{datetime.now().strftime('%H:%M:%S')} - Voice profile created: Sample Voice",
            f"{datetime.now().strftime('%H:%M:%S')} - Dubbing job started: job_12345",
            f"{datetime.now().strftime('%H:%M:%S')} - Quality assessment completed"
        ]
        
        for log in logs[-10:]:  # Show last 10 logs
            st.text(log)

def main():
    """Main application entry point"""
    ui = MultilingualDubbingUI()
    ui.render_main_interface()

if __name__ == "__main__":
    main()