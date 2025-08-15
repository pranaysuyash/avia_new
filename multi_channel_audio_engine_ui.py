"""
Multi-Channel Audio Engine UI

Streamlit interface for the multi-channel audio processing engine,
providing controls for channel routing, real-time monitoring, and
high-resolution audio processing.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json
from typing import Dict, List, Any, Optional

from multi_channel_audio_engine import (
    MultiChannelAudioEngine, MultiChannelAudio, AudioChannel, RoutingMatrix,
    ProcessingConfig, LatencyRequirements, AudioFormat, ChannelLayout, 
    ProcessingMode, HighResolutionAudioProcessor, RealTimeMonitor,
    SpatialMetadata
)

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'engine' not in st.session_state:
        st.session_state.engine = MultiChannelAudioEngine(max_channels=32)
    
    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
    
    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False
    
    if 'routing_matrices' not in st.session_state:
        st.session_state.routing_matrices = {}
    
    if 'performance_history' not in st.session_state:
        st.session_state.performance_history = []

def create_test_audio(channels: int, sample_rate: int, duration: float, 
                     signal_type: str = "sine") -> MultiChannelAudio:
    """Create test audio for demonstration"""
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)
    
    channel_data = []
    for i in range(channels):
        if signal_type == "sine":
            frequency = 440 * (2 ** (i / 12))  # Musical intervals
            signal = np.sin(2 * np.pi * frequency * t) * 0.3
        elif signal_type == "noise":
            signal = np.random.normal(0, 0.1, samples)
        elif signal_type == "sweep":
            f_start = 20 + i * 100
            f_end = f_start + 1000
            signal = np.sin(2 * np.pi * (f_start + (f_end - f_start) * t / duration) * t) * 0.3
        else:
            signal = np.zeros(samples)
        
        channel_data.append(signal)
    
    return st.session_state.engine.create_multichannel_audio(
        channel_data, sample_rate, bit_depth=32,
        format=AudioFormat.FLOAT_32, layout=ChannelLayout.CUSTOM
    )

def render_channel_controls(audio: MultiChannelAudio) -> MultiChannelAudio:
    """Render individual channel controls"""
    st.subheader("Channel Controls")
    
    modified_channels = []
    cols = st.columns(min(4, audio.channel_count))
    
    for i, channel in enumerate(audio.channels):
        with cols[i % 4]:
            st.write(f"**Channel {channel.channel_id + 1}**")
            
            # Gain control
            gain = st.slider(
                f"Gain", 
                min_value=0.0, max_value=2.0, value=channel.gain, step=0.1,
                key=f"gain_{channel.channel_id}"
            )
            
            # Mute/Solo controls
            col1, col2 = st.columns(2)
            with col1:
                muted = st.checkbox("Mute", value=channel.muted, key=f"mute_{channel.channel_id}")
            with col2:
                solo = st.checkbox("Solo", value=channel.solo, key=f"solo_{channel.channel_id}")
            
            # Pan control
            pan = st.slider(
                "Pan", 
                min_value=-1.0, max_value=1.0, value=channel.pan, step=0.1,
                key=f"pan_{channel.channel_id}"
            )
            
            # Create modified channel
            modified_channel = AudioChannel(
                channel_id=channel.channel_id,
                data=channel.data,
                sample_rate=channel.sample_rate,
                bit_depth=channel.bit_depth,
                gain=gain,
                muted=muted,
                solo=solo,
                pan=pan
            )
            modified_channels.append(modified_channel)
    
    # Return modified audio
    return MultiChannelAudio(
        channels=modified_channels,
        sample_rate=audio.sample_rate,
        bit_depth=audio.bit_depth,
        format=audio.format,
        channel_layout=audio.channel_layout,
        spatial_metadata=audio.spatial_metadata,
        processing_history=audio.processing_history
    )

def render_routing_matrix_editor():
    """Render routing matrix editor"""
    st.subheader("Channel Routing Matrix")
    
    if st.session_state.current_audio is None:
        st.warning("Load audio first to configure routing")
        return
    
    audio = st.session_state.current_audio
    
    # Matrix configuration
    col1, col2 = st.columns(2)
    with col1:
        matrix_name = st.text_input("Matrix Name", value="default")
        input_channels = st.multiselect(
            "Input Channels",
            options=list(range(audio.channel_count)),
            default=list(range(audio.channel_count)),
            format_func=lambda x: f"Channel {x + 1}"
        )
    
    with col2:
        output_channels = st.number_input("Output Channels", min_value=1, max_value=32, value=2)
        output_channel_list = list(range(int(output_channels)))
    
    # Create routing matrix
    if st.button("Create Routing Matrix"):
        router = st.session_state.engine.channel_router
        matrix = router.create_routing_matrix(matrix_name, input_channels, output_channel_list)
        st.session_state.routing_matrices[matrix_name] = matrix
        st.success(f"Created routing matrix: {matrix_name}")
    
    # Display existing matrices
    if st.session_state.routing_matrices:
        selected_matrix = st.selectbox(
            "Select Matrix to Edit",
            options=list(st.session_state.routing_matrices.keys())
        )
        
        if selected_matrix:
            matrix = st.session_state.routing_matrices[selected_matrix]
            
            # Routing configuration
            st.write("**Routing Configuration**")
            routing_data = []
            
            for input_ch in matrix.input_channels:
                for output_ch in matrix.output_channels:
                    key = f"route_{input_ch}_{output_ch}"
                    current_gain = 0.0
                    
                    # Check if route exists
                    if input_ch in matrix.routing_map:
                        for out_ch, gain in matrix.routing_map[input_ch]:
                            if out_ch == output_ch:
                                current_gain = gain
                                break
                    
                    gain = st.slider(
                        f"Input {input_ch + 1} → Output {output_ch + 1}",
                        min_value=0.0, max_value=1.0, value=current_gain, step=0.1,
                        key=key
                    )
                    
                    if gain > 0:
                        routing_data.append({
                            'Input': input_ch + 1,
                            'Output': output_ch + 1,
                            'Gain': gain
                        })
                        
                        # Update matrix
                        if input_ch not in matrix.routing_map:
                            matrix.routing_map[input_ch] = []
                        
                        # Remove existing route
                        matrix.routing_map[input_ch] = [
                            (out, g) for out, g in matrix.routing_map[input_ch] 
                            if out != output_ch
                        ]
                        
                        # Add new route
                        if gain > 0:
                            matrix.routing_map[input_ch].append((output_ch, gain))
            
            # Display routing table
            if routing_data:
                df = pd.DataFrame(routing_data)
                st.dataframe(df)

def render_processing_controls():
    """Render audio processing controls"""
    st.subheader("Processing Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        processing_mode = st.selectbox(
            "Processing Mode",
            options=[mode.value for mode in ProcessingMode],
            index=0
        )
        
        buffer_size = st.selectbox(
            "Buffer Size (samples)",
            options=[64, 128, 256, 512, 1024],
            index=2
        )
        
        max_latency = st.slider(
            "Max Latency (ms)",
            min_value=1.0, max_value=50.0, value=10.0, step=1.0
        )
    
    with col2:
        thread_count = st.slider(
            "Thread Count",
            min_value=1, max_value=8, value=4
        )
        
        enable_monitoring = st.checkbox("Enable Monitoring", value=True)
        
        quality_priority = st.checkbox("Quality Priority", value=False)
    
    config = ProcessingConfig(
        mode=ProcessingMode(processing_mode),
        buffer_size=buffer_size,
        max_latency_ms=max_latency,
        enable_monitoring=enable_monitoring,
        thread_count=thread_count,
        quality_priority=quality_priority
    )
    
    return config

def render_latency_optimization():
    """Render latency optimization controls"""
    st.subheader("Latency Optimization")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_input_latency = st.slider(
            "Max Input Latency (ms)",
            min_value=0.1, max_value=10.0, value=5.0, step=0.1
        )
        
        max_processing_latency = st.slider(
            "Max Processing Latency (ms)",
            min_value=0.1, max_value=10.0, value=3.0, step=0.1
        )
    
    with col2:
        max_output_latency = st.slider(
            "Max Output Latency (ms)",
            min_value=0.1, max_value=10.0, value=2.0, step=0.1
        )
        
        jitter_tolerance = st.slider(
            "Jitter Tolerance (ms)",
            min_value=0.1, max_value=5.0, value=1.0, step=0.1
        )
    
    max_total_latency = max_input_latency + max_processing_latency + max_output_latency
    st.metric("Total Max Latency", f"{max_total_latency:.1f} ms")
    
    requirements = LatencyRequirements(
        max_input_latency_ms=max_input_latency,
        max_processing_latency_ms=max_processing_latency,
        max_output_latency_ms=max_output_latency,
        max_total_latency_ms=max_total_latency,
        jitter_tolerance_ms=jitter_tolerance
    )
    
    return requirements

def render_spatial_audio_controls():
    """Render spatial audio controls"""
    st.subheader("Spatial Audio Configuration")
    
    if st.session_state.current_audio is None:
        st.warning("Load audio first to configure spatial processing")
        return {}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        position_x = st.slider("Position X", -10.0, 10.0, 0.0, 0.1)
        position_y = st.slider("Position Y", -10.0, 10.0, 0.0, 0.1)
        position_z = st.slider("Position Z", -10.0, 10.0, 0.0, 0.1)
    
    with col2:
        orientation_azimuth = st.slider("Azimuth (°)", -180.0, 180.0, 0.0, 1.0)
        orientation_elevation = st.slider("Elevation (°)", -90.0, 90.0, 0.0, 1.0)
        distance = st.slider("Distance", 0.1, 100.0, 1.0, 0.1)
    
    with col3:
        room_size = st.slider("Room Size", 0.1, 10.0, 1.0, 0.1)
        reverb_level = st.slider("Reverb Level", 0.0, 1.0, 0.0, 0.05)
    
    spatial_config = {
        'position_x': position_x,
        'position_y': position_y,
        'position_z': position_z,
        'orientation_azimuth': orientation_azimuth,
        'orientation_elevation': orientation_elevation,
        'distance': distance,
        'room_size': room_size,
        'reverb_level': reverb_level
    }
    
    return spatial_config

def render_audio_visualization(audio: MultiChannelAudio):
    """Render audio waveform and spectrum visualization"""
    st.subheader("Audio Visualization")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["Waveforms", "Spectrum", "Levels"])
    
    with tab1:
        # Waveform visualization
        fig = make_subplots(
            rows=min(4, audio.channel_count), cols=1,
            subplot_titles=[f"Channel {i+1}" for i in range(min(4, audio.channel_count))],
            vertical_spacing=0.05
        )
        
        for i, channel in enumerate(audio.channels[:4]):  # Show first 4 channels
            time_axis = np.linspace(0, len(channel.data) / channel.sample_rate, len(channel.data))
            
            fig.add_trace(
                go.Scatter(
                    x=time_axis,
                    y=channel.data,
                    name=f"Channel {channel.channel_id + 1}",
                    line=dict(width=1)
                ),
                row=i+1, col=1
            )
        
        fig.update_layout(height=600, showlegend=False)
        fig.update_xaxes(title_text="Time (s)")
        fig.update_yaxes(title_text="Amplitude")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Spectrum visualization
        monitor = RealTimeMonitor(audio.sample_rate)
        spectra = monitor.analyze_frequency_spectrum(audio)
        
        fig = go.Figure()
        
        for ch_id, spectrum in spectra.items():
            freqs = np.fft.rfftfreq(len(audio.channels[ch_id].data), 1/audio.sample_rate)
            
            fig.add_trace(
                go.Scatter(
                    x=freqs,
                    y=spectrum,
                    name=f"Channel {ch_id + 1}",
                    line=dict(width=2)
                )
            )
        
        fig.update_layout(
            title="Frequency Spectrum",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude (dB)",
            xaxis_type="log",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Level meters
        monitor = RealTimeMonitor(audio.sample_rate)
        levels = monitor.get_current_levels(audio)
        
        # Create level meter visualization
        level_data = []
        for ch_id, level_info in levels.items():
            level_data.append({
                'Channel': f"Ch {ch_id + 1}",
                'Peak (dB)': level_info['peak_db'],
                'RMS (dB)': level_info['rms_db'],
                'Clipping': level_info['clipping']
            })
        
        df = pd.DataFrame(level_data)
        
        # Peak levels bar chart
        fig_peak = px.bar(
            df, x='Channel', y='Peak (dB)',
            title="Peak Levels",
            color='Clipping',
            color_discrete_map={True: 'red', False: 'green'}
        )
        fig_peak.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="0 dB")
        fig_peak.add_hline(y=-6, line_dash="dash", line_color="orange", annotation_text="-6 dB")
        st.plotly_chart(fig_peak, use_container_width=True)
        
        # RMS levels bar chart
        fig_rms = px.bar(df, x='Channel', y='RMS (dB)', title="RMS Levels")
        fig_rms.add_hline(y=-12, line_dash="dash", line_color="green", annotation_text="-12 dB")
        st.plotly_chart(fig_rms, use_container_width=True)
        
        # Level table
        st.dataframe(df)

def render_performance_monitoring():
    """Render performance monitoring dashboard"""
    st.subheader("Performance Monitoring")
    
    stats = st.session_state.engine.get_performance_stats()
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Processed Samples", f"{stats['processed_samples']:,}")
    
    with col2:
        st.metric("Processing Time", f"{stats['processing_time_ms']:.2f} ms")
    
    with col3:
        st.metric("Buffer Underruns", stats['buffer_underruns'])
    
    with col4:
        st.metric("Buffer Overruns", stats['buffer_overruns'])
    
    # Add current stats to history
    if stats['processed_samples'] > 0:
        current_time = time.time()
        st.session_state.performance_history.append({
            'timestamp': current_time,
            'processing_time_ms': stats['processing_time_ms'],
            'processed_samples': stats['processed_samples']
        })
        
        # Keep only last 100 entries
        if len(st.session_state.performance_history) > 100:
            st.session_state.performance_history = st.session_state.performance_history[-100:]
    
    # Performance history chart
    if st.session_state.performance_history:
        df_history = pd.DataFrame(st.session_state.performance_history)
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], unit='s')
        
        fig = px.line(
            df_history, x='timestamp', y='processing_time_ms',
            title="Processing Time History"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Reset stats button
    if st.button("Reset Performance Stats"):
        st.session_state.engine.reset_performance_stats()
        st.session_state.performance_history = []
        st.success("Performance stats reset")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Multi-Channel Audio Engine",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Multi-Channel Audio Processing Engine")
    st.markdown("Professional multi-channel audio processing with real-time monitoring and ultra-low latency")
    
    initialize_session_state()
    
    # Sidebar controls
    with st.sidebar:
        st.header("Audio Source")
        
        # Audio generation options
        audio_source = st.radio(
            "Audio Source",
            options=["Generate Test Audio", "Upload Audio File"]
        )
        
        if audio_source == "Generate Test Audio":
            channels = st.slider("Channels", 1, 16, 8)
            sample_rate = st.selectbox("Sample Rate", [44100, 48000, 96000, 192000], index=1)
            duration = st.slider("Duration (s)", 0.5, 10.0, 2.0, 0.5)
            signal_type = st.selectbox("Signal Type", ["sine", "noise", "sweep"])
            
            if st.button("Generate Audio"):
                with st.spinner("Generating audio..."):
                    st.session_state.current_audio = create_test_audio(
                        channels, sample_rate, duration, signal_type
                    )
                st.success(f"Generated {channels}-channel audio")
        
        else:
            uploaded_file = st.file_uploader(
                "Upload Audio File",
                type=['wav', 'mp3', 'flac', 'aiff']
            )
            
            if uploaded_file is not None:
                st.warning("Audio file upload not implemented in this demo")
        
        st.divider()
        
        # High-resolution audio controls
        st.header("High-Resolution Audio")
        
        if st.session_state.current_audio is not None:
            current_sr = st.session_state.current_audio.sample_rate
            current_bd = st.session_state.current_audio.bit_depth
            
            st.write(f"Current: {current_sr}Hz/{current_bd}-bit")
            
            target_sr = st.selectbox("Target Sample Rate", [48000, 96000, 192000], 
                                   index=2 if current_sr < 192000 else 0)
            target_bd = st.selectbox("Target Bit Depth", [24, 32], index=1)
            
            if st.button("Convert to High-Resolution"):
                with st.spinner("Converting to high-resolution..."):
                    hr_processor = HighResolutionAudioProcessor()
                    st.session_state.current_audio = hr_processor.convert_to_high_res(
                        st.session_state.current_audio, target_sr, target_bd
                    )
                st.success(f"Converted to {target_sr}Hz/{target_bd}-bit")
    
    # Main content area
    if st.session_state.current_audio is None:
        st.info("👈 Generate or upload audio to begin processing")
        return
    
    audio = st.session_state.current_audio
    
    # Audio info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Channels", audio.channel_count)
    with col2:
        st.metric("Sample Rate", f"{audio.sample_rate} Hz")
    with col3:
        st.metric("Bit Depth", f"{audio.bit_depth}-bit")
    with col4:
        st.metric("Duration", f"{audio.duration:.2f} s")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Channel Controls", "Routing Matrix", "Processing", "Spatial Audio", "Monitoring"
    ])
    
    with tab1:
        # Channel controls and visualization
        modified_audio = render_channel_controls(audio)
        st.session_state.current_audio = modified_audio
        
        if st.button("Apply Channel Changes"):
            st.success("Channel changes applied")
        
        # Audio visualization
        render_audio_visualization(modified_audio)
    
    with tab2:
        render_routing_matrix_editor()
        
        # Apply routing
        if st.session_state.routing_matrices:
            selected_matrix = st.selectbox(
                "Apply Routing Matrix",
                options=list(st.session_state.routing_matrices.keys())
            )
            
            if st.button("Apply Routing"):
                with st.spinner("Applying routing..."):
                    router = st.session_state.engine.channel_router
                    router.routing_matrices["default"] = st.session_state.routing_matrices[selected_matrix]
                    routed_audio = router.route_audio(st.session_state.current_audio, "default")
                    st.session_state.current_audio = routed_audio
                st.success("Routing applied")
    
    with tab3:
        config = render_processing_controls()
        latency_req = render_latency_optimization()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Process Audio"):
                with st.spinner("Processing audio..."):
                    processed_audio = st.session_state.engine.process_multichannel_audio(
                        st.session_state.current_audio, config
                    )
                    st.session_state.current_audio = processed_audio
                st.success("Audio processed")
        
        with col2:
            if st.button("Optimize for Latency"):
                with st.spinner("Optimizing latency..."):
                    optimized_stream = st.session_state.engine.optimize_latency(
                        st.session_state.current_audio, latency_req
                    )
                    st.success(f"Optimized with buffer size: {optimized_stream.buffer_size}")
    
    with tab4:
        spatial_config = render_spatial_audio_controls()
        
        if st.button("Apply Spatial Processing"):
            with st.spinner("Applying spatial processing..."):
                spatial_audio = st.session_state.engine.handle_spatial_audio(
                    st.session_state.current_audio, spatial_config
                )
                st.session_state.current_audio = spatial_audio
            st.success("Spatial processing applied")
        
        # 3D position visualization
        if spatial_config:
            fig = go.Figure(data=[go.Scatter3d(
                x=[spatial_config['position_x']],
                y=[spatial_config['position_y']],
                z=[spatial_config['position_z']],
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Audio Source'
            )])
            
            fig.update_layout(
                title="3D Audio Position",
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z"
                ),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        render_performance_monitoring()
        
        # Processing history
        if audio.processing_history.operations:
            st.subheader("Processing History")
            
            history_data = []
            for op in audio.processing_history.operations:
                history_data.append({
                    'Operation': op['operation'],
                    'Timestamp': pd.to_datetime(op['timestamp'], unit='s'),
                    'Parameters': json.dumps(op['parameters'], indent=2)
                })
            
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history)

if __name__ == "__main__":
    main()