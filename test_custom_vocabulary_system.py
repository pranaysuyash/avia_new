"""
Comprehensive test suite for Custom Vocabulary and Domain Adaptation System

This module provides thorough testing of all components including vocabulary
submission, verification, domain adaptation, pronunciation generation, and analytics.
"""

import unittest
import os
import sys
import tempfile
import json
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import warnings
warnings.filterwarnings("ignore")

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from custom_vocabulary_system import (
        CustomVocabularySystem, VocabularyDatabase, VocabularyValidator,
        PhoneticTranscriber, DomainAdaptationEngine, UserSubmissionWorkflow,
        VocabularyEntry, ValidationResult, DomainCategory, VocabularyStatus,
        DomainAdaptationConfig
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

class TestPhoneticTranscriber(unittest.TestCase):
    """Test cases for PhoneticTranscriber"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.transcriber = PhoneticTranscriber()
    
    def test_get_phonetic_transcription(self):
        """Test phonetic transcription generation"""
        # Test common words
        test_words = ["hello", "world", "test", "pronunciation"]
        
        for word in test_words:
            ipa, phonetic = self.transcriber.get_phonetic_transcription(word)
            
            self.assertIsInstance(ipa, str)
            self.assertIsInstance(phonetic, str)
            self.assertGreater(len(ipa), 0)
            self.assertGreater(len(phonetic), 0)
    
    def test_arpabet_to_ipa_conversion(self):
        """Test ARPAbet to IPA conversion"""
        # Test with known ARPAbet phonemes
        test_phonemes = ['HH', 'EH', 'L', 'OW']
        result = self.transcriber._arpabet_to_ipa(test_phonemes)
        
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
    
    def test_phonemes_to_spelling(self):
        """Test phonemes to spelling conversion"""
        test_phonemes = ['HH', 'EH', 'L', 'OW']
        result = self.transcriber._phonemes_to_spelling(test_phonemes)
        
        self.assertIsInstance(result, str)
        self.assertIn('-', result)  # Should contain separators
    
    def test_rule_based_transcription(self):
        """Test rule-based transcription fallback"""
        ipa, phonetic = self.transcriber._rule_based_transcription("example")
        
        self.assertIsInstance(ipa, str)
        self.assertIsInstance(phonetic, str)
        self.assertGreater(len(ipa), 0)
        self.assertGreater(len(phonetic), 0)

class TestVocabularyValidator(unittest.TestCase):
    """Test cases for VocabularyValidator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = VocabularyValidator()
        
        # Create a valid test entry
        self.valid_entry = VocabularyEntry(
            id="test_id",
            term="Test Term",
            definition="A comprehensive definition for testing purposes that meets minimum length requirements.",
            pronunciation="tɛst tɝm",
            phonetic_spelling="test-term",
            domain=DomainCategory.TECHNICAL,
            language="en",
            alternatives=["Alternative Term"],
            context_examples=["This is a test term used in examples."],
            frequency_score=0.5,
            confidence_score=0.8,
            status=VocabularyStatus.PENDING,
            submitter_id="test_user",
            verifier_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            usage_count=0,
            accuracy_score=0.0,
            tags=["test", "example"],
            related_terms=[],
            audio_samples=[],
            source_references=["Test Reference"]
        )
    
    def test_validate_valid_entry(self):
        """Test validation of a valid entry"""
        result = self.validator.validate_entry(self.valid_entry)
        
        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertGreater(result.confidence, 0.5)
        self.assertGreater(result.quality_score, 0.5)
    
    def test_validate_invalid_term(self):
        """Test validation with invalid term"""
        invalid_entry = self.valid_entry
        invalid_entry.term = "x"  # Too short
        
        result = self.validator.validate_entry(invalid_entry)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Term too short", ' '.join(result.issues))
    
    def test_validate_invalid_definition(self):
        """Test validation with invalid definition"""
        invalid_entry = self.valid_entry
        invalid_entry.definition = "Short"  # Too short
        
        result = self.validator.validate_entry(invalid_entry)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Definition too short", ' '.join(result.issues))
    
    def test_validate_term_quality(self):
        """Test term validation"""
        issues = []
        suggestions = []
        
        # Valid term
        score = self.validator._validate_term("Valid Term", issues, suggestions)
        self.assertGreater(score, 0.5)
        
        # Invalid characters
        issues.clear()
        score = self.validator._validate_term("Invalid@Term!", issues, suggestions)
        self.assertLess(score, 1.0)
        self.assertTrue(any("invalid characters" in issue.lower() for issue in issues))
    
    def test_validate_definition_quality(self):
        """Test definition validation"""
        issues = []
        suggestions = []
        
        # Valid definition
        valid_def = "A comprehensive definition that provides clear meaning and context for the term."
        score = self.validator._validate_definition(valid_def, issues, suggestions)
        self.assertGreater(score, 0.5)
        
        # Too short definition
        issues.clear()
        short_def = "Short"
        score = self.validator._validate_definition(short_def, issues, suggestions)
        self.assertLess(score, 1.0)
    
    def test_validate_examples(self):
        """Test context examples validation"""
        issues = []
        suggestions = []
        
        # Valid examples
        valid_examples = ["This term is used in context.", "Another example with the term."]
        score = self.validator._validate_examples(valid_examples, "term", issues, suggestions)
        self.assertGreater(score, 0.5)
        
        # No examples
        issues.clear()
        score = self.validator._validate_examples([], "term", issues, suggestions)
        self.assertLess(score, 1.0)

class TestVocabularyDatabase(unittest.TestCase):
    """Test cases for VocabularyDatabase"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = VocabularyDatabase(self.temp_db.name)
        
        # Create test entry
        self.test_entry = VocabularyEntry(
            id="test_entry_1",
            term="Database Test",
            definition="A test entry for database operations.",
            pronunciation="deɪtəbeɪs tɛst",
            phonetic_spelling="day-tuh-base test",
            domain=DomainCategory.TECHNICAL,
            language="en",
            alternatives=["DB Test"],
            context_examples=["This is a database test entry."],
            frequency_score=0.7,
            confidence_score=0.9,
            status=VocabularyStatus.APPROVED,
            submitter_id="test_user",
            verifier_id="test_verifier",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            usage_count=5,
            accuracy_score=0.85,
            tags=["database", "test"],
            related_terms=["Database", "Testing"],
            audio_samples=[],
            source_references=["Test Source"]
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Check if tables exist
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'vocabulary_entries', 'vocabulary_usage', 
                'domain_configs', 'submission_workflow'
            ]
            
            for table in expected_tables:
                self.assertIn(table, tables)
    
    def test_add_entry(self):
        """Test adding vocabulary entry"""
        success = self.db.add_entry(self.test_entry)
        self.assertTrue(success)
        
        # Verify entry was added
        retrieved_entry = self.db.get_entry(self.test_entry.id)
        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.term, self.test_entry.term)
    
    def test_get_entry(self):
        """Test retrieving vocabulary entry"""
        # Add entry first
        self.db.add_entry(self.test_entry)
        
        # Retrieve entry
        retrieved_entry = self.db.get_entry(self.test_entry.id)
        
        self.assertIsNotNone(retrieved_entry)
        self.assertEqual(retrieved_entry.id, self.test_entry.id)
        self.assertEqual(retrieved_entry.term, self.test_entry.term)
        self.assertEqual(retrieved_entry.domain, self.test_entry.domain)
    
    def test_search_entries(self):
        """Test searching vocabulary entries"""
        # Add test entry
        self.db.add_entry(self.test_entry)
        
        # Search by term
        results = self.db.search_entries("Database")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].term, self.test_entry.term)
        
        # Search by domain
        results = self.db.search_entries("", domain=DomainCategory.TECHNICAL)
        self.assertGreater(len(results), 0)
        
        # Search by status
        results = self.db.search_entries("", status=VocabularyStatus.APPROVED)
        self.assertGreater(len(results), 0)
    
    def test_get_domain_vocabulary(self):
        """Test getting domain-specific vocabulary"""
        # Add test entry
        self.db.add_entry(self.test_entry)
        
        # Get domain vocabulary
        domain_vocab = self.db.get_domain_vocabulary(DomainCategory.TECHNICAL)
        
        self.assertGreater(len(domain_vocab), 0)
        self.assertEqual(domain_vocab[0].domain, DomainCategory.TECHNICAL)
    
    def test_update_usage(self):
        """Test updating vocabulary usage"""
        # Add test entry
        self.db.add_entry(self.test_entry)
        
        # Update usage
        self.db.update_usage(self.test_entry.id, "test_user", "test_context", 0.9)
        
        # Verify usage was updated
        updated_entry = self.db.get_entry(self.test_entry.id)
        self.assertGreater(updated_entry.usage_count, self.test_entry.usage_count)

class TestDomainAdaptationEngine(unittest.TestCase):
    """Test cases for DomainAdaptationEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.vocab_db = VocabularyDatabase(self.temp_db.name)
        self.adaptation_engine = DomainAdaptationEngine(self.vocab_db)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_configure_domain(self):
        """Test domain configuration"""
        config = DomainAdaptationConfig(
            domain=DomainCategory.MEDICAL,
            vocabulary_weight=1.0,
            context_sensitivity=0.5,
            adaptation_threshold=0.3,
            learning_rate=0.1,
            max_vocabulary_size=1000,
            quality_threshold=0.7
        )
        
        self.adaptation_engine.configure_domain(DomainCategory.MEDICAL, config)
        
        # Verify configuration was stored
        self.assertIn(DomainCategory.MEDICAL, self.adaptation_engine.adaptation_configs)
    
    def test_extract_domain_terms(self):
        """Test domain term extraction"""
        sample_corpus = [
            "Machine learning algorithms use neural networks for pattern recognition.",
            "Deep learning models require large datasets for training and validation.",
            "Natural language processing involves tokenization and embedding techniques."
        ]
        
        terms = self.adaptation_engine._extract_domain_terms(sample_corpus, DomainCategory.TECHNICAL)
        
        self.assertIsInstance(terms, list)
        self.assertGreater(len(terms), 0)
        
        # Check for expected technical terms
        terms_lower = [term.lower() for term in terms]
        self.assertIn('machine learning', terms_lower)
        self.assertIn('neural networks', terms_lower)
    
    def test_score_domain_terms(self):
        """Test domain term scoring"""
        sample_corpus = [
            "Medical diagnosis requires clinical examination and laboratory tests.",
            "Patient care involves treatment planning and medication management."
        ]
        
        terms = ["medical", "diagnosis", "clinical", "patient", "treatment"]
        
        scored_terms = self.adaptation_engine._score_domain_terms(
            terms, sample_corpus, DomainCategory.MEDICAL
        )
        
        self.assertIsInstance(scored_terms, list)
        self.assertGreater(len(scored_terms), 0)
        
        # Verify scoring format
        for term, score in scored_terms:
            self.assertIsInstance(term, str)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_calculate_frequency_score(self):
        """Test frequency score calculation"""
        corpus = ["test word appears multiple times", "test appears again", "word frequency test"]
        
        score = self.adaptation_engine._calculate_frequency_score("test", corpus)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    def test_calculate_domain_relevance(self):
        """Test domain relevance calculation"""
        # Medical term
        medical_score = self.adaptation_engine._calculate_domain_relevance(
            "medical diagnosis", DomainCategory.MEDICAL
        )
        
        # Technical term
        technical_score = self.adaptation_engine._calculate_domain_relevance(
            "algorithm optimization", DomainCategory.TECHNICAL
        )
        
        self.assertIsInstance(medical_score, float)
        self.assertIsInstance(technical_score, float)
        self.assertGreaterEqual(medical_score, 0.0)
        self.assertGreaterEqual(technical_score, 0.0)
    
    def test_is_valid_term(self):
        """Test term validation"""
        # Valid terms
        self.assertTrue(self.adaptation_engine._is_valid_term("machine learning"))
        self.assertTrue(self.adaptation_engine._is_valid_term("algorithm"))
        
        # Invalid terms
        self.assertFalse(self.adaptation_engine._is_valid_term("a"))  # Too short
        self.assertFalse(self.adaptation_engine._is_valid_term("the test"))  # Contains stop word

class TestUserSubmissionWorkflow(unittest.TestCase):
    """Test cases for UserSubmissionWorkflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.vocab_db = VocabularyDatabase(self.temp_db.name)
        self.validator = VocabularyValidator()
        self.workflow = UserSubmissionWorkflow(self.vocab_db, self.validator)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_submit_vocabulary(self):
        """Test vocabulary submission"""
        success, message, entry = self.workflow.submit_vocabulary(
            term="Test Submission",
            definition="A comprehensive test definition for vocabulary submission testing.",
            domain=DomainCategory.TECHNICAL,
            submitter_id="test_user",
            context_examples=["This is a test submission example."],
            alternatives=["Test Entry"],
            tags=["test", "submission"]
        )
        
        self.assertTrue(success)
        self.assertIn("successfully", message.lower())
        self.assertIsNotNone(entry)
        self.assertEqual(entry['term'], "Test Submission")
        self.assertEqual(entry['status'], VocabularyStatus.PENDING.value)
    
    def test_verify_submission(self):
        """Test submission verification"""
        # Submit vocabulary first
        success, message, entry = self.workflow.submit_vocabulary(
            term="Verification Test",
            definition="A test entry for verification workflow testing.",
            domain=DomainCategory.TECHNICAL,
            submitter_id="test_user",
            context_examples=["This is a verification test example."]
        )
        
        self.assertTrue(success)
        
        # Verify the submission
        verify_success = self.workflow.verify_submission(
            entry['id'],
            "test_verifier",
            approved=True,
            notes="Approved for testing"
        )
        
        self.assertTrue(verify_success)
        
        # Check if status was updated
        updated_entry = self.vocab_db.get_entry(entry['id'])
        self.assertEqual(updated_entry.status, VocabularyStatus.APPROVED)
        self.assertEqual(updated_entry.verifier_id, "test_verifier")
    
    def test_get_pending_submissions(self):
        """Test getting pending submissions"""
        # Submit vocabulary
        self.workflow.submit_vocabulary(
            term="Pending Test",
            definition="A test entry that should remain pending.",
            domain=DomainCategory.TECHNICAL,
            submitter_id="test_user",
            context_examples=["This is a pending test example."]
        )
        
        # Get pending submissions
        pending = self.workflow.get_pending_submissions()
        
        self.assertIsInstance(pending, list)
        self.assertGreater(len(pending), 0)
        self.assertEqual(pending[0].status, VocabularyStatus.PENDING)

class TestCustomVocabularySystem(unittest.TestCase):
    """Test cases for the complete CustomVocabularySystem"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.vocab_system = CustomVocabularySystem(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_submit_vocabulary(self):
        """Test vocabulary submission through main system"""
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="System Test",
            definition="A comprehensive test of the vocabulary system functionality.",
            domain="technical",
            submitter_id="system_test_user",
            context_examples=["This is a system test example."],
            alternatives=["System Testing"],
            tags=["system", "test"]
        )
        
        self.assertTrue(success)
        self.assertIn("successfully", message.lower())
        self.assertIsNotNone(entry)
    
    def test_verify_vocabulary(self):
        """Test vocabulary verification through main system"""
        # Submit first
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="Verify Test",
            definition="A test entry for system verification testing.",
            domain="technical",
            submitter_id="test_user",
            context_examples=["This is a verification system test."]
        )
        
        self.assertTrue(success)
        
        # Verify
        verify_success = self.vocab_system.verify_vocabulary(
            entry['id'],
            "system_verifier",
            approved=True,
            notes="System verification test"
        )
        
        self.assertTrue(verify_success)
    
    def test_search_vocabulary(self):
        """Test vocabulary search through main system"""
        # Submit and approve vocabulary first
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="Search Test",
            definition="A test entry for search functionality testing.",
            domain="technical",
            submitter_id="test_user",
            context_examples=["This is a search test example."]
        )
        
        self.assertTrue(success)
        
        # Approve it
        self.vocab_system.verify_vocabulary(entry['id'], "verifier", True)
        
        # Search
        results = self.vocab_system.search_vocabulary("Search", domain="technical")
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['term'], "Search Test")
    
    def test_get_domain_vocabulary(self):
        """Test getting domain vocabulary"""
        # Submit and approve vocabulary
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="Domain Test",
            definition="A test entry for domain vocabulary testing.",
            domain="medical",
            submitter_id="test_user",
            context_examples=["This is a domain test example."]
        )
        
        self.assertTrue(success)
        self.vocab_system.verify_vocabulary(entry['id'], "verifier", True)
        
        # Get domain vocabulary
        domain_vocab = self.vocab_system.get_domain_vocabulary("medical")
        
        self.assertIsInstance(domain_vocab, list)
        self.assertGreater(len(domain_vocab), 0)
        self.assertEqual(domain_vocab[0]['domain'], "medical")
    
    def test_get_pronunciation(self):
        """Test pronunciation generation"""
        ipa, phonetic = self.vocab_system.get_pronunciation("example")
        
        self.assertIsInstance(ipa, str)
        self.assertIsInstance(phonetic, str)
        self.assertGreater(len(ipa), 0)
        self.assertGreater(len(phonetic), 0)
    
    def test_get_pending_submissions(self):
        """Test getting pending submissions"""
        # Submit vocabulary
        self.vocab_system.submit_vocabulary(
            term="Pending System Test",
            definition="A test entry for pending submissions testing.",
            domain="technical",
            submitter_id="test_user",
            context_examples=["This is a pending system test."]
        )
        
        # Get pending
        pending = self.vocab_system.get_pending_submissions()
        
        self.assertIsInstance(pending, list)
        self.assertGreater(len(pending), 0)
    
    def test_update_vocabulary_usage(self):
        """Test vocabulary usage updates"""
        # Submit and approve vocabulary
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="Usage Test",
            definition="A test entry for usage tracking testing.",
            domain="technical",
            submitter_id="test_user",
            context_examples=["This is a usage test example."]
        )
        
        self.assertTrue(success)
        self.vocab_system.verify_vocabulary(entry['id'], "verifier", True)
        
        # Update usage
        self.vocab_system.update_vocabulary_usage(
            entry['id'],
            "test_user",
            "test_context",
            0.9
        )
        
        # Verify usage was updated
        results = self.vocab_system.search_vocabulary("Usage Test")
        self.assertGreater(results[0]['usage_count'], 0)
    
    def test_get_vocabulary_analytics(self):
        """Test vocabulary analytics"""
        # Submit some vocabulary
        for i in range(3):
            success, message, entry = self.vocab_system.submit_vocabulary(
                term=f"Analytics Test {i}",
                definition=f"Test entry {i} for analytics testing.",
                domain="technical",
                submitter_id="test_user",
                context_examples=[f"This is analytics test example {i}."]
            )
            
            if success:
                self.vocab_system.verify_vocabulary(entry['id'], "verifier", True)
        
        # Get analytics
        analytics = self.vocab_system.get_vocabulary_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_entries', analytics)
        self.assertGreater(analytics['total_entries'], 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.vocab_system = CustomVocabularySystem(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_complete_workflow(self):
        """Test complete vocabulary workflow"""
        # 1. Submit vocabulary
        success, message, entry = self.vocab_system.submit_vocabulary(
            term="Integration Test",
            definition="A comprehensive test of the complete vocabulary workflow system.",
            domain="technical",
            submitter_id="integration_user",
            context_examples=[
                "This is an integration test example.",
                "Integration testing ensures all components work together."
            ],
            alternatives=["Complete Test", "Full Test"],
            tags=["integration", "testing", "workflow"],
            source_references=["Integration Testing Guide"]
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(entry)
        
        # 2. Verify submission
        verify_success = self.vocab_system.verify_vocabulary(
            entry['id'],
            "integration_verifier",
            approved=True,
            notes="Integration test approved"
        )
        
        self.assertTrue(verify_success)
        
        # 3. Search for the entry
        search_results = self.vocab_system.search_vocabulary("Integration")
        self.assertGreater(len(search_results), 0)
        self.assertEqual(search_results[0]['term'], "Integration Test")
        
        # 4. Update usage
        self.vocab_system.update_vocabulary_usage(
            entry['id'],
            "integration_user",
            "integration_test",
            0.95
        )
        
        # 5. Check analytics
        analytics = self.vocab_system.get_vocabulary_analytics()
        self.assertGreater(analytics['total_entries'], 0)
        
        # 6. Test pronunciation
        ipa, phonetic = self.vocab_system.get_pronunciation("Integration Test")
        self.assertIsInstance(ipa, str)
        self.assertIsInstance(phonetic, str)

def run_performance_tests():
    """Run performance tests for the system"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    try:
        import time
        
        # Create temporary system
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        vocab_system = CustomVocabularySystem(temp_db.name)
        
        # Test submission performance
        print("\nTesting submission performance...")
        start_time = time.time()
        
        for i in range(10):
            vocab_system.submit_vocabulary(
                term=f"Performance Test {i}",
                definition=f"Performance test entry {i} for measuring system speed and efficiency.",
                domain="technical",
                submitter_id="perf_user",
                context_examples=[f"This is performance test example {i}."]
            )
        
        submission_time = time.time() - start_time
        print(f"  10 submissions: {submission_time:.2f}s ({submission_time/10:.3f}s per submission)")
        
        # Test search performance
        print("\nTesting search performance...")
        start_time = time.time()
        
        for i in range(50):
            vocab_system.search_vocabulary("Performance")
        
        search_time = time.time() - start_time
        print(f"  50 searches: {search_time:.2f}s ({search_time/50:.3f}s per search)")
        
        # Test pronunciation performance
        print("\nTesting pronunciation performance...")
        test_words = ["example", "pronunciation", "performance", "vocabulary", "system"]
        
        start_time = time.time()
        for word in test_words * 10:  # 50 total
            vocab_system.get_pronunciation(word)
        
        pronunciation_time = time.time() - start_time
        print(f"  50 pronunciations: {pronunciation_time:.2f}s ({pronunciation_time/50:.3f}s per pronunciation)")
        
        # Clean up
        os.unlink(temp_db.name)
        
    except Exception as e:
        print(f"Performance tests failed: {e}")

def main():
    """Run all tests"""
    print("🧪 CUSTOM VOCABULARY SYSTEM TESTS")
    print("=" * 60)
    
    # Check if required modules are available
    try:
        import nltk
        import spacy
        import sklearn
        print("✅ All required modules available")
    except ImportError as e:
        print(f"❌ Missing required modules: {e}")
        print("Please install: pip install nltk spacy scikit-learn")
        print("Also run: python -m spacy download en_core_web_sm")
        return
    
    # Run unit tests
    print("\n🔍 Running unit tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestPhoneticTranscriber,
        TestVocabularyValidator,
        TestVocabularyDatabase,
        TestDomainAdaptationEngine,
        TestUserSubmissionWorkflow,
        TestCustomVocabularySystem,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    # Run performance tests
    run_performance_tests()
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()