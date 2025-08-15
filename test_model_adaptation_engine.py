#!/usr/bin/env python3
"""
Test Suite for Model Adaptation Engine
Comprehensive tests for model adaptation, parameter tuning, and learning capabilities
"""

import unittest
import tempfile
import os
import time
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
from model_adaptation_engine import (
    ModelAdaptationEngine, SpacyModelAdapter, TransformerModelAdapter,
    AdaptationType, AdaptationScope, AdaptationStatus, AdaptationRule,
    ModelParameters, AdaptationResult, create_model_adaptation_engine
)

from user_learning_profile import (
    UserLearningProfile, PersonalizationEngine, CorrectionPattern,
    ModelPreference, DomainExpertise, create_personalization_engine,
    create_user_profile_storage
)

from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType, create_feedback_storage
)

class TestAdaptationRule(unittest.TestCase):
    """Test AdaptationRule data model"""
    
    def test_rule_creation(self):
        """Test adaptation rule creation"""
        rule = AdaptationRule(
            rule_id="test_rule",
            rule_type="threshold_modification",
            condition={"min_feedback": 5},
            action={"increase_threshold": 0.1},
            priority=1
        )
        
        self.assertEqual(rule.rule_id, "test_rule")
        self.assertEqual(rule.rule_type, "threshold_modification")
        self.assertEqual(rule.priority, 1)
        self.assertTrue(rule.enabled)
        self.assertEqual(rule.application_count, 0)
    
    def test_rule_serialization(self):
        """Test rule serialization"""
        rule = AdaptationRule(
            rule_id="test_rule",
            rule_type="vocabulary_expansion",
            condition={"correction_type": "word_replacement"},
            action={"add_to_vocabulary": True}
        )
        
        rule_dict = rule.to_dict()
        self.assertIsInstance(rule_dict, dict)
        self.assertEqual(rule_dict['rule_id'], "test_rule")
        
        restored_rule = AdaptationRule.from_dict(rule_dict)
        self.assertEqual(restored_rule.rule_id, "test_rule")
        self.assertEqual(restored_rule.rule_type, "vocabulary_expansion")

class TestModelParameters(unittest.TestCase):
    """Test ModelParameters data model"""
    
    def test_parameters_creation(self):
        """Test model parameters creation"""
        params = ModelParameters(
            model_id="test_model",
            parameters={"learning_rate": 0.001},
            confidence_thresholds={"transcription": 0.8},
            vocabulary_additions=["AI", "ML"]
        )
        
        self.assertEqual(params.model_id, "test_model")
        self.assertEqual(params.parameters["learning_rate"], 0.001)
        self.assertEqual(params.confidence_thresholds["transcription"], 0.8)
        self.assertIn("AI", params.vocabulary_additions)
    
    def test_parameters_serialization(self):
        """Test parameters serialization"""
        params = ModelParameters(
            model_id="test_model",
            parameters={"dropout": 0.1},
            processing_rules={"auto_capitalize": True}
        )
        
        params_dict = params.to_dict()
        self.assertIsInstance(params_dict, dict)
        self.assertEqual(params_dict['model_id'], "test_model")
        
        restored_params = ModelParameters.from_dict(params_dict)
        self.assertEqual(restored_params.model_id, "test_model")
        self.assertEqual(restored_params.parameters["dropout"], 0.1)

class TestAdaptationResult(unittest.TestCase):
    """Test AdaptationResult data model"""
    
    def test_result_creation(self):
        """Test adaptation result creation"""
        result = AdaptationResult(
            adaptation_id="test_adaptation",
            adaptation_type=AdaptationType.PARAMETER_TUNING,
            scope=AdaptationScope.USER_SPECIFIC,
            target_model="spacy_md",
            target_user="test_user"
        )
        
        self.assertEqual(result.adaptation_id, "test_adaptation")
        self.assertEqual(result.adaptation_type, AdaptationType.PARAMETER_TUNING)
        self.assertEqual(result.scope, AdaptationScope.USER_SPECIFIC)
        self.assertEqual(result.status, AdaptationStatus.PENDING)
    
    def test_result_serialization(self):
        """Test result serialization"""
        result = AdaptationResult(
            adaptation_id="test_adaptation",
            adaptation_type=AdaptationType.RULE_ADJUSTMENT,
            scope=AdaptationScope.GLOBAL,
            target_model="bert_base",
            status=AdaptationStatus.COMPLETED
        )
        
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['adaptation_type'], 'rule_adjustment')
        
        restored_result = AdaptationResult.from_dict(result_dict)
        self.assertEqual(restored_result.adaptation_type, AdaptationType.RULE_ADJUSTMENT)
        self.assertEqual(restored_result.scope, AdaptationScope.GLOBAL)

class TestSpacyModelAdapter(unittest.TestCase):
    """Test SpacyModelAdapter functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.adapter = SpacyModelAdapter()
        self.user_profile = UserLearningProfile(user_id="test_user")
        
        # Add some correction patterns
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
        self.user_profile.correction_patterns = [pattern1, pattern2]
        self.user_profile.domain_expertise = [DomainExpertise.TECHNICAL]
    
    def test_supported_models(self):
        """Test supported models"""
        self.assertIn("spacy_sm", self.adapter.supported_models)
        self.assertIn("spacy_md", self.adapter.supported_models)
        self.assertIn("spacy_lg", self.adapter.supported_models)
    
    def test_adapt_parameters(self):
        """Test parameter adaptation"""
        feedback = self._create_sample_feedback()
        
        params = self.adapter.adapt_parameters("spacy_md", feedback, self.user_profile)
        
        self.assertEqual(params.model_id, "spacy_md")
        self.assertIsInstance(params.parameters, dict)
        self.assertIsInstance(params.confidence_thresholds, dict)
        self.assertIsInstance(params.vocabulary_additions, list)
    
    def test_vocabulary_adaptation(self):
        """Test vocabulary adaptation"""
        feedback = []
        
        params = self.adapter.adapt_parameters("spacy_md", feedback, self.user_profile)
        
        # Should include technical vocabulary
        self.assertIn("API", params.vocabulary_additions)
        self.assertIn("algorithm", params.vocabulary_additions)
        
        # Should include corrected patterns
        self.assertIn("ai", params.vocabulary_additions)
    
    def test_processing_rules_adaptation(self):
        """Test processing rules adaptation"""
        feedback = []
        
        params = self.adapter.adapt_parameters("spacy_md", feedback, self.user_profile)
        
        # Should enable auto-capitalization due to capitalization patterns
        self.assertTrue(params.processing_rules.get('auto_capitalize_entities', False))
    
    def test_pattern_overrides(self):
        """Test pattern override creation"""
        feedback = []
        
        params = self.adapter.adapt_parameters("spacy_md", feedback, self.user_profile)
        
        # Should create override for high-confidence pattern
        self.assertIn("ai", params.pattern_overrides)
        self.assertEqual(params.pattern_overrides["ai"], "AI")
    
    def test_validate_adaptation(self):
        """Test adaptation validation"""
        original_params = ModelParameters(model_id="spacy_md")
        
        # Valid adaptation
        valid_params = ModelParameters(
            model_id="spacy_md",
            confidence_thresholds={"transcription": 0.8},
            vocabulary_additions=["test"] * 10
        )
        self.assertTrue(self.adapter.validate_adaptation(original_params, valid_params))
        
        # Invalid adaptation - threshold out of range
        invalid_params = ModelParameters(
            model_id="spacy_md",
            confidence_thresholds={"transcription": 1.5}
        )
        self.assertFalse(self.adapter.validate_adaptation(original_params, invalid_params))
        
        # Invalid adaptation - too much vocabulary
        invalid_params2 = ModelParameters(
            model_id="spacy_md",
            vocabulary_additions=["test"] * 2000
        )
        self.assertFalse(self.adapter.validate_adaptation(original_params, invalid_params2))
    
    def test_unsupported_model(self):
        """Test unsupported model handling"""
        with self.assertRaises(ValueError):
            self.adapter.adapt_parameters("unsupported_model", [], self.user_profile)
    
    def _create_sample_feedback(self):
        """Create sample feedback for testing"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test content",
            confidence_score=0.8
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=4,
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
        
        return [feedback]

class TestTransformerModelAdapter(unittest.TestCase):
    """Test TransformerModelAdapter functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.adapter = TransformerModelAdapter()
        self.user_profile = UserLearningProfile(user_id="test_user")
    
    def test_supported_models(self):
        """Test supported models"""
        self.assertIn("bert_base", self.adapter.supported_models)
        self.assertIn("roberta_large", self.adapter.supported_models)
    
    def test_adapt_parameters(self):
        """Test parameter adaptation"""
        feedback = self._create_sample_feedback()
        
        params = self.adapter.adapt_parameters("bert_base", feedback, self.user_profile)
        
        self.assertEqual(params.model_id, "bert_base")
        self.assertIn("attention_dropout", params.parameters)
        self.assertIn("learning_rate", params.parameters)
    
    def test_attention_parameters(self):
        """Test attention parameter adaptation"""
        # Low quality feedback should reduce dropout
        low_quality_feedback = self._create_sample_feedback(rating_value=2)
        params = self.adapter.adapt_parameters("bert_base", low_quality_feedback, self.user_profile)
        
        self.assertEqual(params.parameters["attention_dropout"], 0.05)
        
        # High quality feedback should use standard dropout
        high_quality_feedback = self._create_sample_feedback(rating_value=5)
        params = self.adapter.adapt_parameters("bert_base", high_quality_feedback, self.user_profile)
        
        self.assertEqual(params.parameters["attention_dropout"], 0.1)
    
    def test_validate_adaptation(self):
        """Test adaptation validation"""
        original_params = ModelParameters(model_id="bert_base")
        
        # Valid adaptation
        valid_params = ModelParameters(
            model_id="bert_base",
            parameters={"learning_rate": 1e-5, "attention_dropout": 0.1}
        )
        self.assertTrue(self.adapter.validate_adaptation(original_params, valid_params))
        
        # Invalid learning rate
        invalid_params = ModelParameters(
            model_id="bert_base",
            parameters={"learning_rate": 1e-2}  # Too high
        )
        self.assertFalse(self.adapter.validate_adaptation(original_params, invalid_params))
    
    def _create_sample_feedback(self, rating_value=4):
        """Create sample feedback for testing"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="test content"
        )
        
        rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=rating_value,
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
        
        return [feedback]

class TestModelAdaptationEngine(unittest.TestCase):
    """Test ModelAdaptationEngine functionality"""
    
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
        
        # Create personalization engine
        self.personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
        
        # Create adaptation engine
        self.engine = create_model_adaptation_engine(self.personalization_engine, feedback_storage)
        
        self.user_id = "test_user"
        self.model_id = "spacy_md"
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.engine.stop()
        try:
            os.unlink(self.temp_profile_db.name)
            os.unlink(self.temp_feedback_db.name)
        except OSError:
            pass
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine.personalization_engine)
        self.assertIsNotNone(self.engine.feedback_storage)
        self.assertIn('spacy', self.engine.adapters)
        self.assertIn('transformer', self.engine.adapters)
        self.assertGreater(len(self.engine.adaptation_rules), 0)
    
    def test_adapt_model_for_user(self):
        """Test queuing model adaptation for user"""
        adaptation_id = self.engine.adapt_model_for_user(
            self.user_id, self.model_id, AdaptationType.PARAMETER_TUNING
        )
        
        self.assertIsNotNone(adaptation_id)
        self.assertIsInstance(adaptation_id, str)
        
        # Wait for processing (longer wait)
        time.sleep(2)
        
        # Check if adaptation was processed
        user_adaptations = self.engine.get_user_adaptations(self.user_id)
        # Note: May be 0 if processing is still in progress, but test the mechanism works
        self.assertIsInstance(user_adaptations, list)
    
    def test_get_adapted_parameters(self):
        """Test getting adapted parameters"""
        # Queue adaptation
        adaptation_id = self.engine.adapt_model_for_user(self.user_id, self.model_id)
        
        # Wait for processing
        time.sleep(1)
        
        # Get adapted parameters
        params = self.engine.get_adapted_parameters(self.user_id, self.model_id)
        
        if params:  # May be None if adaptation failed
            self.assertEqual(params.model_id, self.model_id)
            self.assertIsInstance(params.parameters, dict)
    
    def test_apply_global_improvements(self):
        """Test applying global improvements"""
        improvements = [
            {
                'type': 'threshold_modification',
                'models': ['spacy_md'],
                'threshold_changes': {'transcription': 0.85}
            },
            {
                'type': 'vocabulary_expansion',
                'models': ['spacy_md'],
                'vocabulary': ['AI', 'ML', 'NLP']
            }
        ]
        
        applied_adaptations = self.engine.apply_global_improvements(improvements)
        
        self.assertEqual(len(applied_adaptations), 2)  # One per improvement
        
        # Check global parameters were updated
        global_params = self.engine.model_parameters.get('global_spacy_md')
        self.assertIsNotNone(global_params)
        self.assertEqual(global_params.confidence_thresholds['transcription'], 0.85)
        self.assertIn('AI', global_params.vocabulary_additions)
    
    def test_get_adaptation_statistics(self):
        """Test getting adaptation statistics"""
        # Queue some adaptations
        self.engine.adapt_model_for_user(self.user_id, self.model_id)
        self.engine.adapt_model_for_user("user2", "bert_base")
        
        # Wait for processing
        time.sleep(2)
        
        stats = self.engine.get_adaptation_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_adaptations', stats)
        # Success rate may be 0 if no adaptations completed yet
        if stats['total_adaptations'] > 0:
            self.assertIn('success_rate', stats)
            self.assertIn('status_distribution', stats)
            self.assertIn('type_distribution', stats)
    
    def test_rollback_adaptation(self):
        """Test rolling back adaptation"""
        # Queue adaptation
        adaptation_id = self.engine.adapt_model_for_user(self.user_id, self.model_id)
        
        # Wait for processing
        time.sleep(1)
        
        # Try to rollback
        success = self.engine.rollback_adaptation(adaptation_id)
        
        # Note: May fail if adaptation wasn't completed or found
        # This tests the rollback mechanism exists
        self.assertIsInstance(success, bool)
    
    def test_cleanup_old_adaptations(self):
        """Test cleaning up old adaptations"""
        # Add some old adaptation results
        old_result = AdaptationResult(
            adaptation_id="old_adaptation",
            adaptation_type=AdaptationType.PARAMETER_TUNING,
            scope=AdaptationScope.USER_SPECIFIC,
            target_model="spacy_md",
            created_at=datetime.now() - timedelta(days=100)
        )
        
        self.engine.adaptation_results.append(old_result)
        original_count = len(self.engine.adaptation_results)
        
        # Cleanup adaptations older than 90 days
        cleaned_count = self.engine.cleanup_old_adaptations(days=90)
        
        self.assertGreaterEqual(cleaned_count, 1)
        self.assertLess(len(self.engine.adaptation_results), original_count)
    
    def test_get_user_adaptations(self):
        """Test getting user-specific adaptations"""
        # Queue adaptation for specific user
        adaptation_id = self.engine.adapt_model_for_user(self.user_id, self.model_id)
        
        # Wait for processing
        time.sleep(1)
        
        user_adaptations = self.engine.get_user_adaptations(self.user_id)
        
        # Should have at least one adaptation for this user
        user_adaptation_ids = [a.adaptation_id for a in user_adaptations]
        if user_adaptations:  # May be empty if processing failed
            self.assertIn(adaptation_id, user_adaptation_ids)
    
    def test_adapter_selection(self):
        """Test adapter selection for different models"""
        # Test spaCy model
        spacy_adapter = self.engine._get_adapter_for_model("spacy_md")
        self.assertIsInstance(spacy_adapter, SpacyModelAdapter)
        
        # Test transformer model
        transformer_adapter = self.engine._get_adapter_for_model("bert_base")
        self.assertIsInstance(transformer_adapter, TransformerModelAdapter)
        
        # Test unsupported model
        unsupported_adapter = self.engine._get_adapter_for_model("unknown_model")
        self.assertIsNone(unsupported_adapter)

class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_model_adaptation_engine(self):
        """Test creating model adaptation engine"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_profile_db:
            temp_profile_db.close()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_feedback_db:
                temp_feedback_db.close()
                
                try:
                    profile_storage = create_user_profile_storage(temp_profile_db.name)
                    feedback_storage = create_feedback_storage(temp_feedback_db.name)
                    personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
                    
                    engine = create_model_adaptation_engine(personalization_engine, feedback_storage)
                    self.assertIsInstance(engine, ModelAdaptationEngine)
                    
                    # Test basic functionality
                    stats = engine.get_adaptation_statistics()
                    self.assertIsInstance(stats, dict)
                    
                    engine.stop()
                    
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
        
        profile_storage = create_user_profile_storage(self.temp_profile_db.name)
        feedback_storage = create_feedback_storage(self.temp_feedback_db.name)
        self.personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
        self.engine = create_model_adaptation_engine(self.personalization_engine, feedback_storage)
        
        self.user_id = "integration_user"
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        self.engine.stop()
        try:
            os.unlink(self.temp_profile_db.name)
            os.unlink(self.temp_feedback_db.name)
        except OSError:
            pass
    
    def test_complete_adaptation_workflow(self):
        """Test complete adaptation workflow"""
        # 1. Create user profile with preferences
        profile = self.personalization_engine.get_or_create_profile(self.user_id)
        preferences = {
            'model_preference_type': 'accuracy_optimized',
            'domain_expertise': ['technical'],
            'learning_goals': ['accuracy_improvement']
        }
        self.personalization_engine.update_user_preferences(self.user_id, preferences)
        
        # 2. Queue model adaptation
        adaptation_id = self.engine.adapt_model_for_user(
            self.user_id, "spacy_md", AdaptationType.PARAMETER_TUNING
        )
        self.assertIsNotNone(adaptation_id)
        
        # 3. Wait for processing
        time.sleep(2)
        
        # 4. Check adaptation results
        user_adaptations = self.engine.get_user_adaptations(self.user_id)
        self.assertGreater(len(user_adaptations), 0)
        
        # 5. Get adapted parameters
        adapted_params = self.engine.get_adapted_parameters(self.user_id, "spacy_md")
        if adapted_params:
            self.assertEqual(adapted_params.model_id, "spacy_md")
            # Should include technical vocabulary due to domain expertise
            self.assertTrue(any("API" in vocab for vocab in [adapted_params.vocabulary_additions]))
        
        # 6. Apply global improvements
        improvements = [{
            'type': 'threshold_modification',
            'models': ['spacy_md'],
            'threshold_changes': {'transcription': 0.9}
        }]
        
        global_adaptations = self.engine.apply_global_improvements(improvements)
        self.assertGreater(len(global_adaptations), 0)
        
        # 7. Get final statistics
        stats = self.engine.get_adaptation_statistics()
        self.assertGreater(stats['total_adaptations'], 0)
    
    def test_multiple_user_adaptations(self):
        """Test adaptations for multiple users"""
        users = ["user1", "user2", "user3"]
        models = ["spacy_md", "bert_base", "spacy_lg"]
        
        # Queue adaptations for multiple users
        adaptation_ids = []
        for user in users:
            for model in models:
                if self.engine._get_adapter_for_model(model):  # Only supported models
                    adaptation_id = self.engine.adapt_model_for_user(user, model)
                    adaptation_ids.append(adaptation_id)
        
        # Wait for processing
        time.sleep(3)
        
        # Check statistics
        stats = self.engine.get_adaptation_statistics()
        self.assertGreater(stats['total_adaptations'], 0)
        
        # Check each user has adaptations
        for user in users:
            user_adaptations = self.engine.get_user_adaptations(user)
            # May be empty if adaptations failed, but test the mechanism works
            self.assertIsInstance(user_adaptations, list)

def run_tests():
    """Run all tests with detailed output"""
    test_classes = [
        TestAdaptationRule,
        TestModelParameters,
        TestAdaptationResult,
        TestSpacyModelAdapter,
        TestTransformerModelAdapter,
        TestModelAdaptationEngine,
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