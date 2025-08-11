#!/usr/bin/env python3
"""
Test Suite for Advanced AI-Powered Content Intelligence Platform
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from advanced_content_intelligence import (
    AdvancedContentIntelligencePlatform, TextAnalysisEngine, AudioAnalysisEngine,
    VideoAnalysisEngine, ImageAnalysisEngine, CrossModalAnalysisEngine,
    ContentAnalysisResult, AuthenticityAnalysis, DeepfakeDetection, CrossModalInsight
)

class TestTextAnalysisEngine(unittest.TestCase):
    """Test text analysis functionality"""
    
    def setUp(self):
        self.engine = TextAnalysisEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine.suspicious_patterns, list)
        self.assertGreater(len(self.engine.suspicious_patterns), 0)
        self.assertIsInstance(self.engine.quality_indicators, dict)
    
    def test_authenticity_analysis_suspicious_content(self):
        """Test authenticity analysis with suspicious content"""
        suspicious_text = "URGENT! Click here now! You have won $1,000,000! Limited time offer!"
        
        result = self.engine.analyze_authenticity(suspicious_text)
        
        self.assertIsInstance(result, AuthenticityAnalysis)
        self.assertLess(result.confidence_score, 0.8)  # Should be flagged as suspicious
        self.assertGreater(len(result.manipulation_indicators), 0)
        self.assertIn("pattern_analysis", result.verification_methods)
    
    def test_authenticity_analysis_normal_content(self):
        """Test authenticity analysis with normal content"""
        normal_text = "This is a regular business email discussing our quarterly meeting schedule."
        
        result = self.engine.analyze_authenticity(normal_text)
        
        self.assertIsInstance(result, AuthenticityAnalysis)
        self.assertGreater(result.confidence_score, 0.7)  # Should be considered authentic
        self.assertTrue(result.is_authentic)
    
    def test_semantic_feature_extraction(self):
        """Test semantic feature extraction"""
        text = "Our technology company is developing innovative software solutions for business clients."
        
        features = self.engine.extract_semantic_features(text)
        
        self.assertIsInstance(features, dict)
        self.assertIn("word_count", features)
        self.assertIn("unique_words", features)
        self.assertIn("topic_scores", features)
        self.assertIn("dominant_topic", features)
        
        # Should detect business/technology topics
        self.assertIn(features["dominant_topic"], ["business", "technology"])
    
    def test_repetitive_content_detection(self):
        """Test detection of repetitive content"""
        repetitive_text = "buy now buy now buy now sale sale sale urgent urgent urgent"
        
        result = self.engine.analyze_authenticity(repetitive_text)
        
        # Should detect high repetition
        repetition_indicators = [
            indicator for indicator in result.manipulation_indicators
            if indicator["type"] == "high_repetition"
        ]
        self.assertGreater(len(repetition_indicators), 0)

class TestAudioAnalysisEngine(unittest.TestCase):
    """Test audio analysis functionality"""
    
    def setUp(self):
        self.engine = AudioAnalysisEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertEqual(self.engine.sample_rate, 16000)
        self.assertEqual(self.engine.frame_length, 1024)
        self.assertIsInstance(self.engine.quality_thresholds, dict)
    
    def test_deepfake_detection(self):
        """Test deepfake detection in audio"""
        audio_data = b"mock_audio_data_for_testing" * 100
        
        result = self.engine.detect_deepfake_audio(audio_data)
        
        self.assertIsInstance(result, DeepfakeDetection)
        self.assertIsInstance(result.is_deepfake, bool)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIsInstance(result.detection_methods, list)
        self.assertGreater(len(result.detection_methods), 0)
    
    def test_audio_quality_analysis(self):
        """Test audio quality analysis"""
        audio_data = b"sample_audio_data" * 200
        
        quality_metrics = self.engine.analyze_audio_quality(audio_data)
        
        self.assertIsInstance(quality_metrics, dict)
        self.assertIn("duration", quality_metrics)
        self.assertIn("noise_level", quality_metrics)
        self.assertIn("clarity_score", quality_metrics)
        self.assertIn("overall_quality", quality_metrics)
        
        # Quality scores should be between 0 and 1
        self.assertGreaterEqual(quality_metrics["overall_quality"], 0.0)
        self.assertLessEqual(quality_metrics["overall_quality"], 1.0)
    
    def test_quality_thresholds(self):
        """Test quality threshold enforcement"""
        # Test with very short audio (should affect quality)
        short_audio = b"short"
        quality_metrics = self.engine.analyze_audio_quality(short_audio)
        
        # Should have low duration
        self.assertLess(quality_metrics["duration"], self.engine.quality_thresholds["min_duration"])

class TestVideoAnalysisEngine(unittest.TestCase):
    """Test video analysis functionality"""
    
    def setUp(self):
        self.engine = VideoAnalysisEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertEqual(self.engine.frame_rate, 30)
        self.assertIsInstance(self.engine.resolution_threshold, tuple)
    
    def test_deepfake_detection(self):
        """Test deepfake detection in video"""
        video_path = "/path/to/test_video.mp4"
        
        result = self.engine.detect_deepfake_video(video_path)
        
        self.assertIsInstance(result, DeepfakeDetection)
        self.assertIsInstance(result.is_deepfake, bool)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIn("facial_analysis", result.detection_methods)
        self.assertIn("temporal_consistency", result.detection_methods)
    
    def test_video_quality_analysis(self):
        """Test video quality analysis"""
        video_path = "/path/to/sample_video.mp4"
        
        quality_metrics = self.engine.analyze_video_quality(video_path)
        
        self.assertIsInstance(quality_metrics, dict)
        self.assertIn("resolution", quality_metrics)
        self.assertIn("frame_rate", quality_metrics)
        self.assertIn("overall_quality", quality_metrics)
        
        # Quality score should be valid
        self.assertGreaterEqual(quality_metrics["overall_quality"], 0.0)
        self.assertLessEqual(quality_metrics["overall_quality"], 1.0)
    
    def test_suspicious_regions_detection(self):
        """Test detection of suspicious regions in video"""
        # Use a path that should trigger high deepfake probability
        suspicious_video_path = "/path/to/suspicious_video_with_high_hash.mp4"
        
        result = self.engine.detect_deepfake_video(suspicious_video_path)
        
        if result.confidence_score > 0.8:
            self.assertGreater(len(result.suspicious_regions), 0)
            self.assertGreater(len(result.technical_artifacts), 0)

class TestImageAnalysisEngine(unittest.TestCase):
    """Test image analysis functionality"""
    
    def setUp(self):
        self.engine = ImageAnalysisEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine.supported_formats, list)
        self.assertIn('.jpg', self.engine.supported_formats)
        self.assertIn('.png', self.engine.supported_formats)
    
    def test_manipulation_detection(self):
        """Test image manipulation detection"""
        image_path = "/path/to/test_image.jpg"
        
        result = self.engine.detect_manipulation(image_path)
        
        self.assertIsInstance(result, AuthenticityAnalysis)
        self.assertIsInstance(result.is_authentic, bool)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        self.assertIn("metadata_analysis", result.verification_methods)
    
    def test_visual_feature_extraction(self):
        """Test visual feature extraction"""
        image_path = "/path/to/sample_image.png"
        
        features = self.engine.extract_visual_features(image_path)
        
        self.assertIsInstance(features, dict)
        self.assertIn("dominant_colors", features)
        self.assertIn("brightness", features)
        self.assertIn("contrast", features)
        self.assertIn("scene_type", features)
        
        # Color values should be valid hex colors
        for color in features["dominant_colors"]:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)  # #RRGGBB format
    
    def test_manipulation_indicators(self):
        """Test manipulation indicator detection"""
        # Use a path that should trigger manipulation detection
        suspicious_image_path = "/path/to/manipulated_image_high_hash.jpg"
        
        result = self.engine.detect_manipulation(suspicious_image_path)
        
        if result.confidence_score < 0.5:
            self.assertGreater(len(result.manipulation_indicators), 0)

class TestCrossModalAnalysisEngine(unittest.TestCase):
    """Test cross-modal analysis functionality"""
    
    def setUp(self):
        self.engine = CrossModalAnalysisEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine.text_engine, TextAnalysisEngine)
        self.assertIsInstance(self.engine.audio_engine, AudioAnalysisEngine)
        self.assertIsInstance(self.engine.video_engine, VideoAnalysisEngine)
        self.assertIsInstance(self.engine.image_engine, ImageAnalysisEngine)
    
    def test_multimodal_content_analysis(self):
        """Test multimodal content analysis"""
        content_data = {
            "text": "Welcome to our product demonstration",
            "audio": b"demo_audio_data" * 50,
            "video": "/path/to/demo_video.mp4"
        }
        
        insights = self.engine.analyze_multimodal_content(content_data)
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        for insight in insights:
            self.assertIsInstance(insight, CrossModalInsight)
            self.assertIn(insight.insight_type, [
                "text_audio_consistency", "audio_video_sync", 
                "text_image_relevance", "multimodal_authenticity"
            ])
    
    def test_text_audio_consistency(self):
        """Test text-audio consistency analysis"""
        positive_text = "This is great and wonderful news!"
        audio_data = b"positive_audio_data" * 30
        
        insight = self.engine._analyze_text_audio_consistency(positive_text, audio_data)
        
        self.assertIsInstance(insight, CrossModalInsight)
        self.assertEqual(insight.insight_type, "text_audio_consistency")
        self.assertIn("text_sentiment", insight.evidence)
        self.assertIn("audio_emotion", insight.evidence)
    
    def test_sentiment_emotion_detection(self):
        """Test sentiment and emotion detection"""
        # Test positive text
        positive_text = "I love this amazing product!"
        sentiment = self.engine._get_text_sentiment(positive_text)
        self.assertEqual(sentiment, "positive")
        
        # Test negative text
        negative_text = "This is terrible and awful!"
        sentiment = self.engine._get_text_sentiment(negative_text)
        self.assertEqual(sentiment, "negative")
        
        # Test neutral text
        neutral_text = "This is a regular statement."
        sentiment = self.engine._get_text_sentiment(neutral_text)
        self.assertEqual(sentiment, "neutral")
    
    def test_audio_emotion_detection(self):
        """Test audio emotion detection"""
        audio_data = b"test_audio_for_emotion" * 20
        emotion = self.engine._get_audio_emotion(audio_data)
        
        self.assertIn(emotion, ["positive", "negative", "neutral"])

class TestAdvancedContentIntelligencePlatform(unittest.TestCase):
    """Test the main content intelligence platform"""
    
    def setUp(self):
        self.platform = AdvancedContentIntelligencePlatform()
    
    def test_platform_initialization(self):
        """Test platform initializes correctly"""
        self.assertIsInstance(self.platform.cross_modal_engine, CrossModalAnalysisEngine)
        self.assertIsInstance(self.platform.content_cache, dict)
        self.assertIsInstance(self.platform.analysis_history, list)
    
    def test_content_type_determination(self):
        """Test automatic content type determination"""
        # Single modality
        text_only = {"text": "Sample text"}
        self.assertEqual(self.platform._determine_content_type(text_only), "text")
        
        audio_only = {"audio": b"audio_data"}
        self.assertEqual(self.platform._determine_content_type(audio_only), "audio")
        
        # Multiple modalities
        multimodal = {"text": "Sample", "audio": b"audio", "video": "/path/video.mp4"}
        self.assertEqual(self.platform._determine_content_type(multimodal), "multimodal")
        
        # Empty content
        empty = {}
        self.assertEqual(self.platform._determine_content_type(empty), "unknown")
    
    def test_text_content_analysis(self):
        """Test text content analysis"""
        content_data = {"text": "This is a sample business document about technology solutions."}
        
        result = self.platform.analyze_content(content_data, "text")
        
        self.assertIsInstance(result, ContentAnalysisResult)
        self.assertEqual(result.content_type, "text")
        self.assertGreaterEqual(result.authenticity_score, 0.0)
        self.assertLessEqual(result.authenticity_score, 1.0)
        self.assertEqual(result.deepfake_probability, 0.0)  # Not applicable for text
        self.assertIsInstance(result.semantic_features, dict)
    
    def test_audio_content_analysis(self):
        """Test audio content analysis"""
        content_data = {"audio": b"sample_audio_data_for_analysis" * 100}
        
        result = self.platform.analyze_content(content_data, "audio")
        
        self.assertIsInstance(result, ContentAnalysisResult)
        self.assertEqual(result.content_type, "audio")
        self.assertGreaterEqual(result.deepfake_probability, 0.0)
        self.assertLessEqual(result.deepfake_probability, 1.0)
        self.assertIsInstance(result.risk_assessment, dict)
    
    def test_video_content_analysis(self):
        """Test video content analysis"""
        content_data = {"video": "/path/to/test_video.mp4"}
        
        result = self.platform.analyze_content(content_data, "video")
        
        self.assertIsInstance(result, ContentAnalysisResult)
        self.assertEqual(result.content_type, "video")
        self.assertGreaterEqual(result.deepfake_probability, 0.0)
        self.assertLessEqual(result.deepfake_probability, 1.0)
        self.assertIn("deepfake_risk", result.risk_assessment)
    
    def test_image_content_analysis(self):
        """Test image content analysis"""
        content_data = {"image": "/path/to/test_image.jpg"}
        
        result = self.platform.analyze_content(content_data, "image")
        
        self.assertIsInstance(result, ContentAnalysisResult)
        self.assertEqual(result.content_type, "image")
        self.assertGreaterEqual(result.authenticity_score, 0.0)
        self.assertLessEqual(result.authenticity_score, 1.0)
        self.assertIn("manipulation_risk", result.risk_assessment)
    
    def test_multimodal_content_analysis(self):
        """Test multimodal content analysis"""
        content_data = {
            "text": "Product demonstration video",
            "audio": b"narration_audio_data" * 50,
            "video": "/path/to/product_demo.mp4"
        }
        
        result = self.platform.analyze_content(content_data, "multimodal")
        
        self.assertIsInstance(result, ContentAnalysisResult)
        self.assertEqual(result.content_type, "multimodal")
        self.assertIn("modalities", result.semantic_features)
        self.assertIn("cross_modal_consistency", result.semantic_features)
        self.assertGreater(len(result.cross_modal_insights), 0)
    
    def test_content_caching(self):
        """Test content caching functionality"""
        content_data = {"text": "Sample text for caching test"}
        
        # First analysis
        result1 = self.platform.analyze_content(content_data, "text")
        content_id = result1.content_id
        
        # Second analysis of same content (should use cache)
        result2 = self.platform.analyze_content(content_data, "text")
        
        self.assertEqual(result1.content_id, result2.content_id)
        self.assertIn(content_id, self.platform.content_cache)
    
    def test_analysis_summary(self):
        """Test analysis summary generation"""
        content_data = {"text": "Sample text for summary test"}
        
        result = self.platform.analyze_content(content_data, "text")
        summary = self.platform.get_analysis_summary(result.content_id)
        
        self.assertIsInstance(summary, dict)
        self.assertIn("content_id", summary)
        self.assertIn("authenticity_score", summary)
        self.assertIn("risk_level", summary)
        self.assertIn(summary["risk_level"], ["low", "medium", "high"])
    
    def test_analysis_export(self):
        """Test analysis export functionality"""
        content_data = {"text": "Sample text for export test"}
        
        result = self.platform.analyze_content(content_data, "text")
        exported = self.platform.export_analysis(result.content_id, "json")
        
        self.assertIsInstance(exported, str)
        
        # Verify it's valid JSON
        parsed = json.loads(exported)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["content_id"], result.content_id)
    
    def test_auto_content_type_detection(self):
        """Test automatic content type detection"""
        # Test with multimodal content using auto detection
        content_data = {
            "text": "Sample text",
            "audio": b"audio_data" * 20
        }
        
        result = self.platform.analyze_content(content_data, "auto")
        self.assertEqual(result.content_type, "multimodal")
        
        # Test with single modality
        text_only = {"text": "Just text"}
        result = self.platform.analyze_content(text_only, "auto")
        self.assertEqual(result.content_type, "text")

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        self.platform = AdvancedContentIntelligencePlatform()
    
    def test_suspicious_content_detection(self):
        """Test detection of suspicious content"""
        suspicious_content = {
            "text": "URGENT! Click here now! You have won $1,000,000! Act fast!",
            "audio": b"suspicious_audio_with_artificial_patterns" * 80
        }
        
        result = self.platform.analyze_content(suspicious_content, "multimodal")
        
        # Should detect low authenticity
        self.assertLess(result.authenticity_score, 0.7)
        self.assertIn("overall_authenticity_risk", result.risk_assessment)
        self.assertGreater(result.risk_assessment["overall_authenticity_risk"], 0.3)
    
    def test_high_quality_content_analysis(self):
        """Test analysis of high-quality, authentic content"""
        quality_content = {
            "text": "Our quarterly business review shows steady growth in customer satisfaction and revenue.",
            "audio": b"professional_narration_audio_data" * 60
        }
        
        result = self.platform.analyze_content(quality_content, "multimodal")
        
        # Should show high authenticity and quality
        self.assertGreater(result.authenticity_score, 0.6)
        self.assertGreater(result.content_quality_score, 0.4)
    
    def test_batch_content_analysis(self):
        """Test analyzing multiple pieces of content"""
        content_items = [
            {"text": "First document about business strategy"},
            {"text": "Second document about technology trends"},
            {"audio": b"audio_content_sample" * 40},
            {"image": "/path/to/sample_image.jpg"}
        ]
        
        results = []
        for content in content_items:
            result = self.platform.analyze_content(content, "auto")
            results.append(result)
        
        self.assertEqual(len(results), 4)
        
        # Check that different content types were detected
        content_types = [result.content_type for result in results]
        self.assertIn("text", content_types)
        self.assertIn("audio", content_types)
        self.assertIn("image", content_types)
    
    def test_analysis_history_tracking(self):
        """Test analysis history tracking"""
        initial_history_length = len(self.platform.analysis_history)
        
        # Analyze several pieces of content
        for i in range(3):
            content = {"text": f"Sample document {i}"}
            self.platform.analyze_content(content, "text")
        
        # History should have grown
        self.assertEqual(
            len(self.platform.analysis_history), 
            initial_history_length + 3
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)