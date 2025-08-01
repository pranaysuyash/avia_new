"""
Video Processing UI Components for Streamlit
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from typing import Optional

from video_processing import VideoProcessor, VideoAnalysis
from media import is_video_file


class VideoUI:
    """Video processing user interface"""
    
    def __init__(self):
        self.processor = VideoProcessor()
    
    def render_video_analyzer(self) -> Optional[VideoAnalysis]:
        """Render video analysis interface"""
        st.header("🎬 Video Analysis")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Video File",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            help="Upload a video file for analysis"
        )
        
        if not uploaded_file:
            st.info("Upload a video file to begin analysis")
            return None
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            video_path = tmp_file.name
        
        try:
            # Analysis options
            st.subheader("Analysis Options")
            col1, col2 = st.columns(2)
            
            with col1:
                extract_frames = st.checkbox("Extract Keyframes", value=True)
                detect_scenes = st.checkbox("Detect Scenes", value=True)
            
            with col2:
                keyframe_interval = st.slider(
                    "Keyframe Interval (seconds)",
                    min_value=1.0,
                    max_value=30.0,
                    value=5.0,
                    step=1.0
                )
            
            # Run analysis
            if st.button("Analyze Video", type="primary"):
                with st.spinner("Analyzing video..."):
                    analysis = self.processor.analyze_video(
                        video_path,
                        extract_frames=extract_frames,
                        detect_scenes=detect_scenes,
                        keyframe_interval=keyframe_interval
                    )
                
                # Display results
                self._display_analysis_results(analysis)
                return analysis
        
        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.unlink(video_path)
        
        return None
    
    def _display_analysis_results(self, analysis: VideoAnalysis):
        """Display video analysis results"""
        st.success("Video analysis completed!")
        
        # Basic information
        st.subheader("📊 Video Information")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Duration", f"{analysis.duration:.1f}s")
        with col2:
            st.metric("Resolution", f"{analysis.width}×{analysis.height}")
        with col3:
            st.metric("FPS", f"{analysis.fps:.1f}")
        with col4:
            st.metric("Total Frames", analysis.total_frames)
        
        # Content analysis
        if analysis.scenes or analysis.keyframes:
            st.subheader("🎯 Content Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Scenes Detected", len(analysis.scenes))
            with col2:
                st.metric("Keyframes Extracted", len(analysis.keyframes))
            with col3:
                avg_scene_duration = sum(s.duration for s in analysis.scenes) / len(analysis.scenes) if analysis.scenes else 0
                st.metric("Avg Scene Duration", f"{avg_scene_duration:.1f}s")
        
        # Scene breakdown
        if analysis.scenes:
            st.subheader("🎬 Scene Breakdown")
            
            scene_data = []
            for i, scene in enumerate(analysis.scenes):
                scene_data.append({
                    "Scene": i + 1,
                    "Start Time": f"{scene.start_time:.1f}s",
                    "End Time": f"{scene.end_time:.1f}s", 
                    "Duration": f"{scene.duration:.1f}s",
                    "Keyframes": len(scene.keyframes)
                })
            
            st.dataframe(scene_data, use_container_width=True)
        
        # Keyframes gallery
        if analysis.keyframes:
            st.subheader("🖼️ Keyframes")
            
            # Display keyframes in a grid
            cols = st.columns(3)
            for i, frame in enumerate(analysis.keyframes):
                with cols[i % 3]:
                    if frame.image_path and os.path.exists(frame.image_path):
                        st.image(
                            frame.image_path,
                            caption=f"Frame {frame.frame_number} ({frame.timestamp:.1f}s)",
                            use_column_width=True
                        )
                    
                    # Frame details
                    with st.expander(f"Frame {frame.frame_number} Details"):
                        st.write(f"**Timestamp:** {frame.timestamp:.2f}s")
                        st.write(f"**Brightness:** {frame.brightness:.1f}")
                        if frame.scene_id is not None:
                            st.write(f"**Scene:** {frame.scene_id}")
        
        # Technical details
        if analysis.metadata:
            st.subheader("🔧 Technical Details")
            
            with st.expander("Video Metadata"):
                metadata_display = {}
                for key, value in analysis.metadata.items():
                    if value is not None and value != "":
                        # Format key for display
                        display_key = key.replace('_', ' ').title()
                        metadata_display[display_key] = str(value)
                
                st.json(metadata_display)
        
        # Export options
        st.subheader("📤 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download Analysis JSON"):
                analysis_json = analysis.to_dict()
                st.download_button(
                    label="Download JSON",
                    data=str(analysis_json),
                    file_name=f"video_analysis_{analysis.video_path.split('/')[-1]}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Create Thumbnail"):
                try:
                    thumbnail_path = self.processor.create_video_thumbnail(analysis.video_path)
                    st.success(f"Thumbnail saved: {thumbnail_path}")
                    
                    if os.path.exists(thumbnail_path):
                        st.image(thumbnail_path, caption="Video Thumbnail", width=200)
                except Exception as e:
                    st.error(f"Failed to create thumbnail: {e}")
    
    def render_frame_extractor(self):
        """Render frame extraction interface"""
        st.header("🖼️ Frame Extractor")
        
        uploaded_file = st.file_uploader(
            "Upload Video for Frame Extraction",
            type=['mp4', 'avi', 'mov', 'mkv', 'webm'],
            key="frame_extractor"
        )
        
        if not uploaded_file:
            st.info("Upload a video file to extract specific frames")
            return
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            video_path = tmp_file.name
        
        try:
            # Get video info for timestamp validation
            import cv2
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps if fps > 0 else 0
                cap.release()
                
                st.info(f"Video duration: {duration:.1f} seconds ({total_frames} frames at {fps:.1f} FPS)")
                
                # Timestamp input
                st.subheader("Extract Frames at Timestamps")
                timestamp_input = st.text_area(
                    "Enter timestamps (one per line, in seconds)",
                    placeholder="0.5\n1.0\n2.5\n5.0",
                    help="Enter timestamps in seconds, one per line"
                )
                
                if st.button("Extract Frames", type="primary"):
                    if timestamp_input.strip():
                        try:
                            timestamps = [float(t.strip()) for t in timestamp_input.strip().split('\n') if t.strip()]
                            
                            # Validate timestamps
                            valid_timestamps = [t for t in timestamps if 0 <= t <= duration]
                            if len(valid_timestamps) != len(timestamps):
                                st.warning(f"Some timestamps are outside video duration (0-{duration:.1f}s)")
                            
                            if valid_timestamps:
                                with st.spinner("Extracting frames..."):
                                    frames = self.processor.extract_frames_at_timestamps(video_path, valid_timestamps)
                                
                                st.success(f"Extracted {len(frames)} frames")
                                
                                # Display extracted frames
                                cols = st.columns(min(len(frames), 3))
                                for i, frame in enumerate(frames):
                                    with cols[i % 3]:
                                        if frame.image_path and os.path.exists(frame.image_path):
                                            st.image(
                                                frame.image_path,
                                                caption=f"t={frame.timestamp:.1f}s",
                                                use_column_width=True
                                            )
                            else:
                                st.error("No valid timestamps provided")
                        except ValueError:
                            st.error("Invalid timestamp format. Please enter numbers only.")
                    else:
                        st.warning("Please enter at least one timestamp")
        
        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.unlink(video_path)
    
    def render_video_tools(self):
        """Render video processing tools interface"""
        st.header("🛠️ Video Processing Tools")
        
        tabs = st.tabs(["Video Analyzer", "Frame Extractor"])
        
        with tabs[0]:
            self.render_video_analyzer()
        
        with tabs[1]:
            self.render_frame_extractor()


def render_video_ui():
    """Main function to render video UI"""
    video_ui = VideoUI()
    video_ui.render_video_tools()