"""
Comprehensive tests for Production Meeting Communication System

Tests all major functionality including:
- Real API integration architecture
- NLP entity extraction and action item identification
- Meeting management and communication
- Database operations and analytics
- Multi-platform integrations

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from production_meeting_system import (
    ProductionMeetingSystem,
    MeetingEvent,
    MeetingParticipant,
    ActionItem,
    MeetingMinutes,
    APICredentials,
    PlatformType,
    EventType,
    TaskPriority,
    GoogleCalendarIntegration,
    SlackIntegration,
    JiraIntegration,
    EmailIntegration,
    MeetingEntityExtractor,
    MeetingDatabase
)


class TestProductionMeetingSystem(unittest.TestCase):
    """Test suite for Production Meeting Communication System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_meeting_system.db")
        self.system = ProductionMeetingSystem(db_path=self.db_path)
        
        # Sample data
        self.sample_participants = [
            MeetingParticipant(email="alice@test.com", name="Alice", role="organizer"),
            MeetingParticipant(email="bob@test.com", name="Bob", role="attendee"),
        ]
        
        self.sample_meeting = MeetingEvent(
            event_id="test_meeting_001",
            title="Test Meeting",
            description="A test meeting",
            start_time=datetime.now() + timedelta(hours=1),
            end_time=datetime.now() + timedelta(hours=2),
            participants=self.sample_participants
        )
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.system, ProductionMeetingSystem)
        self.assertIsInstance(self.system.db, MeetingDatabase)
        self.assertIsInstance(self.system.entity_extractor, MeetingEntityExtractor)
        self.assertIsNotNone(self.system.config)
    
    def test_meeting_participant_creation(self):
        """Test MeetingParticipant dataclass"""
        participant = MeetingParticipant(
            email="test@example.com",
            name="Test User",
            role="attendee"
        )
        
        self.assertEqual(participant.email, "test@example.com")
        self.assertEqual(participant.name, "Test User")
        self.assertEqual(participant.role, "attendee")
        self.assertEqual(participant.response_status, "needsAction")
        self.assertFalse(participant.is_external)
    
    def test_meeting_event_creation(self):
        """Test MeetingEvent dataclass"""
        meeting = MeetingEvent(
            event_id="test_001",
            title="Test Meeting",
            description="Test description",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            participants=self.sample_participants
        )
        
        self.assertEqual(meeting.event_id, "test_001")
        self.assertEqual(meeting.title, "Test Meeting")
        self.assertEqual(len(meeting.participants), 2)
        self.assertIsNotNone(meeting.created_at)
        self.assertIsNotNone(meeting.updated_at)
    
    def test_action_item_creation(self):
        """Test ActionItem dataclass"""
        action_item = ActionItem(
            item_id="action_001",
            description="Complete testing",
            assignee="alice@test.com",
            due_date=datetime.now() + timedelta(days=7),
            priority=TaskPriority.HIGH
        )
        
        self.assertEqual(action_item.item_id, "action_001")
        self.assertEqual(action_item.description, "Complete testing")
        self.assertEqual(action_item.assignee, "alice@test.com")
        self.assertEqual(action_item.priority, TaskPriority.HIGH)
        self.assertEqual(action_item.status, "open")
        self.assertIsNotNone(action_item.created_at)
    
    def test_api_credentials(self):
        """Test APICredentials dataclass"""
        # Create non-expired credentials
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        creds = APICredentials(
            platform=PlatformType.GOOGLE_CALENDAR,
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token",
            expires_at=future_time
        )
        
        self.assertEqual(creds.platform, PlatformType.GOOGLE_CALENDAR)
        self.assertFalse(creds.is_expired())  # Should not be expired
    
    def test_database_operations(self):
        """Test database operations"""
        db = MeetingDatabase(self.db_path)
        
        # Test storing meeting event
        meeting_id = db.store_meeting_event(self.sample_meeting)
        self.assertGreater(meeting_id, 0)
        
        # Test storing action items
        action_items = [
            ActionItem(
                item_id="test_001",
                description="Test action",
                assignee="alice@test.com",
                due_date=None,
                priority=TaskPriority.MEDIUM
            )
        ]
        
        stored_ids = db.store_action_items(action_items)
        self.assertEqual(len(stored_ids), 1)
        self.assertGreater(stored_ids[0], 0)
        
        # Test retrieving pending action items
        pending = db.get_pending_action_items()
        self.assertGreater(len(pending), 0)
        self.assertEqual(pending[0].item_id, "test_001")
    
    def test_entity_extractor(self):
        """Test MeetingEntityExtractor"""
        extractor = MeetingEntityExtractor()
        
        sample_transcript = """
        Alice: We need to complete the project by Friday.
        Bob: I'll handle the testing and documentation.
        Charlie: The critical bug in payment system needs immediate attention.
        Alice: Let's assign that to Bob as high priority.
        """
        
        # Test action item extraction
        action_items = extractor.extract_action_items(sample_transcript, "test_meeting")
        self.assertGreater(len(action_items), 0)
        
        # Check that action items have required fields
        for item in action_items:
            self.assertIsNotNone(item.item_id)
            self.assertIsNotNone(item.description)
            self.assertIsInstance(item.priority, TaskPriority)
            self.assertEqual(item.meeting_id, "test_meeting")
        
        # Test key points extraction
        key_points = extractor.extract_key_points(sample_transcript)
        self.assertIsInstance(key_points, list)
    
    def test_priority_determination(self):
        """Test priority determination from text"""
        extractor = MeetingEntityExtractor()
        
        test_cases = [
            ("This is critical and urgent", TaskPriority.CRITICAL),
            ("High priority task", TaskPriority.HIGH),
            ("Medium importance", TaskPriority.MEDIUM),
            ("Low priority when time permits", TaskPriority.LOW),
            ("Regular task", TaskPriority.MEDIUM)  # Default
        ]
        
        for text, expected_priority in test_cases:
            priority = extractor._determine_priority(text)
            self.assertEqual(priority, expected_priority)
    
    def test_date_parsing(self):
        """Test date parsing functionality"""
        extractor = MeetingEntityExtractor()
        
        test_cases = [
            "12/25/2023",
            "12-25-2023",
            "2023-12-25",
            "25/12/2023",
            "invalid_date"
        ]
        
        for date_str in test_cases:
            result = extractor._parse_date(date_str)
            if date_str == "invalid_date":
                self.assertIsNone(result)
            else:
                self.assertIsInstance(result, datetime)
    
    def test_google_calendar_integration(self):
        """Test Google Calendar integration"""
        creds = APICredentials(
            platform=PlatformType.GOOGLE_CALENDAR,
            client_id="test_id",
            client_secret="test_secret",
            access_token="test_token"
        )
        
        integration = GoogleCalendarIntegration(creds)
        self.assertEqual(integration.credentials, creds)
        self.assertIsNotNone(integration.scopes)
    
    @patch('production_meeting_system.aiohttp.ClientSession')
    async def test_slack_integration(self, mock_session):
        """Test Slack integration"""
        # Mock the aiohttp response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"ok": True}
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        creds = APICredentials(
            platform=PlatformType.SLACK,
            api_key="test_token"
        )
        
        integration = SlackIntegration(creds)
        
        # Test sending message
        result = await integration.send_message("#test", "Hello World")
        self.assertTrue(result)
        
        # Test meeting notification
        result = await integration.create_meeting_notification(self.sample_meeting, [])
        self.assertTrue(result)
    
    @patch('production_meeting_system.aiohttp.ClientSession')
    async def test_jira_integration(self, mock_session):
        """Test JIRA integration"""
        # Mock the aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"key": "MEET-123"}
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
        
        creds = APICredentials(
            platform=PlatformType.JIRA,
            api_key="test_token"
        )
        
        integration = JiraIntegration(creds, "https://test.atlassian.net")
        
        action_item = ActionItem(
            item_id="test_001",
            description="Test JIRA task",
            assignee="test@example.com",
            due_date=datetime.now() + timedelta(days=7),
            priority=TaskPriority.HIGH
        )
        
        result = await integration.create_task(action_item, "TEST")
        self.assertEqual(result, "MEET-123")
    
    @patch('production_meeting_system.smtplib.SMTP')
    async def test_email_integration(self, mock_smtp):
        """Test Email integration"""
        # Mock SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        integration = EmailIntegration("smtp.test.com", 587, "user@test.com", "password")
        
        # Test sending email
        result = await integration.send_email(
            ["recipient@test.com"],
            "Test Subject",
            "Test Body"
        )
        self.assertTrue(result)
        
        # Test meeting reminder
        result = await integration.send_meeting_reminder(self.sample_meeting, {})
        self.assertTrue(result)
    
    def test_meeting_integration_configuration(self):
        """Test integration configuration"""
        # Test Google Calendar configuration
        google_creds = APICredentials(platform=PlatformType.GOOGLE_CALENDAR)
        self.system.configure_google_calendar(google_creds)
        self.assertIsNotNone(self.system.google_calendar)
        
        # Test Slack configuration
        slack_creds = APICredentials(platform=PlatformType.SLACK)
        self.system.configure_slack(slack_creds)
        self.assertIsNotNone(self.system.slack)
        
        # Test JIRA configuration
        jira_creds = APICredentials(platform=PlatformType.JIRA)
        self.system.configure_jira(jira_creds, "https://test.atlassian.net")
        self.assertIsNotNone(self.system.jira)
        
        # Test Email configuration
        self.system.configure_email("smtp.test.com", 587, "user@test.com", "password")
        self.assertIsNotNone(self.system.email)
    
    async def test_meeting_creation(self):
        """Test meeting creation workflow"""
        # This would normally call external APIs, but we'll test the logic
        meeting_stored = self.system.db.store_meeting_event(self.sample_meeting)
        self.assertGreater(meeting_stored, 0)
    
    async def test_transcript_processing(self):
        """Test meeting transcript processing"""
        sample_transcript = """
        Alice: Good morning team. Let's review our progress.
        Bob: I completed the authentication module. We need to test it by Friday.
        Charlie: I can handle the testing. Also, we should update the documentation.
        Alice: Great. Charlie, please create test cases as high priority.
        Bob: I'll prepare the demo environment by Wednesday.
        Charlie: We have a critical issue with the payment system that needs immediate attention.
        """
        
        minutes = await self.system.process_meeting_transcript(
            self.sample_meeting.event_id,
            sample_transcript
        )
        
        self.assertIsInstance(minutes, MeetingMinutes)
        self.assertEqual(minutes.meeting_id, self.sample_meeting.event_id)
        self.assertIsNotNone(minutes.summary)
        self.assertGreater(len(minutes.action_items), 0)
        self.assertIsInstance(minutes.key_points, list)
    
    def test_analytics(self):
        """Test system analytics"""
        # Add some test data
        self.system.db.store_meeting_event(self.sample_meeting)
        
        action_items = [
            ActionItem(
                item_id="analytics_001",
                description="Test analytics",
                assignee="alice@test.com",
                due_date=None,
                priority=TaskPriority.HIGH,
                status="open"
            ),
            ActionItem(
                item_id="analytics_002",
                description="Test completed",
                assignee="bob@test.com",
                due_date=None,
                priority=TaskPriority.MEDIUM,
                status="completed"
            )
        ]
        
        self.system.db.store_action_items(action_items)
        
        # Get analytics
        analytics = self.system.get_meeting_analytics()
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('total_meetings', analytics)
        self.assertIn('open_action_items', analytics)
        self.assertIn('completed_action_items', analytics)
        self.assertIn('completion_rate', analytics)
        
        self.assertGreater(analytics['total_meetings'], 0)
    
    def test_pending_action_items_retrieval(self):
        """Test pending action items retrieval"""
        # Add test action items
        action_items = [
            ActionItem(
                item_id="pending_001",
                description="Pending task 1",
                assignee="alice@test.com",
                due_date=datetime.now() + timedelta(days=1),
                priority=TaskPriority.HIGH,
                status="open"
            ),
            ActionItem(
                item_id="pending_002",
                description="Pending task 2",
                assignee="bob@test.com",
                due_date=datetime.now() + timedelta(days=3),
                priority=TaskPriority.MEDIUM,
                status="open"
            )
        ]
        
        self.system.db.store_action_items(action_items)
        
        # Test getting all pending items
        all_pending = self.system.db.get_pending_action_items()
        self.assertGreaterEqual(len(all_pending), 2)
        
        # Test getting items for specific assignee
        alice_items = self.system.db.get_pending_action_items("alice@test.com")
        self.assertGreaterEqual(len(alice_items), 1)
        self.assertTrue(all(item.assignee == "alice@test.com" for item in alice_items))
    
    def test_meeting_minutes_generation(self):
        """Test meeting minutes generation"""
        action_items = [
            ActionItem(
                item_id="minutes_001",
                description="Review code",
                assignee="alice@test.com",
                due_date=None,
                priority=TaskPriority.HIGH
            )
        ]
        
        minutes = MeetingMinutes(
            meeting_id="test_meeting",
            summary="Test meeting summary",
            key_points=["Point 1", "Point 2"],
            decisions=["Decision 1"],
            action_items=action_items,
            participants_summary={"alice@test.com": "Presented updates"},
            next_steps=["Follow up on action items"]
        )
        
        self.assertEqual(minutes.meeting_id, "test_meeting")
        self.assertIsNotNone(minutes.generated_at)
        self.assertEqual(len(minutes.action_items), 1)
        self.assertEqual(len(minutes.key_points), 2)
    
    def test_configuration_defaults(self):
        """Test system configuration defaults"""
        config = self.system.config
        
        self.assertIn('default_meeting_duration', config)
        self.assertIn('reminder_advance_time', config)
        self.assertIn('auto_create_tasks', config)
        self.assertIn('default_jira_project', config)
        
        self.assertEqual(config['default_meeting_duration'], 60)
        self.assertEqual(config['reminder_advance_time'], 24)
        self.assertTrue(config['auto_create_tasks'])


class TestIntegrationArchitecture(unittest.TestCase):
    """Test integration architecture and error handling"""
    
    def test_credentials_expiry(self):
        """Test credential expiry checking"""
        # Test non-expired credentials
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        creds = APICredentials(
            platform=PlatformType.GOOGLE_CALENDAR,
            expires_at=future_time
        )
        self.assertFalse(creds.is_expired())
        
        # Test expired credentials
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        creds_expired = APICredentials(
            platform=PlatformType.GOOGLE_CALENDAR,
            expires_at=past_time
        )
        self.assertTrue(creds_expired.is_expired())
        
        # Test credentials without expiry
        creds_no_expiry = APICredentials(
            platform=PlatformType.SLACK,
            expires_at=None
        )
        self.assertFalse(creds_no_expiry.is_expired())
    
    def test_platform_enum(self):
        """Test platform type enumeration"""
        platforms = [
            PlatformType.GOOGLE_CALENDAR,
            PlatformType.SLACK,
            PlatformType.JIRA,
            PlatformType.EMAIL_SMTP
        ]
        
        for platform in platforms:
            self.assertIsInstance(platform.value, str)
    
    def test_priority_enum(self):
        """Test task priority enumeration"""
        priorities = [
            TaskPriority.LOW,
            TaskPriority.MEDIUM,
            TaskPriority.HIGH,
            TaskPriority.URGENT,
            TaskPriority.CRITICAL
        ]
        
        for priority in priorities:
            self.assertIsInstance(priority.value, str)


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Meeting System Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionMeetingSystem))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestIntegrationArchitecture))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)