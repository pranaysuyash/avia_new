"""
Unit Tests for Whisper Advanced Processor

This module contains comprehensive unit tests for the WhisperAdvancedProcessor
and related components, including configuration validation, model management,
and error handling scenarios.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json

from whisper_advanced_processor import (
    WhisperAdvancedProcessor,
    WhisperConfig,
    WhisperModel,
    TranscriptionResult,
    TranscriptionSegment,
    WordLevelTimestamp,
    LanguageDetectionResult,
    SpeakerDiarizationResult,
    ModelManager,
    create_high_accuracy_config,
    create_fast_processing_config,
    create_balanced_config
)

class TestWhisperConfig:
    """Test cases for WhisperConfig class"""
    
    def test_default_config_creation(self):
        """Test creating config with default values"""
        config = WhisperConfig()
        
        assert config.model_size == WhisperModel.BASE
        assert config.language is None
        assert config.task == "transcribe"
        assert config.temperature == 0.0
        assert config.best_of == 5
        assert config.beam_size == 5
        assert config.word_timestamps is True
        assert config.enable_vad is True
        assert config.enable_diarization is False
        assert config.max_speakers == 10
        assert config.custom_vocabulary == []
    
    def test_config_validation_temperature(self):
        """Test temperature validation"""
        # Valid temperature
        config = WhisperConfig(temperature=0.5)
        assert config.temperature == 0.5
        
        # Invalid temperature - too low
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            WhisperConfig(temperature=-0.1)
        
        # Invalid temperature - too high
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            WhisperConfig(temperature=1.1)
    
    def test_config_validation_best_of(self):
        """Test best_of validation"""
        # Valid best_of
        config = WhisperConfig(best_of=3)
        assert config.best_of == 3
        
        # Invalid best_of - too low
        with pytest.raises(ValueError, match="best_of must be between 1 and 10"):
            WhisperConfig(best_of=0)
        
        # Invalid best_of - too high
        with pytest.raises(ValueError, match="best_of must be between 1 and 10"):
            WhisperConfig(best_of=11)
    
    def test_config_validation_beam_size(self):
        """Test beam_size validation"""
        # Valid beam_size
        config = WhisperConfig(beam_size=3)
        assert config.beam_size == 3
        
        # Invalid beam_size - too low
        with pytest.raises(ValueError, match="beam_size must be between 1 and 10"):
            WhisperConfig(beam_size=0)
        
        # Invalid beam_size - too high
        with pytest.raises(ValueError, match="beam_size must be between 1 and 10"):
            WhisperConfig(beam_size=11)
    
    def test_config_validation_patience(self):
        """Test patience validation"""
        # Valid patience
        config = WhisperConfig(patience=1.5)
        assert config.patience == 1.5
        
        # Invalid patience - too low
        with pytest.raises(ValueError, match="patience must be between 0.0 and 2.0"):
            WhisperConfig(patience=-0.1)
        
        # Invalid patience - too high
        with pytest.raises(ValueError, match="patience must be between 0.0 and 2.0"):
            WhisperConfig(patience=2.1)
    
    def test_config_validation_max_speakers(self):
        """Test max_speakers validation"""
        # Valid max_speakers
        config = WhisperConfig(max_speakers=5)
        assert config.max_speakers == 5
        
        # Invalid max_speakers - too low
        with pytest.raises(ValueError, match="max_speakers must be between 1 and 20"):
            WhisperConfig(max_speakers=0)
        
        # Invalid max_speakers - too high
        with pytest.raises(ValueError, match="max_speakers must be between 1 and 20"):
            WhisperConfig(max_speakers=21)
    
    def test_config_validation_task(self):
        """Test task validation"""
        # Valid tasks
        config1 = WhisperConfig(task="transcribe")
        assert config1.task == "transcribe"
        
        config2 = WhisperConfig(task="translate")
        assert config2.task == "translate"
        
        # Invalid task
        with pytest.raises(ValueError, match="task must be 'transcribe' or 'translate'"):
            WhisperConfig(task="invalid_task")
    
    def test_config_to_dict(self):
        """Test converting config to dictionary"""
        config = WhisperConfig(
            model_size=WhisperModel.SMALL,
            temperature=0.2,
            custom_vocabulary=["test", "vocab"]
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['model_size'] == WhisperModel.SMALL
        assert config_dict['temperature'] == 0.2
        assert config_dict['custom_vocabulary'] == ["test", "vocab"]
    
    def test_config_to_legacy_config(self):
        """Test converting to legacy config format"""
        config = WhisperConfig(
            temperature=0.3,
            custom_vocabulary=["test"],
            domain_context="medical"
        )
        
        legacy_config = config.to_legacy_config()
        
        assert legacy_config.temperature == 0.3
        assert legacy_config.custom_vocabulary == ["test"]
        assert legacy_config.domain_context == "medical"

class TestWhisperModel:
    """Test cases for WhisperModel enum"""
    
    def test_model_properties(self):
        """Test model property methods"""
        tiny_model = WhisperModel.TINY
        
        assert tiny_model.parameters == "39M"
        assert tiny_model.vram_required == "~1GB"
        assert tiny_model.relative_speed == "~32x"
        assert "Real-time transcription" in tiny_model.use_cases
        
        large_model = WhisperModel.LARGE_V3
        
        assert large_model.parameters == "1550M"
        assert large_model.vram_required == "~10GB"
        assert large_model.relative_speed == "1x"
        assert "Maximum accuracy" in large_model.use_cases

class TestModelManager:
    """Test cases for ModelManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.model_manager = ModelManager(cache_dir=self.temp_dir)
    
    def test_model_manager_initialization(self):
        """Test ModelManager initialization"""
        assert os.path.exists(self.model_manager.cache_dir)
        assert self.model_manager.loaded_models == {}
        assert self.model_manager.performance_metrics['cache_hits'] == 0
        assert self.model_manager.performance_metrics['cache_misses'] == 0
    
    def test_load_model(self):
        """Test model loading"""
        model = self.model_manager.load_model(WhisperModel.BASE)
        
        assert model is not None
        assert model['name'] == 'base'
        assert model['size'] == '74M'
        assert 'loaded_at' in model
        
        # Test cache hit
        model2 = self.model_manager.load_model(WhisperModel.BASE)
        assert model2 == model
        assert self.model_manager.performance_metrics['cache_hits'] == 1
    
    def test_unload_model(self):
        """Test model unloading"""
        # Load a model first
        self.model_manager.load_model(WhisperModel.BASE)
        assert 'base' in self.model_manager.loaded_models
        
        # Unload the model
        self.model_manager.unload_model(WhisperModel.BASE)
        assert 'base' not in self.model_manager.loaded_models
    
    def test_get_optimal_model_speed(self):
        """Test optimal model selection for speed"""
        # Short audio - should use tiny
        model = self.model_manager.get_optimal_model(240, "speed")  # 4 minutes
        assert model == WhisperModel.TINY
        
        # Medium audio - should use base
        model = self.model_manager.get_optimal_model(900, "speed")  # 15 minutes
        assert model == WhisperModel.BASE
        
        # Long audio - should use small
        model = self.model_manager.get_optimal_model(2400, "speed")  # 40 minutes
        assert model == WhisperModel.SMALL
    
    def test_get_optimal_model_accuracy(self):
        """Test optimal model selection for accuracy"""
        # Short audio - should use large
        model = self.model_manager.get_optimal_model(300, "accuracy")  # 5 minutes
        assert model == WhisperModel.LARGE_V3
        
        # Medium audio - should use medium
        model = self.model_manager.get_optimal_model(1200, "accuracy")  # 20 minutes
        assert model == WhisperModel.MEDIUM
        
        # Long audio - should use small
        model = self.model_manager.get_optimal_model(2400, "accuracy")  # 40 minutes
        assert model == WhisperModel.SMALL
    
    def test_get_optimal_model_balanced(self):
        """Test optimal model selection for balanced"""
        # Short audio - should use base
        model = self.model_manager.get_optimal_model(240, "balanced")  # 4 minutes
        assert model == WhisperModel.BASE
        
        # Medium audio - should use small
        model = self.model_manager.get_optimal_model(900, "balanced")  # 15 minutes
        assert model == WhisperModel.SMALL
        
        # Long audio - should use base
        model = self.model_manager.get_optimal_model(2400, "balanced")  # 40 minutes
        assert model == WhisperModel.BASE
    
    def test_monitor_performance(self):
        """Test performance monitoring"""
        # Load some models
        self.model_manager.load_model(WhisperModel.BASE)
        self.model_manager.load_model(WhisperModel.SMALL)
        
        metrics = self.model_manager.monitor_performance()
        
        assert 'loaded_models' in metrics
        assert 'cache_hit_rate' in metrics
        assert 'total_memory_mb' in metrics
        assert 'average_load_time' in metrics
        assert len(metrics['loaded_models']) == 2
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Load some models
        self.model_manager.load_model(WhisperModel.BASE)
        self.model_manager.load_model(WhisperModel.SMALL)
        
        assert len(self.model_manager.loaded_models) == 2
        
        # Clear cache
        self.model_manager.clear_cache()
        
        assert len(self.model_manager.loaded_models) == 0

class TestWhisperAdvancedProcessor:
    """Test cases for WhisperAdvancedProcessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the API key
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('whisper_advanced_processor.WhisperAPIAdvanced'):
                self.processor = WhisperAdvancedProcessor()
    
    def test_processor_initialization(self):
        """Test processor initialization"""
        assert self.processor.api_key == 'test_key'
        assert self.processor.processing_stats['total_requests'] == 0
        assert self.processor.processing_stats['successful_requests'] == 0
        assert self.processor.processing_stats['failed_requests'] == 0
    
    def test_processor_initialization_no_api_key(self):
        """Test processor initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                WhisperAdvancedProcessor()
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        """Test successful transcription"""
        # Mock the whisper client
        mock_result = Mock()
        mock_result.text = "Test transcription"
        mock_result.language = "en"
        mock_result.duration = 10.0
        mock_result.processing_time = 2.0
        mock_result.segments = []
        mock_result.get_average_confidence = Mock(return_value=0.9)
        
        self.processor.whisper_client.transcribe = AsyncMock(return_value=mock_result)
        
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake audio data')
            temp_file_path = temp_file.name
        
        try:
            config = WhisperConfig(model_size=WhisperModel.BASE)
            result = await self.processor.transcribe(temp_file_path, config)
            
            assert isinstance(result, TranscriptionResult)
            assert result.text == "Test transcription"
            assert result.language == "en"
            assert result.duration == 10.0
            assert result.word_count == 2  # "Test transcription"
            assert result.model_used == "base"
            assert self.processor.processing_stats['successful_requests'] == 1
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_transcribe_failure(self):
        """Test transcription failure handling"""
        # Mock the whisper client to raise an exception
        self.processor.whisper_client.transcribe = AsyncMock(side_effect=Exception("API Error"))
        
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake audio data')
            temp_file_path = temp_file.name
        
        try:
            config = WhisperConfig(model_size=WhisperModel.BASE)
            
            with pytest.raises(Exception, match="API Error"):
                await self.processor.transcribe(temp_file_path, config)
            
            assert self.processor.processing_stats['failed_requests'] == 1
            assert 'Exception' in self.processor.processing_stats['error_types']
            
        finally:
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_detect_language(self):
        """Test language detection"""
        # Mock the transcribe method
        mock_result = TranscriptionResult(
            text="Hello world",
            language="en",
            duration=5.0,
            processing_time=1.0,
            model_used="base",
            word_count=2,
            confidence_score=0.9
        )
        
        self.processor.transcribe = AsyncMock(return_value=mock_result)
        
        # Create test audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake audio data')
            temp_file_path = temp_file.name
        
        try:
            result = await self.processor.detect_language(temp_file_path)
            
            assert isinstance(result, LanguageDetectionResult)
            assert result.detected_language == "en"
            assert result.language_probability == 0.9
            assert "en" in result.all_language_probs
            
        finally:
            os.unlink(temp_file_path)
    
    def test_create_optimized_config(self):
        """Test optimized configuration creation"""
        config = self.processor.create_optimized_config(
            audio_duration=600,  # 10 minutes
            quality_target="balanced",
            domain="medical",
            custom_vocabulary=["diagnosis", "treatment"]
        )
        
        assert isinstance(config, WhisperConfig)
        assert config.domain_context == "medical"
        assert "diagnosis" in config.custom_vocabulary
        assert "treatment" in config.custom_vocabulary
        # Should include medical domain vocabulary
        assert any("medication" in vocab for vocab in [config.custom_vocabulary])
    
    def test_get_processing_statistics(self):
        """Test processing statistics retrieval"""
        # Mock some processing stats
        self.processor.processing_stats['total_requests'] = 10
        self.processor.processing_stats['successful_requests'] = 8
        self.processor.processing_stats['total_processing_time'] = 50.0
        
        stats = self.processor.get_processing_statistics()
        
        assert 'total_requests' in stats
        assert 'successful_requests' in stats
        assert 'success_rate' in stats
        assert 'average_processing_time' in stats
        assert 'model_manager' in stats
        assert 'api_client' in stats
        
        assert stats['success_rate'] == 0.8
        assert stats['average_processing_time'] == 5.0
    
    def test_clear_caches(self):
        """Test cache clearing"""
        # This should not raise any exceptions
        self.processor.clear_caches()

class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_create_high_accuracy_config(self):
        """Test high accuracy configuration creation"""
        config = create_high_accuracy_config(
            model_size=WhisperModel.LARGE_V3,
            custom_vocabulary=["test", "vocab"]
        )
        
        assert config.model_size == WhisperModel.LARGE_V3
        assert config.temperature == 0.0
        assert config.beam_size == 5
        assert config.word_timestamps is True
        assert config.enable_vad is True
        assert config.enable_diarization is True
        assert config.custom_vocabulary == ["test", "vocab"]
    
    def test_create_fast_processing_config(self):
        """Test fast processing configuration creation"""
        config = create_fast_processing_config(
            model_size=WhisperModel.BASE,
            custom_vocabulary=["fast", "test"]
        )
        
        assert config.model_size == WhisperModel.BASE
        assert config.temperature == 0.3
        assert config.beam_size == 1
        assert config.word_timestamps is False
        assert config.enable_vad is False
        assert config.enable_diarization is False
        assert config.custom_vocabulary == ["fast", "test"]
    
    def test_create_balanced_config(self):
        """Test balanced configuration creation"""
        config = create_balanced_config(
            model_size=WhisperModel.SMALL,
            custom_vocabulary=["balanced", "test"]
        )
        
        assert config.model_size == WhisperModel.SMALL
        assert config.temperature == 0.1
        assert config.beam_size == 3
        assert config.word_timestamps is True
        assert config.enable_vad is True
        assert config.enable_diarization is False
        assert config.custom_vocabulary == ["balanced", "test"]

class TestDataModels:
    """Test cases for data model classes"""
    
    def test_transcription_segment_creation(self):
        """Test TranscriptionSegment creation"""
        words = [
            WordLevelTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordLevelTimestamp(word="world", start=0.6, end=1.0, confidence=0.8)
        ]
        
        segment = TranscriptionSegment(
            id=0,
            seek=0,
            start=0.0,
            end=1.0,
            text="Hello world",
            tokens=[1, 2],
            temperature=0.0,
            avg_logprob=-0.1,
            compression_ratio=1.5,
            no_speech_prob=0.1,
            confidence=0.85,
            words=words,
            speaker_id="speaker_1"
        )
        
        assert segment.id == 0
        assert segment.text == "Hello world"
        assert len(segment.words) == 2
        assert segment.speaker_id == "speaker_1"
        assert segment.confidence == 0.85
    
    def test_word_level_timestamp_creation(self):
        """Test WordLevelTimestamp creation"""
        word = WordLevelTimestamp(
            word="test",
            start=1.0,
            end=1.5,
            confidence=0.9
        )
        
        assert word.word == "test"
        assert word.start == 1.0
        assert word.end == 1.5
        assert word.confidence == 0.9
    
    def test_language_detection_result_creation(self):
        """Test LanguageDetectionResult creation"""
        result = LanguageDetectionResult(
            detected_language="en",
            language_probability=0.95,
            all_language_probs={"en": 0.95, "es": 0.03, "fr": 0.02}
        )
        
        assert result.detected_language == "en"
        assert result.language_probability == 0.95
        assert len(result.all_language_probs) == 3
        assert result.all_language_probs["en"] == 0.95
    
    def test_transcription_result_post_init(self):
        """Test TranscriptionResult post-initialization calculations"""
        segments = [
            TranscriptionSegment(
                id=0, seek=0, start=0.0, end=1.0, text="Hello",
                tokens=[1], temperature=0.0, avg_logprob=-0.1,
                compression_ratio=1.5, no_speech_prob=0.1, confidence=0.9
            ),
            TranscriptionSegment(
                id=1, seek=1, start=1.0, end=2.0, text="world",
                tokens=[2], temperature=0.0, avg_logprob=-0.2,
                compression_ratio=1.4, no_speech_prob=0.1, confidence=0.8
            )
        ]
        
        result = TranscriptionResult(
            text="Hello world",
            segments=segments,
            language="en",
            duration=2.0,
            processing_time=1.0,
            model_used="base"
        )
        
        # Test post-init calculations
        assert result.word_count == 2  # "Hello world"
        assert result.confidence_score == 0.85  # Average of 0.9 and 0.8

# Integration tests
class TestIntegration:
    """Integration test cases"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with patch('whisper_advanced_processor.WhisperAPIAdvanced') as mock_whisper:
                # Mock the API response
                mock_result = Mock()
                mock_result.text = "This is a test transcription"
                mock_result.language = "en"
                mock_result.duration = 15.0
                mock_result.processing_time = 3.0
                mock_result.segments = []
                mock_result.get_average_confidence = Mock(return_value=0.85)
                
                mock_whisper.return_value.transcribe = AsyncMock(return_value=mock_result)
                mock_whisper.return_value.get_usage_statistics = Mock(return_value={})
                
                # Initialize processor
                processor = WhisperAdvancedProcessor()
                
                # Create optimized config
                config = processor.create_optimized_config(
                    audio_duration=900,  # 15 minutes
                    quality_target="balanced",
                    domain="business",
                    custom_vocabulary=["revenue", "growth"]
                )
                
                # Create test audio file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file.write(b'fake audio data')
                    temp_file_path = temp_file.name
                
                try:
                    # Perform transcription
                    result = await processor.transcribe(temp_file_path, config)
                    
                    # Verify results
                    assert result.text == "This is a test transcription"
                    assert result.language == "en"
                    assert result.duration == 15.0
                    assert result.word_count == 5
                    assert result.model_used == "small"  # Should be small for balanced 15min audio
                    
                    # Check statistics
                    stats = processor.get_processing_statistics()
                    assert stats['successful_requests'] == 1
                    assert stats['total_requests'] == 1
                    assert stats['success_rate'] == 1.0
                    
                finally:
                    os.unlink(temp_file_path)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])