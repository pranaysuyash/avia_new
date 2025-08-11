#!/usr/bin/env python3
"""
Test Suite for Punctuation Restoration and Text Enhancement
Tests for Task 88: Build punctuation restoration and text enhancement
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from punctuation_restoration import (
    PunctuationRestorer, TextFormatter, PunctuationEnhancementService,
    TextEnhancementResult, PunctuationChange
)

class TestPunctuationRestorer(unittest.TestCase):
    """Test cases for PunctuationRestorer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the model loading to avoid downloading models during tests
        with patch('punctuation_restoration.AutoTokenizer'), \
             patch('punctuation_restoration.AutoModelForTokenClassification'), \
             patch('punctuation_restoration.pipeline'), \
             patch('punctuation_restoration.SentenceTransformer'):
            self.restorer = PunctuationRestorer()
            # Set up mock pipeline
            self.restorer.punctuation_pipeline = Mock()
    
    def test_preprocess_text(self):
        """Test text preprocessing"""
        # Test basic preprocessing
        text = "  hello   world  "
        result = self.restorer._preprocess_text(text)
        self.assertEqual(result, "hello world")
        
        # Test multiple periods removal
        text = "hello world... this is a test"
        result = self.restorer._preprocess_text(text)
        self.assertEqual(result, "hello world this is a test")
        
        # Test empty text
        result = self.restorer._preprocess_text("")
        self.assertEqual(result, "")
    
    def test_split_into_chunks(self):
        """Test text chunking"""
        text = "word " * 100  # 100 words
        chunks = self.restorer._split_into_chunks(text, max_length=50)
        
        # Should split into multiple chunks
        self.assertGreater(len(chunks), 1)
        
        # Each chunk should be within limit
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 50)
    
    def test_map_label_to_punctuation(self):
        """Test label to punctuation mapping"""
        self.assertEqual(self.restorer._map_label_to_punctuation('PERIOD'), '.')
        self.assertEqual(self.restorer._map_label_to_punctuation('COMMA'), ',')
        self.assertEqual(self.restorer._map_label_to_punctuation('QUESTION'), '?')
        self.assertEqual(self.restorer._map_label_to_punctuation('UNKNOWN'), '')
    
    def test_is_question(self):
        """Test question detection"""
        # Test question words
        self.assertTrue(self.restorer._is_question("what time is it"))
        self.assertTrue(self.restorer._is_question("where are you going"))
        self.assertTrue(self.restorer._is_question("how are you"))
        
        # Test auxiliary verbs
        self.assertTrue(self.restorer._is_question("are you coming"))
        self.assertTrue(self.restorer._is_question("can you help me"))
        self.assertTrue(self.restorer._is_question("will you be there"))
        
        # Test non-questions
        self.assertFalse(self.restorer._is_question("this is a statement"))
        self.assertFalse(self.restorer._is_question("hello world"))
    
    def test_is_proper_noun(self):
        """Test proper noun detection"""
        # Test days of week
        self.assertTrue(self.restorer._is_proper_noun("monday"))
        self.assertTrue(self.restorer._is_proper_noun("friday"))
        
        # Test months
        self.assertTrue(self.restorer._is_proper_noun("january"))
        self.assertTrue(self.restorer._is_proper_noun("december"))
        
        # Test languages
        self.assertTrue(self.restorer._is_proper_noun("english"))
        self.assertTrue(self.restorer._is_proper_noun("spanish"))
        
        # Test non-proper nouns
        self.assertFalse(self.restorer._is_proper_noun("hello"))
        self.assertFalse(self.restorer._is_proper_noun("world"))
    
    def test_fix_spacing(self):
        """Test spacing fixes"""
        text = "hello  world  ,  this   is  a  test  ."
        result, changes = self.restorer._fix_spacing(text)
        
        # Should fix multiple spaces and punctuation spacing
        self.assertNotIn("  ", result)  # No double spaces
        self.assertIn("world,", result)  # No space before comma
        self.assertIn("test.", result)   # No space before period
    
    def test_fix_abbreviations(self):
        """Test abbreviation fixes"""
        text = "hello dr smith and mr jones"
        result, changes = self.restorer._fix_abbreviations(text)
        
        # Should capitalize abbreviations
        self.assertIn("Dr.", result)
        self.assertIn("Mr.", result)
    
    def test_restore_punctuation_with_mock(self):
        """Test punctuation restoration with mocked AI model"""
        # Mock the AI pipeline response
        mock_predictions = [
            {
                'entity_group': 'PERIOD',
                'start': 0,
                'end': 11,
                'score': 0.9
            },
            {
                'entity_group': 'COMMA',
                'start': 12,
                'end': 17,
                'score': 0.8
            }
        ]
        
        self.restorer.punctuation_pipeline.return_value = mock_predictions
        
        text = "hello world this is a test"
        result = self.restorer.restore_punctuation(text)
        
        # Should return a TextEnhancementResult
        self.assertIsInstance(result, TextEnhancementResult)
        self.assertEqual(result.original_text, text)
        self.assertIsInstance(result.enhanced_text, str)
        self.assertIsInstance(result.confidence_score, float)
        self.assertIsInstance(result.changes_made, list)
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        original = "hello world"
        enhanced = "Hello world."
        changes = [
            {'confidence': 0.9},
            {'confidence': 0.8}
        ]
        
        confidence = self.restorer._calculate_confidence(original, enhanced, changes)
        
        # Should be between 0 and 1
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        
        # Should be reasonable average
        self.assertGreater(confidence, 0.5)


class TestTextFormatter(unittest.TestCase):
    """Test cases for TextFormatter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('punctuation_restoration.PunctuationRestorer'):
            self.formatter = TextFormatter()
            # Mock the punctuation restorer
            self.formatter.punctuation_restorer = Mock()
            mock_result = TextEnhancementResult(
                original_text="test",
                enhanced_text="Test.",
                confidence_score=0.9,
                changes_made=[],
                processing_time=0.1,
                metadata={}
            )
            self.formatter.punctuation_restorer.restore_punctuation.return_value = mock_result
    
    def test_format_quotes(self):
        """Test quote formatting"""
        text = "he said quote hello world unquote"
        result, changes = self.formatter._format_quotes(text)
        
        self.assertIn('"hello world"', result)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['change_type'], 'replace')
    
    def test_format_numbers(self):
        """Test number formatting"""
        text = "please turn to page twenty three"
        result, changes = self.formatter._format_numbers(text)
        
        # Should convert number words in appropriate context
        self.assertIn("page", result)  # Context should be preserved
        
        # Test that not all number words are converted
        text2 = "one day I will be happy"
        result2, changes2 = self.formatter._format_numbers(text2)
        # "one" in this context should not be converted to "1"
    
    def test_format_dates(self):
        """Test date formatting"""
        text = "the meeting is on January 1st 2024"
        result, changes = self.formatter._format_dates(text)
        
        self.assertIn("January 1, 2024", result)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['change_type'], 'replace')
    
    def test_format_text_comprehensive(self):
        """Test comprehensive text formatting"""
        text = "hello world this is a test"
        options = {
            'restore_punctuation': True,
            'fix_capitalization': True,
            'format_numbers': True,
            'format_quotes': True,
            'format_dates': True
        }
        
        result = self.formatter.format_text(text, options)
        
        # Should return TextEnhancementResult
        self.assertIsInstance(result, TextEnhancementResult)
        self.assertEqual(result.original_text, text)
        self.assertIsInstance(result.enhanced_text, str)
        self.assertIsInstance(result.confidence_score, float)
        self.assertIsInstance(result.changes_made, list)
        self.assertIsInstance(result.processing_time, float)
        self.assertIsInstance(result.metadata, dict)


class TestPunctuationEnhancementService(unittest.TestCase):
    """Test cases for PunctuationEnhancementService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch('punctuation_restoration.TextFormatter'):
            self.service = PunctuationEnhancementService()
            # Mock the text formatter
            self.service.text_formatter = Mock()
            mock_result = TextEnhancementResult(
                original_text="test",
                enhanced_text="Test.",
                confidence_score=0.9,
                changes_made=[{'change_type': 'add', 'confidence': 0.9}],
                processing_time=0.1,
                metadata={'test': True}
            )
            self.service.text_formatter.format_text.return_value = mock_result
    
    def test_enhance_transcript_success(self):
        """Test successful transcript enhancement"""
        transcript = "hello world this is a test"
        result = self.service.enhance_transcript(transcript)
        
        # Should return success result
        self.assertTrue(result['success'])
        self.assertEqual(result['original_text'], transcript)
        self.assertIn('enhanced_text', result)
        self.assertIn('confidence_score', result)
        self.assertIn('changes_made', result)
        self.assertIn('processing_time', result)
        self.assertIn('metadata', result)
        self.assertIn('statistics', result)
        
        # Statistics should be calculated
        stats = result['statistics']
        self.assertIn('original_length', stats)
        self.assertIn('enhanced_length', stats)
        self.assertIn('changes_count', stats)
        self.assertIn('improvement_ratio', stats)
    
    def test_enhance_transcript_with_options(self):
        """Test transcript enhancement with custom options"""
        transcript = "hello world"
        options = {
            'restore_punctuation': False,
            'fix_capitalization': True,
            'confidence_threshold': 0.8
        }
        
        result = self.service.enhance_transcript(transcript, options)
        
        # Should pass options to formatter
        self.service.text_formatter.format_text.assert_called_once()
        call_args = self.service.text_formatter.format_text.call_args
        self.assertEqual(call_args[0][0], transcript)  # First argument should be transcript
        self.assertEqual(call_args[0][1], options)     # Second argument should be options
    
    def test_batch_enhance(self):
        """Test batch enhancement"""
        transcripts = ["hello world", "this is a test", "how are you"]
        results = self.service.batch_enhance(transcripts)
        
        # Should return list of results
        self.assertEqual(len(results), len(transcripts))
        
        # Each result should be a success
        for result in results:
            self.assertTrue(result['success'])
            self.assertIn('enhanced_text', result)
    
    def test_get_enhancement_statistics_empty(self):
        """Test statistics when no enhancements have been performed"""
        stats = self.service.get_enhancement_statistics()
        
        self.assertIn('message', stats)
        self.assertEqual(stats['message'], 'No enhancement history available')
    
    def test_get_enhancement_statistics_with_history(self):
        """Test statistics with enhancement history"""
        # Add some mock history
        mock_result = TextEnhancementResult(
            original_text="test",
            enhanced_text="Test.",
            confidence_score=0.9,
            changes_made=[{'change_type': 'add'}],
            processing_time=0.1,
            metadata={}
        )
        
        self.service.enhancement_history = [mock_result, mock_result]
        
        stats = self.service.get_enhancement_statistics()
        
        self.assertEqual(stats['total_enhancements'], 2)
        self.assertEqual(stats['average_confidence'], 0.9)
        self.assertEqual(stats['average_processing_time'], 0.1)
        self.assertEqual(stats['total_changes_made'], 2)
        self.assertEqual(stats['average_changes_per_text'], 1.0)
    
    def test_history_size_limit(self):
        """Test that history maintains size limit"""
        # Set a small limit for testing
        self.service.max_history = 3
        
        # Add more results than the limit
        for i in range(5):
            mock_result = TextEnhancementResult(
                original_text=f"test{i}",
                enhanced_text=f"Test{i}.",
                confidence_score=0.9,
                changes_made=[],
                processing_time=0.1,
                metadata={}
            )
            self.service._add_to_history(mock_result)
        
        # Should only keep the last 3
        self.assertEqual(len(self.service.enhancement_history), 3)
        
        # Should keep the most recent ones
        self.assertEqual(self.service.enhancement_history[0].original_text, "test2")
        self.assertEqual(self.service.enhancement_history[-1].original_text, "test4")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def test_end_to_end_enhancement(self):
        """Test complete end-to-end enhancement process"""
        # This test uses the actual classes but with mocked external dependencies
        
        with patch('punctuation_restoration.AutoTokenizer'), \
             patch('punctuation_restoration.AutoModelForTokenClassification'), \
             patch('punctuation_restoration.pipeline'), \
             patch('punctuation_restoration.SentenceTransformer'), \
             patch('punctuation_restoration.spacy.load'):
            
            service = PunctuationEnhancementService()
            
            # Test with a simple text
            text = "hello world this is a test"
            result = service.enhance_transcript(text)
            
            # Should complete without errors
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
    
    def test_error_handling(self):
        """Test error handling in the service"""
        with patch('punctuation_restoration.TextFormatter') as mock_formatter:
            # Make the formatter raise an exception
            mock_formatter.return_value.format_text.side_effect = Exception("Test error")
            
            service = PunctuationEnhancementService()
            result = service.enhance_transcript("test text")
            
            # Should handle error gracefully
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            self.assertEqual(result['error'], "Test error")
            self.assertEqual(result['enhanced_text'], "test text")  # Should return original


class TestDataStructures(unittest.TestCase):
    """Test data structures and models"""
    
    def test_text_enhancement_result(self):
        """Test TextEnhancementResult data structure"""
        result = TextEnhancementResult(
            original_text="hello",
            enhanced_text="Hello.",
            confidence_score=0.9,
            changes_made=[],
            processing_time=0.1,
            metadata={'test': True}
        )
        
        self.assertEqual(result.original_text, "hello")
        self.assertEqual(result.enhanced_text, "Hello.")
        self.assertEqual(result.confidence_score, 0.9)
        self.assertEqual(result.changes_made, [])
        self.assertEqual(result.processing_time, 0.1)
        self.assertEqual(result.metadata, {'test': True})
    
    def test_punctuation_change(self):
        """Test PunctuationChange data structure"""
        change = PunctuationChange(
            position=5,
            original="",
            replacement=".",
            change_type="add",
            confidence=0.9,
            reason="End of sentence"
        )
        
        self.assertEqual(change.position, 5)
        self.assertEqual(change.original, "")
        self.assertEqual(change.replacement, ".")
        self.assertEqual(change.change_type, "add")
        self.assertEqual(change.confidence, 0.9)
        self.assertEqual(change.reason, "End of sentence")


def run_performance_tests():
    """Run performance tests"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    import time
    
    # Mock the heavy dependencies for performance testing
    with patch('punctuation_restoration.AutoTokenizer'), \
         patch('punctuation_restoration.AutoModelForTokenClassification'), \
         patch('punctuation_restoration.pipeline'), \
         patch('punctuation_restoration.SentenceTransformer'), \
         patch('punctuation_restoration.spacy.load'):
        
        service = PunctuationEnhancementService()
        
        # Test with different text sizes
        test_sizes = [10, 50, 100, 500]
        
        for size in test_sizes:
            text = "hello world " * size
            
            start_time = time.time()
            result = service.enhance_transcript(text)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            print(f"Text size: {size} words")
            print(f"Processing time: {processing_time:.3f}s")
            print(f"Words per second: {size/processing_time:.1f}")
            print("-" * 30)


def run_example_tests():
    """Run tests with example texts"""
    print("\n" + "="*50)
    print("EXAMPLE TESTS")
    print("="*50)
    
    examples = [
        "hello world this is a test can you hear me yes i can",
        "what time is it now its three thirty pm",
        "please turn to page twenty three and read chapter five",
        "he said quote i will be there at five pm unquote",
        "the meeting is on january fifteenth two thousand twenty four"
    ]
    
    # Mock dependencies for example testing
    with patch('punctuation_restoration.AutoTokenizer'), \
         patch('punctuation_restoration.AutoModelForTokenClassification'), \
         patch('punctuation_restoration.pipeline'), \
         patch('punctuation_restoration.SentenceTransformer'), \
         patch('punctuation_restoration.spacy.load'):
        
        service = PunctuationEnhancementService()
        
        for i, example in enumerate(examples, 1):
            print(f"Example {i}:")
            print(f"Original: {example}")
            
            result = service.enhance_transcript(example)
            
            if result['success']:
                print(f"Enhanced: {result['enhanced_text']}")
                print(f"Confidence: {result['confidence_score']:.2f}")
                print(f"Changes: {len(result['changes_made'])}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            
            print("-" * 50)


if __name__ == '__main__':
    # Run unit tests
    print("Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    run_performance_tests()
    
    # Run example tests
    run_example_tests()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)