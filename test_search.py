"""
Test script for advanced search functionality
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from search import SearchManager, SearchQuery, SearchIntegration


async def test_search_functionality():
    """Test the complete search functionality"""
    
    print("🔍 Testing Advanced Search Functionality\n")
    
    # Initialize search integration
    integration = SearchIntegration("test_search_index.db")
    
    # Create test data
    test_transcripts = [
        {
            "id": "transcript_001",
            "title": "Quarterly Business Review Meeting",
            "text": "John: Good morning everyone. Let's start our quarterly review. "
                   "Mary: Thanks John. Our revenue increased by 15% this quarter. "
                   "John: That's excellent news! What about our customer satisfaction? "
                   "Mary: Customer satisfaction scores improved to 92%, up from 87% last quarter.",
            "segments": [
                {"text": "Good morning everyone. Let's start our quarterly review.", "speaker": "John"},
                {"text": "Thanks John. Our revenue increased by 15% this quarter.", "speaker": "Mary"},
                {"text": "That's excellent news! What about our customer satisfaction?", "speaker": "John"},
                {"text": "Customer satisfaction scores improved to 92%, up from 87% last quarter.", "speaker": "Mary"}
            ],
            "entities": [
                {"text": "John", "label": "PERSON", "confidence": 0.95},
                {"text": "Mary", "label": "PERSON", "confidence": 0.94},
                {"text": "15%", "label": "PERCENT", "confidence": 0.90},
                {"text": "92%", "label": "PERCENT", "confidence": 0.91},
                {"text": "87%", "label": "PERCENT", "confidence": 0.89}
            ],
            "metadata": {
                "tags": ["business", "quarterly-review", "revenue"],
                "created_at": datetime.now().isoformat(),
                "language": "en",
                "confidence": 0.92
            }
        },
        {
            "id": "transcript_002",
            "title": "Product Development Team Standup",
            "text": "Sarah: Yesterday I completed the API integration. "
                   "Mike: Great! I'm working on the UI updates today. "
                   "Sarah: We should be ready for testing by Friday. "
                   "Mike: Perfect. Let's schedule a demo with the stakeholders.",
            "segments": [
                {"text": "Yesterday I completed the API integration.", "speaker": "Sarah"},
                {"text": "Great! I'm working on the UI updates today.", "speaker": "Mike"},
                {"text": "We should be ready for testing by Friday.", "speaker": "Sarah"},
                {"text": "Perfect. Let's schedule a demo with the stakeholders.", "speaker": "Mike"}
            ],
            "entities": [
                {"text": "Sarah", "label": "PERSON", "confidence": 0.93},
                {"text": "Mike", "label": "PERSON", "confidence": 0.92},
                {"text": "Friday", "label": "DATE", "confidence": 0.88},
                {"text": "API", "label": "PRODUCT", "confidence": 0.85}
            ],
            "metadata": {
                "tags": ["development", "standup", "api", "demo"],
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "language": "en",
                "confidence": 0.90
            }
        },
        {
            "id": "transcript_003",
            "title": "Customer Support Call - Issue Resolution",
            "text": "Agent: Hello, this is tech support. How can I help you? "
                   "Customer: My application keeps crashing when I try to export data. "
                   "Agent: I understand. Let me help you troubleshoot this issue. "
                   "Customer: It started happening after the latest update yesterday.",
            "segments": [
                {"text": "Hello, this is tech support. How can I help you?", "speaker": "Agent"},
                {"text": "My application keeps crashing when I try to export data.", "speaker": "Customer"},
                {"text": "I understand. Let me help you troubleshoot this issue.", "speaker": "Agent"},
                {"text": "It started happening after the latest update yesterday.", "speaker": "Customer"}
            ],
            "entities": [
                {"text": "yesterday", "label": "DATE", "confidence": 0.86}
            ],
            "metadata": {
                "tags": ["support", "technical-issue", "bug", "export"],
                "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "language": "en",
                "confidence": 0.88
            }
        }
    ]
    
    # Index test data
    print("📥 Indexing test transcripts...")
    for transcript in test_transcripts:
        success = await integration.index_transcription_result(transcript)
        print(f"  - {transcript['title']}: {'✅' if success else '❌'}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 1: Basic text search
    print("Test 1: Basic Text Search")
    print("Query: 'revenue customer'")
    
    results = await integration.search_manager.search(
        SearchQuery(query="revenue customer")
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']} (relevance: {result['rank']:.2f})")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 2: Speaker filter
    print("Test 2: Speaker Filter Search")
    print("Query: speaker:John")
    
    results = await integration.search_manager.search(
        SearchQuery(query="speaker:John")
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']}")
        print(f"    Speakers: {', '.join(result.get('speakers', []))}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 3: Tag filter
    print("Test 3: Tag Filter Search")
    print("Query: tag:development")
    
    results = await integration.search_manager.search(
        SearchQuery(query="tag:development")
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']}")
        print(f"    Tags: {', '.join(result.get('tags', []))}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 4: Entity type filter
    print("Test 4: Entity Type Filter")
    print("Filters: entity_types=['PERSON']")
    
    results = await integration.search_manager.search(
        SearchQuery(
            query="",
            filters={'entity_types': ['PERSON']}
        )
    )
    
    print(f"Results: {results.total_count} found")
    # Note: Entity filtering happens post-search
    
    print("\n" + "-"*40 + "\n")
    
    # Test 5: Date range filter
    print("Test 5: Date Range Filter")
    print("Query: 'issue' with date:today")
    
    results = await integration.search_manager.search(
        SearchQuery(
            query="issue",
            filters={
                'date_range': {
                    'start': datetime.now().date().isoformat(),
                    'end': datetime.now().date().isoformat()
                }
            }
        )
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']}")
        print(f"    Created: {result.get('created_at', 'Unknown')}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 6: OR operator search
    print("Test 6: OR Operator Search")
    print("Query: 'support OR development'")
    
    results = await integration.search_manager.search(
        SearchQuery(query="support OR development")
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 7: Exact phrase search
    print("Test 7: Exact Phrase Search")
    print('Query: "tech support"')
    
    results = await integration.search_manager.search(
        SearchQuery(query='"tech support"')
    )
    
    print(f"Results: {results.total_count} found")
    for result in results.results:
        print(f"  - {result['title']}")
        if result.get('content_snippet'):
            print(f"    Snippet: {result['content_snippet']}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 8: Faceted search results
    print("Test 8: Faceted Search")
    print("Query: '' (all documents)")
    
    results = await integration.search_manager.search(
        SearchQuery(query="", options={'include_facets': True})
    )
    
    print(f"Total documents: {results.total_count}")
    print("\nFacets:")
    for facet_type, facet_values in results.facets.items():
        if facet_values:
            print(f"\n{facet_type.title()}:")
            for value, count in list(facet_values.items())[:5]:
                print(f"  - {value}: {count}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 9: Search suggestions
    print("Test 9: Search Suggestions")
    print("Partial query: 'rev'")
    
    suggestions = await integration.search_manager.get_search_suggestions("rev")
    print(f"Suggestions: {suggestions}")
    
    print("\n" + "-"*40 + "\n")
    
    # Test 10: Save and retrieve search
    print("Test 10: Saved Searches")
    
    integration.search_manager.save_search(
        "Revenue Reports",
        "revenue customer tag:business",
        {}
    )
    
    saved_searches = integration.search_manager.get_saved_searches()
    print(f"Saved searches: {len(saved_searches)}")
    for search in saved_searches:
        print(f"  - {search['name']}: {search['query']}")
    
    print("\n" + "="*60 + "\n")
    print("✅ All tests completed!")
    
    # Clean up
    integration.close()
    
    # Remove test database
    test_db = Path("test_search_index.db")
    if test_db.exists():
        test_db.unlink()


if __name__ == "__main__":
    asyncio.run(test_search_functionality())