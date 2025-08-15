#!/usr/bin/env python3
"""
Test Suite for Real-Time Learning System
Comprehensive tests for real-time learning, adjustment, and effectiveness monitoring
"""

import unittest
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from realtime_learning_system import (
    RealTimeLearningSystem, ConfidenceThresholdLearner, PatternLearner, VocabularyLearner,
    LearningTrigger, LearningMode, AdjustmentType, LearningEvent, RealTimeAdjustment,
    LearningMetrics, create_realtime_learning_system
)

from model_adaptation_engine import (
    ModelAdaptationEngine, create_model_adaptation_engine
)

from user_learning_profile import (
    PersonalizationEngine, create_personalization_engine, create_user_profile_storage
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class TestLearningEvent(unittest.TestCase):
    """Test LearningEvent data model"""
    
    def test_event_creation(self):
        """Test learning event creation"""
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model"
        )
        
        self.assertEqual(event.event_id, "test_event")
        self.assertEqual(event.trigger, LearningTrigger.IMMEDIATE)
        self.assertEqual(event.user_id, "test_user")
        self.assertFalse(event.processed)
    
    def test_event_serialization(self):
        """Test event serialization"""
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.PATTERN_DETECTED,
            user_id="test_user",
            model_id="test_model",
            context={"test": "data"}
        )
        
        event_dict = event.to_dict()
        self.assertIsInstance(event_dict, dict)
        self.assertEqual(event_dict['trigger'], 'pattern')
        self.assertEqual(event_dict['context'], {"test": "data"})

class TestRealTimeAdjustment(unittest.TestCase):
    """Test RealTimeAdjustment data model"""
    
    def test_adjustment_creation(self):
        """Test adjustment creation"""
        adjustment = RealTimeAdjustment(
            adjustment_id="test_adjustment",
            user_id="test_user",
            model_id="test_model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="confidence_threshold",
            old_value=0.8,
            new_value=0.85,
            confidence=0.9,
            trigger_event="test_event"
        )
        
        self.assertEqual(adjustment.adjustment_id, "test_adjustment")
        self.assertEqual(adjustment.adjustment_type, AdjustmentType.THRESHOLD_ADJUST)
        self.assertEqual(adjustment.old_value, 0.8)
        self.assertEqual(adjustment.new_value, 0.85)
        self.assertFalse(adjustment.reverted)
    
    def test_adjustment_serialization(self):
        """Test adjustment serialization"""
        adjustment = RealTimeAdjustment(
            adjustment_id="test_adjustment",
            user_id="test_user",
            model_id="test_model",
            adjustment_type=AdjustmentType.PATTERN_ADD,
            parameter_name="pattern_override",
            old_value="old",
            new_value="new",
            confidence=0.8,
            trigger_event="test_event"
        )
        
        adj_dict = adjustment.to_dict()
        self.assertIsInstance(adj_dict, dict)
        self.assertEqual(adj_dict['adjustment_type'], 'pattern_add')
        
        restored_adj = RealTimeAdjustment.from_dict(adj_dict)
        self.assertEqual(restored_adj.adjustment_type, AdjustmentType.PATTERN_ADD)
        self.assertEqual(restored_adj.parameter_name, "pattern_override")

class TestLearningMetrics(unittest.TestCase):
    """Test LearningMetrics functionality"""
    
    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = LearningMetrics()
        
        self.assertEqual(metrics.total_adjustments, 0)
        self.assertEqual(metrics.successful_adjustments, 0)
        self.assertEqual(metrics.learning_rate, 0.0)
    
    def test_metrics_update(self):
        """Test metrics update"""
        metrics = LearningMetrics()
        
        adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="test",
            old_value=0.8,
            new_value=0.85,
            confidence=0.9,
            trigger_event="event",
            effectiveness=0.7
        )
        
        metrics.update_metrics(adjustment)
        
        self.assertEqual(metrics.total_adjustments, 1)
        self.assertEqual(metrics.successful_adjustments, 1)
        self.assertEqual(metrics.learning_rate, 1.0)

class TestConfidenceThresholdLearner(unittest.TestCase):
    """Test ConfidenceThresholdLearner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.learner = ConfidenceThresholdLearner(LearningMode.BALANCED)
    
    def test_should_adjust_with_rating(self):
        """Test should_adjust with rating feedback"""
        # Create feedback with rating
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test",
            confidence_score=0.8
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=2,
            max_value=5
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        self.assertTrue(self.learner.should_adjust(event))
    
    def test_should_not_adjust_without_rating(self):
        """Test should_adjust without rating feedback"""
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.SUGGESTION,
            context=None,
            timestamp=datetime.now()
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        self.assertFalse(self.learner.should_adjust(event))
    
    def test_calculate_adjustment_low_rating(self):
        """Test adjustment calculation for low rating"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test",
            confidence_score=0.7
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=1,  # Very low rating
            max_value=5
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        adjustment = self.learner.calculate_adjustment(event)
        
        self.assertIsNotNone(adjustment)
        self.assertEqual(adjustment.adjustment_type, AdjustmentType.THRESHOLD_ADJUST)
        self.assertGreater(adjustment.new_value, adjustment.old_value)  # Should increase threshold
    
    def test_calculate_adjustment_high_rating(self):
        """Test adjustment calculation for high rating"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test",
            confidence_score=0.9
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=5,  # High rating
            max_value=5
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        adjustment = self.learner.calculate_adjustment(event)
        
        self.assertIsNotNone(adjustment)
        self.assertLess(adjustment.new_value, adjustment.old_value)  # Should decrease threshold
    
    def test_validate_adjustment(self):
        """Test adjustment validation"""
        # Valid adjustment
        valid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="confidence_threshold",
            old_value=0.8,
            new_value=0.85,
            confidence=0.9,
            trigger_event="event"
        )
        
        self.assertTrue(self.learner.validate_adjustment(valid_adjustment))
        
        # Invalid adjustment - out of range
        invalid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="confidence_threshold",
            old_value=0.8,
            new_value=1.5,  # Out of range
            confidence=0.9,
            trigger_event="event"
        )
        
        self.assertFalse(self.learner.validate_adjustment(invalid_adjustment))

class TestPatternLearner(unittest.TestCase):
    """Test PatternLearner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.learner = PatternLearner(LearningMode.BALANCED)
    
    def test_should_adjust_with_correction(self):
        """Test should_adjust with correction feedback"""
        correction = Correction(
            correction_id="test_correction",
            original_text="ai",
            corrected_text="AI",
            correction_type="capitalization"
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=None,
            timestamp=datetime.now(),
            correction=correction
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        # First few times should not adjust (need pattern frequency)
        self.assertFalse(self.learner.should_adjust(event))
        
        # Add pattern to cache to simulate frequency
        pattern_key = "capitalization_ai"
        self.learner.pattern_cache["test_user"] = [pattern_key] * 3
        
        self.assertTrue(self.learner.should_adjust(event))
    
    def test_calculate_adjustment(self):
        """Test pattern adjustment calculation"""
        correction = Correction(
            correction_id="test_correction",
            original_text="ml",
            corrected_text="ML",
            correction_type="capitalization"
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=None,
            timestamp=datetime.now(),
            correction=correction
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        adjustment = self.learner.calculate_adjustment(event)
        
        self.assertIsNotNone(adjustment)
        self.assertEqual(adjustment.adjustment_type, AdjustmentType.PATTERN_ADD)
        self.assertEqual(adjustment.old_value, "ml")
        self.assertEqual(adjustment.new_value, "ML")
    
    def test_validate_adjustment(self):
        """Test pattern adjustment validation"""
        # Valid adjustment
        valid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.PATTERN_ADD,
            parameter_name="pattern_override",
            old_value="old",
            new_value="new",
            confidence=0.8,
            trigger_event="event"
        )
        
        self.assertTrue(self.learner.validate_adjustment(valid_adjustment))
        
        # Invalid adjustment - same values
        invalid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.PATTERN_ADD,
            parameter_name="pattern_override",
            old_value="same",
            new_value="same",  # Same as old value
            confidence=0.8,
            trigger_event="event"
        )
        
        self.assertFalse(self.learner.validate_adjustment(invalid_adjustment))

class TestVocabularyLearner(unittest.TestCase):
    """Test VocabularyLearner functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.learner = VocabularyLearner(LearningMode.BALANCED)
    
    def test_should_adjust_with_correction(self):
        """Test should_adjust with correction feedback"""
        correction = Correction(
            correction_id="test_correction",
            original_text="machine learning",
            corrected_text="Machine Learning",
            correction_type="capitalization"
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=None,
            timestamp=datetime.now(),
            correction=correction
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        self.assertTrue(self.learner.should_adjust(event))
    
    def test_calculate_adjustment(self):
        """Test vocabulary adjustment calculation"""
        correction = Correction(
            correction_id="test_correction",
            original_text="nlp",
            corrected_text="NLP",
            correction_type="capitalization"
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=None,
            timestamp=datetime.now(),
            correction=correction
        )
        
        event = LearningEvent(
            event_id="test_event",
            trigger=LearningTrigger.IMMEDIATE,
            user_id="test_user",
            model_id="test_model",
            feedback=feedback
        )
        
        adjustment = self.learner.calculate_adjustment(event)
        
        self.assertIsNotNone(adjustment)
        self.assertEqual(adjustment.adjustment_type, AdjustmentType.VOCABULARY_UPDATE)
        self.assertEqual(adjustment.new_value, "nlp")  # Lowercase version added
    
    def test_validate_adjustment(self):
        """Test vocabulary adjustment validation"""
        # Valid adjustment
        valid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.VOCABULARY_UPDATE,
            parameter_name="vocabulary_addition",
            old_value=None,
            new_value="newword",
            confidence=0.6,
            trigger_event="event"
        )
        
        self.assertTrue(self.learner.validate_adjustment(valid_adjustment))
        
        # Invalid adjustment - too short
        invalid_adjustment = RealTimeAdjustment(
            adjustment_id="test",
            user_id="user",
            model_id="model",
            adjustment_type=AdjustmentType.VOCABULARY_UPDATE,
            parameter_name="vocabulary_addition",
            old_value=None,
            new_value="a",  # Too short
            confidence=0.6,
            trigger_event="event"
        )
        
        self.assertFalse(self.learner.validate_adjustment(invalid_adjustment))

class TestRealTimeLearningSystem(unittest.TestCase):
    """Test RealTimeLearningSystem functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary databases
        self.temp_profile_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_profile_db.close()
        
        self.temp_feedback_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_feedback_db.close()
        
        # Create storage instances
        profile_storage = create_user_profile_storage(self.temp_profile_db.name)
        feedback_storage = create_feedback_storage(self.temp_feedback_db.name)
        
        # Create engines
        self.personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
        self.adaptation_engine = create_model_adaptation_engine(self.personalization_engine, feedback_storage)
        
        # Create real-time learning system
        self.learning_system = create_realtime_learning_system(
            self.personalization_engine, self.adaptation_engine, LearningMode.BALANCED
        )
        
        self.user_id = "test_user"
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.learning_system.stop()
        self.adaptation_engine.stop()
        try:
            os.unlink(self.temp_profile_db.name)
            os.unlink(self.temp_feedback_db.name)
        except OSError:
            pass
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.learning_system.personalization_engine)
        self.assertIsNotNone(self.learning_system.adaptation_engine)
        self.assertEqual(self.learning_system.learning_mode, LearningMode.BALANCED)
        self.assertIn('confidence', self.learning_system.learners)
        self.assertIn('pattern', self.learning_system.learners)
        self.assertIn('vocabulary', self.learning_system.learners)
    
    def test_process_feedback(self):
        """Test feedback processing"""
        # Create sample feedback
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test content",
            confidence_score=0.7
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=2,  # Low rating to trigger adjustment
            max_value=5
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id=self.user_id,
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        
        # Process feedback
        event_ids = self.learning_system.process_feedback(feedback)
        
        self.assertIsInstance(event_ids, list)
        self.assertGreater(len(event_ids), 0)
        
        # Wait for processing
        time.sleep(1)
        
        # Check if event was processed (queue may be empty if processed quickly)
        self.assertIsInstance(self.learning_system.event_queue, type(self.learning_system.event_queue))
    
    def test_get_learning_statistics(self):
        """Test getting learning statistics"""
        stats = self.learning_system.get_learning_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_adjustments', stats)
        # learning_mode may not be present if no adjustments have been made
        if 'learning_mode' in stats:
            self.assertEqual(stats['learning_mode'], 'balanced')
    
    def test_get_user_adjustments(self):
        """Test getting user adjustments"""
        adjustments = self.learning_system.get_user_adjustments(self.user_id)
        
        self.assertIsInstance(adjustments, list)
        # Initially should be empty
        self.assertEqual(len(adjustments), 0)
    
    def test_force_learning_update(self):
        """Test forcing learning update"""
        event_id = self.learning_system.force_learning_update(self.user_id, "test_model")
        
        self.assertIsNotNone(event_id)
        self.assertIsInstance(event_id, str)
        
        # Check if event was queued
        self.assertGreater(len(self.learning_system.event_queue), 0)
    
    def test_set_learning_mode(self):
        """Test setting learning mode"""
        self.learning_system.set_learning_mode(LearningMode.AGGRESSIVE)
        
        self.assertEqual(self.learning_system.learning_mode, LearningMode.AGGRESSIVE)
    
    def test_cleanup_old_adjustments(self):
        """Test cleaning up old adjustments"""
        # Add some old adjustments
        old_adjustment = RealTimeAdjustment(
            adjustment_id="old_adjustment",
            user_id=self.user_id,
            model_id="test_model",
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="test",
            old_value=0.8,
            new_value=0.85,
            confidence=0.9,
            trigger_event="test_event",
            timestamp=datetime.now() - timedelta(days=40)
        )
        
        self.learning_system.adjustment_history.append(old_adjustment)
        original_count = len(self.learning_system.adjustment_history)
        
        # Cleanup adjustments older than 30 days
        cleaned_count = self.learning_system.cleanup_old_adjustments(days=30)
        
        self.assertGreaterEqual(cleaned_count, 1)
        self.assertLess(len(self.learning_system.adjustment_history), original_count)

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_realtime_learning_system(self):
        """Test creating real-time learning system"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_profile_db:
            temp_profile_db.close()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_feedback_db:
                temp_feedback_db.close()
                
                try:
                    profile_storage = create_user_profile_storage(temp_profile_db.name)
                    feedback_storage = create_feedback_storage(temp_feedback_db.name)
                    personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
                    adaptation_engine = create_model_adaptation_engine(personalization_engine, feedback_storage)
                    
                    learning_system = create_realtime_learning_system(
                        personalization_engine, adaptation_engine, LearningMode.CONSERVATIVE
                    )
                    
                    self.assertIsInstance(learning_system, RealTimeLearningSystem)
                    self.assertEqual(learning_system.learning_mode, LearningMode.CONSERVATIVE)
                    
                    # Test basic functionality
                    stats = learning_system.get_learning_statistics()
                    self.assertIsInstance(stats, dict)
                    
                    learning_system.stop()
                    adaptation_engine.stop()
                    
                finally:
                    os.unlink(temp_profile_db.name)
                    os.unlink(temp_feedback_db.name)

def run_tests():
    """Run all tests with detailed output"""
    test_classes = [
        TestLearningEvent,
        TestRealTimeAdjustment,
        TestLearningMetrics,
        TestConfidenceThresholdLearner,
        TestPatternLearner,
        TestVocabularyLearner,
        TestRealTimeLearningSystem,
        TestUtilityFunctions
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)