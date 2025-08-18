"""
Professional Audio Format Handler UI
Streamlit interface for audio format handling and conversion

Requirements: 1.3
Dependencies: professional_audio_format_handler.py
"""

import streamlit as st
import asyncio
import os
import tempfile
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

try:
    from professional_audio_format_handler import (
        ProfessionalAudioFormatHandler, AudioFormat, AudioCodec,
        QualityLevel, ConversionMode, ConversionSettings,
        BatchProcessingJob, AudioMetadata
    )
    FORMAT_HANDLER_AVAILABLE = True
except ImportError:
    FORMAT_HANDLER_AVAILABLE = False
    st.error("Professional Audio Format Handler not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Professional Audio Format Handler",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Professional Audio Format Handler")
    st.markdown("Comprehensive audio format conversion with professional codec support")
    
    if not FORMAT_HANDLER_AVAILABLE:
        st.error("Professional Audio Format Handler is not available. Please check dependencies.")
        return
    
    # Initialize session state
    if 'handler' not in st.session_state:
        st.session_state.handler = ProfessionalAudioFormatHandler()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a function",
        [
            "Format Detection & Analysis",
            "Single File Conversion", 
            "Batch Processing",
            "Format Information",
            "Quality Assessment",
            "Processing Statistics"
        ]
    )
    
    if page == "Format Detection & Analysis":
        format_detection_page()
    elif page == "Single File Conversion":
        single_conversion_page()
    elif page == "Batch Processing":
        batch_processing_page()
    elif page == "Format Information":
        format_info_page()
    elif page == "Quality Assessment":
        quality_assessment_page()
    elif page == "Processing Statistics":
        statistics_page()


def format_detection_page():
    """Format detection and analysis page"""
    st.header("🔍 Format Detection & Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for analysis",
        type=['wav', 'flac', 'aiff', 'mp3', 'm4a', 'aac', 'ogg', 'opus'],
        help="Upload an audio file to detect its format and analyze properties"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Format Detection")
                
                if st.button("Analyze Audio File", type="primary"):
                    with st.spinner("Analyzing audio format..."):
                        # Run async function
                        format_detected, metadata = asyncio.run(
                            st.session_state.handler.detect_format(temp_path)
                        )
                        
                        st.success(f"Detected Format: **{format_detected.value.upper()}**")
                        
                        # Display basic info
                        if metadata.duration:
                            st.metric("Duration", f"{metadata.duration:.2f} seconds")
                        if metadata.sample_rate:
                            st.metric("Sample Rate", f"{metadata.sample_rate} Hz")
                        if metadata.channels:
                            st.metric("Channels", metadata.channels)
                        if metadata.bit_depth:
                            st.metric("Bit Depth", f"{metadata.bit_depth} bits")
                        if metadata.bitrate:
                            st.metric("Bitrate", f"{metadata.bitrate} kbps")
            
            with col2:
                st.subheader("Metadata Information")
                
                if st.button("Extract Detailed Metadata"):
                    with st.spinner("Extracting metadata..."):
                        format_detected, metadata = asyncio.run(
                            st.session_state.handler.detect_format(temp_path)
                        )
                        
                        # Display metadata in organized sections
                        display_metadata(metadata)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def single_conversion_page():
    """Single file conversion page"""
    st.header("🔄 Single File Conversion")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for conversion",
        type=['wav', 'flac', 'aiff', 'mp3', 'm4a', 'aac', 'ogg', 'opus'],
        help="Upload an audio file to convert to another format"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            # Display source file info
            st.subheader("Source File Information")
            
            if st.button("Analyze Source File"):
                with st.spinner("Analyzing source file..."):
                    format_detected, metadata = asyncio.run(
                        st.session_state.handler.detect_format(temp_path)
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Format", format_detected.value.upper())
                        st.metric("Duration", f"{metadata.duration:.2f}s" if metadata.duration else "Unknown")
                    with col2:
                        st.metric("Sample Rate", f"{metadata.sample_rate} Hz" if metadata.sample_rate else "Unknown")
                        st.metric("Channels", metadata.channels if metadata.channels else "Unknown")
                    with col3:
                        st.metric("Bit Depth", f"{metadata.bit_depth} bits" if metadata.bit_depth else "Unknown")
                        st.metric("Bitrate", f"{metadata.bitrate} kbps" if metadata.bitrate else "Unknown")
            
            st.subheader("Conversion Settings")
            
            # Conversion settings form
            with st.form("conversion_settings"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Target Format**")
                    target_format = st.selectbox(
                        "Output Format",
                        options=[f.value for f in AudioFormat],
                        format_func=lambda x: x.upper()
                    )
                    
                    quality_level = st.selectbox(
                        "Quality Level",
                        options=[q.value for q in QualityLevel],
                        index=2,  # Default to HIGH
                        format_func=lambda x: x.replace('_', ' ').title()
                    )
                    
                    conversion_mode = st.selectbox(
                        "Conversion Mode",
                        options=[m.value for m in ConversionMode],
                        index=1,  # Default to BALANCED
                        format_func=lambda x: x.title()
                    )
                
                with col2:
                    st.markdown("**Audio Parameters**")
                    sample_rate = st.selectbox(
                        "Sample Rate (Hz)",
                        options=[None, 22050, 44100, 48000, 88200, 96000, 176400, 192000],
                        format_func=lambda x: "Keep Original" if x is None else f"{x} Hz"
                    )
                    
                    channels = st.selectbox(
                        "Channels",
                        options=[None, 1, 2, 6, 8],
                        format_func=lambda x: "Keep Original" if x is None else f"{x} Channel{'s' if x > 1 else ''}"
                    )
                    
                    bit_depth = st.selectbox(
                        "Bit Depth",
                        options=[None, 16, 24, 32],
                        format_func=lambda x: "Keep Original" if x is None else f"{x} bits"
                    )
                
                # Advanced settings
                with st.expander("Advanced Settings"):
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        bitrate = st.number_input(
                            "Bitrate (kbps)",
                            min_value=64,
                            max_value=320,
                            value=192,
                            step=32,
                            help="For lossy formats only"
                        )
                        
                        preserve_metadata = st.checkbox("Preserve Metadata", value=True)
                        normalize_audio = st.checkbox("Normalize Audio", value=False)
                    
                    with col4:
                        apply_dithering = st.checkbox("Apply Dithering", value=True)
                        
                        # Use case presets
                        use_case = st.selectbox(
                            "Use Case Preset",
                            options=["custom", "streaming", "podcast", "archival", "mobile", "broadcast", "web"],
                            format_func=lambda x: x.title()
                        )
                
                submitted = st.form_submit_button("Convert Audio", type="primary")
                
                if submitted:
                    # Create conversion settings
                    if use_case != "custom":
                        # Get recommended settings for use case
                        settings = asyncio.run(
                            st.session_state.handler.get_conversion_recommendations(temp_path, use_case)
                        )
                    else:
                        # Use custom settings
                        settings = ConversionSettings(
                            target_format=AudioFormat(target_format),
                            sample_rate=sample_rate,
                            channels=channels,
                            bit_depth=bit_depth,
                            bitrate=bitrate if AudioFormat(target_format) not in [AudioFormat.WAV, AudioFormat.FLAC] else None,
                            quality_level=QualityLevel(quality_level),
                            conversion_mode=ConversionMode(conversion_mode),
                            preserve_metadata=preserve_metadata,
                            normalize_audio=normalize_audio,
                            apply_dithering=apply_dithering
                        )
                    
                    # Perform conversion
                    with st.spinner("Converting audio..."):
                        output_file = tempfile.NamedTemporaryFile(
                            delete=False, 
                            suffix=f'.{target_format}'
                        ).name
                        
                        result = asyncio.run(
                            st.session_state.handler.convert_format(temp_path, output_file, settings)
                        )
                        
                        if result.success:
                            st.success("Conversion completed successfully!")
                            
                            # Display conversion results
                            display_conversion_results(result)
                            
                            # Provide download link
                            with open(output_file, 'rb') as f:
                                st.download_button(
                                    label=f"Download {target_format.upper()} File",
                                    data=f.read(),
                                    file_name=f"converted.{target_format}",
                                    mime=f"audio/{target_format}"
                                )
                            
                            # Clean up output file
                            os.unlink(output_file)
                        else:
                            st.error(f"Conversion failed: {result.error_message}")
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)def batch_
processing_page():
    """Batch processing page"""
    st.header("⚡ Batch Processing")
    
    st.markdown("Process multiple audio files simultaneously with the same settings")
    
    uploaded_files = st.file_uploader(
        "Upload multiple audio files",
        type=['wav', 'flac', 'aiff', 'mp3', 'm4a', 'aac', 'ogg', 'opus'],
        accept_multiple_files=True,
        help="Upload multiple audio files for batch conversion"
    )
    
    if uploaded_files:
        st.subheader(f"Selected Files ({len(uploaded_files)})")
        
        # Display file list
        file_data = []
        for file in uploaded_files:
            file_data.append({
                'Filename': file.name,
                'Size': f"{len(file.read()) / 1024 / 1024:.2f} MB"
            })
            file.seek(0)  # Reset file pointer
        
        st.dataframe(pd.DataFrame(file_data), use_container_width=True)
        
        # Batch conversion settings
        st.subheader("Batch Conversion Settings")
        
        with st.form("batch_settings"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                batch_target_format = st.selectbox(
                    "Target Format",
                    options=[f.value for f in AudioFormat],
                    format_func=lambda x: x.upper()
                )
                
                batch_quality = st.selectbox(
                    "Quality Level",
                    options=[q.value for q in QualityLevel],
                    index=2
                )
            
            with col2:
                batch_sample_rate = st.selectbox(
                    "Sample Rate",
                    options=[None, 44100, 48000, 96000],
                    format_func=lambda x: "Keep Original" if x is None else f"{x} Hz"
                )
                
                batch_channels = st.selectbox(
                    "Channels",
                    options=[None, 1, 2],
                    format_func=lambda x: "Keep Original" if x is None else f"{x} Channel{'s' if x > 1 else ''}"
                )
            
            with col3:
                parallel_workers = st.slider(
                    "Parallel Workers",
                    min_value=1,
                    max_value=8,
                    value=4,
                    help="Number of files to process simultaneously"
                )
                
                batch_normalize = st.checkbox("Normalize All Files", value=False)
            
            # Output directory
            output_dir_name = st.text_input(
                "Output Directory Name",
                value="converted_audio",
                help="Name for the output directory"
            )
            
            batch_submitted = st.form_submit_button("Start Batch Processing", type="primary")
            
            if batch_submitted:
                # Save uploaded files temporarily
                temp_files = []
                for file in uploaded_files:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix)
                    temp_file.write(file.read())
                    temp_file.close()
                    temp_files.append(temp_file.name)
                
                try:
                    # Create batch job
                    output_dir = tempfile.mkdtemp(prefix=output_dir_name + "_")
                    
                    batch_settings = ConversionSettings(
                        target_format=AudioFormat(batch_target_format),
                        sample_rate=batch_sample_rate,
                        channels=batch_channels,
                        quality_level=QualityLevel(batch_quality),
                        normalize_audio=batch_normalize,
                        preserve_metadata=True
                    )
                    
                    job = BatchProcessingJob(
                        job_id=f"batch_{len(uploaded_files)}_{batch_target_format}",
                        input_files=temp_files,
                        output_directory=output_dir,
                        conversion_settings=batch_settings,
                        parallel_workers=parallel_workers
                    )
                    
                    # Process batch with progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def progress_callback(progress, result):
                        progress_bar.progress(progress)
                        status_text.text(f"Processing: {result.input_file}")
                    
                    job.progress_callback = progress_callback
                    
                    with st.spinner("Processing batch..."):
                        completed_job = asyncio.run(
                            st.session_state.handler.batch_convert(job)
                        )
                    
                    # Display results
                    st.subheader("Batch Processing Results")
                    
                    successful = sum(1 for r in completed_job.results if r.success)
                    failed = len(completed_job.results) - successful
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Files", len(completed_job.results))
                    with col2:
                        st.metric("Successful", successful, delta=None)
                    with col3:
                        st.metric("Failed", failed, delta=None)
                    
                    # Detailed results
                    results_data = []
                    for result in completed_job.results:
                        results_data.append({
                            'File': Path(result.input_file).name,
                            'Status': '✅ Success' if result.success else '❌ Failed',
                            'Size Reduction': f"{result.compression_ratio:.2f}x" if result.compression_ratio else "N/A",
                            'Processing Time': f"{result.processing_time:.2f}s" if result.processing_time else "N/A",
                            'Error': result.error_message if result.error_message else ""
                        })
                    
                    st.dataframe(pd.DataFrame(results_data), use_container_width=True)
                    
                    # Create download archive
                    if successful > 0:
                        import zipfile
                        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip').name
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for result in completed_job.results:
                                if result.success and result.output_file:
                                    zipf.write(result.output_file, Path(result.output_file).name)
                        
                        with open(zip_path, 'rb') as f:
                            st.download_button(
                                label="Download All Converted Files (ZIP)",
                                data=f.read(),
                                file_name=f"batch_converted_{batch_target_format}.zip",
                                mime="application/zip"
                            )
                        
                        os.unlink(zip_path)
                
                finally:
                    # Clean up temporary files
                    for temp_file in temp_files:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)


def format_info_page():
    """Format information page"""
    st.header("📋 Format Information")
    
    st.markdown("Comprehensive information about supported audio formats")
    
    # Get supported formats
    supported_formats = asyncio.run(st.session_state.handler.get_supported_formats())
    
    # Format selection
    selected_format = st.selectbox(
        "Select Format for Details",
        options=[f.value for f in supported_formats],
        format_func=lambda x: x.upper()
    )
    
    if selected_format:
        format_enum = AudioFormat(selected_format)
        format_info = asyncio.run(st.session_state.handler.get_format_info(format_enum))
        
        if format_info:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Technical Specifications")
                st.write(f"**Codec:** {format_info.codec.value.upper()}")
                st.write(f"**Lossless:** {'Yes' if format_info.is_lossless else 'No'}")
                st.write(f"**Metadata Support:** {'Yes' if format_info.supports_metadata else 'No'}")
                st.write(f"**Multi-channel Support:** {'Yes' if format_info.supports_multichannel else 'No'}")
                
                st.subheader("Limitations")
                st.write(f"**Max Channels:** {format_info.max_channels}")
                st.write(f"**Max Sample Rate:** {format_info.max_sample_rate:,} Hz")
                st.write(f"**Max Bit Depth:** {format_info.max_bit_depth} bits")
            
            with col2:
                st.subheader("File Extensions")
                for ext in format_info.file_extensions:
                    st.code(ext)
                
                st.subheader("Typical Bitrates (kbps)")
                for bitrate in format_info.typical_bitrates:
                    st.write(f"• {bitrate} kbps")
                
                # Use case recommendations
                st.subheader("Recommended Use Cases")
                use_cases = get_format_use_cases(format_enum)
                for use_case in use_cases:
                    st.write(f"• {use_case}")
    
    # Format comparison table
    st.subheader("Format Comparison")
    
    comparison_data = []
    for format_enum in supported_formats:
        info = asyncio.run(st.session_state.handler.get_format_info(format_enum))
        if info:
            comparison_data.append({
                'Format': format_enum.value.upper(),
                'Codec': info.codec.value.upper(),
                'Lossless': '✅' if info.is_lossless else '❌',
                'Max Channels': info.max_channels,
                'Max Sample Rate': f"{info.max_sample_rate:,} Hz",
                'Metadata': '✅' if info.supports_metadata else '❌'
            })
    
    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)


def quality_assessment_page():
    """Quality assessment page"""
    st.header("🔍 Quality Assessment")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for quality assessment",
        type=['wav', 'flac', 'aiff', 'mp3', 'm4a', 'aac', 'ogg', 'opus'],
        help="Upload an audio file to assess its quality and get recommendations"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            if st.button("Assess Audio Quality", type="primary"):
                with st.spinner("Assessing audio quality..."):
                    # Validate audio file
                    validation_result = asyncio.run(
                        st.session_state.handler.validate_audio_file(temp_path)
                    )
                    
                    # Display validation results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Validation Results")
                        
                        if validation_result['is_valid']:
                            st.success("✅ Audio file is valid")
                        else:
                            st.error("❌ Audio file has issues")
                        
                        if validation_result['format_detected']:
                            st.info(f"Format: {validation_result['format_detected'].upper()}")
                        
                        # Display issues
                        if validation_result['issues']:
                            st.subheader("Issues Found")
                            for issue in validation_result['issues']:
                                st.warning(f"⚠️ {issue}")
                    
                    with col2:
                        st.subheader("Quality Metrics")
                        
                        metadata = validation_result.get('metadata')
                        if metadata:
                            if metadata.peak_level is not None:
                                st.metric("Peak Level", f"{metadata.peak_level:.3f}")
                            if metadata.rms_level is not None:
                                st.metric("RMS Level", f"{metadata.rms_level:.3f}")
                            if metadata.dynamic_range is not None:
                                st.metric("Dynamic Range", f"{metadata.dynamic_range:.1f} dB")
                            if metadata.lufs is not None:
                                st.metric("LUFS", f"{metadata.lufs:.1f}")
                        
                        # Display recommendations
                        if validation_result['recommendations']:
                            st.subheader("Recommendations")
                            for rec in validation_result['recommendations']:
                                st.info(f"💡 {rec}")
                    
                    # Quality score visualization
                    if metadata:
                        st.subheader("Quality Assessment")
                        
                        quality_score = calculate_quality_score(metadata)
                        
                        # Create quality gauge
                        import plotly.graph_objects as go
                        
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number+delta",
                            value = quality_score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Overall Quality Score"},
                            delta = {'reference': 80},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 50], 'color': "lightgray"},
                                    {'range': [50, 80], 'color': "gray"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 90
                                }
                            }
                        ))
                        
                        st.plotly_chart(fig, use_container_width=True)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def statistics_page():
    """Processing statistics page"""
    st.header("📊 Processing Statistics")
    
    # Get processing statistics
    stats = asyncio.run(st.session_state.handler.get_processing_statistics())
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Conversions", stats['total_conversions'])
    with col2:
        st.metric("Success Rate", f"{stats['success_rate']:.1%}")
    with col3:
        st.metric("Avg Processing Time", f"{stats['average_processing_time']:.2f}s")
    with col4:
        st.metric("Avg Compression Ratio", f"{stats['average_compression_ratio']:.2f}x")
    
    # Format processing breakdown
    if stats['formats_processed']:
        st.subheader("Format Processing Breakdown")
        
        format_data = []
        for format_combo, count in stats['formats_processed'].items():
            source, target = format_combo.split('_to_')
            format_data.append({
                'Source Format': source.upper(),
                'Target Format': target.upper(),
                'Count': count
            })
        
        st.dataframe(pd.DataFrame(format_data), use_container_width=True)
        
        # Visualization
        import plotly.express as px
        
        df = pd.DataFrame(format_data)
        fig = px.bar(df, x='Source Format', y='Count', color='Target Format',
                     title="Conversion Count by Format")
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance over time (if we had timestamps)
    st.subheader("Performance Summary")
    
    performance_data = {
        'Metric': ['Total Processing Time', 'Successful Conversions', 'Failed Conversions'],
        'Value': [
            f"{stats['total_processing_time']:.2f} seconds",
            stats['successful_conversions'],
            stats['failed_conversions']
        ]
    }
    
    st.table(pd.DataFrame(performance_data))


def display_metadata(metadata: AudioMetadata):
    """Display metadata in organized sections"""
    # Basic Information
    with st.expander("Basic Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            if metadata.title:
                st.write(f"**Title:** {metadata.title}")
            if metadata.artist:
                st.write(f"**Artist:** {metadata.artist}")
            if metadata.album:
                st.write(f"**Album:** {metadata.album}")
        with col2:
            if metadata.year:
                st.write(f"**Year:** {metadata.year}")
            if metadata.genre:
                st.write(f"**Genre:** {metadata.genre}")
            if metadata.track_number:
                track_info = str(metadata.track_number)
                if metadata.total_tracks:
                    track_info += f" of {metadata.total_tracks}"
                st.write(f"**Track:** {track_info}")
    
    # Technical Information
    with st.expander("Technical Information"):
        col1, col2 = st.columns(2)
        with col1:
            if metadata.duration:
                st.write(f"**Duration:** {metadata.duration:.2f} seconds")
            if metadata.sample_rate:
                st.write(f"**Sample Rate:** {metadata.sample_rate} Hz")
            if metadata.channels:
                st.write(f"**Channels:** {metadata.channels}")
        with col2:
            if metadata.bit_depth:
                st.write(f"**Bit Depth:** {metadata.bit_depth} bits")
            if metadata.bitrate:
                st.write(f"**Bitrate:** {metadata.bitrate} kbps")
            if metadata.codec:
                st.write(f"**Codec:** {metadata.codec}")
    
    # Quality Metrics
    if any([metadata.peak_level, metadata.rms_level, metadata.dynamic_range, metadata.lufs]):
        with st.expander("Quality Metrics"):
            col1, col2 = st.columns(2)
            with col1:
                if metadata.peak_level is not None:
                    st.write(f"**Peak Level:** {metadata.peak_level:.3f}")
                if metadata.rms_level is not None:
                    st.write(f"**RMS Level:** {metadata.rms_level:.3f}")
            with col2:
                if metadata.dynamic_range is not None:
                    st.write(f"**Dynamic Range:** {metadata.dynamic_range:.1f} dB")
                if metadata.lufs is not None:
                    st.write(f"**LUFS:** {metadata.lufs:.1f}")
    
    # Professional Information
    if any([metadata.engineer, metadata.producer, metadata.studio, metadata.isrc]):
        with st.expander("Professional Information"):
            if metadata.engineer:
                st.write(f"**Engineer:** {metadata.engineer}")
            if metadata.producer:
                st.write(f"**Producer:** {metadata.producer}")
            if metadata.studio:
                st.write(f"**Studio:** {metadata.studio}")
            if metadata.isrc:
                st.write(f"**ISRC:** {metadata.isrc}")


def display_conversion_results(result):
    """Display conversion results"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if result.original_size and result.converted_size:
            st.metric(
                "File Size", 
                f"{result.converted_size / 1024 / 1024:.2f} MB",
                delta=f"{(result.converted_size - result.original_size) / 1024 / 1024:.2f} MB"
            )
    
    with col2:
        if result.compression_ratio:
            st.metric("Compression Ratio", f"{result.compression_ratio:.2f}x")
    
    with col3:
        if result.processing_time:
            st.metric("Processing Time", f"{result.processing_time:.2f}s")
    
    # Quality metrics
    if result.quality_metrics:
        st.subheader("Quality Metrics")
        metrics_col1, metrics_col2 = st.columns(2)
        
        with metrics_col1:
            if 'snr_db' in result.quality_metrics:
                st.metric("SNR", f"{result.quality_metrics['snr_db']:.1f} dB")
            if 'correlation' in result.quality_metrics:
                st.metric("Correlation", f"{result.quality_metrics['correlation']:.3f}")
        
        with metrics_col2:
            if 'psnr_db' in result.quality_metrics:
                st.metric("PSNR", f"{result.quality_metrics['psnr_db']:.1f} dB")
            if 'rms_difference' in result.quality_metrics:
                st.metric("RMS Difference", f"{result.quality_metrics['rms_difference']:.4f}")
    
    # Warnings
    if result.warnings:
        st.subheader("Warnings")
        for warning in result.warnings:
            st.warning(warning)


def get_format_use_cases(format: AudioFormat) -> List[str]:
    """Get recommended use cases for a format"""
    use_cases = {
        AudioFormat.WAV: ["Professional recording", "Audio editing", "Mastering", "Broadcast"],
        AudioFormat.FLAC: ["Archival storage", "High-quality music", "Lossless distribution"],
        AudioFormat.MP3: ["Music streaming", "Podcasts", "Web audio", "Mobile devices"],
        AudioFormat.AAC: ["Streaming services", "Mobile apps", "Video soundtracks"],
        AudioFormat.OGG: ["Open-source projects", "Gaming", "Web streaming"],
        AudioFormat.OPUS: ["Voice calls", "Low-latency streaming", "Internet radio"],
        AudioFormat.AIFF: ["Mac-based workflows", "Professional audio", "Legacy systems"]
    }
    
    return use_cases.get(format, ["General audio use"])


def calculate_quality_score(metadata: AudioMetadata) -> float:
    """Calculate overall quality score from metadata"""
    score = 50  # Base score
    
    # Sample rate scoring
    if metadata.sample_rate:
        if metadata.sample_rate >= 96000:
            score += 20
        elif metadata.sample_rate >= 48000:
            score += 15
        elif metadata.sample_rate >= 44100:
            score += 10
        else:
            score += 5
    
    # Bit depth scoring
    if metadata.bit_depth:
        if metadata.bit_depth >= 24:
            score += 15
        elif metadata.bit_depth >= 16:
            score += 10
        else:
            score += 5
    
    # Dynamic range scoring
    if metadata.dynamic_range:
        if metadata.dynamic_range >= 20:
            score += 10
        elif metadata.dynamic_range >= 12:
            score += 5
        else:
            score -= 5
    
    # Peak level scoring (avoid clipping)
    if metadata.peak_level:
        if metadata.peak_level < 0.95:
            score += 5
        elif metadata.peak_level >= 1.0:
            score -= 10
    
    return min(100, max(0, score))


if __name__ == "__main__":
    main()