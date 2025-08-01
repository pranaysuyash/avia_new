# Unit tests for Text-to-Speech module

import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from tts import (
    synthesize_speech, list_available_voices, estimate_synthesis_cost,
    get_voice_by_name, validate_voice_settings, cleanup_tts_files,
    DEFAULT_VOICE_ID, DEFAULT_VOICE_SETTINGS, VOICE_PRESETS
)
from errors import TTSError, ErrorCode
from elevenlabs import VoiceSettings

class TestTTSModule:
    """Test cases for TTS functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_text = "Hello, this is a test of the text-to-speech system."
        self.mock_audio_data = b"fake_audio_data"
        
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    @patch("tts._get_elevenlabs_client")
    @patch("tts.ensure_temp_directory")
    @patch("builtins.open", new_callable=mock_open)
    @patch("time.time", return_value=1234567890)
    def test_synthesize_speech_success(self, mock_time, mock_file, mock_ensure_temp, mock_client):
        """Test successful speech synthesis"""
        # Setup mocks
        mock_tts_client = MagicMock()
        mock_tts_client.convert.return_value = [self.mock_audio_data]
        mock_client.return_value.text_to_speech = mock_tts_client
        mock_ensure_temp.return_value = "temp"
        
        # Test synthesis
        result = synthesize_speech(self.test_text)
        
        # Verify results
        assert result == "temp/tts_output_1234567890.mp3"
        mock_tts_client.convert.assert_called_once()
        mock_file.assert_called_once_with("temp/tts_output_1234567890.mp3", "wb")
        mock_file().write.assert_called_once_with(self.mock_audio_data)
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    @patch("tts._get_elevenlabs_client")
    @patch("tts.ensure_temp_directory")
    @patch("builtins.open", new_callable=mock_open)
    def test_synthesize_speech_custom_voice(self, mock_file, mock_ensure_temp, mock_client):
        """Test speech synthesis with custom voice settings"""
        mock_tts_client = MagicMock()
        mock_tts_client.convert.return_value = [self.mock_audio_data]
        mock_client.return_value.text_to_speech = mock_tts_client
        mock_ensure_temp.return_value = "temp"
        
        custom_settings = VoiceSettings(stability=0.5, similarity_boost=0.8)
        custom_voice_id = "custom_voice_123"
        
        result = synthesize_speech(
            self.test_text, 
            voice_id=custom_voice_id,
            voice_settings=custom_settings,
            output_format="wav"
        )
        
        assert result.endswith(".wav")
        mock_tts_client.convert.assert_called_once()
        
        # Check that custom voice was used
        call_args = mock_tts_client.convert.call_args
        assert call_args[1]["voice_id"] == custom_voice_id
    
    def test_synthesize_speech_no_api_key(self):
        """Test synthesis fails without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(TTSError, match="ELEVENLABS_API_KEY environment variable not set"):
                synthesize_speech(self.test_text)
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    def test_synthesize_speech_empty_text(self):
        """Test synthesis fails with empty text"""
        with pytest.raises(TTSError, match="Text cannot be empty"):
            synthesize_speech("")
        
        with pytest.raises(TTSError, match="Text cannot be empty"):
            synthesize_speech("   ")
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    def test_synthesize_speech_text_too_long(self):
        """Test synthesis fails with text too long"""
        long_text = "a" * 5001  # Exceeds 5000 character limit
        with pytest.raises(TTSError, match="Text too long"):
            synthesize_speech(long_text)
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    @patch("tts._get_elevenlabs_client", side_effect=Exception("API Error"))
    def test_synthesize_speech_api_error(self, mock_client):
        """Test synthesis handles API errors gracefully"""
        with pytest.raises(TTSError, match="Speech synthesis failed"):
            synthesize_speech(self.test_text)
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    @patch("tts._get_elevenlabs_client")
    def test_list_available_voices_success(self, mock_client):
        """Test successful voice listing"""
        # Mock voice data
        mock_voice = MagicMock()
        mock_voice.voice_id = "voice_123"
        mock_voice.name = "Test Voice"
        mock_voice.category = "premade"
        mock_voice.description = "A test voice"
        mock_voice.preview_url = "http://example.com/preview.mp3"
        mock_voice.available_for_tiers = ["free", "starter"]
        mock_voice.settings = MagicMock()
        mock_voice.settings.stability = 0.75
        mock_voice.settings.similarity_boost = 0.8
        
        mock_voices_response = MagicMock()
        mock_voices_response.voices = [mock_voice]
        mock_client.return_value.voices.get_all.return_value = mock_voices_response
        
        result = list_available_voices()
        
        assert len(result) == 1
        voice = result[0]
        assert voice["voice_id"] == "voice_123"
        assert voice["name"] == "Test Voice"
        assert voice["category"] == "premade"
        assert voice["description"] == "A test voice"
        assert voice["settings"]["stability"] == 0.75
        assert voice["settings"]["similarity_boost"] == 0.8
    
    @patch.dict(os.environ, {"ELEVENLABS_API_KEY": "test_api_key"})
    @patch("tts._get_elevenlabs_client", side_effect=Exception("API Error"))
    def test_list_available_voices_error(self, mock_client):
        """Test voice listing handles API errors"""
        with pytest.raises(TTSError, match="Failed to list voices"):
            list_available_voices()
    
    def test_estimate_synthesis_cost(self):
        """Test cost estimation calculation"""
        # Test with known text length
        text_1000_chars = "a" * 1000
        cost = estimate_synthesis_cost(text_1000_chars)
        assert cost == 0.30  # $0.30 per 1K characters
        
        text_500_chars = "a" * 500
        cost = estimate_synthesis_cost(text_500_chars)
        assert cost == 0.15  # Half the cost
        
        empty_text = ""
        cost = estimate_synthesis_cost(empty_text)
        assert cost == 0.0
    
    @patch("tts.list_available_voices")
    def test_get_voice_by_name_found(self, mock_list_voices):
        """Test finding voice by name"""
        mock_voices = [
            {"name": "Rachel", "voice_id": "voice_123"},
            {"name": "Domi", "voice_id": "voice_456"}
        ]
        mock_list_voices.return_value = mock_voices
        
        result = get_voice_by_name("Rachel")
        assert result is not None
        assert result["voice_id"] == "voice_123"
        
        # Test case insensitive
        result = get_voice_by_name("rachel")
        assert result is not None
        assert result["voice_id"] == "voice_123"
    
    @patch("tts.list_available_voices")
    def test_get_voice_by_name_not_found(self, mock_list_voices):
        """Test voice not found by name"""
        mock_voices = [
            {"name": "Rachel", "voice_id": "voice_123"}
        ]
        mock_list_voices.return_value = mock_voices
        
        result = get_voice_by_name("NonExistent")
        assert result is None
    
    @patch("tts.list_available_voices", side_effect=TTSError("API Error", ErrorCode.API_SERVICE_UNAVAILABLE, "Failed to list voices"))
    def test_get_voice_by_name_api_error(self, mock_list_voices):
        """Test voice search handles API errors"""
        result = get_voice_by_name("Rachel")
        assert result is None
    
    def test_validate_voice_settings_valid(self):
        """Test voice settings validation with valid input"""
        settings_dict = {
            "stability": 0.8,
            "similarity_boost": 0.7,
            "style": 0.1,
            "use_speaker_boost": True
        }
        
        result = validate_voice_settings(settings_dict)
        assert isinstance(result, VoiceSettings)
        assert result.stability == 0.8
        assert result.similarity_boost == 0.7
        assert result.style == 0.1
        assert result.use_speaker_boost == True
    
    def test_validate_voice_settings_defaults(self):
        """Test voice settings validation with defaults"""
        settings_dict = {}
        
        result = validate_voice_settings(settings_dict)
        assert isinstance(result, VoiceSettings)
        assert result.stability == 0.75
        assert result.similarity_boost == 0.75
        assert result.style == 0.0
        assert result.use_speaker_boost == True
    
    def test_validate_voice_settings_invalid_range(self):
        """Test voice settings validation with invalid ranges"""
        # Test stability out of range
        with pytest.raises(TTSError, match="Stability must be between 0.0 and 1.0"):
            validate_voice_settings({"stability": 1.5})
        
        with pytest.raises(TTSError, match="Stability must be between 0.0 and 1.0"):
            validate_voice_settings({"stability": -0.1})
        
        # Test similarity_boost out of range
        with pytest.raises(TTSError, match="Similarity boost must be between 0.0 and 1.0"):
            validate_voice_settings({"similarity_boost": 1.1})
        
        # Test style out of range
        with pytest.raises(TTSError, match="Style must be between 0.0 and 1.0"):
            validate_voice_settings({"style": -0.5})
    
    @patch("pathlib.Path.glob")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("time.time", return_value=1000000)
    @patch("tts.cleanup_file")
    def test_cleanup_tts_files(self, mock_cleanup, mock_time, mock_exists, mock_glob):
        """Test TTS file cleanup"""
        # Mock old file
        old_file = MagicMock()
        old_file.stat().st_mtime = 900000  # 100000 seconds old
        old_file.__str__ = MagicMock(return_value="temp/tts_output_123.mp3")
        
        # Mock recent file
        recent_file = MagicMock()
        recent_file.stat().st_mtime = 999000  # 1000 seconds old
        recent_file.__str__ = MagicMock(return_value="temp/tts_output_456.mp3")
        
        mock_glob.return_value = [old_file, recent_file]
        
        # Clean files older than 1 hour (3600 seconds)
        cleanup_tts_files(max_age_hours=1)
        
        # Only old file should be cleaned
        mock_cleanup.assert_called_once_with("temp/tts_output_123.mp3")
    
    def test_voice_presets_structure(self):
        """Test that voice presets are properly structured"""
        assert "professional" in VOICE_PRESETS
        assert "conversational" in VOICE_PRESETS
        assert "narrative" in VOICE_PRESETS
        
        for preset_name, preset_config in VOICE_PRESETS.items():
            assert "voice_id" in preset_config
            assert "settings" in preset_config
            assert isinstance(preset_config["settings"], VoiceSettings)
    
    def test_default_constants(self):
        """Test default constants are properly defined"""
        assert DEFAULT_VOICE_ID is not None
        assert isinstance(DEFAULT_VOICE_SETTINGS, VoiceSettings)
        assert 0.0 <= DEFAULT_VOICE_SETTINGS.stability <= 1.0
        assert 0.0 <= DEFAULT_VOICE_SETTINGS.similarity_boost <= 1.0


class TestTTSIntegration:
    """Integration tests for TTS module (require API key)"""
    
    @pytest.mark.skipif(
        not os.getenv("ELEVENLABS_API_KEY"),
        reason="ELEVENLABS_API_KEY not set"
    )
    def test_real_api_voice_listing(self):
        """Test real API voice listing (requires API key)"""
        try:
            voices = list_available_voices()
            assert len(voices) > 0
            
            # Check voice structure
            voice = voices[0]
            required_fields = ["voice_id", "name", "category", "description"]
            for field in required_fields:
                assert field in voice
                
        except TTSError as e:
            pytest.skip(f"API test failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("ELEVENLABS_API_KEY"),
        reason="ELEVENLABS_API_KEY not set"
    )
    def test_real_api_synthesis(self):
        """Test real API synthesis (requires API key)"""
        try:
            test_text = "This is a test of the ElevenLabs API integration."
            result_path = synthesize_speech(test_text)
            
            # Verify file was created
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0
            
            # Clean up
            os.remove(result_path)
            
        except TTSError as e:
            pytest.skip(f"API test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])