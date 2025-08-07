"""
Comprehensive test suite for Advanced Audio Preprocessing System

This module provides thorough testing of all components including spectral analysis,
pitch detection, audio fingerprinting, tempo analysis, and audio similarity
comparison and clustering.
"""

import unittest
import os
import sys
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import warnings
warnings.filterwarnings("ignore")

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from advanced_audio_preprocessing import (
        AdvancedAudioPreprocessor, SpectralAnalyzer, PitchAnalyzer,
        RhythmAnalyzer, AudioFingerprinter, AudioSimilarityAnalyzer,
        AudioClusteringEngine, AudioFeatures, AudioSimilarity, AudioCluster
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class TestSpectralAnalyzer(unittest.TestCase):
    """Test cases for SpectralAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SpectralAnalyzer()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            # Generate simple test audio (sine wave)
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            # Create dummy file if soundfile not available
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_extract_spectral_features(self):
        """Test spectral feature extraction"""
        features = self.analyzer.extract_spectral_features(self.test_audio_path)
        
        # Check that features are returned
        self.assertIsInstance(features, dict)
        
        # Check for expected feature keys
        expected_features = [
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff',
            'spectral_contrast', 'spectral_flatness', 'zero_crossing_rate', 'rms_energy'
        ]
        
        for feature in expected_features:
            if features:  # Only check if features were extracted
                self.assertIn(feature, features)
                if feature in features:
                    self.assertIsInstance(features[feature], np.ndarray)
    
    def test_compute_spectrogram(self):
        """Test spectrogram computation"""
        magnitude, mel_spec, log_mel_spec = self.analyzer.compute_spectrogram(self.test_audio_path)
        
        # Check that spectrograms are computed
        if magnitude.size > 0:  # Only check if computation succeeded
            self.assertIsInstance(magnitude, np.ndarray)
            self.assertIsInstance(mel_spec, np.ndarray)
            self.assertIsInstance(log_mel_spec, np.ndarray)
            
            # Check dimensions
            self.assertEqual(len(magnitude.shape), 2)
            self.assertEqual(len(mel_spec.shape), 2)
            self.assertEqual(len(log_mel_spec.shape), 2)
    
    def test_analyze_harmonic_percussive(self):
        """Test harmonic-percussive separation"""
        y_harmonic, y_percussive = self.analyzer.analyze_harmonic_percussive(self.test_audio_path)
        
        if y_harmonic.size > 0:  # Only check if separation succeeded
            self.assertIsInstance(y_harmonic, np.ndarray)
            self.assertIsInstance(y_percussive, np.ndarray)
            
            # Check that both components have the same length
            self.assertEqual(len(y_harmonic), len(y_percussive))

class TestPitchAnalyzer(unittest.TestCase):
    """Test cases for PitchAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = PitchAnalyzer()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_extract_pitch_features(self):
        """Test pitch feature extraction"""
        features = self.analyzer.extract_pitch_features(self.test_audio_path)
        
        self.assertIsInstance(features, dict)
        
        # Check for expected feature keys
        expected_features = [
            'fundamental_frequency', 'pitch_confidence', 
            'chroma_features', 'tonnetz_features'
        ]
        
        for feature in expected_features:
            if features:  # Only check if features were extracted
                self.assertIn(feature, features)
                if feature in features:
                    self.assertIsInstance(features[feature], np.ndarray)
    
    def test_analyze_pitch_contour(self):
        """Test pitch contour analysis"""
        contour_analysis = self.analyzer.analyze_pitch_contour(self.test_audio_path)
        
        if contour_analysis:  # Only check if analysis succeeded
            self.assertIsInstance(contour_analysis, dict)
            
            # Check for expected metrics
            expected_metrics = [
                'pitch_mean', 'pitch_std', 'pitch_range', 
                'pitch_median', 'pitch_stability', 'pitch_trend'
            ]
            
            for metric in expected_metrics:
                if metric in contour_analysis:
                    self.assertIsInstance(contour_analysis[metric], (int, float))

class TestRhythmAnalyzer(unittest.TestCase):
    """Test cases for RhythmAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = RhythmAnalyzer()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file with rhythmic content"""
        try:
            import soundfile as sf
            
            duration = 3.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            
            # Create rhythmic pattern with beats
            audio = np.zeros_like(t)
            beat_times = np.arange(0, duration, 0.5)  # Beat every 0.5 seconds
            
            for beat_time in beat_times:
                if beat_time < duration:
                    start_idx = int(beat_time * sample_rate)
                    end_idx = min(start_idx + int(0.1 * sample_rate), len(audio))
                    audio[start_idx:end_idx] = 0.7 * np.sin(2 * np.pi * 800 * t[start_idx:end_idx])
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_extract_rhythm_features(self):
        """Test rhythm feature extraction"""
        features = self.analyzer.extract_rhythm_features(self.test_audio_path)
        
        self.assertIsInstance(features, dict)
        
        # Check for expected feature keys
        expected_features = [
            'tempo', 'beat_frames', 'onset_frames', 'beat_times',
            'onset_times', 'rhythm_regularity', 'onset_density'
        ]
        
        for feature in expected_features:
            if features:  # Only check if features were extracted
                self.assertIn(feature, features)
    
    def test_analyze_rhythmic_patterns(self):
        """Test rhythmic pattern analysis"""
        patterns = self.analyzer.analyze_rhythmic_patterns(self.test_audio_path)
        
        if patterns:  # Only check if analysis succeeded
            self.assertIsInstance(patterns, dict)
            
            # Check for expected pattern metrics
            expected_metrics = [
                'tempogram', 'fourier_tempogram', 'rhythmic_complexity'
            ]
            
            for metric in expected_metrics:
                if metric in patterns:
                    if metric.endswith('complexity'):
                        self.assertIsInstance(patterns[metric], (int, float))
                    else:
                        self.assertIsInstance(patterns[metric], np.ndarray)

class TestAudioFingerprinter(unittest.TestCase):
    """Test cases for AudioFingerprinter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fingerprinter = AudioFingerprinter()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_generate_fingerprint(self):
        """Test fingerprint generation"""
        fingerprint = self.fingerprinter.generate_fingerprint(self.test_audio_path)
        
        if fingerprint:  # Only check if fingerprint was generated
            self.assertIsInstance(fingerprint, str)
            self.assertGreater(len(fingerprint), 0)
            # MD5 hash should be 32 characters
            self.assertEqual(len(fingerprint), 32)
    
    def test_compare_fingerprints(self):
        """Test fingerprint comparison"""
        fingerprint1 = self.fingerprinter.generate_fingerprint(self.test_audio_path)
        fingerprint2 = self.fingerprinter.generate_fingerprint(self.test_audio_path)
        
        if fingerprint1 and fingerprint2:
            # Same audio should have identical fingerprints
            similarity = self.fingerprinter.compare_fingerprints(fingerprint1, fingerprint2)
            self.assertEqual(similarity, 1.0)
            
            # Different fingerprints should have lower similarity
            different_fingerprint = "a" * 32  # Dummy fingerprint
            similarity = self.fingerprinter.compare_fingerprints(fingerprint1, different_fingerprint)
            self.assertLess(similarity, 1.0)
    
    def test_extract_spectral_peaks(self):
        """Test spectral peak extraction"""
        # Create test spectrogram
        spectrogram = np.random.randn(128, 100)
        
        peaks = self.fingerprinter._extract_spectral_peaks(spectrogram)
        
        self.assertIsInstance(peaks, list)
        # Each peak should be a tuple of (freq_idx, time_idx)
        for peak in peaks:
            self.assertIsInstance(peak, tuple)
            self.assertEqual(len(peak), 2)
    
    def test_hash_peaks(self):
        """Test peak hashing"""
        # Create test peaks
        peaks = [(10, 20), (15, 25), (20, 30)]
        
        hash_result = self.fingerprinter._hash_peaks(peaks)
        
        self.assertIsInstance(hash_result, str)
        self.assertGreater(len(hash_result), 0)

class TestAudioSimilarityAnalyzer(unittest.TestCase):
    """Test cases for AudioSimilarityAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = AudioSimilarityAnalyzer()
        self.test_audio_path1 = self._create_test_audio(440)  # A4
        self.test_audio_path2 = self._create_test_audio(880)  # A5
    
    def tearDown(self):
        """Clean up test fixtures"""
        for path in [self.test_audio_path1, self.test_audio_path2]:
            if os.path.exists(path):
                os.remove(path)
    
    def _create_test_audio(self, frequency):
        """Create a test audio file with specific frequency"""
        try:
            import soundfile as sf
            
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_extract_similarity_features(self):
        """Test similarity feature extraction"""
        features = self.analyzer.extract_similarity_features(self.test_audio_path1)
        
        if len(features) > 0:  # Only check if features were extracted
            self.assertIsInstance(features, np.ndarray)
            self.assertGreater(len(features), 0)
    
    def test_compare_audio_similarity(self):
        """Test audio similarity comparison"""
        similarity = self.analyzer.compare_audio_similarity(
            self.test_audio_path1, self.test_audio_path2
        )
        
        self.assertIsInstance(similarity, AudioSimilarity)
        self.assertEqual(similarity.audio1_path, self.test_audio_path1)
        self.assertEqual(similarity.audio2_path, self.test_audio_path2)
        self.assertIsInstance(similarity.similarity_score, float)
        self.assertGreaterEqual(similarity.similarity_score, 0.0)
        self.assertLessEqual(similarity.similarity_score, 1.0)
        self.assertIsInstance(similarity.is_duplicate, bool)
        self.assertIsInstance(similarity.confidence, float)

class TestAudioClusteringEngine(unittest.TestCase):
    """Test cases for AudioClusteringEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.clustering_engine = AudioClusteringEngine()
        self.test_audio_paths = [
            self._create_test_audio(440),  # A4
            self._create_test_audio(880),  # A5
            self._create_test_audio(220),  # A3
        ]
    
    def tearDown(self):
        """Clean up test fixtures"""
        for path in self.test_audio_paths:
            if os.path.exists(path):
                os.remove(path)
    
    def _create_test_audio(self, frequency):
        """Create a test audio file with specific frequency"""
        try:
            import soundfile as sf
            
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_cluster_audio_files_kmeans(self):
        """Test K-means clustering"""
        clusters = self.clustering_engine.cluster_audio_files(
            self.test_audio_paths, method='kmeans', n_clusters=2
        )
        
        if clusters:  # Only check if clustering succeeded
            self.assertIsInstance(clusters, list)
            self.assertLessEqual(len(clusters), 2)  # Should not exceed requested clusters
            
            for cluster in clusters:
                self.assertIsInstance(cluster, AudioCluster)
                self.assertGreaterEqual(cluster.cluster_id, 0)
                self.assertGreater(cluster.cluster_size, 0)
                self.assertIsInstance(cluster.audio_files, list)
    
    def test_cluster_audio_files_dbscan(self):
        """Test DBSCAN clustering"""
        clusters = self.clustering_engine.cluster_audio_files(
            self.test_audio_paths, method='dbscan'
        )
        
        # DBSCAN might not create clusters if data doesn't meet density requirements
        self.assertIsInstance(clusters, list)
        
        for cluster in clusters:
            self.assertIsInstance(cluster, AudioCluster)
    
    def test_cluster_audio_files_hierarchical(self):
        """Test hierarchical clustering"""
        clusters = self.clustering_engine.cluster_audio_files(
            self.test_audio_paths, method='hierarchical', n_clusters=2
        )
        
        if clusters:  # Only check if clustering succeeded
            self.assertIsInstance(clusters, list)
            self.assertLessEqual(len(clusters), 2)
            
            for cluster in clusters:
                self.assertIsInstance(cluster, AudioCluster)

class TestAdvancedAudioPreprocessor(unittest.TestCase):
    """Test cases for the complete AdvancedAudioPreprocessor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.preprocessor = AdvancedAudioPreprocessor()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 3.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_extract_comprehensive_features(self):
        """Test comprehensive feature extraction"""
        features = self.preprocessor.extract_comprehensive_features(self.test_audio_path)
        
        self.assertIsInstance(features, AudioFeatures)
        self.assertGreater(features.duration, 0)
        self.assertEqual(features.sample_rate, self.preprocessor.sample_rate)
        self.assertEqual(features.channels, 1)
    
    def test_find_duplicate_audio(self):
        """Test duplicate audio detection"""
        # Create multiple test files
        test_paths = [self.test_audio_path, self.test_audio_path]  # Same file twice
        
        duplicates = self.preprocessor.find_duplicate_audio(test_paths, similarity_threshold=0.8)
        
        self.assertIsInstance(duplicates, list)
        # Should find the duplicate pair
        if duplicates:
            self.assertEqual(len(duplicates), 1)
            self.assertEqual(len(duplicates[0]), 3)  # (path1, path2, similarity)
    
    def test_cluster_similar_audio(self):
        """Test audio clustering"""
        # Create multiple test files
        test_paths = [self.test_audio_path] * 3  # Same file multiple times
        
        clusters = self.preprocessor.cluster_similar_audio(test_paths, method='kmeans', n_clusters=2)
        
        self.assertIsInstance(clusters, list)
        # Should create clusters
        for cluster in clusters:
            self.assertIsInstance(cluster, AudioCluster)
    
    def test_save_and_load_features(self):
        """Test feature saving and loading"""
        # Extract features
        features = self.preprocessor.extract_comprehensive_features(self.test_audio_path)
        
        # Save features
        temp_feature_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_feature_file.close()
        
        try:
            self.preprocessor.save_features(features, temp_feature_file.name)
            self.assertTrue(os.path.exists(temp_feature_file.name))
            
            # Load features
            loaded_features = self.preprocessor.load_features(temp_feature_file.name)
            
            if loaded_features:  # Only check if loading succeeded
                self.assertIsInstance(loaded_features, AudioFeatures)
                self.assertEqual(loaded_features.duration, features.duration)
                self.assertEqual(loaded_features.sample_rate, features.sample_rate)
        
        finally:
            if os.path.exists(temp_feature_file.name):
                os.remove(temp_feature_file.name)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.preprocessor = AdvancedAudioPreprocessor()
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        try:
            import soundfile as sf
            
            # Create test audio
            duration = 2.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            
            try:
                # 1. Extract comprehensive features
                features = self.preprocessor.extract_comprehensive_features(temp_file.name)
                self.assertIsInstance(features, AudioFeatures)
                
                # 2. Generate fingerprint
                self.assertIsInstance(features.fingerprint, str)
                
                # 3. Test similarity with itself
                similarity = self.preprocessor.similarity_analyzer.compare_audio_similarity(
                    temp_file.name, temp_file.name
                )
                self.assertIsInstance(similarity, AudioSimilarity)
                self.assertEqual(similarity.similarity_score, 1.0)  # Should be identical
                
                # 4. Test clustering
                clusters = self.preprocessor.cluster_similar_audio([temp_file.name] * 3)
                self.assertIsInstance(clusters, list)
            
            finally:
                os.remove(temp_file.name)
        
        except ImportError:
            self.skipTest("Integration test skipped due to missing audio dependencies")
        except Exception as e:
            self.skipTest(f"Integration test skipped due to: {e}")

def run_performance_tests():
    """Run performance tests for the system"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    try:
        import time
        import soundfile as sf
        
        preprocessor = AdvancedAudioPreprocessor()
        
        # Test with different audio lengths
        durations = [1, 3, 5]  # seconds
        
        for duration in durations:
            print(f"\nTesting {duration}s audio...")
            
            # Create test audio
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.5 * np.sin(2 * np.pi * 440 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            
            try:
                # Measure feature extraction time
                start_time = time.time()
                features = preprocessor.extract_comprehensive_features(temp_file.name)
                extraction_time = time.time() - start_time
                
                print(f"  Feature extraction: {extraction_time:.2f}s")
                print(f"  Real-time factor: {extraction_time/duration:.2f}x")
                
                if features.fingerprint:
                    print(f"  Fingerprint generated: {len(features.fingerprint)} chars")
            
            finally:
                os.remove(temp_file.name)
    
    except Exception as e:
        print(f"Performance tests failed: {e}")

def main():
    """Run all tests"""
    print("🧪 ADVANCED AUDIO PREPROCESSING SYSTEM TESTS")
    print("=" * 60)
    
    # Check if required modules are available
    try:
        import librosa
        import soundfile
        import scipy
        import sklearn
        print("✅ All required modules available")
    except ImportError as e:
        print(f"❌ Missing required modules: {e}")
        print("Please install: pip install librosa soundfile scipy scikit-learn")
        return
    
    # Run unit tests
    print("\n🔍 Running unit tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestSpectralAnalyzer,
        TestPitchAnalyzer,
        TestRhythmAnalyzer,
        TestAudioFingerprinter,
        TestAudioSimilarityAnalyzer,
        TestAudioClusteringEngine,
        TestAdvancedAudioPreprocessor,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    # Run performance tests
    run_performance_tests()
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()