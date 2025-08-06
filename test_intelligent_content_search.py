#!/usr/bin/env python3
"""
Test suite for Intelligent Content Search System
Tests visual scene analysis, audio pattern recognition, and semantic search
"""

import unittest
import tempfile
import os
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from intelligent_content_search import (
    IntelligentContentSearchSystem, VisualSceneAnalyzer, AudioPatternRecognizer,
    SemanticVideoSearchEngine, VisualScene, AudioPattern, SearchResult
)

class TestVisualSceneAnalyzer(unittest.TestCase):
    """Test cases for VisualSceneAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = VisualSceneAnalyzer()
    
    def test_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        # Model loading might fail in test environment
        # But analyzer should still initialize
    
    def test_analyze_frame(self):
        """Test frame analysis"""
        # Create a mock frame (100x100 RGB)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        scene = self.analyzer.analyze_frame(frame, frame_number=1, timestamp=1.0)
        
        self.assertIsInstance(scene, VisualScene)
        self.assertEqual(scene.frame_number, 1)
        self.assertEqual(scene.timestamp, 1.0)
        self.assertIsInstance(scene.description, str)
        self.assertIsInstance(scene.objects, list)
        self.assertIsInstance(scene.confidence, float)
        self.assertGreaterEqual(scene.confidence, 0.0)
        self.assertLessEqual(scene.confidence, 1.0)
    
    def test_generate_description_fallback(self):
        """Test description generation fallback"""
        # Without model, should return fallback
        self.analyzer.processor = None
        self.analyzer.model = None
        
        from PIL import Image
        image = Image.new('RGB', (100, 100))
        
        description = self.analyzer.generate_description(image)
        self.assertEqual(description, "Scene analysis unavailable")
    
    def test_detect_objects(self):
        """Test object detection"""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        objects = self.analyzer.detect_objects(frame)
        
        self.assertIsInstance(objects, list)
        # Mock implementation returns 1-3 objects
        self.assertGreaterEqual(len(objects), 1)
        self.assertLessEqual(len(objects), 3)
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # Test with description and objects
        confidence1 = self.analyzer.calculate_confidence("A person walking", ["person"])
        self.assertGreater(confidence1, 0.7)
        
        # Test without description
        confidence2 = self.analyzer.calculate_confidence("Scene analysis unavailable", [])
        self.assertEqual(confidence2, 0.7)

class TestAudioPatternRecognizer(unittest.TestCase):
    """Test cases for AudioPatternRecognizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.recognizer = AudioPatternRecognizer()
    
    def test_initialization(self):
        """Test recognizer initialization"""
        self.assertIsNotNone(self.recognizer)
        self.assertEqual(self.recognizer.sample_rate, 22050)
        self.assertEqual(self.recognizer.hop_length, 512)
        self.assertIn('music', self.recognizer.patterns)
        self.assertIn('speech', self.recognizer.patterns)
    
    def test_analyze_audio_segment(self):
        """Test audio segment analysis"""
        # Create mock audio data (1 second of sine wave)
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        patterns = self.recognizer.analyze_audio_segment(
            audio_data, sr, start_time=0.0, end_time=1.0
        )
        
        self.assertIsInstance(patterns, list)
        self.assertEqual(len(patterns), 1)
        
        pattern = patterns[0]
        self.assertIsInstance(pattern, AudioPattern)
        self.assertEqual(pattern.start_time, 0.0)
        self.assertEqual(pattern.end_time, 1.0)
        self.assertIn(pattern.pattern_type, ['music', 'speech', 'silence', 'noise', 'unknown'])
        self.assertIsInstance(pattern.confidence, float)
    
    def test_extract_audio_features(self):
        """Test audio feature extraction"""
        # Create simple audio
        sr = 22050
        audio_data = np.random.randn(sr)  # 1 second of noise
        
        features = self.recognizer.extract_audio_features(audio_data, sr)
        
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape, (17,))  # 13 MFCC + 4 other features
    
    def test_classify_audio_pattern(self):
        """Test audio pattern classification"""
        # Test silence classification
        silence_features = np.zeros(17)
        silence_features[-1] = 0.05  # Low energy
        pattern_type, confidence = self.recognizer.classify_audio_pattern(silence_features)
        self.assertEqual(pattern_type, 'silence')
        self.assertGreater(confidence, 0.8)
        
        # Test speech classification
        speech_features = np.random.randn(17)
        speech_features[:13] = np.random.randn(13) * 2  # High MFCC variance
        speech_features[-1] = 0.5  # Medium energy
        pattern_type, confidence = self.recognizer.classify_audio_pattern(speech_features)
        self.assertEqual(pattern_type, 'speech')

class TestSemanticVideoSearchEngine(unittest.TestCase):
    """Test cases for SemanticVideoSearchEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.search_engine = SemanticVideoSearchEngine()
    
    def test_initialization(self):
        """Test search engine initialization"""
        self.assertIsNotNone(self.search_engine)
        self.assertIsNotNone(self.search_engine.embedding_model)
        self.assertEqual(self.search_engine.embedding_dim, 384)
    
    def test_create_embedding(self):
        """Test text embedding creation"""
        text = "A person walking in the park"
        embedding = self.search_engine.create_embedding(text)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))
    
    def test_create_visual_embedding(self):
        """Test visual scene embedding"""
        scene = VisualScene(
            scene_id="test_001",
            file_path="test.mp4",
            timestamp=1.0,
            frame_number=30,
            description="A car on the street",
            objects=["car", "street"],
            confidence=0.9
        )
        
        embedding = self.search_engine.create_visual_embedding(scene)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))
    
    def test_search_similar_scenes(self):
        """Test scene similarity search"""
        # Create mock scene embeddings
        scene_embeddings = []
        for i in range(5):
            scene_id = f"scene_{i}"
            embedding = np.random.randn(384)
            scene_embeddings.append((scene_id, embedding))
        
        # Search
        query = "person walking"
        results = self.search_engine.search_similar_scenes(query, scene_embeddings, top_k=3)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        
        for scene_id, similarity in results:
            self.assertIsInstance(scene_id, str)
            self.assertIsInstance(similarity, float)
            self.assertGreaterEqual(similarity, -1.0)
            self.assertLessEqual(similarity, 1.0)

class TestIntelligentContentSearchSystem(unittest.TestCase):
    """Test cases for the complete search system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.search_system = IntelligentContentSearchSystem(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.search_system)
        self.assertIsInstance(self.search_system.visual_analyzer, VisualSceneAnalyzer)
        self.assertIsInstance(self.search_system.audio_recognizer, AudioPatternRecognizer)
        self.assertIsInstance(self.search_system.search_engine, SemanticVideoSearchEngine)
        
        # Check database exists
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    @patch('cv2.VideoCapture')
    def test_process_video_file_mock(self, mock_capture):
        """Test video processing with mocked video"""
        # Mock video capture
        mock_cap = MagicMock()
        mock_cap.isOpened.side_effect = [True, True, False]  # Process 2 frames
        mock_cap.read.side_effect = [
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (True, np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)),
            (False, None)
        ]
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 60
        }.get(prop, 0)
        
        mock_capture.return_value = mock_cap
        
        # Process video
        with patch.object(self.search_system, '_extract_audio', return_value=(None, None)):
            results = self.search_system.process_video_file("test_video.mp4", sample_interval=1.0)
        
        self.assertIn('visual_scenes', results)
        self.assertIn('audio_patterns', results)
        self.assertIn('metadata', results)
        
        # Should have processed 2 scenes (at 0s and 1s)
        self.assertEqual(len(results['visual_scenes']), 2)
        self.assertEqual(results['metadata']['scenes_analyzed'], 2)
    
    def test_save_and_retrieve_visual_scene(self):
        """Test saving and retrieving visual scenes"""
        # Create a scene
        scene = VisualScene(
            scene_id="test_scene_001",
            file_path="test.mp4",
            timestamp=5.0,
            frame_number=150,
            description="Test scene description",
            objects=["object1", "object2"],
            confidence=0.85,
            embedding=np.random.randn(384).astype(np.float32)
        )
        
        # Save scene
        self.search_system._save_visual_scene(scene)
        
        # Search for it
        results = self.search_system.search_visual_scenes("test scene", top_k=5)
        
        # Should find at least this scene
        self.assertGreater(len(results), 0)
        
        # Check first result
        result = results[0]
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.content_type, 'visual')
    
    def test_save_and_retrieve_audio_pattern(self):
        """Test saving and retrieving audio patterns"""
        # Create a pattern
        pattern = AudioPattern(
            pattern_id="test_pattern_001",
            file_path="test.mp4",
            start_time=10.0,
            end_time=15.0,
            pattern_type="music",
            confidence=0.9,
            features=np.random.randn(17).astype(np.float32)
        )
        
        # Save pattern
        self.search_system._save_audio_pattern(pattern)
        
        # Search for it
        results = self.search_system.search_audio_patterns(pattern_type="music")
        
        # Should find this pattern
        self.assertEqual(len(results), 1)
        
        result = results[0]
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.content_type, 'audio')
        self.assertEqual(result.content_id, "test_pattern_001")
    
    def test_get_video_timeline(self):
        """Test timeline generation"""
        # Add some test data
        test_file = "timeline_test.mp4"
        
        # Add visual scenes
        for i in range(3):
            scene = VisualScene(
                scene_id=f"timeline_scene_{i}",
                file_path=test_file,
                timestamp=float(i * 10),
                frame_number=i * 300,
                description=f"Scene {i}",
                objects=[f"object_{i}"],
                confidence=0.8
            )
            self.search_system._save_visual_scene(scene)
        
        # Add audio patterns
        for i in range(2):
            pattern = AudioPattern(
                pattern_id=f"timeline_pattern_{i}",
                file_path=test_file,
                start_time=float(i * 15),
                end_time=float(i * 15 + 5),
                pattern_type="music",
                confidence=0.7
            )
            self.search_system._save_audio_pattern(pattern)
        
        # Get timeline
        timeline = self.search_system.get_video_timeline(test_file)
        
        self.assertEqual(timeline['file_path'], test_file)
        self.assertEqual(len(timeline['visual_events']), 3)
        self.assertEqual(len(timeline['audio_events']), 2)
        self.assertEqual(len(timeline['combined_timeline']), 5)
        
        # Check timeline is sorted
        timestamps = [event['timestamp'] for event in timeline['combined_timeline']]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_get_statistics(self):
        """Test statistics generation"""
        # Add some test data
        for i in range(5):
            scene = VisualScene(
                scene_id=f"stat_scene_{i}",
                file_path=f"test_{i % 2}.mp4",
                timestamp=float(i),
                frame_number=i * 30,
                description=f"Scene {i}",
                objects=[],
                confidence=0.8
            )
            self.search_system._save_visual_scene(scene)
        
        for i, pattern_type in enumerate(['music', 'speech', 'music']):
            pattern = AudioPattern(
                pattern_id=f"stat_pattern_{i}",
                file_path="test.mp4",
                start_time=float(i * 10),
                end_time=float(i * 10 + 5),
                pattern_type=pattern_type,
                confidence=0.7
            )
            self.search_system._save_audio_pattern(pattern)
        
        # Get statistics
        stats = self.search_system.get_statistics()
        
        self.assertEqual(stats['total_scenes'], 5)
        self.assertEqual(stats['total_patterns'], 3)
        self.assertEqual(stats['files_processed'], 2)  # test_0.mp4 and test_1.mp4
        self.assertEqual(stats['pattern_distribution']['music'], 2)
        self.assertEqual(stats['pattern_distribution']['speech'], 1)

def run_tests():
    """Run all tests"""
    print("🧪 Running Intelligent Content Search Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestVisualSceneAnalyzer,
        TestAudioPatternRecognizer,
        TestSemanticVideoSearchEngine,
        TestIntelligentContentSearchSystem
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            error_lines = traceback.split('\n')
            error_msg = error_lines[-2] if len(error_lines) >= 2 else str(traceback)
            print(f"   - {test}: {error_msg}")
    
    if not result.failures and not result.errors:
        print("✅ All tests passed successfully!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)