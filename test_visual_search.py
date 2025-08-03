#!/usr/bin/env python3
"""
Test script for visual search and content discovery functionality
Tests Task 38: Build visual search and content discovery
"""

import os
import sys
import logging
import numpy as np
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from visual_search import (
    visual_search_engine, timeline_generator, EmbeddingGenerator,
    VisualSearchEngine, ContentTimelineGenerator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_embedding_generation():
    """Test embedding generation functionality"""
    print("\n🧠 Testing Embedding Generation...")
    
    try:
        generator = EmbeddingGenerator()
        
        # Test single embedding
        test_text = "This is a test document about machine learning and artificial intelligence."
        embedding = generator.generate_embedding(test_text)
        
        print(f"✅ Single embedding generated: shape {embedding.shape}")
        print(f"   Embedding type: {type(embedding)}")
        print(f"   Sample values: {embedding[:5]}")
        
        # Test batch embeddings
        test_texts = [
            "Machine learning is a subset of artificial intelligence.",
            "Natural language processing helps computers understand human language.",
            "Computer vision enables machines to interpret visual information.",
            "Deep learning uses neural networks with multiple layers."
        ]
        
        batch_embeddings = generator.generate_batch_embeddings(test_texts)
        print(f"✅ Batch embeddings generated: shape {batch_embeddings.shape}")
        
        # Test similarity
        similarity = np.dot(batch_embeddings[0], batch_embeddings[1])
        print(f"✅ Similarity between first two texts: {similarity:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_engine():
    """Test visual search engine functionality"""
    print("\n🔍 Testing Visual Search Engine...")
    
    try:
        # Create test content
        test_content = [
            {
                'id': 'content_1',
                'title': 'Machine Learning Basics',
                'transcript': 'Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.',
                'metadata': {'category': 'Education', 'duration': 120}
            },
            {
                'id': 'content_2', 
                'title': 'Deep Learning Introduction',
                'transcript': 'Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.',
                'metadata': {'category': 'Education', 'duration': 180}
            },
            {
                'id': 'content_3',
                'title': 'Business Meeting Notes',
                'transcript': 'Today we discussed the quarterly sales figures and marketing strategy. The team agreed to focus on digital marketing channels and customer retention programs.',
                'metadata': {'category': 'Business', 'duration': 90}
            },
            {
                'id': 'content_4',
                'title': 'Project Planning Session',
                'transcript': 'We need to plan the next phase of the project. The timeline includes development, testing, and deployment phases. Resource allocation is critical for success.',
                'metadata': {'category': 'Business', 'duration': 150}
            }
        ]
        
        # Add content to search engine
        search_engine = VisualSearchEngine()
        
        for content in test_content:
            search_engine.add_transcript(
                transcript_id=content['id'],
                title=content['title'],
                transcript=content['transcript'],
                metadata=content['metadata']
            )
        
        print(f"✅ Added {len(test_content)} items to search index")
        
        # Test text search
        search_queries = [
            "machine learning algorithms",
            "business meeting discussion",
            "project development timeline",
            "artificial intelligence"
        ]
        
        for query in search_queries:
            results = search_engine.search_by_text(query, top_k=3)
            print(f"\n🔍 Query: '{query}'")
            print(f"   Found {len(results)} results:")
            
            for i, result in enumerate(results):
                print(f"   {i+1}. {result.content_item.title} (similarity: {result.similarity_score:.3f})")
                print(f"      {result.relevance_explanation}")
        
        # Test content-based search
        if search_engine.content_items:
            first_item = search_engine.content_items[0]
            similar_results = search_engine.search_by_content(first_item, top_k=2)
            
            print(f"\n🔗 Similar to '{first_item.title}':")
            for result in similar_results:
                print(f"   • {result.content_item.title} (similarity: {result.similarity_score:.3f})")
        
        # Test clustering
        clusters = search_engine.get_content_clusters(n_clusters=2)
        print(f"\n🎯 Generated {len(clusters)} clusters:")
        
        for i, cluster in enumerate(clusters):
            print(f"   Cluster {i+1}: {cluster.name}")
            print(f"   Items: {len(cluster.items)}")
            print(f"   Topics: {', '.join(cluster.topics[:3])}")
            print(f"   Summary: {cluster.summary}")
        
        # Test content map generation
        map_data = search_engine.get_content_map_data(method="pca")
        if map_data:
            print(f"\n🗺️ Content map generated:")
            print(f"   Points: {len(map_data['x'])}")
            print(f"   Dimensions: 2D coordinates")
            print(f"   Sample coordinates: ({map_data['x'][0]:.3f}, {map_data['y'][0]:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Search engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeline_generation():
    """Test timeline generation functionality"""
    print("\n📊 Testing Timeline Generation...")
    
    try:
        # Use the search engine from previous test
        search_engine = VisualSearchEngine()
        
        # Add some test content with different timestamps
        import time
        current_time = time.time()
        
        timeline_content = [
            {
                'id': 'timeline_1',
                'title': 'Morning Meeting',
                'transcript': 'Morning standup meeting discussing daily goals and priorities.',
                'metadata': {'duration': 30, 'timestamp': current_time - 86400}  # 1 day ago
            },
            {
                'id': 'timeline_2',
                'title': 'Afternoon Review',
                'transcript': 'Afternoon review session covering project progress and blockers.',
                'metadata': {'duration': 45, 'timestamp': current_time - 43200}  # 12 hours ago
            },
            {
                'id': 'timeline_3',
                'title': 'Evening Wrap-up',
                'transcript': 'Evening wrap-up meeting summarizing the day achievements.',
                'metadata': {'duration': 20, 'timestamp': current_time - 3600}   # 1 hour ago
            }
        ]
        
        for content in timeline_content:
            # Manually create content item with custom timestamp
            from visual_search import ContentItem
            import numpy as np
            
            embedding = search_engine.embedding_generator.generate_embedding(content['transcript'])
            
            content_item = ContentItem(
                id=content['id'],
                title=content['title'],
                transcript=content['transcript'],
                embedding=embedding,
                metadata=content['metadata'],
                timestamp=content['metadata']['timestamp'],
                duration=content['metadata']['duration']
            )
            
            search_engine.add_content(content_item)
        
        # Create timeline generator
        timeline_gen = ContentTimelineGenerator(search_engine)
        
        # Test timeline data generation
        timeline_data = timeline_gen.generate_timeline_data(time_granularity="day")
        
        if timeline_data:
            print(f"✅ Timeline data generated:")
            print(f"   Time points: {len(timeline_data['dates'])}")
            print(f"   Content counts: {timeline_data['content_counts']}")
            print(f"   Total durations: {timeline_data['total_durations']}")
        
        # Test density map generation
        density_data = timeline_gen.generate_content_density_map()
        
        if density_data:
            print(f"✅ Density map generated:")
            print(f"   Points: {len(density_data['x'])}")
            print(f"   Density range: {min(density_data['densities'])}-{max(density_data['densities'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Timeline generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration with main application components"""
    print("\n🔗 Testing Integration...")
    
    try:
        # Test global instances
        from visual_search import visual_search_engine, timeline_generator
        
        print(f"✅ Global search engine available: {type(visual_search_engine)}")
        print(f"✅ Global timeline generator available: {type(timeline_generator)}")
        
        # Test UI components import
        from visual_search_ui import visual_search_ui
        print(f"✅ Visual search UI available: {type(visual_search_ui)}")
        
        # Test basic functionality
        test_transcript = "This is a test transcript for integration testing."
        content_item = visual_search_engine.add_transcript(
            transcript_id="integration_test",
            title="Integration Test Content",
            transcript=test_transcript,
            metadata={'category': 'Test', 'duration': 10}
        )
        
        print(f"✅ Content added to global search engine: {content_item.title}")
        
        # Test search
        results = visual_search_engine.search_by_text("integration test", top_k=1)
        if results:
            print(f"✅ Search working: found '{results[0].content_item.title}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Test performance with larger datasets"""
    print("\n⚡ Testing Performance...")
    
    try:
        import time
        
        # Create larger test dataset
        search_engine = VisualSearchEngine()
        
        # Generate test content
        categories = ['Education', 'Business', 'Technology', 'Healthcare', 'Finance']
        topics = [
            'machine learning', 'data analysis', 'project management', 
            'customer service', 'software development', 'market research',
            'team collaboration', 'strategic planning', 'quality assurance'
        ]
        
        print("Generating test content...")
        start_time = time.time()
        
        for i in range(50):  # Create 50 test items
            category = categories[i % len(categories)]
            topic = topics[i % len(topics)]
            
            transcript = f"This is a {category.lower()} discussion about {topic}. " * 10
            
            search_engine.add_transcript(
                transcript_id=f"perf_test_{i}",
                title=f"{category} - {topic.title()} {i}",
                transcript=transcript,
                metadata={'category': category, 'duration': 60 + i}
            )
        
        creation_time = time.time() - start_time
        print(f"✅ Created 50 items in {creation_time:.2f} seconds")
        
        # Test search performance
        search_start = time.time()
        results = search_engine.search_by_text("machine learning data analysis", top_k=10)
        search_time = time.time() - search_start
        
        print(f"✅ Search completed in {search_time:.3f} seconds")
        print(f"   Found {len(results)} results")
        
        # Test clustering performance
        cluster_start = time.time()
        clusters = search_engine.get_content_clusters(n_clusters=5)
        cluster_time = time.time() - cluster_start
        
        print(f"✅ Clustering completed in {cluster_time:.3f} seconds")
        print(f"   Generated {len(clusters)} clusters")
        
        # Test map generation performance
        map_start = time.time()
        map_data = search_engine.get_content_map_data(method="pca")
        map_time = time.time() - map_start
        
        print(f"✅ Map generation completed in {map_time:.3f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all visual search tests"""
    print("🚀 Starting Visual Search & Content Discovery Tests (Task 38)")
    print("=" * 70)
    
    tests = [
        ("Embedding Generation", test_embedding_generation),
        ("Search Engine", test_search_engine),
        ("Timeline Generation", test_timeline_generation),
        ("Integration", test_integration),
        ("Performance", test_performance)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with error: {e}")
        
        print("-" * 70)
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All visual search tests passed!")
        print("\n🚀 Visual search and content discovery is ready to use!")
        print("\nTo use visual search features:")
        print("1. Run: streamlit run app.py")
        print("2. Enable '🔍 Visual Search & Discovery' mode in sidebar")
        print("3. Add content and explore with visual similarity!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Check the output above for details.")
    
    return passed == failed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)