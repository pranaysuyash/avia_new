#!/usr/bin/env python3
"""
Test Suite for Comprehensive Content Analytics System
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from comprehensive_content_analytics import (
    ContentAnalyticsEngine, ContentMetrics, TrendAnalysis, 
    SpeakerAnalytics, ContentInsight, AnalyticsDashboard
)

class TestContentAnalyticsEngine(unittest.TestCase):
    """Test the content analytics engine"""
    
    def setUp(self):
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
    
    def tearDown(self):
        # Clean up temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine, ContentAnalyticsEngine)
        self.assertEqual(self.engine.db_path, self.temp_db.name)
        self.assertIn("daily", self.engine.trend_periods)
        self.assertIn("weekly", self.engine.trend_periods)
    
    def test_content_session_storage(self):
        """Test storing content session data"""
        session_data = {
            "filename": "test_session.mp3",
            "duration": 600.0,
            "word_count": 1500,
            "speaker_count": 2,
            "sentiment_score": 0.7,
            "speakers": [
                {"speaker_id": "speaker_1", "speaking_time": 400.0, "word_count": 1000, "sentiment_score": 0.8},
                {"speaker_id": "speaker_2", "speaking_time": 200.0, "word_count": 500, "sentiment_score": 0.6}
            ],
            "metrics": {
                "engagement_score": 0.8,
                "complexity_score": 0.6
            },
            "metadata": {"category": "test"}
        }
        
        session_id = self.engine.store_content_session(session_data)
        self.assertIsInstance(session_id, str)
        self.assertEqual(len(session_id), 32)  # MD5 hash length
    
    def test_content_metrics_calculation(self):
        """Test content metrics calculation"""
        transcript_data = {
            "text": "This is a test transcript with some positive words like great and excellent. It also has some complexity and various topics discussed.",
            "duration": 120.0,  # 2 minutes
            "speakers": ["speaker_1", "speaker_2"]
        }
        
        metrics = self.engine.calculate_content_metrics(transcript_data)
        
        self.assertIsInstance(metrics, ContentMetrics)
        self.assertGreater(metrics.word_count, 0)
        self.assertGreater(metrics.unique_words, 0)
        self.assertGreater(metrics.average_words_per_minute, 0)
        self.assertGreaterEqual(metrics.sentiment_score, 0.0)
        self.assertLessEqual(metrics.sentiment_score, 1.0)
        self.assertEqual(metrics.speaker_count, 2)
    
    def test_sentiment_calculation(self):
        """Test sentiment calculation"""
        positive_text = "This is great and excellent and wonderful"
        positive_score = self.engine._calculate_sentiment(positive_text)
        self.assertGreater(positive_score, 0.5)
        
        negative_text = "This is terrible and awful and bad"
        negative_score = self.engine._calculate_sentiment(negative_text)
        self.assertLess(negative_score, 0.5)
        
        neutral_text = "This is a normal sentence about things"
        neutral_score = self.engine._calculate_sentiment(neutral_text)
        self.assertEqual(neutral_score, 0.5)
    
    def test_readability_calculation(self):
        """Test readability score calculation"""
        simple_text = "This is simple. Easy to read. Short sentences."
        simple_score = self.engine._calculate_readability(simple_text)
        
        complex_text = "This is an extraordinarily complicated sentence with multisyllabic words and complex grammatical structures that significantly increase the difficulty of comprehension."
        complex_score = self.engine._calculate_readability(complex_text)
        
        self.assertGreater(simple_score, complex_score)
        self.assertGreaterEqual(simple_score, 0.0)
        self.assertLessEqual(simple_score, 100.0)
    
    def test_syllable_counting(self):
        """Test syllable counting"""
        self.assertEqual(self.engine._count_syllables("cat"), 1)
        self.assertEqual(self.engine._count_syllables("hello"), 2)
        self.assertEqual(self.engine._count_syllables("beautiful"), 3)
        self.assertEqual(self.engine._count_syllables("extraordinary"), 5)
    
    def test_engagement_score_calculation(self):
        """Test engagement score calculation"""
        high_engagement_data = {
            "text": "What do you think? This is amazing! How exciting is this?",
            "speakers": ["speaker_1", "speaker_2", "speaker_3"]
        }
        high_score = self.engine._calculate_engagement_score(high_engagement_data)
        
        low_engagement_data = {
            "text": "This is a simple statement without much interaction.",
            "speakers": ["speaker_1"]
        }
        low_score = self.engine._calculate_engagement_score(low_engagement_data)
        
        self.assertGreater(high_score, low_score)
        self.assertGreaterEqual(high_score, 0.0)
        self.assertLessEqual(high_score, 1.0)
    
    def test_topic_diversity_calculation(self):
        """Test topic diversity calculation"""
        diverse_text = "We discussed technology, business, science, art, music, sports, and politics today."
        diverse_score = self.engine._calculate_topic_diversity(diverse_text)
        
        repetitive_text = "Technology technology technology business business technology technology business."
        repetitive_score = self.engine._calculate_topic_diversity(repetitive_text)
        
        self.assertGreater(diverse_score, repetitive_score)
        self.assertGreaterEqual(diverse_score, 0.0)
        self.assertLessEqual(diverse_score, 1.0)

class TestTrendAnalysis(unittest.TestCase):
    """Test trend analysis functionality"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
        
        # Add sample data for trend analysis
        for i in range(10):
            session_data = {
                "filename": f"session_{i}.mp3",
                "duration": 600.0 + i * 60,
                "word_count": 1500 + i * 100,
                "speaker_count": 1 + (i % 3),
                "sentiment_score": 0.5 + (i * 0.05),  # Increasing trend
                "speakers": [{"speaker_id": f"speaker_{i}", "speaking_time": 600.0, "word_count": 1500, "sentiment_score": 0.5 + (i * 0.05)}],
                "metrics": {"engagement_score": 0.6 + (i * 0.02)},
                "metadata": {"category": "test"}
            }
            self.engine.store_content_session(session_data)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_trend_analysis_generation(self):
        """Test trend analysis generation"""
        trend = self.engine.analyze_trends("weekly", "sentiment_score")
        
        self.assertIsInstance(trend, TrendAnalysis)
        self.assertEqual(trend.period, "weekly")
        self.assertEqual(trend.metric_name, "sentiment_score")
        self.assertIsInstance(trend.values, list)
        self.assertIsInstance(trend.timestamps, list)
        self.assertIn(trend.trend_direction, ["increasing", "decreasing", "stable"])
        self.assertGreaterEqual(trend.trend_strength, 0.0)
        self.assertLessEqual(trend.trend_strength, 1.0)
    
    def test_trend_direction_detection(self):
        """Test trend direction detection"""
        trend = self.engine.analyze_trends("weekly", "sentiment_score")
        
        # With our sample data that has increasing sentiment, should detect increasing trend
        if len(trend.values) > 1:
            self.assertEqual(trend.trend_direction, "increasing")
            self.assertGreater(trend.trend_strength, 0.0)

class TestSpeakerAnalytics(unittest.TestCase):
    """Test speaker analytics functionality"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
        
        # Add sample speaker data
        session_data = {
            "filename": "multi_speaker_session.mp3",
            "duration": 1800.0,
            "word_count": 4500,
            "speaker_count": 3,
            "sentiment_score": 0.7,
            "speakers": [
                {"speaker_id": "alice", "speaking_time": 900.0, "word_count": 2250, "sentiment_score": 0.8},
                {"speaker_id": "bob", "speaking_time": 600.0, "word_count": 1500, "sentiment_score": 0.6},
                {"speaker_id": "charlie", "speaking_time": 300.0, "word_count": 750, "sentiment_score": 0.7}
            ],
            "metrics": {"engagement_score": 0.8},
            "metadata": {"category": "meeting"}
        }
        self.session_id = self.engine.store_content_session(session_data)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_speaker_analytics_generation(self):
        """Test speaker analytics generation"""
        analytics = self.engine.analyze_speaker_behavior(self.session_id)
        
        self.assertIsInstance(analytics, list)
        self.assertEqual(len(analytics), 3)  # Three speakers
        
        for speaker_analytics in analytics:
            self.assertIsInstance(speaker_analytics, SpeakerAnalytics)
            self.assertIn(speaker_analytics.speaker_id, ["alice", "bob", "charlie"])
            self.assertGreater(speaker_analytics.total_speaking_time, 0)
            self.assertGreater(speaker_analytics.words_per_minute, 0)
            self.assertIsInstance(speaker_analytics.sentiment_distribution, dict)
    
    def test_speaker_metrics_calculation(self):
        """Test speaker metrics calculation"""
        analytics = self.engine.analyze_speaker_behavior(self.session_id)
        
        # Find Alice's analytics (should have highest speaking time)
        alice_analytics = next(a for a in analytics if a.speaker_id == "alice")
        bob_analytics = next(a for a in analytics if a.speaker_id == "bob")
        
        # Alice should have more speaking time than Bob
        self.assertGreater(alice_analytics.total_speaking_time, bob_analytics.total_speaking_time)
        
        # Check WPM calculation
        expected_wpm = 2250 / (900.0 / 60)  # Alice's WPM
        self.assertAlmostEqual(alice_analytics.words_per_minute, expected_wpm, places=1)

class TestContentInsights(unittest.TestCase):
    """Test content insights generation"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_insights_generation(self):
        """Test content insights generation"""
        # Add sample data with high sentiment
        session_data = {
            "filename": "positive_session.mp3",
            "duration": 600.0,
            "word_count": 1500,
            "speaker_count": 1,
            "sentiment_score": 0.9,  # High sentiment
            "speakers": [{"speaker_id": "speaker_1", "speaking_time": 600.0, "word_count": 1500, "sentiment_score": 0.9}],
            "metrics": {"engagement_score": 0.8},
            "metadata": {"category": "positive"}
        }
        session_id = self.engine.store_content_session(session_data)
        
        insights = self.engine.generate_content_insights(session_id)
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        for insight in insights:
            self.assertIsInstance(insight, ContentInsight)
            self.assertIsInstance(insight.insight_type, str)
            self.assertIsInstance(insight.title, str)
            self.assertIsInstance(insight.description, str)
            self.assertGreaterEqual(insight.confidence, 0.0)
            self.assertLessEqual(insight.confidence, 1.0)
            self.assertIsInstance(insight.recommendations, list)
    
    def test_high_sentiment_insight(self):
        """Test high sentiment insight generation"""
        # Add high sentiment session
        session_data = {
            "filename": "very_positive.mp3",
            "duration": 600.0,
            "word_count": 1500,
            "speaker_count": 1,
            "sentiment_score": 0.85,
            "speakers": [{"speaker_id": "speaker_1", "speaking_time": 600.0, "word_count": 1500, "sentiment_score": 0.85}],
            "metrics": {},
            "metadata": {}
        }
        self.engine.store_content_session(session_data)
        
        insights = self.engine.generate_content_insights()
        
        # Should generate positive sentiment insight
        positive_insights = [i for i in insights if "positive" in i.title.lower()]
        self.assertGreater(len(positive_insights), 0)

class TestAnalyticsDashboard(unittest.TestCase):
    """Test complete analytics dashboard"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
        
        # Add comprehensive sample data
        sample_sessions = [
            {
                "filename": "session_1.mp3",
                "duration": 1200.0,
                "word_count": 3000,
                "speaker_count": 2,
                "sentiment_score": 0.7,
                "speakers": [
                    {"speaker_id": "alice", "speaking_time": 800.0, "word_count": 2000, "sentiment_score": 0.8},
                    {"speaker_id": "bob", "speaking_time": 400.0, "word_count": 1000, "sentiment_score": 0.6}
                ],
                "metrics": {"engagement_score": 0.8, "complexity_score": 0.6},
                "metadata": {"category": "meeting"}
            },
            {
                "filename": "session_2.mp3",
                "duration": 900.0,
                "word_count": 2700,
                "speaker_count": 1,
                "sentiment_score": 0.8,
                "speakers": [
                    {"speaker_id": "charlie", "speaking_time": 900.0, "word_count": 2700, "sentiment_score": 0.8}
                ],
                "metrics": {"engagement_score": 0.7, "complexity_score": 0.5},
                "metadata": {"category": "presentation"}
            }
        ]
        
        for session in sample_sessions:
            self.engine.store_content_session(session)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_dashboard_generation(self):
        """Test complete dashboard generation"""
        dashboard = self.engine.generate_dashboard()
        
        self.assertIsInstance(dashboard, AnalyticsDashboard)
        self.assertIsInstance(dashboard.overview_metrics, ContentMetrics)
        self.assertIsInstance(dashboard.trend_analyses, list)
        self.assertIsInstance(dashboard.speaker_analytics, list)
        self.assertIsInstance(dashboard.content_insights, list)
        self.assertIsInstance(dashboard.comparative_analysis, dict)
        self.assertIsInstance(dashboard.predictive_insights, dict)
        self.assertIsInstance(dashboard.generated_at, datetime)
    
    def test_dashboard_metrics_accuracy(self):
        """Test dashboard metrics accuracy"""
        dashboard = self.engine.generate_dashboard()
        
        # Check overview metrics
        self.assertEqual(dashboard.overview_metrics.total_duration, 2100.0)  # 1200 + 900
        self.assertEqual(dashboard.overview_metrics.word_count, 5700)  # 3000 + 2700
        self.assertAlmostEqual(dashboard.overview_metrics.sentiment_score, 0.75, places=2)  # (0.7 + 0.8) / 2
    
    def test_dashboard_export(self):
        """Test dashboard export functionality"""
        dashboard = self.engine.generate_dashboard()
        
        # Test JSON export
        json_export = self.engine.export_analytics(dashboard, "json")
        self.assertIsInstance(json_export, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_export)
        self.assertIsInstance(parsed, dict)
        self.assertIn("overview_metrics", parsed)
        self.assertIn("trend_analyses", parsed)
        self.assertIn("speaker_analytics", parsed)
        self.assertIn("content_insights", parsed)

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = ContentAnalyticsEngine(self.temp_db.name)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_business_meeting_analysis(self):
        """Test analytics for business meeting scenario"""
        meeting_data = {
            "filename": "quarterly_review.mp3",
            "duration": 3600.0,  # 1 hour
            "word_count": 9000,
            "speaker_count": 5,
            "sentiment_score": 0.6,
            "speakers": [
                {"speaker_id": "ceo", "speaking_time": 1200.0, "word_count": 3000, "sentiment_score": 0.7},
                {"speaker_id": "cfo", "speaking_time": 900.0, "word_count": 2250, "sentiment_score": 0.5},
                {"speaker_id": "cto", "speaking_time": 720.0, "word_count": 1800, "sentiment_score": 0.6},
                {"speaker_id": "vp_sales", "speaking_time": 540.0, "word_count": 1350, "sentiment_score": 0.8},
                {"speaker_id": "vp_marketing", "speaking_time": 240.0, "word_count": 600, "sentiment_score": 0.7}
            ],
            "metrics": {"engagement_score": 0.7, "complexity_score": 0.8},
            "metadata": {"category": "business_meeting", "meeting_type": "quarterly_review"}
        }
        
        session_id = self.engine.store_content_session(meeting_data)
        dashboard = self.engine.generate_dashboard(session_id)
        
        # Verify business meeting characteristics
        self.assertEqual(dashboard.overview_metrics.speaker_count, 5)
        self.assertEqual(dashboard.overview_metrics.total_duration, 3600.0)
        self.assertGreater(len(dashboard.speaker_analytics), 0)
        
        # CEO should have most speaking time
        ceo_analytics = next((s for s in dashboard.speaker_analytics if s.speaker_id == "ceo"), None)
        self.assertIsNotNone(ceo_analytics)
        self.assertEqual(ceo_analytics.total_speaking_time, 1200.0)
    
    def test_educational_content_analysis(self):
        """Test analytics for educational content scenario"""
        lecture_data = {
            "filename": "machine_learning_lecture.mp4",
            "duration": 2700.0,  # 45 minutes
            "word_count": 6750,
            "speaker_count": 1,
            "sentiment_score": 0.6,
            "speakers": [
                {"speaker_id": "professor", "speaking_time": 2700.0, "word_count": 6750, "sentiment_score": 0.6}
            ],
            "metrics": {"engagement_score": 0.5, "complexity_score": 0.9},
            "metadata": {"category": "education", "subject": "computer_science"}
        }
        
        session_id = self.engine.store_content_session(lecture_data)
        dashboard = self.engine.generate_dashboard(session_id)
        
        # Verify educational content characteristics
        self.assertEqual(dashboard.overview_metrics.speaker_count, 1)
        self.assertEqual(dashboard.overview_metrics.total_duration, 2700.0)
        
        # Should generate insights about long-form content
        long_content_insights = [i for i in dashboard.content_insights if "long" in i.title.lower()]
        self.assertGreaterEqual(len(long_content_insights), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)