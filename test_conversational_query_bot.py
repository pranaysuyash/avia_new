#!/usr/bin/env python3
"""
Test suite for Conversational Query Bot
Comprehensive testing of RAG functionality, vector search, and conversation management
"""

import unittest
import tempfile
import os
import json
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from conversational_query_bot import (
    ConversationalQueryBot, MediaContent, QueryResult, ConversationContext,
    EmbeddingManager, VectorDatabase
)

class TestEmbeddingManager(unittest.TestCase):
    """Test cases for EmbeddingManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.embedding_manager = EmbeddingManager()
    
    def test_initialization(self):
        """Test embedding manager initialization"""
        self.assertIsNotNone(self.embedding_manager)
        self.assertEqual(self.embedding_manager.dimension, 384)
    
    def test_encode_text(self):
        """Test text encoding"""
        text = "This is a test sentence"
        embedding = self.embedding_manager.encode_text(text)
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))
        self.assertEqual(embedding.dtype, np.float32)
    
    def test_encode_batch(self):
        """Test batch text encoding"""
        texts = ["First sentence", "Second sentence", "Third sentence"]
        embeddings = self.embedding_manager.encode_batch(texts)
        
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape, (3, 384))
        self.assertEqual(embeddings.dtype, np.float32)
    
    def test_encode_empty_text(self):
        """Test encoding empty text"""
        embedding = self.embedding_manager.encode_text("")
        
        self.assertIsInstance(embedding, np.ndarray)
        self.assertEqual(embedding.shape, (384,))

class TestVectorDatabase(unittest.TestCase):
    """Test cases for VectorDatabase"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.vector_db = VectorDatabase(dimension=384)
        
        # Create sample content
        self.sample_content = MediaContent(
            id="test_001",
            title="Test Content",
            content_type="transcript",
            text_content="This is test content for vector database testing"
        )
    
    def test_initialization(self):
        """Test vector database initialization"""
        self.assertEqual(self.vector_db.dimension, 384)
        self.assertEqual(self.vector_db.next_id, 0)
        self.assertEqual(len(self.vector_db.content_map), 0)
    
    def test_add_content(self):
        """Test adding content to vector database"""
        embedding = np.random.random(384).astype(np.float32)
        content_id = self.vector_db.add_content(self.sample_content, embedding)
        
        self.assertEqual(content_id, 0)
        self.assertEqual(self.vector_db.next_id, 1)
        self.assertIn(0, self.vector_db.content_map)
        self.assertEqual(self.vector_db.content_map[0], self.sample_content)
    
    def test_search(self):
        """Test vector search functionality"""
        # Add multiple content items
        embeddings = []
        for i in range(3):
            content = MediaContent(
                id=f"test_{i:03d}",
                title=f"Test Content {i}",
                content_type="transcript",
                text_content=f"This is test content number {i}"
            )
            embedding = np.random.random(384).astype(np.float32)
            embeddings.append(embedding)
            self.vector_db.add_content(content, embedding)
        
        # Search with similar embedding
        query_embedding = embeddings[0] + np.random.normal(0, 0.1, 384).astype(np.float32)
        results = self.vector_db.search(query_embedding, k=2)
        
        self.assertLessEqual(len(results), 2)
        for content, score in results:
            self.assertIsInstance(content, MediaContent)
            self.assertIsInstance(score, float)
    
    def test_get_stats(self):
        """Test getting database statistics"""
        # Add some content
        embedding = np.random.random(384).astype(np.float32)
        self.vector_db.add_content(self.sample_content, embedding)
        
        stats = self.vector_db.get_stats()
        
        self.assertIn("total_documents", stats)
        self.assertIn("dimension", stats)
        self.assertIn("content_types", stats)
        self.assertEqual(stats["total_documents"], 1)
        self.assertEqual(stats["dimension"], 384)

class TestMediaContent(unittest.TestCase):
    """Test cases for MediaContent dataclass"""
    
    def test_creation(self):
        """Test MediaContent creation"""
        content = MediaContent(
            id="test_001",
            title="Test Content",
            content_type="transcript",
            text_content="Test content text",
            timestamp=120.5,
            speaker="John Doe"
        )
        
        self.assertEqual(content.id, "test_001")
        self.assertEqual(content.title, "Test Content")
        self.assertEqual(content.content_type, "transcript")
        self.assertEqual(content.text_content, "Test content text")
        self.assertEqual(content.timestamp, 120.5)
        self.assertEqual(content.speaker, "John Doe")
        self.assertIsInstance(content.created_at, datetime)
    
    def test_creation_with_defaults(self):
        """Test MediaContent creation with default values"""
        content = MediaContent(
            id="test_002",
            title="Test Content",
            content_type="document",
            text_content="Test content text"
        )
        
        self.assertIsNone(content.timestamp)
        self.assertIsNone(content.speaker)
        self.assertIsNone(content.file_path)
        self.assertIsNone(content.metadata)
        self.assertIsInstance(content.created_at, datetime)

class TestConversationalQueryBot(unittest.TestCase):
    """Test cases for ConversationalQueryBot"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize bot with temporary database
        self.bot = ConversationalQueryBot(db_path=self.temp_db.name)
        
        # Create sample content
        self.sample_contents = [
            MediaContent(
                id="test_001",
                title="Team Meeting",
                content_type="transcript",
                text_content="We discussed the budget allocation for Q4. The marketing team needs additional funding for the new campaign.",
                timestamp=60.0,
                speaker="Alice"
            ),
            MediaContent(
                id="test_002",
                title="Product Requirements",
                content_type="document",
                text_content="The new feature should include user authentication, data encryption, and real-time notifications."
            ),
            MediaContent(
                id="test_003",
                title="Customer Interview",
                content_type="transcript",
                text_content="The customer mentioned that they love the current interface but would like better mobile support.",
                timestamp=180.5,
                speaker="Customer"
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """Test bot initialization"""
        self.assertIsInstance(self.bot, ConversationalQueryBot)
        self.assertIsInstance(self.bot.embedding_manager, EmbeddingManager)
        self.assertIsInstance(self.bot.vector_db, VectorDatabase)
        self.assertEqual(self.bot.db_path, self.temp_db.name)
    
    def test_add_content(self):
        """Test adding content to the bot"""
        content = self.sample_contents[0]
        result = self.bot.add_content(content)
        
        self.assertTrue(result)
        
        # Verify content was added to vector database
        stats = self.bot.get_statistics()
        self.assertEqual(stats['vector_database']['total_documents'], 1)
    
    def test_add_multiple_content(self):
        """Test adding multiple content items"""
        for content in self.sample_contents:
            result = self.bot.add_content(content)
            self.assertTrue(result)
        
        stats = self.bot.get_statistics()
        self.assertEqual(stats['vector_database']['total_documents'], 3)
    
    def test_query_basic(self):
        """Test basic query functionality"""
        # Add content
        for content in self.sample_contents:
            self.bot.add_content(content)
        
        # Query
        results = self.bot.query("budget allocation", max_results=5)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        for result in results:
            self.assertIsInstance(result, QueryResult)
            self.assertIsInstance(result.content, MediaContent)
            self.assertIsInstance(result.relevance_score, float)
            self.assertIsInstance(result.snippet, str)
    
    def test_query_with_conversation(self):
        """Test query with conversation context"""
        # Add content
        for content in self.sample_contents:
            self.bot.add_content(content)
        
        conversation_id = "test_conversation"
        
        # First query
        results1 = self.bot.query("budget", conversation_id=conversation_id)
        self.assertGreater(len(results1), 0)
        
        # Second query in same conversation
        results2 = self.bot.query("marketing", conversation_id=conversation_id)
        self.assertGreater(len(results2), 0)
        
        # Check conversation context
        context = self.bot.get_conversation_history(conversation_id)
        self.assertIsInstance(context, ConversationContext)
        self.assertEqual(len(context.query_history), 2)
        self.assertEqual(len(context.result_history), 2)
    
    def test_query_with_content_type_filter(self):
        """Test query with content type filtering"""
        # Add content
        for content in self.sample_contents:
            self.bot.add_content(content)
        
        # Query only transcripts
        results = self.bot.query(
            "customer", 
            content_types=["transcript"],
            max_results=5
        )
        
        self.assertGreater(len(results), 0)
        
        for result in results:
            self.assertEqual(result.content.content_type, "transcript")
    
    def test_generate_answer(self):
        """Test answer generation"""
        # Add content
        for content in self.sample_contents:
            self.bot.add_content(content)
        
        # Query and generate answer
        results = self.bot.query("budget allocation")
        answer = self.bot.generate_answer("What about budget allocation?", results)
        
        self.assertIsInstance(answer, str)
        self.assertGreater(len(answer), 0)
        self.assertIn("Based on your media library", answer)
    
    def test_generate_answer_no_results(self):
        """Test answer generation with no results"""
        answer = self.bot.generate_answer("test query", [])
        
        self.assertIsInstance(answer, str)
        self.assertIn("couldn't find any relevant information", answer)
    
    def test_get_statistics(self):
        """Test getting system statistics"""
        # Add content and perform queries
        for content in self.sample_contents:
            self.bot.add_content(content)
        
        self.bot.query("test query 1")
        self.bot.query("test query 2")
        
        stats = self.bot.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("content_statistics", stats)
        self.assertIn("total_queries", stats)
        self.assertIn("average_processing_time", stats)
        self.assertIn("active_conversations", stats)
        self.assertIn("vector_database", stats)
        
        self.assertEqual(stats["total_queries"], 2)
    
    def test_clear_conversation(self):
        """Test clearing conversation history"""
        conversation_id = "test_conversation"
        
        # Create conversation
        self.bot.query("test", conversation_id=conversation_id)
        self.assertIn(conversation_id, self.bot.conversations)
        
        # Clear conversation
        result = self.bot.clear_conversation(conversation_id)
        self.assertTrue(result)
        self.assertNotIn(conversation_id, self.bot.conversations)
        
        # Try to clear non-existent conversation
        result = self.bot.clear_conversation("non_existent")
        self.assertFalse(result)
    
    def test_context_window_generation(self):
        """Test context window generation"""
        content = MediaContent(
            id="test_context",
            title="Long Content",
            content_type="transcript",
            text_content="This is a very long piece of content that contains multiple sentences and should be used to test the context window generation functionality. The budget allocation was discussed in detail during the meeting."
        )
        
        context_window = self.bot._generate_context_window(content, "budget allocation")
        
        self.assertIsInstance(context_window, str)
        self.assertIn("budget allocation", context_window.lower())
    
    def test_database_persistence(self):
        """Test database persistence"""
        # Add content
        content = self.sample_contents[0]
        self.bot.add_content(content)
        
        # Create new bot instance with same database
        new_bot = ConversationalQueryBot(db_path=self.temp_db.name)
        
        # Check that content was loaded
        stats = new_bot.get_statistics()
        self.assertEqual(stats['vector_database']['total_documents'], 1)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with invalid content
        invalid_content = MediaContent(
            id="",  # Empty ID
            title="",  # Empty title
            content_type="invalid_type",
            text_content=""  # Empty content
        )
        
        # Should handle gracefully
        result = self.bot.add_content(invalid_content)
        self.assertIsInstance(result, bool)
        
        # Test query with empty string
        results = self.bot.query("")
        self.assertIsInstance(results, list)
        
        # Test with very long query
        long_query = "test " * 1000
        results = self.bot.query(long_query)
        self.assertIsInstance(results, list)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.bot = ConversationalQueryBot(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # 1. Add diverse content
        contents = [
            MediaContent(
                id="meeting_001",
                title="Q4 Planning Meeting",
                content_type="transcript",
                text_content="We need to increase our marketing budget by 25% for Q4. The sales team reported strong performance in the enterprise segment.",
                timestamp=120.0,
                speaker="CEO"
            ),
            MediaContent(
                id="doc_001",
                title="Marketing Strategy",
                content_type="document",
                text_content="Our marketing strategy focuses on digital channels, content marketing, and customer retention programs. Budget allocation should prioritize high-ROI activities."
            ),
            MediaContent(
                id="interview_001",
                title="Customer Feedback",
                content_type="transcript",
                text_content="Customers appreciate our product quality but want better customer support and faster response times.",
                timestamp=300.5,
                speaker="Customer"
            )
        ]
        
        for content in contents:
            result = self.bot.add_content(content)
            self.assertTrue(result)
        
        # 2. Perform conversational queries
        conversation_id = "integration_test"
        
        # Query about budget
        budget_results = self.bot.query(
            "What did we discuss about budget?",
            conversation_id=conversation_id
        )
        self.assertGreater(len(budget_results), 0)
        
        # Follow-up query about marketing
        marketing_results = self.bot.query(
            "Tell me about marketing strategy",
            conversation_id=conversation_id
        )
        self.assertGreater(len(marketing_results), 0)
        
        # Query about customer feedback
        customer_results = self.bot.query(
            "What do customers think?",
            conversation_id=conversation_id
        )
        self.assertGreater(len(customer_results), 0)
        
        # 3. Generate answers
        for results in [budget_results, marketing_results, customer_results]:
            answer = self.bot.generate_answer("test query", results)
            self.assertIsInstance(answer, str)
            self.assertGreater(len(answer), 0)
        
        # 4. Check conversation context
        context = self.bot.get_conversation_history(conversation_id)
        self.assertIsInstance(context, ConversationContext)
        self.assertEqual(len(context.query_history), 3)
        
        # 5. Verify statistics
        stats = self.bot.get_statistics()
        self.assertEqual(stats["total_queries"], 3)
        self.assertEqual(stats["active_conversations"], 1)
        self.assertEqual(stats["vector_database"]["total_documents"], 3)
        
        # 6. Test content type filtering
        transcript_results = self.bot.query(
            "customer feedback",
            content_types=["transcript"]
        )
        
        for result in transcript_results:
            self.assertEqual(result.content.content_type, "transcript")
        
        # 7. Test timestamp citations
        for result in transcript_results:
            if result.content.timestamp:
                self.assertIsNotNone(result.timestamp_citation)
                self.assertIn(":", result.timestamp_citation)

def run_tests():
    """Run all tests"""
    print("🧪 Running Conversational Query Bot Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestEmbeddingManager,
        TestVectorDatabase,
        TestMediaContent,
        TestConversationalQueryBot,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"🎯 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            error_lines = traceback.split('\n')
            error_msg = error_lines[-2] if len(error_lines) >= 2 else str(traceback)
            print(f"   - {test}: {error_msg}")
    
    if not result.failures and not result.errors:
        print("✅ All tests passed successfully!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)