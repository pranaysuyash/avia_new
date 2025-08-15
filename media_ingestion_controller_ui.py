"""
Streamlit UI for Media Ingestion Controller
"""

import streamlit as st
import asyncio
import tempfile
import os
from pathlib import Path
import time

from media_ingestion_controller import (
    MediaIngestionController, ProcessingOptions
)


def main():
    """Main Streamlit interface for Media Ingestion Controller"""
    st.set_page_config(
        page_title="Media Ingestion Controller",
        page_icon="📥",
        layout="wide"
    )
    
    st.title("📥 Media Ingestion Controller")
    st.markdown("Unified media processing with intelligent format detection and preprocessing")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Processing Options")
        
        enable_preprocessing = st.checkbox("Enable Preprocessing", value=True)
        enable_optimization = st.checkbox("Enable Optimization", value=False)
        
        target_quality = st.selectbox(
            "Target Quality",
            ["low", "medium", "high", "ultra"],
            index=2
        )
        
        st.subheader("Image Processing")
        max_width = st.number_input("Max Width (px)", min_value=100, max_value=4000, value=1920)
        max_height = st.number_input("Max Height (px)", min_value=100, max_value=4000, value=1080)
        
        st.subheader("File Size Limits")
        max_file_size = st.number_input("Max File Size (MB)", min_value=1, max_value=2048, value=100)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a media file",
            type=['mp3', 'wav', 'm4a', 'flac', 'mp4', 'avi', 'mov', 'mkv', 
                  'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp',
                  'pdf', 'txt', 'docx', 'doc', 'rtf'],
            help="Supported formats: Audio, Video, Image, and Document files"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.subheader("📋 File Information")
            file_info_col1, file_info_col2 = st.columns(2)
            
            with file_info_col1:
                st.metric("Filename", uploaded_file.name)
                st.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
            
            with file_info_col2:
                file_extension = Path(uploaded_file.name).suffix.lower()
                st.metric("Extension", file_extension)
                
                # Determine file type
                if file_extension in ['.mp3', '.wav', '.m4a', '.flac']:
                    file_type = "🎵 Audio"
                elif file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
                    file_type = "🎬 Video"
                elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                    file_type = "🖼️ Image"
                elif file_extension in ['.pdf', '.txt', '.docx', '.doc', '.rtf']:
                    file_type = "📄 Document"
                else:
                    file_type = "❓ Unknown"
                
                st.metric("Type", file_type)
            
            # Process button
            if st.button("🚀 Process Media", type="primary"):
                process_media(uploaded_file, enable_preprocessing, enable_optimization, 
                            target_quality, max_width, max_height, max_file_size)
    
    with col2:
        st.header("📊 Supported Formats")
        
        with st.expander("🎵 Audio Formats"):
            st.write("• MP3, WAV, M4A, FLAC, AAC")
        
        with st.expander("🎬 Video Formats"):
            st.write("• MP4, AVI, MOV, MKV, WebM")
        
        with st.expander("🖼️ Image Formats"):
            st.write("• JPG, PNG, GIF, BMP, TIFF, WebP")
        
        with st.expander("📄 Document Formats"):
            st.write("• PDF, TXT, DOCX, DOC, RTF")
        
        st.header("ℹ️ Processing Features")
        st.info("""
        **Format Detection**: Intelligent multi-method format detection
        
        **Content Validation**: Comprehensive file integrity checks
        
        **Quality Analysis**: Automatic quality scoring and metrics
        
        **Preprocessing**: Type-specific optimization and enhancement
        
        **Progress Tracking**: Real-time processing status updates
        """)


def process_media(uploaded_file, enable_preprocessing, enable_optimization, 
                 target_quality, max_width, max_height, max_file_size):
    """Process the uploaded media file"""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Initialize controller
        controller = MediaIngestionController(max_file_size_mb=max_file_size)
        
        # Save uploaded file temporarily
        status_text.text("💾 Saving uploaded file...")
        progress_bar.progress(10)
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        
        try:
            # Configure processing options
            status_text.text("⚙️ Configuring processing options...")
            progress_bar.progress(20)
            
            options = ProcessingOptions(
                enable_preprocessing=enable_preprocessing,
                enable_optimization=enable_optimization,
                target_quality=target_quality,
                max_resolution=(max_width, max_height) if max_width and max_height else None
            )
            
            # Run ingestion in async context
            status_text.text("🔍 Analyzing media format...")
            progress_bar.progress(40)
            
            async def run_ingestion():
                return await controller.ingest_media(temp_path, uploaded_file.name, options)
            
            # Execute async function
            result = asyncio.run(run_ingestion())
            
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Display results
            display_results(result, uploaded_file.name)
            
        finally:
            # Cleanup
            os.unlink(temp_path)
            
    except Exception as e:
        st.error(f"❌ Processing failed: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Processing failed")


def display_results(result, filename):
    """Display processing results"""
    
    st.subheader("📊 Processing Results")
    
    if result.success:
        st.success("✅ Media processing completed successfully!")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Processing Time", f"{result.processing_time:.2f}s")
        
        with col2:
            quality_score = result.media_file.quality_metrics.quality_score if result.media_file.quality_metrics else 0
            st.metric("Quality Score", f"{quality_score:.1f}/100")
        
        with col3:
            st.metric("Operations", len(result.operations_applied))
        
        # Format information
        if result.media_file.format:
            st.subheader("📋 Format Details")
            format_col1, format_col2 = st.columns(2)
            
            with format_col1:
                st.write(f"**File Type:** {result.media_file.format.file_type.title()}")
                st.write(f"**MIME Type:** {result.media_file.format.mime_type}")
                st.write(f"**Extension:** {result.media_file.format.extension}")
            
            with format_col2:
                st.write(f"**Supported:** {'✅ Yes' if result.media_file.format.is_supported else '❌ No'}")
                if result.media_file.format.codec:
                    st.write(f"**Codec:** {result.media_file.format.codec}")
                if result.media_file.format.container:
                    st.write(f"**Container:** {result.media_file.format.container}")
        
        # Quality metrics
        if result.media_file.quality_metrics:
            st.subheader("📈 Quality Metrics")
            metrics = result.media_file.quality_metrics
            
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                st.write(f"**File Size:** {metrics.file_size:,} bytes")
                if metrics.resolution:
                    st.write(f"**Resolution:** {metrics.resolution[0]}×{metrics.resolution[1]}")
                if metrics.duration:
                    st.write(f"**Duration:** {metrics.duration:.1f} seconds")
            
            with metrics_col2:
                if metrics.bitrate:
                    st.write(f"**Bitrate:** {metrics.bitrate:,} bps")
                if metrics.sample_rate:
                    st.write(f"**Sample Rate:** {metrics.sample_rate:,} Hz")
                if metrics.channels:
                    st.write(f"**Channels:** {metrics.channels}")
        
        # Operations applied
        if result.operations_applied:
            st.subheader("🔧 Operations Applied")
            for operation in result.operations_applied:
                st.write(f"• {operation}")
        
        # Warnings
        if result.warnings:
            st.subheader("⚠️ Warnings")
            for warning in result.warnings:
                st.warning(warning)
    
    else:
        st.error("❌ Media processing failed!")
        
        if result.errors:
            st.subheader("💥 Errors")
            for error in result.errors:
                st.error(error)


if __name__ == "__main__":
    main()