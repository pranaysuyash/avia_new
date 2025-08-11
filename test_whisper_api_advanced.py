"""
Comprehensive tests for Advanced Whisper API Configuration System

Tests cover all major components including configuration validation, API integration,
domain-specific presets, optimization strategies, and error handling.
"""

import pytest
import asyncio
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

from whisper_api_advanced import (
    WhisperAPIAdvanced,
    WhisperConfig,
    WhisperModel,
    ResponseFormat,
    LanguageCode,
    TranscriptionResult,
    create_medical_transcription_config,
    create_meeting_transcription_config,
    create_interview_transcription_config
)

class TestWhisperConfig:
    """Test cases for WhisperConfig class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = WhisperConfig()
        
        assert config.model == WhisperModel.WHISPER_1
        assert config.language == LanguageCode.AUTO
        assert config.prompt is None
        assert config.response_format == ResponseFormat.VERBOSE_JSON
        assert config.temperature == 0.0
        assert config.timestamp_granularities == ["segment"]
        assert config.custom_vocabulary == []
        assert config.confidence_threshold == 0.0
        assert config.enable_word_timestamps is True
        assert config.enable_segment_timestamps is True
    
    def test_custom_configuration(self):
        """Test custom configuration creation"""
        custom_vocab = ['test', 'vocabulary', 'words']
        
        config = WhisperConfig(
            model=WhisperModel.WHISPER_1,
            language=LanguageCode.ENGLISH,
            prompt="Test prompt",
            temperature=0.5,
            custom_vocabulary=custom_vocab,
            confidence_threshold=0.7,
            domain_context="test"
        )
        
        assert config.model == WhisperModel.WHISPER_1
        assert config.language == LanguageCode.ENGLISH
        assert config.prompt == "Test prompt"
        assert config.temperature == 0.5
        assert config.custom_vocabulary == custom_vocab
        assert config.confidence_threshold == 0.7
        assert config.domain_context == "test"
    
    def test_temperature_validation(self):
        """Test temperature validation"""
        # Valid temperatures
        config1 = WhisperConfig(temperature=0.0)
        config2 = WhisperConfig(temperature=1.0)
        config3 = WhisperConfig(temperature=0.5)
        
        assert config1.temperature == 0.0
        assert config2.temperature == 1.0
        assert config3.temperature == 0.5
        
        # Invalid temperatures
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            WhisperConfig(temperature=-0.1)
        
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            WhisperConfig(temperature=1.1)
    
    def test_confidence_threshold_validation(self):
        """Test confidence threshold validation"""
        # Valid thresholds
        config1 = WhisperConfig(confidence_threshold=0.0)
        config2 = WhisperConfig(confidence_threshold=1.0)
        config3 = WhisperConfig(confidence_threshold=0.5)
        
        assert config1.confidence_threshold == 0.0
        assert config2.confidence_threshold == 1.0
        assert config3.confidence_threshold == 0.5
        
        # Invalid thresholds
        with pytest.raises(ValueError, match="Confidence threshold must be between 0.0 and 1.0"):
            WhisperConfig(confidence_threshold=-0.1)
        
        with pytest.raises(ValueError, match="Confidence threshold must be between 0.0 and 1.0"):
            WhisperConfig(confidence_threshold=1.1)
    
    def test_to_api_params(self):
        """Test conversion to API parameters"""
        config = WhisperConfig(
            model=WhisperModel.WHISPER_1,
            language=LanguageCode.ENGLISH,
            prompt="Test prompt",
            temperature=0.3,
            response_format=ResponseFormat.JSON,
            timestamp_granularities=["word", "segment"]
        )
        
        params = config.to_api_params()
        
        assert params["model"] == "whisper-1"
        assert params["language"] == "en"
        assert params["temperature"] == 0.3
        assert params["response_format"] == "json"
        assert params["timestamp_granularities"] == ["word", "segment"]
        assert "prompt" in params
    
    def test_enhanced_prompt_building(self):
        """Test enhanced prompt building with context and vocabulary"""
        config = WhisperConfig(
            prompt="Base prompt",
            domain_context="medical",
            speaker_context="Dr. Smith",
            content_type="consultation",
            custom_vocabulary=["diagnosis", "treatment", "medication"]
        )
        
        enhanced_prompt = config._build_enhanced_prompt()
        
        assert "Base prompt" in enhanced_prompt
        assert "Domain: medical" in enhanced_prompt
        assert "Speaker: Dr. Smith" in enhanced_prompt
        assert "Content type: consultation" in enhanced_prompt
        assert "diagnosis, treatment, medication" in enhanced_prompt
    
    def test_auto_language_detection(self):
        """Test auto language detection handling"""
        config = WhisperConfig(language=LanguageCode.AUTO)
        params = config.to_api_params()
        
        # Auto language should not be included in API params
        assert "language" not in params

class TestTranscriptionResult:
    """Test cases for TranscriptionResult class"""
    
    def test_default_result(self):
        """Test default transcription result"""
        result = TranscriptionResult(text="Test transcription")
        
        assert result.text == "Test transcription"
        assert result.language is None
        assert result.duration is None
        assert result.segments == []
        assert result.words == []
        assert result.confidence_scores == {}
        assert result.processing_time == 0.0
        assert result.metadata == {}
    
    def test_result_with_data(self):
        """Test transcription result with full data"""
        segments = [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "Hello world", "avg_logprob": -0.3}
        ]
        words = [
            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.95},
            {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.92}
        ]
        
        result = TranscriptionResult(
            text="Hello world",
            language="en",
            duration=2.0,
            segments=segments,
            words=words,
            processing_time=1.5
        )
        
        assert result.text == "Hello world"
        assert result.language == "en"
        assert result.duration == 2.0
        assert len(result.segments) == 1
        assert len(result.words) == 2
        assert result.processing_time == 1.5
    
    def test_average_confidence_calculation(self):
        """Test average confidence calculation"""
        words = [
            {"word": "Hello", "confidence": 0.9},
            {"word": "world", "confidence": 0.8},
            {"word": "test", "confidence": 0.7}
        ]
        
        result = TranscriptionResult(text="Hello world test", words=words)
        avg_confidence = result.get_average_confidence()
        
        assert avg_confidence == pytest.approx(0.8, rel=1e-2)
    
    def test_average_confidence_no_words(self):
        """Test average confidence with no words"""
        result = TranscriptionResult(text="Test")
        avg_confidence = result.get_average_confidence()
        
        assert avg_confidence == 0.0
    
    def test_low_confidence_segments(self):
        """Test low confidence segment identification"""
        segments = [
            {"id": 0, "text": "High confidence", "avg_logprob": -0.2},
            {"id": 1, "text": "Low confidence", "avg_logprob": -0.8},
            {"id": 2, "text": "Medium confidence", "avg_logprob": -0.4}
        ]
        
        result = TranscriptionResult(text="Test", segments=segments)
        low_conf = result.get_low_confidence_segments(threshold=-0.5)
        
        assert len(low_conf) == 1
        assert low_conf[0]["text"] == "Low confidence"
    
    def test_confidence_filtering(self):
        """Test confidence-based filtering"""
        words = [
            {"word": "High", "confidence": 0.9},
            {"word": "Medium", "confidence": 0.6},
            {"word": "Low", "confidence": 0.3}
        ]
        
        result = TranscriptionResult(text="High Medium Low", words=words)
        filtered = result.filter_by_confidence(0.7)
        
        assert "High" in filtered.text
        assert "Medium" not in filtered.text
        assert "Low" not in filtered.text
        assert len(filtered.words) == 1

class TestWhisperAPIAdvanced:
    """Test cases for WhisperAPIAdvanced class"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Whisper API client"""
        with patch('whisper_api_advanced.OpenAI') as mock_openai:
            mock_openai.return_value.audio.transcriptions.create.return_value = Mock(
                text="Mock transcription result",
                language="en",
                duration=10.0,
                segments=[],
                words=[]
            )
            
            # Mock environment variable
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                client = WhisperAPIAdvanced()
                return client
    
    def test_initialization_with_api_key(self):
        """Test client initialization with API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('whisper_api_advanced.OpenAI'):
                client = WhisperAPIAdvanced()
                assert client.api_key == 'test_key'
    
    def test_initialization_without_api_key(self):
        """Test client initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                WhisperAPIAdvanced()
    
    def test_initialization_with_explicit_key(self):
        """Test client initialization with explicit API key"""
        with patch('whisper_api_advanced.OpenAI'):
            client = WhisperAPIAdvanced(api_key='explicit_key')
            assert client.api_key == 'explicit_key'
    
    def test_file_validation_success(self, mock_client):
        """Test successful file validation"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b"fake audio data")
            tmp_file_path = tmp_file.name
        
        try:
            # Should not raise exception
            mock_client._validate_audio_file(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_validation_not_found(self, mock_client):
        """Test file validation with non-existent file"""
        with pytest.raises(FileNotFoundError):
            mock_client._validate_audio_file("non_existent_file.mp3")
    
    def test_file_validation_unsupported_format(self, mock_client):
        """Test file validation with unsupported format"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp_file:
            tmp_file.write(b"fake data")
            tmp_file_path = tmp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                mock_client._validate_audio_file(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)
    
    def test_file_validation_too_large(self, mock_client):
        """Test file validation with file too large"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            # Create a file larger than 25MB
            large_data = b"x" * (26 * 1024 * 1024)  # 26MB
            tmp_file.write(large_data)
            tmp_file_path = tmp_file.name
        
        try:
            with pytest.raises(ValueError, match="File size.*exceeds maximum"):
                mock_client._validate_audio_file(tmp_file_path)
        finally:
            os.unlink(tmp_file_path)
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_client):
        """Test successful transcription"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b"fake audio data")
            tmp_file_path = tmp_file.name
        
        try:
            config = WhisperConfig()
            result = await mock_client.transcribe(tmp_file_path, config)
            
            assert isinstance(result, TranscriptionResult)
            assert result.text == "Mock transcription result"
            assert result.model_used == "whisper-1"
            assert result.processing_time > 0
        finally:
            os.unlink(tmp_file_path)
    
    @pytest.mark.asyncio
    async def test_transcribe_with_retry_success(self, mock_client):
        """Test transcription with retry - success case"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b"fake audio data")
            tmp_file_path = tmp_file.name
        
        try:
            config = WhisperConfig()
            result = await mock_client.transcribe_with_retry(tmp_file_path, config, max_retries=2)
            
            assert isinstance(result, TranscriptionResult)
            assert result.text == "Mock transcription result"
        finally:
            os.unlink(tmp_file_path)
    
    @pytest.mark.asyncio
    async def test_transcribe_with_retry_failure(self, mock_client):
        """Test transcription with retry - failure case"""
        # Mock the transcribe method to always fail
        mock_client.transcribe = AsyncMock(side_effect=Exception("API Error"))
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b"fake audio data")
            tmp_file_path = tmp_file.name
        
        try:
            config = WhisperConfig()
            
            with pytest.raises(Exception, match="API Error"):
                await mock_client.transcribe_with_retry(tmp_file_path, config, max_retries=2)
        finally:
            os.unlink(tmp_file_path)
    
    @pytest.mark.asyncio
    async def test_batch_transcribe(self, mock_client):
        """Test batch transcription"""
        # Create multiple temporary files
        temp_files = []
        for i in range(3):
            tmp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            tmp_file.write(b"fake audio data")
            temp_files.append(tmp_file.name)
            tmp_file.close()
        
        try:
            config = WhisperConfig()
            results = await mock_client.batch_transcribe(temp_files, config, max_concurrent=2)
            
            assert len(results) == 3
            assert all(isinstance(result, TranscriptionResult) for result in results)
        finally:
            for file_path in temp_files:
                os.unlink(file_path)
    
    def test_cache_key_generation(self, mock_client):
        """Test cache key generation"""
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
            tmp_file.write(b"fake audio data")
            tmp_file_path = tmp_file.name
        
        try:
            config = WhisperConfig()
            key1 = mock_client._generate_cache_key(tmp_file_path, config)
            key2 = mock_client._generate_cache_key(tmp_file_path, config)
            
            # Same file and config should generate same key
            assert key1 == key2
            
            # Different config should generate different key
            config2 = WhisperConfig(temperature=0.5)
            key3 = mock_client._generate_cache_key(tmp_file_path, config2)
            assert key1 != key3
        finally:
            os.unlink(tmp_file_path)
    
    def test_usage_statistics(self, mock_client):
        """Test usage statistics tracking"""
        initial_stats = mock_client.get_usage_statistics()
        
        assert 'total_requests' in initial_stats
        assert 'total_duration' in initial_stats
        assert 'total_cost_estimate' in initial_stats
        assert 'requests_by_model' in initial_stats
        assert 'average_processing_time' in initial_stats
        assert 'cache_size' in initial_stats
        assert 'cache_hit_rate' in initial_stats
    
    def test_cache_management(self, mock_client):
        """Test cache management"""
        # Add something to cache
        mock_client.cache['test_key'] = 'test_value'
        
        stats_before = mock_client.get_usage_statistics()
        assert stats_before['cache_size'] == 1
        
        # Clear cache
        mock_client.clear_cache()
        
        stats_after = mock_client.get_usage_statistics()
        assert stats_after['cache_size'] == 0

class TestDomainSpecificConfigs:
    """Test cases for domain-specific configuration presets"""
    
    def test_medical_transcription_config(self):
        """Test medical transcription configuration"""
        config = create_medical_transcription_config(
            custom_vocabulary=['stethoscope', 'diagnosis'],
            speaker_context="Dr. Smith and Patient"
        )
        
        assert config.domain_context == "medical"
        assert config.temperature == 0.1
        assert config.confidence_threshold == 0.8
        assert 'stethoscope' in config.custom_vocabulary
        assert 'diagnosis' in config.custom_vocabulary
        assert 'medication' in config.custom_vocabulary  # Default medical vocab
        assert config.speaker_context == "Dr. Smith and Patient"
        assert "medical conversation" in config.prompt.lower()
    
    def test_meeting_transcription_config(self):
        """Test meeting transcription configuration"""
        participants = ["Alice", "Bob", "Carol"]
        config = create_meeting_transcription_config(
            participants=participants,
            meeting_type="quarterly review"
        )
        
        assert config.domain_context == "business"
        assert config.content_type == "quarterly review"
        assert "Alice, Bob, Carol" in config.speaker_context
        assert 'agenda' in config.custom_vocabulary
        assert 'action items' in config.custom_vocabulary
        assert "quarterly review" in config.prompt
    
    def test_interview_transcription_config(self):
        """Test interview transcription configuration"""
        config = create_interview_transcription_config(
            interviewer="Sarah Wilson",
            interviewee="John Doe",
            topic="software engineering"
        )
        
        assert config.domain_context == "interview"
        assert config.content_type == "interview"
        assert "Sarah Wilson" in config.speaker_context
        assert "John Doe" in config.speaker_context
        assert "software engineering" in config.prompt
        assert 'question' in config.custom_vocabulary
        assert 'experience' in config.custom_vocabulary

class TestConfigurationOptimization:
    """Test cases for configuration optimization"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client for optimization tests"""
        with patch('whisper_api_advanced.OpenAI'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                return WhisperAPIAdvanced()
    
    def test_optimize_for_quality(self, mock_client):
        """Test quality optimization"""
        base_config = WhisperConfig(
            temperature=0.5,
            confidence_threshold=0.3,
            response_format=ResponseFormat.TEXT
        )
        
        optimized = mock_client.optimize_config_for_quality(base_config)
        
        assert optimized.temperature == 0.0  # Lowest for consistency
        assert optimized.confidence_threshold == 0.7  # Higher threshold
        assert optimized.response_format == ResponseFormat.VERBOSE_JSON
        assert optimized.enable_word_timestamps is True
        assert "word" in optimized.timestamp_granularities
    
    def test_optimize_for_speed(self, mock_client):
        """Test speed optimization"""
        base_config = WhisperConfig(
            temperature=0.0,
            confidence_threshold=0.8,
            custom_vocabulary=['word1', 'word2', 'word3', 'word4', 'word5', 'word6'],
            response_format=ResponseFormat.VERBOSE_JSON
        )
        
        optimized = mock_client.optimize_config_for_speed(base_config)
        
        assert optimized.temperature == 0.3  # Higher for speed
        assert optimized.confidence_threshold == 0.3  # Lower threshold
        assert optimized.response_format == ResponseFormat.TEXT
        assert optimized.enable_word_timestamps is False
        assert len(optimized.custom_vocabulary) <= 10  # Limited vocabulary
    
    def test_create_domain_config(self, mock_client):
        """Test domain-specific configuration creation"""
        config = mock_client.create_domain_config(
            domain='medical',
            vocabulary=['custom_term1', 'custom_term2'],
            context_prompt="Custom medical context"
        )
        
        assert config.domain_context == 'medical'
        assert config.prompt == "Custom medical context"
        assert 'custom_term1' in config.custom_vocabulary
        assert 'custom_term2' in config.custom_vocabulary
        assert 'diagnosis' in config.custom_vocabulary  # Default medical terms
        assert config.temperature == 0.1  # Medical domain default
        assert config.confidence_threshold == 0.7
    
    def test_unknown_domain_config(self, mock_client):
        """Test configuration for unknown domain"""
        config = mock_client.create_domain_config(domain='unknown_domain')
        
        # Should fall back to business domain defaults
        assert config.domain_context == 'unknown_domain'
        assert config.temperature == 0.3  # Business default
        assert config.confidence_threshold == 0.5

class TestErrorHandling:
    """Test cases for error handling and edge cases"""
    
    def test_invalid_temperature_range(self):
        """Test invalid temperature values"""
        with pytest.raises(ValueError):
            WhisperConfig(temperature=-0.1)
        
        with pytest.raises(ValueError):
            WhisperConfig(temperature=1.1)
    
    def test_invalid_confidence_threshold(self):
        """Test invalid confidence threshold values"""
        with pytest.raises(ValueError):
            WhisperConfig(confidence_threshold=-0.1)
        
        with pytest.raises(ValueError):
            WhisperConfig(confidence_threshold=1.1)
    
    def test_empty_custom_vocabulary(self):
        """Test empty custom vocabulary handling"""
        config = WhisperConfig(custom_vocabulary=[])
        assert config.custom_vocabulary == []
        
        # Should not include empty vocabulary in prompt
        prompt = config._build_enhanced_prompt()
        assert "Key terms:" not in prompt
    
    def test_none_values_handling(self):
        """Test handling of None values in configuration"""
        config = WhisperConfig(
            prompt=None,
            domain_context=None,
            speaker_context=None,
            content_type=None
        )
        
        # Should handle None values gracefully
        prompt = config._build_enhanced_prompt()
        assert prompt == ""  # Should be empty when all context is None
    
    def test_large_vocabulary_handling(self):
        """Test handling of large custom vocabulary"""
        large_vocab = [f"term_{i}" for i in range(100)]
        config = WhisperConfig(custom_vocabulary=large_vocab)
        
        prompt = config._build_enhanced_prompt()
        # Should limit vocabulary in prompt to avoid length issues
        vocab_terms = prompt.split("Key terms: ")[1] if "Key terms: " in prompt else ""
        term_count = len(vocab_terms.split(", ")) if vocab_terms else 0
        assert term_count <= 20

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        with patch('whisper_api_advanced.OpenAI') as mock_openai:
            # Mock API response
            mock_response = Mock()
            mock_response.text = "This is a test transcription"
            mock_response.language = "en"
            mock_response.duration = 5.0
            mock_response.segments = [
                {"id": 0, "start": 0.0, "end": 5.0, "text": "This is a test transcription", "avg_logprob": -0.2}
            ]
            mock_response.words = [
                {"word": "This", "start": 0.0, "end": 0.5, "confidence": 0.95},
                {"word": "is", "start": 0.5, "end": 0.7, "confidence": 0.92},
                {"word": "a", "start": 0.7, "end": 0.8, "confidence": 0.88},
                {"word": "test", "start": 0.8, "end": 1.2, "confidence": 0.94},
                {"word": "transcription", "start": 1.2, "end": 2.0, "confidence": 0.96}
            ]
            
            mock_openai.return_value.audio.transcriptions.create.return_value = mock_response
            
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
                # Initialize client
                client = WhisperAPIAdvanced()
                
                # Create configuration
                config = WhisperConfig(
                    temperature=0.1,
                    custom_vocabulary=['test', 'transcription'],
                    confidence_threshold=0.9,
                    enable_word_timestamps=True
                )
                
                # Create temporary audio file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    tmp_file.write(b"fake audio data")
                    tmp_file_path = tmp_file.name
                
                try:
                    # Perform transcription
                    result = await client.transcribe(tmp_file_path, config)
                    
                    # Verify result
                    assert isinstance(result, TranscriptionResult)
                    assert result.text == "This is a test transcription"
                    assert result.language == "en"
                    assert result.duration == 5.0
                    assert len(result.segments) == 1
                    assert len(result.words) == 5
                    assert result.model_used == "whisper-1"
                    assert result.config_used == config
                    
                    # Test confidence filtering
                    filtered_result = result.filter_by_confidence(0.9)
                    high_conf_words = [w for w in result.words if w['confidence'] >= 0.9]
                    assert len(filtered_result.words) == len(high_conf_words)
                    
                    # Verify filtered text contains only high confidence words
                    expected_filtered_text = " ".join([w['word'] for w in high_conf_words])
                    assert filtered_result.text == expected_filtered_text
                    
                    # Test usage statistics
                    stats = client.get_usage_statistics()
                    assert stats['total_requests'] == 1
                    assert stats['total_duration'] == 5.0
                    
                finally:
                    os.unlink(tmp_file_path)
    
    def test_configuration_serialization(self):
        """Test configuration serialization and deserialization"""
        config = WhisperConfig(
            model=WhisperModel.WHISPER_1,
            language=LanguageCode.ENGLISH,
            prompt="Test prompt",
            temperature=0.3,
            custom_vocabulary=['test', 'vocab'],
            confidence_threshold=0.7,
            domain_context="test"
        )
        
        # Convert to API params (simulates serialization)
        api_params = config.to_api_params()
        
        # Verify all important parameters are included
        assert api_params['model'] == 'whisper-1'
        assert api_params['language'] == 'en'
        assert api_params['temperature'] == 0.3
        assert 'prompt' in api_params
        
        # Verify enhanced prompt includes vocabulary
        assert 'test, vocab' in api_params['prompt']

def test_model_enum_properties():
    """Test WhisperModel enum properties"""
    model = WhisperModel.WHISPER_1
    
    assert model.value == "whisper-1"
    assert model.max_file_size_mb == 25
    assert 'mp3' in model.supported_formats
    assert 'wav' in model.supported_formats
    assert 'mp4' in model.supported_formats

def test_response_format_enum():
    """Test ResponseFormat enum values"""
    assert ResponseFormat.JSON.value == "json"
    assert ResponseFormat.TEXT.value == "text"
    assert ResponseFormat.SRT.value == "srt"
    assert ResponseFormat.VERBOSE_JSON.value == "verbose_json"
    assert ResponseFormat.VTT.value == "vtt"

def test_language_code_enum():
    """Test LanguageCode enum values"""
    assert LanguageCode.AUTO.value is None
    assert LanguageCode.ENGLISH.value == "en"
    assert LanguageCode.SPANISH.value == "es"
    assert LanguageCode.FRENCH.value == "fr"
    assert LanguageCode.GERMAN.value == "de"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])