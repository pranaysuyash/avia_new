"""
Spatial Audio Processor UI
Streamlit interface for spatial audio processing and format conversion

Requirements: 1.2, 1.5
Dependencies: spatial_audio_processor.py
"""

import streamlit as st
import asyncio
import os
import tempfile
import json
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional
import logging

try:
    from spatial_audio_processor import (
        SpatialAudioProcessor, SpatialFormat, SpatialProcessingMode,
        AmbisonicsOrder, SpatialPosition
    )
    SPATIAL_PROCESSOR_AVAILABLE = True
except ImportError:
    SPATIAL_PROCESSOR_AVAILABLE = False
    st.error("Spatial Audio Processor not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Spatial Audio Processor",
        page_icon="🎧",
        layout="wide"
    )
    
    st.title("🎧 Professional Spatial Audio Processor")
    st.markdown("Advanced spatial audio processing with format conversion and enhancement")
    
    if not SPATIAL_PROCESSOR_AVAILABLE:
        st.error("Spatial Audio Processor is not available. Please check dependencies.")
        return
    
    # Initialize session state
    if 'processor' not in st.session_state:
        st.session_state.processor = SpatialAudioProcessor()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a function",
        [
            "Format Detection & Analysis",
            "Format Conversion",
            "Spatial Enhancement",
            "Visualization",
            "Batch Processing"
        ]
    )
    
    if page == "Format Detection & Analysis":
        format_detection_page()
    elif page == "Format Conversion":
        format_conversion_page()
    elif page == "Spatial Enhancement":
        spatial_enhancement_page()
    elif page == "Visualization":
        visualization_page()
    elif page == "Batch Processing":
        batch_processing_page()


def format_detection_page():
    """Format detection and analysis page"""
    st.header("🔍 Spatial Format Detection & Analysis")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for analysis",
        type=['wav', 'flac', 'aiff', 'mp3', 'm4a'],
        help="Upload a spatial audio file to analyze its format and properties"
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
                
                if st.button("Analyze Audio Format", type="primary"):
                    with st.spinner("Analyzing spatial format..."):
                        # Run async function
                        format_result = asyncio.run(
                            st.session_state.processor.detect_spatial_format(temp_path)
                        )
                        
                        st.success(f"Detected Format: **{format_result.value.upper()}**")
                        
                        # Display format information
                        format_info = get_format_info(format_result)
                        st.info(format_info)
            
            with col2:
                st.subheader("Spatial Analysis")
                
                if st.button("Perform Spatial Analysis"):
                    with st.spinner("Analyzing spatial properties..."):
                        analysis = asyncio.run(
                            st.session_state.processor.analyze_spatial_properties(temp_path)
                        )
                        
                        # Display analysis results
                        display_spatial_analysis(analysis)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def format_conversion_page():
    """Format conversion page"""
    st.header("🔄 Spatial Format Conversion")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for conversion",
        type=['wav', 'flac', 'aiff'],
        help="Upload a spatial audio file to convert to another format"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Source Format")
                
                # Detect source format
                if st.button("Detect Source Format"):
                    with st.spinner("Detecting format..."):
                        source_format = asyncio.run(
                            st.session_state.processor.detect_spatial_format(temp_path)
                        )
                        st.session_state.source_format = source_format
                        st.success(f"Source: {source_format.value.upper()}")
            
            with col2:
                st.subheader("Target Format")
                
                # Target format selection
                target_format_options = {
                    "Stereo": SpatialFormat.STEREO,
                    "5.1 Surround": SpatialFormat.SURROUND_5_1,
                    "7.1 Surround": SpatialFormat.SURROUND_7_1,
                    "Ambisonics FOA": SpatialFormat.AMBISONICS_FOA,
                    "Binaural": SpatialFormat.BINAURAL,
                    "Quad": SpatialFormat.QUAD
                }
                
                selected_target = st.selectbox(
                    "Select target format",
                    list(target_format_options.keys())
                )
                target_format = target_format_options[selected_target]
            
            st.subheader("Conversion Settings")
            
            col3, col4 = st.columns(2)
            with col3:
                preserve_dynamics = st.checkbox("Preserve Dynamics", value=True)
                normalize_levels = st.checkbox("Normalize Levels", value=False)
            
            with col4:
                quality_mode = st.selectbox(
                    "Quality Mode",
                    ["Standard", "High Quality", "Broadcast"]
                )
            
            if st.button("Convert Format", type="primary"):
                with st.spinner(f"Converting to {selected_target}..."):
                    try:
                        converted_path = asyncio.run(
                            st.session_state.processor.convert_spatial_format(
                                temp_path, target_format
                            )
                        )
                        
                        st.success("Conversion completed!")
                        
                        # Provide download link
                        with open(converted_path, 'rb') as f:
                            st.download_button(
                                label=f"Download {selected_target} Audio",
                                data=f.read(),
                                file_name=f"converted_{selected_target.lower().replace(' ', '_')}.wav",
                                mime="audio/wav"
                            )
                        
                        # Clean up converted file
                        os.unlink(converted_path)
                        
                    except Exception as e:
                        st.error(f"Conversion failed: {str(e)}")
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def spatial_enhancement_page():
    """Spatial enhancement page"""
    st.header("✨ Spatial Audio Enhancement")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for enhancement",
        type=['wav', 'flac', 'aiff'],
        help="Upload a spatial audio file to enhance its spatial properties"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            st.subheader("Enhancement Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Spatial Dimensions**")
                width_enhancement = st.checkbox("Width Enhancement", help="Enhance stereo width")
                depth_enhancement = st.checkbox("Depth Enhancement", help="Enhance front-back dimension")
                height_enhancement = st.checkbox("Height Enhancement", help="Enhance vertical dimension")
            
            with col2:
                st.markdown("**Perceptual Enhancement**")
                immersion_boost = st.checkbox("Immersion Boost", help="Increase spatial immersion")
                localization_improvement = st.checkbox("Localization Improvement", help="Improve source localization")
                clarity_enhancement = st.checkbox("Clarity Enhancement", help="Enhance spatial clarity")
            
            with col3:
                st.markdown("**Processing Options**")
                real_time_mode = st.checkbox("Real-time Mode", help="Optimize for real-time processing")
                preserve_original = st.checkbox("Preserve Original Character", value=True)
                
                enhancement_strength = st.slider(
                    "Enhancement Strength",
                    min_value=0.1,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    help="Overall enhancement intensity"
                )
            
            # Advanced settings
            with st.expander("Advanced Settings"):
                col4, col5 = st.columns(2)
                
                with col4:
                    room_simulation = st.selectbox(
                        "Room Simulation",
                        ["None", "Small Room", "Medium Room", "Large Hall", "Cathedral"]
                    )
                    
                    crossfeed_amount = st.slider(
                        "Crossfeed Amount (for headphones)",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.3,
                        step=0.1
                    )
                
                with col5:
                    bass_management = st.checkbox("Bass Management")
                    phase_correction = st.checkbox("Phase Correction")
                    
                    output_format = st.selectbox(
                        "Output Format",
                        ["Same as Input", "Stereo", "5.1", "7.1", "Binaural"]
                    )
            
            if st.button("Apply Enhancements", type="primary"):
                # Create enhancement configuration
                enhancement_config = {
                    'width_enhancement': width_enhancement,
                    'depth_enhancement': depth_enhancement,
                    'height_enhancement': height_enhancement,
                    'immersion_boost': immersion_boost,
                    'localization_improvement': localization_improvement,
                    'clarity_enhancement': clarity_enhancement,
                    'enhancement_strength': enhancement_strength,
                    'room_simulation': room_simulation.lower().replace(' ', '_'),
                    'crossfeed_amount': crossfeed_amount,
                    'bass_management': bass_management,
                    'phase_correction': phase_correction,
                    'preserve_original': preserve_original,
                    'real_time_mode': real_time_mode
                }
                
                with st.spinner("Applying spatial enhancements..."):
                    try:
                        enhanced_path = asyncio.run(
                            st.session_state.processor.enhance_spatial_audio(
                                temp_path, enhancement_config
                            )
                        )
                        
                        st.success("Enhancement completed!")
                        
                        # Provide download link
                        with open(enhanced_path, 'rb') as f:
                            st.download_button(
                                label="Download Enhanced Audio",
                                data=f.read(),
                                file_name="enhanced_spatial_audio.wav",
                                mime="audio/wav"
                            )
                        
                        # Show before/after analysis
                        show_enhancement_comparison(temp_path, enhanced_path)
                        
                        # Clean up enhanced file
                        os.unlink(enhanced_path)
                        
                    except Exception as e:
                        st.error(f"Enhancement failed: {str(e)}")
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def visualization_page():
    """Spatial visualization page"""
    st.header("📊 Spatial Audio Visualization")
    
    uploaded_file = st.file_uploader(
        "Upload audio file for visualization",
        type=['wav', 'flac', 'aiff'],
        help="Upload a spatial audio file to visualize its spatial properties"
    )
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_path = tmp_file.name
        
        try:
            if st.button("Generate Spatial Visualization", type="primary"):
                with st.spinner("Creating spatial visualization..."):
                    # Generate visualization data
                    viz_path = asyncio.run(
                        st.session_state.processor.create_spatial_visualization(temp_path)
                    )
                    
                    # Load and display visualization
                    with open(viz_path, 'r') as f:
                        viz_data = json.load(f)
                    
                    display_spatial_visualization(viz_data)
                    
                    # Clean up visualization file
                    os.unlink(viz_path)
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


def batch_processing_page():
    """Batch processing page"""
    st.header("⚡ Batch Spatial Processing")
    
    st.markdown("Process multiple spatial audio files simultaneously")
    
    uploaded_files = st.file_uploader(
        "Upload multiple audio files",
        type=['wav', 'flac', 'aiff'],
        accept_multiple_files=True,
        help="Upload multiple spatial audio files for batch processing"
    )
    
    if uploaded_files:
        st.subheader("Batch Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            batch_operation = st.selectbox(
                "Batch Operation",
                [
                    "Format Detection",
                    "Format Conversion",
                    "Spatial Enhancement",
                    "Analysis Report"
                ]
            )
            
            if batch_operation == "Format Conversion":
                target_format_options = {
                    "Stereo": SpatialFormat.STEREO,
                    "5.1 Surround": SpatialFormat.SURROUND_5_1,
                    "7.1 Surround": SpatialFormat.SURROUND_7_1,
                    "Binaural": SpatialFormat.BINAURAL
                }
                
                batch_target_format = st.selectbox(
                    "Target Format",
                    list(target_format_options.keys())
                )
        
        with col2:
            parallel_processing = st.checkbox("Parallel Processing", value=True)
            progress_updates = st.checkbox("Show Progress Updates", value=True)
            
            if batch_operation == "Spatial Enhancement":
                batch_enhancement_preset = st.selectbox(
                    "Enhancement Preset",
                    ["Light Enhancement", "Standard Enhancement", "Maximum Enhancement"]
                )
        
        if st.button("Start Batch Processing", type="primary"):
            process_batch_files(
                uploaded_files, 
                batch_operation, 
                locals()
            )


def get_format_info(format: SpatialFormat) -> str:
    """Get information about a spatial format"""
    format_descriptions = {
        SpatialFormat.STEREO: "Standard stereo with left and right channels",
        SpatialFormat.SURROUND_5_1: "5.1 surround sound with 6 channels (FL, FR, C, LFE, RL, RR)",
        SpatialFormat.SURROUND_7_1: "7.1 surround sound with 8 channels (FL, FR, C, LFE, SL, SR, RL, RR)",
        SpatialFormat.AMBISONICS_FOA: "First Order Ambisonics with 4 channels (W, X, Y, Z)",
        SpatialFormat.AMBISONICS_HOA: "Higher Order Ambisonics with 9+ channels",
        SpatialFormat.BINAURAL: "Binaural audio optimized for headphone listening",
        SpatialFormat.QUAD: "Quadraphonic audio with 4 channels",
        SpatialFormat.DOLBY_ATMOS: "Object-based spatial audio format",
        SpatialFormat.DTS_X: "Object-based spatial audio format"
    }
    
    return format_descriptions.get(format, "Unknown spatial format")


def display_spatial_analysis(analysis):
    """Display spatial analysis results"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Spatial Dimensions")
        
        # Create radar chart for spatial dimensions
        dimensions = ['Width', 'Depth', 'Height']
        values = [analysis.spatial_width, analysis.spatial_depth, analysis.spatial_height]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=dimensions,
            fill='toself',
            name='Spatial Dimensions'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display numerical values
        st.metric("Spatial Width", f"{analysis.spatial_width:.2f}")
        st.metric("Spatial Depth", f"{analysis.spatial_depth:.2f}")
        st.metric("Spatial Height", f"{analysis.spatial_height:.2f}")
    
    with col2:
        st.subheader("Quality Metrics")
        
        # Quality metrics
        st.metric("Immersion Score", f"{analysis.immersion_score:.2f}")
        st.metric("Localization Accuracy", f"{analysis.localization_accuracy:.2f}")
        
        # Center of mass
        st.subheader("Spatial Center of Mass")
        st.write(f"X (L/R): {analysis.center_of_mass.x:.2f}")
        st.write(f"Y (F/B): {analysis.center_of_mass.y:.2f}")
        st.write(f"Z (U/D): {analysis.center_of_mass.z:.2f}")
        
        # Artifacts
        if analysis.spatial_artifacts:
            st.subheader("Detected Issues")
            for artifact in analysis.spatial_artifacts:
                st.warning(artifact)
        else:
            st.success("No spatial artifacts detected")
    
    # Channel correlation heatmap
    if analysis.spatial_correlation.size > 1:
        st.subheader("Channel Correlation Matrix")
        
        fig = px.imshow(
            analysis.spatial_correlation,
            color_continuous_scale='RdBu_r',
            aspect='auto',
            title="Inter-channel Correlation"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def display_spatial_visualization(viz_data: Dict[str, Any]):
    """Display spatial visualization"""
    st.subheader("Spatial Audio Visualization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 3D spatial representation
        st.subheader("3D Spatial Representation")
        
        center = viz_data['center_of_mass']
        
        fig = go.Figure(data=[go.Scatter3d(
            x=[center['x']],
            y=[center['y']],
            z=[center['z']],
            mode='markers',
            marker=dict(
                size=12,
                color='red',
                symbol='circle'
            ),
            name='Center of Mass'
        )])
        
        fig.update_layout(
            scene=dict(
                xaxis_title='Left-Right',
                yaxis_title='Front-Back',
                zaxis_title='Up-Down',
                xaxis=dict(range=[-1, 1]),
                yaxis=dict(range=[-1, 1]),
                zaxis=dict(range=[-1, 1])
            ),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Spatial metrics
        st.subheader("Spatial Metrics")
        
        dimensions = viz_data['spatial_dimensions']
        metrics = viz_data['quality_metrics']
        
        # Create gauge charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Width', 'Depth', 'Immersion', 'Localization'),
            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                   [{'type': 'indicator'}, {'type': 'indicator'}]]
        )
        
        # Width gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=dimensions['width'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 1]},
                   'bar': {'color': "darkblue"},
                   'steps': [{'range': [0, 0.5], 'color': "lightgray"},
                            {'range': [0.5, 1], 'color': "gray"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                               'thickness': 0.75, 'value': 0.9}}
        ), row=1, col=1)
        
        # Depth gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=dimensions['depth'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 1]},
                   'bar': {'color': "darkgreen"}}
        ), row=1, col=2)
        
        # Immersion gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=metrics['immersion_score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 1]},
                   'bar': {'color': "darkorange"}}
        ), row=2, col=1)
        
        # Localization gauge
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=metrics['localization_accuracy'],
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 1]},
                   'bar': {'color': "darkred"}}
        ), row=2, col=2)
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Format information
    st.subheader("Format Information")
    col3, col4 = st.columns(2)
    
    with col3:
        st.write(f"**Detected Format:** {viz_data['format'].upper()}")
        st.write(f"**Analysis Time:** {viz_data['timestamp']}")
    
    with col4:
        if viz_data['artifacts']:
            st.subheader("Detected Issues")
            for artifact in viz_data['artifacts']:
                st.warning(artifact)
        else:
            st.success("No issues detected")


def show_enhancement_comparison(original_path: str, enhanced_path: str):
    """Show before/after enhancement comparison"""
    st.subheader("Enhancement Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Before Enhancement**")
        # Would show original analysis
        st.info("Original spatial properties")
    
    with col2:
        st.markdown("**After Enhancement**")
        # Would show enhanced analysis
        st.success("Enhanced spatial properties")


def process_batch_files(files, operation: str, config: Dict[str, Any]):
    """Process multiple files in batch"""
    st.subheader("Batch Processing Results")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, file in enumerate(files):
        status_text.text(f"Processing {file.name}...")
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(file.read())
            temp_path = tmp_file.name
        
        try:
            if operation == "Format Detection":
                result = asyncio.run(
                    st.session_state.processor.detect_spatial_format(temp_path)
                )
                results.append({
                    'file': file.name,
                    'format': result.value,
                    'status': 'Success'
                })
            
            elif operation == "Spatial Enhancement":
                # Use preset configuration
                preset_configs = {
                    "Light Enhancement": {
                        'width_enhancement': True,
                        'enhancement_strength': 0.5
                    },
                    "Standard Enhancement": {
                        'width_enhancement': True,
                        'depth_enhancement': True,
                        'enhancement_strength': 1.0
                    },
                    "Maximum Enhancement": {
                        'width_enhancement': True,
                        'depth_enhancement': True,
                        'height_enhancement': True,
                        'immersion_boost': True,
                        'enhancement_strength': 1.5
                    }
                }
                
                enhancement_config = preset_configs.get(
                    config.get('batch_enhancement_preset', 'Standard Enhancement'),
                    preset_configs['Standard Enhancement']
                )
                
                enhanced_path = asyncio.run(
                    st.session_state.processor.enhance_spatial_audio(
                        temp_path, enhancement_config
                    )
                )
                
                results.append({
                    'file': file.name,
                    'output': enhanced_path,
                    'status': 'Success'
                })
        
        except Exception as e:
            results.append({
                'file': file.name,
                'status': f'Error: {str(e)}'
            })
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # Update progress
        progress_bar.progress((i + 1) / len(files))
    
    status_text.text("Batch processing completed!")
    
    # Display results
    st.subheader("Processing Results")
    for result in results:
        if result['status'] == 'Success':
            st.success(f"✅ {result['file']}: {result.get('format', 'Processed')}")
        else:
            st.error(f"❌ {result['file']}: {result['status']}")


if __name__ == "__main__":
    main()