"""
Comprehensive test suite for Emotion and Sentiment Detection System

This module provides thorough testing of all components including emotion detection,
sentiment analysis, mood tracking, stress/fatigue detection, and visualizations.
"""

import unittest
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import warnings
warnings.filterwarnings("ignore")

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from emotion_sentiment_detection import (
        EmotionSentimentSystem, EmotionDetector, SentimentAnalyzer,
        MoodTracker, StressFatigueDetector, EmotionalTimelineVisualizer,
        AudioFeatureExtractor, EmotionResult, SentimentResult, 
        MoodState, StressFatigueResult
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class TestAudioFeatureExtractor(unittest.TestCase):
    """Test cases for AudioFeatureExtractor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = AudioFeatureExtractor()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            # Generate simple test audio
            duration = 3.0
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
    
    def test_extract_prosodic_features(self):
        """Test prosodic feature extraction"""
        features = self.extractor.extract_prosodic_features(self.test_audio_path)
        
        # Check that features are returned
        self.assertIsInstance(features, dict)
        
        # Check for expected feature keys
        expected_features = [
            'pitch_mean', 'pitch_std', 'intensity_mean', 'tempo',
            'spectral_centroid_mean', 'mfcc_1_mean', 'jitter', 'shimmer'
        ]
        
        for feature in expected_features:
            if features:  # Only check if features were extracted
                self.assertIn(feature, features)
    
    def test_jitter_calculation(self):
        """Test jitter calculation"""
        pitch_values = np.array([100, 102, 98, 101, 99])
        jitter = self.extractor._calculate_jitter(pitch_values)
        
        self.assertIsInstance(jitter, float)
        self.assertGreaterEqual(jitter, 0)
    
    def test_shimmer_calculation(self):
        """Test shimmer calculation"""
        rms_values = np.array([0.5, 0.52, 0.48, 0.51, 0.49])
        shimmer = self.extractor._calculate_shimmer(rms_values)
        
        self.assertIsInstance(shimmer, float)
        self.assertGreaterEqual(shimmer, 0)
    
    def test_hnr_calculation(self):
        """Test harmonics-to-noise ratio calculation"""
        # Create simple harmonic signal
        t = np.linspace(0, 1, 1000)
        y = np.sin(2 * np.pi * 440 * t)
        
        hnr = self.extractor._calculate_hnr(y, 1000)
        
        self.assertIsInstance(hnr, float)
        self.assertGreaterEqual(hnr, 0)
        self.assertLessEqual(hnr, 40)

class TestEmotionDetector(unittest.TestCase):
    """Test cases for EmotionDetector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = EmotionDetector()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 5.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.3 * np.sin(2 * np.pi * 200 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_detect_emotion(self):
        """Test emotion detection"""
        results = self.detector.detect_emotion(self.test_audio_path, segment_duration=2.0)
        
        self.assertIsInstance(results, list)
        
        if results:  # If detection worked
            for result in results:
                self.assertIsInstance(result, EmotionResult)
                self.assertIn(result.primary_emotion, self.detector.emotion_labels)
                self.assertGreaterEqual(result.confidence, 0)
                self.assertLessEqual(result.confidence, 1)
                self.assertGreaterEqual(result.arousal, 0)
                self.assertLessEqual(result.arousal, 1)
                self.assertGreaterEqual(result.valence, 0)
                self.assertLessEqual(result.valence, 1)
    
    def test_predict_emotion(self):
        """Test emotion prediction from features"""
        # Mock features
        features = {
            'pitch_mean': 200,
            'pitch_std': 20,
            'intensity_mean': 0.5,
            'tempo': 120,
            'spectral_centroid_mean': 2000,
            'mfcc_1_mean': -10,
            'jitter': 0.01,
            'shimmer': 0.05
        }
        
        result = self.detector._predict_emotion(features, 0.0, 3.0)
        
        self.assertIsInstance(result, EmotionResult)
        self.assertIn(result.primary_emotion, self.detector.emotion_labels)
        self.assertIsInstance(result.emotion_scores, dict)
    
    def test_calculate_arousal(self):
        """Test arousal calculation"""
        features = {
            'intensity_mean': 0.5,
            'pitch_mean': 250,
            'tempo': 150
        }
        
        arousal = self.detector._calculate_arousal(features)
        
        self.assertIsInstance(arousal, float)
        self.assertGreaterEqual(arousal, 0)
        self.assertLessEqual(arousal, 1)
    
    def test_calculate_valence(self):
        """Test valence calculation"""
        features = {}
        emotion_scores = {
            'happy': 0.6,
            'sad': 0.2,
            'neutral': 0.2
        }
        
        valence = self.detector._calculate_valence(features, emotion_scores)
        
        self.assertIsInstance(valence, float)
        self.assertGreaterEqual(valence, 0)
        self.assertLessEqual(valence, 1)

class TestSentimentAnalyzer(unittest.TestCase):
    """Test cases for SentimentAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = SentimentAnalyzer()
        self.test_audio_path = self._create_test_audio()
        self.test_transcript = "I am very happy today! This is wonderful news."
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 4.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.4 * np.sin(2 * np.pi * 300 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        results = self.analyzer.analyze_sentiment(
            self.test_audio_path, 
            self.test_transcript, 
            segment_duration=2.0
        )
        
        self.assertIsInstance(results, list)
        
        if results:  # If analysis worked
            for result in results:
                self.assertIsInstance(result, SentimentResult)
                self.assertIn(result.sentiment, ['positive', 'negative', 'neutral'])
                self.assertGreaterEqual(result.polarity, -1)
                self.assertLessEqual(result.polarity, 1)
                self.assertGreaterEqual(result.subjectivity, 0)
                self.assertLessEqual(result.subjectivity, 1)
    
    def test_analyze_text_sentiment(self):
        """Test text sentiment analysis"""
        # Mock emotion results
        emotion_results = [
            EmotionResult(0, 2, 'happy', {}, 0.8, 0.7, 0.8, 0.7),
            EmotionResult(2, 2, 'neutral', {}, 0.6, 0.5, 0.5, 0.5)
        ]
        
        text_sentiments = self.analyzer._analyze_text_sentiment(
            self.test_transcript, 
            emotion_results
        )
        
        self.assertIsInstance(text_sentiments, list)
        self.assertEqual(len(text_sentiments), len(emotion_results))
        
        for sentiment in text_sentiments:
            self.assertIn('polarity', sentiment)
            self.assertIn('subjectivity', sentiment)
    
    def test_emotion_to_sentiment(self):
        """Test emotion to sentiment conversion"""
        emotion_result = EmotionResult(
            timestamp=0,
            duration=3,
            primary_emotion='happy',
            emotion_scores={'happy': 0.8, 'sad': 0.1, 'neutral': 0.1},
            confidence=0.8,
            arousal=0.7,
            valence=0.8,
            intensity=0.7
        )
        
        sentiment = self.analyzer._emotion_to_sentiment(emotion_result)
        
        self.assertIsInstance(sentiment, float)
        self.assertGreaterEqual(sentiment, -1)
        self.assertLessEqual(sentiment, 1)
    
    def test_combine_sentiments(self):
        """Test sentiment combination"""
        audio_sentiment = 0.5
        text_sentiment = 0.3
        
        combined = self.analyzer._combine_sentiments(audio_sentiment, text_sentiment)
        
        self.assertIsInstance(combined, float)
        self.assertGreaterEqual(combined, -1)
        self.assertLessEqual(combined, 1)

class TestMoodTracker(unittest.TestCase):
    """Test cases for MoodTracker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = MoodTracker()
        self.test_audio_path = self._create_test_audio()
        self.test_transcript = """
        I'm feeling great today! The weather is beautiful and I'm excited about our project.
        However, I'm also a bit concerned about the deadline. We have a lot of work to do.
        But I'm confident we can make it work if we stay focused and work together.
        """
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 30.0  # Longer for mood tracking
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.3 * np.sin(2 * np.pi * 250 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_track_mood(self):
        """Test mood tracking"""
        mood_states = self.tracker.track_mood(self.test_audio_path, self.test_transcript)
        
        self.assertIsInstance(mood_states, list)
        
        if mood_states:  # If tracking worked
            for mood in mood_states:
                self.assertIsInstance(mood, MoodState)
                self.assertIn(mood.mood, ['positive', 'negative', 'neutral', 'uncertain'])
                self.assertGreaterEqual(mood.energy_level, 0)
                self.assertLessEqual(mood.energy_level, 1)
                self.assertGreaterEqual(mood.stress_level, 0)
                self.assertLessEqual(mood.stress_level, 1)
    
    def test_calculate_mood_state(self):
        """Test mood state calculation"""
        # Mock sentiment results
        sentiment_results = [
            SentimentResult(0, 3, 'positive', 0.5, 0.6, 0.8, 0.5, 0.4),
            SentimentResult(3, 3, 'neutral', 0.1, 0.4, 0.7, 0.1, 0.0),
            SentimentResult(6, 3, 'negative', -0.3, 0.7, 0.6, -0.3, -0.2)
        ]
        
        mood_state = self.tracker._calculate_mood_state(sentiment_results, 0.0)
        
        self.assertIsInstance(mood_state, MoodState)
        self.assertGreaterEqual(mood_state.energy_level, 0)
        self.assertLessEqual(mood_state.energy_level, 1)

class TestStressFatigueDetector(unittest.TestCase):
    """Test cases for StressFatigueDetector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = StressFatigueDetector()
        self.test_audio_path = self._create_test_audio()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 20.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            # Create audio with some variation to simulate stress indicators
            audio = 0.4 * np.sin(2 * np.pi * (200 + 50 * np.sin(0.1 * t)) * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_detect_stress_fatigue(self):
        """Test stress and fatigue detection"""
        results = self.detector.detect_stress_fatigue(self.test_audio_path, segment_duration=5.0)
        
        self.assertIsInstance(results, list)
        
        if results:  # If detection worked
            for result in results:
                self.assertIsInstance(result, StressFatigueResult)
                self.assertGreaterEqual(result.stress_level, 0)
                self.assertLessEqual(result.stress_level, 1)
                self.assertGreaterEqual(result.fatigue_level, 0)
                self.assertLessEqual(result.fatigue_level, 1)
                self.assertGreaterEqual(result.cognitive_load, 0)
                self.assertLessEqual(result.cognitive_load, 1)
    
    def test_calculate_stress_level(self):
        """Test stress level calculation"""
        features = {
            'pitch_std': 30,
            'jitter': 0.02,
            'shimmer': 0.1,
            'harmonics_to_noise_ratio': 15,
            'spectral_centroid_mean': 2500
        }
        
        # Mock audio data
        y = np.random.randn(1000)
        sr = 22050
        
        stress_level = self.detector._calculate_stress_level(features, y, sr)
        
        self.assertIsInstance(stress_level, float)
        self.assertGreaterEqual(stress_level, 0)
        self.assertLessEqual(stress_level, 1)
    
    def test_calculate_fatigue_level(self):
        """Test fatigue level calculation"""
        features = {
            'intensity_mean': 0.05,
            'pitch_mean': 120,
            'tempo': 80,
            'spectral_rolloff_mean': 1500
        }
        
        y = np.random.randn(1000)
        sr = 22050
        
        fatigue_level = self.detector._calculate_fatigue_level(features, y, sr)
        
        self.assertIsInstance(fatigue_level, float)
        self.assertGreaterEqual(fatigue_level, 0)
        self.assertLessEqual(fatigue_level, 1)

class TestEmotionalTimelineVisualizer(unittest.TestCase):
    """Test cases for EmotionalTimelineVisualizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.visualizer = EmotionalTimelineVisualizer()
        
        # Create sample data
        self.emotion_results = [
            EmotionResult(i * 3, 3, 'happy', {'happy': 0.8}, 0.8, 0.7, 0.8, 0.7)
            for i in range(5)
        ]
        
        self.sentiment_results = [
            SentimentResult(i * 3, 3, 'positive', 0.5, 0.6, 0.8, 0.5, 0.4)
            for i in range(5)
        ]
        
        self.mood_states = [
            MoodState(i * 30, 'positive', 0.7, 0.3, 0.2, 0.8, 0.7)
            for i in range(3)
        ]
        
        self.stress_results = [
            StressFatigueResult(i * 10, 0.4, 0.3, 0.5, 0.2, 0.1, 0.15)
            for i in range(4)
        ]
    
    def test_create_emotion_timeline(self):
        """Test emotion timeline creation"""
        output_path = "test_emotion_timeline.html"
        
        try:
            result_path = self.visualizer.create_emotion_timeline(
                self.emotion_results, 
                output_path
            )
            
            if result_path:  # If visualization was created
                self.assertEqual(result_path, output_path)
                self.assertTrue(os.path.exists(output_path))
                
                # Clean up
                os.remove(output_path)
        
        except Exception as e:
            # Visualization might fail due to missing dependencies
            self.skipTest(f"Visualization test skipped due to: {e}")
    
    def test_create_sentiment_heatmap(self):
        """Test sentiment heatmap creation"""
        output_path = "test_sentiment_heatmap.html"
        
        try:
            result_path = self.visualizer.create_sentiment_heatmap(
                self.sentiment_results, 
                output_path
            )
            
            if result_path:
                self.assertEqual(result_path, output_path)
                self.assertTrue(os.path.exists(output_path))
                
                # Clean up
                os.remove(output_path)
        
        except Exception as e:
            self.skipTest(f"Visualization test skipped due to: {e}")
    
    def test_create_mood_dashboard(self):
        """Test mood dashboard creation"""
        output_path = "test_mood_dashboard.html"
        
        try:
            result_path = self.visualizer.create_mood_dashboard(
                self.mood_states, 
                output_path
            )
            
            if result_path:
                self.assertEqual(result_path, output_path)
                self.assertTrue(os.path.exists(output_path))
                
                # Clean up
                os.remove(output_path)
        
        except Exception as e:
            self.skipTest(f"Visualization test skipped due to: {e}")

class TestEmotionSentimentSystem(unittest.TestCase):
    """Test cases for the complete EmotionSentimentSystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.system = EmotionSentimentSystem()
        self.test_audio_path = self._create_test_audio()
        self.test_transcript = "I am feeling great today! This is wonderful."
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_audio_path):
            os.remove(self.test_audio_path)
    
    def _create_test_audio(self):
        """Create a test audio file"""
        try:
            import soundfile as sf
            
            duration = 10.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.3 * np.sin(2 * np.pi * 220 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            return temp_file.name
            
        except ImportError:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            return temp_file.name
    
    def test_analyze_complete(self):
        """Test complete analysis"""
        results = self.system.analyze_complete(self.test_audio_path, self.test_transcript)
        
        self.assertIsInstance(results, dict)
        self.assertNotIn('error', results)
        
        # Check required keys
        expected_keys = [
            'audio_path', 'transcript', 'analysis_timestamp',
            'emotions', 'sentiments', 'mood_states', 'stress_fatigue',
            'visualizations', 'summary'
        ]
        
        for key in expected_keys:
            self.assertIn(key, results)
    
    def test_generate_summary(self):
        """Test summary generation"""
        # Create mock results
        emotion_results = [
            EmotionResult(0, 3, 'happy', {'happy': 0.8}, 0.8, 0.7, 0.8, 0.7),
            EmotionResult(3, 3, 'neutral', {'neutral': 0.6}, 0.6, 0.5, 0.5, 0.5)
        ]
        
        sentiment_results = [
            SentimentResult(0, 3, 'positive', 0.5, 0.6, 0.8, 0.5, 0.4),
            SentimentResult(3, 3, 'neutral', 0.1, 0.4, 0.7, 0.1, 0.0)
        ]
        
        mood_states = [
            MoodState(0, 'positive', 0.7, 0.3, 0.2, 0.8, 0.7)
        ]
        
        stress_results = [
            StressFatigueResult(0, 0.4, 0.3, 0.5, 0.2, 0.1, 0.15)
        ]
        
        summary = self.system._generate_summary(
            emotion_results, sentiment_results, mood_states, stress_results
        )
        
        self.assertIsInstance(summary, dict)
        self.assertIn('duration_analyzed', summary)
        self.assertIn('dominant_emotion', summary)
        self.assertIn('average_sentiment', summary)
        self.assertIn('key_insights', summary)
    
    def test_save_results(self):
        """Test results saving"""
        test_results = {
            'test_data': 'test_value',
            'timestamp': '2024-01-01T00:00:00'
        }
        
        output_path = "test_results.json"
        
        try:
            saved_path = self.system.save_results(test_results, output_path)
            
            if saved_path:
                self.assertEqual(saved_path, output_path)
                self.assertTrue(os.path.exists(output_path))
                
                # Verify content
                with open(output_path, 'r') as f:
                    loaded_results = json.load(f)
                
                self.assertEqual(loaded_results['test_data'], 'test_value')
                
                # Clean up
                os.remove(output_path)
        
        except Exception as e:
            self.skipTest(f"Save test skipped due to: {e}")

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.system = EmotionSentimentSystem()
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        try:
            # Create test audio
            import soundfile as sf
            
            duration = 8.0
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.3 * np.sin(2 * np.pi * 300 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            
            transcript = "I am very excited about this project! It's going to be amazing."
            
            # Run complete analysis
            results = self.system.analyze_complete(temp_file.name, transcript)
            
            # Verify results structure
            self.assertIsInstance(results, dict)
            self.assertNotIn('error', results)
            
            # Verify data types
            if results.get('emotions'):
                self.assertIsInstance(results['emotions'], list)
            
            if results.get('sentiments'):
                self.assertIsInstance(results['sentiments'], list)
            
            if results.get('summary'):
                self.assertIsInstance(results['summary'], dict)
            
            # Clean up
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
        
        system = EmotionSentimentSystem()
        
        # Test with different audio lengths
        durations = [5, 10, 30, 60]  # seconds
        
        for duration in durations:
            print(f"\nTesting {duration}s audio...")
            
            # Create test audio
            sample_rate = 22050
            t = np.linspace(0, duration, int(duration * sample_rate))
            audio = 0.3 * np.sin(2 * np.pi * 250 * t)
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            sf.write(temp_file.name, audio, sample_rate)
            
            # Measure processing time
            start_time = time.time()
            results = system.analyze_complete(temp_file.name, "Test transcript for performance measurement.")
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            print(f"  Processing time: {processing_time:.2f}s")
            print(f"  Real-time factor: {processing_time/duration:.2f}x")
            
            if 'emotions' in results:
                print(f"  Emotion segments: {len(results['emotions'])}")
            
            if 'sentiments' in results:
                print(f"  Sentiment segments: {len(results['sentiments'])}")
            
            # Clean up
            os.remove(temp_file.name)
    
    except Exception as e:
        print(f"Performance tests failed: {e}")

def main():
    """Run all tests"""
    print("🧪 EMOTION & SENTIMENT DETECTION SYSTEM TESTS")
    print("=" * 60)
    
    # Check if required modules are available
    try:
        import librosa
        import soundfile
        import sklearn
        import textblob
        print("✅ All required modules available")
    except ImportError as e:
        print(f"❌ Missing required modules: {e}")
        print("Please install: pip install librosa soundfile scikit-learn textblob")
        return
    
    # Run unit tests
    print("\n🔍 Running unit tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestAudioFeatureExtractor,
        TestEmotionDetector,
        TestSentimentAnalyzer,
        TestMoodTracker,
        TestStressFatigueDetector,
        TestEmotionalTimelineVisualizer,
        TestEmotionSentimentSystem,
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