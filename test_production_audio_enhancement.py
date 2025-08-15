"""
Comprehensive tests for Production AI Audio Enhancement System

Tests all major functionality including:
- Neural audio enhancement
- Real-time processing
- Quality assessment
- Batch processing
- Database operations
- Error handling and fallbacks

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import numpy as np
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
import soundfile as sf

from production_audio_enhancement_system import (
    ProductionAudioEnhancementSystem,
    EnhancementConfig,
    EnhancementType,
    QualityMetric,
    ProcessingMode,
    AudioFile,
    QualityMetrics,
    EnhancementResult,
    NeuralDenoiser,
    SpeechEnhancer,
    QualityAssessor,
    RealTimeProcessor,
    AudioEnhancementDatabase
)


class TestProductionAudioEnhancementSystem(unittest.TestCase):
    """Test suite for Production Audio Enhancement System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_audio_enhancement.db")
        self.system = ProductionAudioEnhancementSystem(
            db_path=self.db_path, 
            gpu_acceleration=False  # Use CPU for testing
        )
        
        # Create test audio
        self.sample_rate = 16000
        self.duration = 1.0
        self.test_audio = self._create_test_audio()
        self.test_file = os.path.join(self.temp_dir, "test_audio.wav")
        sf.write(self.test_file, self.test_audio, self.sample_rate)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_audio(self) -> np.ndarray:
        """Create synthetic test audio with noise"""
        t = np.linspace(0, self.duration, int(self.sample_rate * self.duration), False)
        # Speech-like signal
        signal = (
            np.sin(2 * np.pi * 200 * t) * 0.3 +
            np.sin(2 * np.pi * 400 * t) * 0.2 +
            np.sin(2 * np.pi * 600 * t) * 0.1
        )
        # Add noise
        noise = np.random.normal(0, 0.05, len(signal))
        return signal + noise
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.system, ProductionAudioEnhancementSystem)
        self.assertIsInstance(self.system.denoiser, NeuralDenoiser)
        self.assertIsInstance(self.system.enhancer, SpeechEnhancer)
        self.assertIsInstance(self.system.quality_assessor, QualityAssessor)
        self.assertIsInstance(self.system.real_time_processor, RealTimeProcessor)
        self.assertIsInstance(self.system.db, AudioEnhancementDatabase)
    
    def test_enhancement_config(self):
        """Test enhancement configuration"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE,
            strength=0.8,
            preserve_speech=True,
            gpu_acceleration=False
        )
        
        self.assertEqual(config.enhancement_type, EnhancementType.DENOISE)
        self.assertEqual(config.strength, 0.8)
        self.assertTrue(config.preserve_speech)
        self.assertFalse(config.gpu_acceleration)
        
        # Test serialization
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['enhancement_type'], 'denoise')
    
    def test_denoise_enhancement(self):
        """Test denoising enhancement"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE,
            strength=0.7
        )
        
        output_file = os.path.join(self.temp_dir, "denoised.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        self.assertIsInstance(result, EnhancementResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.session_id)
        self.assertTrue(os.path.exists(output_file))
        self.assertGreater(result.processing_time, 0)
    
    def test_speech_enhancement(self):
        """Test speech enhancement"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.SPEECH_ENHANCE,
            strength=0.8
        )
        
        output_file = os.path.join(self.temp_dir, "enhanced.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))
    
    def test_noise_suppression(self):
        """Test noise suppression (combined enhancement)"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.NOISE_SUPPRESS,
            strength=0.6
        )
        
        output_file = os.path.join(self.temp_dir, "suppressed.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))
    
    def test_volume_normalization(self):
        """Test volume normalization"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.VOLUME_NORMALIZE,
            strength=1.0
        )
        
        output_file = os.path.join(self.temp_dir, "normalized.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))
        
        # Check that volume was actually normalized
        original_audio, _ = sf.read(self.test_file)
        normalized_audio, _ = sf.read(output_file)
        
        original_rms = np.sqrt(np.mean(original_audio**2))
        normalized_rms = np.sqrt(np.mean(normalized_audio**2))
        
        # Normalized audio should have different RMS
        self.assertNotAlmostEqual(original_rms, normalized_rms, places=3)
    
    def test_quality_assessment(self):
        """Test audio quality assessment"""
        assessor = QualityAssessor()
        
        # Test quality assessment
        metrics = assessor.assess_quality(self.test_audio, None, self.sample_rate)
        
        self.assertIsInstance(metrics, QualityMetrics)
        self.assertIsNotNone(metrics.snr_db)
        self.assertIsNotNone(metrics.perceptual_quality)
        self.assertGreater(metrics.processing_time, 0)
        
        # Test with reference audio
        reference = self.test_audio + np.random.normal(0, 0.01, len(self.test_audio))
        metrics_with_ref = assessor.assess_quality(self.test_audio, reference, self.sample_rate)
        
        self.assertIsNotNone(metrics_with_ref.spectral_distance)
    
    def test_batch_processing(self):
        """Test batch audio enhancement"""
        # Create multiple test files
        test_files = []
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"test_batch_{i}.wav")
            sf.write(file_path, self.test_audio, self.sample_rate)
            test_files.append(file_path)
        
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE,
            strength=0.5
        )
        
        output_dir = os.path.join(self.temp_dir, "batch_output")
        results = self.system.batch_enhance(test_files, output_dir, config)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result.success)
        
        # Check output files exist
        self.assertTrue(os.path.exists(output_dir))
        output_files = os.listdir(output_dir)
        self.assertEqual(len(output_files), 3)
    
    def test_real_time_processing(self):
        """Test real-time audio processing"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE,
            real_time=True
        )
        
        # Start real-time processing
        self.system.start_real_time_enhancement(config)
        
        # Process some chunks
        chunk_size = 1024
        chunks = []
        for i in range(5):
            start_idx = i * chunk_size
            end_idx = min(start_idx + chunk_size, len(self.test_audio))
            if start_idx < len(self.test_audio):
                chunk = self.test_audio[start_idx:end_idx]
                processed_chunk = self.system.process_real_time_chunk(chunk)
                chunks.append(processed_chunk)
        
        self.system.stop_real_time_enhancement()
        
        self.assertEqual(len(chunks), 5)
        for chunk in chunks:
            self.assertIsInstance(chunk, np.ndarray)
    
    def test_database_operations(self):
        """Test database storage and retrieval"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE,
            strength=0.6
        )
        
        output_file = os.path.join(self.temp_dir, "db_test.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        # Test history retrieval
        history = self.system.get_enhancement_history(limit=10)
        self.assertGreater(len(history), 0)
        
        # Check latest entry
        latest = history[0]
        self.assertEqual(latest['enhancement_type'], 'denoise')
        self.assertEqual(latest['success'], 1)
        
        # Test analytics
        analytics = self.system.get_performance_analytics()
        self.assertIn('denoise', analytics)
        self.assertGreater(analytics['denoise']['success_rate'], 0)
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.DENOISE
        )
        
        # Test with non-existent input file
        result = self.system.enhance_audio("/nonexistent/file.wav", "output.wav", config)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        
        # Test with invalid output path
        result = self.system.enhance_audio(self.test_file, "/invalid/path/output.wav", config)
        self.assertFalse(result.success)
    
    def test_neural_denoiser(self):
        """Test neural denoiser component"""
        denoiser = NeuralDenoiser(gpu=False)
        
        # Test without loading model (should use fallback)
        enhanced = denoiser.denoise(self.test_audio, self.sample_rate)
        self.assertIsInstance(enhanced, np.ndarray)
        self.assertEqual(len(enhanced), len(self.test_audio))
        
        # Test with model loading
        denoiser.load_model()
        enhanced_with_model = denoiser.denoise(self.test_audio, self.sample_rate)
        self.assertIsInstance(enhanced_with_model, np.ndarray)
    
    def test_speech_enhancer(self):
        """Test speech enhancer component"""
        enhancer = SpeechEnhancer(gpu=False)
        
        # Test enhancement
        enhanced = enhancer.enhance(self.test_audio, self.sample_rate)
        self.assertIsInstance(enhanced, np.ndarray)
        self.assertEqual(len(enhanced), len(self.test_audio))
        
        # Test with model loading
        enhancer.load_model()
        enhanced_with_model = enhancer.enhance(self.test_audio, self.sample_rate)
        self.assertIsInstance(enhanced_with_model, np.ndarray)
    
    def test_audio_file_metadata(self):
        """Test audio file metadata creation"""
        audio_file = self.system._create_audio_file_metadata(
            self.test_file, self.test_audio, self.sample_rate
        )
        
        self.assertIsInstance(audio_file, AudioFile)
        self.assertEqual(audio_file.file_path, self.test_file)
        self.assertEqual(audio_file.sample_rate, self.sample_rate)
        self.assertAlmostEqual(audio_file.duration, self.duration, places=1)
    
    def test_session_id_generation(self):
        """Test session ID generation"""
        config = EnhancementConfig(enhancement_type=EnhancementType.DENOISE)
        
        session_id1 = self.system._generate_session_id(self.test_file, config)
        session_id2 = self.system._generate_session_id(self.test_file, config)
        
        # Should be consistent for same inputs
        self.assertIsInstance(session_id1, str)
        self.assertEqual(len(session_id1), 32)  # MD5 hash length
    
    @patch('production_audio_enhancement_system.TORCH_AVAILABLE', False)
    def test_cpu_fallback(self):
        """Test CPU fallback when PyTorch is not available"""
        system_cpu = ProductionAudioEnhancementSystem(gpu_acceleration=False)
        
        config = EnhancementConfig(enhancement_type=EnhancementType.DENOISE)
        output_file = os.path.join(self.temp_dir, "cpu_fallback.wav")
        
        result = system_cpu.enhance_audio(self.test_file, output_file, config)
        self.assertTrue(result.success)
    
    def test_enhancement_strength_scaling(self):
        """Test enhancement strength scaling"""
        # Test with different strength values
        strengths = [0.0, 0.5, 1.0]
        results = []
        
        for strength in strengths:
            config = EnhancementConfig(
                enhancement_type=EnhancementType.DENOISE,
                strength=strength
            )
            
            output_file = os.path.join(self.temp_dir, f"strength_{strength}.wav")
            result = self.system.enhance_audio(self.test_file, output_file, config)
            results.append(result)
        
        # All should succeed
        for result in results:
            self.assertTrue(result.success)
    
    def test_bandwidth_extension(self):
        """Test bandwidth extension enhancement"""
        config = EnhancementConfig(
            enhancement_type=EnhancementType.BANDWIDTH_EXTEND,
            strength=0.7
        )
        
        output_file = os.path.join(self.temp_dir, "bandwidth_extended.wav")
        result = self.system.enhance_audio(self.test_file, output_file, config)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))
    
    def test_echo_cancellation(self):
        """Test echo cancellation enhancement"""
        # Create audio with echo
        delay_samples = int(0.1 * self.sample_rate)  # 100ms delay
        echo_audio = self.test_audio.copy()
        if len(echo_audio) > delay_samples:
            echo_audio[delay_samples:] += 0.3 * echo_audio[:-delay_samples]
        
        echo_file = os.path.join(self.temp_dir, "echo_audio.wav")
        sf.write(echo_file, echo_audio, self.sample_rate)
        
        config = EnhancementConfig(
            enhancement_type=EnhancementType.ECHO_CANCEL,
            strength=0.8
        )
        
        output_file = os.path.join(self.temp_dir, "echo_cancelled.wav")
        result = self.system.enhance_audio(echo_file, output_file, config)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))


class TestEnhancementDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.db")
        self.db = AudioEnhancementDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_database_initialization(self):
        """Test database schema creation"""
        # Check that database file exists
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that tables exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'audio_files',
                'enhancement_sessions',
                'quality_metrics',
                'performance_analytics'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables)
    
    def test_audio_file_storage(self):
        """Test audio file metadata storage"""
        audio_file = AudioFile(
            file_path="/test/audio.wav",
            sample_rate=16000,
            duration=3.0,
            channels=1,
            bit_depth=16,
            file_size=96000,
            format=".wav"
        )
        
        file_id = self.db.store_audio_file(audio_file)
        self.assertGreater(file_id, 0)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Audio Enhancement Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.makeSuite(TestProductionAudioEnhancementSystem))
    test_suite.addTest(unittest.makeSuite(TestEnhancementDatabase))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)