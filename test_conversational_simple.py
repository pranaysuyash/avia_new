#!/usr/bin/env python3
"""Simple test for conversational query bot"""

from conversational_query_bot import ConversationalQueryBot, MediaContent

try:
    print("Testing Conversational Query Bot...")
    
    # Initialize bot
    bot = ConversationalQueryBot()
    print("✅ Bot initialized successfully")
    
    # Add sample content
    content = MediaContent(
        id="test_001",
        title="Test Content",
        content_type="transcript",
        text_content="This is a test about budget allocation and marketing strategy."
    )
    
    result = bot.add_content(content)
    print(f"✅ Content added: {result}")
    
    # Query
    results = bot.query("budget")
    print(f"✅ Query returned {len(results)} results")
    
    # Get statistics
    stats = bot.get_statistics()
    print(f"✅ Stats: {stats.get('total_queries')} queries, {stats.get('vector_database', {}).get('total_documents')} documents")
    
    print("\n✅ All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()