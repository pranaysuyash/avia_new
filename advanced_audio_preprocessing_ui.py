"""
Streamlit UI for Advanced Audio Preprocessing System

This module provides a comprehensive user interface for advanced audio preprocessing
including spectral analysis, pitch detection, audio fingerprinting, tempo analysis,
and audio similarity comparison and clustering.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import librosa
import librosa.display
from datetime import datetime
import tempfile
import os
import logging
from dataclasses import asdict

# Import the main preprocessing system
try:
    from advanced_audio_preprocessing import (
        AdvancedAudioPreprocessor, AudioFeatures
    )
except ImportError:
    st.error("Could not import advanced_audio_preprocessing module. Please ensure it's available.")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_session_state():
    """Initialize session state variables"""
    if 'preprocessor' not in st.session_state:
        st.session_state.preprocessor = AdvancedAudioPreprocessor()
    
    if 'extracted_features' not in st.session_state:
        st.session_state.extracted_features = None
    
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = None
    
    if 'similarity_results' not in st.session_state:
        st.session_state.similarity_results = []
    
    if 'clustering_results' not in st.session_state:
        st.session_state.clustering_results = []

def display_spectral_analysis(features: AudioFeatures):
    """Display spectral analysis results"""
    st.subheader("🌈 Spectral Analysis")
    
    if len(features.spectral_centroid) == 0:
        st.warning("No spectral features available")
        return
    
    # Create spectral features plot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Spectral Centroid', 'Spectral Bandwidth', 
                       'Spectral Rolloff', 'Spectral Flatness'],
        vertical_spacing=0.1
    )
    
    # Time axis
    time_frames = np.arange(len(features.spectral_centroid))
    time_seconds = librosa.frames_to_time(time_frames, sr=features.sample_rate)
    
    # Spectral centroid
    fig.add_trace(
        go.Scatter(x=time_seconds, y=features.spectral_centroid,
                  mode='lines', name='Spectral Centroid'),
        row=1, col=1
    )
    
    # Spectral bandwidth
    if len(features.spectral_bandwidth) > 0:
        fig.add_trace(
            go.Scatter(x=time_seconds, y=features.spectral_bandwidth,
                      mode='lines', name='Spectral Bandwidth'),
            row=1, col=2
        )
    
    # Spectral rolloff
    if len(features.spectral_rolloff) > 0:
        fig.add_trace(
            go.Scatter(x=time_seconds, y=features.spectral_rolloff,
                      mode='lines', name='Spectral Rolloff'),
            row=2, col=1
        )
    
    # Spectral flatness
    if len(features.spectral_flatness) > 0:
        fig.add_trace(
            go.Scatter(x=time_seconds, y=features.spectral_flatness,
                      mode='lines', name='Spectral Flatness'),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="Time (s)")
    fig.update_yaxes(title_text="Hz", row=1, col=1)
    fig.update_yaxes(title_text="Hz", row=1, col=2)
    fig.update_yaxes(title_text="Hz", row=2, col=1)
    fig.update_yaxes(title_text="Flatness", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display spectral statistics
    if features.feature_statistics:
        st.subheader("📊 Spectral Statistics")
        
        spectral_stats = {}
        for feature_name, stats in features.feature_statistics.items():
            if 'spectral' in feature_name.lower():
                spectral_stats[feature_name] = stats
        
        if spectral_stats:
            stats_df = pd.DataFrame(spectral_stats).T
            st.dataframe(stats_df.round(2))

def display_pitch_analysis(features: AudioFeatures):
    """Display pitch analysis results"""
    st.subheader("🎵 Pitch Analysis")
    
    if len(features.fundamental_frequency) == 0:
        st.warning("No pitch features available")
        return
    
    # Create pitch analysis plot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Fundamental Frequency', 'Pitch Confidence', 
                       'Chroma Features', 'Tonnetz Features'],
        vertical_spacing=0.15
    )
    
    # Time axis
    time_frames = np.arange(len(features.fundamental_frequency))
    time_seconds = librosa.frames_to_time(time_frames, sr=features.sample_rate)
    
    # Fundamental frequency
    f0_nonzero = features.fundamental_frequency.copy()
    f0_nonzero[f0_nonzero == 0] = np.nan  # Replace zeros with NaN for better visualization
    
    fig.add_trace(
        go.Scatter(x=time_seconds, y=f0_nonzero,
                  mode='lines', name='F0'),
        row=1, col=1
    )
    
    # Pitch confidence
    if len(features.pitch_confidence) > 0:
        fig.add_trace(
            go.Scatter(x=time_seconds, y=features.pitch_confidence,
                      mode='lines', name='Confidence'),
            row=1, col=2
        )
    
    fig.update_layout(height=600, showlegend=False)
    fig.update_xaxes(title_text="Time (s)")
    fig.update_yaxes(title_text="Hz", row=1, col=1)
    fig.update_yaxes(title_text="Confidence", row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Chroma features heatmap
    if features.chroma_features.size > 0:
        st.subheader("🎼 Chroma Features")
        
        fig_chroma = go.Figure(data=go.Heatmap(
            z=features.chroma_features,
            x=np.arange(features.chroma_features.shape[1]),
            y=['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'],
            colorscale='Viridis'
        ))
        
        fig_chroma.update_layout(
            title="Chroma Features Over Time",
            xaxis_title="Time Frames",
            yaxis_title="Pitch Class",
            height=400
        )
        
        st.plotly_chart(fig_chroma, use_container_width=True)

def display_rhythm_analysis(features: AudioFeatures):
    """Display rhythm and tempo analysis results"""
    st.subheader("🥁 Rhythm Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tempo", f"{features.tempo:.1f} BPM")
    
    with col2:
        st.metric("Beat Frames", len(features.beat_frames))
    
    with col3:
        st.metric("Onset Frames", len(features.onset_frames))
    
    # Beat and onset visualization
    if len(features.beat_frames) > 0 or len(features.onset_frames) > 0:
        fig = go.Figure()
        
        # Convert frames to time
        if len(features.beat_frames) > 0:
            beat_times = librosa.frames_to_time(features.beat_frames, sr=features.sample_rate)
            fig.add_trace(go.Scatter(
                x=beat_times,
                y=[1] * len(beat_times),
                mode='markers',
                marker=dict(size=10, color='red'),
                name='Beats'
            ))
        
        if len(features.onset_frames) > 0:
            onset_times = librosa.frames_to_time(features.onset_frames, sr=features.sample_rate)
            fig.add_trace(go.Scatter(
                x=onset_times,
                y=[0.5] * len(onset_times),
                mode='markers',
                marker=dict(size=8, color='blue'),
                name='Onsets'
            ))
        
        fig.update_layout(
            title="Beat and Onset Detection",
            xaxis_title="Time (s)",
            yaxis_title="Event Type",
            height=300,
            yaxis=dict(tickvals=[0.5, 1], ticktext=['Onsets', 'Beats'])
        )
        
        st.plotly_chart(fig, use_container_width=True)

def display_mfcc_analysis(features: AudioFeatures):
    """Display MFCC analysis results"""
    st.subheader("🔊 MFCC Analysis")
    
    if features.mfcc.size == 0:
        st.warning("No MFCC features available")
        return
    
    # MFCC heatmap
    fig = go.Figure(data=go.Heatmap(
        z=features.mfcc,
        colorscale='RdBu_r',
        x=np.arange(features.mfcc.shape[1]),
        y=[f'MFCC {i+1}' for i in range(features.mfcc.shape[0])]
    ))
    
    fig.update_layout(
        title="MFCC Features Over Time",
        xaxis_title="Time Frames",
        yaxis_title="MFCC Coefficients",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Delta MFCC
    if features.delta_mfcc.size > 0:
        st.subheader("📈 Delta MFCC")
        
        fig_delta = go.Figure(data=go.Heatmap(
            z=features.delta_mfcc,
            colorscale='RdBu_r',
            x=np.arange(features.delta_mfcc.shape[1]),
            y=[f'Δ MFCC {i+1}' for i in range(features.delta_mfcc.shape[0])]
        ))
        
        fig_delta.update_layout(
            title="Delta MFCC Features Over Time",
            xaxis_title="Time Frames",
            yaxis_title="Delta MFCC Coefficients",
            height=400
        )
        
        st.plotly_chart(fig_delta, use_container_width=True)

def display_audio_fingerprint(features: AudioFeatures):
    """Display audio fingerprint information"""
    st.subheader("🔍 Audio Fingerprint")
    
    if features.fingerprint:
        st.code(features.fingerprint, language='text')
        st.caption("Unique audio fingerprint for duplicate detection")
    else:
        st.warning("No fingerprint available")

def display_similarity_results(similarity_results):
    """Display audio similarity comparison results"""
    st.subheader("🔗 Audio Similarity Results")
    
    if not similarity_results:
        st.info("No similarity comparisons performed yet")
        return
    
    for i, similarity in enumerate(similarity_results):
        with st.expander(f"Comparison {i+1}: {similarity.similarity_score:.3f} similarity"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Audio 1:** {os.path.basename(similarity.audio1_path)}")
                st.write(f"**Audio 2:** {os.path.basename(similarity.audio2_path)}")
                st.write(f"**Similarity Score:** {similarity.similarity_score:.3f}")
                st.write(f"**Is Duplicate:** {'Yes' if similarity.is_duplicate else 'No'}")
                st.write(f"**Confidence:** {similarity.confidence:.3f}")
            
            with col2:
                st.write("**Distance Metrics:**")
                for metric, value in similarity.distance_metrics.items():
                    st.write(f"  • {metric}: {value:.3f}")
                
                st.write("**Feature Correlations:**")
                for correlation, value in similarity.feature_correlations.items():
                    st.write(f"  • {correlation}: {value:.3f}")

def display_clustering_results(clustering_results):
    """Display audio clustering results"""
    st.subheader("🎯 Audio Clustering Results")
    
    if not clustering_results:
        st.info("No clustering performed yet")
        return
    
    # Cluster overview
    st.write(f"**Number of Clusters:** {len(clustering_results)}")
    
    # Cluster details
    for cluster in clustering_results:
        with st.expander(f"Cluster {cluster.cluster_id} ({cluster.cluster_size} files)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Cluster Size:** {cluster.cluster_size}")
                st.write(f"**Intra-cluster Similarity:** {cluster.intra_cluster_similarity:.3f}")
                st.write(f"**Representative Audio:** {os.path.basename(cluster.representative_audio)}")
            
            with col2:
                st.write("**Audio Files in Cluster:**")
                for audio_file in cluster.audio_files:
                    st.write(f"  • {os.path.basename(audio_file)}")

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Advanced Audio Preprocessing",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Advanced Audio Preprocessing System")
    st.markdown("Comprehensive audio analysis with spectral features, pitch detection, and similarity comparison")
    
    # Initialize session state
    init_session_state()
    
    # Sidebar for navigation and controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Navigation
        page = st.selectbox(
            "Select Analysis Type",
            options=[
                "🎵 Single Audio Analysis",
                "🔗 Audio Similarity Comparison", 
                "🎯 Audio Clustering",
                "📦 Batch Processing",
                "🔍 Duplicate Detection"
            ]
        )
        
        st.divider()
        
        # Audio processing settings
        st.subheader("⚙️ Settings")
        
        sample_rate = st.selectbox(
            "Sample Rate",
            options=[22050, 44100, 48000],
            index=0
        )
        
        if sample_rate != st.session_state.preprocessor.sample_rate:
            st.session_state.preprocessor = AdvancedAudioPreprocessor(sample_rate)
    
    # Main content area
    if page == "🎵 Single Audio Analysis":
        st.header("🎵 Single Audio Analysis")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Audio File",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Upload an audio file for comprehensive analysis"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_audio_path = tmp_file.name
            
            try:
                if st.button("🚀 Analyze Audio", type="primary"):
                    with st.spinner("Extracting comprehensive audio features..."):
                        features = st.session_state.preprocessor.extract_comprehensive_features(temp_audio_path)
                        st.session_state.extracted_features = features
                    
                    st.success("✅ Analysis completed!")
                
                # Display results if available
                if st.session_state.extracted_features:
                    features = st.session_state.extracted_features
                    
                    # Basic info
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Duration", f"{features.duration:.2f}s")
                    
                    with col2:
                        st.metric("Sample Rate", f"{features.sample_rate} Hz")
                    
                    with col3:
                        st.metric("Tempo", f"{features.tempo:.1f} BPM")
                    
                    with col4:
                        st.metric("Channels", features.channels)
                    
                    # Analysis tabs
                    tabs = st.tabs([
                        "🌈 Spectral", "🎵 Pitch", "🥁 Rhythm", 
                        "🔊 MFCC", "🔍 Fingerprint"
                    ])
                    
                    with tabs[0]:
                        display_spectral_analysis(features)
                    
                    with tabs[1]:
                        display_pitch_analysis(features)
                    
                    with tabs[2]:
                        display_rhythm_analysis(features)
                    
                    with tabs[3]:
                        display_mfcc_analysis(features)
                    
                    with tabs[4]:
                        display_audio_fingerprint(features)
                    
                    # Export features
                    if st.button("💾 Export Features"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"audio_features_{timestamp}.json"
                        
                        st.session_state.preprocessor.save_features(features, filename)
                        st.success(f"✅ Features exported to {filename}")
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
    
    elif page == "🔗 Audio Similarity Comparison":
        st.header("🔗 Audio Similarity Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Audio File 1")
            uploaded_file1 = st.file_uploader(
                "Upload First Audio File",
                type=['wav', 'mp3', 'm4a', 'flac'],
                key="audio1"
            )
        
        with col2:
            st.subheader("Audio File 2")
            uploaded_file2 = st.file_uploader(
                "Upload Second Audio File",
                type=['wav', 'mp3', 'm4a', 'flac'],
                key="audio2"
            )
        
        if uploaded_file1 and uploaded_file2:
            # Save uploaded files temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file1:
                tmp_file1.write(uploaded_file1.getvalue())
                temp_audio_path1 = tmp_file1.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file2:
                tmp_file2.write(uploaded_file2.getvalue())
                temp_audio_path2 = tmp_file2.name
            
            try:
                if st.button("🔍 Compare Similarity", type="primary"):
                    with st.spinner("Comparing audio similarity..."):
                        similarity = st.session_state.preprocessor.similarity_analyzer.compare_audio_similarity(
                            temp_audio_path1, temp_audio_path2
                        )
                        st.session_state.similarity_results = [similarity]
                    
                    st.success("✅ Similarity analysis completed!")
                
                # Display results
                display_similarity_results(st.session_state.similarity_results)
            
            finally:
                # Clean up temporary files
                for temp_path in [temp_audio_path1, temp_audio_path2]:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    elif page == "🎯 Audio Clustering":
        st.header("🎯 Audio Clustering")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Upload Multiple Audio Files",
            type=['wav', 'mp3', 'm4a', 'flac'],
            accept_multiple_files=True,
            help="Upload multiple audio files for clustering analysis"
        )
        
        if uploaded_files and len(uploaded_files) >= 2:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            # Clustering settings
            col1, col2 = st.columns(2)
            
            with col1:
                clustering_method = st.selectbox(
                    "Clustering Method",
                    options=['kmeans', 'dbscan', 'hierarchical'],
                    help="Select clustering algorithm"
                )
            
            with col2:
                if clustering_method in ['kmeans', 'hierarchical']:
                    n_clusters = st.number_input(
                        "Number of Clusters",
                        min_value=2,
                        max_value=min(10, len(uploaded_files)),
                        value=min(3, len(uploaded_files) // 2)
                    )
                else:
                    n_clusters = None
            
            if st.button("🎯 Perform Clustering", type="primary"):
                # Save uploaded files temporarily
                temp_paths = []
                
                try:
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_paths.append(tmp_file.name)
                    
                    with st.spinner("Clustering audio files..."):
                        clusters = st.session_state.preprocessor.cluster_similar_audio(
                            temp_paths, clustering_method, n_clusters
                        )
                        st.session_state.clustering_results = clusters
                    
                    st.success("✅ Clustering completed!")
                
                finally:
                    # Clean up temporary files
                    for temp_path in temp_paths:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
            
            # Display results
            display_clustering_results(st.session_state.clustering_results)
        
        elif uploaded_files:
            st.warning("⚠️ Please upload at least 2 audio files for clustering")
    
    elif page == "📦 Batch Processing":
        st.header("📦 Batch Processing")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Upload Audio Files for Batch Processing",
            type=['wav', 'mp3', 'm4a', 'flac'],
            accept_multiple_files=True,
            help="Upload multiple audio files for batch feature extraction"
        )
        
        if uploaded_files:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            # Processing options
            include_duplicates = st.checkbox("🔍 Find Duplicate Audio", value=True)
            include_clustering = st.checkbox("🎯 Perform Clustering", value=True)
            
            if st.button("🚀 Start Batch Processing", type="primary"):
                # Save uploaded files temporarily
                temp_paths = []
                
                try:
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_paths.append(tmp_file.name)
                    
                    with st.spinner("Processing audio files..."):
                        # Process audio files with user-selected options
                        results = st.session_state.preprocessor.batch_process_audio(temp_paths)
                        st.session_state.batch_results = results
                        
                        # Additional processing based on user selections
                        if include_duplicates and len(temp_paths) > 1:
                            with st.spinner("Finding duplicate audio files..."):
                                duplicates = st.session_state.preprocessor.find_duplicate_audio(temp_paths)
                                results['duplicates'] = duplicates
                        
                        if include_clustering and len(temp_paths) > 2:
                            with st.spinner("Clustering similar audio files..."):
                                clusters = st.session_state.preprocessor.cluster_similar_audio(temp_paths)
                                results['clusters'] = [asdict(cluster) for cluster in clusters]
                    
                    st.success("✅ Batch processing completed!")
                
                finally:
                    # Clean up temporary files
                    for temp_path in temp_paths:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
            
            # Display batch results
            if st.session_state.batch_results:
                results = st.session_state.batch_results
                
                # Processing statistics
                st.subheader("📊 Processing Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Files", results['processing_stats']['total_files'])
                
                with col2:
                    st.metric("Processed", results['processing_stats']['processed_successfully'])
                
                with col3:
                    st.metric("Failed", results['processing_stats']['failed_processing'])
                
                with col4:
                    st.metric("Duplicates", results['processing_stats']['duplicates_found'])
                
                # Duplicates
                if results['duplicates']:
                    st.subheader("🔍 Duplicate Audio Files")
                    
                    duplicates_df = pd.DataFrame([
                        {
                            'File 1': os.path.basename(dup[0]),
                            'File 2': os.path.basename(dup[1]),
                            'Similarity': f"{dup[2]:.3f}"
                        }
                        for dup in results['duplicates']
                    ])
                    
                    st.dataframe(duplicates_df)
                
                # Clusters
                if results['clusters']:
                    st.subheader("🎯 Audio Clusters")
                    
                    for cluster in results['clusters']:
                        with st.expander(f"Cluster {cluster['cluster_id']} ({cluster['cluster_size']} files)"):
                            st.write(f"**Intra-cluster Similarity:** {cluster['intra_cluster_similarity']:.3f}")
                            st.write("**Files:**")
                            for audio_file in cluster['audio_files']:
                                st.write(f"  • {os.path.basename(audio_file)}")
    
    elif page == "🔍 Duplicate Detection":
        st.header("🔍 Duplicate Detection")
        
        # Multiple file upload
        uploaded_files = st.file_uploader(
            "Upload Audio Files for Duplicate Detection",
            type=['wav', 'mp3', 'm4a', 'flac'],
            accept_multiple_files=True,
            help="Upload audio files to find duplicates"
        )
        
        if uploaded_files and len(uploaded_files) >= 2:
            st.success(f"📁 {len(uploaded_files)} files uploaded")
            
            # Similarity threshold
            similarity_threshold = st.slider(
                "Similarity Threshold",
                min_value=0.5,
                max_value=1.0,
                value=0.85,
                step=0.05,
                help="Threshold for considering files as duplicates"
            )
            
            if st.button("🔍 Find Duplicates", type="primary"):
                # Save uploaded files temporarily
                temp_paths = []
                
                try:
                    for uploaded_file in uploaded_files:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            temp_paths.append(tmp_file.name)
                    
                    with st.spinner("Searching for duplicate audio files..."):
                        duplicates = st.session_state.preprocessor.find_duplicate_audio(
                            temp_paths, similarity_threshold
                        )
                    
                    if duplicates:
                        st.success(f"✅ Found {len(duplicates)} potential duplicate pairs")
                        
                        # Display duplicates
                        duplicates_df = pd.DataFrame([
                            {
                                'File 1': os.path.basename(dup[0]),
                                'File 2': os.path.basename(dup[1]),
                                'Similarity Score': f"{dup[2]:.3f}"
                            }
                            for dup in duplicates
                        ])
                        
                        st.dataframe(duplicates_df)
                        
                        # Visualization
                        if len(duplicates) > 0:
                            fig = px.bar(
                                duplicates_df,
                                x=range(len(duplicates_df)),
                                y='Similarity Score',
                                title="Duplicate Audio Similarity Scores",
                                labels={'x': 'Duplicate Pair', 'y': 'Similarity Score'}
                            )
                            
                            fig.add_hline(
                                y=similarity_threshold,
                                line_dash="dash",
                                line_color="red",
                                annotation_text="Threshold"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    else:
                        st.info("🎉 No duplicate audio files found!")
                
                finally:
                    # Clean up temporary files
                    for temp_path in temp_paths:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
        
        elif uploaded_files:
            st.warning("⚠️ Please upload at least 2 audio files for duplicate detection")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Advanced Audio Preprocessing System | 
        Powered by librosa, scipy, and machine learning</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()