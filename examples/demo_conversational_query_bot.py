#!/usr/bin/env python3
"""
Conversational Query Bot Demo
Demonstrates the RAG-powered natural language querying system
"""

import json
import uuid
from datetime import datetime
from conversational_query_bot import (
    ConversationalQueryBot, MediaContent, QueryResult, ConversationContext
)

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}\n")

def print_result(result: QueryResult, index: int):
    """Print a single query result"""
    print(f"\n📋 Result #{index}")
    print(f"   Title: {result.content.title}")
    print(f"   Type: {result.content.content_type}")
    print(f"   Relevance: {result.relevance_score:.3f}")
    if result.content.speaker:
        print(f"   Speaker: {result.content.speaker}")
    if result.timestamp_citation:
        print(f"   Time: {result.timestamp_citation}")
    print(f"\n   Preview: {result.snippet[:150]}...")
    if result.context_window:
        print(f"   Context: {result.context_window[:100]}...")

def demo_basic_functionality():
    """Demonstrate basic query functionality"""
    print_header("Basic Query Functionality Demo")
    
    # Initialize bot
    bot = ConversationalQueryBot()
    print("✅ Initialized Conversational Query Bot")
    
    # Add sample content
    print("\n📚 Adding sample content to the library...")
    
    contents = [
        MediaContent(
            id="demo_001",
            title="Q4 Planning Meeting",
            content_type="transcript",
            text_content="""Welcome everyone to our Q4 planning meeting. Today we'll discuss 
            budget allocation, marketing strategies, and product roadmap. Sarah from marketing 
            will present the campaign proposals, and Mike from engineering will update us on 
            the new features. We need to allocate an additional $500k for digital marketing 
            and $300k for product development.""",
            timestamp=30.0,
            speaker="CEO"
        ),
        MediaContent(
            id="demo_002",
            title="Marketing Strategy Document",
            content_type="document",
            text_content="""Our Q4 marketing strategy focuses on three key areas: 
            1) Social media engagement with influencer partnerships, 
            2) Content marketing through blog posts and webinars, 
            3) Email campaigns targeting enterprise customers. 
            Budget requirements: $500k total, with $200k for influencers, 
            $150k for content creation, and $150k for email marketing tools."""
        ),
        MediaContent(
            id="demo_003",
            title="Customer Interview - Enterprise Client",
            content_type="transcript",
            text_content="""The customer expressed satisfaction with our current features 
            but requested better API documentation and more integration options. They 
            specifically mentioned needing Salesforce integration and advanced analytics. 
            They're willing to upgrade to our enterprise plan if we add these features.""",
            timestamp=180.5,
            speaker="Customer Success Manager"
        ),
        MediaContent(
            id="demo_004",
            title="Product Roadmap",
            content_type="document",
            text_content="""Q4 Product Roadmap: 
            - October: Launch API v2 with improved documentation
            - November: Release Salesforce integration (beta)
            - December: Deploy advanced analytics dashboard
            Engineering resources needed: 5 developers, 2 QA engineers
            Estimated cost: $300k for Q4 development"""
        )
    ]
    
    for content in contents:
        if bot.add_content(content):
            print(f"   ✅ Added: {content.title}")
    
    # Demonstrate queries
    print("\n🔍 Demonstrating various queries...")
    
    queries = [
        "What's our budget allocation for Q4?",
        "Tell me about marketing strategies",
        "What features did customers request?",
        "Show me information about API development"
    ]
    
    conversation_id = str(uuid.uuid4())
    
    for query in queries:
        print(f"\n💬 Query: '{query}'")
        
        results = bot.query(query, conversation_id=conversation_id, max_results=3)
        
        if results:
            # Generate AI answer
            answer = bot.generate_answer(query, results)
            print(f"\n🤖 AI Answer: {answer}")
            
            # Show top results
            print(f"\n📊 Found {len(results)} relevant results:")
            for i, result in enumerate(results[:3], 1):
                print_result(result, i)
        else:
            print("   ❌ No results found")
    
    # Show conversation context
    print("\n💬 Conversation Context:")
    context = bot.get_conversation_history(conversation_id)
    print(f"   Total queries in conversation: {len(context.query_history)}")
    print(f"   Queries: {context.query_history}")

def demo_advanced_features():
    """Demonstrate advanced features"""
    print_header("Advanced Features Demo")
    
    bot = ConversationalQueryBot()
    
    # Content type filtering
    print("🎯 Content Type Filtering:")
    
    # Add mixed content
    contents = [
        MediaContent(
            id="adv_001",
            title="Meeting Transcript",
            content_type="transcript",
            text_content="Discussion about Q1 goals and objectives",
            speaker="Team Lead"
        ),
        MediaContent(
            id="adv_002",
            title="Technical Documentation",
            content_type="document",
            text_content="API endpoints and integration guide for Q1 features"
        ),
        MediaContent(
            id="adv_003",
            title="Screenshot Analysis",
            content_type="image_text",
            text_content="Dashboard showing Q1 metrics and KPIs"
        )
    ]
    
    for content in contents:
        bot.add_content(content)
    
    # Query with filters
    print("\n   Querying only transcripts...")
    transcript_results = bot.query("Q1", content_types=["transcript"])
    print(f"   Found {len(transcript_results)} transcript results")
    
    print("\n   Querying only documents...")
    doc_results = bot.query("Q1", content_types=["document"])
    print(f"   Found {len(doc_results)} document results")
    
    # Statistics
    print("\n📊 System Statistics:")
    stats = bot.get_statistics()
    print(f"   Total queries: {stats.get('total_queries', 0)}")
    print(f"   Active conversations: {stats.get('active_conversations', 0)}")
    print(f"   Average processing time: {stats.get('average_processing_time', 0):.3f}s")
    
    # Vector database stats
    vector_stats = stats.get('vector_database', {})
    print(f"\n   Vector Database:")
    print(f"   - Total documents: {vector_stats.get('total_documents', 0)}")
    print(f"   - Dimension: {vector_stats.get('dimension', 0)}")
    
    # Content distribution
    content_stats = stats.get('content_statistics', {})
    if content_stats:
        print(f"\n   Content Distribution:")
        for content_type, count in content_stats.items():
            print(f"   - {content_type}: {count}")

def demo_conversation_management():
    """Demonstrate conversation management"""
    print_header("Conversation Management Demo")
    
    bot = ConversationalQueryBot()
    
    # Add content
    content = MediaContent(
        id="conv_001",
        title="Product Planning Session",
        content_type="transcript",
        text_content="""Let's discuss our product strategy. We need to focus on 
        mobile features, improve performance, and add enterprise security. 
        The mobile app should support offline mode and push notifications. 
        Performance improvements include faster loading and better caching. 
        Enterprise security requires SSO and audit logs.""",
        speaker="Product Manager"
    )
    bot.add_content(content)
    
    # Create conversation
    conversation_id = "demo_conversation"
    
    print("💬 Starting a conversation...")
    
    # Multiple queries in conversation
    queries = [
        "What mobile features were discussed?",
        "Tell me more about performance",
        "What about security requirements?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        results = bot.query(query, conversation_id=conversation_id)
        
        if results:
            answer = bot.generate_answer(query, results)
            print(f"   Answer: {answer[:150]}...")
    
    # Get conversation history
    print("\n📜 Conversation History:")
    context = bot.get_conversation_history(conversation_id)
    for i, query in enumerate(context.query_history, 1):
        print(f"   {i}. {query}")
    
    # Clear conversation
    print("\n🗑️ Clearing conversation...")
    if bot.clear_conversation(conversation_id):
        print("   ✅ Conversation cleared successfully")

def demo_bulk_operations():
    """Demonstrate bulk content operations"""
    print_header("Bulk Operations Demo")
    
    bot = ConversationalQueryBot()
    
    # Prepare bulk content
    print("📦 Preparing bulk content import...")
    
    bulk_content = []
    for i in range(10):
        content = MediaContent(
            id=f"bulk_{i:03d}",
            title=f"Document {i+1}",
            content_type="document" if i % 2 == 0 else "transcript",
            text_content=f"This is sample content {i+1} discussing various topics like "
                        f"{'technology' if i % 3 == 0 else 'business'} and "
                        f"{'innovation' if i % 2 == 0 else 'strategy'}.",
            speaker=f"Speaker {i % 3 + 1}" if i % 2 == 1 else None
        )
        bulk_content.append(content)
    
    # Add all content
    print(f"\n   Adding {len(bulk_content)} items...")
    success_count = 0
    for content in bulk_content:
        if bot.add_content(content):
            success_count += 1
    
    print(f"   ✅ Successfully added {success_count}/{len(bulk_content)} items")
    
    # Query the bulk content
    print("\n🔍 Querying bulk content...")
    
    test_queries = ["technology", "business", "innovation", "strategy"]
    
    for query in test_queries:
        results = bot.query(query, max_results=3)
        print(f"\n   Query: '{query}' - Found {len(results)} results")
        if results:
            print(f"   Top result: {results[0].content.title} (relevance: {results[0].relevance_score:.3f})")

def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("🤖 CONVERSATIONAL QUERY BOT DEMO")
    print("Powered by RAG (Retrieval Augmented Generation)")
    print("="*60)
    
    demos = [
        ("Basic Functionality", demo_basic_functionality),
        ("Advanced Features", demo_advanced_features),
        ("Conversation Management", demo_conversation_management),
        ("Bulk Operations", demo_bulk_operations)
    ]
    
    for name, demo_func in demos:
        input(f"\n⏯️  Press Enter to run {name} demo...")
        try:
            demo_func()
            print(f"\n✅ {name} demo completed successfully!")
        except Exception as e:
            print(f"\n❌ Error in {name} demo: {e}")
    
    print("\n" + "="*60)
    print("🎉 All demos completed!")
    print("="*60)

if __name__ == "__main__":
    main()