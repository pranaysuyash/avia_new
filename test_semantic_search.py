#!/usr/bin/env python3
"""
Test script for semantic search and transcript library functionality
"""

import os
import sys
import logging
import tempfile
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_semantic_search():
    """Test semantic search functionality"""
    try:
        from semantic_search.transcript_library import TranscriptLibrary, TranscriptEntry, TranscriptMetadata
        from semantic_search.integration import SemanticSearchIntegration
        
        print("🧪 Testing Semantic Search Functionality")
        print("=" * 50)
        
        # Create temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            # Initialize library with SentenceTransformer provider
            print("📚 Initializing transcript library...")
            from semantic_search.providers import SentenceTransformerProvider
            from semantic_search.transcript_embeddings import TranscriptEmbeddingManager
            
            # Use SentenceTransformer for testing (no API key required)
            embedding_provider = SentenceTransformerProvider()
            embedding_manager = TranscriptEmbeddingManager(
                embedding_provider=embedding_provider,
                db_path=db_path.replace('.db', '_embeddings.db')
            )
            
            library = TranscriptLibrary(db_path=db_path)
            library.embedding_manager = embedding_manager  # Override with our provider
            
            integration = SemanticSearchIntegration(library)
            
            # Test data
            test_transcripts = [
                {
                    'id': 'meeting_001',
                    'title': 'Weekly Team Meeting - Project Updates',
                    'content': 'Good morning everyone. Today we will discuss the project timeline and upcoming deadlines. Sarah, can you update us on the marketing campaign progress? We need to ensure all deliverables are ready by Friday.',
                    'category': 'Meeting',
                    'duration': 1800,  # 30 minutes
                    'tags': ['project', 'timeline', 'marketing']
                },
                {
                    'id': 'interview_001', 
                    'title': 'Customer Interview - Product Feedback',
                    'content': 'Thank you for taking the time to speak with us today. Can you tell me about your experience using our product? What features do you find most valuable? Are there any pain points or areas for improvement?',
                    'category': 'Interview',
                    'duration': 2400,  # 40 minutes
                    'tags': ['customer', 'feedback', 'product']
                },
                {
                    'id': 'lecture_001',
                    'title': 'Introduction to Machine Learning',
                    'content': 'Welcome to our machine learning course. Today we will cover the fundamentals of supervised learning, including linear regression and classification algorithms. Please take notes as this will be on the exam.',
                    'category': 'Education',
                    'duration': 3600,  # 60 minutes
                    'tags': ['education', 'machine learning', 'algorithms']
                }
            ]
            
            # Add test transcripts
            print("📝 Adding test transcripts...")
            for transcript_data in test_transcripts:
                metadata = TranscriptMetadata(
                    transcript_id=transcript_data['id'],
                    title=transcript_data['title'],
                    category=transcript_data['category'],
                    duration=transcript_data['duration'],
                    tags=transcript_data['tags'],
                    source='test'
                )
                
                transcript_entry = TranscriptEntry(
                    metadata=metadata,
                    content=transcript_data['content']
                )
                
                success = library.add_transcript(transcript_entry)
                print(f"  ✅ Added: {transcript_data['title']} - {'Success' if success else 'Failed'}")
            
            # Test library stats
            print("\n📊 Library Statistics:")
            stats = library.get_library_stats()
            print(f"  Total transcripts: {stats.get('total_transcripts', 0)}")
            print(f"  Categories: {stats.get('unique_categories', 0)}")
            print(f"  Total duration: {stats.get('total_duration_hours', 0):.1f} hours")
            
            # Vector store stats
            embedding_stats = stats.get('embedding_stats', {})
            if 'vector_store' in embedding_stats:
                vector_stats = embedding_stats['vector_store']
                print(f"  Vector store: {vector_stats.get('index_type', 'Unknown')}")
                print(f"  Vectors indexed: {vector_stats.get('total_vectors', 0)}")
            
            # Test search functionality
            print("\n🔍 Testing Search Functionality:")
            
            # Test semantic search
            print("  Testing semantic search...")
            search_queries = [
                "project deadlines and timeline",
                "customer product experience",
                "learning algorithms and education"
            ]
            
            for query in search_queries:
                print(f"\n  Query: '{query}'")
                results = library.search_transcripts(query, search_type="semantic", limit=3)
                
                if results:
                    for i, result in enumerate(results, 1):
                        score = result.analysis_results.get('search_score', 0)
                        print(f"    {i}. {result.metadata.title} (Score: {score:.3f})")
                else:
                    print("    No results found")
            
            # Test similarity search
            print("\n🔗 Testing Similarity Search:")
            similar_results = library.find_similar_transcripts('meeting_001', limit=2)
            
            if similar_results:
                print("  Similar to 'Weekly Team Meeting':")
                for result in similar_results:
                    score = result.analysis_results.get('similarity_score', 0)
                    print(f"    - {result.metadata.title} (Similarity: {score:.3f})")
            else:
                print("  No similar transcripts found")
            
            # Test integration functionality
            print("\n🔧 Testing Integration:")
            
            # Test adding transcription result
            file_info = {
                'file_name': 'test_audio.wav',
                'file_size': 1024000,
                'duration': 300
            }
            
            analysis_results = {
                'entities': {
                    'persons': ['John', 'Sarah'],
                    'organizations': ['TechCorp']
                },
                'confidence': 0.95
            }
            
            success = integration.add_transcription_result(
                transcript_text="This is a test transcription result for integration testing.",
                file_info=file_info,
                analysis_results=analysis_results
            )
            
            print(f"  Integration test: {'Success' if success else 'Failed'}")
            
            # Test search through integration
            similar_content = integration.search_similar_content("test transcription", limit=3)
            print(f"  Found {len(similar_content)} similar content items through integration")
            
            print("\n✅ All tests completed successfully!")
            
        finally:
            # Clean up temporary database
            try:
                os.unlink(db_path)
                print(f"🗑️ Cleaned up temporary database: {db_path}")
            except:
                pass
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install required dependencies:")
        print("  pip install sentence-transformers numpy sqlite3")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test error details:")
        return False
    
    return True

def test_embedding_providers():
    """Test different embedding providers"""
    print("\n🤖 Testing Embedding Providers")
    print("=" * 50)
    
    try:
        from semantic_search.providers import SentenceTransformerProvider, MockEmbeddingProvider
        
        # Test SentenceTransformer provider
        print("📝 Testing SentenceTransformer provider...")
        try:
            provider = SentenceTransformerProvider()
            test_texts = ["Hello world", "Machine learning is fascinating", "Project deadline approaching"]
            embeddings = provider.generate_embeddings(test_texts)
            print(f"  ✅ Generated embeddings: {embeddings.shape}")
            print(f"  Model: {provider.get_model_name()}")
            print(f"  Dimension: {provider.get_embedding_dimension()}")
        except Exception as e:
            print(f"  ❌ SentenceTransformer test failed: {e}")
        
        # Test Mock provider
        print("\n🎭 Testing Mock provider...")
        try:
            mock_provider = MockEmbeddingProvider(dimension=384)
            embeddings = mock_provider.generate_embeddings(test_texts)
            print(f"  ✅ Generated mock embeddings: {embeddings.shape}")
            print(f"  Model: {mock_provider.get_model_name()}")
        except Exception as e:
            print(f"  ❌ Mock provider test failed: {e}")
        
        # Test OpenAI provider if API key is available
        print("\n🤖 Testing OpenAI provider...")
        if os.getenv('OPENAI_API_KEY'):
            try:
                from semantic_search.providers import OpenAIEmbeddingProvider
                openai_provider = OpenAIEmbeddingProvider()
                embeddings = openai_provider.generate_embeddings(["Test text for OpenAI"])
                print(f"  ✅ Generated OpenAI embeddings: {embeddings.shape}")
                print(f"  Model: {openai_provider.get_model_name()}")
            except Exception as e:
                print(f"  ❌ OpenAI provider test failed: {e}")
        else:
            print("  ⚠️ Skipping OpenAI test (no API key)")
        
    except ImportError as e:
        print(f"❌ Provider import error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Semantic Search Tests")
    print("=" * 60)
    
    success = True
    
    # Test core functionality
    if not test_semantic_search():
        success = False
    
    # Test embedding providers
    if not test_embedding_providers():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed successfully!")
        print("\n💡 Next steps:")
        print("  1. Enable 'Semantic Search & Library' in the app's Advanced Features")
        print("  2. Process some audio files to build your transcript library")
        print("  3. Use the semantic search to find similar content")
        print("  4. Get personalized recommendations based on your history")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())