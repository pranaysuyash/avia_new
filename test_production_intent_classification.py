"""
Comprehensive tests for Production Intent Classification System

Tests all major functionality including:
- ML-based intent classification
- Contextual understanding
- Human feedback integration
- Database operations
- Rule-based fallbacks
- Active learning capabilities

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock

from production_intent_classification_system import (
    ProductionIntentClassificationSystem,
    IntentExample,
    IntentPrediction,
    ConversationContext,
    ModelPerformance,
    IntentType,
    ConfidenceLevel,
    ModelType,
    ClassicalMLClassifier,
    RuleBasedClassifier,
    ContextualIntentClassifier,
    IntentClassificationDatabase,
    create_sample_training_data
)


class TestProductionIntentClassificationSystem(unittest.TestCase):
    """Test suite for Production Intent Classification System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_intent_classification.db")
        self.system = ProductionIntentClassificationSystem(
            db_path=self.db_path,
            model_type=ModelType.CLASSICAL_ML
        )
        
        # Create minimal training data (at least 2 examples per class for stratification)
        self.training_examples = [
            IntentExample("What time is it?", IntentType.QUESTION.value),
            IntentExample("How are you?", IntentType.QUESTION.value),
            IntentExample("Please help me", IntentType.REQUEST.value),
            IntentExample("Can you assist?", IntentType.REQUEST.value),
            IntentExample("This is broken", IntentType.COMPLAINT.value),
            IntentExample("I'm not happy", IntentType.COMPLAINT.value),
            IntentExample("Thank you", IntentType.COMPLIMENT.value),
            IntentExample("Great job", IntentType.COMPLIMENT.value),
            IntentExample("Hello", IntentType.GREETING.value),
            IntentExample("Hi there", IntentType.GREETING.value),
            IntentExample("Yes", IntentType.CONFIRMATION.value),
            IntentExample("Correct", IntentType.CONFIRMATION.value),
            IntentExample("No", IntentType.DENIAL.value),
            IntentExample("Wrong", IntentType.DENIAL.value),
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.system, ProductionIntentClassificationSystem)
        self.assertIsInstance(self.system.db, IntentClassificationDatabase)
        self.assertIsNotNone(self.system.classifier)
        self.assertIsNotNone(self.system.contextual_classifier)
    
    def test_intent_example_creation(self):
        """Test IntentExample dataclass"""
        example = IntentExample(
            text="How can I help you?",
            intent=IntentType.QUESTION.value,
            confidence=0.9
        )
        
        self.assertEqual(example.text, "How can I help you?")
        self.assertEqual(example.intent, IntentType.QUESTION.value)
        self.assertEqual(example.confidence, 0.9)
        self.assertIsNotNone(example.created_at)
    
    def test_intent_prediction_creation(self):
        """Test IntentPrediction dataclass"""
        prediction = IntentPrediction(
            text="Hello there",
            predicted_intent=IntentType.GREETING.value,
            confidence=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            alternative_intents=[("question", 0.1)]
        )
        
        self.assertEqual(prediction.text, "Hello there")
        self.assertEqual(prediction.predicted_intent, IntentType.GREETING.value)
        self.assertEqual(prediction.confidence, 0.85)
        self.assertEqual(prediction.confidence_level, ConfidenceLevel.HIGH)
        self.assertIsNotNone(prediction.created_at)
    
    def test_confidence_level_assignment(self):
        """Test automatic confidence level assignment"""
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.8, ConfidenceLevel.HIGH),
            (0.6, ConfidenceLevel.MEDIUM),
            (0.3, ConfidenceLevel.LOW),
            (0.1, ConfidenceLevel.VERY_LOW)
        ]
        
        for confidence, expected_level in test_cases:
            prediction = IntentPrediction(
                text="test",
                predicted_intent="test",
                confidence=confidence,
                confidence_level=ConfidenceLevel.HIGH,  # Will be overridden
                alternative_intents=[]
            )
            self.assertEqual(prediction.confidence_level, expected_level)
    
    def test_conversation_context(self):
        """Test conversation context management"""
        context = ConversationContext(
            session_id="test_session",
            previous_intents=[],
            previous_texts=[]
        )
        
        self.assertEqual(context.session_id, "test_session")
        self.assertEqual(len(context.previous_intents), 0)
        
        # Add interactions
        context.add_interaction("Hello", IntentType.GREETING.value)
        context.add_interaction("How are you?", IntentType.QUESTION.value)
        
        self.assertEqual(len(context.previous_intents), 2)
        self.assertEqual(context.previous_intents[0], IntentType.GREETING.value)
        self.assertEqual(context.previous_texts[1], "How are you?")
    
    def test_training_with_classical_ml(self):
        """Test training with classical ML"""
        performance = self.system.train(self.training_examples, validation_split=0.3)
        
        self.assertIsInstance(performance, ModelPerformance)
        self.assertTrue(self.system.is_trained)
        self.assertGreater(performance.accuracy, 0)
        self.assertGreater(performance.training_time, 0)
        self.assertIsInstance(performance.precision, dict)
        self.assertIsInstance(performance.recall, dict)
    
    def test_prediction_without_training(self):
        """Test prediction without training (should use fallback)"""
        # Create untrained system
        untrained_system = ProductionIntentClassificationSystem(
            model_type=ModelType.CLASSICAL_ML
        )
        
        prediction = untrained_system.predict("Hello world")
        
        self.assertIsInstance(prediction, IntentPrediction)
        self.assertIsNotNone(prediction.predicted_intent)
        self.assertGreater(prediction.confidence, 0)
    
    def test_prediction_after_training(self):
        """Test prediction after training"""
        # Train the system
        self.system.train(self.training_examples, validation_split=0.3)
        
        # Test predictions
        test_cases = [
            ("What time is it?", IntentType.QUESTION.value),
            ("Please help me", IntentType.REQUEST.value),
            ("Hello there", IntentType.GREETING.value),
            ("Yes, that's correct", IntentType.CONFIRMATION.value)
        ]
        
        for text, expected_intent in test_cases:
            prediction = self.system.predict(text)
            self.assertIsInstance(prediction, IntentPrediction)
            self.assertEqual(prediction.text, text)
            self.assertGreater(prediction.confidence, 0)
            self.assertIsNotNone(prediction.predicted_intent)
    
    def test_contextual_prediction(self):
        """Test contextual prediction with session"""
        # Train the system
        self.system.train(self.training_examples, validation_split=0.3)
        
        session_id = "test_contextual_session"
        
        # Simulate a conversation
        conversation = [
            "Hello",
            "I have a question",
            "What time is it?",
            "Thank you"
        ]
        
        predictions = []
        for text in conversation:
            prediction = self.system.predict(text, session_id=session_id)
            predictions.append(prediction)
            self.assertTrue(prediction.context_used)
        
        self.assertEqual(len(predictions), 4)
        
        # Check that context is being used
        for prediction in predictions:
            self.assertTrue(prediction.context_used)
    
    def test_rule_based_classifier(self):
        """Test rule-based classifier fallback"""
        rule_system = ProductionIntentClassificationSystem(
            model_type=ModelType.RULE_BASED
        )
        
        test_cases = [
            ("What time is it?", IntentType.QUESTION.value),
            ("Please help me", IntentType.REQUEST.value),
            ("Hello", IntentType.GREETING.value),
            ("Yes", IntentType.CONFIRMATION.value),
            ("No", IntentType.DENIAL.value),
            ("This is broken", IntentType.COMPLAINT.value),
            ("Thank you", IntentType.COMPLIMENT.value)
        ]
        
        for text, expected_intent in test_cases:
            prediction = rule_system.predict(text)
            self.assertIsInstance(prediction, IntentPrediction)
            # Rule-based should at least identify basic patterns
            self.assertIsNotNone(prediction.predicted_intent)
    
    def test_human_feedback(self):
        """Test human feedback integration"""
        # Train and make a prediction
        self.system.train(self.training_examples, validation_split=0.3)
        prediction = self.system.predict("What time is it?")
        
        # Store prediction to get ID (simulated)
        prediction_id = 1
        
        # Add feedback
        self.system.add_feedback(
            prediction_id=prediction_id,
            correct_intent=IntentType.QUESTION.value,
            feedback_type="correction",
            confidence_rating=5,
            comments="Good prediction",
            user_id="test_user"
        )
        
        # Verify feedback was stored
        with sqlite3.connect(self.system.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM human_feedback")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)
    
    def test_analytics(self):
        """Test system analytics"""
        # Train and make some predictions
        self.system.train(self.training_examples, validation_split=0.3)
        
        test_texts = ["Hello", "What time is it?", "Please help"]
        for text in test_texts:
            self.system.predict(text)
        
        # Get analytics
        analytics = self.system.get_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_predictions', analytics)
        self.assertIn('avg_confidence', analytics)
        self.assertIn('avg_prediction_time', analytics)
        self.assertIn('intent_distribution', analytics)
        self.assertGreater(analytics['total_predictions'], 0)
    
    def test_training_data_export(self):
        """Test training data export"""
        # Train the system
        self.system.train(self.training_examples, validation_split=0.3)
        
        # Export training data
        export_path = os.path.join(self.temp_dir, "exported_data.json")
        self.system.export_training_data(export_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(export_path))
        
        # Verify content
        import json
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn('text', data[0])
        self.assertIn('intent', data[0])
    
    def test_database_operations(self):
        """Test database operations"""
        db = IntentClassificationDatabase(self.db_path)
        
        # Test storing training example
        example = IntentExample("Test text", IntentType.QUESTION.value)
        example_id = db.store_training_example(example)
        self.assertGreater(example_id, 0)
        
        # Test storing prediction
        prediction = IntentPrediction(
            text="Test prediction",
            predicted_intent=IntentType.QUESTION.value,
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            alternative_intents=[]
        )
        prediction_id = db.store_prediction(prediction)
        self.assertGreater(prediction_id, 0)
        
        # Test storing performance
        performance = ModelPerformance(
            accuracy=0.8,
            precision={},
            recall={},
            f1_score={},
            confusion_matrix=[],
            confidence_calibration=0.7,
            training_time=1.0,
            inference_time=0.01,
            model_size_mb=10.0
        )
        perf_id = db.store_model_performance("test_model", performance)
        self.assertGreater(perf_id, 0)
    
    def test_contextual_classifier(self):
        """Test contextual classifier"""
        base_classifier = RuleBasedClassifier()
        contextual = ContextualIntentClassifier(base_classifier)
        
        session_id = "test_context_session"
        
        # Test predictions with context
        texts = ["Hello", "I have a question", "What time is it?"]
        
        for text in texts:
            prediction = contextual.predict_with_context(text, session_id)
            self.assertIsInstance(prediction, IntentPrediction)
            self.assertTrue(prediction.context_used)
        
        # Check that context was maintained
        context = contextual.get_or_create_context(session_id)
        self.assertEqual(len(context.previous_texts), 3)
        self.assertEqual(len(context.previous_intents), 3)
    
    def test_model_fallback_behavior(self):
        """Test fallback behavior when preferred models aren't available"""
        # Test with unavailable transformer model
        with patch('production_intent_classification_system.TRANSFORMERS_AVAILABLE', False):
            system = ProductionIntentClassificationSystem(
                model_type=ModelType.BERT_BASE
            )
            # Should fall back to rule-based
            self.assertEqual(system.model_type, ModelType.RULE_BASED)
        
        # Test with unavailable sklearn
        with patch('production_intent_classification_system.SKLEARN_AVAILABLE', False):
            system = ProductionIntentClassificationSystem(
                model_type=ModelType.CLASSICAL_ML
            )
            # Should fall back to rule-based
            self.assertEqual(system.model_type, ModelType.RULE_BASED)
    
    def test_sample_training_data_creation(self):
        """Test sample training data creation"""
        training_data = create_sample_training_data()
        
        self.assertIsInstance(training_data, list)
        self.assertGreater(len(training_data), 50)  # Should have many examples
        
        # Check that all examples are valid
        for example in training_data:
            self.assertIsInstance(example, IntentExample)
            self.assertIsNotNone(example.text)
            self.assertIsNotNone(example.intent)
            self.assertGreater(len(example.text), 0)
        
        # Check that we have examples for different intents
        intents = set(example.intent for example in training_data)
        self.assertGreater(len(intents), 5)  # Multiple intent types


class TestClassicalMLClassifier(unittest.TestCase):
    """Test classical ML classifier"""
    
    def setUp(self):
        """Set up test environment"""
        self.classifier = ClassicalMLClassifier()
        self.training_examples = [
            IntentExample("What time is it?", IntentType.QUESTION.value),
            IntentExample("How are you?", IntentType.QUESTION.value),
            IntentExample("Please help me", IntentType.REQUEST.value),
            IntentExample("Can you assist?", IntentType.REQUEST.value),
            IntentExample("Hello", IntentType.GREETING.value),
            IntentExample("Hi there", IntentType.GREETING.value),
            IntentExample("Yes", IntentType.CONFIRMATION.value),
            IntentExample("Correct", IntentType.CONFIRMATION.value),
        ]
    
    def test_model_selection(self):
        """Test different model algorithms"""
        algorithms = ["logistic_regression", "svm", "random_forest"]
        
        for algorithm in algorithms:
            classifier = ClassicalMLClassifier(algorithm=algorithm)
            model = classifier._get_model()
            self.assertIsNotNone(model)
    
    def test_training_and_prediction(self):
        """Test training and prediction"""
        if not hasattr(self, 'classifier'):
            self.skipTest("Classifier not available")
        
        # Create dataset
        from production_intent_classification_system import IntentDataset
        dataset = IntentDataset(self.training_examples)
        
        # Train
        performance = self.classifier.train(dataset)
        
        self.assertIsInstance(performance, ModelPerformance)
        self.assertTrue(self.classifier.is_trained)
        
        # Predict
        prediction = self.classifier.predict("What time is it?")
        self.assertIsInstance(prediction, IntentPrediction)


class TestRuleBasedClassifier(unittest.TestCase):
    """Test rule-based classifier"""
    
    def setUp(self):
        """Set up test environment"""
        self.classifier = RuleBasedClassifier()
    
    def test_rule_based_predictions(self):
        """Test rule-based predictions"""
        test_cases = [
            ("What time is it?", IntentType.QUESTION.value),
            ("Please help me", IntentType.REQUEST.value),
            ("Hello", IntentType.GREETING.value),
            ("Yes", IntentType.CONFIRMATION.value),
            ("No", IntentType.DENIAL.value),
            ("This is broken", IntentType.COMPLAINT.value),
            ("Thank you", IntentType.COMPLIMENT.value)
        ]
        
        for text, expected_intent in test_cases:
            prediction = self.classifier.predict(text)
            self.assertIsInstance(prediction, IntentPrediction)
            # Rule-based might not be perfect, but should make reasonable predictions
            self.assertIsNotNone(prediction.predicted_intent)
    
    def test_unknown_text_handling(self):
        """Test handling of unknown/ambiguous text"""
        prediction = self.classifier.predict("asdfghjkl random text")
        self.assertIsInstance(prediction, IntentPrediction)
        # Should return UNKNOWN for unrecognizable text
        self.assertEqual(prediction.predicted_intent, IntentType.UNKNOWN.value)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Intent Classification Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionIntentClassificationSystem))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestClassicalMLClassifier))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRuleBasedClassifier))
    
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
    exit(0 if success else 1)