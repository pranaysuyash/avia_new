"""
Test Suite for Customer Support System
Tests all components of the comprehensive support system.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import uuid

from customer_support_system import (
    CustomerSupportSystem,
    SupportTicketManager,
    HelpDocumentationSystem,
    ChatSupportSystem,
    TutorialSystem,
    CommunityForumSystem,
    FeedbackSystem,
    TicketStatus,
    TicketPriority,
    ArticleCategory,
    TutorialType,
    SupportTicket,
    HelpArticle,
    Tutorial,
    ForumPost
)


class TestSupportTicketManager(unittest.TestCase):
    """Test support ticket management"""
    
    def setUp(self):
        """Set up test instance"""
        self.ticket_manager = SupportTicketManager()
        self.test_user_id = "test_user_123"
    
    def test_create_ticket(self):
        """Test ticket creation"""
        ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test issue",
            description="This is a test issue description",
            category="technical"
        )
        
        self.assertIsInstance(ticket, SupportTicket)
        self.assertEqual(ticket.user_id, self.test_user_id)
        self.assertEqual(ticket.subject, "Test issue")
        self.assertEqual(ticket.status, TicketStatus.OPEN)
        self.assertIn(ticket.id, self.ticket_manager.tickets)
    
    def test_auto_priority_detection(self):
        """Test automatic priority detection"""
        # Test urgent priority
        urgent_ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="URGENT: System is down",
            description="The entire system is broken and not accessible",
            category="technical"
        )
        self.assertEqual(urgent_ticket.priority, TicketPriority.URGENT)
        
        # Test high priority
        high_ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Error in transcription",
            description="Getting error messages when uploading",
            category="technical"
        )
        self.assertEqual(high_ticket.priority, TicketPriority.HIGH)
        
        # Test medium priority (default)
        medium_ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Question about features",
            description="How do I use the export feature?",
            category="general"
        )
        self.assertEqual(medium_ticket.priority, TicketPriority.MEDIUM)
    
    def test_assign_ticket(self):
        """Test ticket assignment"""
        ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket",
            description="Test",
            category="technical"
        )
        
        result = self.ticket_manager.assign_ticket(ticket.id, "agent123")
        
        self.assertTrue(result)
        self.assertEqual(ticket.assigned_to, "agent123")
        self.assertEqual(ticket.status, TicketStatus.IN_PROGRESS)
        self.assertIn("agent123", self.ticket_manager.agent_assignments)
    
    def test_add_reply(self):
        """Test adding replies to ticket"""
        ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket",
            description="Initial message",
            category="technical"
        )
        
        # Add agent reply
        self.ticket_manager.add_reply(
            ticket.id,
            "I'm looking into this issue",
            is_agent=True
        )
        
        # Add customer reply
        self.ticket_manager.add_reply(
            ticket.id,
            "Thank you for the update",
            is_agent=False
        )
        
        self.assertEqual(len(ticket.conversation), 3)  # Initial + 2 replies
        self.assertEqual(ticket.conversation[1]["type"], "agent")
        self.assertEqual(ticket.conversation[2]["type"], "customer")
    
    def test_resolve_ticket(self):
        """Test ticket resolution"""
        ticket = self.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket",
            description="Test",
            category="technical"
        )
        
        result = self.ticket_manager.resolve_ticket(
            ticket.id,
            "Issue has been resolved",
            satisfaction_rating=5
        )
        
        self.assertTrue(result)
        self.assertEqual(ticket.status, TicketStatus.RESOLVED)
        self.assertIsNotNone(ticket.resolved_at)
        self.assertEqual(ticket.satisfaction_rating, 5)
    
    def test_ticket_metrics(self):
        """Test ticket metrics calculation"""
        # Create multiple tickets
        for i in range(5):
            ticket = self.ticket_manager.create_ticket(
                user_id=f"user_{i}",
                subject=f"Issue {i}",
                description="Test",
                category="technical"
            )
            
            if i < 2:  # Resolve first 2 tickets
                self.ticket_manager.resolve_ticket(
                    ticket.id,
                    "Resolved",
                    satisfaction_rating=4 + i
                )
        
        metrics = self.ticket_manager.get_ticket_metrics()
        
        self.assertEqual(metrics["total_tickets"], 5)
        self.assertEqual(metrics["open_tickets"], 3)
        self.assertIn("status_distribution", metrics)
        self.assertIn("priority_distribution", metrics)
        self.assertGreater(metrics["satisfaction_score"], 0)


class TestHelpDocumentationSystem(unittest.TestCase):
    """Test help documentation system"""
    
    def setUp(self):
        """Set up test instance"""
        self.help_docs = HelpDocumentationSystem()
    
    def test_default_content(self):
        """Test default FAQ and articles are loaded"""
        self.assertGreater(len(self.help_docs.faq_items), 0)
        self.assertGreater(len(self.help_docs.articles), 0)
    
    def test_create_article(self):
        """Test article creation"""
        article = self.help_docs.create_article(
            title="Test Article",
            content="# Test Content\n\nThis is a test article.",
            category=ArticleCategory.TECHNICAL,
            tags=["test", "example"],
            author="Test Author"
        )
        
        self.assertIsInstance(article, HelpArticle)
        self.assertEqual(article.title, "Test Article")
        self.assertEqual(article.category, ArticleCategory.TECHNICAL)
        self.assertIn("test", article.tags)
        self.assertIn(article.id, self.help_docs.articles)
    
    def test_search_articles(self):
        """Test article search functionality"""
        # Create test articles
        self.help_docs.create_article(
            title="Transcription Accuracy Guide",
            content="How to improve transcription accuracy",
            category=ArticleCategory.TRANSCRIPTION,
            tags=["accuracy", "guide"],
            author="Test"
        )
        
        self.help_docs.create_article(
            title="Billing FAQ",
            content="Common billing questions",
            category=ArticleCategory.BILLING,
            tags=["billing", "faq"],
            author="Test"
        )
        
        # Search for accuracy
        results = self.help_docs.search_articles("accuracy")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("accuracy" in article.title.lower() or 
                           "accuracy" in article.tags 
                           for article in results))
        
        # Search with category filter
        billing_results = self.help_docs.search_articles(
            "billing",
            category=ArticleCategory.BILLING
        )
        self.assertTrue(all(article.category == ArticleCategory.BILLING 
                           for article in billing_results))
    
    def test_article_feedback(self):
        """Test article helpfulness feedback"""
        article = list(self.help_docs.articles.values())[0]
        initial_helpful = article.helpful_count
        initial_not_helpful = article.not_helpful_count
        
        # Mark as helpful
        result = self.help_docs.mark_article_helpful(article.id, True)
        self.assertTrue(result)
        self.assertEqual(article.helpful_count, initial_helpful + 1)
        
        # Mark as not helpful
        result = self.help_docs.mark_article_helpful(article.id, False)
        self.assertTrue(result)
        self.assertEqual(article.not_helpful_count, initial_not_helpful + 1)


class TestChatSupportSystem(unittest.TestCase):
    """Test chat support system"""
    
    def setUp(self):
        """Set up test instance"""
        self.chat_support = ChatSupportSystem()
        self.test_user_id = "test_user_123"
    
    def test_start_chat_session(self):
        """Test starting a chat session"""
        session_id = self.chat_support.start_chat_session(self.test_user_id)
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.chat_support.chat_sessions)
        
        # Check initial message
        messages = self.chat_support.chat_sessions[session_id]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "assistant")
    
    def test_process_message(self):
        """Test message processing"""
        session_id = self.chat_support.start_chat_session(self.test_user_id)
        
        # Send user message
        response = self.chat_support.process_message(
            session_id,
            "I need help with transcription"
        )
        
        self.assertIn("message", response)
        self.assertIsInstance(response["message"], str)
        
        # Check conversation history
        messages = self.chat_support.chat_sessions[session_id]
        self.assertGreater(len(messages), 2)  # Initial + user + assistant
    
    def test_escalation_triggers(self):
        """Test human escalation triggers"""
        session_id = self.chat_support.start_chat_session(self.test_user_id)
        
        # Test escalation trigger
        response = self.chat_support.process_message(
            session_id,
            "I want to speak to a human agent"
        )
        
        self.assertTrue(response.get("escalated", False))
        self.assertIn("agent_available", response)
    
    def test_suggested_articles(self):
        """Test article suggestions"""
        session_id = self.chat_support.start_chat_session(self.test_user_id)
        
        response = self.chat_support.process_message(
            session_id,
            "How do I improve transcription accuracy?"
        )
        
        # Should categorize as transcription help
        self.assertEqual(response.get("category"), "transcription_help")
        self.assertIsInstance(response.get("suggested_articles"), list)


class TestTutorialSystem(unittest.TestCase):
    """Test tutorial system"""
    
    def setUp(self):
        """Set up test instance"""
        self.tutorials = TutorialSystem()
    
    def test_default_tutorials(self):
        """Test default tutorials are loaded"""
        self.assertGreater(len(self.tutorials.tutorials), 0)
        self.assertGreater(len(self.tutorials.learning_paths), 0)
    
    def test_create_tutorial(self):
        """Test tutorial creation"""
        tutorial = self.tutorials.create_tutorial(
            title="Test Tutorial",
            description="Test description",
            type=TutorialType.VIDEO,
            duration_minutes=10,
            difficulty="beginner",
            content_url="https://example.com/tutorial",
            learning_objectives=["Objective 1", "Objective 2"]
        )
        
        self.assertIsInstance(tutorial, Tutorial)
        self.assertEqual(tutorial.title, "Test Tutorial")
        self.assertEqual(tutorial.type, TutorialType.VIDEO)
        self.assertEqual(tutorial.duration_minutes, 10)
        self.assertIn(tutorial.id, self.tutorials.tutorials)
    
    def test_learning_paths(self):
        """Test learning path retrieval"""
        # Test beginner path
        beginner_path = self.tutorials.get_learning_path("beginner")
        self.assertIsInstance(beginner_path, list)
        self.assertGreater(len(beginner_path), 0)
        
        # Test developer path
        dev_path = self.tutorials.get_learning_path("developer")
        self.assertIsInstance(dev_path, list)
        
        # Test default path for unknown type
        unknown_path = self.tutorials.get_learning_path("unknown")
        self.assertEqual(unknown_path, beginner_path)  # Should default to beginner
    
    def test_track_progress(self):
        """Test tutorial progress tracking"""
        tutorial = list(self.tutorials.tutorials.values())[0]
        
        # Track progress
        result = self.tutorials.track_progress(
            self.test_user_id,
            tutorial.id,
            75.0
        )
        
        self.assertTrue(result)
        
        # Track completion (>90%)
        initial_completion = tutorial.completion_rate
        result = self.tutorials.track_progress(
            self.test_user_id,
            tutorial.id,
            95.0
        )
        
        self.assertTrue(result)
        self.assertGreaterEqual(tutorial.completion_rate, initial_completion)


class TestCommunityForumSystem(unittest.TestCase):
    """Test community forum system"""
    
    def setUp(self):
        """Set up test instance"""
        self.forum = CommunityForumSystem()
        self.test_user_id = "test_user_123"
    
    def test_create_post(self):
        """Test forum post creation"""
        post = self.forum.create_post(
            author_id=self.test_user_id,
            title="Test Post",
            content="This is a test post content",
            category="General Discussion",
            tags=["test", "example"]
        )
        
        self.assertIsInstance(post, ForumPost)
        self.assertEqual(post.author_id, self.test_user_id)
        self.assertEqual(post.title, "Test Post")
        self.assertIn(post.id, self.forum.posts)
        
        # Check reputation awarded
        self.assertEqual(self.forum.user_reputation[self.test_user_id], 5)
    
    def test_add_reply(self):
        """Test adding replies to posts"""
        post = self.forum.create_post(
            author_id=self.test_user_id,
            title="Test Post",
            content="Test content",
            category="General Discussion",
            tags=[]
        )
        
        # Add reply
        reply_id = self.forum.add_reply(
            post.id,
            "user456",
            "This is a helpful reply"
        )
        
        self.assertIsNotNone(reply_id)
        self.assertEqual(len(post.replies), 1)
        self.assertEqual(post.replies[0]["author_id"], "user456")
        
        # Check reputation awarded for reply
        self.assertEqual(self.forum.user_reputation["user456"], 2)
    
    def test_upvote_post(self):
        """Test post upvoting"""
        post = self.forum.create_post(
            author_id=self.test_user_id,
            title="Test Post",
            content="Test content",
            category="General Discussion",
            tags=[]
        )
        
        initial_upvotes = post.upvotes
        initial_reputation = self.forum.user_reputation[self.test_user_id]
        
        # Upvote post
        result = self.forum.upvote_post(post.id, "voter123")
        
        self.assertTrue(result)
        self.assertEqual(post.upvotes, initial_upvotes + 1)
        self.assertEqual(
            self.forum.user_reputation[self.test_user_id],
            initial_reputation + 10
        )
    
    def test_mark_as_solved(self):
        """Test marking post as solved"""
        post = self.forum.create_post(
            author_id=self.test_user_id,
            title="Help needed",
            content="I need help with this",
            category="General Discussion",
            tags=[]
        )
        
        # Add answer
        answer_id = self.forum.add_reply(
            post.id,
            "helper123",
            "Here's the solution"
        )
        
        initial_reputation = self.forum.user_reputation["helper123"]
        
        # Mark as solved
        result = self.forum.mark_as_solved(post.id, answer_id)
        
        self.assertTrue(result)
        self.assertTrue(post.is_solved)
        self.assertEqual(post.accepted_answer_id, answer_id)
        self.assertEqual(
            self.forum.user_reputation["helper123"],
            initial_reputation + 25
        )
    
    def test_search_posts(self):
        """Test forum search functionality"""
        # Create test posts
        post1 = self.forum.create_post(
            author_id="user1",
            title="Transcription tips",
            content="Here are some tips for better transcription",
            category="Tips & Tricks",
            tags=["transcription", "tips"]
        )
        
        post2 = self.forum.create_post(
            author_id="user2",
            title="API question",
            content="How do I use the API?",
            category="API & Development",
            tags=["api", "development"]
        )
        
        # Search for transcription
        results = self.forum.search_posts("transcription")
        self.assertGreater(len(results), 0)
        self.assertIn(post1, results)
        
        # Search with category filter
        api_results = self.forum.search_posts(
            "api",
            category="API & Development"
        )
        self.assertIn(post2, api_results)
        
        # Search for solved posts only
        self.forum.mark_as_solved(post1.id, "answer123")
        solved_results = self.forum.search_posts(
            "",
            solved_only=True
        )
        self.assertTrue(all(post.is_solved for post in solved_results))


class TestFeedbackSystem(unittest.TestCase):
    """Test feedback and feature request system"""
    
    def setUp(self):
        """Set up test instance"""
        self.feedback = FeedbackSystem()
        self.test_user_id = "test_user_123"
    
    def test_submit_feedback(self):
        """Test feedback submission"""
        feedback_id = self.feedback.submit_feedback(
            user_id=self.test_user_id,
            category="Bug Report",
            subject="Button not working",
            description="The export button doesn't work",
            rating=3
        )
        
        self.assertIsNotNone(feedback_id)
        self.assertEqual(len(self.feedback.feedback_items), 1)
        
        feedback = self.feedback.feedback_items[0]
        self.assertEqual(feedback["user_id"], self.test_user_id)
        self.assertEqual(feedback["category"], "Bug Report")
        self.assertEqual(feedback["rating"], 3)
    
    def test_priority_calculation(self):
        """Test feedback priority calculation"""
        # High priority bug
        high_priority_id = self.feedback.submit_feedback(
            user_id=self.test_user_id,
            category="Bug Report",
            subject="App crashes",
            description="The app crashes when I upload files",
            rating=1
        )
        
        # Low priority feedback
        low_priority_id = self.feedback.submit_feedback(
            user_id=self.test_user_id,
            category="User Experience",
            subject="Color suggestion",
            description="I think blue would be better",
            rating=4
        )
        
        high_priority = next(f for f in self.feedback.feedback_items 
                           if f["id"] == high_priority_id)
        low_priority = next(f for f in self.feedback.feedback_items 
                          if f["id"] == low_priority_id)
        
        self.assertEqual(high_priority["priority"], "high")
        self.assertEqual(low_priority["priority"], "low")
    
    def test_create_feature_request(self):
        """Test feature request creation"""
        request_id = self.feedback.create_feature_request(
            user_id=self.test_user_id,
            title="Dark mode",
            description="Please add dark mode support"
        )
        
        self.assertIsNotNone(request_id)
        self.assertIn(request_id, self.feedback.feature_requests)
        
        request = self.feedback.feature_requests[request_id]
        self.assertEqual(request["title"], "Dark mode")
        self.assertEqual(request["upvotes"], 1)  # Creator auto-upvotes
        self.assertEqual(request["status"], "under_review")
    
    def test_upvote_feature_request(self):
        """Test feature request upvoting"""
        request_id = self.feedback.create_feature_request(
            user_id=self.test_user_id,
            title="Test feature",
            description="Test"
        )
        
        initial_upvotes = self.feedback.feature_requests[request_id]["upvotes"]
        
        # Upvote
        result = self.feedback.upvote_feature_request(request_id, "voter123")
        
        self.assertTrue(result)
        self.assertEqual(
            self.feedback.feature_requests[request_id]["upvotes"],
            initial_upvotes + 1
        )
    
    def test_trending_features(self):
        """Test trending feature requests"""
        # Create multiple feature requests with different upvotes
        features = []
        for i in range(5):
            request_id = self.feedback.create_feature_request(
                user_id=f"user_{i}",
                title=f"Feature {i}",
                description=f"Description {i}"
            )
            
            # Add varying upvotes
            for j in range(i * 2):
                self.feedback.upvote_feature_request(request_id, f"voter_{j}")
            
            features.append(request_id)
        
        # Get trending features
        trending = self.feedback.get_trending_features(3)
        
        self.assertEqual(len(trending), 3)
        # Should be sorted by upvotes descending
        self.assertGreater(trending[0]["upvotes"], trending[1]["upvotes"])
        self.assertGreater(trending[1]["upvotes"], trending[2]["upvotes"])
    
    def test_feedback_summary(self):
        """Test feedback summary statistics"""
        # Create various feedback items
        for i in range(5):
            self.feedback.submit_feedback(
                user_id=f"user_{i}",
                category="Bug Report" if i < 2 else "Feature Request",
                subject=f"Feedback {i}",
                description="Test",
                rating=3 + (i % 3)
            )
        
        summary = self.feedback.get_feedback_summary()
        
        self.assertEqual(summary["total_feedback"], 5)
        self.assertGreater(summary["average_rating"], 0)
        self.assertIn("Bug Report", summary["category_distribution"])
        self.assertIn("Feature Request", summary["category_distribution"])


class TestCustomerSupportSystem(unittest.TestCase):
    """Test the integrated customer support system"""
    
    def setUp(self):
        """Set up test instance"""
        self.system = CustomerSupportSystem()
        self.test_user_id = "test_user_123"
    
    def test_system_initialization(self):
        """Test all components are initialized"""
        self.assertIsInstance(self.system.ticket_manager, SupportTicketManager)
        self.assertIsInstance(self.system.help_docs, HelpDocumentationSystem)
        self.assertIsInstance(self.system.chat_support, ChatSupportSystem)
        self.assertIsInstance(self.system.tutorials, TutorialSystem)
        self.assertIsInstance(self.system.forum, CommunityForumSystem)
        self.assertIsInstance(self.system.feedback, FeedbackSystem)
    
    def test_support_dashboard(self):
        """Test support dashboard data"""
        # Create some test data
        self.system.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket",
            description="Test",
            category="technical"
        )
        
        self.system.forum.create_post(
            author_id=self.test_user_id,
            title="Test post",
            content="Test",
            category="General",
            tags=[]
        )
        
        dashboard = self.system.get_support_dashboard()
        
        self.assertIn("tickets", dashboard)
        self.assertIn("help_articles", dashboard)
        self.assertIn("tutorials", dashboard)
        self.assertIn("forum", dashboard)
        self.assertIn("feedback", dashboard)
        self.assertIn("chat_sessions", dashboard)
    
    def test_search_all_resources(self):
        """Test cross-resource search"""
        # Create test content
        self.system.help_docs.create_article(
            title="Transcription Guide",
            content="Guide for transcription",
            category=ArticleCategory.TRANSCRIPTION,
            tags=["transcription"],
            author="Test"
        )
        
        self.system.forum.create_post(
            author_id=self.test_user_id,
            title="Transcription tips",
            content="Tips for transcription",
            category="Tips",
            tags=["transcription"]
        )
        
        # Search across all resources
        results = self.system.search_all_resources("transcription")
        
        self.assertIn("help_articles", results)
        self.assertIn("faq", results)
        self.assertIn("forum_posts", results)
        self.assertIn("tutorials", results)
        
        self.assertGreater(len(results["help_articles"]), 0)
        self.assertGreater(len(results["forum_posts"]), 0)
    
    def test_user_support_history(self):
        """Test user support history tracking"""
        # Create user activity
        self.system.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket 1",
            description="Test",
            category="technical"
        )
        
        self.system.ticket_manager.create_ticket(
            user_id=self.test_user_id,
            subject="Test ticket 2",
            description="Test",
            category="billing"
        )
        
        self.system.forum.create_post(
            author_id=self.test_user_id,
            title="My post",
            content="Content",
            category="General",
            tags=[]
        )
        
        self.system.feedback.submit_feedback(
            user_id=self.test_user_id,
            category="Feature Request",
            subject="New feature",
            description="Please add this",
            rating=4
        )
        
        # Get history
        history = self.system.get_user_support_history(self.test_user_id)
        
        self.assertEqual(history["tickets"], 2)
        self.assertEqual(history["forum_posts"], 1)
        self.assertGreater(history["forum_reputation"], 0)
        self.assertEqual(history["feedback_submitted"], 1)
        self.assertIsNotNone(history["last_interaction"])


if __name__ == "__main__":
    unittest.main()