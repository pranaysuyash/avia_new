"""
Unit Tests for Whisper Audio Preprocessor

This module contains comprehensive unit tests for the AudioPreprocessor class
and related components, including audio processing, quality assessment, and
Whisper optimization functionality.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import soundfile as sf
from pathlib import Path

from whisper_audio_preprocessor import (
    AudioPreprocessor,
    AudioConfig,
    AudioFormat,
    ProcessingMode,
    AudioPreprocessingResult,
    create_fast_config,
    create_quality_config,
    create_balanced_config
)

from audio_enhancement_pipeline import AudioQualityMetrics
from whisper_advanced_exceptions import AudioFileError, ProcessingError

class TestAudioConfig:
    """Test cases for AudioConfig class"""
    
    def test_default_config_creation(self):
        """Test creating config with default values"""
        config = AudioConfig()
        
        assert config.target_sample_rate == 16000
        assert config.target_channels == 1
        assert config.target_bit_depth == 16
        assert config.enable_noise_reduction is True
        assert config.enable_normalization is True
        assert config.enable_enhancement is True
        assert config.enable_repair is True
        assert config.processing_mode == ProcessingMode.BALANCED
        assert config.min_snr_db == 10.0
        assert config.min_quality_score == 50.0
        assert config.max_duration_seconds == 1800.0
    
    def test_custom_config_creation(self):
        """Test creating config with custom values"""
        config = AudioConfig(
            target_sample_rate=22050,
            processing_mode=ProcessingMode.QUALITY,
            enable_noise_reduction=False,
            min_snr_db=15.0
        )
        
        assert config.target_sample_rate == 22050
        assert config.processing_mode == ProcessingMode.QUALITY
        assert config.enable_noise_reduction is False
        assert config.min_snr_db == 15.0

class TestAudioFormat:
    """Test cases for AudioFormat enum"""
    
    def test_audio_format_values(self):
        """Test AudioFormat enum values"""
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.M4A.value == "m4a"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.OGG.value == "ogg"
        assert AudioFormat.AAC.value == "aac"
        assert AudioFormat.WEBM.value == "webm"

class TestProcessingMode:
    """Test cases for ProcessingMode enum"""
    
    def test_processing_mode_values(self):
        """Test ProcessingMode enum values"""
        assert ProcessingMode.FAST.value == "fast"
        assert ProcessingMode.BALANCED.value == "balanced"
        assert ProcessingMode.QUALITY.value == "quality"
        assert ProcessingMode.CUSTOM.value == "custom"

class TestAudioPreprocessor:
    """Test cases for AudioPreprocessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the enhancement pipeline to avoid dependencies
        with patch('whisper_audio_preprocessor.AudioEnhancementPipeline'):
            self.preprocessor = AudioPreprocessor(temp_dir=self.temp_dir)
    
    def test_preprocessor_initialization(self):
        """Test AudioPreprocessor initialization"""
        assert os.path.exists(self.preprocessor.temp_dir)
        assert os.path.exists(self.preprocessor.cache_dir)
        assert self.preprocessor.supported_input_formats == ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.webm']
        assert self.preprocessor.whisper_optimal_formats == ['.wav', '.flac']
        assert self.preprocessor.processing_stats['total_files_processed'] == 0
    
    def test_validate_input_file_success(self):
        """Test successful input file validation"""
        # Create a test audio file
        test_audio = np.random.randn(16000)  # 1 second of audio
        test_file = os.path.join(self.temp_dir, "test.wav")
        sf.write(test_file, test_audio, 16000)
        
        # Should not raise any exception
        self.preprocessor._validate_input_file(test_file)
    
    def test_validate_input_file_not_found(self):
        """Test validation with non-existent file"""
        with pytest.raises(AudioFileError, match="Audio file not found"):
            self.preprocessor._validate_input_file("nonexistent.wav")
    
    def test_validate_input_file_unsupported_format(self):
        """Test validation with unsupported format"""
        test_file = os.path.join(self.temp_dir, "test.xyz")
        Path(test_file).touch()  # Create empty file
        
        with pytest.raises(AudioFileError, match="Unsupported audio format"):
            self.preprocessor._validate_input_file(test_file)
    
    def test_validate_input_file_too_large(self):
        """Test validation with file too large"""
        # Create a large dummy file
        test_file = os.path.join(self.temp_dir, "large.wav")
        with open(test_file, 'wb') as f:
            f.write(b'0' * (101 * 1024 * 1024))  # 101MB
        
        with pytest.raises(AudioFileError, match="File size too large"):
            self.preprocessor._validate_input_file(test_file)
    
    def test_load_audio_safely_success(self):
        """Test successful audio loading"""
        # Create test audio
        test_audio = np.random.randn(16000)
        test_file = os.path.join(self.temp_dir, "test.wav")
        sf.write(test_file, test_audio, 16000)
        
        audio_data, sample_rate = self.preprocessor._load_audio_safely(test_file)
        
        assert audio_data.shape[0] == 1  # Should be 2D with 1 channel
        assert audio_data.shape[1] == 16000  # 1 second at 16kHz
        assert sample_rate == 16000
    
    def test_load_audio_safely_stereo(self):
        """Test loading stereo audio"""
        # Create stereo test audio
        test_audio = np.random.randn(2, 16000)  # 2 channels
        test_file = os.path.join(self.temp_dir, "stereo.wav")
        sf.write(test_file, test_audio.T, 16000)
        
        audio_data, sample_rate = self.preprocessor._load_audio_safely(test_file)
        
        assert audio_data.shape[0] == 2  # Should have 2 channels
        assert sample_rate == 16000
    
    def test_load_audio_safely_duration_too_long(self):
        """Test loading audio that's too long"""
        # Create very long audio (more than 30 minutes)
        long_audio = np.random.randn(16000 * 1801)  # 1801 seconds
        test_file = os.path.join(self.temp_dir, "long.wav")
        sf.write(test_file, long_audio, 16000)
        
        with pytest.raises(AudioFileError, match="Audio duration too long"):
            self.preprocessor._load_audio_safely(test_file)
    
    def test_save_audio_safely_mono(self):
        """Test saving mono audio"""
        test_audio = np.random.randn(1, 16000)
        output_file = os.path.join(self.temp_dir, "output.wav")
        
        self.preprocessor._save_audio_safely(test_audio, 16000, output_file)
        
        assert os.path.exists(output_file)
        
        # Verify saved audio
        loaded_audio, loaded_sr = sf.read(output_file)
        assert loaded_sr == 16000
        assert len(loaded_audio) == 16000
    
    def test_save_audio_safely_clipping_prevention(self):
        """Test that clipping is prevented during save"""
        # Create audio with values > 1.0
        test_audio = np.random.randn(1, 16000) * 2.0  # Values up to ±2.0
        output_file = os.path.join(self.temp_dir, "clipped.wav")
        
        self.preprocessor._save_audio_safely(test_audio, 16000, output_file)
        
        # Verify no clipping occurred
        loaded_audio, _ = sf.read(output_file)
        assert np.max(np.abs(loaded_audio)) <= 1.0
    
    def test_assess_quality_mock(self):
        """Test quality assessment with mocked enhancement pipeline"""
        # Create test audio
        test_audio = np.random.randn(16000)
        test_file = os.path.join(self.temp_dir, "test.wav")
        sf.write(test_file, test_audio, 16000)
        
        # Mock the quality assessment
        mock_metrics = AudioQualityMetrics(
            snr_db=20.0, thd_percent=1.0, dynamic_range_db=25.0,
            spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
            rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
            quality_score=75.0, recommendations=["Good quality audio"]
        )
        
        self.preprocessor.enhancement_pipeline._assess_audio_quality = Mock(return_value=mock_metrics)
        
        result = self.preprocessor.assess_quality(test_file)
        
        assert isinstance(result, AudioQualityMetrics)
        assert result.quality_score == 75.0
        assert result.snr_db == 20.0
    
    def test_determine_processing_pipeline_fast_mode(self):
        """Test processing pipeline determination for fast mode"""
        config = AudioConfig(processing_mode=ProcessingMode.FAST)
        metrics = AudioQualityMetrics(
            snr_db=15.0, thd_percent=3.0, dynamic_range_db=20.0,
            spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
            rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
            quality_score=60.0, recommendations=[]
        )
        
        pipeline = self.preprocessor._determine_processing_pipeline(metrics, config)
        
        assert pipeline['noise_reduction'] is False
        assert pipeline['enhancement'] is False
        assert pipeline['repair'] is False
        assert pipeline['normalization'] is True
        assert pipeline['format_conversion'] is True
    
    def test_determine_processing_pipeline_quality_mode(self):
        """Test processing pipeline determination for quality mode"""
        config = AudioConfig(processing_mode=ProcessingMode.QUALITY)
        metrics = AudioQualityMetrics(
            snr_db=15.0, thd_percent=3.0, dynamic_range_db=20.0,
            spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
            rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
            quality_score=60.0, recommendations=[]
        )
        
        pipeline = self.preprocessor._determine_processing_pipeline(metrics, config)
        
        assert pipeline['noise_reduction'] is True
        assert pipeline['enhancement'] is True
        assert pipeline['repair'] is True
        assert pipeline['normalization'] is True
    
    def test_optimize_for_whisper_mono_conversion(self):
        """Test Whisper optimization converts stereo to mono"""
        # Create stereo audio
        stereo_audio = np.random.randn(2, 16000)
        config = AudioConfig()
        
        optimized_audio, optimized_sr = self.preprocessor._optimize_for_whisper(
            stereo_audio, 16000, config
        )
        
        assert optimized_audio.shape[0] == 1  # Should be mono
        assert optimized_sr == 16000
    
    def test_optimize_for_whisper_resampling(self):
        """Test Whisper optimization resamples to target rate"""
        # Create audio at different sample rate
        audio = np.random.randn(1, 22050)  # 1 second at 22.05kHz
        config = AudioConfig(target_sample_rate=16000)
        
        optimized_audio, optimized_sr = self.preprocessor._optimize_for_whisper(
            audio, 22050, config
        )
        
        assert optimized_sr == 16000
        assert optimized_audio.shape[1] == 16000  # Should be resampled
    
    def test_apply_whisper_normalization(self):
        """Test Whisper-specific normalization"""
        # Create quiet audio
        quiet_audio = np.random.randn(1, 16000) * 0.01  # Very quiet
        
        normalized_audio = self.preprocessor._apply_whisper_normalization(quiet_audio, 16000)
        
        # Should be louder after normalization
        original_rms = np.sqrt(np.mean(quiet_audio**2))
        normalized_rms = np.sqrt(np.mean(normalized_audio**2))
        assert normalized_rms > original_rms
        
        # Should not clip
        assert np.max(np.abs(normalized_audio)) <= 1.0
    
    def test_generate_whisper_recommendations_good_quality(self):
        """Test recommendations for good quality audio"""
        good_metrics = AudioQualityMetrics(
            snr_db=25.0, thd_percent=0.5, dynamic_range_db=25.0,
            spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
            rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
            quality_score=85.0, recommendations=[]
        )
        
        recommendations = self.preprocessor._generate_whisper_recommendations(good_metrics)
        
        assert "well-optimized for Whisper transcription" in recommendations[0]
    
    def test_generate_whisper_recommendations_poor_quality(self):
        """Test recommendations for poor quality audio"""
        poor_metrics = AudioQualityMetrics(
            snr_db=8.0, thd_percent=5.0, dynamic_range_db=5.0,
            spectral_centroid=500.0, spectral_rolloff=2000.0, zero_crossing_rate=0.1,
            rms_energy=0.1, peak_level_db=0.0, loudness_lufs=-23.0,
            quality_score=30.0, recommendations=[]
        )
        
        recommendations = self.preprocessor._generate_whisper_recommendations(poor_metrics)
        
        assert len(recommendations) > 1  # Should have multiple recommendations
        assert any("noise reduction" in rec for rec in recommendations)
        assert any("audio enhancement" in rec for rec in recommendations)
        assert any("dynamic range" in rec for rec in recommendations)
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.wav")
        Path(test_file).touch()
        
        config = AudioConfig()
        
        cache_key1 = self.preprocessor._generate_cache_key(test_file, config)
        cache_key2 = self.preprocessor._generate_cache_key(test_file, config)
        
        # Same file and config should produce same key
        assert cache_key1 == cache_key2
        assert len(cache_key1) == 32  # MD5 hash length
    
    def test_cache_key_different_configs(self):
        """Test that different configs produce different cache keys"""
        test_file = os.path.join(self.temp_dir, "test.wav")
        Path(test_file).touch()
        
        config1 = AudioConfig(processing_mode=ProcessingMode.FAST)
        config2 = AudioConfig(processing_mode=ProcessingMode.QUALITY)
        
        cache_key1 = self.preprocessor._generate_cache_key(test_file, config1)
        cache_key2 = self.preprocessor._generate_cache_key(test_file, config2)
        
        assert cache_key1 != cache_key2
    
    def test_get_processing_statistics_empty(self):
        """Test getting statistics when no files processed"""
        stats = self.preprocessor.get_processing_statistics()
        
        assert stats['total_files_processed'] == 0
        assert stats['average_processing_time'] == 0.0
        assert stats['cache_hit_rate'] == 0.0
        assert stats['average_quality_improvement'] == 0.0
    
    def test_update_processing_stats(self):
        """Test updating processing statistics"""
        # Create mock result
        mock_result = AudioPreprocessingResult(
            processed_audio_path="output.wav",
            original_path="input.wav",
            original_format="mp3",
            processed_format="wav",
            original_metrics=Mock(),
            processed_metrics=Mock(),
            processing_time=2.5,
            operations_applied=["noise_reduction", "normalization"],
            quality_improvement=15.0,
            whisper_optimized=True,
            recommendations=[],
            metadata={}
        )
        
        self.preprocessor._update_processing_stats(mock_result)
        
        stats = self.preprocessor.get_processing_statistics()
        assert stats['total_files_processed'] == 1
        assert stats['total_processing_time'] == 2.5
        assert stats['average_quality_improvement'] == 15.0
        assert stats['format_conversions']['mp3_to_wav'] == 1
        assert stats['common_issues_fixed']['noise_reduction'] == 1
        assert stats['common_issues_fixed']['normalization'] == 1
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Create some cache files
        cache_file = os.path.join(self.preprocessor.cache_dir, "test_cache.json")
        with open(cache_file, 'w') as f:
            f.write('{"test": "data"}')
        
        assert os.path.exists(cache_file)
        
        self.preprocessor.clear_cache()
        
        # Cache directory should exist but be empty
        assert os.path.exists(self.preprocessor.cache_dir)
        assert not os.path.exists(cache_file)

class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    def test_create_fast_config(self):
        """Test fast configuration creation"""
        config = create_fast_config()
        
        assert config.processing_mode == ProcessingMode.FAST
        assert config.enable_noise_reduction is False
        assert config.enable_enhancement is False
        assert config.enable_repair is False
        assert config.enable_normalization is True
    
    def test_create_quality_config(self):
        """Test quality configuration creation"""
        config = create_quality_config()
        
        assert config.processing_mode == ProcessingMode.QUALITY
        assert config.enable_noise_reduction is True
        assert config.enable_enhancement is True
        assert config.enable_repair is True
        assert config.enable_normalization is True
        assert config.min_snr_db == 15.0
        assert config.min_quality_score == 70.0
    
    def test_create_balanced_config(self):
        """Test balanced configuration creation"""
        config = create_balanced_config()
        
        assert config.processing_mode == ProcessingMode.BALANCED
        assert config.enable_noise_reduction is True
        assert config.enable_enhancement is True
        assert config.enable_repair is False
        assert config.enable_normalization is True

class TestIntegration:
    """Integration test cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def test_full_preprocessing_workflow_mock(self):
        """Test complete preprocessing workflow with mocked dependencies"""
        # Create test audio file
        test_audio = np.random.randn(16000) * 0.5  # 1 second, moderate level
        test_file = os.path.join(self.temp_dir, "test.wav")
        sf.write(test_file, test_audio, 16000)
        
        with patch('whisper_audio_preprocessor.AudioEnhancementPipeline') as mock_pipeline:
            # Mock enhancement pipeline
            mock_enhancement_result = Mock()
            mock_enhancement_result.enhancement_applied = ["noise_reduction"]
            mock_pipeline.return_value.enhance_audio.return_value = mock_enhancement_result
            
            # Mock quality assessment
            mock_metrics = AudioQualityMetrics(
                snr_db=18.0, thd_percent=1.5, dynamic_range_db=22.0,
                spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
                rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
                quality_score=70.0, recommendations=[]
            )
            mock_pipeline.return_value._assess_audio_quality.return_value = mock_metrics
            
            # Initialize preprocessor
            preprocessor = AudioPreprocessor(temp_dir=self.temp_dir)
            
            # Create config
            config = create_balanced_config()
            
            # Process audio
            result = preprocessor.preprocess_audio(test_file, config=config)
            
            # Verify result
            assert isinstance(result, AudioPreprocessingResult)
            assert os.path.exists(result.processed_audio_path)
            assert result.original_format == "wav"
            assert result.processed_format == "wav"
            assert result.whisper_optimized is True
            assert result.processing_time > 0
            assert len(result.operations_applied) > 0
            assert len(result.recommendations) > 0
    
    def test_optimize_for_whisper_workflow(self):
        """Test quick Whisper optimization workflow"""
        # Create test audio file
        test_audio = np.random.randn(2, 22050)  # Stereo, 22.05kHz
        test_file = os.path.join(self.temp_dir, "stereo.wav")
        sf.write(test_file, test_audio.T, 22050)
        
        with patch('whisper_audio_preprocessor.AudioEnhancementPipeline') as mock_pipeline:
            # Mock quality assessment
            mock_metrics = AudioQualityMetrics(
                snr_db=20.0, thd_percent=1.0, dynamic_range_db=25.0,
                spectral_centroid=2000.0, spectral_rolloff=4000.0, zero_crossing_rate=0.1,
                rms_energy=0.1, peak_level_db=-6.0, loudness_lufs=-23.0,
                quality_score=75.0, recommendations=[]
            )
            mock_pipeline.return_value._assess_audio_quality.return_value = mock_metrics
            
            # Initialize preprocessor
            preprocessor = AudioPreprocessor(temp_dir=self.temp_dir)
            
            # Quick optimization
            result = preprocessor.optimize_for_whisper(test_file)
            
            # Verify optimization
            assert result.whisper_optimized is True
            assert os.path.exists(result.processed_audio_path)
            
            # Verify audio is optimized for Whisper
            optimized_audio, sr = sf.read(result.processed_audio_path)
            assert sr == 16000  # Should be resampled
            assert len(optimized_audio.shape) == 1  # Should be mono

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])