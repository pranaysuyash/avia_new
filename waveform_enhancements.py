"""
Additional enhancements for waveform visualization
Provides advanced features like zoom, filtering, and export options
"""

import os
import logging
import json
import base64
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import librosa

logger = logging.getLogger(__name__)

class WaveformEnhancer:
    """Advanced waveform enhancement features"""
    
    def __init__(self):
        self.zoom_level = 1.0
        self.filter_applied = False
        self.current_view = "full"
    
    def create_zoomable_waveform(
        self, 
        audio_path: str, 
        zoom_start: float = 0, 
        zoom_duration: float = None
    ) -> str:
        """Create a zoomable waveform view"""
        try:
            # Load audio
            audio_data, sr = librosa.load(audio_path, sr=16000)
            total_duration = len(audio_data) / sr
            
            # Apply zoom
            if zoom_duration is None:
                zoom_duration = total_duration
            
            start_sample = int(zoom_start * sr)
            end_sample = int(min((zoom_start + zoom_duration) * sr, len(audio_data)))
            
            zoomed_audio = audio_data[start_sample:end_sample]
            zoomed_time = np.linspace(zoom_start, zoom_start + len(zoomed_audio)/sr, len(zoomed_audio))
            
            # Create enhanced plot
            plt.style.use('default')
            fig, ax = plt.subplots(figsize=(14, 5), dpi=120)
            
            # Plot waveform with enhanced styling
            ax.plot(zoomed_time, zoomed_audio, color='#2E86AB', linewidth=0.8, alpha=0.9)
            ax.fill_between(zoomed_time, zoomed_audio, alpha=0.4, color='#A23B72')
            
            # Enhanced styling
            ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Amplitude', fontsize=12, fontweight='bold')
            ax.set_title(f'Audio Waveform - Zoom View ({zoom_start:.1f}s - {zoom_start + zoom_duration:.1f}s)', 
                        fontsize=14, fontweight='bold', pad=20)
            
            # Grid and styling
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_facecolor('#F8F9FA')
            
            # Add time markers
            time_markers = np.arange(zoom_start, zoom_start + zoom_duration, max(1, zoom_duration/10))
            for marker in time_markers:
                if marker <= zoom_start + zoom_duration:
                    ax.axvline(x=marker, color='gray', alpha=0.5, linestyle=':', linewidth=1)
            
            plt.tight_layout()
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                plt.savefig(temp_file.name, dpi=120, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                plt.close()
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Zoomable waveform creation failed: {e}")
            raise
    
    def create_frequency_analysis_plot(self, audio_path: str) -> str:
        """Create frequency analysis visualization"""
        try:
            # Load audio
            audio_data, sr = librosa.load(audio_path, sr=16000)
            
            # Compute spectrogram
            D = librosa.stft(audio_data)
            S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
            
            # Create plot
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), dpi=100)
            
            # Waveform
            time_axis = np.linspace(0, len(audio_data)/sr, len(audio_data))
            ax1.plot(time_axis, audio_data, color='#1f77b4', linewidth=0.5)
            ax1.set_title('Waveform', fontweight='bold')
            ax1.set_ylabel('Amplitude')
            ax1.grid(True, alpha=0.3)
            
            # Spectrogram
            img = librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz', ax=ax2)
            ax2.set_title('Frequency Analysis (Spectrogram)', fontweight='bold')
            ax2.set_ylabel('Frequency (Hz)')
            ax2.set_xlabel('Time (seconds)')
            
            # Add colorbar
            fig.colorbar(img, ax=ax2, format='%+2.0f dB')
            
            plt.tight_layout()
            
            # Save to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                plt.savefig(temp_file.name, dpi=100, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                plt.close()
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Frequency analysis plot creation failed: {e}")
            raise
    
    def export_waveform_data(
        self, 
        audio_path: str, 
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """Export comprehensive waveform data"""
        try:
            # Load audio
            audio_data, sr = librosa.load(audio_path, sr=16000)
            duration = len(audio_data) / sr
            
            # Basic waveform data
            export_data = {
                'metadata': {
                    'duration': duration,
                    'sample_rate': sr,
                    'samples': len(audio_data),
                    'format': 'WAV',
                    'channels': 1
                },
                'waveform': {
                    'time_axis': np.linspace(0, duration, len(audio_data)).tolist(),
                    'amplitude': audio_data.tolist()
                }
            }
            
            if include_analysis:
                # Add analysis data
                export_data['analysis'] = {
                    'rms_energy': float(np.sqrt(np.mean(audio_data**2))),
                    'peak_amplitude': float(np.max(np.abs(audio_data))),
                    'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(audio_data))),
                    'spectral_centroid': librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0].tolist(),
                    'spectral_rolloff': librosa.feature.spectral_rolloff(y=audio_data, sr=sr)[0].tolist()
                }
                
                # Tempo and beat tracking
                try:
                    tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sr)
                    export_data['analysis']['tempo'] = float(tempo)
                    export_data['analysis']['beats'] = librosa.frames_to_time(beats, sr=sr).tolist()
                except:
                    export_data['analysis']['tempo'] = None
                    export_data['analysis']['beats'] = []
            
            return export_data
            
        except Exception as e:
            logger.error(f"Waveform data export failed: {e}")
            raise

class WaveformBookmarkManager:
    """Manage bookmarks and annotations on waveforms"""
    
    def __init__(self):
        self.bookmarks = []
        self.annotations = []
    
    def add_bookmark(self, time_position: float, label: str, description: str = ""):
        """Add a bookmark at specific time position"""
        bookmark = {
            'id': len(self.bookmarks),
            'time': time_position,
            'label': label,
            'description': description,
            'created_at': np.datetime64('now').astype(str)
        }
        self.bookmarks.append(bookmark)
        return bookmark['id']
    
    def add_annotation(self, start_time: float, end_time: float, text: str, category: str = "general"):
        """Add an annotation for a time range"""
        annotation = {
            'id': len(self.annotations),
            'start': start_time,
            'end': end_time,
            'text': text,
            'category': category,
            'created_at': np.datetime64('now').astype(str)
        }
        self.annotations.append(annotation)
        return annotation['id']
    
    def get_bookmarks_in_range(self, start_time: float, end_time: float) -> List[Dict]:
        """Get bookmarks within a time range"""
        return [b for b in self.bookmarks if start_time <= b['time'] <= end_time]
    
    def export_bookmarks(self) -> str:
        """Export bookmarks as JSON"""
        return json.dumps({
            'bookmarks': self.bookmarks,
            'annotations': self.annotations
        }, indent=2)

def create_interactive_waveform_component(
    waveform_image_path: str,
    audio_duration: float,
    bookmarks: List[Dict] = None,
    annotations: List[Dict] = None
) -> str:
    """Create an advanced interactive waveform component"""
    
    # Convert image to base64
    with open(waveform_image_path, 'rb') as img_file:
        img_data = base64.b64encode(img_file.read()).decode()
    
    # Prepare bookmark data
    bookmark_js = json.dumps(bookmarks or [])
    annotation_js = json.dumps(annotations or [])
    
    html_content = f"""
    <div id="advanced-waveform-container" style="position: relative; width: 100%; max-width: 1000px; margin: 0 auto;">
        <div id="waveform-controls" style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <button onclick="zoomIn()" style="margin-right: 5px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">Zoom In</button>
            <button onclick="zoomOut()" style="margin-right: 5px; padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">Zoom Out</button>
            <button onclick="resetZoom()" style="margin-right: 5px; padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">Reset</button>
            <button onclick="addBookmark()" style="margin-right: 5px; padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">Add Bookmark</button>
            <span style="margin-left: 20px; font-weight: bold;">Zoom: <span id="zoom-level">100%</span></span>
        </div>
        
        <div id="waveform-display" style="position: relative; border: 1px solid #ddd; border-radius: 5px; overflow: hidden;">
            <img id="waveform-image" src="data:image/png;base64,{img_data}" 
                 style="width: 100%; height: auto; cursor: crosshair; display: block;" 
                 onclick="handleWaveformClick(event)"
                 onmousemove="showTimeTooltip(event)">
            
            <div id="position-marker" style="position: absolute; top: 0; bottom: 0; width: 2px; 
                 background-color: #dc3545; display: none; pointer-events: none; z-index: 10;"></div>
            
            <div id="bookmarks-layer" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 5;"></div>
            
            <div id="time-tooltip" style="position: absolute; background: rgba(0,0,0,0.8); color: white; 
                 padding: 4px 8px; border-radius: 3px; font-size: 12px; display: none; pointer-events: none; z-index: 15;"></div>
        </div>
        
        <div id="time-display" style="margin-top: 10px; padding: 10px; background: #e9ecef; border-radius: 5px; font-family: monospace; font-size: 14px;">
            <div style="display: flex; justify-content: space-between;">
                <span>Position: <span id="current-position">00:00</span></span>
                <span>Duration: {int(audio_duration//60):02d}:{int(audio_duration%60):02d}</span>
                <span>Selected: <span id="selected-range">None</span></span>
            </div>
        </div>
        
        <div id="bookmark-list" style="margin-top: 10px; max-height: 150px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 10px; background: white;">
            <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #495057;">Bookmarks & Annotations</h4>
            <div id="bookmark-items"></div>
        </div>
    </div>
    
    <script>
    let currentZoom = 1.0;
    let currentPosition = 0;
    let bookmarks = {bookmark_js};
    let annotations = {annotation_js};
    let audioDuration = {audio_duration};
    
    function handleWaveformClick(event) {{
        const img = event.target;
        const rect = img.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const imageWidth = rect.width;
        const timePosition = (clickX / imageWidth) * audioDuration;
        
        currentPosition = timePosition;
        updatePositionMarker(clickX);
        updateTimeDisplay(timePosition);
        
        // Trigger custom event
        window.parent.postMessage({{
            type: 'waveform-click',
            position: timePosition,
            pixel: clickX
        }}, '*');
    }}
    
    function showTimeTooltip(event) {{
        const img = event.target;
        const rect = img.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const timePosition = (mouseX / rect.width) * audioDuration;
        
        const tooltip = document.getElementById('time-tooltip');
        const minutes = Math.floor(timePosition / 60);
        const seconds = Math.floor(timePosition % 60);
        
        tooltip.innerHTML = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
        tooltip.style.left = (event.clientX - rect.left + 10) + 'px';
        tooltip.style.top = (event.clientY - rect.top - 30) + 'px';
        tooltip.style.display = 'block';
    }}
    
    function updatePositionMarker(pixelX) {{
        const marker = document.getElementById('position-marker');
        marker.style.left = pixelX + 'px';
        marker.style.display = 'block';
    }}
    
    function updateTimeDisplay(timePosition) {{
        const minutes = Math.floor(timePosition / 60);
        const seconds = Math.floor(timePosition % 60);
        document.getElementById('current-position').textContent = 
            `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
    }}
    
    function zoomIn() {{
        currentZoom = Math.min(currentZoom * 1.5, 10);
        updateZoom();
    }}
    
    function zoomOut() {{
        currentZoom = Math.max(currentZoom / 1.5, 0.1);
        updateZoom();
    }}
    
    function resetZoom() {{
        currentZoom = 1.0;
        updateZoom();
    }}
    
    function updateZoom() {{
        const img = document.getElementById('waveform-image');
        img.style.transform = `scaleX(${{currentZoom}})`;
        document.getElementById('zoom-level').textContent = Math.round(currentZoom * 100) + '%';
    }}
    
    function addBookmark() {{
        const label = prompt('Enter bookmark label:');
        if (label) {{
            const bookmark = {{
                id: bookmarks.length,
                time: currentPosition,
                label: label,
                description: ''
            }};
            bookmarks.push(bookmark);
            renderBookmarks();
            
            // Trigger custom event
            window.parent.postMessage({{
                type: 'bookmark-added',
                bookmark: bookmark
            }}, '*');
        }}
    }}
    
    function renderBookmarks() {{
        const container = document.getElementById('bookmark-items');
        container.innerHTML = '';
        
        bookmarks.forEach(bookmark => {{
            const div = document.createElement('div');
            div.style.cssText = 'margin-bottom: 5px; padding: 5px; background: #f8f9fa; border-radius: 3px; font-size: 12px;';
            div.innerHTML = `
                <strong>${{bookmark.label}}</strong> - ${{Math.floor(bookmark.time/60).toString().padStart(2,'0')}}:${{Math.floor(bookmark.time%60).toString().padStart(2,'0')}}
                <button onclick="jumpToBookmark(${{bookmark.time}})" style="margin-left: 10px; padding: 2px 6px; font-size: 10px; background: #007bff; color: white; border: none; border-radius: 2px; cursor: pointer;">Jump</button>
            `;
            container.appendChild(div);
        }});
    }}
    
    function jumpToBookmark(time) {{
        const img = document.getElementById('waveform-image');
        const rect = img.getBoundingClientRect();
        const pixelX = (time / audioDuration) * rect.width;
        
        currentPosition = time;
        updatePositionMarker(pixelX);
        updateTimeDisplay(time);
    }}
    
    // Initialize
    renderBookmarks();
    
    // Hide tooltip when mouse leaves
    document.getElementById('waveform-image').addEventListener('mouseleave', function() {{
        document.getElementById('time-tooltip').style.display = 'none';
    }});
    </script>
    """
    
    return html_content

# Global instances
waveform_enhancer = WaveformEnhancer()
bookmark_manager = WaveformBookmarkManager()