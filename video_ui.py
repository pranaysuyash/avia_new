#!/usr/bin/env python3
"""
Video Processing UI Components
Streamlit interface for video-specific processing features
"""

import os
import streamlit as st
import tempfile
from typing import Dict, List, Any, Optional
import json
from video_processing import VideoProcessor, VideoMetadata, VideoThumbnail, VideoChapter, VideoQualityMetrics
import base64
from PIL import Image


class VideoUI:
    """Streamlit UI components for video processing"""
    
    def __init__(self):
        self.processor = VideoProcessor()
        
    def render_video_upload_section(self) -> Optional[str]:
        """Render video upload section and return uploaded file path"""
        st.subheader("📹 Video Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'],
            help="Upload a video file for processing. Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V"
        )
        
        if uploaded_file is not None:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name
            
            # Display file info
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.success(f"✅ Uploaded: {uploaded_file.name} ({file_size_mb:.1f} MB)")
            
            return temp_path
        
        return None
    
    def render_video_metadata_section(self, video_path: str) -> VideoMetadata:
        """Render video metadata display"""
        try:
            metadata = self.processor.extract_metadata(video_path)
            
            st.subheader("📊 Video Information")
            
            # Create columns for metadata display
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Duration", f"{metadata.duration:.1f}s")
                st.metric("Resolution", f"{metadata.width}×{metadata.height}")
                st.metric("Aspect Ratio", metadata.aspect_ratio)
            
            with col2:
                st.metric("Frame Rate", f"{metadata.fps:.1f} FPS")
                st.metric("Bitrate", f"{metadata.bitrate / 1_000_000:.1f} Mbps")
                st.metric("File Size", f"{metadata.size_bytes / (1024*1024):.1f} MB")
            
            with col3:
                st.metric("Video Codec", metadata.codec)
                st.metric("Format", metadata.format)
                st.metric("Audio", "Yes" if metadata.has_audio else "No")
            
            # Expandable detailed info
            with st.expander("🔍 Detailed Technical Information"):
                tech_info = {
                    "Video Codec": metadata.codec,
                    "Audio Codec": metadata.audio_codec or "None",
                    "Audio Bitrate": f"{metadata.audio_bitrate / 1000:.0f} kbps" if metadata.audio_bitrate else "N/A",
                    "Audio Sample Rate": f"{metadata.audio_sample_rate} Hz" if metadata.audio_sample_rate else "N/A",
                    "Total Pixels": f"{metadata.width * metadata.height:,}",
                    "Data Rate": f"{metadata.size_bytes / metadata.duration / 1024:.1f} KB/s" if metadata.duration > 0 else "N/A"
                }
                
                for key, value in tech_info.items():
                    st.text(f"{key}: {value}")
            
            return metadata
            
        except Exception as e:
            st.error(f"❌ Failed to extract video metadata: {e}")
            return None
    
    def render_video_thumbnails_section(self, video_path: str) -> List[VideoThumbnail]:
        """Render video thumbnails generation and display"""
        st.subheader("🖼️ Video Thumbnails")
        
        # Thumbnail generation options
        col1, col2 = st.columns(2)
        with col1:
            thumbnail_count = st.slider("Number of thumbnails", 1, 20, 8)
        with col2:
            quality_threshold = st.slider("Quality threshold", 0.0, 1.0, 0.5, 0.1)
        
        if st.button("🎯 Generate Thumbnails", type="primary"):
            try:
                with st.spinner("Generating thumbnails..."):
                    thumbnails = self.processor.generate_thumbnails(
                        video_path, 
                        count=thumbnail_count,
                        quality_threshold=quality_threshold
                    )
                
                if thumbnails:
                    st.success(f"✅ Generated {len(thumbnails)} thumbnails")
                    
                    # Display thumbnails in a grid
                    cols_per_row = 4
                    for i in range(0, len(thumbnails), cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for j, col in enumerate(cols):
                            if i + j < len(thumbnails):
                                thumbnail = thumbnails[i + j]
                                
                                with col:
                                    # Display thumbnail image
                                    if os.path.exists(thumbnail.image_path):
                                        image = Image.open(thumbnail.image_path)
                                        st.image(image, caption=f"t={thumbnail.timestamp:.1f}s", use_column_width=True)
                                        
                                        # Quality info
                                        quality_color = "🟢" if thumbnail.quality_score > 0.7 else "🟡" if thumbnail.quality_score > 0.4 else "🔴"
                                        st.caption(f"{quality_color} Quality: {thumbnail.quality_score:.2f}")
                                        
                                        # Download button
                                        with open(thumbnail.image_path, "rb") as file:
                                            st.download_button(
                                                label="📥 Download",
                                                data=file.read(),
                                                file_name=f"thumbnail_{thumbnail.timestamp:.1f}s.jpg",
                                                mime="image/jpeg",
                                                key=f"thumb_download_{i+j}"
                                            )
                    
                    return thumbnails
                else:
                    st.warning("⚠️ No thumbnails generated")
                    return []
                    
            except Exception as e:
                st.error(f"❌ Failed to generate thumbnails: {e}")
                return []
        
        return []
    
    def render_subtitle_generation_section(self, video_path: str, transcript_data: Dict[str, Any]) -> Optional[str]:
        """Render subtitle generation section"""
        st.subheader("📝 Subtitle Generation")
        
        if not transcript_data:
            st.warning("⚠️ No transcript data available. Please transcribe the video first.")
            return None
        
        # Subtitle options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            subtitle_format = st.selectbox("Format", ["srt", "vtt"], index=0)
        
        with col2:
            max_chars_per_line = st.number_input("Max chars per line", 20, 80, 42)
        
        with col3:
            max_lines = st.number_input("Max lines", 1, 3, 2)
        
        if st.button("🎬 Generate Subtitles", type="primary"):
            try:
                with st.spinner("Generating subtitles..."):
                    # Create temporary subtitle file
                    subtitle_filename = f"subtitles.{subtitle_format}"
                    subtitle_path = os.path.join(tempfile.gettempdir(), subtitle_filename)
                    
                    generated_path = self.processor.generate_subtitles(
                        transcript_data=transcript_data,
                        output_path=subtitle_path,
                        format_type=subtitle_format,
                        max_chars_per_line=max_chars_per_line,
                        max_lines=max_lines
                    )
                
                if generated_path and os.path.exists(generated_path):
                    st.success(f"✅ Generated {subtitle_format.upper()} subtitles")
                    
                    # Display subtitle preview
                    with st.expander("👀 Subtitle Preview"):
                        with open(generated_path, 'r', encoding='utf-8') as f:
                            subtitle_content = f.read()
                            # Show first 1000 characters
                            preview_content = subtitle_content[:1000]
                            if len(subtitle_content) > 1000:
                                preview_content += "\n\n... (truncated)"
                            
                            st.code(preview_content, language='text')
                    
                    # Download button
                    with open(generated_path, 'r', encoding='utf-8') as f:
                        subtitle_content = f.read()
                        st.download_button(
                            label=f"📥 Download {subtitle_format.upper()} File",
                            data=subtitle_content,
                            file_name=subtitle_filename,
                            mime="text/plain"
                        )
                    
                    return generated_path
                else:
                    st.error("❌ Failed to generate subtitles")
                    return None
                    
            except Exception as e:
                st.error(f"❌ Failed to generate subtitles: {e}")
                return None
        
        return None
    
    def render_chapter_detection_section(self, video_path: str, transcript_data: Dict[str, Any]) -> List[VideoChapter]:
        """Render chapter detection section"""
        st.subheader("📚 Chapter Detection")
        
        # Chapter detection options
        col1, col2 = st.columns(2)
        
        with col1:
            min_chapter_length = st.slider("Min chapter length (seconds)", 10.0, 300.0, 30.0, 10.0)
        
        with col2:
            scene_threshold = st.slider("Scene change sensitivity", 0.1, 1.0, 0.3, 0.1)
        
        if st.button("🔍 Detect Chapters", type="primary"):
            try:
                with st.spinner("Detecting chapters..."):
                    chapters = self.processor.detect_chapters(
                        video_path=video_path,
                        transcript_data=transcript_data,
                        min_chapter_length=min_chapter_length,
                        scene_threshold=scene_threshold
                    )
                
                if chapters:
                    st.success(f"✅ Detected {len(chapters)} chapters")
                    
                    # Display chapters
                    for i, chapter in enumerate(chapters):
                        with st.expander(f"📖 Chapter {i+1}: {chapter.title}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Duration:** {chapter.start_time:.1f}s - {chapter.end_time:.1f}s ({chapter.end_time - chapter.start_time:.1f}s)")
                                st.write(f"**Description:** {chapter.description}")
                                
                                if chapter.keywords:
                                    st.write(f"**Keywords:** {', '.join(chapter.keywords[:10])}")
                                
                                st.write(f"**Confidence:** {chapter.confidence:.2f}")
                            
                            with col2:
                                # Display chapter thumbnail if available
                                if chapter.thumbnail_path and os.path.exists(chapter.thumbnail_path):
                                    image = Image.open(chapter.thumbnail_path)
                                    st.image(image, caption=f"Chapter {i+1}", use_column_width=True)
                    
                    # Export chapters as JSON
                    chapters_json = json.dumps([
                        {
                            "title": chapter.title,
                            "start_time": chapter.start_time,
                            "end_time": chapter.end_time,
                            "description": chapter.description,
                            "keywords": chapter.keywords or [],
                            "confidence": chapter.confidence
                        }
                        for chapter in chapters
                    ], indent=2)
                    
                    st.download_button(
                        label="📥 Download Chapters (JSON)",
                        data=chapters_json,
                        file_name="video_chapters.json",
                        mime="application/json"
                    )
                    
                    return chapters
                else:
                    st.warning("⚠️ No chapters detected")
                    return []
                    
            except Exception as e:
                st.error(f"❌ Failed to detect chapters: {e}")
                return []
        
        return []
    
    def render_quality_analysis_section(self, video_path: str) -> Optional[VideoQualityMetrics]:
        """Render video quality analysis section"""
        st.subheader("🎯 Video Quality Analysis")
        
        if st.button("🔬 Analyze Video Quality", type="primary"):
            try:
                with st.spinner("Analyzing video quality..."):
                    quality_metrics = self.processor.analyze_video_quality(video_path)
                
                # Overall quality score
                score_color = "🟢" if quality_metrics.overall_score > 0.8 else "🟡" if quality_metrics.overall_score > 0.6 else "🔴"
                st.metric(
                    "Overall Quality Score", 
                    f"{quality_metrics.overall_score:.2f}",
                    delta=None,
                    help="Quality score from 0.0 (poor) to 1.0 (excellent)"
                )
                
                # Individual scores
                st.subheader("📊 Quality Breakdown")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Resolution", f"{quality_metrics.resolution_score:.2f}")
                
                with col2:
                    st.metric("Bitrate", f"{quality_metrics.bitrate_score:.2f}")
                
                with col3:
                    st.metric("Frame Rate", f"{quality_metrics.fps_score:.2f}")
                
                with col4:
                    st.metric("Compression", f"{quality_metrics.compression_score:.2f}")
                
                # Quality visualization
                quality_data = {
                    "Resolution": quality_metrics.resolution_score,
                    "Bitrate": quality_metrics.bitrate_score,
                    "Frame Rate": quality_metrics.fps_score,
                    "Compression": quality_metrics.compression_score
                }
                
                st.subheader("📈 Quality Radar Chart")
                st.bar_chart(quality_data)
                
                # Recommendations
                if quality_metrics.recommendations:
                    st.subheader("💡 Recommendations")
                    for i, recommendation in enumerate(quality_metrics.recommendations):
                        st.write(f"{i+1}. {recommendation}")
                else:
                    st.success("✅ No quality improvements needed!")
                
                # Technical details
                with st.expander("🔧 Technical Details"):
                    for key, value in quality_metrics.technical_details.items():
                        if isinstance(value, float):
                            st.text(f"{key.replace('_', ' ').title()}: {value:.2f}")
                        else:
                            st.text(f"{key.replace('_', ' ').title()}: {value}")
                
                return quality_metrics
                
            except Exception as e:
                st.error(f"❌ Failed to analyze video quality: {e}")
                return None
        
        return None
    
    def render_video_player_section(self, video_path: str, subtitle_path: str = None, chapters: List[VideoChapter] = None):
        """Render enhanced video player with synchronized features"""
        st.subheader("🎬 Enhanced Video Player")
        
        # Basic video player
        st.video(video_path)
        
        # Player controls and features
        col1, col2 = st.columns(2)
        
        with col1:
            if subtitle_path:
                st.success("✅ Subtitles available")
                with open(subtitle_path, 'r', encoding='utf-8') as f:
                    subtitle_content = f.read()
                    with st.expander("📝 View Subtitles"):
                        st.code(subtitle_content, language='text')
            else:
                st.info("ℹ️ No subtitles available")
        
        with col2:
            if chapters:
                st.success(f"✅ {len(chapters)} chapters detected")
                with st.expander("📚 Chapter Navigation"):
                    for i, chapter in enumerate(chapters):
                        st.write(f"**{i+1}. {chapter.title}**")
                        st.write(f"⏱️ {chapter.start_time:.1f}s - {chapter.end_time:.1f}s")
                        if st.button(f"▶️ Jump to Chapter {i+1}", key=f"chapter_{i}"):
                            st.info(f"Would jump to {chapter.start_time:.1f}s (feature requires JavaScript)")
            else:
                st.info("ℹ️ No chapters detected")
        
        # Generate enhanced HTML player
        if st.button("🚀 Generate Enhanced Player", type="secondary"):
            try:
                from video_processing import create_video_player_html
                
                html_content = create_video_player_html(
                    video_path=video_path,
                    subtitle_path=subtitle_path,
                    chapters=chapters or []
                )
                
                # Save HTML file
                html_filename = "enhanced_video_player.html"
                html_path = os.path.join(tempfile.gettempdir(), html_filename)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                st.success("✅ Enhanced player generated!")
                
                # Download button for HTML player
                st.download_button(
                    label="📥 Download Enhanced Player (HTML)",
                    data=html_content,
                    file_name=html_filename,
                    mime="text/html"
                )
                
                # Display preview
                with st.expander("👀 Player Preview"):
                    st.components.v1.html(html_content, height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"❌ Failed to generate enhanced player: {e}")
    
    def render_video_preview_section(self, video_path: str):
        """Render video preview generation section"""
        st.subheader("🎞️ Video Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            preview_duration = st.slider("Preview duration (seconds)", 5.0, 60.0, 30.0, 5.0)
        
        with col2:
            start_offset = st.slider("Start offset (seconds)", 0.0, 300.0, 10.0, 5.0)
        
        if st.button("🎬 Create Preview", type="secondary"):
            try:
                with st.spinner("Creating video preview..."):
                    preview_filename = "video_preview.mp4"
                    preview_path = os.path.join(tempfile.gettempdir(), preview_filename)
                    
                    generated_path = self.processor.create_video_preview(
                        video_path=video_path,
                        output_path=preview_path,
                        duration=preview_duration,
                        start_offset=start_offset
                    )
                
                if generated_path and os.path.exists(generated_path):
                    st.success("✅ Preview created successfully!")
                    
                    # Display preview
                    st.video(generated_path)
                    
                    # Download button
                    with open(generated_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Preview",
                            data=f.read(),
                            file_name=preview_filename,
                            mime="video/mp4"
                        )
                else:
                    st.error("❌ Failed to create preview")
                    
            except Exception as e:
                st.error(f"❌ Failed to create preview: {e}")


def main():
    """Main function for testing the video UI components"""
    st.set_page_config(
        page_title="Video Processing Features",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Video Processing Features")
    st.markdown("Advanced video processing capabilities for transcription and analysis")
    
    # Initialize UI
    video_ui = VideoUI()
    
    # Video upload
    video_path = video_ui.render_video_upload_section()
    
    if video_path:
        # Store video path in session state
        st.session_state.video_path = video_path
        
        # Video metadata
        metadata = video_ui.render_video_metadata_section(video_path)
        
        if metadata:
            # Create tabs for different features
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "🖼️ Thumbnails", 
                "📝 Subtitles", 
                "📚 Chapters", 
                "🎯 Quality", 
                "🎬 Player",
                "🎞️ Preview"
            ])
            
            with tab1:
                thumbnails = video_ui.render_video_thumbnails_section(video_path)
                if thumbnails:
                    st.session_state.thumbnails = thumbnails
            
            with tab2:
                # For demo purposes, create sample transcript data
                sample_transcript = {
                    "segments": [
                        {"start": 0.0, "end": 5.0, "text": "Welcome to this video demonstration."},
                        {"start": 5.0, "end": 10.0, "text": "Today we'll be exploring video processing features."},
                        {"start": 10.0, "end": 15.0, "text": "This includes subtitle generation and chapter detection."}
                    ]
                }
                
                subtitle_path = video_ui.render_subtitle_generation_section(video_path, sample_transcript)
                if subtitle_path:
                    st.session_state.subtitle_path = subtitle_path
            
            with tab3:
                chapters = video_ui.render_chapter_detection_section(video_path, sample_transcript)
                if chapters:
                    st.session_state.chapters = chapters
            
            with tab4:
                quality_metrics = video_ui.render_quality_analysis_section(video_path)
                if quality_metrics:
                    st.session_state.quality_metrics = quality_metrics
            
            with tab5:
                video_ui.render_video_player_section(
                    video_path,
                    st.session_state.get('subtitle_path'),
                    st.session_state.get('chapters')
                )
            
            with tab6:
                video_ui.render_video_preview_section(video_path)


if __name__ == "__main__":
    main()