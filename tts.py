# Text-to-Speech Module
# Handles speech synthesis using ElevenLabs API

import os
import logging
import tempfile
import time
from typing import List, Dict, Optional
from pathlib import Path

from elevenlabs.client import ElevenLabs
from elevenlabs import text_to_speech, voices, Voice, VoiceSettings

from utils import ensure_temp_directory, cleanup_file
from errors import TTSError, APIError, handle_error, ErrorCode, create_api_key_error

logger = logging.getLogger(__name__)

# Default voice settings optimized for clarity
DEFAULT_VOICE_SETTINGS = VoiceSettings(
    stability=0.75,
    similarity_boost=0.75,
    style=0.0,
    use_speaker_boost=True
)

# Default voice ID (Rachel - clear, professional voice)
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# TTSError is now imported from errors module

def _get_elevenlabs_client():
    """Get ElevenLabs client with API key"""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise create_api_key_error("ElevenLabs")
    
    try:
        return ElevenLabs(api_key=api_key)
    except Exception as e:
        raise APIError(
            message=f"Failed to initialize ElevenLabs client: {e}",
            error_code=ErrorCode.API_AUTHENTICATION_ERROR,
            user_message="Failed to connect to ElevenLabs API.",
            api_name="ElevenLabs",
            suggestions=[
                "Check your ElevenLabs API key configuration",
                "Verify your internet connection",
                "Check ElevenLabs service status"
            ]
        )

def synthesize_speech(text: str, voice_id: str = DEFAULT_VOICE_ID, 
                     voice_settings: Optional[VoiceSettings] = None,
                     output_format: str = "mp3") -> str:
    """
    Convert text to speech and return audio file path
    
    Args:
        text: Text to synthesize
        voice_id: ElevenLabs voice ID to use
        voice_settings: Voice configuration settings
        output_format: Output audio format (mp3, wav)
    
    Returns:
        Path to generated audio file
        
    Raises:
        TTSError: If synthesis fails
    """
    try:
        # Get client
        client = _get_elevenlabs_client()
        
        # Validate input
        if not text or not text.strip():
            raise TTSError(
                "Text cannot be empty",
                ErrorCode.TTS_SYNTHESIS_ERROR,
                "Please provide text to convert to speech"
            )
        
        if len(text) > 5000:  # ElevenLabs character limit
            raise TTSError(
                "Text too long (max 5000 characters)",
                ErrorCode.TTS_TEXT_TOO_LONG,
                "Text must be less than 5000 characters. Please shorten your text."
            )
        
        # Use default voice settings if none provided
        if voice_settings is None:
            voice_settings = DEFAULT_VOICE_SETTINGS
        
        logger.info(f"Synthesizing speech for {len(text)} characters using voice {voice_id}")
        
        # Generate speech
        start_time = time.time()
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            voice_settings=voice_settings,
            model_id="eleven_monolingual_v1"
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Speech synthesis completed in {processing_time:.2f} seconds")
        
        # Save to temporary file
        ensure_temp_directory()
        timestamp = int(time.time())
        filename = f"tts_output_{timestamp}.{output_format}"
        output_path = os.path.join("temp", filename)
        
        # Convert audio generator to bytes
        audio_bytes = b"".join(audio)
        
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        logger.info(f"Audio saved to {output_path}")
        return output_path
        
    except Exception as e:
        error_msg = f"Speech synthesis failed: {str(e)}"
        logger.error(error_msg)
        raise TTSError(
            error_msg,
            ErrorCode.TTS_SYNTHESIS_ERROR,
            "Failed to generate speech. Please try again or use a different voice."
        ) from e

def list_available_voices() -> List[Dict]:
    """
    Get list of available voice options
    
    Returns:
        List of voice dictionaries with id, name, and description
        
    Raises:
        TTSError: If voice listing fails
    """
    try:
        client = _get_elevenlabs_client()
        
        logger.info("Fetching available voices from ElevenLabs")
        voice_list = client.voices.get_all()
        
        available_voices = []
        for voice in voice_list.voices:
            voice_info = {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": voice.category,
                "description": voice.description or "No description available",
                "preview_url": voice.preview_url if hasattr(voice, 'preview_url') else None,
                "available_for_tiers": voice.available_for_tiers if hasattr(voice, 'available_for_tiers') else [],
                "settings": {
                    "stability": voice.settings.stability if voice.settings else 0.75,
                    "similarity_boost": voice.settings.similarity_boost if voice.settings else 0.75
                }
            }
            available_voices.append(voice_info)
        
        logger.info(f"Found {len(available_voices)} available voices")
        return available_voices
        
    except Exception as e:
        error_msg = f"Failed to list voices: {str(e)}"
        logger.error(error_msg)
        raise TTSError(
            error_msg,
            ErrorCode.TTS_SYNTHESIS_ERROR,
            "Failed to generate speech. Please try again or use a different voice."
        ) from e

def get_voice_by_name(voice_name: str) -> Optional[Dict]:
    """
    Get voice information by name
    
    Args:
        voice_name: Name of the voice to find
        
    Returns:
        Voice dictionary if found, None otherwise
    """
    try:
        available_voices = list_available_voices()
        for voice in available_voices:
            if voice["name"].lower() == voice_name.lower():
                return voice
        return None
    except TTSError:
        return None

def estimate_synthesis_cost(text: str) -> float:
    """
    Estimate API cost for text synthesis
    
    Args:
        text: Text to estimate cost for
        
    Returns:
        Estimated cost in USD
    """
    # ElevenLabs pricing (as of 2024): ~$0.30 per 1K characters
    # This is an approximation and may vary based on subscription tier
    character_count = len(text)
    cost_per_1k_chars = 0.30
    estimated_cost = (character_count / 1000) * cost_per_1k_chars
    
    logger.info(f"Estimated cost for {character_count} characters: ${estimated_cost:.4f}")
    return estimated_cost

def get_synthesis_history() -> List[Dict]:
    """
    Get history of recent synthesis requests
    
    Returns:
        List of synthesis history items
        
    Raises:
        TTSError: If history retrieval fails
    """
    try:
        client = _get_elevenlabs_client()
        
        history = client.history.get_all()
        history_items = []
        
        for item in history.history[:10]:  # Get last 10 items
            history_item = {
                "history_item_id": item.history_item_id,
                "text": item.text,
                "voice_id": item.voice_id,
                "voice_name": item.voice_name,
                "date_unix": item.date_unix,
                "character_count": item.character_count,
                "state": item.state
            }
            history_items.append(history_item)
        
        return history_items
        
    except Exception as e:
        error_msg = f"Failed to get synthesis history: {str(e)}"
        logger.error(error_msg)
        raise TTSError(
            error_msg,
            ErrorCode.TTS_SYNTHESIS_ERROR,
            "Failed to generate speech. Please try again or use a different voice."
        ) from e

def validate_voice_settings(settings: Dict) -> VoiceSettings:
    """
    Validate and create VoiceSettings object
    
    Args:
        settings: Dictionary with voice settings
        
    Returns:
        VoiceSettings object
        
    Raises:
        TTSError: If settings are invalid
    """
    try:
        stability = settings.get("stability", 0.75)
        similarity_boost = settings.get("similarity_boost", 0.75)
        style = settings.get("style", 0.0)
        use_speaker_boost = settings.get("use_speaker_boost", True)
        
        # Validate ranges
        if not 0.0 <= stability <= 1.0:
            raise ValueError("Stability must be between 0.0 and 1.0")
        if not 0.0 <= similarity_boost <= 1.0:
            raise ValueError("Similarity boost must be between 0.0 and 1.0")
        if not 0.0 <= style <= 1.0:
            raise ValueError("Style must be between 0.0 and 1.0")
        
        return VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=use_speaker_boost
        )
        
    except Exception as e:
        raise TTSError(
            f"Invalid voice settings: {str(e)}",
            ErrorCode.TTS_VOICE_ERROR,
            "Invalid voice settings provided. Please check your settings."
        ) from e

def cleanup_tts_files(max_age_hours: int = 24):
    """
    Clean up old TTS files from temp directory
    
    Args:
        max_age_hours: Maximum age of files to keep in hours
    """
    try:
        temp_dir = Path("temp")
        if not temp_dir.exists():
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        for file_path in temp_dir.glob("tts_output_*.mp3"):
            if current_time - file_path.stat().st_mtime > max_age_seconds:
                cleanup_file(str(file_path))
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old TTS files")
            
    except Exception as e:
        logger.warning(f"Failed to cleanup TTS files: {str(e)}")

# Predefined voice configurations for common use cases
VOICE_PRESETS = {
    "professional": {
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "settings": VoiceSettings(stability=0.8, similarity_boost=0.7, style=0.0)
    },
    "conversational": {
        "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Domi
        "settings": VoiceSettings(stability=0.6, similarity_boost=0.8, style=0.2)
    },
    "narrative": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella
        "settings": VoiceSettings(stability=0.9, similarity_boost=0.6, style=0.1)
    }
}