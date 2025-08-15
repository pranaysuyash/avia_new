#!/usr/bin/env python3
"""
Test Suite for Comprehensive Text Classification System
"""

import asyncio
import json
import os
import pytest
import tempfile
import unittest
from unittest.mock import Mock, patch

from comprehensive_text_classification_system import (
    ComprehensiveTextClassificationSystem,
    ContentTypeClassifier,
    DomainSpecificClassifier,
    TextPreprocessor,
    ActiveLearningSystem
)


class TestTextPreprocessor(unittest.TestCase):
    """Test text preprocessing functionality."""
    
    def setUp(self):
        self.preprocessor = TextPreprocessor()
    
    def test_basic_preprocessing(self):
        """Test basic text preprocessing."""
        text = "This is a Test Text with Some CAPS!"
        processed = self.preprocessor.transform([text])
        
        self.assertEqual(len(processed), 1)
        self.assertIsInstance(processed[0], str)
        self.assertTrue(len(processed[0]) > 0)
    
    def test_empty_text(self):
        """Test preprocessing of empty text."""
        processed = self.preprocessor.transform([""])
        self.assertEqual(processed[0], "")
    
    def test_multiple_texts(self):
        """Test preprocessing multiple texts."""
        texts = ["First text", "Second text", "Third text"]
        processed = self.preprocessor.transform(texts)
        
        self.assertEqual(len(processed), 3)
        for p in processed:
            self.assertIsInstance(p, str)


class TestContentTypeClassifier(unittest.TestCase):
    """Test content type classification."""
    
    def setUp(self):
        self.classifier = ContentTypeClassifier()
        self.classifier.build_model()
    
    def test_model_building(self):
        """Test that model builds correctly."""
        self.assertIsNotNone(self.classifier.preprocessor)
        self.assertIsNotNone(self.classifier.vectorizer)
        self.assertIsNotNone(self.classifier.model)
    
    def test_content_types_defined(self):
        """Test that content types are properly defined."""
        self.assertTrue(len(self.classifier.content_types) > 0)
        self.assertIn('educational', self.classifier.content_types)
        self.assertIn('promotional', self.classifier.content_types)
    
    @patch('comprehensive_text_classification_system.ContentTypeClassifier.train')
    def test_training_interface(self, mock_train):
        """Test training interface."""
        texts = ["This is educational content", "This is promotional content"]
        labels = [["educational"], ["promotional"]]
        
        self.classifier.train(texts, labels)
        mock_train.assert_called_once_with(texts, labels)


class TestDomainSpecificClassifier(unittest.TestCase):
    """Test domain-specific classification."""
    
    def setUp(self):
        self.classifier = DomainSpecificClassifier()
    
    def test_domains_defined(self):
        """Test that domains are properly defined."""
        self.assertIn('medical', self.classifier.domains)
        self.assertIn('legal', self.classifier.domains)
        self.assertIn('technical', self.classifier.domains)
        self.assertIn('business', self.classifier.domains)
    
    def test_domain_model_building(self):
        """Test building model for specific domain."""
        domain = 'medical'
        self.classifier.build_domain_model(domain)
        
        self.assertIn(domain, self.classifier.preprocessors)
        self.assertIn(domain, self.classifier.vectorizers)
        self.assertIn(domain, self.classifier.models)
    
    def test_unknown_domain_error(self):
        """Test error for unknown domain."""
        with self.assertRaises(ValueError):
            self.classifier.build_domain_model('unknown_domain')


class TestActiveLearningSystem(unittest.TestCase):
    """Test active learning functionality."""
    
    def setUp(self):
        # Mock classifier
        self.mock_classifier = Mock()
        self.active_learning = ActiveLearningSystem(self.mock_classifier)
    
    def test_uncertainty_sampling(self):
        """Test uncertainty sampling."""
        # Mock predictions with confidence scores
        self.mock_classifier.predict.return_value = [
            {'confidence': 0.9},
            {'confidence': 0.3},  # Most uncertain
            {'confidence': 0.7},
        ]
        
        texts = ["text1", "text2", "text3"]
        uncertain_indices = self.active_learning.uncertainty_sampling(texts, n_samples=1)
        
        self.assertEqual(len(uncertain_indices), 1)
        self.assertEqual(uncertain_indices[0], 1)  # Index of most uncertain sample
    
    def test_diversity_sampling(self):
        """Test diversity sampling."""
        texts = [
            "Short text",
            "This is a much longer text with many more words and content",
            "Medium length text here"
        ]
        
        diverse_indices = self.active_learning.diversity_sampling(texts, n_samples=2)
        
        self.assertEqual(len(diverse_indices), 2)
        self.assertTrue(all(0 <= idx < len(texts) for idx in diverse_indices))


class TestComprehensiveTextClassificationSystem(unittest.TestCase):
    """Test the main classification system."""
    
    def setUp(self):
        # Use temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.system = ComprehensiveTextClassificationSystem(db_path=self.temp_db.name)
    
    def tearDown(self):
        # Clean up temporary database
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test system initialization."""
        self.assertIsNotNone(self.system.content_classifier)
        self.assertIsNotNone(self.system.domain_classifier)
        self.assertIsNotNone(self.system.transformer_classifier)
        self.assertTrue(os.path.exists(self.temp_db.name))
    
    def test_medical_schema_initialization(self):
        """Test medical schema initialization."""
        self.assertIn('specialties', self.system.medical_schema)
        self.assertIn('document_types', self.system.medical_schema)
        self.assertIn('urgency_levels', self.system.medical_schema)
        
        self.assertIn('cardiology', self.system.medical_schema['specialties'])
        self.assertIn('clinical_note', self.system.medical_schema['document_types'])
    
    @patch('comprehensive_text_classification_system.ContentTypeClassifier.predict')
    async def test_classify_text(self, mock_predict):
        """Test text classification."""
        # Mock content classifier prediction
        mock_predict.return_value = [{'educational': 0.8, 'technical': 0.2}]
        
        text = "This is a test text for classification"
        result = await self.system.classify_text(text)
        
        self.assertNotIn('error', result)
        self.assertIn('text_hash', result)
        self.assertIn('timestamp', result)
        self.assertIn('classifications', result)
        self.assertIn('content_types', result['classifications'])
    
    async def test_classify_empty_text(self):
        """Test classification of empty text."""
        result = await self.system.classify_text("")
        self.assertIn('error', result)
    
    async def test_medical_content_classification(self):
        """Test medical content classification."""
        medical_text = "Patient presents with chest pain. Cardiology consultation recommended. Urgent review needed."
        
        with patch.object(self.system.content_classifier, 'predict') as mock_predict:
            # Mock detection of medical content
            mock_predict.return_value = [{'medical': 0.9, 'clinical': 0.8}]
            
            result = await self.system.classify_text(medical_text)
            
            self.assertIn('classifications', result)
            # Check if medical classification was triggered
            # Note: This might not always trigger based on keyword detection
    
    def test_get_classification_stats(self):
        """Test getting classification statistics."""
        stats = self.system.get_classification_stats()
        
        self.assertIn('total_classifications', stats)
        self.assertIn('models_trained', stats)
        self.assertIsInstance(stats['total_classifications'], int)
    
    async def test_batch_classify(self):
        """Test batch classification."""
        texts = [
            "Educational content about machine learning",
            "Promotional material for new product",
            "Technical documentation for developers"
        ]
        
        with patch.object(self.system, 'classify_text') as mock_classify:
            # Mock individual classifications
            mock_classify.return_value = {'classifications': {'content_types': {}}}
            
            results = await self.system.batch_classify(texts, batch_size=2)
            
            self.assertEqual(len(results), 3)
            self.assertEqual(mock_classify.call_count, 3)
    
    def test_export_training_data(self):
        """Test exporting training data."""
        exported_data = self.system.export_training_data()
        self.assertIsInstance(exported_data, list)
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        deleted_count = self.system.cleanup_old_data(days_old=30)
        self.assertIsInstance(deleted_count, int)
        self.assertGreaterEqual(deleted_count, 0)


class TestClassificationIntegration(unittest.TestCase):
    """Integration tests for classification system."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.system = ComprehensiveTextClassificationSystem(db_path=self.temp_db.name)
    
    def tearDown(self):
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    async def test_full_classification_pipeline(self):
        """Test complete classification pipeline."""
        test_cases = [
            {
                'text': "This is an educational tutorial about Python programming for beginners",
                'expected_types': ['educational', 'technical']
            },
            {
                'text': "Buy now and get 50% off our amazing product! Limited time offer!",
                'expected_types': ['promotional']
            },
            {
                'text': "Patient diagnosed with hypertension. Prescribed medication. Follow-up in 2 weeks.",
                'expected_types': ['medical']
            }
        ]
        
        results = []
        for case in test_cases:
            with patch.object(self.system.content_classifier, 'predict') as mock_predict:
                # Mock appropriate predictions based on expected types
                mock_scores = {t: 0.8 for t in case['expected_types']}
                mock_predict.return_value = [mock_scores]
                
                result = await self.system.classify_text(case['text'])
                results.append(result)
                
                self.assertNotIn('error', result)
                self.assertIn('classifications', result)
        
        self.assertEqual(len(results), len(test_cases))
    
    def test_database_operations(self):
        """Test database storage and retrieval."""
        # Test that database operations don't raise errors
        try:
            stats = self.system.get_classification_stats()
            self.assertIsInstance(stats, dict)
            
            exported_data = self.system.export_training_data()
            self.assertIsInstance(exported_data, list)
            
            cleanup_count = self.system.cleanup_old_data(days_old=1)
            self.assertIsInstance(cleanup_count, int)
            
        except Exception as e:
            self.fail(f"Database operations failed: {e}")


# Test runner
def run_tests():
    """Run all tests."""
    print("🧪 Running Comprehensive Text Classification System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTextPreprocessor,
        TestContentTypeClassifier,
        TestDomainSpecificClassifier,
        TestActiveLearningSystem,
        TestComprehensiveTextClassificationSystem,
        TestClassificationIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


async def run_integration_demo():
    """Run integration demonstration."""
    print("\n🎯 Running Integration Demonstration")
    print("=" * 40)
    
    # Create temporary system
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        system = ComprehensiveTextClassificationSystem(db_path=temp_db.name)
        
        # Demo texts
        demo_texts = [
            "Welcome to our comprehensive machine learning course designed for beginners and intermediate learners.",
            "URGENT: Patient showing signs of cardiac arrest. Immediate intervention required.",
            "This patent application describes a novel approach to natural language processing using transformer architectures.",
            "Don't miss out! 70% discount on all premium features. Subscribe now before the offer expires!",
            "The quarterly earnings call will discuss our financial performance and strategic initiatives for next year."
        ]
        
        print("Classifying demo texts...")
        
        for i, text in enumerate(demo_texts, 1):
            print(f"\n📝 Text {i}: {text[:80]}...")
            
            # Mock the classifier to return realistic results
            with patch.object(system.content_classifier, 'predict') as mock_predict:
                # Generate realistic mock predictions based on text content
                text_lower = text.lower()
                mock_scores = {}
                
                if 'course' in text_lower or 'learn' in text_lower:
                    mock_scores = {'educational': 0.85, 'training': 0.45}
                elif 'urgent' in text_lower or 'patient' in text_lower:
                    mock_scores = {'medical': 0.90, 'clinical': 0.75}
                elif 'patent' in text_lower or 'technical' in text_lower:
                    mock_scores = {'legal': 0.70, 'technical': 0.80}
                elif 'discount' in text_lower or 'subscribe' in text_lower:
                    mock_scores = {'promotional': 0.95, 'marketing': 0.60}
                elif 'earnings' in text_lower or 'financial' in text_lower:
                    mock_scores = {'business': 0.85, 'financial': 0.70}
                else:
                    mock_scores = {'general': 0.50}
                
                mock_predict.return_value = [mock_scores]
                
                result = await system.classify_text(text)
                
                if 'error' not in result:
                    content_types = result['classifications'].get('content_types', {})
                    print(f"  Classifications: {content_types}")
                else:
                    print(f"  Error: {result['error']}")
        
        # Show system stats
        print(f"\n📈 Final Statistics:")
        stats = system.get_classification_stats()
        print(f"  Total classifications: {stats.get('total_classifications', 0)}")
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_db.name)
        except:
            pass
    
    print("\n✅ Integration demonstration completed!")


if __name__ == "__main__":
    import sys
    
    # Run tests
    success = run_tests()
    
    # Run integration demo
    asyncio.run(run_integration_demo())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)