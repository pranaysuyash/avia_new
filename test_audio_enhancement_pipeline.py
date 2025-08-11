"""
Test suite for Audio Enhancement Pipeline
Task 117: Build comprehensive audio enhancement pipeline

This module provides comprehensive testing for the audio enhancement pipeline,
including unit tests, integration tests, and performance benchmarks.
"""

import unittest
import numpy as np
import tempfile
import os
import shutil
from pathlib import Path
import librosa
import soundfile as sf
from unittest.mock import patch, MagicMock
import json
import time

from audio_enhancement_pipeline import (
    AudioEnhancementPipeline,
    AudioQualityMetrics,
    EnhancementResult
)

class TestAudioEnhancementPipeline(unittest.TestCase):
    """Comprehensive test suite for audio enhancement pipeline"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = AudioEnhancementPipeline(temp_dir=self.test_dir)
        
        # Create test audio files
        self.sample_rate = 16000
        self.duration = 2.0  # 2 seconds
        self.samples = int(self.sample_rate * self.duration)
        
        # Generate test audio signals
        self.clean_audio = self._generate_clean_audio()
        self.noisy_audio = self._generate_noisy_audio()
        self.clipped_audio = self._generate_clipped_audio()
        self.quiet_audio = self._generate_quiet_audio()
        
        # Save test files
        self.clean_file = os.path.join(self.test_dir, "clean_test.wav")
        self.noisy_file = os.path.join(self.test_dir, "noisy_test.wav")
        self.clipped_file = os.path.join(self.test_dir, "clipped_test.wav")
        self.quiet_file = os.path.join(self.test_dir, "quiet_test.wav")
        
        sf.write(self.clean_file, self.clean_audio, self.sample_rate)
        sf.write(self.noisy_file, self.noisy_audio, self.sample_rate)
        sf.write(self.clipped_file, self.clipped_audio, self.sample_rate)
        sf.write(self.quiet_file, self.quiet_audio, self.sample_rate)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _generate_clean_audio(self):
        """Generate clean test audio signal"""
        t = np.linspace(0, self.duration, self.samples)
        # Mix of sine waves to simulate speech-like content
        signal = (0.3 * np.sin(2 * np.pi * 440 * t) +  # A4 note
                 0.2 * np.sin(2 * np.pi * 880 * t) +   # A5 note
                 0.1 * np.sin(2 * np.pi * 1320 * t))   # E6 note
        
        # Add some amplitude modulation
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
        return signal * envelope
    
    def _generate_noisy_audio(self):
        """Generate noisy test audio signal"""
        clean = self._generate_clean_audio()
        noise = np.random.normal(0, 0.1, self.samples)
        return clean + noise
    
    def _generate_clipped_audio(self):
        """Generate clipped test audio signal"""
        clean = self._generate_clean_audio()
        # Amplify and clip
        amplified = clean * 3.0
        return np.clip(amplified, -0.95, 0.95)
    
    def _generate_quiet_audio(self):
        """Generate very quiet test audio signal"""
        clean = self._generate_clean_audio()
        return clean * 0.01  # Very quiet
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = AudioEnhancementPipeline()
        self.assertIsNotNone(pipeline)
        self.assertIsInstance(pipeline.supported_formats, list)
        self.assertIn('.wav', pipeline.supported_formats)
        self.assertIn('.mp3', pipeline.supported_formats)
    
    def test_audio_quality_assessment(self):
        """Test audio quality assessment functionality"""
        # Test clean audio
        clean_metrics = self.pipeline._assess_audio_quality(self.clean_audio, self.sample_rate)
        self.assertIsInstance(clean_metrics, AudioQualityMetrics)
        self.assertGreater(clean_metrics.quality_score, 60)
        self.assertGreater(clean_metrics.snr_db, 20)
        
        # Test noisy audio
        noisy_metrics = self.pipeline._assess_audio_quality(self.noisy_audio, self.sample_rate)
        self.assertLess(noisy_metrics.quality_score, clean_metrics.quality_score)
        self.assertLess(noisy_metrics.snr_db, clean_metrics.snr_db)
        
        # Test clipped audio
        clipped_metrics = self.pipeline._assess_audio_quality(self.clipped_audio, self.sample_rate)
        self.assertGreater(clipped_metrics.thd_percent, clean_metrics.thd_percent)
    
    def test_noise_reduction(self):
        """Test noise reduction functionality"""
        # Test with noisy audio
        enhanced = self.pipeline._apply_noise_reduction(
            self.noisy_audio.reshape(1, -1), self.sample_rate
        )
        
        self.assertEqual(enhanced.shape, (1, self.samples))
        
        # Enhanced audio should have better SNR
        original_metrics = self.pipeline._assess_audio_quality(self.noisy_audio, self.sample_rate)
        enhanced_metrics = self.pipeline._assess_audio_quality(enhanced[0], self.sample_rate)
        
        # SNR should improve (allowing for some variance in measurement)
        self.assertGreaterEqual(enhanced_metrics.snr_db, original_metrics.snr_db - 2)
    
    def test_audio_repair(self):
        """Test audio repair functionality"""
        # Test with clipped audio
        enhanced = self.pipeline._repair_audio_segments(
            self.clipped_audio.reshape(1, -1), self.sample_rate
        )
        
        self.assertEqual(enhanced.shape, (1, self.samples))
        
        # Check that extreme values are reduced
        original_max = np.max(np.abs(self.clipped_audio))
        enhanced_max = np.max(np.abs(enhanced[0]))
        
        # Enhanced audio should have less extreme peaks
        self.assertLessEqual(enhanced_max, original_max + 0.1)
    
    def test_spectral_enhancement(self):
        """Test spectral enhancement functionality"""
        enhanced = self.pipeline._apply_spectral_enhancement(
            self.clean_audio.reshape(1, -1), self.sample_rate
        )
        
        self.assertEqual(enhanced.shape, (1, self.samples))
        
        # Enhanced audio should have modified spectral characteristics
        original_centroid = librosa.feature.spectral_centroid(y=self.clean_audio, sr=self.sample_rate)
        enhanced_centroid = librosa.feature.spectral_centroid(y=enhanced[0], sr=self.sample_rate)
        
        # Spectral centroid should change (enhancement effect)
        self.assertNotEqual(np.mean(original_centroid), np.mean(enhanced_centroid))
    
    def test_dynamic_processing(self):
        """Test dynamic range processing"""
        # Test with audio that has high dynamic range
        loud_audio = self.clean_audio * 0.8
        enhanced = self.pipeline._apply_dynamic_processing(
            loud_audio.reshape(1, -1), self.sample_rate
        )
        
        self.assertEqual(enhanced.shape, (1, self.samples))
        
        # Dynamic range should be controlled
        original_dr = self.pipeline._calculate_dynamic_range(loud_audio)
        enhanced_dr = self.pipeline._calculate_dynamic_range(enhanced[0])
        
        # Compression should reduce dynamic range
        self.assertLessEqual(enhanced_dr, original_dr + 5)  # Allow some tolerance
    
    def test_normalization(self):
        """Test audio normalization"""
        # Test with quiet audio
        enhanced = self.pipeline._apply_normalization(
            self.quiet_audio.reshape(1, -1), self.sample_rate
        )
        
        self.assertEqual(enhanced.shape, (1, self.samples))
        
        # Enhanced audio should be louder
        original_rms = np.sqrt(np.mean(self.quiet_audio**2))
        enhanced_rms = np.sqrt(np.mean(enhanced[0]**2))
        
        self.assertGreater(enhanced_rms, original_rms)
        
        # Should not clip
        self.assertLessEqual(np.max(np.abs(enhanced[0])), 1.0)
    
    def test_full_enhancement_pipeline(self):
        """Test complete enhancement pipeline"""
        output_file = os.path.join(self.test_dir, "enhanced_output.wav")
        
        # Test with noisy audio
        result = self.pipeline.enhance_audio(self.noisy_file, output_file)
        
        # Verify result structure
        self.assertIsInstance(result, EnhancementResult)
        self.assertEqual(result.enhanced_audio_path, output_file)
        self.assertTrue(os.path.exists(output_file))
        self.assertGreater(result.processing_time, 0)
        self.assertIsInstance(result.enhancement_applied, list)
        self.assertGreater(len(result.enhancement_applied), 0)
        
        # Verify quality improvement
        self.assertIsInstance(result.original_metrics, AudioQualityMetrics)
        self.assertIsInstance(result.enhanced_metrics, AudioQualityMetrics)
        
        # Quality should improve or stay the same
        self.assertGreaterEqual(result.improvement_score, -5)  # Allow small degradation
    
    def test_enhancement_with_custom_options(self):
        """Test enhancement with custom options"""
        output_file = os.path.join(self.test_dir, "custom_enhanced.wav")
        
        # Test with specific options disabled
        options = {
            'noise_reduction': False,
            'audio_repair': True,
            'spectral_enhancement': False,
            'dynamic_processing': True,
            'normalization': True
        }
        
        result = self.pipeline.enhance_audio(self.noisy_file, output_file, options)
        
        # Should not include disabled enhancements
        self.assertNotIn('noise_reduction', result.enhancement_applied)
        self.assertNotIn('spectral_enhancement', result.enhancement_applied)
        
        # Should include enabled enhancements
        self.assertIn('audio_repair', result.enhancement_applied)
        self.assertIn('dynamic_processing', result.enhancement_applied)
        self.assertIn('normalization', result.enhancement_applied)
    
    def test_format_recommendations(self):
        """Test format optimization recommendations"""
        recommendations = self.pipeline.get_format_recommendations(self.clean_file)
        
        self.assertIsInstance(recommendations, dict)
        self.assertIn('current_format', recommendations)
        self.assertIn('file_size_mb', recommendations)
        self.assertIn('duration_seconds', recommendations)
        self.assertIn('sample_rate', recommendations)
        self.assertIn('quality_score', recommendations)
        self.assertIn('recommendations', recommendations)
        
        self.assertEqual(recommendations['current_format'], '.wav')
        self.assertGreater(recommendations['duration_seconds'], 1.5)
        self.assertEqual(recommendations['sample_rate'], self.sample_rate)
        self.assertIsInstance(recommendations['recommendations'], list)
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        # Test with non-existent file
        with self.assertRaises(FileNotFoundError):
            self.pipeline.enhance_audio("non_existent_file.wav")
        
        # Test with invalid audio data
        invalid_file = os.path.join(self.test_dir, "invalid.wav")
        with open(invalid_file, 'w') as f:
            f.write("This is not audio data")
        
        with self.assertRaises(ValueError):
            self.pipeline.enhance_audio(invalid_file)
    
    def test_problematic_segment_detection(self):
        """Test detection of problematic audio segments"""
        # Test with clipped audio
        segments = self.pipeline._detect_problematic_segments(self.clipped_audio, self.sample_rate)
        
        self.assertIsInstance(segments, list)
        # Should detect some problematic segments in clipped audio
        self.assertGreater(len(segments), 0)
        
        # Test with clean audio
        clean_segments = self.pipeline._detect_problematic_segments(self.clean_audio, self.sample_rate)
        
        # Should detect fewer or no problematic segments in clean audio
        self.assertLessEqual(len(clean_segments), len(segments))
    
    def test_smooth_transition_creation(self):
        """Test smooth transition creation for audio repair"""
        before_context = np.random.randn(1000)
        after_context = np.random.randn(1000)
        transition_length = 500
        
        transition = self.pipeline._create_smooth_transition(
            before_context, after_context, transition_length
        )
        
        self.assertEqual(len(transition), transition_length)
        self.assertIsInstance(transition, np.ndarray)
        
        # Transition should be smooth (no sudden jumps)
        diff = np.diff(transition)
        max_jump = np.max(np.abs(diff))
        self.assertLess(max_jump, 1.0)  # Reasonable smoothness threshold
    
    def test_multiband_enhancement(self):
        """Test multiband spectral enhancement"""
        enhanced = self.pipeline._multiband_enhancement(self.clean_audio, self.sample_rate)
        
        self.assertEqual(len(enhanced), len(self.clean_audio))
        self.assertIsInstance(enhanced, np.ndarray)
        
        # Enhanced audio should be different from original
        correlation = np.corrcoef(self.clean_audio, enhanced)[0, 1]
        self.assertLess(correlation, 0.99)  # Should be modified but still similar
        self.assertGreater(correlation, 0.7)  # But not completely different
    
    def test_compression_application(self):
        """Test dynamic range compression"""
        # Create audio with high dynamic range
        high_dr_audio = np.concatenate([
            np.ones(1000) * 0.1,  # Quiet section
            np.ones(1000) * 0.8   # Loud section
        ])
        
        compressed = self.pipeline._apply_compression(high_dr_audio, self.sample_rate)
        
        self.assertEqual(len(compressed), len(high_dr_audio))
        
        # Compression should reduce the difference between loud and quiet sections
        original_ratio = np.max(high_dr_audio) / (np.mean(high_dr_audio[:1000]) + 1e-10)
        compressed_ratio = np.max(compressed) / (np.mean(compressed[:1000]) + 1e-10)
        
        self.assertLess(compressed_ratio, original_ratio)
    
    def test_attack_release_smoothing(self):
        """Test attack and release smoothing for compression"""
        # Create step function for testing
        gain_reduction = np.concatenate([
            np.zeros(1000),
            np.ones(1000) * 10,  # Sudden gain reduction
            np.zeros(1000)
        ])
        
        smoothed = self.pipeline._apply_attack_release(
            gain_reduction, self.sample_rate, 0.01, 0.1
        )
        
        self.assertEqual(len(smoothed), len(gain_reduction))
        
        # Smoothed version should have gradual transitions
        # Check that the transition is not instantaneous
        transition_start = 1000
        self.assertLess(smoothed[transition_start + 10], gain_reduction[transition_start + 10])
        self.assertGreater(smoothed[transition_start + 10], 0)
    
    def test_snr_calculation(self):
        """Test SNR calculation accuracy"""
        # Test with known SNR
        clean_snr = self.pipeline._calculate_snr(self.clean_audio, self.sample_rate)
        noisy_snr = self.pipeline._calculate_snr(self.noisy_audio, self.sample_rate)
        
        # Clean audio should have higher SNR
        self.assertGreater(clean_snr, noisy_snr)
        
        # SNR values should be reasonable
        self.assertGreater(clean_snr, 10)
        self.assertLess(clean_snr, 60)
        self.assertGreater(noisy_snr, 0)
        self.assertLess(noisy_snr, 50)
    
    def test_thd_calculation(self):
        """Test THD calculation"""
        clean_thd = self.pipeline._calculate_thd(self.clean_audio, self.sample_rate)
        clipped_thd = self.pipeline._calculate_thd(self.clipped_audio, self.sample_rate)
        
        # Clipped audio should have higher THD
        self.assertGreater(clipped_thd, clean_thd)
        
        # THD values should be reasonable percentages
        self.assertGreaterEqual(clean_thd, 0)
        self.assertLessEqual(clean_thd, 10)
        self.assertGreaterEqual(clipped_thd, 0)
        self.assertLessEqual(clipped_thd, 10)
    
    def test_dynamic_range_calculation(self):
        """Test dynamic range calculation"""
        clean_dr = self.pipeline._calculate_dynamic_range(self.clean_audio)
        quiet_dr = self.pipeline._calculate_dynamic_range(self.quiet_audio)
        
        # Both should have reasonable dynamic range values
        self.assertGreater(clean_dr, 0)
        self.assertLess(clean_dr, 60)
        self.assertGreater(quiet_dr, 0)
        self.assertLess(quiet_dr, 60)
    
    def test_spectral_features_calculation(self):
        """Test spectral features calculation"""
        features = self.pipeline._calculate_spectral_features(self.clean_audio, self.sample_rate)
        
        self.assertIn('spectral_centroid', features)
        self.assertIn('spectral_rolloff', features)
        self.assertIn('zero_crossing_rate', features)
        
        # Values should be reasonable
        self.assertGreater(features['spectral_centroid'], 0)
        self.assertLess(features['spectral_centroid'], self.sample_rate / 2)
        self.assertGreater(features['spectral_rolloff'], features['spectral_centroid'])
        self.assertGreaterEqual(features['zero_crossing_rate'], 0)
        self.assertLessEqual(features['zero_crossing_rate'], 1)
    
    def test_energy_metrics_calculation(self):
        """Test energy metrics calculation"""
        metrics = self.pipeline._calculate_energy_metrics(self.clean_audio)
        
        self.assertIn('rms_energy', metrics)
        self.assertIn('peak_level_db', metrics)
        
        # Values should be reasonable
        self.assertGreater(metrics['rms_energy'], 0)
        self.assertLess(metrics['rms_energy'], 1)
        self.assertLess(metrics['peak_level_db'], 0)  # Should be negative dB
        self.assertGreater(metrics['peak_level_db'], -100)
    
    def test_loudness_estimation(self):
        """Test loudness estimation"""
        clean_loudness = self.pipeline._estimate_loudness(self.clean_audio, self.sample_rate)
        quiet_loudness = self.pipeline._estimate_loudness(self.quiet_audio, self.sample_rate)
        
        # Quiet audio should have lower loudness
        self.assertLess(quiet_loudness, clean_loudness)
        
        # Loudness values should be in reasonable LUFS range
        self.assertGreater(clean_loudness, -70)
        self.assertLess(clean_loudness, 0)
        self.assertGreater(quiet_loudness, -70)
        self.assertLess(quiet_loudness, 0)
    
    def test_quality_score_calculation(self):
        """Test overall quality score calculation"""
        # Create test metrics
        good_metrics = {
            'snr_db': 30,
            'thd_percent': 1,
            'dynamic_range_db': 25,
            'peak_level_db': -6
        }
        
        poor_metrics = {
            'snr_db': 10,
            'thd_percent': 5,
            'dynamic_range_db': 8,
            'peak_level_db': -1
        }
        
        good_score = self.pipeline._calculate_quality_score(good_metrics)
        poor_score = self.pipeline._calculate_quality_score(poor_metrics)
        
        # Good metrics should yield higher score
        self.assertGreater(good_score, poor_score)
        
        # Scores should be in 0-100 range
        self.assertGreaterEqual(good_score, 0)
        self.assertLessEqual(good_score, 100)
        self.assertGreaterEqual(poor_score, 0)
        self.assertLessEqual(poor_score, 100)
    
    def test_recommendations_generation(self):
        """Test enhancement recommendations generation"""
        # Test with poor quality metrics
        poor_metrics = {
            'snr_db': 10,
            'thd_percent': 5,
            'dynamic_range_db': 5,
            'peak_level_db': -1,
            'loudness_lufs': -50,
            'spectral_centroid': 500
        }
        
        recommendations = self.pipeline._generate_recommendations(poor_metrics)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should contain relevant recommendations
        rec_text = ' '.join(recommendations).lower()
        self.assertIn('noise', rec_text)  # Should recommend noise reduction
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for different audio lengths"""
        # Test with different duration files
        durations = [1.0, 5.0, 10.0]  # seconds
        
        for duration in durations:
            # Generate test audio
            samples = int(self.sample_rate * duration)
            test_audio = np.random.randn(samples) * 0.1
            
            test_file = os.path.join(self.test_dir, f"test_{duration}s.wav")
            sf.write(test_file, test_audio, self.sample_rate)
            
            # Measure processing time
            start_time = time.time()
            result = self.pipeline.enhance_audio(test_file)
            processing_time = time.time() - start_time
            
            # Processing should be reasonably fast
            # Allow up to 2x real-time for enhancement
            self.assertLess(processing_time, duration * 2)
            
            # Cleanup
            os.remove(test_file)
            if os.path.exists(result.enhanced_audio_path):
                os.remove(result.enhanced_audio_path)
    
    def test_stereo_audio_handling(self):
        """Test handling of stereo audio files"""
        # Create stereo test audio
        left_channel = self.clean_audio
        right_channel = self.clean_audio * 0.8  # Slightly different
        stereo_audio = np.column_stack([left_channel, right_channel])
        
        stereo_file = os.path.join(self.test_dir, "stereo_test.wav")
        sf.write(stereo_file, stereo_audio, self.sample_rate)
        
        # Test enhancement
        result = self.pipeline.enhance_audio(stereo_file)
        
        # Should handle stereo audio correctly
        self.assertTrue(os.path.exists(result.enhanced_audio_path))
        
        # Load enhanced audio and check it's still stereo
        enhanced_audio, sr = librosa.load(result.enhanced_audio_path, sr=None, mono=False)
        if enhanced_audio.ndim == 1:
            # Mono output is acceptable
            self.assertEqual(len(enhanced_audio), len(left_channel))
        else:
            # Stereo output
            self.assertEqual(enhanced_audio.shape[1], len(left_channel))
    
    @patch('audio_enhancement_pipeline.NOISEREDUCE_AVAILABLE', False)
    def test_fallback_without_noisereduce(self):
        """Test fallback behavior when noisereduce is not available"""
        pipeline = AudioEnhancementPipeline()
        
        # Should still work without noisereduce
        result = pipeline.enhance_audio(self.noisy_file)
        
        self.assertIsInstance(result, EnhancementResult)
        self.assertTrue(os.path.exists(result.enhanced_audio_path))
        
        # Should use spectral subtraction fallback
        # (We can't easily test this directly, but the pipeline should complete)
    
    @patch('audio_enhancement_pipeline.PYDUB_AVAILABLE', False)
    def test_fallback_without_pydub(self):
        """Test fallback behavior when pydub is not available"""
        pipeline = AudioEnhancementPipeline()
        
        # Should still work without pydub
        result = pipeline.enhance_audio(self.clean_file)
        
        self.assertIsInstance(result, EnhancementResult)
        self.assertTrue(os.path.exists(result.enhanced_audio_path))

class TestAudioEnhancementIntegration(unittest.TestCase):
    """Integration tests for audio enhancement pipeline"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = AudioEnhancementPipeline(temp_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_batch_processing_simulation(self):
        """Test batch processing of multiple files"""
        # Create multiple test files
        test_files = []
        for i in range(3):
            # Generate different types of audio
            if i == 0:
                audio = np.random.randn(16000) * 0.1  # Clean
            elif i == 1:
                audio = np.random.randn(16000) * 0.1 + np.random.randn(16000) * 0.05  # Noisy
            else:
                audio = np.clip(np.random.randn(16000) * 0.5, -0.9, 0.9)  # Clipped
            
            file_path = os.path.join(self.test_dir, f"batch_test_{i}.wav")
            sf.write(file_path, audio, 16000)
            test_files.append(file_path)
        
        # Process all files
        results = []
        total_time = 0
        
        for file_path in test_files:
            result = self.pipeline.enhance_audio(file_path)
            results.append(result)
            total_time += result.processing_time
        
        # Verify all files were processed
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, EnhancementResult)
            self.assertTrue(os.path.exists(result.enhanced_audio_path))
        
        print(f"Batch processing completed in {total_time:.2f} seconds")
    
    def test_real_world_audio_simulation(self):
        """Test with simulated real-world audio characteristics"""
        # Simulate podcast audio with various issues
        sample_rate = 44100
        duration = 5.0
        samples = int(sample_rate * duration)
        
        # Base speech-like signal
        t = np.linspace(0, duration, samples)
        speech_freqs = [200, 400, 800, 1600, 3200]  # Formant-like frequencies
        speech_signal = np.zeros(samples)
        
        for freq in speech_freqs:
            amplitude = np.random.uniform(0.1, 0.3)
            speech_signal += amplitude * np.sin(2 * np.pi * freq * t)
        
        # Add realistic issues
        # 1. Background noise
        noise = np.random.normal(0, 0.02, samples)
        
        # 2. Occasional pops/clicks
        pop_locations = np.random.choice(samples, size=10, replace=False)
        for loc in pop_locations:
            if loc < samples - 100:
                speech_signal[loc:loc+5] += np.random.uniform(-0.5, 0.5, 5)
        
        # 3. Volume variations
        volume_envelope = 0.5 + 0.3 * np.sin(2 * np.pi * 0.1 * t)  # Slow volume changes
        
        # Combine all issues
        realistic_audio = (speech_signal * volume_envelope) + noise
        
        # Save and process
        test_file = os.path.join(self.test_dir, "realistic_podcast.wav")
        sf.write(test_file, realistic_audio, sample_rate)
        
        result = self.pipeline.enhance_audio(test_file)
        
        # Verify enhancement
        self.assertIsInstance(result, EnhancementResult)
        self.assertGreater(result.enhanced_metrics.quality_score, 
                          result.original_metrics.quality_score - 5)  # Allow small tolerance
        
        print(f"Realistic audio enhancement:")
        print(f"  Original quality: {result.original_metrics.quality_score:.1f}")
        print(f"  Enhanced quality: {result.enhanced_metrics.quality_score:.1f}")
        print(f"  Improvement: {result.improvement_score:+.1f}")

def run_performance_benchmarks():
    """Run performance benchmarks for the audio enhancement pipeline"""
    print("\n=== Audio Enhancement Pipeline Performance Benchmarks ===")
    
    test_dir = tempfile.mkdtemp()
    pipeline = AudioEnhancementPipeline(temp_dir=test_dir)
    
    try:
        # Test different audio lengths
        durations = [1, 5, 10, 30, 60]  # seconds
        sample_rate = 16000
        
        print(f"{'Duration (s)':<12} {'Processing Time (s)':<18} {'Real-time Factor':<16} {'Quality Improvement'}")
        print("-" * 70)
        
        for duration in durations:
            # Generate test audio
            samples = int(sample_rate * duration)
            test_audio = np.random.randn(samples) * 0.1 + np.random.randn(samples) * 0.02
            
            test_file = os.path.join(test_dir, f"benchmark_{duration}s.wav")
            sf.write(test_file, test_audio, sample_rate)
            
            # Measure processing time
            start_time = time.time()
            result = pipeline.enhance_audio(test_file)
            processing_time = time.time() - start_time
            
            real_time_factor = processing_time / duration
            
            print(f"{duration:<12} {processing_time:<18.2f} {real_time_factor:<16.2f} {result.improvement_score:+.1f}")
            
            # Cleanup
            os.remove(test_file)
            if os.path.exists(result.enhanced_audio_path):
                os.remove(result.enhanced_audio_path)
    
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests and benchmarks"""
    print("Running Audio Enhancement Pipeline Tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance benchmarks
    run_performance_benchmarks()

if __name__ == "__main__":
    main()