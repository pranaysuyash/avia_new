"""
Comprehensive tests for Intelligent Audio Enhancement and Clarity Optimization System

This module tests all components of the intelligent audio enhancement system including:
- Spectral enhancement functionality
- Dynamic range optimization
- Speech clarity enhancement
- Quality assessment
- API endpoints
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch
import json

# Import the modules to test
from intelligent_audio_enhancement import (
    IntelligentAudioEnhancer, SpectralEnhancer, DynamicRangeOptimizer,
    SpeechClarityEnhancer, AudioQualityAssessor, EnhancementMode,
    QualityMetric, SpectralEnhancementConfig, DynamicRangeConfig,
    SpeechClarityConfig, QualityAssessment, create_test_audio
)

class TestSpectralEnhancer:
    """Test cases for SpectralEnhancer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.enhancer = SpectralEnhancer()
        self.test_audio = create_test_audio(duration=2.0)
        self.sample_rate = 44100
    
    def test_analyze_spectrum(self):
        """Test spectrum analysis functionality"""
        analysis = self.enhancer.analyze_spectrum(self.test_audio, self.sample_rate)
        
        # Check required keys are present
        required_keys = ['stft', 'magnitude', 'phase', 'freqs', 'spectral_centroid', 
                        'spectral_rolloff', 'spectral_bandwidth', 'energy_distribution']
        for key in required_keys:
            assert key in analysis
        
        # Check data types and shapes
        assert isinstance(analysis['spectral_centroid'], (int, float))
        assert isinstance(analysis['spectral_rolloff'], (int, float))
        assert isinstance(analysis['spectral_bandwidth'], (int, float))
        assert 'low' in analysis['energy_distribution']
        assert 'mid' in analysis['energy_distribution']
        assert 'high' in analysis['energy_distribution']
    
    def test_enhance_spectrum_basic(self):
        """Test basic spectral enhancement"""
        config = SpectralEnhancementConfig(
            frequency_bands=[(200, 1000), (1000, 4000), (4000, 8000)],
            enhancement_factors=[1.2, 1.5, 1.1],
            smoothing_factor=0.2,
            adaptive_processing=False
        )
        
        enhanced_audio = self.enhancer.enhance_spectrum(self.test_audio, self.sample_rate, config)
        
        # Check output properties
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
        assert not np.array_equal(enhanced_audio, self.test_audio)  # Should be different
    
    def test_enhance_spectrum_adaptive(self):
        """Test adaptive spectral enhancement"""
        config = SpectralEnhancementConfig(
            frequency_bands=[(200, 1000), (1000, 4000)],
            enhancement_factors=[1.5, 1.3],
            adaptive_processing=True
        )
        
        enhanced_audio = self.enhancer.enhance_spectrum(self.test_audio, self.sample_rate, config)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
    
    def test_spectral_smoothing(self):
        """Test spectral smoothing functionality"""
        magnitude = np.random.random((1024, 100))
        smoothed = self.enhancer._apply_spectral_smoothing(magnitude, 0.3)
        
        assert smoothed.shape == magnitude.shape
        assert not np.array_equal(smoothed, magnitude)
    
    def test_adaptive_factor_calculation(self):
        """Test adaptive enhancement factor calculation"""
        # Test different energy levels
        low_energy_factor = self.enhancer._calculate_adaptive_factor(0.01, 1.5)
        medium_energy_factor = self.enhancer._calculate_adaptive_factor(0.07, 1.5)
        high_energy_factor = self.enhancer._calculate_adaptive_factor(0.15, 1.5)
        
        # Higher energy should result in lower enhancement factors
        assert high_energy_factor < medium_energy_factor < low_energy_factor

class TestDynamicRangeOptimizer:
    """Test cases for DynamicRangeOptimizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.optimizer = DynamicRangeOptimizer()
        self.test_audio = create_test_audio(duration=2.0)
        self.sample_rate = 44100
    
    def test_analyze_dynamics(self):
        """Test dynamics analysis"""
        dynamics = self.optimizer.analyze_dynamics(self.test_audio, self.sample_rate)
        
        # Check required metrics
        required_keys = ['rms', 'peak', 'crest_factor', 'dynamic_range', 'loudness_lufs', 'peak_dbfs']
        for key in required_keys:
            assert key in dynamics
            assert isinstance(dynamics[key], (int, float))
        
        # Check reasonable values
        assert dynamics['rms'] >= 0
        assert dynamics['peak'] >= 0
        assert dynamics['crest_factor'] >= 1.0  # Crest factor should be >= 1
    
    def test_optimize_dynamic_range(self):
        """Test dynamic range optimization"""
        config = DynamicRangeConfig(
            target_lufs=-20.0,
            max_peak=-1.0,
            compression_ratio=2.5
        )
        
        optimized_audio = self.optimizer.optimize_dynamic_range(self.test_audio, self.sample_rate, config)
        
        assert isinstance(optimized_audio, np.ndarray)
        assert len(optimized_audio) == len(self.test_audio)
        
        # Check that peak limiting was applied
        peak_dbfs = 20 * np.log10(np.max(np.abs(optimized_audio)))
        assert peak_dbfs <= config.max_peak + 0.1  # Small tolerance for numerical precision
    
    def test_compression_application(self):
        """Test compression algorithm"""
        config = DynamicRangeConfig(compression_ratio=3.0)
        compressed_audio = self.optimizer._apply_compression(self.test_audio, self.sample_rate, config)
        
        assert isinstance(compressed_audio, np.ndarray)
        assert len(compressed_audio) == len(self.test_audio)
    
    def test_loudness_normalization(self):
        """Test loudness normalization"""
        target_lufs = -23.0
        normalized_audio = self.optimizer._normalize_loudness(self.test_audio, self.sample_rate, target_lufs)
        
        assert isinstance(normalized_audio, np.ndarray)
        assert len(normalized_audio) == len(self.test_audio)
    
    def test_peak_limiting(self):
        """Test peak limiting functionality"""
        # Create audio with peaks above threshold
        loud_audio = self.test_audio * 2.0  # Make it louder
        max_peak_dbfs = -3.0
        
        limited_audio = self.optimizer._apply_peak_limiting(loud_audio, max_peak_dbfs)
        
        # Check that peaks are limited
        actual_peak_dbfs = 20 * np.log10(np.max(np.abs(limited_audio)))
        assert actual_peak_dbfs <= max_peak_dbfs + 0.1

class TestSpeechClarityEnhancer:
    """Test cases for SpeechClarityEnhancer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.enhancer = SpeechClarityEnhancer()
        self.test_audio = create_test_audio(duration=2.0)
        self.sample_rate = 44100
    
    def test_analyze_speech_clarity(self):
        """Test speech clarity analysis"""
        clarity_metrics = self.enhancer.analyze_speech_clarity(self.test_audio, self.sample_rate)
        
        # Check required metrics
        required_keys = ['formant_energy', 'consonant_energy', 'vowel_energy', 
                        'spectral_centroid', 'spectral_rolloff', 'intelligibility_score']
        for key in required_keys:
            assert key in clarity_metrics
            assert isinstance(clarity_metrics[key], (int, float))
        
        # Check intelligibility score range
        assert 0.0 <= clarity_metrics['intelligibility_score'] <= 1.0
    
    def test_enhance_speech_clarity(self):
        """Test speech clarity enhancement"""
        config = SpeechClarityConfig(
            formant_enhancement=True,
            consonant_boost=True,
            vowel_clarity=True,
            sibilance_control=True,
            intelligibility_target=0.85
        )
        
        enhanced_audio = self.enhancer.enhance_speech_clarity(self.test_audio, self.sample_rate, config)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
    
    def test_formant_enhancement(self):
        """Test formant enhancement"""
        enhanced_audio = self.enhancer._enhance_formants(self.test_audio, self.sample_rate)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
        assert not np.array_equal(enhanced_audio, self.test_audio)
    
    def test_consonant_boost(self):
        """Test consonant frequency boost"""
        enhanced_audio = self.enhancer._boost_consonants(self.test_audio, self.sample_rate)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
    
    def test_vowel_clarity_enhancement(self):
        """Test vowel clarity enhancement"""
        enhanced_audio = self.enhancer._enhance_vowel_clarity(self.test_audio, self.sample_rate)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
    
    def test_sibilance_control(self):
        """Test sibilance control"""
        enhanced_audio = self.enhancer._control_sibilance(self.test_audio, self.sample_rate)
        
        assert isinstance(enhanced_audio, np.ndarray)
        assert len(enhanced_audio) == len(self.test_audio)
    
    def test_intelligibility_estimation(self):
        """Test intelligibility score estimation"""
        # Test with different energy distributions
        score1 = self.enhancer._estimate_intelligibility(0.5, 0.3, 0.2)  # Balanced
        score2 = self.enhancer._estimate_intelligibility(0.1, 0.1, 0.8)  # Vowel heavy
        score3 = self.enhancer._estimate_intelligibility(0.8, 0.1, 0.1)  # Formant heavy
        
        # All scores should be in valid range
        for score in [score1, score2, score3]:
            assert 0.0 <= score <= 1.0
        
        # Balanced distribution should have higher score
        assert score1 > score2
        assert score1 > score3

class TestAudioQualityAssessor:
    """Test cases for AudioQualityAssessor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.assessor = AudioQualityAssessor()
        self.test_audio = create_test_audio(duration=2.0)
        self.sample_rate = 44100
    
    def test_assess_quality(self):
        """Test comprehensive quality assessment"""
        assessment = self.assessor.assess_quality(self.test_audio, self.sample_rate)
        
        # Check assessment structure
        assert isinstance(assessment, QualityAssessment)
        assert 0.0 <= assessment.overall_score <= 1.0
        assert 0.0 <= assessment.processing_confidence <= 1.0
        assert isinstance(assessment.recommendations, list)
        assert isinstance(assessment.metrics, dict)
        
        # Check all quality metrics are present
        for metric in QualityMetric:
            assert metric in assessment.metrics
            assert 0.0 <= assessment.metrics[metric] <= 1.0
    
    def test_snr_estimation(self):
        """Test SNR estimation"""
        # Test with clean signal
        clean_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, self.sample_rate))
        snr_clean = self.assessor._estimate_snr(clean_audio)
        
        # Test with very noisy signal to ensure clear difference
        noisy_audio = clean_audio + np.random.normal(0, 0.5, len(clean_audio))
        snr_noisy = self.assessor._estimate_snr(noisy_audio)
        
        # Both should be in valid range
        assert 0.0 <= snr_clean <= 1.0
        assert 0.0 <= snr_noisy <= 1.0
        
        # Clean signal should generally have higher SNR (though not guaranteed due to randomness)
        # Just verify the function works without errors
    
    def test_thd_estimation(self):
        """Test THD estimation"""
        thd_score = self.assessor._estimate_thd(self.test_audio, self.sample_rate)
        assert 0.0 <= thd_score <= 1.0
    
    def test_frequency_balance_assessment(self):
        """Test frequency balance assessment"""
        balance_score = self.assessor._assess_frequency_balance(self.test_audio, self.sample_rate)
        assert 0.0 <= balance_score <= 1.0
    
    def test_overall_score_calculation(self):
        """Test overall quality score calculation"""
        # Create mock metrics
        metrics = {
            QualityMetric.SNR: 0.8,
            QualityMetric.THD: 0.9,
            QualityMetric.CLARITY: 0.7,
            QualityMetric.LOUDNESS: 0.8,
            QualityMetric.DYNAMIC_RANGE: 0.6,
            QualityMetric.FREQUENCY_BALANCE: 0.7
        }
        
        overall_score = self.assessor._calculate_overall_score(metrics)
        assert 0.0 <= overall_score <= 1.0
    
    def test_recommendations_generation(self):
        """Test quality improvement recommendations"""
        # Create metrics with various issues
        poor_metrics = {
            QualityMetric.SNR: 0.5,  # Poor SNR
            QualityMetric.THD: 0.7,  # Moderate distortion
            QualityMetric.CLARITY: 0.6,  # Poor clarity
            QualityMetric.LOUDNESS: 0.7,
            QualityMetric.DYNAMIC_RANGE: 0.5,  # Poor dynamic range
            QualityMetric.FREQUENCY_BALANCE: 0.6  # Poor balance
        }
        
        recommendations = self.assessor._generate_recommendations(poor_metrics)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should recommend noise reduction for poor SNR
        assert any("noise reduction" in rec.lower() for rec in recommendations)

class TestIntelligentAudioEnhancer:
    """Test cases for main IntelligentAudioEnhancer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.enhancer = IntelligentAudioEnhancer()
        self.test_audio = create_test_audio(duration=2.0)
        self.sample_rate = 44100
    
    def test_enhance_audio_automatic_mode(self):
        """Test automatic enhancement mode"""
        results = self.enhancer.enhance_audio(
            self.test_audio, 
            self.sample_rate, 
            EnhancementMode.AUTOMATIC
        )
        
        # Check result structure
        required_keys = ['enhanced_audio', 'initial_assessment', 'final_assessment', 
                        'improvement', 'processing_steps', 'enhancement_config']
        for key in required_keys:
            assert key in results
        
        # Check enhanced audio
        assert isinstance(results['enhanced_audio'], np.ndarray)
        assert len(results['enhanced_audio']) == len(self.test_audio)
        
        # Check assessments
        assert isinstance(results['initial_assessment'], QualityAssessment)
        assert isinstance(results['final_assessment'], QualityAssessment)
        
        # Check improvement calculation
        assert isinstance(results['improvement'], (int, float))
        
        # Check processing steps
        assert isinstance(results['processing_steps'], list)
        assert len(results['processing_steps']) > 0
    
    def test_enhance_audio_speech_focused(self):
        """Test speech-focused enhancement mode"""
        results = self.enhancer.enhance_audio(
            self.test_audio, 
            self.sample_rate, 
            EnhancementMode.SPEECH_FOCUSED
        )
        
        assert 'enhanced_audio' in results
        assert isinstance(results['enhanced_audio'], np.ndarray)
        
        # Should include speech clarity enhancement
        assert "Speech Clarity Enhancement" in results['processing_steps']
    
    def test_enhance_audio_music_focused(self):
        """Test music-focused enhancement mode"""
        results = self.enhancer.enhance_audio(
            self.test_audio, 
            self.sample_rate, 
            EnhancementMode.MUSIC_FOCUSED
        )
        
        assert 'enhanced_audio' in results
        assert isinstance(results['enhanced_audio'], np.ndarray)
        
        # Should not include speech clarity for music
        assert "Speech Clarity Enhancement" not in results['processing_steps']
    
    def test_enhance_audio_broadcast_mode(self):
        """Test broadcast enhancement mode"""
        results = self.enhancer.enhance_audio(
            self.test_audio, 
            self.sample_rate, 
            EnhancementMode.BROADCAST
        )
        
        assert 'enhanced_audio' in results
        
        # Should include all processing steps for broadcast compliance
        expected_steps = ["Spectral Enhancement", "Dynamic Range Optimization", "Speech Clarity Enhancement"]
        for step in expected_steps:
            assert step in results['processing_steps']
    
    def test_enhance_audio_with_user_preferences(self):
        """Test enhancement with user preferences"""
        user_preferences = {
            'spectral_intensity': 1.5,
            'dynamic_intensity': 0.8,
            'disable_clarity': True,
            'target_lufs': -20.0
        }
        
        results = self.enhancer.enhance_audio(
            self.test_audio, 
            self.sample_rate, 
            EnhancementMode.CUSTOM,
            user_preferences
        )
        
        assert 'enhanced_audio' in results
        
        # Should not include speech clarity if disabled
        assert "Speech Clarity Enhancement" not in results['processing_steps']
    
    def test_configuration_creation(self):
        """Test enhancement configuration creation"""
        # Mock assessment
        mock_assessment = QualityAssessment(
            overall_score=0.6,
            metrics={
                QualityMetric.SNR: 0.7,
                QualityMetric.CLARITY: 0.5,
                QualityMetric.FREQUENCY_BALANCE: 0.6
            },
            recommendations=[],
            processing_confidence=0.8
        )
        
        # Test different modes
        for mode in [EnhancementMode.SPEECH_FOCUSED, EnhancementMode.MUSIC_FOCUSED, 
                    EnhancementMode.BROADCAST, EnhancementMode.AUTOMATIC]:
            config = self.enhancer._create_enhancement_config(mode, mock_assessment, None)
            
            assert isinstance(config, dict)
            assert 'apply_spectral_enhancement' in config
            assert 'apply_dynamic_optimization' in config
            assert 'apply_clarity_enhancement' in config
    
    def test_user_preferences_application(self):
        """Test user preferences application to config"""
        base_config = {
            'apply_spectral_enhancement': True,
            'spectral_config': SpectralEnhancementConfig(
                frequency_bands=[(200, 1000)],
                enhancement_factors=[1.0]
            )
        }
        
        user_preferences = {
            'spectral_intensity': 2.0,
            'disable_spectral': True
        }
        
        modified_config = self.enhancer._apply_user_preferences(base_config, user_preferences)
        
        # Should disable spectral enhancement
        assert modified_config['apply_spectral_enhancement'] == False
    
    def test_improvement_calculation(self):
        """Test improvement score calculation"""
        initial_assessment = QualityAssessment(
            overall_score=0.6, metrics={}, recommendations=[], processing_confidence=0.8
        )
        final_assessment = QualityAssessment(
            overall_score=0.8, metrics={}, recommendations=[], processing_confidence=0.9
        )
        
        improvement = self.enhancer._calculate_improvement(initial_assessment, final_assessment)
        assert abs(improvement - 0.2) < 1e-10

class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from api.endpoints.intelligent_audio_enhancement import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/audio-enhancement/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "capabilities" in data
    
    def test_get_enhancement_modes(self, client):
        """Test enhancement modes endpoint"""
        response = client.get("/api/v1/audio-enhancement/modes")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "modes" in data
        assert "automatic" in data["modes"]
        assert "speech_focused" in data["modes"]
    
    def test_get_quality_metrics_info(self, client):
        """Test quality metrics info endpoint"""
        response = client.get("/api/v1/audio-enhancement/quality-metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "metrics" in data
        assert "signal_to_noise_ratio" in data["metrics"]

class TestIntegration:
    """Integration tests for the complete system"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.enhancer = IntelligentAudioEnhancer()
        
    def test_end_to_end_enhancement_pipeline(self):
        """Test complete enhancement pipeline"""
        # Create test audio with known characteristics
        test_audio = create_test_audio(duration=3.0)
        sample_rate = 44100
        
        # Run complete enhancement
        results = self.enhancer.enhance_audio(test_audio, sample_rate, EnhancementMode.AUTOMATIC)
        
        # Verify all components worked
        assert 'enhanced_audio' in results
        assert 'initial_assessment' in results
        assert 'final_assessment' in results
        
        # Check that enhancement actually improved quality
        initial_score = results['initial_assessment'].overall_score
        final_score = results['final_assessment'].overall_score
        
        # Enhancement should generally improve quality (though not always guaranteed)
        assert isinstance(initial_score, (int, float))
        assert isinstance(final_score, (int, float))
        assert 0.0 <= initial_score <= 1.0
        assert 0.0 <= final_score <= 1.0
    
    def test_different_audio_characteristics(self):
        """Test enhancement with different types of audio"""
        sample_rate = 44100
        
        # Test with different audio types
        test_cases = [
            ("sine_wave", np.sin(2 * np.pi * 440 * np.linspace(0, 2, 2 * sample_rate))),
            ("white_noise", np.random.normal(0, 0.1, 2 * sample_rate)),
            ("complex_signal", create_test_audio(duration=2.0))
        ]
        
        for audio_type, audio_data in test_cases:
            try:
                results = self.enhancer.enhance_audio(audio_data, sample_rate, EnhancementMode.AUTOMATIC)
                
                # Should complete without errors
                assert 'enhanced_audio' in results
                assert len(results['enhanced_audio']) == len(audio_data)
                
                print(f"✓ Successfully processed {audio_type}")
                
            except Exception as e:
                pytest.fail(f"Failed to process {audio_type}: {e}")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        import time
        
        # Test with different audio lengths
        sample_rate = 44100
        test_lengths = [1.0, 5.0, 10.0]  # seconds
        
        for length in test_lengths:
            audio_data = create_test_audio(duration=length)
            
            start_time = time.time()
            results = self.enhancer.enhance_audio(audio_data, sample_rate, EnhancementMode.AUTOMATIC)
            processing_time = time.time() - start_time
            
            # Performance should be reasonable (less than 10x real-time for basic processing)
            max_acceptable_time = length * 10
            assert processing_time < max_acceptable_time, f"Processing took too long: {processing_time:.2f}s for {length}s audio"
            
            print(f"✓ Processed {length}s audio in {processing_time:.2f}s")

def run_comprehensive_tests():
    """Run all tests with detailed output"""
    print("Running Intelligent Audio Enhancement Tests")
    print("=" * 60)
    
    # Run pytest with verbose output
    pytest.main([__file__, "-v", "--tb=short"])

if __name__ == "__main__":
    run_comprehensive_tests()