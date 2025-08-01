#!/usr/bin/env python3
"""
Comprehensive tests for semantic search functionality
"""

import pytest
import asyncio
import tempfile
import os
import shutil
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

from semantic_search.providers import OpenAIEmbeddingProvider, SentenceTransformerProvider, MockEmbeddingProvider
from semantic_search.embeddings import EmbeddingManager
from semantic_search.transcript_embeddings import TranscriptEmbeddingManager, TranscriptChunk, SimilarTranscript
from semantic_search.semantic_engine import SemanticSearchEngine, SemanticSearchResult


class TestEmbeddingProviders:
    """Test embedding providers"""
    
    def test_mock_provider(self):
        """Test mock embedding provider"""
        provider = MockEmbeddingProvider(dimension=384)
        
        # Test basic functionality
        assert provider.get_embedding_dimension() == 384
        assert provider.get_model_name() == "mock-embeddings"
        
        # Test embedding generation
        texts = ["Hello world", "This is a test", "Machine learning"]
        embeddings = provider.generate_embeddings(texts)
        
        assert embeddings.shape == (3, 384)
        assert np.allclose(np.linalg.norm(embeddings, axis=1), 1.0)  # Unit vectors
    
    def test_mock_provider_empty_input(self):
        """Test mock provider with empty input"""
        provider = MockEmbeddingProvider()
        embeddings = provider.generate_embeddings([])
        assert embeddings.shape == (0,)
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OpenAI API key not available")
    def test_openai_provider(self):
        """Test OpenAI embedding provider (requires API key)"""
        provider = OpenAIEmbeddingProvider()
        
        assert provider.get_embedding_dimension() == 1536
        assert provider.get_model_name() == "text-embedding-ada-002"
        
        # Test with small input to avoid API costs
        texts = ["Hello world"]
        embeddings = provider.generate_embeddings(texts)
        
        assert embeddings.shape == (1, 1536)
    
    def test_sentence_transformer_provider(self):
        """Test SentenceTransformer provider"""
        try:
            provider = SentenceTransformerProvider()
            
            assert provider.get_embedding_dimension() > 0
            assert "MiniLM" in provider.get_model_name()
            
            texts = ["Hello world", "This is a test"]
            embeddings = provider.generate_embeddings(texts)
            
            assert embeddings.shape[0] == 2
            assert embeddings.shape[1] == provider.get_embedding_dimension()
            
        except Exception as e:
            pytest.skip(f"SentenceTransformer not available: {e}")


class TestEmbeddingManager:
    """Test embedding manager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.provider = MockEmbeddingProvider(dimension=128)
        self.manager = EmbeddingManager(
            self.provider,
            cache_dir=os.path.join(self.temp_dir, "embeddings")
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_embedding_generation(self):
        """Test basic embedding generation"""
        texts = ["Hello world", "This is a test", "Machine learning"]
        embeddings = self.manager.get_embeddings(texts)
        
        assert embeddings.shape == (3, 128)
        assert np.allclose(np.linalg.norm(embeddings, axis=1), 1.0)
    
    def test_embedding_caching(self):
        """Test embedding caching functionality"""
        texts = ["Hello world", "This is a test"]
        
        # First call should generate embeddings
        embeddings1 = self.manager.get_embeddings(texts, use_cache=True)
        
        # Second call should use cache
        embeddings2 = self.manager.get_embeddings(texts, use_cache=True)
        
        np.testing.assert_array_equal(embeddings1, embeddings2)
    
    def test_similarity_computation(self):
        """Test similarity computation"""
        embedding1 = np.array([1.0, 0.0, 0.0])
        embedding2 = np.array([0.0, 1.0, 0.0])
        embedding3 = np.array([1.0, 0.0, 0.0])
        
        # Test cosine similarity
        sim1 = self.manager.compute_similarity(embedding1, embedding2, "cosine")
        sim2 = self.manager.compute_similarity(embedding1, embedding3, "cosine")
        
        assert abs(sim1 - 0.0) < 1e-6  # Orthogonal vectors
        assert abs(sim2 - 1.0) < 1e-6  # Identical vectors
    
    def test_find_similar(self):
        """Test finding similar embeddings"""
        # Create test embeddings
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.9, 0.1, 0.0],  # Similar to first
            [0.0, 0.0, 1.0]
        ])
        
        query_embedding = np.array([1.0, 0.0, 0.0])
        
        similar = self.manager.find_similar(query_embedding, embeddings, top_k=2)
        
        assert len(similar) == 2
        assert similar[0][0] == 0  # First embedding (identical)
        assert similar[1][0] == 2  # Third embedding (similar)
        assert similar[0][1] > similar[1][1]  # Sorted by similarity


class TestTranscriptEmbeddingManager:
    """Test transcript embedding manager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_embeddings.db")
        self.provider = MockEmbeddingProvider(dimension=128)
        self.manager = TranscriptEmbeddingManager(
            embedding_provider=self.provider,
            db_path=self.db_path,
            chunk_size=50,  # Small chunks for testing
            chunk_overlap=10
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_transcript_indexing(self):
        """Test transcript indexing"""
        transcript_id = "test_001"
        title = "Test Transcript"
        content = "This is a test transcript with some content. " * 20  # Long enough to create multiple chunks
        
        success = self.manager.index_transcript(transcript_id, title, content)
        assert success
        
        # Check database
        stats = self.manager.get_stats()
        assert stats['total_transcripts'] == 1
        assert stats['total_chunks'] > 1  # Should create multiple chunks
    
    def test_chunking(self):
        """Test transcript chunking"""
        transcript_id = "test_001"
        content = " ".join([f"word{i}" for i in range(100)])  # 100 words
        
        chunks = self.manager._chunk_transcript(transcript_id, content)
        
        assert len(chunks) > 1  # Should create multiple chunks
        
        # Check chunk properties
        for chunk in chunks:
            assert chunk.transcript_id == transcript_id
            assert len(chunk.text.split()) <= 50  # Chunk size limit
            assert chunk.start_pos < chunk.end_pos
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        # Index test transcripts
        transcripts = [
            ("trans_1", "Meeting Notes", "We discussed the project timeline and budget constraints."),
            ("trans_2", "Interview", "The candidate has strong technical skills in machine learning."),
            ("trans_3", "Lecture", "Today we'll cover supervised learning algorithms and their applications.")
        ]
        
        for tid, title, content in transcripts:
            self.manager.index_transcript(tid, title, content)
        
        # Search for similar content
        results = self.manager.search_similar_transcripts(
            "machine learning algorithms", limit=5, min_similarity=0.0
        )
        
        assert len(results) > 0
        assert all(isinstance(r, SimilarTranscript) for r in results)
        assert all(r.similarity_score >= 0 for r in results)
    
    def test_similarity_search(self):
        """Test finding similar transcripts"""
        # Index test transcripts
        transcripts = [
            ("trans_1", "Meeting A", "We discussed project deadlines and resource allocation."),
            ("trans_2", "Meeting B", "The team talked about project timelines and budget planning."),
            ("trans_3", "Interview", "The candidate demonstrated excellent programming skills.")
        ]
        
        for tid, title, content in transcripts:
            self.manager.index_transcript(tid, title, content)
        
        # Find similar to first transcript
        results = self.manager.find_similar_content("trans_1", limit=5, min_similarity=0.0)
        
        assert len(results) > 0
        # Should not include the reference transcript itself
        assert all(r.transcript_id != "trans_1" for r in results)
    
    def test_recommendations(self):
        """Test content recommendations"""
        # Index test transcripts
        transcripts = [
            ("trans_1", "Tech Meeting", "We discussed API development and database optimization."),
            ("trans_2", "Code Review", "The team reviewed the authentication system implementation."),
            ("trans_3", "Marketing", "We planned the product launch campaign and social media strategy."),
            ("trans_4", "Development", "The developers worked on API endpoints and database queries.")
        ]
        
        for tid, title, content in transcripts:
            self.manager.index_transcript(tid, title, content)
        
        # Get recommendations based on tech-related history
        user_history = ["trans_1", "trans_2"]
        results = self.manager.get_content_recommendations(user_history, limit=5)
        
        assert len(results) > 0
        # Should not include transcripts from history
        assert all(r.transcript_id not in user_history for r in results)
    
    def test_transcript_deletion(self):
        """Test transcript deletion"""
        transcript_id = "test_delete"
        title = "Delete Test"
        content = "This transcript will be deleted."
        
        # Index transcript
        success = self.manager.index_transcript(transcript_id, title, content)
        assert success
        
        # Verify it exists
        stats_before = self.manager.get_stats()
        assert stats_before['total_transcripts'] == 1
        
        # Delete transcript
        success = self.manager.delete_transcript(transcript_id)
        assert success
        
        # Verify it's gone
        stats_after = self.manager.get_stats()
        assert stats_after['total_transcripts'] == 0


class TestSemanticSearchEngine:
    """Test semantic search engine"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_engine.db")
        
        provider = MockEmbeddingProvider(dimension=128)
        self.embedding_manager = TranscriptEmbeddingManager(
            embedding_provider=provider,
            db_path=self.db_path,
            chunk_size=30
        )
        self.engine = SemanticSearchEngine(self.embedding_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search functionality"""
        # Index test transcripts
        await self.engine.index_transcript(
            "test_1", "Technical Discussion", 
            "We talked about machine learning algorithms and data preprocessing techniques."
        )
        await self.engine.index_transcript(
            "test_2", "Business Meeting", 
            "The team discussed quarterly sales targets and marketing strategies."
        )
        
        # Perform semantic search
        results = await self.engine.semantic_search("machine learning", limit=5)
        
        assert len(results) > 0
        assert all(isinstance(r, SemanticSearchResult) for r in results)
        assert all(r.search_type == 'semantic' for r in results)
    
    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test similarity search"""
        # Index test transcripts
        transcripts = [
            ("ref_1", "Reference", "This is about project management and team coordination."),
            ("sim_1", "Similar", "We discussed project planning and team collaboration."),
            ("diff_1", "Different", "The weather was nice and we went for a walk.")
        ]
        
        for tid, title, content in transcripts:
            await self.engine.index_transcript(tid, title, content)
        
        # Find similar transcripts
        results = await self.engine.find_similar_transcripts("ref_1", limit=5)
        
        assert len(results) > 0
        assert all(r.transcript_id != "ref_1" for r in results)  # Exclude reference
    
    @pytest.mark.asyncio
    async def test_recommendations(self):
        """Test recommendation system"""
        # Index test transcripts
        transcripts = [
            ("hist_1", "History 1", "Machine learning and artificial intelligence research."),
            ("hist_2", "History 2", "Deep learning models and neural network architectures."),
            ("rec_1", "Recommendation", "Computer vision and image processing algorithms."),
            ("unrel_1", "Unrelated", "Cooking recipes and kitchen techniques.")
        ]
        
        for tid, title, content in transcripts:
            await self.engine.index_transcript(tid, title, content)
        
        # Get recommendations
        user_history = ["hist_1", "hist_2"]
        results = await self.engine.get_recommendations(user_history, limit=5)
        
        assert len(results) > 0
        assert all(r.transcript_id not in user_history for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_indexing(self):
        """Test batch indexing functionality"""
        transcripts = [
            {
                'id': 'batch_1',
                'title': 'Batch Test 1',
                'content': 'This is the first batch test transcript.',
                'metadata': {'type': 'test'}
            },
            {
                'id': 'batch_2',
                'title': 'Batch Test 2',
                'content': 'This is the second batch test transcript.',
                'metadata': {'type': 'test'}
            }
        ]
        
        results = await self.engine.batch_index_transcripts(transcripts)
        
        assert len(results) == 2
        assert all(success for success in results.values())
        
        # Verify indexing
        stats = self.engine.get_search_stats()
        assert stats['semantic_search_enabled']
        assert stats['embedding_stats']['total_transcripts'] == 2
    
    @pytest.mark.asyncio
    async def test_within_transcript_search(self):
        """Test searching within a specific transcript"""
        transcript_content = """
        This transcript contains multiple topics. First, we discuss machine learning algorithms
        and their applications in data science. Then we move on to discuss web development
        frameworks and database optimization techniques. Finally, we cover project management
        methodologies and team collaboration strategies.
        """
        
        await self.engine.index_transcript("multi_topic", "Multi-topic Discussion", transcript_content)
        
        # Search within the transcript
        results = await self.engine.search_within_transcript("multi_topic", "machine learning", limit=3)
        
        assert len(results) > 0
        assert all('similarity' in result for result in results)
        assert all('text' in result for result in results)
    
    def test_search_stats(self):
        """Test search statistics"""
        stats = self.engine.get_search_stats()
        
        assert 'semantic_search_enabled' in stats
        assert 'embedding_stats' in stats
        assert 'search_capabilities' in stats
        
        capabilities = stats['search_capabilities']
        expected_capabilities = [
            'semantic_search',
            'similarity_search', 
            'content_recommendations',
            'hybrid_search'
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities


class TestIntegration:
    """Integration tests for the complete semantic search system"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "integration_test.db")
        
        # Use mock provider for consistent testing
        provider = MockEmbeddingProvider(dimension=256)
        self.embedding_manager = TranscriptEmbeddingManager(
            embedding_provider=provider,
            db_path=self.db_path
        )
        self.engine = SemanticSearchEngine(self.embedding_manager)
    
    def teardown_method(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete semantic search workflow"""
        # Step 1: Index multiple transcripts
        transcripts = [
            {
                'id': 'meeting_001',
                'title': 'Team Meeting - Q1 Planning',
                'content': 'We discussed quarterly goals, budget allocation, and team assignments for the upcoming projects.',
                'metadata': {'type': 'meeting', 'quarter': 'Q1'}
            },
            {
                'id': 'interview_001', 
                'title': 'Technical Interview - Senior Developer',
                'content': 'The candidate demonstrated strong skills in Python, machine learning, and system design.',
                'metadata': {'type': 'interview', 'position': 'senior_developer'}
            },
            {
                'id': 'lecture_001',
                'title': 'Introduction to Data Science',
                'content': 'Today we covered statistical analysis, data visualization, and machine learning fundamentals.',
                'metadata': {'type': 'lecture', 'subject': 'data_science'}
            }
        ]
        
        # Batch index
        index_results = await self.engine.batch_index_transcripts(transcripts)
        assert all(success for success in index_results.values())
        
        # Step 2: Perform semantic search
        search_results = await self.engine.semantic_search("machine learning", limit=5)
        assert len(search_results) > 0
        
        # Should find relevant transcripts
        relevant_ids = [r.transcript_id for r in search_results]
        assert 'interview_001' in relevant_ids or 'lecture_001' in relevant_ids
        
        # Step 3: Find similar transcripts
        similar_results = await self.engine.find_similar_transcripts('interview_001', limit=3)
        assert len(similar_results) > 0
        assert all(r.transcript_id != 'interview_001' for r in similar_results)
        
        # Step 4: Get recommendations
        user_history = ['meeting_001']
        recommendations = await self.engine.get_recommendations(user_history, limit=3)
        assert len(recommendations) > 0
        assert all(r.transcript_id not in user_history for r in recommendations)
        
        # Step 5: Verify statistics
        stats = self.engine.get_search_stats()
        assert stats['semantic_search_enabled']
        assert stats['embedding_stats']['total_transcripts'] == 3
        
        # Step 6: Test deletion
        delete_success = await self.engine.delete_transcript('meeting_001')
        assert delete_success
        
        # Verify deletion
        final_stats = self.engine.get_search_stats()
        assert final_stats['embedding_stats']['total_transcripts'] == 2


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()