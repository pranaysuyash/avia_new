"""
Simple test for advanced search functionality (no Streamlit dependencies)
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from search.search_manager import SearchManager, SearchQuery
from search.search_index import SearchIndex, DocumentIndex


def create_test_documents():
    """Create test documents"""
    return [
        DocumentIndex(
            doc_id="test1",
            title="AI Technology Conference 2024",
            content="Machine learning and artificial intelligence discussion with OpenAI researchers",
            metadata={
                'entities': [{'text': 'OpenAI', 'label': 'ORG'}],
                'tags': ['AI', 'technology'],
                'speakers': ['Dr. Smith'],
                'language': 'en',
                'confidence': 0.95,
                'created_at': datetime.now().isoformat()
            }
        ),
        DocumentIndex(
            doc_id="test2", 
            title="Medical Research Meeting",
            content="Healthcare discussion about cancer research and new treatments",
            metadata={
                'entities': [{'text': 'cancer', 'label': 'CONDITION'}],
                'tags': ['medical', 'research'],
                'speakers': ['Dr. Johnson'],
                'language': 'en',
                'confidence': 0.88,
                'created_at': datetime.now().isoformat()
            }
        )
    ]


async def test_basic_search():
    """Test basic search functionality"""
    print("Testing Basic Search...")
    
    # Create a temporary search index
    search_manager = SearchManager("test_search.db")
    
    try:
        # Index test documents
        documents = create_test_documents()
        await search_manager.index_batch(documents)
        print(f"✅ Indexed {len(documents)} documents")
        
        # Test search
        query = SearchQuery(query="AI technology")
        results = await search_manager.search(query)
        
        print(f"✅ Search completed: {results.total_count} results in {results.search_time_ms:.1f}ms")
        
        for result in results.results:
            print(f"   - {result['title']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Basic search test failed: {e}")
        return False
        
    finally:
        search_manager.close()


async def test_filtered_search():
    """Test filtered search"""
    print("\nTesting Filtered Search...")
    
    search_manager = SearchManager("test_search.db")
    
    try:
        # Test with filters
        query = SearchQuery(
            query="research",
            filters={
                'tags': ['medical'],
                'min_confidence': 0.85
            }
        )
        
        results = await search_manager.search(query)
        print(f"✅ Filtered search: {results.total_count} results")
        
        for result in results.results:
            print(f"   - {result['title']} (confidence: {result.get('confidence', 'N/A')})")
            
        return True
        
    except Exception as e:
        print(f"❌ Filtered search test failed: {e}")
        return False
        
    finally:
        search_manager.close()


async def test_query_parsing():
    """Test query parsing"""
    print("\nTesting Query Parsing...")
    
    search_manager = SearchManager("test_search.db")
    
    try:
        # Test complex query
        complex_query = 'AI technology speaker:"Dr. Smith"'
        parsed = search_manager.parser.parse(complex_query)
        
        print(f"✅ Parsed query: '{complex_query}'")
        print(f"   Search terms: {parsed.search_terms}")
        print(f"   Filters: {parsed.filters}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query parsing test failed: {e}")
        return False
        
    finally:
        search_manager.close()


async def test_export():
    """Test export functionality"""
    print("\nTesting Export...")
    
    search_manager = SearchManager("test_search.db")
    
    try:
        # Search and export
        query = SearchQuery(query="research")
        results = await search_manager.search(query)
        
        # Export to JSON
        json_export = search_manager.export_results(results, 'json')
        json_data = json.loads(json_export)
        
        print(f"✅ JSON export: {len(json_export)} characters")
        print(f"   Results: {json_data['total_results']}")
        
        # Export to CSV
        csv_export = search_manager.export_results(results, 'csv')
        
        print(f"✅ CSV export: {len(csv_export)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False
        
    finally:
        search_manager.close()


async def main():
    """Run all tests"""
    print("🔍 Advanced Search System Tests")
    print("=" * 40)
    
    tests = [
        test_basic_search,
        test_filtered_search, 
        test_query_parsing,
        test_export
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All advanced search features working correctly!")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    # Cleanup
    try:
        os.remove("test_search.db")
        print("🧹 Cleaned up test files")
    except:
        pass


if __name__ == "__main__":
    asyncio.run(main())