"""
Test suite for Advanced Noise Reduction System

Comprehensive tests for all components of the advanced noise reduction and audio
restoration system including unit tests, integration tests, and performance tests.
"""

import pytest
import numpy as np
import librosa
import tempfile
import os
from unittest.mock import patch, MagicMock

from advanced_noise_reduction_system import (
    AdvancedNoiseReductionSystem,
    AdaptiveNoiseReducer,
    AudioArtifactRemover,
    SpectralEnhancer,
    AIAudioReconstructor,
    RestorationSettings,
    NoiseProfile,
    RestorationResult,
    NoiseType,
    ArtifactType,
    create_test_audio
)

class TestAdvancedNoiseReductionSystem:
    """Test the main noise reduction system"""
    
    @pytest.fixture
    def system(self):
        """Create a system instance for testing"""
        return AdvancedNoiseReductionSystem()
    
    @pytest.fixture
    def test_audio(self):
        """Create test audio for testing"""
        return create_test_audio(duration=2.0, sr=22050), 22050
    
    @pytest.fixture
    def default_settings(self):
        """Create default restoration settings"""
        return RestorationSettings()
    
    def test_system_initialization(self, system):
        """Test system initialization"""
        assert isinstance(system.noise_reducer, AdaptiveNoiseReducer)
        assert isinstance(system.artifact_remover, AudioArtifactRemover)
        assert isinstance(system.spectral_enhancer, SpectralEnhancer)
        assert isinstance(system.ai_reconstructor, AIAudioReconstructor)
    
    def test_process_audio_basic(self, system, test_audio, default_settings):
        """Test basic audio processing"""
        audio, sr = test_audio
        
        result = system.process_audio(audio, sr, default_settings)
        
        assert isinstance(result, RestorationResult)
        assert len(result.restored_audio) == len(audio)
        assert result.processing_time > 0
        assert 0 <= result.confidence_score <= 1
        assert isinstance(result.quality_improvement, dict)
        assert isinstance(result.artifacts_removed, list)
    
    def test_process_audio_with_different_settings(self, system, test_audio):
        """Test processing with different settings configurations"""
        audio, sr = test_audio
        
        # Conservative settings
        conservative = RestorationSettings(
            noise_reduction_strength=0.3,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.5,
            spectral_enhancement=False,
            dynamic_range_optimization=False,
            ai_reconstruction=False
        )
        
        result_conservative = system.process_audio(audio, sr, conservative)
        
        # Aggressive settings
        aggressive = RestorationSettings(
            noise_reduction_strength=0.9,
            preserve_speech_quality=False,
            artifact_removal_sensitivity=1.0,
            spectral_enhancement=True,
            dynamic_range_optimization=True,
            ai_reconstruction=True
        )
        
        result_aggressive = system.process_audio(audio, sr, aggressive)
        
        # Aggressive should have more processing applied
        assert result_aggressive.noise_reduction_applied >= result_conservative.noise_reduction_applied
        assert len(result_aggressive.quality_improvement) >= len(result_conservative.quality_improvement)
    
    def test_process_empty_audio(self, system, default_settings):
        """Test processing empty audio"""
        empty_audio = np.array([])
        sr = 22050
        
        result = system.process_audio(empty_audio, sr, default_settings)
        
        assert len(result.restored_audio) == 0
        assert result.confidence_score >= 0
    
    def test_process_silent_audio(self, system, default_settings):
        """Test processing silent audio"""
        silent_audio = np.zeros(22050)  # 1 second of silence
        sr = 22050
        
        result = system.process_audio(silent_audio, sr, default_settings)
        
        assert len(result.restored_audio) == len(silent_audio)
        assert np.allclose(result.restored_audio, silent_audio, atol=1e-6)

class TestAdaptiveNoiseReducer:
    """Test the adaptive noise reducer component"""
    
    @pytest.fixture
    def noise_reducer(self):
        """Create noise reducer instance"""
        return AdaptiveNoiseReducer()
    
    @pytest.fixture
    def noisy_audio(self):
        """Create noisy test audio"""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(duration * sr))
        
        # Clean signal
        clean = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.5)
        
        # Add noise
        noise = 0.3 * np.random.normal(0, 1, len(t))
        
        return clean + noise, sr
    
    def test_analyze_noise_profile(self, noise_reducer, noisy_audio):
        """Test noise profile analysis"""
        audio, sr = noisy_audio
        
        profile = noise_reducer.analyze_noise_profile(audio, sr)
        
        assert isinstance(profile, NoiseProfile)
        assert isinstance(profile.noise_type, NoiseType)
        assert 0 <= profile.confidence <= 1
        assert 0 <= profile.recommended_reduction <= 1
        assert len(profile.frequency_profile) > 0
        assert len(profile.power_spectrum) > 0
        assert isinstance(profile.temporal_characteristics, dict)
    
    def test_noise_type_classification(self, noise_reducer):
        """Test different noise type classification"""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(duration * sr))
        
        # Broadband noise
        broadband = 0.5 * np.random.normal(0, 1, len(t))
        profile_broadband = noise_reducer.analyze_noise_profile(broadband, sr)
        
        # Tonal noise
        tonal = (0.3 * np.sin(2 * np.pi * 60 * t) + 
                0.2 * np.sin(2 * np.pi * 120 * t) +
                0.1 * np.sin(2 * np.pi * 1000 * t))
        profile_tonal = noise_reducer.analyze_noise_profile(tonal, sr)
        
        # Should detect different characteristics
        assert profile_broadband.noise_type != profile_tonal.noise_type or \
               abs(profile_broadband.confidence - profile_tonal.confidence) > 0.1
    
    def test_reduce_noise(self, noise_reducer, noisy_audio):
        """Test noise reduction functionality"""
        audio, sr = noisy_audio
        
        # Analyze noise first
        profile = noise_reducer.analyze_noise_profile(audio, sr)
        
        # Apply noise reduction
        reduced = noise_reducer.reduce_noise(audio, sr, profile, preserve_speech=True)
        
        assert len(reduced) == len(audio)
        assert not np.array_equal(reduced, audio)  # Should be different
        
        # Check that energy is generally reduced
        original_energy = np.mean(audio**2)
        reduced_energy = np.mean(reduced**2)
        assert reduced_energy <= original_energy * 1.1  # Allow small increase due to processing
    
    def test_speech_preservation(self, noise_reducer, noisy_audio):
        """Test speech preservation functionality"""
        audio, sr = noisy_audio
        profile = noise_reducer.analyze_noise_profile(audio, sr)
        
        # Test with and without speech preservation
        reduced_with_preservation = noise_reducer.reduce_noise(audio, sr, profile, preserve_speech=True)
        reduced_without_preservation = noise_reducer.reduce_noise(audio, sr, profile, preserve_speech=False)
        
        # Both should be valid outputs
        assert len(reduced_with_preservation) == len(audio)
        assert len(reduced_without_preservation) == len(audio)

class TestAudioArtifactRemover:
    """Test the audio artifact remover component"""
    
    @pytest.fixture
    def artifact_remover(self):
        """Create artifact remover instance"""
        return AudioArtifactRemover()
    
    def test_detect_clicks(self, artifact_remover):
        """Test click detection"""
        sr = 22050
        duration = 2.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * sr)))
        
        # Add clicks
        click_positions = [1000, 5000, 10000]
        for pos in click_positions:
            if pos < len(audio):
                audio[pos] += 2.0  # Sharp click
        
        clicks = artifact_remover._detect_clicks(audio, sr)
        
        assert len(clicks) > 0
        # Should detect at least some of the clicks
        detected_positions = [click[0] for click in clicks]
        assert any(abs(pos - detected) < 100 for pos in click_positions for detected in detected_positions)
    
    def test_detect_hums(self, artifact_remover):
        """Test hum detection"""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(duration * sr))
        
        # Create audio with 60 Hz hum
        audio = (np.sin(2 * np.pi * 440 * t) + 
                0.3 * np.sin(2 * np.pi * 60 * t))
        
        hums = artifact_remover._detect_hums(audio, sr)
        
        assert len(hums) > 0
        assert 60 in hums or any(abs(freq - 60) < 5 for freq in hums)
    
    def test_detect_clipping(self, artifact_remover):
        """Test clipping detection"""
        sr = 22050
        duration = 1.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * sr)))
        
        # Add clipping
        clipped_audio = np.clip(audio * 2, -0.8, 0.8)
        
        clipping_regions = artifact_remover._detect_clipping(clipped_audio, sr)
        
        assert len(clipping_regions) > 0
    
    def test_remove_artifacts(self, artifact_remover):
        """Test artifact removal"""
        sr = 22050
        duration = 2.0
        audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(duration * sr)))
        
        # Add various artifacts
        # Clicks
        audio[1000] += 2.0
        audio[5000] += -1.5
        
        # Detect artifacts
        artifacts = artifact_remover.detect_artifacts(audio, sr)
        
        # Remove artifacts
        cleaned, removed_types = artifact_remover.remove_artifacts(audio, sr, artifacts)
        
        assert len(cleaned) == len(audio)
        assert isinstance(removed_types, list)
        
        # Should be different from original (artifacts removed)
        if len(removed_types) > 0:
            assert not np.array_equal(cleaned, audio)

class TestSpectralEnhancer:
    """Test the spectral enhancer component"""
    
    @pytest.fixture
    def enhancer(self):
        """Create spectral enhancer instance"""
        return SpectralEnhancer()
    
    @pytest.fixture
    def test_tone(self):
        """Create test tone"""
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(duration * sr))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        return audio, sr
    
    def test_enhance_spectrum(self, enhancer, test_tone):
        """Test spectral enhancement"""
        audio, sr = test_tone
        
        enhanced = enhancer.enhance_spectrum(audio, sr, enhancement_strength=0.5)
        
        assert len(enhanced) == len(audio)
        assert not np.array_equal(enhanced, audio)
        
        # Check that enhancement was applied
        original_energy = np.mean(audio**2)
        enhanced_energy = np.mean(enhanced**2)
        
        # Enhanced version should have similar or slightly higher energy
        assert enhanced_energy >= original_energy * 0.8
    
    def test_optimize_dynamic_range(self, enhancer, test_tone):
        """Test dynamic range optimization"""
        audio, sr = test_tone
        
        # Create audio with poor dynamic range
        poor_dynamics = audio * 0.1  # Very quiet
        
        optimized = enhancer.optimize_dynamic_range(poor_dynamics, sr, target_lufs=-23.0)
        
        assert len(optimized) == len(poor_dynamics)
        
        # Should have increased energy
        original_rms = np.sqrt(np.mean(poor_dynamics**2))
        optimized_rms = np.sqrt(np.mean(optimized**2))
        
        assert optimized_rms > original_rms
    
    def test_multiband_compression(self, enhancer, test_tone):
        """Test multiband compression"""
        audio, sr = test_tone
        
        # Create audio with high dynamic range
        high_dynamics = audio * 2.0
        high_dynamics = np.clip(high_dynamics, -0.95, 0.95)
        
        compressed = enhancer._apply_multiband_compression(high_dynamics, sr)
        
        assert len(compressed) == len(high_dynamics)
        
        # Should reduce peak levels
        original_peak = np.max(np.abs(high_dynamics))
        compressed_peak = np.max(np.abs(compressed))
        
        assert compressed_peak <= original_peak

class TestAIAudioReconstructor:
    """Test the AI audio reconstructor component"""
    
    @pytest.fixture
    def reconstructor(self):
        """Create AI reconstructor instance"""
        return AIAudioReconstructor()
    
    @pytest.fixture
    def audio_with_gaps(self):
        """Create audio with missing segments"""
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(duration * sr))
        audio = np.sin(2 * np.pi * 440 * t) * 0.5
        
        # Create gaps
        gap_start = sr // 2  # 0.5 seconds
        gap_end = gap_start + sr // 10  # 0.1 second gap
        audio[gap_start:gap_end] = 0
        
        return audio, sr, (gap_start, gap_end)
    
    def test_detect_missing_segments(self, reconstructor, audio_with_gaps):
        """Test missing segment detection"""
        audio, sr, (gap_start, gap_end) = audio_with_gaps
        
        missing_segments = reconstructor.detect_missing_segments(audio, sr)
        
        assert len(missing_segments) > 0
        
        # Should detect the gap we created
        detected_gap = missing_segments[0]
        assert abs(detected_gap[0] - gap_start) < sr * 0.1  # Within 100ms
        assert abs(detected_gap[1] - gap_end) < sr * 0.1
    
    def test_reconstruct_segments(self, reconstructor, audio_with_gaps):
        """Test segment reconstruction"""
        audio, sr, (gap_start, gap_end) = audio_with_gaps
        
        missing_segments = [(gap_start, gap_end)]
        
        reconstructed = reconstructor.reconstruct_segments(audio, sr, missing_segments)
        
        assert len(reconstructed) == len(audio)
        
        # Gap should no longer be silent
        gap_energy_before = np.mean(audio[gap_start:gap_end]**2)
        gap_energy_after = np.mean(reconstructed[gap_start:gap_end]**2)
        
        assert gap_energy_after > gap_energy_before
    
    def test_spectral_interpolation(self, reconstructor):
        """Test spectral interpolation method"""
        sr = 22050
        
        # Create context audio
        t_before = np.linspace(0, 0.5, sr // 2)
        t_after = np.linspace(0, 0.5, sr // 2)
        
        before_context = np.sin(2 * np.pi * 440 * t_before)
        after_context = np.sin(2 * np.pi * 440 * t_after)
        
        target_length = sr // 10  # 0.1 second
        
        interpolated = reconstructor._spectral_interpolation(
            before_context, after_context, target_length, sr
        )
        
        assert len(interpolated) == target_length
        assert not np.allclose(interpolated, 0)  # Should not be silent

class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_processing(self):
        """Test complete end-to-end processing pipeline"""
        system = AdvancedNoiseReductionSystem()
        
        # Create complex test audio
        sr = 22050
        duration = 3.0
        t = np.linspace(0, duration, int(duration * sr))
        
        # Base signal
        signal = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.3)
        
        # Add various issues
        signal += 0.2 * np.random.normal(0, 1, len(t))  # Noise
        signal += 0.1 * np.sin(2 * np.pi * 60 * t)      # Hum
        signal[sr:sr+100] += 2.0                         # Click
        signal[2*sr:2*sr+sr//10] = 0                     # Gap
        
        # Process with full settings
        settings = RestorationSettings(
            noise_reduction_strength=0.8,
            preserve_speech_quality=True,
            artifact_removal_sensitivity=0.8,
            spectral_enhancement=True,
            dynamic_range_optimization=True,
            ai_reconstruction=True
        )
        
        result = system.process_audio(signal, sr, settings)
        
        # Verify result
        assert isinstance(result, RestorationResult)
        assert len(result.restored_audio) == len(signal)
        assert result.processing_time > 0
        assert 0 <= result.confidence_score <= 1
        assert len(result.quality_improvement) > 0
    
    def test_performance_with_long_audio(self):
        """Test performance with longer audio files"""
        system = AdvancedNoiseReductionSystem()
        
        # Create 10-second audio
        long_audio = create_test_audio(duration=10.0, sr=22050)
        sr = 22050
        
        settings = RestorationSettings(noise_reduction_strength=0.5)
        
        import time
        start_time = time.time()
        result = system.process_audio(long_audio, sr, settings)
        processing_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 2x real-time for this test)
        assert processing_time < 20.0  # 10 seconds * 2
        assert len(result.restored_audio) == len(long_audio)
    
    def test_different_sample_rates(self):
        """Test processing with different sample rates"""
        system = AdvancedNoiseReductionSystem()
        settings = RestorationSettings(noise_reduction_strength=0.5)
        
        sample_rates = [16000, 22050, 44100, 48000]
        
        for sr in sample_rates:
            audio = create_test_audio(duration=1.0, sr=sr)
            
            result = system.process_audio(audio, sr, settings)
            
            assert len(result.restored_audio) == len(audio)
            assert result.confidence_score >= 0

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_audio_input(self):
        """Test handling of invalid audio input"""
        system = AdvancedNoiseReductionSystem()
        settings = RestorationSettings()
        
        # Test with None
        result = system.process_audio(None, 22050, settings)
        assert result.confidence_score == 0.0
        
        # Test with invalid array
        invalid_audio = np.array([np.inf, np.nan, 1.0])
        result = system.process_audio(invalid_audio, 22050, settings)
        assert len(result.restored_audio) == len(invalid_audio)
    
    def test_extreme_settings(self):
        """Test with extreme settings values"""
        system = AdvancedNoiseReductionSystem()
        audio = create_test_audio(duration=1.0, sr=22050)
        
        # Extreme settings
        extreme_settings = RestorationSettings(
            noise_reduction_strength=1.0,
            artifact_removal_sensitivity=1.0
        )
        
        result = system.process_audio(audio, 22050, extreme_settings)
        
        assert len(result.restored_audio) == len(audio)
        assert result.confidence_score >= 0
    
    def test_zero_sample_rate(self):
        """Test handling of invalid sample rate"""
        system = AdvancedNoiseReductionSystem()
        audio = create_test_audio(duration=1.0, sr=22050)
        settings = RestorationSettings()
        
        # This should handle the error gracefully
        result = system.process_audio(audio, 0, settings)
        assert result.confidence_score >= 0

def test_create_test_audio():
    """Test the test audio creation function"""
    audio = create_test_audio(duration=2.0, sr=22050)
    
    assert len(audio) == int(2.0 * 22050)
    assert np.max(np.abs(audio)) <= 1.0  # Should be normalized
    assert np.std(audio) > 0  # Should not be silent

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])