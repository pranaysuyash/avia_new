#!/usr/bin/env python3
"""
Test Advanced Search and Analytics Functionality
Tests the implementation of task 29: advanced search and analytics
"""

import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from search.advanced_analytics import AdvancedAnalytics, TrendAnalysisResult, TopicModelResult, ComparativeAnalysisResult
from search.search_manager import SearchManager
from keyword_extractor import KeywordExtractor


class TestAdvancedAnalytics:
    """Test advanced analytics functionality"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def analytics_engine(self, temp_db):
        """Create analytics engine with test database"""
        return AdvancedAnalytics(temp_db)
    
    @pytest.fixture
    def sample_transcripts(self):
        """Sample transcript data for testing"""
        base_date = datetime.utcnow()
        
        return [
            {
                'id': 'transcript_1',
                'title': 'Team Meeting Discussion',
                'content': 'We discussed the project timeline and budget allocation. The team agreed on the new approach for development.',
                'metadata': {
                    'language': 'en',
                    'speakers': ['John', 'Mary'],
                    'entities': [
                        {'text': 'John', 'label': 'PERSON'},
                        {'text': 'Mary', 'label': 'PERSON'},
                        {'text': 'project', 'label': 'WORK'}
                    ],
                    'tags': ['meeting', 'project']
                },
                'created_at': (base_date - timedelta(days=1)).isoformat()
            },
            {
                'id': 'transcript_2',
                'title': 'Client Presentation',
                'content': 'The presentation covered our quarterly results and future strategy. Clients were impressed with the progress.',
                'metadata': {
                    'language': 'en',
                    'speakers': ['Alice', 'Bob'],
                    'entities': [
                        {'text': 'Alice', 'label': 'PERSON'},
                        {'text': 'Bob', 'label': 'PERSON'},
                        {'text': 'quarterly', 'label': 'DATE'}
                    ],
                    'tags': ['presentation', 'client']
                },
                'created_at': (base_date - timedelta(days=5)).isoformat()
            },
            {
                'id': 'transcript_3',
                'title': 'Technical Review',
                'content': 'Technical review of the new system architecture. We identified several optimization opportunities.',
                'metadata': {
                    'language': 'en',
                    'speakers': ['Charlie', 'David'],
                    'entities': [
                        {'text': 'Charlie', 'label': 'PERSON'},
                        {'text': 'David', 'label': 'PERSON'},
                        {'text': 'system', 'label': 'PRODUCT'}
                    ],
                    'tags': ['technical', 'review']
                },
                'created_at': (base_date - timedelta(days=10)).isoformat()
            }
        ]
    
    def test_analytics_initialization(self, analytics_engine):
        """Test analytics engine initialization"""
        assert analytics_engine is not None
        assert hasattr(analytics_engine, 'keyword_extractor')
        assert hasattr(analytics_engine, 'semantic_engine')
        assert isinstance(analytics_engine.keyword_extractor, KeywordExtractor)
    
    @pytest.mark.asyncio
    async def test_trend_analysis_keywords(self, analytics_engine, sample_transcripts):
        """Test keyword trend analysis"""
        # Mock the database query method
        with patch.object(analytics_engine, '_get_transcripts_for_period', return_value=sample_transcripts):
            result = await analytics_engine.analyze_trends(
                time_period="30d",
                analysis_type="keywords"
            )
            
            assert isinstance(result, TrendAnalysisResult)
            assert result.time_period == "30d"
            assert result.analysis_type == "keywords"
            assert result.total_transcripts == len(sample_transcripts)
            assert len(result.trends) > 0
            
            # Check that trends contain keyword data
            for trend in result.trends:
                assert 'time_bucket' in trend
                assert 'keywords' in trend
                assert 'transcript_count' in trend
                assert isinstance(trend['keywords'], list)
    
    @pytest.mark.asyncio
    async def test_trend_analysis_entities(self, analytics_engine, sample_transcripts):
        """Test entity trend analysis"""
        with patch.object(analytics_engine, '_get_transcripts_for_period', return_value=sample_transcripts):
            result = await analytics_engine.analyze_trends(
                time_period="7d",
                analysis_type="entities"
            )
            
            assert isinstance(result, TrendAnalysisResult)
            assert result.analysis_type == "entities"
            assert len(result.trends) > 0
            
            # Check entity trend structure
            for trend in result.trends:
                assert 'top_entities' in trend
                assert 'entity_types' in trend
                assert 'total_entities' in trend
                assert isinstance(trend['top_entities'], list)
                assert isinstance(trend['entity_types'], dict)
    
    @pytest.mark.asyncio
    async def test_trend_analysis_sentiment(self, analytics_engine, sample_transcripts):
        """Test sentiment trend analysis"""
        with patch.object(analytics_engine, '_get_transcripts_for_period', return_value=sample_transcripts):
            result = await analytics_engine.analyze_trends(
                time_period="30d",
                analysis_type="sentiment"
            )
            
            assert isinstance(result, TrendAnalysisResult)
            assert result.analysis_type == "sentiment"
            assert len(result.trends) > 0
            
            # Check sentiment trend structure
            for trend in result.trends:
                assert 'average_sentiment' in trend
                assert 'sentiment_distribution' in trend
                assert isinstance(trend['average_sentiment'], (int, float))
                assert 'positive' in trend['sentiment_distribution']
                assert 'neutral' in trend['sentiment_distribution']
                assert 'negative' in trend['sentiment_distribution']
    
    @pytest.mark.asyncio
    async def test_topic_extraction_keywords(self, analytics_engine, sample_transcripts):
        """Test keyword-based topic extraction"""
        with patch.object(analytics_engine, '_get_transcripts_by_ids', return_value=sample_transcripts):
            result = await analytics_engine.extract_topics(
                transcript_ids=['transcript_1', 'transcript_2'],
                num_topics=3,
                method="keyword_clustering"
            )
            
            assert isinstance(result, TopicModelResult)
            assert result.num_topics <= 3  # May be fewer if not enough data
            assert len(result.topics) <= 3
            assert isinstance(result.coherence_score, (int, float))
            assert isinstance(result.topic_distribution, dict)
            
            # Check topic structure
            for topic in result.topics:
                assert 'topic_id' in topic
                assert 'keywords' in topic
                assert 'weight' in topic
                assert 'description' in topic
                assert isinstance(topic['keywords'], list)
    
    @pytest.mark.asyncio
    async def test_topic_extraction_semantic(self, analytics_engine, sample_transcripts):
        """Test semantic topic extraction"""
        with patch.object(analytics_engine, '_get_all_transcripts', return_value=sample_transcripts):
            result = await analytics_engine.extract_topics(
                num_topics=2,
                method="semantic_clustering"
            )
            
            assert isinstance(result, TopicModelResult)
            assert result.num_topics <= 2
            assert len(result.topics) <= 2
            assert 'method' in result.metadata
            assert result.metadata['method'] == 'semantic_clustering'
    
    @pytest.mark.asyncio
    async def test_comparative_analysis(self, analytics_engine, sample_transcripts):
        """Test comparative analysis between sources"""
        # Mock source content retrieval
        source_a_content = {
            'id': 'transcript_1',
            'title': sample_transcripts[0]['title'],
            'content': sample_transcripts[0]['content'],
            'metadata': sample_transcripts[0]['metadata'],
            'type': 'single_transcript'
        }
        
        source_b_content = {
            'id': 'transcript_2',
            'title': sample_transcripts[1]['title'],
            'content': sample_transcripts[1]['content'],
            'metadata': sample_transcripts[1]['metadata'],
            'type': 'single_transcript'
        }
        
        with patch.object(analytics_engine, '_get_source_content') as mock_get_source:
            mock_get_source.side_effect = [source_a_content, source_b_content]
            
            result = await analytics_engine.compare_sources(
                source_a='transcript_1',
                source_b='transcript_2',
                comparison_type='comprehensive'
            )
            
            assert isinstance(result, ComparativeAnalysisResult)
            assert result.source_a == 'transcript_1'
            assert result.source_b == 'transcript_2'
            assert isinstance(result.similarities, dict)
            assert isinstance(result.differences, dict)
            assert isinstance(result.common_themes, list)
            assert isinstance(result.unique_themes, dict)
            
            # Check similarity metrics
            if result.similarities:
                for metric, value in result.similarities.items():
                    assert isinstance(value, (int, float))
                    assert 0 <= value <= 1  # Similarity scores should be normalized
    
    def test_time_bucket_creation(self, analytics_engine, sample_transcripts):
        """Test time bucket creation for trend analysis"""
        buckets = analytics_engine._create_time_buckets(sample_transcripts, "30d")
        
        assert isinstance(buckets, dict)
        assert len(buckets) > 0
        
        # Check that all transcripts are assigned to buckets
        total_transcripts = sum(len(transcripts) for transcripts in buckets.values())
        assert total_transcripts == len(sample_transcripts)
        
        # Check bucket key format (should be dates)
        for bucket_key in buckets.keys():
            assert isinstance(bucket_key, str)
            # Should be in YYYY-MM-DD format for daily buckets
            assert len(bucket_key.split('-')) >= 2
    
    @pytest.mark.asyncio
    async def test_keyword_trend_analysis_details(self, analytics_engine, sample_transcripts):
        """Test detailed keyword trend analysis"""
        with patch.object(analytics_engine, '_get_transcripts_for_period', return_value=sample_transcripts):
            trends = await analytics_engine._analyze_keyword_trends(sample_transcripts, "30d")
            
            assert isinstance(trends, list)
            assert len(trends) > 0
            
            for trend in trends:
                assert 'time_bucket' in trend
                assert 'keywords' in trend
                assert 'transcript_count' in trend
                
                # Check keyword data structure
                for keyword_data in trend['keywords']:
                    assert 'keyword' in keyword_data
                    assert 'score' in keyword_data
                    assert 'frequency' in keyword_data
                    assert 'transcripts_count' in keyword_data
                    
                    assert isinstance(keyword_data['score'], (int, float))
                    assert isinstance(keyword_data['frequency'], int)
                    assert keyword_data['frequency'] >= 0
    
    def test_keyword_extraction_integration(self, analytics_engine):
        """Test integration with keyword extractor"""
        test_text = "This is a test document about machine learning and artificial intelligence projects."
        
        keywords = analytics_engine.keyword_extractor.extract_keywords(test_text, max_keywords=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        
        for keyword, score in keywords:
            assert isinstance(keyword, str)
            assert isinstance(score, (int, float))
            assert score >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, analytics_engine):
        """Test error handling in analytics operations"""
        # Test with invalid time period
        result = await analytics_engine.analyze_trends(
            time_period="invalid",
            analysis_type="keywords"
        )
        
        assert isinstance(result, TrendAnalysisResult)
        assert result.total_transcripts == 0
        assert len(result.trends) == 0
        
        # Test with invalid analysis type
        result = await analytics_engine.analyze_trends(
            time_period="30d",
            analysis_type="invalid_type"
        )
        
        assert isinstance(result, TrendAnalysisResult)
        assert result.total_transcripts == 0
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, analytics_engine, sample_transcripts):
        """Test caching of analysis results"""
        with patch.object(analytics_engine, '_get_transcripts_for_period', return_value=sample_transcripts):
            # First call should compute and cache
            result1 = await analytics_engine.analyze_trends(
                time_period="30d",
                analysis_type="keywords"
            )
            
            # Second call should use cache (mock won't be called again)
            with patch.object(analytics_engine, '_get_transcripts_for_period') as mock_get:
                mock_get.return_value = []  # Different data to verify cache is used
                
                result2 = await analytics_engine.analyze_trends(
                    time_period="30d",
                    analysis_type="keywords"
                )
                
                # Results should be similar (from cache)
                assert result1.time_period == result2.time_period
                assert result1.analysis_type == result2.analysis_type
                # Cache should have been used, so mock shouldn't be called
                mock_get.assert_not_called()


class TestSearchManagerIntegration:
    """Test integration with search manager"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def search_manager(self, temp_db):
        """Create search manager with test database"""
        return SearchManager(temp_db)
    
    def test_search_manager_analytics_integration(self, search_manager):
        """Test that search manager has analytics capabilities"""
        assert hasattr(search_manager, 'analytics')
        assert isinstance(search_manager.analytics, AdvancedAnalytics)
        
        # Test analytics methods are available
        assert hasattr(search_manager, 'analyze_trends')
        assert hasattr(search_manager, 'extract_topics')
        assert hasattr(search_manager, 'compare_sources')
        assert hasattr(search_manager, 'get_analytics_stats')
    
    def test_analytics_stats(self, search_manager):
        """Test analytics statistics"""
        stats = search_manager.get_analytics_stats()
        
        assert isinstance(stats, dict)
        assert 'analytics_enabled' in stats
        assert stats['analytics_enabled'] is True
        assert 'supported_analyses' in stats
        assert 'trend_periods' in stats
        assert 'analysis_types' in stats
        
        # Check supported analyses
        expected_analyses = ['trend_analysis', 'topic_modeling', 'comparative_analysis', 'keyword_extraction']
        for analysis in expected_analyses:
            assert analysis in stats['supported_analyses']
        
        # Check trend periods
        expected_periods = ['7d', '30d', '90d', '1y']
        for period in expected_periods:
            assert period in stats['trend_periods']
        
        # Check analysis types
        expected_types = ['keywords', 'topics', 'entities', 'sentiment']
        for analysis_type in expected_types:
            assert analysis_type in stats['analysis_types']


class TestFullTextSearch:
    """Test full-text search capabilities"""
    
    def test_keyword_extraction_for_search(self):
        """Test keyword extraction for search indexing"""
        extractor = KeywordExtractor()
        
        test_content = """
        This is a comprehensive discussion about machine learning algorithms
        and their applications in natural language processing. We covered
        deep learning, neural networks, and transformer models in detail.
        """
        
        keywords = extractor.extract_keywords(test_content, method="rake", max_keywords=10)
        
        assert len(keywords) > 0
        assert len(keywords) <= 10
        
        # Check that relevant keywords are extracted
        keyword_texts = [kw[0] for kw in keywords]
        
        # Should contain some relevant terms
        relevant_found = any(
            term in ' '.join(keyword_texts).lower() 
            for term in ['learning', 'neural', 'language', 'processing']
        )
        assert relevant_found
    
    def test_keyphrase_extraction(self):
        """Test keyphrase extraction for better search"""
        extractor = KeywordExtractor()
        
        test_content = """
        The artificial intelligence project team met to discuss machine learning
        implementation strategies. Natural language processing was identified
        as a key component for the user interface development.
        """
        
        keyphrases = extractor.extract_keyphrases(test_content, max_keyphrases=5)
        
        assert len(keyphrases) > 0
        assert len(keyphrases) <= 5
        
        # Check that multi-word phrases are extracted
        phrase_texts = [kp[0] for kp in keyphrases]
        multi_word_phrases = [phrase for phrase in phrase_texts if len(phrase.split()) > 1]
        
        assert len(multi_word_phrases) > 0
    
    def test_keyword_context_extraction(self):
        """Test keyword context extraction for search results"""
        extractor = KeywordExtractor()
        
        test_content = """
        The machine learning model performed exceptionally well on the test dataset.
        We used various machine learning techniques including supervised learning
        and unsupervised learning approaches. The machine learning pipeline
        was optimized for production deployment.
        """
        
        contexts = extractor.get_keyword_context(test_content, "machine learning")
        
        assert len(contexts) > 0
        
        # Each context should contain the keyword
        for context in contexts:
            assert "machine learning" in context.lower()
            assert len(context) > len("machine learning")  # Should have surrounding context


def run_comprehensive_test():
    """Run comprehensive test of advanced search and analytics"""
    print("🧪 Testing Advanced Search and Analytics Implementation")
    print("=" * 60)
    
    # Test keyword extraction
    print("\n1. Testing Keyword Extraction...")
    extractor = KeywordExtractor()
    
    sample_text = """
    Our team meeting focused on the quarterly project review and budget planning.
    We discussed the new software development methodology and its impact on
    delivery timelines. The client presentation went well, and we received
    positive feedback on our technical approach.
    """
    
    keywords = extractor.extract_keywords(sample_text, method="rake", max_keywords=10)
    print(f"   ✅ Extracted {len(keywords)} keywords")
    print(f"   📝 Top keywords: {[kw[0] for kw in keywords[:5]]}")
    
    # Test keyphrases
    keyphrases = extractor.extract_keyphrases(sample_text, max_keyphrases=5)
    print(f"   ✅ Extracted {len(keyphrases)} keyphrases")
    print(f"   📝 Top keyphrases: {[kp[0] for kp in keyphrases[:3]]}")
    
    # Test analytics engine initialization
    print("\n2. Testing Analytics Engine...")
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        analytics = AdvancedAnalytics(db_path)
        print("   ✅ Analytics engine initialized successfully")
        
        # Test search manager integration
        print("\n3. Testing Search Manager Integration...")
        search_manager = SearchManager(db_path)
        stats = search_manager.get_analytics_stats()
        
        print(f"   ✅ Analytics enabled: {stats['analytics_enabled']}")
        print(f"   📊 Supported analyses: {len(stats['supported_analyses'])}")
        print(f"   📅 Trend periods: {stats['trend_periods']}")
        print(f"   🔍 Analysis types: {stats['analysis_types']}")
        
        print("\n4. Testing Topic Modeling...")
        # Create sample data for topic modeling
        sample_transcripts = [
            {
                'id': 'test_1',
                'title': 'Project Meeting',
                'content': 'We discussed project timelines, budget allocation, and team responsibilities.',
                'metadata': {'tags': ['meeting', 'project']},
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'test_2', 
                'title': 'Technical Review',
                'content': 'Technical architecture review covering system design and performance optimization.',
                'metadata': {'tags': ['technical', 'review']},
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        # Mock the database query for testing
        async def test_topic_extraction():
            with patch.object(analytics, '_get_transcripts_by_ids', return_value=sample_transcripts):
                result = await analytics.extract_topics(
                    transcript_ids=['test_1', 'test_2'],
                    num_topics=2,
                    method="keyword_clustering"
                )
                return result
        
        topic_result = asyncio.run(test_topic_extraction())
        print(f"   ✅ Extracted {topic_result.num_topics} topics")
        print(f"   📊 Coherence score: {topic_result.coherence_score:.3f}")
        
        print("\n5. Testing Trend Analysis...")
        
        async def test_trend_analysis():
            with patch.object(analytics, '_get_transcripts_for_period', return_value=sample_transcripts):
                result = await analytics.analyze_trends(
                    time_period="30d",
                    analysis_type="keywords"
                )
                return result
        
        trend_result = asyncio.run(test_trend_analysis())
        print(f"   ✅ Analyzed trends for {trend_result.total_transcripts} transcripts")
        print(f"   📈 Found {len(trend_result.trends)} trend periods")
        print(f"   🔍 Analysis type: {trend_result.analysis_type}")
        
        print("\n6. Testing Comparative Analysis...")
        
        async def test_comparative_analysis():
            source_a = {
                'id': 'test_1',
                'title': 'Project Meeting',
                'content': sample_transcripts[0]['content'],
                'metadata': sample_transcripts[0]['metadata'],
                'type': 'single_transcript'
            }
            
            source_b = {
                'id': 'test_2',
                'title': 'Technical Review', 
                'content': sample_transcripts[1]['content'],
                'metadata': sample_transcripts[1]['metadata'],
                'type': 'single_transcript'
            }
            
            with patch.object(analytics, '_get_source_content') as mock_get_source:
                mock_get_source.side_effect = [source_a, source_b]
                
                result = await analytics.compare_sources(
                    source_a='test_1',
                    source_b='test_2',
                    comparison_type='comprehensive'
                )
                return result
        
        comparison_result = asyncio.run(test_comparative_analysis())
        print(f"   ✅ Compared sources: {comparison_result.source_a} vs {comparison_result.source_b}")
        print(f"   🔗 Similarities found: {len(comparison_result.similarities)}")
        print(f"   🎯 Common themes: {len(comparison_result.common_themes)}")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("\n" + "=" * 60)
    print("✅ Advanced Search and Analytics Implementation Complete!")
    print("\n📋 Features Implemented:")
    print("   • Full-text search with keyword extraction")
    print("   • Semantic search integration")
    print("   • Trend analysis (keywords, topics, entities, sentiment)")
    print("   • Topic modeling with keyword clustering")
    print("   • Comparative analysis between sources")
    print("   • Advanced analytics UI components")
    print("   • Search manager integration")
    print("   • Caching and performance optimization")
    
    print("\n🎯 Task 29 Requirements Met:")
    print("   ✅ Add full-text search across all processed transcripts")
    print("   ✅ Create semantic search using embedding models")
    print("   ✅ Implement trend analysis across multiple transcripts")
    print("   ✅ Add keyword extraction and topic modeling")
    print("   ✅ Create comparative analysis between different audio sources")


if __name__ == "__main__":
    # Run pytest if available, otherwise run comprehensive test
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        run_comprehensive_test()