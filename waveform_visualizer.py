"""
Waveform Visualization and Audio Navigation Module
Generates waveform images and provides interactive audio navigation
"""

import os
import logging
import tempfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import librosa
import soundfile as sf
from typing import Optional, List, Tuple, Dict, Any
import base64
from io import BytesIO
import streamlit as st

from errors import MediaProcessingError, ErrorCode

logger = logging.getLogger(__name__)

class WaveformVisualizer:
    """Generate and manage waveform visualizations for audio files"""
    
    def __init__(self):
        self.sample_rate = 16000  # Standard sample rate for processing
        self.figure_size = (12, 4)  # Default figure size
        self.dpi = 100  # Default DPI for images
        
    def generate_waveform_image(
        self, 
        audio_path: str, 
        output_path: Optional[str] = None,
        duration_limit: Optional[float] = None,
        speaker_segments: Optional[List[Dict]] = None,
        transcript_segments: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate waveform image for audio file with optional speaker and transcript markers
        
        Args:
            audio_path: Path to audio file
            output_path: Optional output path for image (if None, creates temp file)
            duration_limit: Optional limit for audio duration (for long files)
            speaker_segments: Optional list of speaker change segments
            transcript_segments: Optional list of transcript segments with timestamps
            
        Returns:
            str: Path to generated waveform image
            
        Raises:
            MediaProcessingError: If waveform generation fails
        """
        try:
            logger.info(f"Generating waveform for: {audio_path}")
            
            # Load audio file
            audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Apply duration limit if specified
            if duration_limit and len(audio_data) / sr > duration_limit:
                max_samples = int(duration_limit * sr)
                audio_data = audio_data[:max_samples]
                logger.info(f"Limited audio to {duration_limit} seconds")
            
            # Create time axis
            time_axis = np.linspace(0, len(audio_data) / sr, len(audio_data))
            
            # Create figure and axis
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)
            
            # Plot waveform
            ax.plot(time_axis, audio_data, color='#1f77b4', linewidth=0.5, alpha=0.8)
            ax.fill_between(time_axis, audio_data, alpha=0.3, color='#1f77b4')
            
            # Add speaker change markers if provided
            if speaker_segments:
                self._add_speaker_markers(ax, speaker_segments, max(time_axis))
            
            # Add transcript segment markers if provided
            if transcript_segments:
                self._add_transcript_markers(ax, transcript_segments, max(time_axis))
            
            # Customize appearance
            ax.set_xlabel('Time (seconds)', fontsize=10)
            ax.set_ylabel('Amplitude', fontsize=10)
            ax.set_title('Audio Waveform', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, max(time_axis))
            
            # Set y-axis limits for better visualization
            y_max = max(abs(audio_data.min()), abs(audio_data.max()))
            ax.set_ylim(-y_max * 1.1, y_max * 1.1)
            
            # Tight layout
            plt.tight_layout()
            
            # Save image
            if output_path is None:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    output_path = temp_file.name
            
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            logger.info(f"Waveform image generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate waveform: {str(e)}")
            raise MediaProcessingError(
                message=f"Waveform generation failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to generate waveform visualization.",
                suggestions=[
                    "Check that the audio file is valid",
                    "Try with a shorter audio file",
                    "Ensure sufficient disk space for image generation"
                ]
            )
    
    def _add_speaker_markers(self, ax, speaker_segments: List[Dict], max_time: float):
        """Add visual markers for speaker changes"""
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        
        for i, segment in enumerate(speaker_segments):
            start_time = segment.get('start', 0)
            end_time = segment.get('end', max_time)
            speaker = segment.get('speaker', f'Speaker {i+1}')
            
            if start_time < max_time:
                # Add vertical line at speaker change
                ax.axvline(x=start_time, color=colors[i % len(colors)], 
                          linestyle='--', alpha=0.7, linewidth=2)
                
                # Add speaker label
                ax.text(start_time + 0.1, ax.get_ylim()[1] * 0.8, 
                       speaker, rotation=90, fontsize=8, 
                       color=colors[i % len(colors)], fontweight='bold')
    
    def _add_transcript_markers(self, ax, transcript_segments: List[Dict], max_time: float):
        """Add visual markers for transcript segments"""
        for i, segment in enumerate(transcript_segments):
            start_time = segment.get('start', 0)
            end_time = segment.get('end', start_time + 5)  # Default 5-second segments
            
            if start_time < max_time:
                # Add subtle background highlighting for segments
                rect = patches.Rectangle(
                    (start_time, ax.get_ylim()[0]), 
                    min(end_time - start_time, max_time - start_time), 
                    ax.get_ylim()[1] - ax.get_ylim()[0],
                    linewidth=0, facecolor='yellow', alpha=0.1
                )
                ax.add_patch(rect)
    
    def generate_interactive_waveform_data(
        self, 
        audio_path: str,
        segment_duration: float = 10.0
    ) -> Dict[str, Any]:
        """
        Generate data for interactive waveform navigation
        
        Args:
            audio_path: Path to audio file
            segment_duration: Duration of each segment in seconds
            
        Returns:
            Dict containing waveform data and segment information
        """
        try:
            # Load audio file
            audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
            total_duration = len(audio_data) / sr
            
            # Create segments
            segments = []
            num_segments = int(np.ceil(total_duration / segment_duration))
            
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, total_duration)
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                
                segment_data = audio_data[start_sample:end_sample]
                segment_time = np.linspace(start_time, end_time, len(segment_data))
                
                segments.append({
                    'index': i,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'data': segment_data.tolist(),
                    'time': segment_time.tolist(),
                    'rms': float(np.sqrt(np.mean(segment_data**2))),  # RMS amplitude
                    'peak': float(np.max(np.abs(segment_data)))  # Peak amplitude
                })
            
            return {
                'total_duration': total_duration,
                'sample_rate': sr,
                'segments': segments,
                'segment_duration': segment_duration,
                'num_segments': num_segments
            }
            
        except Exception as e:
            logger.error(f"Failed to generate interactive waveform data: {str(e)}")
            raise MediaProcessingError(
                message=f"Interactive waveform data generation failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to generate interactive waveform data."
            )
    
    def create_waveform_with_timeline(
        self,
        audio_path: str,
        transcript_data: Optional[List[Dict]] = None,
        speaker_data: Optional[List[Dict]] = None
    ) -> str:
        """
        Create enhanced waveform with timeline markers
        
        Args:
            audio_path: Path to audio file
            transcript_data: Optional transcript with timestamps
            speaker_data: Optional speaker diarization data
            
        Returns:
            str: Path to generated timeline waveform image
        """
        try:
            # Load audio
            audio_data, sr = librosa.load(audio_path, sr=self.sample_rate)
            time_axis = np.linspace(0, len(audio_data) / sr, len(audio_data))
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 6), 
                                          height_ratios=[3, 1], dpi=self.dpi)
            
            # Main waveform plot
            ax1.plot(time_axis, audio_data, color='#1f77b4', linewidth=0.5, alpha=0.8)
            ax1.fill_between(time_axis, audio_data, alpha=0.3, color='#1f77b4')
            ax1.set_ylabel('Amplitude', fontsize=10)
            ax1.set_title('Audio Waveform with Timeline', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            # Timeline plot (bottom)
            ax2.set_xlim(0, max(time_axis))
            ax2.set_ylim(-0.5, 1.5)
            ax2.set_xlabel('Time (seconds)', fontsize=10)
            ax2.set_ylabel('Events', fontsize=10)
            
            # Add speaker timeline if available
            if speaker_data:
                for i, segment in enumerate(speaker_data):
                    start = segment.get('start', 0)
                    end = segment.get('end', start + 1)
                    speaker = segment.get('speaker', f'S{i+1}')
                    color = plt.cm.Set3(i % 12)
                    
                    # Speaker segment bar
                    ax2.barh(0.8, end - start, left=start, height=0.3, 
                            color=color, alpha=0.7, label=speaker if i < 5 else "")
                    
                    # Speaker label
                    if end - start > 2:  # Only label longer segments
                        ax2.text(start + (end - start) / 2, 0.95, speaker, 
                                ha='center', va='center', fontsize=8, fontweight='bold')
            
            # Add transcript markers if available
            if transcript_data:
                for i, segment in enumerate(transcript_data):
                    start = segment.get('start', 0)
                    end = segment.get('end', start + 1)
                    
                    # Transcript segment marker
                    ax2.barh(0.2, end - start, left=start, height=0.2, 
                            color='green', alpha=0.5)
                    
                    # Add text snippet for longer segments
                    if end - start > 5 and 'text' in segment:
                        text_snippet = segment['text'][:20] + "..." if len(segment['text']) > 20 else segment['text']
                        ax2.text(start + (end - start) / 2, 0.3, text_snippet, 
                                ha='center', va='center', fontsize=7, rotation=45)
            
            # Customize timeline
            ax2.set_yticks([0.3, 0.95])
            ax2.set_yticklabels(['Transcript', 'Speakers'])
            ax2.grid(True, alpha=0.3)
            
            # Add legend if speakers are present
            if speaker_data and len(speaker_data) <= 5:
                ax2.legend(loc='upper right', fontsize=8)
            
            plt.tight_layout()
            
            # Save image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                output_path = temp_file.name
            
            plt.savefig(output_path, dpi=self.dpi, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            logger.info(f"Timeline waveform generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate timeline waveform: {str(e)}")
            raise MediaProcessingError(
                message=f"Timeline waveform generation failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to generate timeline waveform."
            )

class AudioNavigator:
    """Provide interactive audio navigation capabilities"""
    
    def __init__(self):
        self.current_position = 0.0
        self.total_duration = 0.0
        self.segments = []
    
    def initialize_navigation(self, audio_path: str, segment_duration: float = 10.0):
        """Initialize navigation with audio file"""
        try:
            # Get audio duration
            audio_data, sr = librosa.load(audio_path, sr=None)
            self.total_duration = len(audio_data) / sr
            
            # Create navigation segments
            num_segments = int(np.ceil(self.total_duration / segment_duration))
            self.segments = []
            
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, self.total_duration)
                
                self.segments.append({
                    'index': i,
                    'start': start_time,
                    'end': end_time,
                    'duration': end_time - start_time,
                    'label': f"Segment {i+1} ({start_time:.1f}s - {end_time:.1f}s)"
                })
            
            logger.info(f"Navigation initialized: {len(self.segments)} segments, {self.total_duration:.1f}s total")
            
        except Exception as e:
            logger.error(f"Failed to initialize navigation: {str(e)}")
            raise MediaProcessingError(
                message=f"Navigation initialization failed: {str(e)}",
                error_code=ErrorCode.MEDIA_PROCESSING_ERROR,
                user_message="Failed to initialize audio navigation."
            )
    
    def get_segment_at_time(self, time_position: float) -> Optional[Dict]:
        """Get the segment containing the specified time position"""
        for segment in self.segments:
            if segment['start'] <= time_position < segment['end']:
                return segment
        return None
    
    def get_navigation_controls(self) -> Dict[str, Any]:
        """Get data for rendering navigation controls"""
        return {
            'total_duration': self.total_duration,
            'current_position': self.current_position,
            'segments': self.segments,
            'formatted_duration': self._format_time(self.total_duration),
            'formatted_position': self._format_time(self.current_position)
        }
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

def create_clickable_waveform_html(
    waveform_image_path: str,
    audio_duration: float,
    segments: Optional[List[Dict]] = None
) -> str:
    """
    Create HTML for clickable waveform navigation
    
    Args:
        waveform_image_path: Path to waveform image
        audio_duration: Total audio duration in seconds
        segments: Optional list of segments for navigation
        
    Returns:
        str: HTML string for clickable waveform
    """
    try:
        # Convert image to base64 for embedding
        with open(waveform_image_path, 'rb') as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
        
        # Create HTML with JavaScript for interactivity
        html_content = f"""
        <div id="waveform-container" style="position: relative; width: 100%; max-width: 800px;">
            <img id="waveform-image" src="data:image/png;base64,{img_data}" 
                 style="width: 100%; height: auto; cursor: pointer;" 
                 onclick="handleWaveformClick(event)">
            <div id="position-marker" style="position: absolute; top: 0; bottom: 0; width: 2px; 
                 background-color: red; display: none; pointer-events: none;"></div>
            <div id="time-display" style="margin-top: 10px; font-family: monospace; font-size: 14px;">
                Click on waveform to navigate • Duration: {audio_duration:.1f}s
            </div>
        </div>
        
        <script>
        function handleWaveformClick(event) {{
            const img = event.target;
            const rect = img.getBoundingClientRect();
            const clickX = event.clientX - rect.left;
            const imageWidth = rect.width;
            const timePosition = (clickX / imageWidth) * {audio_duration};
            
            // Update position marker
            const marker = document.getElementById('position-marker');
            marker.style.left = clickX + 'px';
            marker.style.display = 'block';
            
            // Update time display
            const timeDisplay = document.getElementById('time-display');
            const minutes = Math.floor(timePosition / 60);
            const seconds = Math.floor(timePosition % 60);
            timeDisplay.innerHTML = `Position: ${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}} • Duration: {audio_duration:.1f}s`;
            
            // Trigger custom event for Streamlit integration
            window.parent.postMessage({{
                type: 'waveform-click',
                position: timePosition
            }}, '*');
        }}
        </script>
        """
        
        return html_content
        
    except Exception as e:
        logger.error(f"Failed to create clickable waveform HTML: {str(e)}")
        return f"<p>Error creating interactive waveform: {str(e)}</p>"

# Global instances
waveform_visualizer = WaveformVisualizer()
audio_navigator = AudioNavigator()