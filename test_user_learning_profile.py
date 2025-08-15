#!/usr/bin/env python3
"""
Test Suite for User Learning Profile System
Comprehensive tests for user profile management, personalization, and learning capabilities
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from user_learning_profile import (
    UserLearningProfile, UserProfileStorage, PersonalizationEngine,
    ModelPreference, DomainExpertise, LearningGoal, CorrectionPattern,
    QualityThreshold, FeedbackHistory, create_user_profile_storage,
    create_personalization_engine
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class TestUserLearningProfile(unittest.TestCase):
    """Test UserLearningProfile data model"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user_123"
        self.profile = UserLearningProfile(user_id=self.user_id)
    
    def test_profile_creation(self):
        """Test basic profile creation"""
        self.assertEqual(self.profile.user_id, self.user_id)
        self.assertIsNotNone(self.profile.profile_id)
        self.assertEqual(self.profile.model_preference_type, ModelPreference.BALANCED)
        self.assertEqual(self.profile.domain_expertise, [DomainExpertise.GENERAL])
        self.assertTrue(self.profile.auto_apply_corrections)
    
    def test_profile_serialization(self):
        """Test profile to_dict and from_dict methods"""
        # Add some data to the profile
        self.profile.preferred_models = ["spacy_md", "bert_base"]
        self.profile.model_preference_type = ModelPreference.ACCURACY_OPTIMIZED
        self.profile.domain_expertise = [DomainExpertise.TECHNICAL, DomainExpertise.BUSINESS]
        
        # Add correction pattern
        pattern = CorrectionPattern(
            pattern_id="test_pattern",
            pattern_type="capitalization",
            original_pattern="ai",
            corrected_pattern="AI",
            frequency=5,
            confidence=0.8
        )
        self.profile.correction_patterns.append(pattern)
        
        # Add quality threshold
        threshold = QualityThreshold(
            content_type=ContentType.TRANSCRIPTION,
            minimum_confidence=0.7,
            preferred_confidence=0.9,
            acceptable_error_rate=0.1
        )
        self.profile.quality_thresholds.append(threshold)
        
        # Test serialization
        profile_dict = self.profile.to_dict()
        self.assertIsInstance(profile_dict, dict)
        self.assertEqual(profile_dict['user_id'], self.user_id)
        self.assertEqual(profile_dict['preferred_models'], ["spacy_md", "bert_base"])
        self.assertEqual(profile_dict['model_preference_type'], 'accuracy_optimized')
        
        # Test deserialization
        restored_profile = UserLearningProfile.from_dict(profile_dict)
        self.assertEqual(restored_profile.user_id, self.user_id)
        self.assertEqual(restored_profile.preferred_models, ["spacy_md", "bert_base"])
        self.assertEqual(restored_profile.model_preference_type, ModelPreference.ACCURACY_OPTIMIZED)
        self.assertEqual(len(restored_profile.correction_patterns), 1)
        self.assertEqual(len(restored_profile.quality_thresholds), 1)

class TestCorrectionPattern(unittest.TestCase):
    """Test CorrectionPattern data model"""
    
    def test_pattern_creation(self):
        """Test correction pattern creation"""
        pattern = CorrectionPattern(
            pattern_id="test_pattern",
            pattern_type="word_replacement",
            original_pattern="machine learning",
            corrected_pattern="Machine Learning",
            frequency=3,
            confidence=0.6
        )
        
        self.assertEqual(pattern.pattern_id, "test_pattern")
        self.assertEqual(pattern.pattern_type, "word_replacement")
        self.assertEqual(pattern.frequency, 3)
        self.assertEqual(pattern.confidence, 0.6)
    
    def test_pattern_serialization(self):
        """Test pattern serialization"""
        pattern = CorrectionPattern(
            pattern_id="test_pattern",
            pattern_type="punctuation",
            original_pattern="hello world",
            corrected_pattern="hello, world",
            frequency=2,
            confidence=0.4,
            context_tags=["greeting", "punctuation"]
        )
        
        pattern_dict = pattern.to_dict()
        self.assertIsInstance(pattern_dict, dict)
        self.assertEqual(pattern_dict['pattern_type'], "punctuation")
        self.assertEqual(pattern_dict['context_tags'], ["greeting", "punctuation"])
        
        restored_pattern = CorrectionPattern.from_dict(pattern_dict)
        self.assertEqual(restored_pattern.pattern_id, "test_pattern")
        self.assertEqual(restored_pattern.context_tags, ["greeting", "punctuation"])

class TestUserProfileStorage(unittest.TestCase):
    """Test UserProfileStorage functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = UserProfileStorage(self.temp_db.name)
        
        self.user_id = "test_user_456"
        self.profile = UserLearningProfile(user_id=self.user_id)
        self.profile.preferred_models = ["spacy_lg"]
        self.profile.model_preference_type = ModelPreference.SPEED_OPTIMIZED
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except OSError:
            pass
    
    def test_store_and_retrieve_profile(self):
        """Test storing and retrieving profiles"""
        # Store profile
        success = self.storage.store_profile(self.profile)
        self.assertTrue(success)
        
        # Retrieve profile
        retrieved_profile = self.storage.retrieve_profile(self.user_id)
        self.assertIsNotNone(retrieved_profile)
        self.assertEqual(retrieved_profile.user_id, self.user_id)
        self.assertEqual(retrieved_profile.preferred_models, ["spacy_lg"])
        self.assertEqual(retrieved_profile.model_preference_type, ModelPreference.SPEED_OPTIMIZED)
    
    def test_retrieve_nonexistent_profile(self):
        """Test retrieving non-existent profile"""
        profile = self.storage.retrieve_profile("nonexistent_user")
        self.assertIsNone(profile)
    
    def test_update_profile(self):
        """Test updating existing profile"""
        # Store initial profile
        self.storage.store_profile(self.profile)
        
        # Update profile
        self.profile.preferred_models = ["bert_large"]
        self.profile.model_preference_type = ModelPreference.ACCURACY_OPTIMIZED
        
        success = self.storage.store_profile(self.profile)
        self.assertTrue(success)
        
        # Retrieve updated profile
        updated_profile = self.storage.retrieve_profile(self.user_id)
        self.assertEqual(updated_profile.preferred_models, ["bert_large"])
        self.assertEqual(updated_profile.model_preference_type, ModelPreference.ACCURACY_OPTIMIZED)
    
    def test_delete_profile(self):
        """Test deleting profile"""
        # Store profile
        self.storage.store_profile(self.profile)
        
        # Verify it exists
        retrieved_profile = self.storage.retrieve_profile(self.user_id)
        self.assertIsNotNone(retrieved_profile)
        
        # Delete profile
        success = self.storage.delete_profile(self.user_id)
        self.assertTrue(success)
        
        # Verify it's gone
        deleted_profile = self.storage.retrieve_profile(self.user_id)
        self.assertIsNone(deleted_profile)
    
    def test_list_profiles(self):
        """Test listing profiles"""
        # Store multiple profiles
        profiles = []
        for i in range(5):
            profile = UserLearningProfile(user_id=f"user_{i}")
            profiles.append(profile)
            self.storage.store_profile(profile)
        
        # List profiles
        profile_list = self.storage.list_profiles(limit=3)
        self.assertEqual(len(profile_list), 3)
        
        # Check structure
        for profile_info in profile_list:
            self.assertIn('user_id', profile_info)
            self.assertIn('profile_id', profile_info)
            self.assertIn('created_at', profile_info)
    
    def test_profile_statistics(self):
        """Test profile statistics"""
        # Store some profiles
        for i in range(3):
            profile = UserLearningProfile(user_id=f"stats_user_{i}")
            self.storage.store_profile(profile)
        
        stats = self.storage.get_profile_statistics()
        self.assertIsInstance(stats, dict)
        self.assertGreaterEqual(stats.get('total_profiles', 0), 3)

class TestPersonalizationEngine(unittest.TestCase):
    """Test PersonalizationEngine functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary databases
        self.temp_profile_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_profile_db.close()
        
        self.temp_feedback_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_feedback_db.close()
        
        # Create storage instances
        self.profile_storage = UserProfileStorage(self.temp_profile_db.name)
        self.feedback_storage = create_feedback_storage(self.temp_feedback_db.name)
        
        # Create personalization engine
        self.engine = PersonalizationEngine(self.profile_storage, self.feedback_storage)
        
        self.user_id = "test_user_789"
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_profile_db.name)
            os.unlink(self.temp_feedback_db.name)
        except OSError:
            pass
    
    def test_get_or_create_profile(self):
        """Test getting or creating user profile"""
        # First call should create new profile
        profile = self.engine.get_or_create_profile(self.user_id)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user_id, self.user_id)
        self.assertEqual(len(profile.quality_thresholds), 4)  # Default thresholds
        
        # Second call should retrieve existing profile
        profile2 = self.engine.get_or_create_profile(self.user_id)
        self.assertEqual(profile.profile_id, profile2.profile_id)
    
    def test_update_profile_from_feedback(self):
        """Test updating profile from feedback"""
        # Create feedback with rating
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test content",
            confidence_score=0.85
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=4,
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
        
        # Update profile from feedback
        success = self.engine.update_profile_from_feedback(self.user_id, feedback)
        self.assertTrue(success)
        
        # Verify profile was updated
        profile = self.engine.get_or_create_profile(self.user_id)
        self.assertEqual(profile.feedback_history.total_feedback_count, 1)
        self.assertGreater(profile.feedback_history.average_rating, 0)
    
    def test_update_profile_with_correction(self):
        """Test updating profile with correction feedback"""
        # Create feedback with correction
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test content"
        )
        
        correction = Correction(
            correction_id="test_correction",
            original_text="ai",
            corrected_text="AI",
            correction_type="capitalization"
        )
        
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id=self.user_id,
            feedback_type=FeedbackType.CORRECTION,
            context=context,
            timestamp=datetime.now(),
            correction=correction
        )
        
        # Update profile from feedback
        success = self.engine.update_profile_from_feedback(self.user_id, feedback)
        self.assertTrue(success)
        
        # Verify correction pattern was added
        profile = self.engine.get_or_create_profile(self.user_id)
        self.assertEqual(profile.feedback_history.correction_count, 1)
        self.assertEqual(len(profile.correction_patterns), 1)
        self.assertEqual(profile.correction_patterns[0].pattern_type, "capitalization")
    
    def test_recommend_model_selection(self):
        """Test model selection recommendations"""
        # Create profile with preferences
        profile = self.engine.get_or_create_profile(self.user_id)
        profile.model_preference_type = ModelPreference.ACCURACY_OPTIMIZED
        profile.preferred_models = ["custom_model"]
        self.profile_storage.store_profile(profile)
        
        # Get recommendations
        recommendations = self.engine.recommend_model_selection(
            self.user_id, ContentType.TRANSCRIPTION, content_complexity=0.8
        )
        
        self.assertIsInstance(recommendations, dict)
        self.assertIn('recommended_models', recommendations)
        self.assertIn('priority', recommendations)
        self.assertEqual(recommendations['priority'], 'accuracy')
        self.assertIn('custom_model', recommendations['recommended_models'])
    
    def test_get_personalized_settings(self):
        """Test getting personalized settings"""
        settings = self.engine.get_personalized_settings(self.user_id)
        
        self.assertIsInstance(settings, dict)
        self.assertIn('auto_apply_corrections', settings)
        self.assertIn('feedback_frequency', settings)
        self.assertIn('domain_expertise', settings)
        self.assertIn('learning_goals', settings)
    
    def test_update_user_preferences(self):
        """Test updating user preferences"""
        preferences = {
            'model_preference_type': 'speed_optimized',
            'preferred_models': ['spacy_sm', 'distilbert'],
            'domain_expertise': ['technical', 'business'],
            'learning_goals': ['speed_improvement'],
            'auto_apply_corrections': False,
            'feedback_frequency_preference': 'high'
        }
        
        success = self.engine.update_user_preferences(self.user_id, preferences)
        self.assertTrue(success)
        
        # Verify preferences were updated
        profile = self.engine.get_or_create_profile(self.user_id)
        self.assertEqual(profile.model_preference_type, ModelPreference.SPEED_OPTIMIZED)
        self.assertEqual(profile.preferred_models, ['spacy_sm', 'distilbert'])
        self.assertIn(DomainExpertise.TECHNICAL, profile.domain_expertise)
        self.assertIn(DomainExpertise.BUSINESS, profile.domain_expertise)
        self.assertFalse(profile.auto_apply_corrections)
        self.assertEqual(profile.feedback_frequency_preference, 'high')
    
    def test_analyze_user_patterns(self):
        """Test user pattern analysis"""
        # Create profile with some data
        profile = self.engine.get_or_create_profile(self.user_id)
        
        # Add correction patterns
        pattern1 = CorrectionPattern(
            pattern_id="pattern1",
            pattern_type="capitalization",
            original_pattern="ai",
            corrected_pattern="AI",
            frequency=5,
            confidence=0.8
        )
        pattern2 = CorrectionPattern(
            pattern_id="pattern2",
            pattern_type="punctuation",
            original_pattern="hello world",
            corrected_pattern="hello, world",
            frequency=3,
            confidence=0.6
        )
        profile.correction_patterns = [pattern1, pattern2]
        
        # Update feedback history
        profile.feedback_history.total_feedback_count = 20
        profile.feedback_history.correction_count = 8
        profile.feedback_history.average_rating = 0.75
        
        self.profile_storage.store_profile(profile)
        
        # Analyze patterns
        analysis = self.engine.analyze_user_patterns(self.user_id)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('pattern_analysis', analysis)
        self.assertIn('feedback_analysis', analysis)
        self.assertIn('recommendations', analysis)
        self.assertIn('learning_progress', analysis)
        
        # Check pattern analysis
        pattern_analysis = analysis['pattern_analysis']
        self.assertEqual(pattern_analysis['total_patterns'], 2)
        self.assertIn('capitalization', pattern_analysis['pattern_types'])
        self.assertIn('punctuation', pattern_analysis['pattern_types'])
    
    def test_model_recommendation_speed_optimized(self):
        """Test model recommendations for speed-optimized preference"""
        # Set speed-optimized preference
        preferences = {'model_preference_type': 'speed_optimized'}
        self.engine.update_user_preferences(self.user_id, preferences)
        
        recommendations = self.engine.recommend_model_selection(
            self.user_id, ContentType.TRANSCRIPTION, content_complexity=0.3
        )
        
        self.assertEqual(recommendations['priority'], 'speed')
        self.assertIn('spacy_sm', recommendations['recommended_models'])
    
    def test_model_recommendation_accuracy_optimized(self):
        """Test model recommendations for accuracy-optimized preference"""
        # Set accuracy-optimized preference
        preferences = {'model_preference_type': 'accuracy_optimized'}
        self.engine.update_user_preferences(self.user_id, preferences)
        
        recommendations = self.engine.recommend_model_selection(
            self.user_id, ContentType.TRANSCRIPTION, content_complexity=0.8
        )
        
        self.assertEqual(recommendations['priority'], 'accuracy')
        self.assertIn('spacy_lg', recommendations['recommended_models'])

class TestFeedbackHistory(unittest.TestCase):
    """Test FeedbackHistory functionality"""
    
    def test_feedback_history_serialization(self):
        """Test feedback history serialization"""
        history = FeedbackHistory(
            total_feedback_count=10,
            rating_distribution={'stars_4': 5, 'stars_5': 3, 'stars_3': 2},
            correction_count=3,
            suggestion_count=1,
            average_rating=0.8,
            most_common_corrections=['capitalization', 'punctuation'],
            feedback_frequency=2.5,
            last_feedback_date=datetime.now()
        )
        
        history_dict = history.to_dict()
        self.assertIsInstance(history_dict, dict)
        self.assertEqual(history_dict['total_feedback_count'], 10)
        self.assertEqual(history_dict['correction_count'], 3)
        
        restored_history = FeedbackHistory.from_dict(history_dict)
        self.assertEqual(restored_history.total_feedback_count, 10)
        self.assertEqual(restored_history.correction_count, 3)
        self.assertIsInstance(restored_history.last_feedback_date, datetime)

class TestQualityThreshold(unittest.TestCase):
    """Test QualityThreshold functionality"""
    
    def test_quality_threshold_creation(self):
        """Test quality threshold creation"""
        threshold = QualityThreshold(
            content_type=ContentType.TRANSCRIPTION,
            minimum_confidence=0.7,
            preferred_confidence=0.9,
            acceptable_error_rate=0.1
        )
        
        self.assertEqual(threshold.content_type, ContentType.TRANSCRIPTION)
        self.assertEqual(threshold.minimum_confidence, 0.7)
        self.assertEqual(threshold.preferred_confidence, 0.9)
        self.assertEqual(threshold.acceptable_error_rate, 0.1)
    
    def test_quality_threshold_serialization(self):
        """Test quality threshold serialization"""
        threshold = QualityThreshold(
            content_type=ContentType.MOM_DOCUMENT,
            minimum_confidence=0.8,
            preferred_confidence=0.95,
            acceptable_error_rate=0.05
        )
        
        threshold_dict = threshold.to_dict()
        self.assertEqual(threshold_dict['content_type'], 'mom_document')
        self.assertEqual(threshold_dict['minimum_confidence'], 0.8)
        
        restored_threshold = QualityThreshold.from_dict(threshold_dict)
        self.assertEqual(restored_threshold.content_type, ContentType.MOM_DOCUMENT)
        self.assertEqual(restored_threshold.minimum_confidence, 0.8)

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_user_profile_storage(self):
        """Test creating user profile storage"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
            temp_db.close()
            
            try:
                storage = create_user_profile_storage(temp_db.name)
                self.assertIsInstance(storage, UserProfileStorage)
                
                # Test that database is initialized
                profile = UserLearningProfile(user_id="test_user")
                success = storage.store_profile(profile)
                self.assertTrue(success)
                
            finally:
                os.unlink(temp_db.name)
    
    def test_create_personalization_engine(self):
        """Test creating personalization engine"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_profile_db:
            temp_profile_db.close()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_feedback_db:
                temp_feedback_db.close()
                
                try:
                    profile_storage = create_user_profile_storage(temp_profile_db.name)
                    feedback_storage = create_feedback_storage(temp_feedback_db.name)
                    
                    engine = create_personalization_engine(profile_storage, feedback_storage)
                    self.assertIsInstance(engine, PersonalizationEngine)
                    
                    # Test basic functionality
                    profile = engine.get_or_create_profile("test_user")
                    self.assertIsNotNone(profile)
                    
                finally:
                    os.unlink(temp_profile_db.name)
                    os.unlink(temp_feedback_db.name)

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_profile_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_profile_db.close()
        
        self.temp_feedback_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_feedback_db.close()
        
        self.profile_storage = UserProfileStorage(self.temp_profile_db.name)
        self.feedback_storage = create_feedback_storage(self.temp_feedback_db.name)
        self.engine = PersonalizationEngine(self.profile_storage, self.feedback_storage)
        
        self.user_id = "integration_user"
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        try:
            os.unlink(self.temp_profile_db.name)
            os.unlink(self.temp_feedback_db.name)
        except OSError:
            pass
    
    def test_complete_user_journey(self):
        """Test complete user journey from profile creation to personalization"""
        # 1. Create new user profile
        profile = self.engine.get_or_create_profile(self.user_id)
        self.assertIsNotNone(profile)
        
        # 2. User provides initial preferences
        preferences = {
            'model_preference_type': 'accuracy_optimized',
            'domain_expertise': ['technical'],
            'learning_goals': ['accuracy_improvement'],
            'auto_apply_corrections': True
        }
        success = self.engine.update_user_preferences(self.user_id, preferences)
        self.assertTrue(success)
        
        # 3. User provides feedback with corrections
        for i in range(5):
            context = FeedbackContext(
                content_type=ContentType.TRANSCRIPTION,
                content_id=f"content_{i}",
                original_content=f"test content {i}",
                confidence_score=0.8 + i * 0.02
            )
            
            correction = Correction(
                correction_id=f"correction_{i}",
                original_text="ai",
                corrected_text="AI",
                correction_type="capitalization"
            )
            
            feedback = Feedback(
                feedback_id=f"feedback_{i}",
                user_id=self.user_id,
                feedback_type=FeedbackType.CORRECTION,
                context=context,
                timestamp=datetime.now(),
                correction=correction
            )
            
            self.engine.update_profile_from_feedback(self.user_id, feedback)
        
        # 4. Get personalized recommendations
        recommendations = self.engine.recommend_model_selection(
            self.user_id, ContentType.TRANSCRIPTION, content_complexity=0.7
        )
        
        self.assertEqual(recommendations['priority'], 'accuracy')
        self.assertIsInstance(recommendations['recommended_models'], list)
        
        # 5. Analyze user patterns
        analysis = self.engine.analyze_user_patterns(self.user_id)
        
        self.assertEqual(analysis['pattern_analysis']['total_patterns'], 1)
        self.assertEqual(analysis['feedback_analysis']['correction_ratio'], 1.0)
        self.assertIn('recommendations', analysis)
        
        # 6. Get personalized settings
        settings = self.engine.get_personalized_settings(self.user_id)
        
        self.assertTrue(settings['auto_apply_corrections'])
        self.assertIn('technical', settings['domain_expertise'])
        self.assertEqual(settings['total_feedback'], 5)

def run_tests():
    """Run all tests with detailed output"""
    # Create test suite
    test_classes = [
        TestUserLearningProfile,
        TestCorrectionPattern,
        TestUserProfileStorage,
        TestPersonalizationEngine,
        TestFeedbackHistory,
        TestQualityThreshold,
        TestUtilityFunctions,
        TestIntegrationScenarios
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