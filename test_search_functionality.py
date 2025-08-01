#!/usr/bin/env python3
"""
Test script to verify search functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from search.search_index import SearchIndex, DocumentIndex
from search.search_manager import SearchManager, SearchQuery

async def test_search():
    """Test the search functionality with sample data"""
    
    print("🔍 Testing Search Functionality")
    print("=" * 50)
    
    # Initialize search components
    search_index = SearchIndex()
    search_manager = SearchManager()
    
    # Create test documents
    test_documents = [
        {
            "doc_id": "test_001",
            "title": "Product Launch Meeting",
            "content": "Discussed the new product launch strategy for Q4. John presented market analysis showing strong demand. Sarah outlined the marketing campaign.",
            "entities": [{"text": "John", "type": "PERSON"}, {"text": "Sarah", "type": "PERSON"}, {"text": "Q4", "type": "DATE"}],
            "tags": ["meeting", "product", "strategy"],
            "speakers": ["John", "Sarah"],
            "created_at": "2024-01-15T10:00:00"
        },
        {
            "doc_id": "test_002",
            "title": "Customer Support Training",
            "content": "Training session on handling customer complaints. Mike demonstrated the new ticketing system. Important: always follow up within 24 hours.",
            "entities": [{"text": "Mike", "type": "PERSON"}, {"text": "24 hours", "type": "TIME"}],
            "tags": ["training", "support", "customer service"],
            "speakers": ["Mike"],
            "created_at": "2024-01-16T14:00:00"
        },
        {
            "doc_id": "test_003",
            "title": "Technical Architecture Review",
            "content": "Review of the system architecture. Database performance issues were discussed. Need to optimize queries and add caching layer.",
            "entities": [{"text": "database", "type": "TECH"}, {"text": "caching", "type": "TECH"}],
            "tags": ["technical", "architecture", "performance"],
            "speakers": ["Engineering Team"],
            "created_at": "2024-01-17T09:00:00"
        }
    ]
    
    print("\n1. Indexing test documents...")
    for doc_data in test_documents:
        # Convert to DocumentIndex format
        metadata = {
            'entities': doc_data.get('entities', []),
            'tags': doc_data.get('tags', []),
            'speakers': doc_data.get('speakers', []),
            'created_at': doc_data.get('created_at')
        }
        
        doc = DocumentIndex(
            doc_id=doc_data['doc_id'],
            title=doc_data['title'],
            content=doc_data['content'],
            metadata=metadata
        )
        
        search_index.index_document(doc)
    print(f"✅ Indexed {len(test_documents)} documents")
    
    # Test different search queries
    test_queries = [
        ("product launch", "Basic text search"),
        ("\"market analysis\"", "Exact phrase search"),
        ("customer -complaints", "Exclusion search"),
        ("speaker:John", "Speaker filter"),
        ("tag:technical", "Tag filter"),
        ("database performance", "Multi-word search")
    ]
    
    print("\n2. Testing search queries:")
    for query_text, description in test_queries:
        print(f"\n   Query: '{query_text}' ({description})")
        query = SearchQuery(
            query=query_text,
            options={'limit': 10}
        )
        
        results = await search_manager.search(query)
        print(f"   Results: {results.total_count} documents found")
        
        for i, result in enumerate(results.results[:3], 1):
            print(f"   {i}. {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.2f})")
            highlights = result.get('highlights', [])
            if highlights:
                print(f"      Highlight: ...{highlights[0]}...")
    
    # Test faceted search
    print("\n3. Testing faceted search:")
    query = SearchQuery(
        query="",  # Empty query to get all documents
        options={'limit': 10, 'include_facets': True}
    )
    
    results = await search_manager.search(query)
    if results.facets:
        print("   Facets found:")
        for facet_type, facet_values in results.facets.items():
            print(f"   - {facet_type}:")
            for value, count in facet_values.items():
                print(f"     • {value}: {count} documents")
    
    print("\n✅ Search functionality test completed!")
    
    # Cleanup
    search_index.close()

if __name__ == "__main__":
    asyncio.run(test_search())