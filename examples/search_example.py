"""
Example: How to use the advanced search functionality
"""

import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search import SearchIntegration, SearchQuery, SearchManager


async def main():
    """Demonstrate search functionality usage"""
    
    print("🔍 Advanced Search Example\n")
    
    # Initialize search integration
    search = SearchIntegration("example_search.db")
    
    # Example 1: Index a transcript
    print("1. Indexing a transcript:")
    
    transcript = {
        "id": "meeting_2024_01",
        "title": "Team Planning Meeting - Q1 2024",
        "text": "Alice: Let's discuss our goals for Q1. "
               "Bob: I think we should focus on improving performance. "
               "Alice: Good idea. We also need to address customer feedback.",
        "segments": [
            {"text": "Let's discuss our goals for Q1.", "speaker": "Alice"},
            {"text": "I think we should focus on improving performance.", "speaker": "Bob"},
            {"text": "Good idea. We also need to address customer feedback.", "speaker": "Alice"}
        ],
        "entities": [
            {"text": "Alice", "label": "PERSON"},
            {"text": "Bob", "label": "PERSON"},
            {"text": "Q1", "label": "DATE"}
        ],
        "metadata": {
            "tags": ["planning", "goals", "q1-2024"],
            "created_at": datetime.now().isoformat(),
            "language": "en"
        }
    }
    
    success = await search.index_transcription_result(transcript)
    print(f"  Indexed: {success} ✅\n")
    
    # Example 2: Basic search
    print("2. Basic text search:")
    print("   Query: 'performance customer'")
    
    results = search.search("performance customer")
    print(f"   Found: {results['total_count']} results")
    
    for result in results['results']:
        print(f"   - {result['title']}")
    
    print()
    
    # Example 3: Search with filters
    print("3. Search with speaker filter:")
    print("   Query: 'goals' + speaker:Alice")
    
    results = search.search(
        "goals",
        filters={'speakers': ['Alice']}
    )
    
    print(f"   Found: {results['total_count']} results")
    
    print()
    
    # Example 4: Search with multiple filters
    print("4. Complex search with multiple filters:")
    
    results = search.search(
        "",  # Empty query to browse all
        filters={
            'tags': ['planning'],
            'language': 'en',
            'date_range': {
                'start': datetime.now().date().isoformat()
            }
        },
        options={
            'limit': 10,
            'sort_by': 'date_desc'
        }
    )
    
    print(f"   Found: {results['total_count']} results matching filters")
    
    print()
    
    # Example 5: Get search suggestions
    print("5. Search suggestions:")
    print("   Partial query: 'perf'")
    
    suggestions = search.get_search_suggestions("perf")
    print(f"   Suggestions: {suggestions}")
    
    print()
    
    # Example 6: Export results
    print("6. Export search results:")
    
    # Perform a search
    results = await search.search_manager.search(
        SearchQuery(query="Alice Bob", options={'limit': 5})
    )
    
    # Export as JSON
    json_export = search.search_manager.export_results(results, 'json')
    print("   Exported to JSON format")
    print(f"   Size: {len(json_export)} bytes")
    
    # Export as CSV
    csv_export = search.search_manager.export_results(results, 'csv')
    print("   Exported to CSV format")
    print(f"   Size: {len(csv_export)} bytes")
    
    print()
    
    # Example 7: Query parser examples
    print("7. Query parser examples:")
    
    from search.query_parser import QueryParser
    parser = QueryParser()
    
    example_queries = [
        "revenue increase speaker:John",
        '"exact phrase" -excluded +required',
        "date:2024-01 tag:important confidence:>0.8",
        "entity:PERSON language:en"
    ]
    
    for query in example_queries:
        parsed = parser.parse(query)
        print(f"\n   Query: {query}")
        print(f"   Search terms: {parsed.search_terms}")
        print(f"   Filters: {parsed.filters}")
    
    # Clean up
    search.close()
    
    print("\n✅ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())