#!/usr/bin/env python3
"""
Test Suite for Smart B-roll Suggestion System
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from smart_broll_suggestions import (
    SmartBRollSuggestionEngine, ContentAnalyzer, UnsplashProvider, PexelsProvider,
    MediaAsset, ContentContext, BRollSuggestion
)

class TestContentAnalyzer(unittest.TestCase):
    """Test content analysis functionality"""
    
    def setUp(self):
        self.analyzer = ContentAnalyzer()
    
    def test_keyword_extraction(self):
        """Test keyword extraction from text"""
        text = "This is a test about business technology and innovation in the modern world"
        keywords = self.analyzer._extract_keywords(text)
        
        self.assertIsInstance(keywords, list)
        self.assertIn("business", keywords)
        self.assertIn("technology", keywords)
        self.assertIn("innovation", keywords)
    
    def test_scene_detection(self):
        """Test scene type detection"""
        text = "We're in a corporate office meeting with the business team discussing technology"
        keywords = self.analyzer._extract_keywords(text)
        scenes = self.analyzer._detect_scenes(text, keywords)
        
        self.assertIsInstance(scenes, list)
        self.assertIn("business", scenes)
        self.assertIn("technology", scenes)
    
    def test_style_determination(self):
        """Test video style determination"""
        educational_text = "Let me explain how to learn and understand this concept"
        style = self.analyzer._determine_style(educational_text, [])
        self.assertEqual(style, "educational")
        
        commercial_text = "Buy our amazing product with this special offer"
        style = self.analyzer._determine_style(commercial_text, [])
        self.assertEqual(style, "commercial")
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis"""
        positive_text = "This is great and amazing and wonderful"
        sentiment = self.analyzer._analyze_sentiment(positive_text)
        self.assertEqual(sentiment, "positive")
        
        negative_text = "This is terrible and awful and bad"
        sentiment = self.analyzer._analyze_sentiment(negative_text)
        self.assertEqual(sentiment, "negative")
        
        neutral_text = "This is a normal sentence about things"
        sentiment = self.analyzer._analyze_sentiment(neutral_text)
        self.assertEqual(sentiment, "neutral")
    
    def test_content_context_creation(self):
        """Test complete content context creation"""
        transcript = "We're discussing business technology in our corporate office"
        context = self.analyzer.analyze_content(transcript)
        
        self.assertIsInstance(context, ContentContext)
        self.assertEqual(context.transcript_text, transcript)
        self.assertIsInstance(context.keywords, list)
        self.assertIsInstance(context.scene_descriptions, list)
        self.assertIn(context.video_style, ["documentary", "commercial", "educational", "corporate", "entertainment", "general"])
        self.assertIn(context.sentiment, ["positive", "negative", "neutral"])

class TestStockMediaProviders(unittest.TestCase):
    """Test stock media provider functionality"""
    
    def test_unsplash_provider_demo_mode(self):
        """Test Unsplash provider in demo mode (no API key)"""
        provider = UnsplashProvider()
        assets = provider.search("business", "photo", 3)
        
        self.assertIsInstance(assets, list)
        self.assertLessEqual(len(assets), 5)  # Demo mode returns max 5
        
        if assets:
            asset = assets[0]
            self.assertIsInstance(asset, MediaAsset)
            self.assertEqual(asset.source, "demo")
            self.assertIn("business", asset.title.lower())
    
    def test_pexels_provider_demo_mode(self):
        """Test Pexels provider in demo mode (no API key)"""
        provider = PexelsProvider()
        
        # Test photo search
        photo_assets = provider.search("technology", "photo", 3)
        self.assertIsInstance(photo_assets, list)
        
        # Test video search
        video_assets = provider.search("technology", "video", 2)
        self.assertIsInstance(video_assets, list)
        
        if video_assets:
            video_asset = video_assets[0]
            self.assertIsInstance(video_asset.duration, float)
            self.assertGreater(video_asset.duration, 0)

class TestSmartBRollEngine(unittest.TestCase):
    """Test the main B-roll suggestion engine"""
    
    def setUp(self):
        self.engine = SmartBRollSuggestionEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine.providers, dict)
        self.assertIn("unsplash", self.engine.providers)
        self.assertIn("pexels", self.engine.providers)
        self.assertIsInstance(self.engine.content_analyzer, ContentAnalyzer)
    
    def test_suggestion_generation(self):
        """Test B-roll suggestion generation"""
        transcript = """
        Welcome to our documentary about sustainable technology. 
        We're exploring how solar panels and wind turbines are 
        transforming the energy landscape in urban environments.
        """
        
        suggestions = self.engine.generate_suggestions(
            transcript=transcript,
            topics=["sustainability", "technology", "energy"]
        )
        
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 10)  # Max 10 suggestions
        
        if suggestions:
            suggestion = suggestions[0]
            self.assertIsInstance(suggestion, BRollSuggestion)
            self.assertIsInstance(suggestion.assets, list)
            self.assertIsInstance(suggestion.confidence_score, float)
            self.assertGreaterEqual(suggestion.confidence_score, 0.0)
            self.assertLessEqual(suggestion.confidence_score, 1.0)
    
    def test_relevance_scoring(self):
        """Test asset relevance scoring"""
        context = ContentContext(
            transcript_text="business meeting in corporate office",
            detected_entities=[],
            topics=["business"],
            sentiment="neutral",
            scene_descriptions=["business"],
            keywords=["business", "meeting", "corporate"],
            video_style="corporate",
            target_audience="business",
            duration_needed=30.0,
            aspect_ratio="16:9"
        )
        
        # Create test asset
        asset = MediaAsset(
            id="test_asset",
            title="Business Meeting in Corporate Office",
            description="Professional business meeting",
            url="https://example.com",
            thumbnail_url="https://example.com/thumb",
            download_url="https://example.com/download",
            source="test",
            license_type="Test License",
            license_url="https://example.com/license",
            author="Test Author",
            author_url="https://example.com/author",
            tags=["business", "meeting", "corporate"],
            dimensions={"width": 1920, "height": 1080},
            file_size=None,
            duration=None,
            relevance_score=0.8,
            metadata={}
        )
        
        score = self.engine._calculate_relevance_score(asset, "business", context)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.8)  # Should be boosted due to matches
    
    def test_export_functionality(self):
        """Test suggestion export functionality"""
        # Create a simple suggestion for testing
        asset = MediaAsset(
            id="test_asset",
            title="Test Asset",
            description="Test description",
            url="https://example.com",
            thumbnail_url="https://example.com/thumb",
            download_url="https://example.com/download",
            source="test",
            license_type="Test License",
            license_url="https://example.com/license",
            author="Test Author",
            author_url="https://example.com/author",
            tags=["test"],
            dimensions={"width": 1920, "height": 1080},
            file_size=None,
            duration=None,
            relevance_score=0.8,
            metadata={}
        )
        
        suggestion = BRollSuggestion(
            assets=[asset],
            context_match="test: business",
            usage_suggestion="Use for testing",
            timing_suggestions=[],
            transition_recommendations=["fade"],
            confidence_score=0.8,
            reasoning="Test reasoning"
        )
        
        # Test JSON export
        json_export = self.engine.export_suggestions([suggestion], "json")
        self.assertIsInstance(json_export, str)
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(json_export)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)
        self.assertIn("context_match", parsed[0])
        self.assertIn("assets", parsed[0])

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        self.engine = SmartBRollSuggestionEngine()
    
    def test_documentary_scenario(self):
        """Test B-roll suggestions for documentary content"""
        transcript = """
        Climate change is affecting wildlife populations around the world. 
        In the Arctic, polar bears are struggling to find food as ice caps melt. 
        Meanwhile, in tropical rainforests, deforestation threatens countless species.
        """
        
        suggestions = self.engine.generate_suggestions(
            transcript=transcript,
            topics=["climate change", "wildlife", "environment"]
        )
        
        self.assertGreater(len(suggestions), 0)
        
        # Check that suggestions are relevant to nature/environment
        nature_related = any(
            "nature" in suggestion.context_match.lower() or
            "wildlife" in suggestion.context_match.lower() or
            "environment" in suggestion.context_match.lower()
            for suggestion in suggestions
        )
        self.assertTrue(nature_related)
    
    def test_business_presentation_scenario(self):
        """Test B-roll suggestions for business presentation"""
        transcript = """
        Our quarterly results show strong growth in the technology sector. 
        Team collaboration has improved with our new digital tools, 
        and customer satisfaction is at an all-time high.
        """
        
        suggestions = self.engine.generate_suggestions(
            transcript=transcript,
            topics=["business", "technology", "teamwork"]
        )
        
        self.assertGreater(len(suggestions), 0)
        
        # Check for business-related suggestions
        business_related = any(
            "business" in suggestion.context_match.lower() or
            "technology" in suggestion.context_match.lower()
            for suggestion in suggestions
        )
        self.assertTrue(business_related)
    
    def test_educational_content_scenario(self):
        """Test B-roll suggestions for educational content"""
        transcript = """
        Today we're learning about photosynthesis in plants. 
        This process converts sunlight into energy, helping plants grow. 
        Students can observe this in our school garden experiment.
        """
        
        suggestions = self.engine.generate_suggestions(
            transcript=transcript,
            topics=["education", "science", "plants"]
        )
        
        self.assertGreater(len(suggestions), 0)
        
        # Check for educational/science-related suggestions
        educational_related = any(
            "education" in suggestion.context_match.lower() or
            "science" in suggestion.context_match.lower() or
            "plants" in suggestion.context_match.lower()
            for suggestion in suggestions
        )
        self.assertTrue(educational_related)

if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)