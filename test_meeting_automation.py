#!/usr/bin/env python3
"""
Test suite for Meeting Automation System (Task 64)
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os

from meeting_automation_system import (
    MeetingAutomationSystem, MeetingAnalyzer, EmailIntegration,
    CalendarIntegration, ProjectManagementIntegration, CollaborationIntegration,
    MeetingMinutes, MeetingType, TaskPriority, ActionItem, Attendee, Decision
)


class TestMeetingAnalyzer(unittest.TestCase):
    """Test the MeetingAnalyzer class"""
    
    def setUp(self):
        self.analyzer = MeetingAnalyzer()
        self.sample_transcript = {
            'segments': [
                {'text': "Let's start our sprint planning meeting.", 'speaker': 'John', 'start': 0, 'end': 3},
                {'text': "Today we'll discuss the upcoming features.", 'speaker': 'John', 'start': 3, 'end': 7},
                {'text': "I think we should prioritize the API redesign.", 'speaker': 'Sarah', 'start': 7, 'end': 11},
                {'text': "Agreed. I'll take that task.", 'speaker': 'Mike', 'start': 11, 'end': 14},
                {'text': "We've decided to use GraphQL for the new API.", 'speaker': 'John', 'start': 14, 'end': 18},
                {'text': "I'll create the Jira tickets by tomorrow.", 'speaker': 'Mike', 'start': 18, 'end': 22},
                {'text': "Next meeting is scheduled for Monday at 10 AM.", 'speaker': 'John', 'start': 22, 'end': 26}
            ],
            'speakers': {
                'John': 'John Smith',
                'Sarah': 'Sarah Johnson',
                'Mike': 'Mike Wilson'
            }
        }
    
    def test_analyze_meeting(self):
        """Test basic meeting analysis"""
        minutes = self.analyzer.analyze_meeting(self.sample_transcript)
        
        self.assertIsInstance(minutes, MeetingMinutes)
        self.assertEqual(minutes.meeting_type, MeetingType.PLANNING)
        self.assertEqual(len(minutes.attendees), 3)
        self.assertGreater(len(minutes.action_items), 0)
        self.assertGreater(len(minutes.decisions), 0)
    
    def test_detect_meeting_type(self):
        """Test meeting type detection"""
        # Test standup
        standup_text = "Let's do our daily standup. What did you work on yesterday?"
        self.assertEqual(
            self.analyzer._detect_meeting_type(standup_text),
            MeetingType.STANDUP
        )
        
        # Test retrospective
        retro_text = "Time for our sprint retrospective. What went well?"
        self.assertEqual(
            self.analyzer._detect_meeting_type(retro_text),
            MeetingType.RETROSPECTIVE
        )
        
        # Test client meeting
        client_text = "Welcome to our client review meeting."
        self.assertEqual(
            self.analyzer._detect_meeting_type(client_text),
            MeetingType.CLIENT_MEETING
        )
    
    def test_extract_attendees(self):
        """Test attendee extraction"""
        attendees = self.analyzer._extract_attendees(
            self.sample_transcript['segments'],
            self.sample_transcript['speakers']
        )
        
        self.assertEqual(len(attendees), 3)
        
        # Check attendee names
        attendee_names = [a.name for a in attendees]
        self.assertIn('John Smith', attendee_names)
        self.assertIn('Sarah Johnson', attendee_names)
        self.assertIn('Mike Wilson', attendee_names)
        
        # Check speaking time is calculated
        for attendee in attendees:
            self.assertGreater(attendee.speaking_time, 0)
    
    def test_extract_action_items(self):
        """Test action item extraction"""
        attendees = self.analyzer._extract_attendees(
            self.sample_transcript['segments'],
            self.sample_transcript['speakers']
        )
        
        action_items = self.analyzer._extract_action_items(
            self.sample_transcript['segments'],
            attendees
        )
        
        self.assertGreater(len(action_items), 0)
        
        # Check for specific action items
        action_texts = [item.description for item in action_items]
        self.assertTrue(any('take that task' in text for text in action_texts))
        self.assertTrue(any('create the Jira tickets' in text for text in action_texts))
    
    def test_extract_decisions(self):
        """Test decision extraction"""
        attendees = self.analyzer._extract_attendees(
            self.sample_transcript['segments'],
            self.sample_transcript['speakers']
        )
        
        decisions = self.analyzer._extract_decisions(
            self.sample_transcript['segments'],
            attendees
        )
        
        self.assertGreater(len(decisions), 0)
        
        # Check for GraphQL decision
        decision_texts = [d.description for d in decisions]
        self.assertTrue(any('GraphQL' in text for text in decision_texts))
    
    def test_extract_priority(self):
        """Test priority extraction from text"""
        # Test urgent
        self.assertEqual(
            self.analyzer._extract_priority("This is urgent and needs immediate attention"),
            TaskPriority.URGENT
        )
        
        # Test high
        self.assertEqual(
            self.analyzer._extract_priority("This is a high priority task"),
            TaskPriority.HIGH
        )
        
        # Test low
        self.assertEqual(
            self.analyzer._extract_priority("This is low priority, do it when possible"),
            TaskPriority.LOW
        )
        
        # Test default (medium)
        self.assertEqual(
            self.analyzer._extract_priority("Regular task to be done"),
            TaskPriority.MEDIUM
        )
    
    def test_extract_due_date(self):
        """Test due date extraction"""
        # Test tomorrow
        due_date = self.analyzer._extract_due_date("Complete this by tomorrow")
        self.assertIsNotNone(due_date)
        self.assertEqual(
            due_date.date(),
            (datetime.now() + timedelta(days=1)).date()
        )
        
        # Test week
        due_date = self.analyzer._extract_due_date("Due by end of week")
        self.assertIsNotNone(due_date)
        self.assertEqual(
            due_date.date(),
            (datetime.now() + timedelta(weeks=1)).date()
        )
    
    def test_empty_transcript(self):
        """Test handling of empty transcript"""
        empty_transcript = {'segments': []}
        minutes = self.analyzer.analyze_meeting(empty_transcript)
        
        self.assertIsInstance(minutes, MeetingMinutes)
        self.assertEqual(len(minutes.attendees), 0)
        self.assertEqual(len(minutes.action_items), 0)
        self.assertEqual(minutes.duration, 0)


class TestEmailIntegration(unittest.TestCase):
    """Test the EmailIntegration class"""
    
    def setUp(self):
        self.email_integration = EmailIntegration({
            'host': 'smtp.example.com',
            'port': 587,
            'username': 'test@example.com',
            'password': 'testpass',
            'use_tls': True
        })
        
        self.sample_minutes = MeetingMinutes(
            meeting_id='MTG-123',
            title='Test Meeting',
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.PLANNING,
            attendees=[
                Attendee(name='John Smith', email='john@example.com'),
                Attendee(name='Jane Doe', email='jane@example.com')
            ],
            agenda=['Item 1', 'Item 2'],
            discussion_points=[],
            decisions=[
                Decision(
                    description='Use new framework',
                    rationale='Better performance',
                    made_by='John Smith',
                    timestamp=datetime.now()
                )
            ],
            action_items=[
                ActionItem(
                    description='Implement feature X',
                    assignee='Jane Doe',
                    priority=TaskPriority.HIGH
                )
            ],
            key_insights=['Important insight 1']
        )
    
    @patch('smtplib.SMTP')
    def test_send_meeting_summary_success(self, mock_smtp):
        """Test successful email sending"""
        # Configure mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Send email
        result = self.email_integration.send_meeting_summary(
            self.sample_minutes,
            ['recipient@example.com']
        )
        
        self.assertTrue(result)
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_meeting_summary_failure(self, mock_smtp):
        """Test email sending failure"""
        # Configure mock to raise exception
        mock_smtp.side_effect = Exception("SMTP error")
        
        # Send email
        result = self.email_integration.send_meeting_summary(
            self.sample_minutes,
            ['recipient@example.com']
        )
        
        self.assertFalse(result)
    
    def test_generate_html_email(self):
        """Test HTML email generation"""
        html = self.email_integration._generate_html_email(self.sample_minutes)
        
        self.assertIn('Test Meeting', html)
        self.assertIn('John Smith', html)
        self.assertIn('Use new framework', html)
        self.assertIn('Implement feature X', html)
    
    def test_generate_text_email(self):
        """Test plain text email generation"""
        text = self.email_integration._generate_text_email(self.sample_minutes)
        
        self.assertIn('MEETING MINUTES: Test Meeting', text)
        self.assertIn('ATTENDEES:', text)
        self.assertIn('KEY DECISIONS:', text)
        self.assertIn('ACTION ITEMS:', text)


class TestCalendarIntegration(unittest.TestCase):
    """Test the CalendarIntegration class"""
    
    def setUp(self):
        self.calendar_integration = CalendarIntegration()
        self.sample_minutes = MeetingMinutes(
            meeting_id='MTG-123',
            title='Test Meeting',
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.PLANNING,
            attendees=[
                Attendee(name='John Smith', email='john@example.com')
            ],
            agenda=[],
            discussion_points=[],
            decisions=[],
            action_items=[],
            key_insights=[],
            next_meeting=datetime.now() + timedelta(days=7)
        )
    
    @patch('googleapiclient.discovery.build')
    def test_create_google_event(self, mock_build):
        """Test Google Calendar event creation"""
        # Configure mock
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.events().insert().execute.return_value = {
            'htmlLink': 'https://calendar.google.com/event/123'
        }
        
        # Set mock credentials
        self.calendar_integration.google_creds = MagicMock()
        
        # Create event
        event_link = self.calendar_integration.create_follow_up_meeting(
            self.sample_minutes,
            'google'
        )
        
        self.assertIsNotNone(event_link)
        mock_service.events().insert.assert_called_once()
    
    def test_generate_event_description(self):
        """Test calendar event description generation"""
        description = self.calendar_integration._generate_event_description(
            self.sample_minutes
        )
        
        self.assertIn('follow-up', description)
        self.assertIn('Previous Meeting Summary', description)
        self.assertIn('Outstanding Action Items', description)


class TestProjectManagementIntegration(unittest.TestCase):
    """Test the ProjectManagementIntegration class"""
    
    def setUp(self):
        self.pm_integration = ProjectManagementIntegration()
        self.sample_action_items = [
            ActionItem(
                description='Implement feature X',
                assignee='John Doe',
                priority=TaskPriority.HIGH,
                due_date=datetime.now() + timedelta(days=7)
            ),
            ActionItem(
                description='Review documentation',
                assignee='Jane Smith',
                priority=TaskPriority.MEDIUM
            )
        ]
    
    @patch('requests.post')
    def test_create_jira_issue(self, mock_post):
        """Test Jira issue creation"""
        # Configure mock
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'key': 'PROJ-123'}
        
        # Set config
        self.pm_integration.jira_config = {
            'url': 'https://example.atlassian.net',
            'username': 'user',
            'api_token': 'token',
            'project_key': 'PROJ'
        }
        
        # Create issue
        issue_id = self.pm_integration._create_jira_issue(
            self.sample_action_items[0]
        )
        
        self.assertEqual(issue_id, 'PROJ-123')
        mock_post.assert_called_once()
        
        # Verify request data
        call_args = mock_post.call_args
        request_data = call_args[1]['json']
        self.assertEqual(request_data['fields']['summary'], 'Implement feature X')
        self.assertEqual(request_data['fields']['priority']['name'], 'High')
    
    @patch('requests.post')
    def test_create_asana_task(self, mock_post):
        """Test Asana task creation"""
        # Configure mock
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            'data': {'gid': '1234567890'}
        }
        
        # Set config
        self.pm_integration.asana_config = {
            'access_token': 'token',
            'workspace_id': 'workspace123'
        }
        
        # Create task
        task_id = self.pm_integration._create_asana_task(
            self.sample_action_items[1]
        )
        
        self.assertEqual(task_id, '1234567890')
        mock_post.assert_called_once()
    
    @patch('requests.get')
    @patch('requests.post')
    def test_create_trello_card(self, mock_post, mock_get):
        """Test Trello card creation"""
        # Configure mocks
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [
            {'id': 'list123', 'name': 'To Do'}
        ]
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'id': 'card123'}
        
        # Set config
        self.pm_integration.trello_config = {
            'api_key': 'key',
            'token': 'token',
            'board_id': 'board123'
        }
        
        # Create card
        card_id = self.pm_integration._create_trello_card(
            self.sample_action_items[0]
        )
        
        self.assertEqual(card_id, 'card123')
        mock_get.assert_called_once()  # Get lists
        mock_post.assert_called_once()  # Create card
    
    def test_create_tasks_from_action_items(self):
        """Test creating tasks from multiple action items"""
        with patch.object(self.pm_integration, '_create_jira_issue', return_value='PROJ-123'):
            self.pm_integration.jira_config = {
                'url': 'https://example.atlassian.net',
                'username': 'user',
                'api_token': 'token',
                'project_key': 'PROJ'
            }
            
            task_ids = self.pm_integration.create_tasks_from_action_items(
                self.sample_action_items,
                'jira'
            )
            
            self.assertEqual(len(task_ids), 2)
            self.assertEqual(task_ids[0], 'PROJ-123')


class TestCollaborationIntegration(unittest.TestCase):
    """Test the CollaborationIntegration class"""
    
    def setUp(self):
        self.collab_integration = CollaborationIntegration()
        self.sample_minutes = MeetingMinutes(
            meeting_id='MTG-123',
            title='Sprint Planning',
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.PLANNING,
            attendees=[
                Attendee(name='John Smith', email='john@example.com')
            ],
            agenda=['Review backlog', 'Plan sprint'],
            discussion_points=[],
            decisions=[
                Decision(
                    description='Prioritize API work',
                    rationale='Customer feedback',
                    made_by='John Smith',
                    timestamp=datetime.now()
                )
            ],
            action_items=[
                ActionItem(
                    description='Design API schema',
                    assignee='John Smith',
                    priority=TaskPriority.HIGH
                )
            ],
            key_insights=['API is critical path']
        )
    
    @patch('requests.post')
    def test_share_to_slack(self, mock_post):
        """Test Slack sharing"""
        # Configure mock
        mock_post.return_value.status_code = 200
        
        # Set config
        self.collab_integration.slack_config = {
            'webhook_url': 'https://hooks.slack.com/services/123',
            'bot_token': 'xoxb-123'
        }
        
        # Share to Slack
        result = self.collab_integration.share_meeting_summary(
            self.sample_minutes,
            'slack',
            '#general'
        )
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify message structure
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertIn('blocks', payload)
        self.assertTrue(any('Sprint Planning' in str(block) for block in payload['blocks']))
    
    @patch('requests.post')
    def test_share_to_teams(self, mock_post):
        """Test Teams sharing"""
        # Configure mock
        mock_post.return_value.status_code = 200
        
        # Set config
        self.collab_integration.teams_config = {
            'webhook_url': 'https://outlook.office.com/webhook/123'
        }
        
        # Share to Teams
        result = self.collab_integration.share_meeting_summary(
            self.sample_minutes,
            'teams'
        )
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify card structure
        call_args = mock_post.call_args
        card = call_args[1]['json']
        self.assertEqual(card['@type'], 'MessageCard')
        self.assertIn('Sprint Planning', card['summary'])


class TestMeetingAutomationSystem(unittest.TestCase):
    """Test the main MeetingAutomationSystem class"""
    
    def setUp(self):
        self.system = MeetingAutomationSystem()
        self.sample_transcript = {
            'segments': [
                {'text': "Let's review our Q2 goals.", 'speaker': 'Manager', 'start': 0, 'end': 3},
                {'text': "Sales target is $1M for this quarter.", 'speaker': 'Manager', 'start': 3, 'end': 7},
                {'text': "I'll update the forecast by Friday.", 'speaker': 'Analyst', 'start': 7, 'end': 11},
                {'text': "We've decided to launch the new product in May.", 'speaker': 'Manager', 'start': 11, 'end': 15}
            ]
        }
    
    def test_process_meeting_basic(self):
        """Test basic meeting processing"""
        results = self.system.process_meeting(self.sample_transcript)
        
        self.assertEqual(results['status'], 'success')
        self.assertIsNotNone(results['meeting_minutes'])
        self.assertIn('meeting_id', results['meeting_minutes'])
        
        # Check meeting content
        minutes = results['meeting_minutes']
        self.assertGreater(len(minutes['attendees']), 0)
        self.assertGreater(len(minutes['action_items']), 0)
        self.assertGreater(len(minutes['decisions']), 0)
    
    @patch.object(EmailIntegration, 'send_meeting_summary')
    def test_process_meeting_with_email(self, mock_send_email):
        """Test meeting processing with email integration"""
        mock_send_email.return_value = True
        
        options = {
            'send_email': True,
            'email_recipients': ['test@example.com']
        }
        
        results = self.system.process_meeting(
            self.sample_transcript,
            options=options
        )
        
        self.assertTrue(results['email_sent'])
        mock_send_email.assert_called_once()
    
    def test_generate_meeting_report_html(self):
        """Test HTML report generation"""
        minutes = MeetingMinutes(
            meeting_id='MTG-123',
            title='Test Meeting',
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.GENERAL,
            attendees=[Attendee(name='Test User', email='test@example.com')],
            agenda=['Test item'],
            discussion_points=[],
            decisions=[],
            action_items=[],
            key_insights=['Test insight']
        )
        
        html_report = self.system.generate_meeting_report(minutes, 'html')
        
        self.assertIn('<html>', html_report)
        self.assertIn('Test Meeting', html_report)
        self.assertIn('Test User', html_report)
        self.assertIn('Test insight', html_report)
    
    def test_generate_meeting_report_markdown(self):
        """Test Markdown report generation"""
        minutes = MeetingMinutes(
            meeting_id='MTG-123',
            title='Test Meeting',
            date=datetime.now(),
            duration=3600,
            meeting_type=MeetingType.GENERAL,
            attendees=[Attendee(name='Test User', email='test@example.com')],
            agenda=['Test item'],
            discussion_points=[],
            decisions=[],
            action_items=[
                ActionItem(
                    description='Test task',
                    assignee='Test User',
                    priority=TaskPriority.HIGH
                )
            ],
            key_insights=[]
        )
        
        md_report = self.system.generate_meeting_report(minutes, 'markdown')
        
        self.assertIn('# Meeting Minutes:', md_report)
        self.assertIn('## Attendees', md_report)
        self.assertIn('## Action Items', md_report)
        self.assertIn('Test task', md_report)
    
    def test_process_meeting_with_all_integrations(self):
        """Test meeting processing with all integrations enabled"""
        with patch.multiple(
            'meeting_automation_system',
            EmailIntegration=MagicMock(),
            CalendarIntegration=MagicMock(),
            ProjectManagementIntegration=MagicMock(),
            CollaborationIntegration=MagicMock()
        ):
            options = {
                'send_email': True,
                'email_recipients': ['test@example.com'],
                'create_calendar_event': True,
                'calendar_type': 'google',
                'create_tasks': True,
                'pm_platform': 'jira',
                'share_to_collaboration': True,
                'collab_platform': 'slack'
            }
            
            results = self.system.process_meeting(
                self.sample_transcript,
                options=options
            )
            
            self.assertEqual(results['status'], 'success')
    
    def test_error_handling(self):
        """Test error handling in meeting processing"""
        # Test with invalid transcript
        invalid_transcript = {'invalid': 'data'}
        
        results = self.system.process_meeting(invalid_transcript)
        
        self.assertEqual(results['status'], 'error')
        self.assertGreater(len(results['errors']), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def test_end_to_end_meeting_processing(self):
        """Test complete meeting processing workflow"""
        # Create sample meeting transcript
        transcript = {
            'segments': [
                {'text': "Welcome to our project kickoff meeting.", 'speaker': 'PM', 'start': 0, 'end': 4},
                {'text': "Let's discuss the project timeline.", 'speaker': 'PM', 'start': 4, 'end': 8},
                {'text': "I think we need 3 months for development.", 'speaker': 'Dev', 'start': 8, 'end': 12},
                {'text': "Agreed. Let's plan for a June release.", 'speaker': 'PM', 'start': 12, 'end': 16},
                {'text': "I'll set up the development environment by next week.", 'speaker': 'Dev', 'start': 16, 'end': 20},
                {'text': "And I'll create the project plan in Jira.", 'speaker': 'PM', 'start': 20, 'end': 24},
                {'text': "We've decided to use agile methodology.", 'speaker': 'PM', 'start': 24, 'end': 28},
                {'text': "Let's have our next sync on Monday.", 'speaker': 'PM', 'start': 28, 'end': 32}
            ],
            'speakers': {
                'PM': 'Project Manager',
                'Dev': 'Lead Developer'
            }
        }
        
        # Process meeting
        system = MeetingAutomationSystem()
        results = system.process_meeting(transcript)
        
        # Verify results
        self.assertEqual(results['status'], 'success')
        
        minutes_data = results['meeting_minutes']
        self.assertIn('project kickoff', minutes_data['title'].lower())
        self.assertEqual(len(minutes_data['attendees']), 2)
        
        # Check action items
        action_items = minutes_data['action_items']
        self.assertGreater(len(action_items), 0)
        
        action_descriptions = [item['description'] for item in action_items]
        self.assertTrue(any('development environment' in desc for desc in action_descriptions))
        self.assertTrue(any('project plan' in desc for desc in action_descriptions))
        
        # Check decisions
        decisions = minutes_data['decisions']
        self.assertGreater(len(decisions), 0)
        
        decision_descriptions = [d['description'] for d in decisions]
        self.assertTrue(any('June release' in desc for desc in decision_descriptions))
        self.assertTrue(any('agile methodology' in desc for desc in decision_descriptions))


def run_all_tests():
    """Run all tests"""
    test_classes = [
        TestMeetingAnalyzer,
        TestEmailIntegration,
        TestCalendarIntegration,
        TestProjectManagementIntegration,
        TestCollaborationIntegration,
        TestMeetingAutomationSystem,
        TestIntegration
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    print("\n" + "="*50)
    print(f"Test suite {'PASSED' if success else 'FAILED'}")
    print("="*50)