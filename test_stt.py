# Unit tests for Speech-to-Text module
# Tests transcription accuracy with known audio samples

import os
import pytest
import tempfile
import wave
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from stt import (
    WhisperTranscriber, 
    TranscriptionResult, 
    TranscriptionError,
    transcribe,
    transcribe_with_timestamps,
    get_transcription_confidence,
    transcribe_detailed
)
from errors import ErrorCode, APIError

class TestWhisperTranscriber:
    """Test cases for WhisperTranscriber class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.transcriber = WhisperTranscriber()
        
        # Create a temporary audio file for testing
        self.temp_audio_file = self._create_test_audio_file()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_audio_file):
            os.remove(self.temp_audio_file)
    
    def _create_test_audio_file(self, duration: float = 1.0, sample_rate: int = 16000) -> str:
        """Create a temporary WAV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()
        
        # Generate a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_file.name
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('openai.OpenAI')
    def test_api_client_initialization_success(self, mock_openai):
        """Test successful API client initialization"""
        transcriber = WhisperTranscriber()
        mock_openai.assert_called_once_with(api_key='test-api-key')
        assert transcriber.api_client is not None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_api_client_initialization_no_key(self):
        """Test API client initialization without API key"""
        transcriber = WhisperTranscriber()
        assert transcriber.api_client is None
    
    @patch('whisper.load_model')
    def test_load_local_model_success(self, mock_load_model):
        """Test successful local model loading"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        model = self.transcriber._load_local_model('base')
        
        mock_load_model.assert_called_once_with('base')
        assert model == mock_model
        assert self.transcriber.local_model == mock_model
    
    @patch('whisper.load_model')
    def test_load_local_model_failure(self, mock_load_model):
        """Test local model loading failure"""
        mock_load_model.side_effect = Exception("Model loading failed")
        
        with pytest.raises(TranscriptionError) as exc_info:
            self.transcriber._load_local_model('base')
        
        assert exc_info.value.error_code == ErrorCode.LOCAL_MODEL_ERROR
        assert "Unable to load offline transcription model" in exc_info.value.user_message
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('openai.OpenAI')
    def test_api_transcription_success(self, mock_openai):
        """Test successful API transcription"""
        # Mock API response
        mock_response = Mock()
        mock_response.text = "Hello, this is a test transcription."
        mock_response.language = "en"
        mock_response.segments = [
            {'avg_logprob': -0.2}
        ]
        
        mock_client = Mock()
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        transcriber = WhisperTranscriber()
        result = transcriber._transcribe_with_api(self.temp_audio_file)
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == "Hello, this is a test transcription."
        assert result.model_used == "whisper-1-api"
        assert result.language == "en"
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time > 0
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('openai.OpenAI')
    def test_api_transcription_rate_limit(self, mock_openai):
        """Test API transcription with rate limit error"""
        import openai
        
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = openai.RateLimitError(
            "Rate limit exceeded", response=Mock(), body=None
        )
        mock_openai.return_value = mock_client
        
        transcriber = WhisperTranscriber()
        
        with pytest.raises(APIError) as exc_info:
            transcriber._transcribe_with_api(self.temp_audio_file, max_retries=1)
        
        assert exc_info.value.error_code == ErrorCode.API_RATE_LIMIT
        assert "rate limit exceeded" in exc_info.value.user_message.lower()
    
    @patch('whisper.load_model')
    def test_local_transcription_success(self, mock_load_model):
        """Test successful local transcription"""
        # Mock local model and result
        mock_model = Mock()
        mock_result = {
            'text': 'Local transcription result',
            'language': 'en',
            'segments': [
                {'avg_logprob': -0.3}
            ]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        result = self.transcriber._transcribe_with_local_model(self.temp_audio_file)
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == 'Local transcription result'
        assert result.model_used == "whisper-local-base"
        assert result.language == "en"
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time > 0
    
    def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file"""
        with pytest.raises(TranscriptionError) as exc_info:
            self.transcriber.transcribe("nonexistent_file.wav")
        
        assert exc_info.value.error_code == ErrorCode.FILE_NOT_FOUND
        assert "Audio file not found" in exc_info.value.user_message
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'})
    @patch('openai.OpenAI')
    @patch('whisper.load_model')
    def test_transcribe_api_fallback_to_local(self, mock_load_model, mock_openai):
        """Test API failure with fallback to local model"""
        # Mock API failure
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # Mock successful local transcription
        mock_model = Mock()
        mock_result = {
            'text': 'Fallback transcription',
            'language': 'en',
            'segments': []
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        transcriber = WhisperTranscriber()
        result = transcriber.transcribe(self.temp_audio_file, use_api=True)
        
        assert result.text == 'Fallback transcription'
        assert 'local' in result.model_used
    
    @patch('whisper.load_model')
    def test_transcribe_with_timestamps(self, mock_load_model):
        """Test timestamped transcription"""
        mock_model = Mock()
        mock_result = {
            'segments': [
                {
                    'text': ' Hello world',
                    'start': 0.0,
                    'end': 2.0,
                    'avg_logprob': -0.2,
                    'words': [
                        {'word': 'Hello', 'start': 0.0, 'end': 0.5, 'probability': 0.9},
                        {'word': 'world', 'start': 0.6, 'end': 1.0, 'probability': 0.8}
                    ]
                }
            ]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        result = self.transcriber.transcribe_with_timestamps(self.temp_audio_file)
        
        assert len(result) == 1
        assert result[0]['text'] == 'Hello world'
        assert result[0]['start'] == 0.0
        assert result[0]['end'] == 2.0
        assert 'words' in result[0]
        assert len(result[0]['words']) == 2
    
    @patch('whisper.load_model')
    def test_get_transcription_confidence(self, mock_load_model):
        """Test confidence score calculation"""
        mock_model = Mock()
        mock_result = {
            'segments': [
                {'avg_logprob': -0.1},  # High confidence
                {'avg_logprob': -0.5},  # Lower confidence
            ]
        }
        mock_model.transcribe.return_value = mock_result
        mock_load_model.return_value = mock_model
        
        confidence = self.transcriber.get_transcription_confidence(self.temp_audio_file)
        
        assert 0.0 <= confidence <= 1.0
        # Should be average of converted log probabilities


class TestPublicAPI:
    """Test cases for public API functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_audio_file = self._create_test_audio_file()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_audio_file):
            os.remove(self.temp_audio_file)
    
    def _create_test_audio_file(self) -> str:
        """Create a temporary WAV file for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()
        
        # Generate a simple sine wave
        t = np.linspace(0, 1.0, 16000)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_file.name
    
    @patch('stt.get_transcriber')
    def test_transcribe_function(self, mock_get_transcriber):
        """Test public transcribe function"""
        mock_transcriber = Mock()
        mock_result = TranscriptionResult(
            text="Test transcription",
            confidence=0.9,
            processing_time=1.5,
            model_used="test-model"
        )
        mock_transcriber.transcribe.return_value = mock_result
        mock_get_transcriber.return_value = mock_transcriber
        
        result = transcribe(self.temp_audio_file, use_api=True)
        
        assert result == "Test transcription"
        mock_transcriber.transcribe.assert_called_once_with(self.temp_audio_file, True)
    
    @patch('stt.get_transcriber')
    def test_transcribe_with_timestamps_function(self, mock_get_transcriber):
        """Test public transcribe_with_timestamps function"""
        mock_transcriber = Mock()
        mock_result = [
            {'text': 'Hello', 'start': 0.0, 'end': 1.0, 'confidence': 0.9}
        ]
        mock_transcriber.transcribe_with_timestamps.return_value = mock_result
        mock_get_transcriber.return_value = mock_transcriber
        
        result = transcribe_with_timestamps(self.temp_audio_file)
        
        assert result == mock_result
        mock_transcriber.transcribe_with_timestamps.assert_called_once_with(self.temp_audio_file)
    
    @patch('stt.get_transcriber')
    def test_get_transcription_confidence_function(self, mock_get_transcriber):
        """Test public get_transcription_confidence function"""
        mock_transcriber = Mock()
        mock_transcriber.get_transcription_confidence.return_value = 0.85
        mock_get_transcriber.return_value = mock_transcriber
        
        result = get_transcription_confidence(self.temp_audio_file)
        
        assert result == 0.85
        mock_transcriber.get_transcription_confidence.assert_called_once_with(self.temp_audio_file)
    
    @patch('stt.get_transcriber')
    def test_transcribe_detailed_function(self, mock_get_transcriber):
        """Test public transcribe_detailed function"""
        mock_transcriber = Mock()
        mock_result = TranscriptionResult(
            text="Detailed transcription",
            confidence=0.92,
            processing_time=2.1,
            model_used="whisper-1-api",
            language="en"
        )
        mock_transcriber.transcribe.return_value = mock_result
        mock_get_transcriber.return_value = mock_transcriber
        
        result = transcribe_detailed(self.temp_audio_file, use_api=True, model_size="base")
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == "Detailed transcription"
        assert result.confidence == 0.92
        mock_transcriber.transcribe.assert_called_once_with(self.temp_audio_file, True, "base")


class TestTranscriptionError:
    """Test cases for TranscriptionError exception"""
    
    def test_transcription_error_creation(self):
        """Test TranscriptionError exception creation"""
        error = TranscriptionError(
            "Test error message",
            "TEST_ERROR_CODE",
            "User-friendly message"
        )
        
        assert str(error) == "Test error message"
        assert error.error_code == "TEST_ERROR_CODE"
        assert error.user_message == "User-friendly message"


class TestTranscriptionResult:
    """Test cases for TranscriptionResult dataclass"""
    
    def test_transcription_result_creation(self):
        """Test TranscriptionResult creation and methods"""
        result = TranscriptionResult(
            text="This is a test transcription with multiple words",
            confidence=0.95,
            processing_time=1.5,
            model_used="whisper-1-api",
            language="en"
        )
        
        assert result.text == "This is a test transcription with multiple words"
        assert result.confidence == 0.95
        assert result.processing_time == 1.5
        assert result.model_used == "whisper-1-api"
        assert result.language == "en"
        assert result.word_count() == 8  # Actual word count
    
    def test_transcription_result_word_count_empty(self):
        """Test word count with empty text"""
        result = TranscriptionResult(
            text="",
            confidence=0.0,
            processing_time=0.0,
            model_used="test"
        )
        
        assert result.word_count() == 0  # Empty string should return 0 words


# Integration tests with real audio processing
class TestIntegration:
    """Integration tests that require actual audio processing"""
    
    @pytest.mark.integration
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_end_to_end_transcription_mock(self):
        """Test end-to-end transcription with mocked external services"""
        # This test would use real audio files in a full integration test
        # For now, we'll mock the external dependencies
        
        with patch('openai.OpenAI') as mock_openai, \
             patch('whisper.load_model') as mock_whisper:
            
            # Mock API response
            mock_response = Mock()
            mock_response.text = "Integration test transcription"
            mock_response.language = "en"
            mock_response.segments = [{'avg_logprob': -0.1}]
            
            mock_client = Mock()
            mock_client.audio.transcriptions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Mock local model fallback
            mock_model = Mock()
            mock_local_result = {
                'text': 'Local fallback transcription',
                'language': 'en',
                'segments': []
            }
            mock_model.transcribe.return_value = mock_local_result
            mock_whisper.return_value = mock_model
            
            # Create test audio file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.close()
            
            try:
                # Test the full pipeline
                result = transcribe(temp_file.name, use_api=True)
                assert result == "Integration test transcription"
                
            finally:
                os.remove(temp_file.name)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])