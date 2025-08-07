"""
Enhanced Audio Player Component
Provides programmatic control over audio playback with JavaScript integration
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Optional, Dict, Any
import json
import base64

logger = logging.getLogger(__name__)


def create_audio_player_component(
    audio_file_path: str,
    start_time: float = 0,
    player_id: str = "audio-player"
) -> str:
    """
    Create an HTML audio player with JavaScript controls
    
    Args:
        audio_file_path: Path to the audio file
        start_time: Initial playback position in seconds
        player_id: HTML element ID for the player
        
    Returns:
        HTML string for the audio player component
    """
    
    # Read audio file and encode as base64
    try:
        with open(audio_file_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            
        # Detect audio format
        if audio_file_path.endswith('.mp3'):
            audio_format = 'audio/mp3'
        elif audio_file_path.endswith('.wav'):
            audio_format = 'audio/wav'
        elif audio_file_path.endswith('.m4a'):
            audio_format = 'audio/mp4'
        else:
            audio_format = 'audio/mpeg'
            
    except Exception as e:
        logger.error(f"Error reading audio file: {e}")
        return ""
    
    # Create HTML component with JavaScript controls
    html_content = f"""
    <div id="{player_id}-container" style="margin: 20px 0;">
        <audio 
            id="{player_id}" 
            controls 
            style="width: 100%; outline: none;"
            preload="metadata"
        >
            <source src="data:{audio_format};base64,{audio_base64}" type="{audio_format}">
            Your browser does not support the audio element.
        </audio>
        
        <div id="{player_id}-info" style="margin-top: 10px; font-size: 14px; color: #666;">
            <span id="{player_id}-current-time">00:00</span> / 
            <span id="{player_id}-duration">00:00</span>
        </div>
    </div>
    
    <script>
    (function() {{
        const audio = document.getElementById('{player_id}');
        const currentTimeSpan = document.getElementById('{player_id}-current-time');
        const durationSpan = document.getElementById('{player_id}-duration');
        
        // Format time helper
        function formatTime(seconds) {{
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${{minutes.toString().padStart(2, '0')}}:${{secs.toString().padStart(2, '0')}}`;
        }}
        
        // Set initial time
        audio.currentTime = {start_time};
        
        // Update time display
        audio.addEventListener('loadedmetadata', function() {{
            durationSpan.textContent = formatTime(audio.duration);
        }});
        
        audio.addEventListener('timeupdate', function() {{
            currentTimeSpan.textContent = formatTime(audio.currentTime);
            
            // Send time update to Streamlit
            window.parent.postMessage({{
                type: 'audio-timeupdate',
                playerId: '{player_id}',
                currentTime: audio.currentTime,
                duration: audio.duration
            }}, '*');
        }});
        
        // Listen for jump commands from Streamlit
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'audio-jump' && event.data.playerId === '{player_id}') {{
                audio.currentTime = event.data.time;
                if (event.data.play) {{
                    audio.play();
                }}
            }}
        }});
        
        // Send player ready message
        window.parent.postMessage({{
            type: 'audio-ready',
            playerId: '{player_id}'
        }}, '*');
    }})();
    </script>
    """
    
    return html_content


def render_enhanced_audio_player(
    audio_file_path: str,
    height: int = 150,
    key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Render an enhanced audio player with programmatic control
    
    Args:
        audio_file_path: Path to the audio file
        height: Component height in pixels
        key: Unique key for the component
        
    Returns:
        Dict with player state information
    """
    
    # Initialize session state for audio control
    if 'audio_jump_time' not in st.session_state:
        st.session_state.audio_jump_time = 0
    if 'audio_jump_trigger' not in st.session_state:
        st.session_state.audio_jump_trigger = 0
    
    # Create player HTML
    player_html = create_audio_player_component(
        audio_file_path,
        start_time=st.session_state.audio_jump_time,
        player_id="enhanced-audio-player"
    )
    
    # JavaScript to handle communication with the player
    bridge_script = f"""
    <script>
    // Bridge between Streamlit and audio player
    window.streamlitAudioBridge = {{
        jumpToTime: function(time, autoPlay = true) {{
            window.postMessage({{
                type: 'audio-jump',
                playerId: 'enhanced-audio-player',
                time: time,
                play: autoPlay
            }}, '*');
        }},
        
        getCurrentTime: function() {{
            // This would need to be implemented with proper state management
            return 0;
        }}
    }};
    
    // Listen for Streamlit commands
    window.addEventListener('message', function(event) {{
        if (event.data.type === 'streamlit-audio-command') {{
            if (event.data.command === 'jump') {{
                window.streamlitAudioBridge.jumpToTime(event.data.time, event.data.play);
            }}
        }}
    }});
    </script>
    """
    
    # Render the component
    components.html(
        player_html + bridge_script,
        height=height,
        scrolling=False,
        key=key
    )
    
    return {
        'current_time': st.session_state.get('audio_current_time', 0),
        'is_playing': st.session_state.get('audio_playing', False)
    }


def jump_to_audio_time(time_seconds: float, auto_play: bool = True):
    """
    Jump to a specific time in the audio player
    
    Args:
        time_seconds: Time to jump to in seconds
        auto_play: Whether to start playing after jumping
    """
    st.session_state.audio_jump_time = time_seconds
    st.session_state.audio_jump_trigger += 1
    
    # Inject JavaScript to control the player
    jump_script = f"""
    <script>
    (function() {{
        // Send jump command to the audio player
        window.postMessage({{
            type: 'streamlit-audio-command',
            command: 'jump',
            time: {time_seconds},
            play: {str(auto_play).lower()}
        }}, '*');
    }})();
    </script>
    """
    
    components.html(jump_script, height=0, key=f"jump_{st.session_state.audio_jump_trigger}")


def create_audio_control_interface():
    """Create an interface for testing audio controls"""
    st.markdown("### 🎵 Audio Control Test")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        jump_time = st.number_input(
            "Jump to (seconds)",
            min_value=0.0,
            max_value=3600.0,
            value=0.0,
            step=1.0,
            key="jump_time_input"
        )
    
    with col2:
        if st.button("⏯️ Jump & Play", key="jump_play"):
            jump_to_audio_time(jump_time, auto_play=True)
            st.success(f"Jumped to {jump_time}s")
    
    with col3:
        if st.button("⏸️ Jump (Paused)", key="jump_pause"):
            jump_to_audio_time(jump_time, auto_play=False)
            st.info(f"Jumped to {jump_time}s (paused)")


# Demo usage
if __name__ == "__main__":
    st.title("Enhanced Audio Player Demo")
    
    # Create test audio file path
    test_audio = "test_data/audio/business_meeting.wav"
    
    if st.checkbox("Show audio player"):
        render_enhanced_audio_player(test_audio, key="demo_player")
        
        # Control interface
        create_audio_control_interface()
        
        # Test jump buttons
        st.markdown("### Quick Jump Tests")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Jump to 0:30"):
                jump_to_audio_time(30)
        
        with col2:
            if st.button("Jump to 1:00"):
                jump_to_audio_time(60)
        
        with col3:
            if st.button("Jump to 1:30"):
                jump_to_audio_time(90)
        
        with col4:
            if st.button("Jump to 2:00"):
                jump_to_audio_time(120)