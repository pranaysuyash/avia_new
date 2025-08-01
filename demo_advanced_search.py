"""
Demo script for advanced search functionality
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from search.search_manager import SearchManager, SearchQuery
from search.search_index import DocumentIndex
from search.result_ranker import ResultRanker
from search.providers.sqlite_search import SQLiteSearchProvider
from search.providers.whoosh_search import WhooshSearchProvider, WHOOSH_AVAILABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_documents():
    """Create sample documents for testing"""
    documents = [
        DocumentIndex(
            doc_id="doc1",
            title="AI Technology Conference 2024",
            content="The annual AI technology conference featured discussions about machine learning, "
                   "natural language processing, and deep learning. Speakers included researchers from "
                   "OpenAI, Google DeepMind, and Microsoft Research. The event covered breakthrough "
                   "innovations in generative AI and their applications in healthcare and finance.",
            metadata={
                'entities': [
                    {'text': 'OpenAI', 'label': 'ORG'},
                    {'text': 'Google DeepMind', 'label': 'ORG'},
                    {'text': 'Microsoft Research', 'label': 'ORG'}
                ],
                'tags': ['AI', 'technology', 'conference'],
                'speakers': ['Dr. Sarah Chen', 'Prof. Michael Johnson'],
                'language': 'en',
                'confidence': 0.95,
                'created_at': (datetime.now() - timedelta(days=5)).isoformat()
            }
        ),
        DocumentIndex(
            doc_id="doc2",
            title="Medical Research Meeting",
            content="Today's medical research meeting focused on breakthrough treatments for cancer "
                   "and diabetes. The team discussed clinical trial results and new drug discoveries. "
                   "Participants included researchers from Mayo Clinic, Johns Hopkins, and Harvard Medical School.",
            metadata={
                'entities': [
                    {'text': 'Mayo Clinic', 'label': 'ORG'},
                    {'text': 'Johns Hopkins', 'label': 'ORG'},
                    {'text': 'Harvard Medical School', 'label': 'ORG'},
                    {'text': 'cancer', 'label': 'CONDITION'},
                    {'text': 'diabetes', 'label': 'CONDITION'}
                ],
                'tags': ['medical', 'research', 'healthcare'],
                'speakers': ['Dr. Maria Rodriguez', 'Dr. James Wilson'],
                'language': 'en',
                'confidence': 0.89,
                'created_at': (datetime.now() - timedelta(days=2)).isoformat()
            }
        ),
        DocumentIndex(
            doc_id="doc3",
            title="Business Strategy Discussion",
            content="The quarterly business strategy meeting covered market expansion plans, "
                   "competitive analysis, and revenue projections. Key topics included entering "
                   "the European market and launching new product lines. The finance team presented "
                   "budget allocations and ROI forecasts.",
            metadata={
                'entities': [
                    {'text': 'European market', 'label': 'LOC'},
                    {'text': 'Q3 2024', 'label': 'DATE'},
                    {'text': '$2.5M', 'label': 'MONEY'}
                ],
                'tags': ['business', 'strategy', 'finance'],
                'speakers': ['CEO John Smith', 'CFO Lisa Brown'],
                'language': 'en',
                'confidence': 0.92,
                'created_at': (datetime.now() - timedelta(days=1)).isoformat()
            }
        ),
        DocumentIndex(
            doc_id="doc4",
            title="Technical Architecture Review",
            content="Architecture review meeting discussing cloud infrastructure, microservices "
                   "implementation, and DevOps practices. The team evaluated AWS vs Azure platforms "
                   "and planned the migration strategy. Security considerations and performance "
                   "optimization were key discussion points.",
            metadata={
                'entities': [
                    {'text': 'AWS', 'label': 'ORG'},
                    {'text': 'Azure', 'label': 'ORG'},
                    {'text': 'DevOps', 'label': 'TECH'}
                ],
                'tags': ['technical', 'architecture', 'cloud'],
                'speakers': ['Lead Architect Tom Davis', 'DevOps Engineer Alice Cooper'],
                'language': 'en',
                'confidence': 0.87,
                'created_at': (datetime.now() - timedelta(days=3)).isoformat()
            }
        )
    ]
    
    return documents


async def demo_basic_search():
    """Demo basic search functionality"""
    print("\n" + "="*60)
    print("DEMO: Basic Search Functionality")
    print("="*60)
    
    # Initialize search manager
    search_manager = SearchManager("demo_search_index.db")
    
    try:
        # Index sample documents
        documents = create_sample_documents()
        await search_manager.index_batch(documents)
        print(f"✅ Indexed {len(documents)} sample documents")
        
        # Test basic searches
        test_queries = [
            "AI machine learning",
            "medical research cancer",
            "business strategy market",
            "cloud architecture AWS"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Searching: '{query}'")
            
            search_query = SearchQuery(query=query)
            results = await search_manager.search(search_query)
            
            print(f"   Found {results.total_count} results in {results.search_time_ms:.1f}ms")
            
            for i, result in enumerate(results.results[:2]):
                print(f"   {i+1}. {result['title']}")
                print(f"      Score: {result.get('rank', 0):.2f}")
                if result.get('content_snippet'):
                    snippet = result['content_snippet'][:100] + "..."
                    print(f"      Snippet: {snippet}")
                    
    finally:
        search_manager.close()


async def demo_advanced_filters():
    """Demo advanced filtering capabilities"""
    print("\n" + "="*60)
    print("DEMO: Advanced Search Filters")
    print("="*60)
    
    search_manager = SearchManager("demo_search_index.db")
    
    try:
        # Test various filter combinations
        filter_tests = [
            {
                'name': 'Entity Type Filter',
                'query': 'research',
                'filters': {'entity_types': ['ORG']}
            },
            {
                'name': 'Tag Filter',
                'query': '',
                'filters': {'tags': ['medical', 'AI']}
            },
            {
                'name': 'Speaker Filter',
                'query': '',
                'filters': {'speakers': ['Dr. Sarah Chen']}
            },
            {
                'name': 'Date Range Filter',
                'query': 'meeting',
                'filters': {
                    'date_range': {
                        'start': (datetime.now() - timedelta(days=3)).isoformat(),
                        'end': datetime.now().isoformat()
                    }
                }
            },
            {
                'name': 'Confidence Filter',
                'query': '',
                'filters': {'min_confidence': 0.9}
            }
        ]
        
        for test in filter_tests:
            print(f"\n🔍 {test['name']}")
            print(f"   Query: '{test['query']}'")
            print(f"   Filters: {test['filters']}")
            
            search_query = SearchQuery(
                query=test['query'],
                filters=test['filters']
            )
            
            results = await search_manager.search(search_query)
            
            print(f"   Results: {results.total_count} documents")
            
            for result in results.results[:2]:
                print(f"   - {result['title']}")
                
    finally:
        search_manager.close()


async def demo_query_parsing():
    """Demo advanced query parsing"""
    print("\n" + "="*60)
    print("DEMO: Advanced Query Parsing")
    print("="*60)
    
    search_manager = SearchManager("demo_search_index.db")
    
    try:
        # Test complex queries
        complex_queries = [
            'AI technology speaker:"Dr. Sarah Chen"',
            'research tag:medical confidence:>=0.9',
            'meeting date:week',
            '"machine learning" AND technology',
            'business NOT finance',
            '+strategy market',
            'cloud -security'
        ]
        
        for query in complex_queries:
            print(f"\n🔍 Complex Query: '{query}'")
            
            # Parse the query
            parsed = search_manager.parser.parse(query)
            
            print(f"   Search terms: {parsed.search_terms}")
            print(f"   Exact phrases: {parsed.exact_phrases}")
            print(f"   Required terms: {parsed.required_terms}")
            print(f"   Excluded terms: {parsed.excluded_terms}")
            print(f"   Filters: {parsed.filters}")
            
            # Execute search
            search_query = SearchQuery(query=query)
            results = await search_manager.search(search_query)
            
            print(f"   Results: {results.total_count} documents")
            
    finally:
        search_manager.close()


async def demo_result_ranking():
    """Demo advanced result ranking"""
    print("\n" + "="*60)
    print("DEMO: Advanced Result Ranking")
    print("="*60)
    
    search_manager = SearchManager("demo_search_index.db")
    ranker = ResultRanker()
    
    try:
        # Search for results
        search_query = SearchQuery(query="research technology")
        results = await search_manager.search(search_query)
        
        if results.results:
            print(f"🔍 Ranking {len(results.results)} results for 'research technology'")
            
            # Apply advanced ranking
            ranked_results = ranker.rank_results(
                results.results, 
                "research technology"
            )
            
            print("\n📊 Ranked Results:")
            for i, result in enumerate(ranked_results[:3]):
                features = result.get('ranking_features')
                print(f"\n{i+1}. {result['title']}")
                print(f"   Final Score: {result['final_score']:.3f}")
                
                if features:
                    print(f"   - Text Relevance: {features.text_relevance:.3f}")
                    print(f"   - Title Match: {features.title_match:.3f}")
                    print(f"   - Content Match: {features.content_match:.3f}")
                    print(f"   - Entity Match: {features.entity_match:.3f}")
                    print(f"   - Recency: {features.recency:.3f}")
                    print(f"   - Quality: {features.quality_score:.3f}")
                
                # Show ranking explanation
                explanation = ranker.explain_ranking(result)
                top_factors = explanation.get('top_factors', [])[:2]
                
                print(f"   Top Contributing Factors:")
                for factor_name, factor_data in top_factors:
                    print(f"     - {factor_name}: {factor_data['contribution']:.3f}")
                    
    finally:
        search_manager.close()


async def demo_search_providers():
    """Demo different search providers"""
    print("\n" + "="*60)
    print("DEMO: Search Provider Comparison")
    print("="*60)
    
    providers = [
        ("SQLite FTS5", SQLiteSearchProvider)
    ]
    
    if WHOOSH_AVAILABLE:
        providers.append(("Whoosh", WhooshSearchProvider))
    else:
        print("⚠️  Whoosh not available - install with: pip install whoosh")
    
    documents = create_sample_documents()
    query = "AI technology research"
    
    for provider_name, provider_class in providers:
        print(f"\n🔧 Testing {provider_name} Provider")
        
        try:
            # Initialize provider
            provider = provider_class()
            
            if provider_name == "SQLite FTS5":
                provider.initialize({'db_path': f'demo_{provider_name.lower().replace(" ", "_")}.db'})
            else:
                provider.initialize({'index_dir': f'demo_{provider_name.lower()}_index'})
            
            # Index documents
            search_docs = [
                doc for doc in documents
            ]
            provider.index_batch(search_docs)
            
            # Search
            import time
            start_time = time.time()
            results, total_count = provider.search(query, limit=5)
            search_time = (time.time() - start_time) * 1000
            
            print(f"   Query: '{query}'")
            print(f"   Results: {total_count} documents in {search_time:.1f}ms")
            
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['title']}")
                print(f"      Score: {result.get('rank', 0):.3f}")
            
            # Get provider stats
            stats = provider.get_stats()
            print(f"   Stats: {stats}")
            
            provider.close()
            
        except Exception as e:
            print(f"   ❌ Error with {provider_name}: {e}")


async def demo_saved_searches():
    """Demo saved searches and history"""
    print("\n" + "="*60)
    print("DEMO: Saved Searches & History")
    print("="*60)
    
    search_manager = SearchManager("demo_search_index.db")
    
    try:
        # Save some searches
        searches_to_save = [
            ("AI Research", "AI machine learning research", {"tags": ["AI", "technology"]}),
            ("Medical Studies", "medical research healthcare", {"entity_types": ["ORG"]}),
            ("Business Meetings", "business strategy meeting", {"speakers": ["CEO"]})
        ]
        
        for name, query, filters in searches_to_save:
            search_manager.save_search(name, query, filters)
            print(f"💾 Saved search: '{name}'")
        
        # Show saved searches
        saved_searches = search_manager.get_saved_searches()
        print(f"\n📚 Retrieved {len(saved_searches)} saved searches:")
        
        for search in saved_searches:
            print(f"   - {search['name']}: '{search['query']}'")
            if search['filters']:
                print(f"     Filters: {search['filters']}")
        
        # Execute a few searches to build history
        test_queries = ["technology", "research meeting", "business strategy"]
        
        for query in test_queries:
            search_query = SearchQuery(query=query)
            await search_manager.search(search_query)
        
        # Show search history
        history = search_manager.get_search_history(limit=5)
        print(f"\n🕐 Recent search history ({len(history)} entries):")
        
        for hist in history:
            print(f"   - '{hist['query']}' → {hist['result_count']} results")
            
    finally:
        search_manager.close()


async def demo_export_functionality():
    """Demo search result export"""
    print("\n" + "="*60)
    print("DEMO: Search Result Export")
    print("="*60)
    
    search_manager = SearchManager("demo_search_index.db")
    
    try:
        # Perform search
        search_query = SearchQuery(query="research technology")
        results = await search_manager.search(search_query)
        
        if results.results:
            print(f"🔍 Exporting {len(results.results)} search results")
            
            # Export to JSON
            json_export = search_manager.export_results(results, 'json')
            json_data = json.loads(json_export)
            
            print(f"\n📄 JSON Export Preview:")
            print(f"   Query: {json_data['query']}")
            print(f"   Total Results: {json_data['total_results']}")
            print(f"   Search Time: {json_data['search_time_ms']:.1f}ms")
            print(f"   Export Size: {len(json_export)} characters")
            
            # Export to CSV  
            csv_export = search_manager.export_results(results, 'csv')
            csv_lines = csv_export.strip().split('\n')
            
            print(f"\n📊 CSV Export Preview:")
            print(f"   Header: {csv_lines[0] if csv_lines else 'N/A'}")
            print(f"   Rows: {len(csv_lines) - 1}")
            print(f"   Export Size: {len(csv_export)} characters")
            
        else:
            print("❌ No results to export")
            
    finally:
        search_manager.close()


async def main():
    """Run all search demos"""
    print("🚀 Advanced Search System Demo")
    print("This demo showcases the comprehensive search capabilities")
    
    try:
        await demo_basic_search()
        await demo_advanced_filters()
        await demo_query_parsing()
        await demo_result_ranking()
        await demo_search_providers()
        await demo_saved_searches()
        await demo_export_functionality()
        
        print("\n" + "="*60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\n🔍 Advanced Search Features Demonstrated:")
        print("   ✓ Full-text search with SQLite FTS5")
        print("   ✓ Advanced filtering (entity types, tags, speakers, dates)")
        print("   ✓ Complex query parsing (Boolean operators, filters)")
        print("   ✓ Intelligent result ranking")
        print("   ✓ Multiple search providers (SQLite, Whoosh)")
        print("   ✓ Saved searches and search history")
        print("   ✓ Export functionality (JSON, CSV)")
        print("   ✓ Search highlighting and snippets")
        print("   ✓ Faceted search with metadata")
        print("   ✓ Performance optimization and caching")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")


if __name__ == "__main__":
    asyncio.run(main())