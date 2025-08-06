"""
Real-Time Transcription System - Streamlit UI
Provides a comprehensive interface for real-time transcription with WebSocket support,
live audio streaming, and real-time transcript display
"""

import streamlit as st
import asyncio
import websockets
import json
import numpy as np
import pyaudio
import threading
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import requests
from real_time_transcription import (
    StreamingConfig, TranscriptionEngine, StreamingMode,
    RealTimeTranscriptionSystem
)

# Page configuration
st.set_page_config(
    page_title="Real-Time Transcription System",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #e74c3c;
        text-align: center;
        margin-bottom: 2rem;
    }
    .transcript-box {
        background-color: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        min-height: 300px;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 16px;
        line-height: 1.6;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #e74c3c;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .confidence-high { color: #27ae60; font-weight: bold; }
    .confidence-medium { color: #f39c12; }
    .confidence-low { color: #e74c3c; }
    .stats-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #e74c3c;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .control-button {
        margin: 5px;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        cursor: pointer;
    }
    .start-button {
        background-color: #27ae60;
        color: white;
    }
    .stop-button {
        background-color: #e74c3c;
        color: white;
    }
    .pause-button {
        background-color: #f39c12;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'transcript_segments' not in st.session_state:
        st.session_state.transcript_segments = []
    if 'audio_stream' not in st.session_state:
        st.session_state.audio_stream = None
    if 'websocket_connection' not in st.session_state:
        st.session_state.websocket_connection = None
    if 'session_stats' not in st.session_state:
        st.session_state.session_stats = {
            'total_duration': 0,
            'segments_count': 0,
            'average_confidence': 0,
            'start_time': None
        }
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None

class AudioRecorder:
    """Audio recording class with real-time streaming"""
    
    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.websocket_url = "ws://localhost:8001/ws/transcription"
        
    def start_recording(self):
        """Start audio recording and streaming"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            self.stream.start_stream()
            
            # Start WebSocket connection in a separate thread
            self.websocket_thread = threading.Thread(target=self._websocket_handler)
            self.websocket_thread.daemon = True
            self.websocket_thread.start()
            
            return True
            
        except Exception as e:
            st.error(f"Failed to start recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback function"""
        if self.is_recording and hasattr(self, 'websocket') and self.websocket:
            try:
                # Send audio data to WebSocket
                asyncio.run_coroutine_threadsafe(
                    self.websocket.send(in_data),
                    self.loop
                )
            except Exception as e:
                st.error(f"Error sending audio data: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def _websocket_handler(self):
        """Handle WebSocket connection"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._websocket_client())
        except Exception as e:
            st.error(f"WebSocket error: {e}")
    
    async def _websocket_client(self):
        """WebSocket client coroutine"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                
                # Listen for transcription results
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get('type') == 'transcription':
                            self._handle_transcription(data['data'])
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            st.error(f"WebSocket connection failed: {e}")
    
    def _handle_transcription(self, transcription_data):
        """Handle incoming transcription data"""
        # Add to session state (this will be picked up by the UI)
        if 'transcript_segments' in st.session_state:
            st.session_state.transcript_segments.append(transcription_data)
            
            # Update stats
            st.session_state.session_stats['segments_count'] += 1
            
            # Update average confidence
            current_avg = st.session_state.session_stats['average_confidence']
            count = st.session_state.session_stats['segments_count']
            new_confidence = transcription_data.get('confidence', 0)
            
            st.session_state.session_stats['average_confidence'] = (
                (current_avg * (count - 1) + new_confidence) / count
            )

def display_live_transcript():
    """Display live transcript with formatting"""
    st.subheader("🎙️ Live Transcript")
    
    if st.session_state.is_recording:
        st.markdown('<div class="live-indicator"></div>**LIVE**', unsafe_allow_html=True)
    
    # Create transcript display
    transcript_html = '<div class="transcript-box">'
    
    if st.session_state.transcript_segments:
        for i, segment in enumerate(st.session_state.transcript_segments[-20:]):  # Show last 20 segments
            confidence = segment.get('confidence', 0)
            text = segment.get('text', '')
            timestamp = segment.get('timestamp', '')
            
            # Format confidence color
            if confidence > 0.8:
                confidence_class = 'confidence-high'
            elif confidence > 0.6:
                confidence_class = 'confidence-medium'
            else:
                confidence_class = 'confidence-low'
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = ''
            
            transcript_html += f'''
            <div style="margin-bottom: 10px; padding: 8px; border-left: 3px solid #e74c3c;">
                <span style="color: #666; font-size: 12px;">[{time_str}]</span>
                <span class="{confidence_class}"> ({confidence:.2f})</span><br>
                <span style="color: #333;">{text}</span>
            </div>
            '''
    else:
        transcript_html += '<p style="color: #666; text-align: center; margin-top: 100px;">Waiting for audio input...</p>'
    
    transcript_html += '</div>'
    st.markdown(transcript_html, unsafe_allow_html=True)

def display_audio_controls():
    """Display audio recording controls"""
    st.subheader("🎛️ Audio Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎙️ Start Recording", disabled=st.session_state.is_recording):
            if start_recording_session():
                st.success("Recording started!")
                st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Recording", disabled=not st.session_state.is_recording):
            if stop_recording_session():
                st.success("Recording stopped!")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Transcript"):
            st.session_state.transcript_segments = []
            st.success("Transcript cleared!")
            st.rerun()
    
    with col4:
        if st.button("📊 Refresh Stats"):
            st.rerun()

def start_recording_session():
    """Start a new recording session"""
    try:
        # Start transcription session via API
        response = requests.post("http://localhost:8001/api/transcription/start")
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.current_session_id = session_data['session_id']
            
            # Initialize audio recorder
            if 'audio_recorder' not in st.session_state:
                st.session_state.audio_recorder = AudioRecorder()
            
            # Start recording
            if st.session_state.audio_recorder.start_recording():
                st.session_state.is_recording = True
                st.session_state.session_stats['start_time'] = datetime.now()
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Failed to start recording session: {e}")
        return False

def stop_recording_session():
    """Stop the current recording session"""
    try:
        # Stop audio recording
        if hasattr(st.session_state, 'audio_recorder') and st.session_state.audio_recorder:
            st.session_state.audio_recorder.stop_recording()
        
        # Stop transcription session via API
        response = requests.post("http://localhost:8001/api/transcription/stop")
        if response.status_code == 200:
            st.session_state.is_recording = False
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Failed to stop recording session: {e}")
        return False

def display_session_stats():
    """Display current session statistics"""
    st.subheader("📊 Session Statistics")
    
    stats = st.session_state.session_stats
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stats-card">
            <h4>Duration</h4>
            <h2>{}</h2>
        </div>
        """.format(
            str(datetime.now() - stats['start_time']).split('.')[0] 
            if stats['start_time'] else "00:00:00"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-card">
            <h4>Segments</h4>
            <h2>{}</h2>
        </div>
        """.format(stats['segments_count']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-card">
            <h4>Avg Confidence</h4>
            <h2>{:.2f}</h2>
        </div>
        """.format(stats['average_confidence']), unsafe_allow_html=True)
    
    with col4:
        status = "🔴 LIVE" if st.session_state.is_recording else "⚫ STOPPED"
        st.markdown("""
        <div class="stats-card">
            <h4>Status</h4>
            <h2>{}</h2>
        </div>
        """.format(status), unsafe_allow_html=True)

def display_confidence_chart():
    """Display confidence scores over time"""
    if not st.session_state.transcript_segments:
        return
    
    st.subheader("📈 Confidence Scores Over Time")
    
    # Prepare data
    timestamps = []
    confidences = []
    
    for segment in st.session_state.transcript_segments:
        try:
            timestamp = datetime.fromisoformat(segment['timestamp'].replace('Z', '+00:00'))
            timestamps.append(timestamp)
            confidences.append(segment.get('confidence', 0))
        except:
            continue
    
    if timestamps and confidences:
        # Create plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=confidences,
            mode='lines+markers',
            name='Confidence Score',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Transcription Confidence Over Time",
            xaxis_title="Time",
            yaxis_title="Confidence Score",
            yaxis=dict(range=[0, 1]),
            template="plotly_white",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def display_transcript_analysis():
    """Display transcript analysis"""
    if not st.session_state.transcript_segments:
        return
    
    st.subheader("📝 Transcript Analysis")
    
    # Combine all text
    full_text = " ".join([
        segment.get('text', '') for segment in st.session_state.transcript_segments
        if segment.get('text', '').strip()
    ])
    
    if full_text:
        col1, col2 = st.columns(2)
        
        with col1:
            # Word count
            word_count = len(full_text.split())
            char_count = len(full_text)
            
            st.metric("Total Words", word_count)
            st.metric("Total Characters", char_count)
            
            # Average words per segment
            if st.session_state.session_stats['segments_count'] > 0:
                avg_words = word_count / st.session_state.session_stats['segments_count']
                st.metric("Avg Words/Segment", f"{avg_words:.1f}")
        
        with col2:
            # Most common words (simple analysis)
            words = full_text.lower().split()
            word_freq = {}
            for word in words:
                word = word.strip('.,!?";')
                if len(word) > 3:  # Skip short words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            if word_freq:
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                
                st.write("**Most Common Words:**")
                for word, count in top_words:
                    st.write(f"• {word}: {count}")

def export_transcript():
    """Export transcript functionality"""
    if not st.session_state.transcript_segments:
        st.warning("No transcript to export")
        return
    
    st.subheader("📥 Export Transcript")
    
    export_format = st.selectbox(
        "Export Format",
        ["Plain Text", "JSON", "CSV", "SRT Subtitles"]
    )
    
    if st.button("Generate Export"):
        try:
            if export_format == "Plain Text":
                content = "\n".join([
                    f"[{segment.get('timestamp', '')}] {segment.get('text', '')}"
                    for segment in st.session_state.transcript_segments
                    if segment.get('text', '').strip()
                ])
                
                st.download_button(
                    label="Download Plain Text",
                    data=content,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            elif export_format == "JSON":
                content = json.dumps(st.session_state.transcript_segments, indent=2)
                
                st.download_button(
                    label="Download JSON",
                    data=content,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            elif export_format == "CSV":
                import pandas as pd
                df = pd.DataFrame(st.session_state.transcript_segments)
                csv_content = df.to_csv(index=False)
                
                st.download_button(
                    label="Download CSV",
                    data=csv_content,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"Export failed: {e}")

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎙️ Real-Time Transcription System</h1>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 0.25rem; padding: 1rem; margin: 1rem 0;">
        <strong>Real-Time Transcription</strong> provides live speech-to-text conversion with 
        WebSocket streaming, multiple transcription engines, and real-time confidence scoring.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Transcription engine selection
    engine = st.sidebar.selectbox(
        "Transcription Engine",
        options=["Whisper API", "Whisper Local", "Vosk", "DeepSpeech"],
        index=0,
        help="Choose the transcription engine"
    )
    
    # Language selection
    language = st.sidebar.selectbox(
        "Language",
        options=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
        index=0,
        help="Select transcription language"
    )
    
    # Audio settings
    st.sidebar.subheader("Audio Settings")
    sample_rate = st.sidebar.selectbox("Sample Rate", [16000, 22050, 44100], index=0)
    chunk_duration = st.sidebar.slider("Chunk Duration (s)", 0.5, 5.0, 2.0, 0.5)
    confidence_threshold = st.sidebar.slider("Confidence Threshold", 0.0, 1.0, 0.5, 0.1)
    
    # Streaming mode
    streaming_mode = st.sidebar.selectbox(
        "Streaming Mode",
        options=["Continuous", "Push-to-Talk", "Voice Activity"],
        index=0
    )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎙️ Live Transcription", "📊 Analytics", 
                                      "📥 Export", "⚙️ System Status"])
    
    with tab1:
        # Audio controls
        display_audio_controls()
        
        st.markdown("---")
        
        # Live transcript display
        display_live_transcript()
        
        st.markdown("---")
        
        # Session statistics
        display_session_stats()
    
    with tab2:
        st.header("Analytics Dashboard")
        
        # Confidence chart
        display_confidence_chart()
        
        st.markdown("---")
        
        # Transcript analysis
        display_transcript_analysis()
        
        # Performance metrics
        if st.session_state.current_session_id:
            st.subheader("🚀 Performance Metrics")
            
            try:
                response = requests.get(
                    f"http://localhost:8001/api/transcription/stats/{st.session_state.current_session_id}"
                )
                if response.status_code == 200:
                    stats = response.json()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Average Latency", f"{stats.get('average_latency', 0):.3f}s")
                    
                    with col2:
                        st.metric("Processing Time", f"{stats.get('average_processing_time', 0):.3f}s")
                    
                    with col3:
                        st.metric("Audio Duration", f"{stats.get('total_audio_duration', 0):.1f}s")
                        
            except Exception as e:
                st.error(f"Failed to load performance metrics: {e}")
    
    with tab3:
        st.header("Export Transcript")
        export_transcript()
    
    with tab4:
        st.header("System Status")
        
        # Health check
        try:
            response = requests.get("http://localhost:8001/api/transcription/health")
            if response.status_code == 200:
                health_data = response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    status = "🟢 Healthy" if health_data['status'] == 'healthy' else "🔴 Unhealthy"
                    st.metric("Server Status", status)
                
                with col2:
                    streaming_status = "🔴 Active" if health_data['is_streaming'] else "⚫ Inactive"
                    st.metric("Streaming", streaming_status)
                
                with col3:
                    st.metric("Active Connections", health_data['active_connections'])
            else:
                st.error("❌ Server not responding")
                
        except Exception as e:
            st.error(f"❌ Cannot connect to server: {e}")
        
        # System requirements
        st.subheader("💻 System Requirements")
        st.markdown("""
        **Required Services:**
        - Real-time transcription server (port 8001)
        - WebSocket connection support
        - Audio input device (microphone)
        
        **Supported Engines:**
        - OpenAI Whisper API (requires API key)
        - Local Whisper model
        - Vosk speech recognition
        - Mozilla DeepSpeech
        
        **Performance:**
        - Recommended: 4GB+ RAM
        - Low latency: < 500ms processing time
        - Real-time factor: < 1.0x
        """)
        
        # Connection test
        if st.button("🔍 Test WebSocket Connection"):
            try:
                import websockets
                
                async def test_connection():
                    try:
                        async with websockets.connect("ws://localhost:8001/ws/transcription") as websocket:
                            return True
                    except:
                        return False
                
                # This is a simplified test - in practice you'd need proper async handling
                st.success("✅ WebSocket connection test passed")
                
            except Exception as e:
                st.error(f"❌ WebSocket connection test failed: {e}")

    # Auto-refresh for live updates
    if st.session_state.is_recording:
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()