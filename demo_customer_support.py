"""
Demo script for Customer Support System
Shows comprehensive support features including tickets, chat, help center, tutorials, forum, and feedback.
"""
import asyncio
from datetime import datetime, timedelta
from customer_support_system import (
    CustomerSupportSystem,
    TicketPriority,
    ArticleCategory,
    TutorialType
)

def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print('='*60)

def print_result(operation: str, result=None):
    """Print operation result"""
    print(f"\n✓ {operation}")
    if result:
        print(f"  Result: {result}")

async def demo_support_tickets():
    """Demonstrate support ticket functionality"""
    print_section("Support Ticket Management")
    
    system = CustomerSupportSystem()
    
    # Create tickets
    print("\n1. Creating support tickets...")
    
    ticket1 = system.ticket_manager.create_ticket(
        user_id="user123",
        subject="Transcription not working for large files",
        description="I'm trying to transcribe a 2-hour video but it keeps failing after 30 minutes.",
        category="technical",
        attachments=[{"name": "error_log.txt", "size": 1024}]
    )
    print_result(f"Created ticket {ticket1.id} - Priority: {ticket1.priority.value}")
    
    ticket2 = system.ticket_manager.create_ticket(
        user_id="user456",
        subject="Billing question about subscription",
        description="I was charged twice this month. Can you please check?",
        category="billing"
    )
    print_result(f"Created ticket {ticket2.id} - Priority: {ticket2.priority.value}")
    
    # Assign ticket
    print("\n2. Assigning ticket to agent...")
    system.ticket_manager.assign_ticket(ticket1.id, "agent001")
    print_result(f"Ticket {ticket1.id} assigned to agent001")
    
    # Add replies
    print("\n3. Adding replies to ticket...")
    system.ticket_manager.add_reply(
        ticket1.id,
        "I've reviewed your error log. It seems the issue is with memory allocation. Let me provide a solution.",
        is_agent=True
    )
    
    system.ticket_manager.add_reply(
        ticket1.id,
        "Thank you! I'll try the solution you provided.",
        is_agent=False
    )
    print_result(f"Added 2 replies to ticket {ticket1.id}")
    
    # Resolve ticket
    print("\n4. Resolving ticket...")
    system.ticket_manager.resolve_ticket(
        ticket1.id,
        "Issue resolved by increasing memory allocation settings",
        satisfaction_rating=5
    )
    print_result(f"Ticket {ticket1.id} resolved with rating 5/5")
    
    # Get metrics
    print("\n5. Ticket metrics:")
    metrics = system.ticket_manager.get_ticket_metrics()
    print(f"  - Total tickets: {metrics['total_tickets']}")
    print(f"  - Open tickets: {metrics['open_tickets']}")
    print(f"  - Avg resolution time: {metrics['avg_resolution_time_hours']:.1f} hours")
    print(f"  - Satisfaction score: {metrics['satisfaction_score']:.1f}/5")

async def demo_live_chat():
    """Demonstrate live chat support"""
    print_section("Live Chat Support")
    
    system = CustomerSupportSystem()
    
    # Start chat session
    print("\n1. Starting chat session...")
    session_id = system.chat_support.start_chat_session("user123")
    print_result(f"Chat session started: {session_id}")
    
    # Simulate chat conversation
    messages = [
        "Hi, I need help with transcription accuracy",
        "My transcriptions are missing some words",
        "Can I speak to a human agent?",
    ]
    
    print("\n2. Chat conversation:")
    for msg in messages:
        print(f"\n  User: {msg}")
        response = system.chat_support.process_message(session_id, msg)
        print(f"  Assistant: {response['message']}")
        
        if response.get('suggested_articles'):
            print("  Suggested articles:")
            for article in response['suggested_articles']:
                print(f"    - {article['title']}")
        
        if response.get('escalated'):
            print("  [Chat escalated to human agent]")

async def demo_help_center():
    """Demonstrate help documentation system"""
    print_section("Help Center & Documentation")
    
    system = CustomerSupportSystem()
    
    # Create help articles
    print("\n1. Creating help articles...")
    
    article1 = system.help_docs.create_article(
        title="How to Improve Transcription Accuracy",
        content="""# How to Improve Transcription Accuracy

## Tips for Better Results

1. **Use high-quality audio**: Clear audio with minimal background noise
2. **Proper microphone placement**: Keep microphone 6-12 inches from speaker
3. **Speak clearly**: Avoid mumbling or speaking too fast
4. **Add custom vocabulary**: Include technical terms specific to your field

## Audio Requirements

- Supported formats: MP3, WAV, M4A, MP4
- Recommended bitrate: 128 kbps or higher
- Sample rate: 16 kHz or higher
""",
        category=ArticleCategory.TRANSCRIPTION,
        tags=["accuracy", "audio quality", "best practices"],
        author="Support Team"
    )
    print_result(f"Created article: {article1.title}")
    
    # Search articles
    print("\n2. Searching help articles...")
    results = system.help_docs.search_articles("accuracy")
    print_result(f"Found {len(results)} articles matching 'accuracy'")
    for article in results[:3]:
        print(f"  - {article.title} (Views: {article.views})")
    
    # Mark article as helpful
    print("\n3. User feedback on article...")
    system.help_docs.mark_article_helpful(article1.id, True)
    article1.views = 150  # Simulate views
    print_result(f"Article marked as helpful (Views: {article1.views})")
    
    # Show FAQ
    print("\n4. Frequently Asked Questions:")
    for faq in system.help_docs.faq_items[:3]:
        print(f"\n  Q: {faq['question']}")
        print(f"  A: {faq['answer'][:100]}...")

async def demo_tutorials():
    """Demonstrate tutorial system"""
    print_section("Video Tutorials & Learning Paths")
    
    system = CustomerSupportSystem()
    
    # Get learning path
    print("\n1. Learning path for beginners:")
    learning_path = system.tutorials.get_learning_path("beginner")
    for i, tutorial in enumerate(learning_path):
        print(f"\n  Step {i+1}: {tutorial.title}")
        print(f"    - Duration: {tutorial.duration_minutes} minutes")
        print(f"    - Difficulty: {tutorial.difficulty}")
        print(f"    - Learning objectives:")
        for obj in tutorial.learning_objectives[:2]:
            print(f"      • {obj}")
    
    # Track progress
    print("\n2. Tracking tutorial progress...")
    tutorial_id = learning_path[0].id if learning_path else "tutorial_123"
    system.tutorials.track_progress("user123", tutorial_id, 75.0)
    print_result("Tutorial progress: 75% complete")
    
    # Show tutorial metrics
    print("\n3. Tutorial engagement metrics:")
    print("  - Total tutorials: 3")
    print("  - Average completion rate: 68%")
    print("  - Most popular: 'Getting Started with Video NER'")

async def demo_community_forum():
    """Demonstrate community forum"""
    print_section("Community Forum")
    
    system = CustomerSupportSystem()
    
    # Create forum post
    print("\n1. Creating forum post...")
    post = system.forum.create_post(
        author_id="user123",
        title="Tips for transcribing multiple speakers",
        content="I've found that using speaker diarization really helps when transcribing meetings. Here are my tips...",
        category="Tips & Tricks",
        tags=["diarization", "meetings", "multiple speakers"]
    )
    print_result(f"Created post: {post.title}")
    
    # Add replies
    print("\n2. Community engagement...")
    reply_id = system.forum.add_reply(
        post.id,
        "user456",
        "Great tips! I also recommend using a good microphone array for better speaker separation."
    )
    print_result("Added reply to post")
    
    # Upvote and mark as solved
    system.forum.upvote_post(post.id, "user789")
    print_result("Post upvoted (Reputation +10 for author)")
    
    if reply_id:
        system.forum.mark_as_solved(post.id, reply_id)
        print_result("Post marked as solved (Reputation +25 for answer author)")
    
    # Search forum
    print("\n3. Searching forum posts...")
    search_results = system.forum.search_posts("speaker")
    print_result(f"Found {len(search_results)} posts about 'speaker'")
    
    # Show user reputation
    print("\n4. Top community contributors:")
    print(f"  - user123: {system.forum.user_reputation['user123']} reputation points")
    print(f"  - user456: {system.forum.user_reputation['user456']} reputation points")

async def demo_feedback_system():
    """Demonstrate feedback and feature request system"""
    print_section("Feedback & Feature Requests")
    
    system = CustomerSupportSystem()
    
    # Submit feedback
    print("\n1. Submitting user feedback...")
    feedback_id = system.feedback.submit_feedback(
        user_id="user123",
        category="Feature Request",
        subject="Add real-time collaboration",
        description="It would be great to have real-time collaboration on transcripts, similar to Google Docs.",
        rating=4
    )
    print_result(f"Feedback submitted: {feedback_id}")
    
    # Create feature requests
    print("\n2. Feature requests from users...")
    
    request1_id = system.feedback.create_feature_request(
        "user456",
        "Dark mode for the interface",
        "Please add a dark mode option for late night work sessions."
    )
    
    request2_id = system.feedback.create_feature_request(
        "user789",
        "Batch export to multiple formats",
        "Allow exporting multiple transcripts at once in different formats."
    )
    print_result("Created 2 feature requests")
    
    # Upvote features
    print("\n3. Community voting on features...")
    for _ in range(15):
        system.feedback.upvote_feature_request(request1_id, f"user_{_}")
    for _ in range(8):
        system.feedback.upvote_feature_request(request2_id, f"user_{_}")
    
    # Show trending features
    print("\n4. Trending feature requests:")
    trending = system.feedback.get_trending_features(3)
    for i, feature in enumerate(trending):
        print(f"\n  #{i+1}: {feature['title']}")
        print(f"      Upvotes: {feature['upvotes']}")
        print(f"      Status: {feature['status']}")
    
    # Feedback summary
    print("\n5. Feedback summary:")
    summary = system.feedback.get_feedback_summary()
    print(f"  - Total feedback: {summary['total_feedback']}")
    print(f"  - Average rating: {summary['average_rating']:.1f}/5")
    print(f"  - Feature requests: {summary['total_feature_requests']}")

async def demo_support_dashboard():
    """Demonstrate comprehensive support dashboard"""
    print_section("Support Dashboard Overview")
    
    system = CustomerSupportSystem()
    
    # Get dashboard data
    dashboard = system.get_support_dashboard()
    
    print("\n1. Support Metrics Overview:")
    print(f"  - Open tickets: {dashboard['tickets']['open_tickets']}")
    print(f"  - Avg resolution time: {dashboard['tickets']['avg_resolution_time_hours']:.1f} hours")
    print(f"  - Chat sessions: {dashboard['chat_sessions']}")
    print(f"  - Help articles: {dashboard['help_articles']['total']}")
    print(f"  - Forum posts: {dashboard['forum']['total_posts']}")
    print(f"  - Active forum users: {dashboard['forum']['active_users']}")
    
    print("\n2. User Support History:")
    history = system.get_user_support_history("user123")
    print(f"  - Tickets created: {history['tickets']}")
    print(f"  - Forum posts: {history['forum_posts']}")
    print(f"  - Forum reputation: {history['forum_reputation']}")
    print(f"  - Feedback submitted: {history['feedback_submitted']}")
    
    print("\n3. Cross-Resource Search:")
    search_results = system.search_all_resources("transcription")
    print(f"  - Help articles found: {len(search_results['help_articles'])}")
    print(f"  - FAQ matches: {len(search_results['faq'])}")
    print(f"  - Forum posts found: {len(search_results['forum_posts'])}")
    print(f"  - Tutorials found: {len(search_results['tutorials'])}")

async def main():
    """Run all customer support demos"""
    print("="*60)
    print("Customer Support System Demo")
    print("="*60)
    
    # Run all demos
    await demo_support_tickets()
    await demo_live_chat()
    await demo_help_center()
    await demo_tutorials()
    await demo_community_forum()
    await demo_feedback_system()
    await demo_support_dashboard()
    
    print_section("Demo Completed Successfully!")
    
    print("\n🎯 Key Features Demonstrated:")
    print("1. Support ticket management with auto-prioritization")
    print("2. AI-powered live chat with escalation")
    print("3. Comprehensive help documentation and FAQ")
    print("4. Video tutorials with learning paths")
    print("5. Community forum with reputation system")
    print("6. Feedback and feature request tracking")
    print("7. Unified support dashboard")
    print("8. Cross-resource search capabilities")
    
    print("\n📊 Benefits:")
    print("• Reduced support response time")
    print("• Self-service options for users")
    print("• Community-driven support")
    print("• Data-driven feature prioritization")
    print("• Comprehensive support metrics")

if __name__ == "__main__":
    asyncio.run(main())