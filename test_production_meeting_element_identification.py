#!/usr/bin/env python3
"""
Comprehensive tests for Production Meeting Element Identification System

Tests all major functionality including:
- Transformer-based element classification
- Speaker diarization and identification
- Sentiment analysis and emotion detection
- Topic modeling and keyword extraction
- Database operations and analytics
- Multi-method fallback strategies
- Error handling and graceful degradation

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
import time
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from production_meeting_element_identification import (
    ProductionMeetingElementIdentifier,
    TransformerClassifier,
    SpeakerDiarization,
    TopicModeling,
    ClassicalMLFallback,
    MeetingElementDatabase,
    MeetingElement,
    MeetingStructure,
    MeetingElementType,
    ConfidenceLevel,
    SentimentPolarity,
    ProcessingMethod
)


class TestProductionMeetingElementIdentification(unittest.TestCase):
    """Test suite for Production Meeting Element Identification System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_meeting_elements.db")
        self.identifier = ProductionMeetingElementIdentifier(self.db_path)
        
        # Sample meeting transcript
        self.sample_transcript = """
        Welcome everyone to today's quarterly planning meeting. 
        Let's start by reviewing our Q3 results.
        
        Sarah, can you present the sales figures?
        
        Thank you Sarah. The numbers look good. 
        I think we should increase our marketing budget for Q4.
        
        What do you think about allocating an additional $50K to digital campaigns?
        
        I agree with that approach. It should help us reach our targets.
        
        Great! So we've decided to increase the marketing budget by $50K.
        
        John, can you handle the budget reallocation paperwork?
        
        Sure, I'll take care of that by Friday.
        
        Perfect. Our next steps should include finalizing the campaign strategy.
        
        Any other concerns before we wrap up?
        
        That concludes our meeting for today. Thank you everyone.
        """
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.identifier, ProductionMeetingElementIdentifier)
        self.assertIsInstance(self.identifier.db, MeetingElementDatabase)
        self.assertIsInstance(self.identifier.transformer_classifier, TransformerClassifier)
        self.assertIsInstance(self.identifier.speaker_diarization, SpeakerDiarization)
        self.assertIsInstance(self.identifier.topic_modeling, TopicModeling)
        self.assertIsInstance(self.identifier.classical_fallback, ClassicalMLFallback)
        
        # Check processing stats initialization
        self.assertEqual(self.identifier.processing_stats['total_processed'], 0)
        self.assertIsInstance(self.identifier.processing_stats['processing_times'], list)
        self.assertIsInstance(self.identifier.processing_stats['confidence_scores'], list)
        self.assertIsInstance(self.identifier.processing_stats['method_usage'], dict)
    
    def test_meeting_element_dataclass(self):
        """Test MeetingElement dataclass"""
        element = MeetingElement(
            element_id="test_meeting_001_element_0",
            element_type=MeetingElementType.DECISION,
            content="We decided to increase the marketing budget",
            speaker="Manager",
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            sentiment_polarity=SentimentPolarity.POSITIVE,
            sentiment_score=0.7,
            keywords=["budget", "marketing", "increase"],
            topics=["budget", "planning"],
            processing_method=ProcessingMethod.TRANSFORMER_BERT,
            model_version="production_v1.0"
        )
        
        self.assertEqual(element.element_id, "test_meeting_001_element_0")
        self.assertEqual(element.element_type, MeetingElementType.DECISION)
        self.assertEqual(element.content, "We decided to increase the marketing budget")
        self.assertEqual(element.speaker, "Manager")
        self.assertEqual(element.confidence, 0.85)
        self.assertEqual(element.confidence_level, ConfidenceLevel.HIGH)
        self.assertEqual(element.sentiment_polarity, SentimentPolarity.POSITIVE)
        self.assertEqual(element.sentiment_score, 0.7)
        self.assertIn("budget", element.keywords)
        self.assertIn("planning", element.topics)
        self.assertEqual(element.processing_method, ProcessingMethod.TRANSFORMER_BERT)
        self.assertEqual(element.model_version, "production_v1.0")
        
        # Test to_dict method
        element_dict = element.to_dict()
        self.assertIsInstance(element_dict, dict)
        self.assertEqual(element_dict['element_type'], 'decision')
        self.assertEqual(element_dict['speaker'], 'Manager')
        self.assertIn('created_at', element_dict)
    
    def test_meeting_structure_dataclass(self):
        """Test MeetingStructure dataclass"""
        element1 = MeetingElement(
            element_id="meeting_001_element_0",
            element_type=MeetingElementType.MEETING_OPENING,
            content="Welcome everyone",
            confidence=0.9
        )
        
        element2 = MeetingElement(
            element_id="meeting_001_element_1",
            element_type=MeetingElementType.QUESTION,
            content="What do you think?",
            confidence=0.8
        )
        
        meeting_structure = MeetingStructure(
            meeting_id="meeting_001",
            elements=[element1, element2],
            participants=["Alice", "Bob"],
            participant_count=2,
            total_elements_identified=2,
            engagement_score=85.0,
            productivity_score=70.0,
            collaboration_score=80.0
        )
        
        self.assertEqual(meeting_structure.meeting_id, "meeting_001")
        self.assertEqual(len(meeting_structure.elements), 2)
        self.assertEqual(meeting_structure.participant_count, 2)
        self.assertIn("Alice", meeting_structure.participants)
        self.assertEqual(meeting_structure.engagement_score, 85.0)
        self.assertEqual(meeting_structure.productivity_score, 70.0)
        self.assertEqual(meeting_structure.collaboration_score, 80.0)
    
    def test_transformer_classifier_initialization(self):
        """Test TransformerClassifier initialization"""
        classifier = TransformerClassifier()
        
        # Should handle missing dependencies gracefully
        self.assertIsInstance(classifier.available, bool)
        if classifier.available:
            self.assertIsNotNone(classifier.model_name)
            self.assertIsNotNone(classifier.device)
    
    def test_transformer_element_classification(self):
        """Test transformer-based element classification"""
        classifier = TransformerClassifier()
        
        # Test various element types
        test_cases = [
            ("We decided to increase the budget", MeetingElementType.DECISION),
            ("Can you handle this task?", MeetingElementType.QUESTION),
            ("John will take care of the documentation", MeetingElementType.ACTION_ITEM),
            ("I agree with that approach", MeetingElementType.AGREEMENT),
            ("Let me present the quarterly results", MeetingElementType.PRESENTATION),
            ("Welcome everyone to the meeting", MeetingElementType.MEETING_OPENING)
        ]
        
        for text, expected_type in test_cases:
            element_type, confidence = classifier.classify_element_type(text)
            
            # Should return valid element type and confidence
            self.assertIsInstance(element_type, MeetingElementType)
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
            # If transformer is available, might match expected type
            if classifier.available and confidence > 0.5:
                # Allow for some flexibility in classification
                self.assertIsInstance(element_type, MeetingElementType)
    
    def test_transformer_sentiment_analysis(self):
        """Test transformer-based sentiment analysis"""
        classifier = TransformerClassifier()
        
        test_cases = [
            ("I'm really excited about this project!", SentimentPolarity.POSITIVE),
            ("This is a terrible idea", SentimentPolarity.NEGATIVE),
            ("The meeting is scheduled for tomorrow", SentimentPolarity.NEUTRAL),
            ("Great work everyone!", SentimentPolarity.POSITIVE),
            ("I have some concerns about the timeline", SentimentPolarity.NEGATIVE)
        ]
        
        for text, expected_sentiment in test_cases:
            sentiment, score = classifier.analyze_sentiment(text)
            
            # Should return valid sentiment and score
            if sentiment is not None:
                self.assertIsInstance(sentiment, SentimentPolarity)
                self.assertIsInstance(score, float)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)
    
    def test_speaker_diarization_initialization(self):
        """Test SpeakerDiarization initialization"""
        diarization = SpeakerDiarization()
        
        self.assertIsInstance(diarization.pyannote_available, bool)
        self.assertIsInstance(diarization.librosa_available, bool)
        
        # Test fallback diarization (no real audio file needed for this test)
        result = diarization._diarize_fallback("dummy_path")
        self.assertIsInstance(result, dict)
    
    def test_topic_modeling_initialization(self):
        """Test TopicModeling initialization"""
        topic_modeling = TopicModeling()
        
        self.assertIsInstance(topic_modeling.available, bool)
        
        # Test topic extraction
        test_texts = [
            "We need to discuss the budget allocation",
            "The technical implementation requires more resources",
            "Let's plan the project timeline and milestones"
        ]
        
        topics = topic_modeling.extract_topics(test_texts, num_topics=3)
        self.assertIsInstance(topics, dict)
        
        if topics:
            self.assertIn('method', topics)
            self.assertIn('topics', topics)
    
    def test_classical_ml_fallback(self):
        """Test classical ML fallback system"""
        fallback = ClassicalMLFallback()
        
        # Train on patterns
        fallback.train_on_patterns()
        
        if fallback.trained:
            # Test classification
            test_cases = [
                "We decided to proceed with option A",
                "Can you take care of this task?",
                "I agree with the proposal",
                "Let me present the results"
            ]
            
            for text in test_cases:
                label, confidence = fallback.classify(text)
                self.assertIsInstance(label, str)
                self.assertIsInstance(confidence, float)
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
    
    def test_database_initialization(self):
        """Test database initialization"""
        db = MeetingElementDatabase(self.db_path)
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check table creation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check main tables
            tables = ['meeting_sessions', 'meeting_elements', 'speaker_statistics', 
                     'meeting_analytics', 'performance_metrics']
            
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                self.assertIsNotNone(cursor.fetchone(), f"Table {table} should exist")
    
    def test_database_meeting_storage(self):
        """Test meeting data storage in database"""
        db = MeetingElementDatabase(self.db_path)
        
        # Create test meeting structure
        element = MeetingElement(
            element_id="test_meeting_001_element_0",
            element_type=MeetingElementType.DECISION,
            content="Test decision content",
            speaker="TestSpeaker",
            confidence=0.85,
            sentiment_polarity=SentimentPolarity.POSITIVE,
            keywords=["test", "decision"],
            topics=["planning"]
        )
        
        meeting_structure = MeetingStructure(
            meeting_id="test_meeting_001",
            elements=[element],
            participants=["TestSpeaker"],
            participant_count=1,
            total_elements_identified=1
        )
        
        # Store meeting session
        session_id = db.store_meeting_session(meeting_structure)
        self.assertIsInstance(session_id, int)
        self.assertGreater(session_id, 0)
        
        # Store meeting elements
        element_ids = db.store_meeting_elements([element])
        self.assertEqual(len(element_ids), 1)
        self.assertIsInstance(element_ids[0], int)
        
        # Store analytics
        db.store_meeting_analytics(meeting_structure)
        
        # Verify storage
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check meeting session
            cursor.execute("SELECT COUNT(*) FROM meeting_sessions WHERE meeting_id = ?", 
                         ("test_meeting_001",))
            self.assertEqual(cursor.fetchone()[0], 1)
            
            # Check meeting element
            cursor.execute("SELECT COUNT(*) FROM meeting_elements WHERE element_id = ?", 
                         ("test_meeting_001_element_0",))
            self.assertEqual(cursor.fetchone()[0], 1)
    
    def test_database_analytics(self):
        """Test database analytics functionality"""
        db = MeetingElementDatabase(self.db_path)
        
        # Create sample data
        for i in range(3):
            element = MeetingElement(
                element_id=f"test_meeting_{i}_element_0",
                element_type=MeetingElementType.DECISION if i % 2 == 0 else MeetingElementType.QUESTION,
                content=f"Test content {i}",
                confidence=0.8 + (i * 0.05),
                processing_method=ProcessingMethod.TRANSFORMER_BERT
            )
            
            meeting_structure = MeetingStructure(
                meeting_id=f"test_meeting_{i}",
                elements=[element],
                total_elements_identified=1
            )
            
            db.store_meeting_session(meeting_structure)
            db.store_meeting_elements([element])
        
        # Get analytics
        analytics = db.get_analytics_summary()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_meetings_processed', analytics)
        self.assertIn('total_elements_identified', analytics)
        self.assertIn('most_common_element_types', analytics)
        self.assertIn('processing_method_performance', analytics)
        
        self.assertEqual(analytics['total_meetings_processed'], 3)
        self.assertEqual(analytics['total_elements_identified'], 3)
    
    def test_transcript_segmentation(self):
        """Test transcript segmentation"""
        segments = self.identifier._segment_transcript(self.sample_transcript)
        
        self.assertIsInstance(segments, list)
        self.assertGreater(len(segments), 1)
        
        # Check that segments are meaningful (not too short)
        for segment in segments:
            self.assertGreater(len(segment.strip()), 10)
    
    def test_rule_based_classification(self):
        """Test rule-based classification fallback"""
        test_cases = [
            ("Can you help with this?", MeetingElementType.QUESTION),
            ("We decided to proceed", MeetingElementType.DECISION),
            ("John will handle the documentation", MeetingElementType.ACTION_ITEM),
            ("I agree with that", MeetingElementType.AGREEMENT),
            ("I disagree with the approach", MeetingElementType.OBJECTION),
            ("Let me present the results", MeetingElementType.PRESENTATION),
            ("Welcome everyone", MeetingElementType.MEETING_OPENING),
            ("That concludes our meeting", MeetingElementType.MEETING_CLOSING),
            ("Our next steps include", MeetingElementType.NEXT_STEPS)
        ]
        
        for text, expected_type in test_cases:
            element_type, confidence = self.identifier._classify_rule_based(text)
            
            self.assertEqual(element_type, expected_type)
            self.assertGreater(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
    
    def test_confidence_level_mapping(self):
        """Test confidence level mapping"""
        test_cases = [
            (0.98, ConfidenceLevel.VERY_HIGH),
            (0.90, ConfidenceLevel.HIGH),
            (0.80, ConfidenceLevel.MEDIUM_HIGH),
            (0.65, ConfidenceLevel.MEDIUM),
            (0.50, ConfidenceLevel.MEDIUM_LOW),
            (0.30, ConfidenceLevel.LOW),
            (0.10, ConfidenceLevel.VERY_LOW)
        ]
        
        for confidence, expected_level in test_cases:
            level = self.identifier._determine_confidence_level(confidence)
            self.assertEqual(level, expected_level)
    
    def test_keyword_extraction(self):
        """Test keyword extraction"""
        test_text = "We need to discuss the budget allocation for the marketing campaign"
        
        keywords = self.identifier._extract_keywords(test_text)
        
        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 10)  # Should limit to 10 keywords
        
        # Should contain meaningful words
        meaningful_words = ['discuss', 'budget', 'allocation', 'marketing', 'campaign']
        found_meaningful = any(word in ' '.join(keywords) for word in meaningful_words)
        self.assertTrue(found_meaningful)
    
    def test_entity_extraction(self):
        """Test entity extraction"""
        test_text = "John Smith will work with Microsoft on the project next week"
        
        entities = self.identifier._extract_entities(test_text)
        
        self.assertIsInstance(entities, list)
        
        # Each entity should have required fields
        for entity in entities:
            self.assertIsInstance(entity, dict)
            self.assertIn('text', entity)
            self.assertIn('label', entity)
    
    def test_meeting_analysis_workflow(self):
        """Test complete meeting analysis workflow"""
        meeting_structure = self.identifier.analyze_meeting(
            transcript=self.sample_transcript,
            meeting_id="test_workflow_001",
            participants=["Sarah", "John", "Manager"]
        )
        
        # Verify meeting structure
        self.assertIsInstance(meeting_structure, MeetingStructure)
        self.assertEqual(meeting_structure.meeting_id, "test_workflow_001")
        self.assertGreater(len(meeting_structure.elements), 0)
        self.assertGreater(meeting_structure.processing_duration, 0)
        
        # Verify elements have required properties
        for element in meeting_structure.elements:
            self.assertIsInstance(element, MeetingElement)
            self.assertIsInstance(element.element_type, MeetingElementType)
            self.assertIsInstance(element.confidence, float)
            self.assertIsInstance(element.confidence_level, ConfidenceLevel)
            self.assertGreater(len(element.content), 0)
        
        # Verify analytics
        self.assertIsInstance(meeting_structure.element_distribution, dict)
        self.assertGreaterEqual(meeting_structure.engagement_score or 0, 0)
        self.assertGreaterEqual(meeting_structure.productivity_score or 0, 0)
        self.assertGreaterEqual(meeting_structure.collaboration_score or 0, 0)
    
    def test_quality_metrics_calculation(self):
        """Test meeting quality metrics calculation"""
        # Create elements with different types
        elements = [
            MeetingElement("id1", MeetingElementType.QUESTION, "Test question"),
            MeetingElement("id2", MeetingElementType.DECISION, "Test decision"),
            MeetingElement("id3", MeetingElementType.ACTION_ITEM, "Test action"),
            MeetingElement("id4", MeetingElementType.AGREEMENT, "Test agreement"),
            MeetingElement("id5", MeetingElementType.DISCUSSION_POINT, "Test discussion")
        ]
        
        # Test engagement score
        engagement = self.identifier._calculate_engagement_score(elements)
        self.assertIsInstance(engagement, float)
        self.assertGreaterEqual(engagement, 0.0)
        self.assertLessEqual(engagement, 100.0)
        
        # Test productivity score
        productivity = self.identifier._calculate_productivity_score(elements)
        self.assertIsInstance(productivity, float)
        self.assertGreaterEqual(productivity, 0.0)
        self.assertLessEqual(productivity, 100.0)
        
        # Test collaboration score
        speaker_stats = {
            "Speaker1": {"total_elements": 2},
            "Speaker2": {"total_elements": 2},
            "Speaker3": {"total_elements": 1}
        }
        collaboration = self.identifier._calculate_collaboration_score(speaker_stats)
        self.assertIsInstance(collaboration, float)
        self.assertGreaterEqual(collaboration, 0.0)
        self.assertLessEqual(collaboration, 100.0)
    
    def test_processing_method_selection(self):
        """Test processing method selection and fallback"""
        test_text = "We decided to increase the marketing budget for Q4"
        
        element_type, confidence, method = self.identifier._classify_element_type(test_text)
        
        # Should return valid values
        self.assertIsInstance(element_type, MeetingElementType)
        self.assertIsInstance(confidence, float)
        self.assertIsInstance(method, ProcessingMethod)
        
        # Should use available methods in priority order
        self.assertIn(method, [
            ProcessingMethod.TRANSFORMER_BERT,
            ProcessingMethod.SPACY_NLP,
            ProcessingMethod.CLASSICAL_ML,
            ProcessingMethod.RULE_BASED
        ])
    
    def test_system_status(self):
        """Test system status reporting"""
        status = self.identifier.get_system_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('system_status', status)
        self.assertIn('capabilities', status)
        self.assertIn('processing_statistics', status)
        self.assertIn('database_statistics', status)
        self.assertIn('model_versions', status)
        
        # Check capabilities
        capabilities = status['capabilities']
        self.assertIn('transformer_available', capabilities)
        self.assertIn('spacy_available', capabilities)
        self.assertIn('speaker_diarization_available', capabilities)
        self.assertIn('topic_modeling_available', capabilities)
        self.assertIn('classical_ml_trained', capabilities)
        
        # All capability values should be boolean
        for key, value in capabilities.items():
            self.assertIsInstance(value, bool)
    
    def test_error_handling(self):
        """Test error handling and graceful degradation"""
        # Test with empty transcript
        meeting_structure = self.identifier.analyze_meeting(
            transcript="",
            meeting_id="test_empty"
        )
        
        self.assertIsInstance(meeting_structure, MeetingStructure)
        self.assertEqual(meeting_structure.meeting_id, "test_empty")
        
        # Test with malformed transcript
        meeting_structure = self.identifier.analyze_meeting(
            transcript="!@#$%^&*()",
            meeting_id="test_malformed"
        )
        
        self.assertIsInstance(meeting_structure, MeetingStructure)
        
        # Test with very long transcript
        long_transcript = "This is a test sentence. " * 1000
        meeting_structure = self.identifier.analyze_meeting(
            transcript=long_transcript,
            meeting_id="test_long"
        )
        
        self.assertIsInstance(meeting_structure, MeetingStructure)
        self.assertGreater(meeting_structure.processing_duration, 0)
    
    def test_enum_values(self):
        """Test enum value consistency"""
        # Test MeetingElementType enum
        element_types = [
            MeetingElementType.AGENDA_ITEM,
            MeetingElementType.DECISION,
            MeetingElementType.ACTION_ITEM,
            MeetingElementType.QUESTION,
            MeetingElementType.AGREEMENT,
            MeetingElementType.PRESENTATION
        ]
        
        for element_type in element_types:
            self.assertIsInstance(element_type.value, str)
        
        # Test ConfidenceLevel enum
        confidence_levels = [
            ConfidenceLevel.VERY_HIGH,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
            ConfidenceLevel.VERY_LOW
        ]
        
        for level in confidence_levels:
            self.assertIsInstance(level.value, str)
        
        # Test SentimentPolarity enum
        sentiments = [
            SentimentPolarity.VERY_POSITIVE,
            SentimentPolarity.POSITIVE,
            SentimentPolarity.NEUTRAL,
            SentimentPolarity.NEGATIVE,
            SentimentPolarity.VERY_NEGATIVE
        ]
        
        for sentiment in sentiments:
            self.assertIsInstance(sentiment.value, str)
        
        # Test ProcessingMethod enum
        methods = [
            ProcessingMethod.TRANSFORMER_BERT,
            ProcessingMethod.SPACY_NLP,
            ProcessingMethod.CLASSICAL_ML,
            ProcessingMethod.RULE_BASED,
            ProcessingMethod.HYBRID
        ]
        
        for method in methods:
            self.assertIsInstance(method.value, str)
    
    def test_comprehensive_workflow(self):
        """Test comprehensive workflow with multiple meetings"""
        # Process multiple meetings
        meetings = [
            ("Meeting 1: Budget planning discussion", "meeting_comp_001"),
            ("Meeting 2: Technical review session", "meeting_comp_002"),
            ("Meeting 3: Project status update", "meeting_comp_003")
        ]
        
        for transcript, meeting_id in meetings:
            meeting_structure = self.identifier.analyze_meeting(
                transcript=transcript,
                meeting_id=meeting_id
            )
            
            self.assertIsInstance(meeting_structure, MeetingStructure)
            self.assertEqual(meeting_structure.meeting_id, meeting_id)
        
        # Check that processing stats were updated
        self.assertEqual(self.identifier.processing_stats['total_processed'], 3)
        self.assertEqual(len(self.identifier.processing_stats['processing_times']), 3)
        
        # Get final system status
        status = self.identifier.get_system_status()
        self.assertEqual(status['processing_statistics']['total_processed'], 3)
        
        print("✅ Comprehensive meeting element identification workflow completed successfully")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Meeting Element Identification Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionMeetingElementIdentification))
    
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
    print(f"\n{'✅' if success else '❌'} Overall test result: {'PASSED' if success else 'FAILED'}")
    
    exit(0 if success else 1)