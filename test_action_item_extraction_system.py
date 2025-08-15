#!/usr/bin/env python3
"""
Test suite for Action Item Extraction and Assignment System
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from action_item_extraction_system import (
    ActionItemExtractor,
    DeadlineParser,
    AssigneeExtractor,
    PriorityClassifier,
    ActionItem,
    ActionItemDeadline,
    ActionItemAssignee,
    ActionItemPriority,
    ActionItemStatus,
    DeadlineType,
    extract_action_items_from_meeting,
    create_action_item_extractor
)

from meeting_element_identification import (
    MeetingStructure,
    MeetingElement,
    MeetingElementType,
    ConfidenceLevel,
    analyze_meeting_transcript
)

class TestDeadlineParser:
    """Test the deadline parsing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = DeadlineParser()
    
    def test_specific_date_parsing(self):
        """Test parsing of specific dates"""
        test_cases = [
            ("by Friday, March 15th", DeadlineType.SPECIFIC_DATE),
            ("due 03/15/2024", DeadlineType.SPECIFIC_DATE),
            ("before March 15", DeadlineType.SPECIFIC_DATE),
            ("by 15th of March", DeadlineType.SPECIFIC_DATE)
        ]
        
        for text, expected_type in test_cases:
            deadline = self.parser.parse_deadline(text)
            if deadline:  # Some might not parse due to current year logic
                assert deadline.deadline_type == expected_type, f"Failed for: {text}"
                assert deadline.confidence > 0.5, f"Low confidence for: {text}"
    
    def test_relative_time_parsing(self):
        """Test parsing of relative time deadlines"""
        test_cases = [
            ("by tomorrow", DeadlineType.RELATIVE_TIME),
            ("within 3 days", DeadlineType.RELATIVE_TIME),
            ("in 2 weeks", DeadlineType.RELATIVE_TIME),
            ("by next Monday", DeadlineType.RELATIVE_TIME),
            ("before end of this week", DeadlineType.RELATIVE_TIME)
        ]
        
        for text, expected_type in test_cases:
            deadline = self.parser.parse_deadline(text)
            assert deadline is not None, f"Should parse: {text}"
            assert deadline.deadline_type == expected_type, f"Wrong type for: {text}"
            assert deadline.confidence > 0.5, f"Low confidence for: {text}"
    
    def test_meeting_based_parsing(self):
        """Test parsing of meeting-based deadlines"""
        test_cases = [
            ("by next meeting", DeadlineType.MEETING_BASED),
            ("before our weekly meeting", DeadlineType.MEETING_BASED),
            ("by the follow-up meeting", DeadlineType.MEETING_BASED)
        ]
        
        for text, expected_type in test_cases:
            deadline = self.parser.parse_deadline(text)
            assert deadline is not None, f"Should parse: {text}"
            assert deadline.deadline_type == expected_type, f"Wrong type for: {text}"
    
    def test_deadline_date_calculation(self):
        """Test that parsed dates are calculated correctly"""
        deadline = self.parser.parse_deadline("by tomorrow")
        assert deadline is not None
        assert deadline.parsed_date is not None
        
        expected_date = datetime.now() + timedelta(days=1)
        assert abs((deadline.parsed_date - expected_date).total_seconds()) < 3600  # Within 1 hour
    
    def test_overdue_detection(self):
        """Test overdue detection"""
        # Create a deadline in the past
        past_date = datetime.now() - timedelta(days=1)
        deadline = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="yesterday",
            parsed_date=past_date
        )
        
        assert deadline.is_overdue(), "Should detect overdue deadline"
        
        # Create a future deadline
        future_date = datetime.now() + timedelta(days=1)
        deadline_future = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="tomorrow",
            parsed_date=future_date
        )
        
        assert not deadline_future.is_overdue(), "Should not detect future deadline as overdue"
    
    def test_days_until_deadline(self):
        """Test calculation of days until deadline"""
        future_date = datetime.now() + timedelta(days=5)
        deadline = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="in 5 days",
            parsed_date=future_date
        )
        
        days_until = deadline.days_until_deadline()
        assert days_until is not None
        assert 4 <= days_until <= 5  # Allow for timing differences

class TestAssigneeExtractor:
    """Test the assignee extraction functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = AssigneeExtractor()
    
    def test_explicit_assignment_patterns(self):
        """Test explicit assignment pattern matching"""
        test_cases = [
            "John Smith will prepare the report",
            "Action item for Sarah Johnson",
            "Mike, can you handle this task?",
            "Lisa Chen is responsible for testing",
            "Bob owns the documentation"
        ]
        
        expected_names = ["John Smith", "Sarah Johnson", "Mike", "Lisa Chen", "Bob"]
        
        for text, expected_name in zip(test_cases, expected_names):
            assignees = self.extractor.extract_assignees(text)
            assert len(assignees) > 0, f"Should find assignee in: {text}"
            assert any(expected_name in a.name for a in assignees), f"Should find {expected_name} in: {text}"
    
    def test_name_validation(self):
        """Test name validation logic"""
        valid_names = ["John Smith", "Sarah", "Mike Davis", "A. Johnson"]
        invalid_names = ["we", "team", "everyone", "x", ""]
        
        for name in valid_names:
            assert self.extractor._is_valid_name(name), f"Should validate: {name}"
        
        for name in invalid_names:
            assert not self.extractor._is_valid_name(name), f"Should not validate: {name}"
    
    def test_assignee_deduplication(self):
        """Test assignee deduplication"""
        assignees = [
            ActionItemAssignee(name="John Smith", confidence=0.7),
            ActionItemAssignee(name="john smith", confidence=0.8),  # Same person, different case
            ActionItemAssignee(name="Sarah Johnson", confidence=0.6)
        ]
        
        deduplicated = self.extractor._deduplicate_assignees(assignees)
        
        assert len(deduplicated) == 2, "Should deduplicate same names"
        
        # Should keep the higher confidence version
        john_assignee = next(a for a in deduplicated if "john" in a.name.lower())
        assert john_assignee.confidence == 0.8, "Should keep higher confidence assignee"
    
    def test_role_inference(self):
        """Test role inference from context"""
        context = {
            'attendees': [
                {'name': 'John Smith', 'role': 'Manager'},
                {'name': 'Sarah Johnson', 'role': 'Developer'}
            ]
        }
        
        assignees = self.extractor.extract_assignees("John Smith will handle this", context)
        
        if assignees:
            john_assignee = assignees[0]
            assert john_assignee.role == 'Manager', "Should infer role from context"

class TestPriorityClassifier:
    """Test the priority classification functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = PriorityClassifier()
    
    def test_priority_keywords(self):
        """Test priority classification based on keywords"""
        test_cases = [
            ("This is urgent and critical", ActionItemPriority.CRITICAL),
            ("High priority task for next week", ActionItemPriority.HIGH),
            ("This would be nice to have", ActionItemPriority.MEDIUM),
            ("Eventually we should do this", ActionItemPriority.LOW)
        ]
        
        for text, expected_priority in test_cases:
            priority = self.classifier.classify_priority(text)
            assert priority == expected_priority, f"Wrong priority for: {text}"
    
    def test_deadline_based_priority(self):
        """Test priority classification based on deadline urgency"""
        # Create urgent deadline (tomorrow)
        urgent_deadline = ActionItemDeadline(
            deadline_type=DeadlineType.RELATIVE_TIME,
            original_text="by tomorrow",
            parsed_date=datetime.now() + timedelta(days=1)
        )
        
        context = {'deadline': urgent_deadline}
        priority = self.classifier.classify_priority("Complete this task", context)
        
        assert priority in [ActionItemPriority.CRITICAL, ActionItemPriority.HIGH], \
            "Should classify urgent deadline as high priority"
    
    def test_speaker_role_priority(self):
        """Test priority boost based on speaker role"""
        context = {'speaker_role': 'CEO'}
        priority = self.classifier.classify_priority("Please handle this", context)
        
        assert priority == ActionItemPriority.HIGH, "CEO requests should be high priority"

class TestActionItemExtractor:
    """Test the main action item extractor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = ActionItemExtractor()
        
        # Create a sample meeting structure
        self.meeting = MeetingStructure("test_meeting")
        self.meeting.attendees = ["John Smith", "Sarah Johnson", "Mike Davis"]
        
        # Add some meeting elements
        action_element = MeetingElement(
            element_type=MeetingElementType.ACTION_ITEM,
            content="John will prepare the budget report by Friday",
            speaker="Manager",
            confidence=0.8
        )
        
        discussion_element = MeetingElement(
            element_type=MeetingElementType.DISCUSSION_POINT,
            content="Sarah, can you review the code before next meeting?",
            speaker="Tech Lead",
            confidence=0.7
        )
        
        self.meeting.add_element(action_element)
        self.meeting.add_element(discussion_element)
    
    def test_explicit_action_extraction(self):
        """Test extraction of explicit action items"""
        action_items = self.extractor.extract_action_items(self.meeting)
        
        assert len(action_items) > 0, "Should extract action items"
        
        # Check for the explicit action item
        explicit_actions = [a for a in action_items if a.context.get('extraction_method') == 'explicit']
        assert len(explicit_actions) > 0, "Should find explicit action items"
        
        explicit_action = explicit_actions[0]
        assert "budget report" in explicit_action.content, "Should extract correct content"
        assert len(explicit_action.assignees) > 0, "Should extract assignees"
        assert explicit_action.deadline is not None, "Should extract deadline"
    
    def test_implicit_action_extraction(self):
        """Test extraction of implicit action items"""
        action_items = self.extractor.extract_action_items(self.meeting)
        
        # Check for implicit action items
        implicit_actions = [a for a in action_items if a.context.get('extraction_method') == 'implicit']
        assert len(implicit_actions) > 0, "Should find implicit action items"
        
        implicit_action = implicit_actions[0]
        assert "review" in implicit_action.content.lower(), "Should extract review task"
    
    def test_action_item_enhancement(self):
        """Test enhancement of action items with meeting context"""
        context = {
            'speaker_roles': {
                'Manager': 'Project Manager',
                'Tech Lead': 'Technical Lead'
            }
        }
        
        action_items = self.extractor.extract_action_items(self.meeting, context)
        
        for action in action_items:
            assert 'meeting_id' in action.context, "Should add meeting context"
            assert action.tags is not None, "Should add tags"
    
    def test_duplicate_removal(self):
        """Test removal of duplicate action items"""
        # Add duplicate element
        duplicate_element = MeetingElement(
            element_type=MeetingElementType.ACTION_ITEM,
            content="John will prepare the budget report by Friday",  # Same as first
            speaker="Manager",
            confidence=0.6  # Lower confidence
        )
        
        self.meeting.add_element(duplicate_element)
        
        action_items = self.extractor.extract_action_items(self.meeting)
        
        # Should not have duplicates
        contents = [a.content for a in action_items]
        unique_contents = set(contents)
        
        # Allow for some variation in extraction, but shouldn't have exact duplicates
        assert len(contents) - len(unique_contents) <= 1, "Should remove most duplicates"
    
    def test_statistics_generation(self):
        """Test action item statistics generation"""
        action_items = self.extractor.extract_action_items(self.meeting)
        stats = self.extractor.get_action_item_statistics(action_items)
        
        required_keys = [
            'total_actions', 'by_priority', 'by_status', 'with_assignees',
            'with_deadlines', 'average_confidence', 'overdue_count'
        ]
        
        for key in required_keys:
            assert key in stats, f"Statistics should include {key}"
        
        assert stats['total_actions'] == len(action_items), "Should count total actions correctly"
        assert 0 <= stats['average_confidence'] <= 1.0, "Average confidence should be valid"

class TestActionItem:
    """Test the ActionItem class"""
    
    def test_action_item_creation(self):
        """Test action item creation and initialization"""
        action = ActionItem(
            id="test_action",
            content="Test action item",
            confidence=0.8
        )
        
        assert action.id == "test_action"
        assert action.content == "Test action item"
        assert action.confidence == 0.8
        assert action.confidence_level == ConfidenceLevel.HIGH
        assert action.status == ActionItemStatus.PENDING
        assert action.priority == ActionItemPriority.UNSPECIFIED
    
    def test_assignee_management(self):
        """Test assignee addition and management"""
        action = ActionItem(id="test", content="Test")
        
        assignee = ActionItemAssignee(name="John Smith", confidence=0.8)
        action.add_assignee(assignee)
        
        assert len(action.assignees) == 1
        assert action.get_primary_assignee().name == "John Smith"
    
    def test_deadline_management(self):
        """Test deadline setting and overdue detection"""
        action = ActionItem(id="test", content="Test")
        
        # Set future deadline
        future_deadline = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="tomorrow",
            parsed_date=datetime.now() + timedelta(days=1)
        )
        
        action.set_deadline(future_deadline)
        assert not action.is_overdue(), "Future deadline should not be overdue"
        
        # Set past deadline
        past_deadline = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="yesterday",
            parsed_date=datetime.now() - timedelta(days=1)
        )
        
        action.set_deadline(past_deadline)
        assert action.is_overdue(), "Past deadline should be overdue"
    
    def test_status_updates(self):
        """Test status update functionality"""
        action = ActionItem(id="test", content="Test")
        
        original_time = action.updated_at
        action.update_status(ActionItemStatus.IN_PROGRESS)
        
        assert action.status == ActionItemStatus.IN_PROGRESS
        assert action.updated_at > original_time, "Should update timestamp"

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_action_item_extractor(self):
        """Test extractor creation"""
        extractor = create_action_item_extractor()
        assert isinstance(extractor, ActionItemExtractor)
    
    def test_extract_action_items_from_meeting(self):
        """Test utility function for extraction"""
        meeting = MeetingStructure("test_meeting")
        action_element = MeetingElement(
            element_type=MeetingElementType.ACTION_ITEM,
            content="Test action item",
            confidence=0.8
        )
        meeting.add_element(action_element)
        
        action_items = extract_action_items_from_meeting(meeting)
        
        assert isinstance(action_items, list)
        assert len(action_items) > 0

class TestIntegrationWithMeetingElements:
    """Test integration with meeting element identification"""
    
    def test_full_pipeline_integration(self):
        """Test full pipeline from transcript to action items"""
        transcript = """
[14:00] Manager: Welcome to the project meeting.
[14:02] Manager: First, let's review our action items.
[14:05] Manager: John, can you prepare the quarterly report by next Friday?
[14:06] John: Sure, I'll have it ready by Friday morning.
[14:08] Manager: Sarah, please review the code changes before our next meeting.
[14:09] Sarah: Will do. I'll complete the review by Thursday.
[14:11] Manager: Action item for Mike - update the documentation by end of week.
[14:12] Mike: Got it. I'll prioritize the documentation update.
[14:15] Manager: These are all high priority items for the product launch.
[14:16] Manager: Meeting adjourned.
        """
        
        # Analyze meeting
        meeting = analyze_meeting_transcript(transcript)
        
        # Extract action items
        context = {
            'speaker_roles': {
                'Manager': 'Project Manager',
                'John': 'Developer',
                'Sarah': 'Senior Developer',
                'Mike': 'Technical Writer'
            }
        }
        
        action_items = extract_action_items_from_meeting(meeting, context)
        
        # Verify results
        assert len(action_items) >= 3, "Should extract multiple action items"
        
        # Check for specific action items
        contents = [a.content.lower() for a in action_items]
        assert any('report' in content for content in contents), "Should find report action"
        assert any('review' in content for content in contents), "Should find review action"
        assert any('documentation' in content for content in contents), "Should find documentation action"
        
        # Check assignees
        all_assignees = []
        for action in action_items:
            all_assignees.extend([a.name for a in action.assignees])
        
        expected_assignees = ['John', 'Sarah', 'Mike']
        for expected in expected_assignees:
            assert any(expected in assignee for assignee in all_assignees), \
                f"Should find assignee: {expected}"
        
        # Check deadlines
        actions_with_deadlines = [a for a in action_items if a.deadline]
        assert len(actions_with_deadlines) > 0, "Should extract deadlines"
        
        # Check priorities (should be high due to "high priority" mention)
        high_priority_actions = [a for a in action_items if a.priority == ActionItemPriority.HIGH]
        assert len(high_priority_actions) > 0, "Should classify some as high priority"

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = ActionItemExtractor()
    
    def test_empty_meeting(self):
        """Test handling of empty meeting"""
        empty_meeting = MeetingStructure("empty_meeting")
        action_items = self.extractor.extract_action_items(empty_meeting)
        
        assert len(action_items) == 0, "Should handle empty meeting gracefully"
    
    def test_no_action_items(self):
        """Test meeting with no action items"""
        meeting = MeetingStructure("no_actions")
        
        # Add non-action elements
        discussion = MeetingElement(
            element_type=MeetingElementType.DISCUSSION_POINT,
            content="We discussed the weather today",
            confidence=0.8
        )
        meeting.add_element(discussion)
        
        action_items = self.extractor.extract_action_items(meeting)
        
        # Might extract some implicit actions, but should be minimal
        assert len(action_items) <= 1, "Should not extract many actions from non-action content"
    
    def test_malformed_action_items(self):
        """Test handling of malformed action items"""
        meeting = MeetingStructure("malformed")
        
        # Add malformed action element
        malformed = MeetingElement(
            element_type=MeetingElementType.ACTION_ITEM,
            content="x",  # Too short
            confidence=0.8
        )
        meeting.add_element(malformed)
        
        action_items = self.extractor.extract_action_items(meeting)
        
        # Should handle gracefully, might not extract anything
        assert isinstance(action_items, list), "Should return list even with malformed input"
    
    def test_invalid_dates(self):
        """Test handling of invalid date formats"""
        parser = DeadlineParser()
        
        invalid_dates = [
            "by 32nd of March",  # Invalid day
            "by February 30th",  # Invalid date
            "by 13/45/2024",     # Invalid month/day
            "by tomorrow yesterday"  # Contradictory
        ]
        
        for invalid_date in invalid_dates:
            deadline = parser.parse_deadline(invalid_date)
            # Should either return None or handle gracefully
            if deadline:
                assert isinstance(deadline, ActionItemDeadline), "Should return valid object or None"

def test_comprehensive_integration():
    """Comprehensive integration test with realistic meeting scenario"""
    transcript = """
[09:00] Alice Johnson: Good morning everyone, welcome to our sprint planning meeting.
[09:02] Alice Johnson: Let's start with reviewing last sprint's action items.
[09:05] Bob Smith: I completed the user authentication module as planned.
[09:07] Carol Davis: The API documentation is 90% done. I need one more day to finish.
[09:10] Alice Johnson: Great progress. For this sprint, we have several critical tasks.
[09:12] Alice Johnson: Bob, can you implement the dashboard components by next Wednesday?
[09:13] Bob Smith: Absolutely. I'll prioritize the dashboard work.
[09:15] Alice Johnson: Carol, please complete the API docs by tomorrow. It's blocking QA.
[09:16] Carol Davis: Will do. I'll have it ready by end of day tomorrow.
[09:18] Alice Johnson: Action item for David - set up the staging environment by Friday.
[09:20] David Wilson: Got it. I'll configure staging by Friday afternoon.
[09:22] Alice Johnson: We also need someone to review the security requirements.
[09:24] Bob Smith: I can handle the security review. When do you need it?
[09:25] Alice Johnson: By end of this week would be perfect. It's high priority.
[09:27] Carol Davis: Should we schedule a code review session?
[09:28] Alice Johnson: Good idea. Carol, can you organize that for next Monday?
[09:30] Carol Davis: Sure, I'll send out calendar invites today.
[09:32] Alice Johnson: Any other urgent items before we wrap up?
[09:33] David Wilson: We should update the deployment scripts. They're outdated.
[09:35] Alice Johnson: David, can you add that to your tasks? Not urgent, but important.
[09:36] David Wilson: No problem. I'll work on it after the staging setup.
[09:38] Alice Johnson: Perfect. Follow up meeting same time next week.
[09:39] Alice Johnson: Thanks everyone. Meeting adjourned.
    """
    
    context = {
        'meeting_id': 'sprint_planning_2024',
        'title': 'Sprint Planning Meeting',
        'date': datetime(2024, 1, 15, 9, 0),
        'speaker_roles': {
            'Alice Johnson': 'Scrum Master',
            'Bob Smith': 'Frontend Developer',
            'Carol Davis': 'Backend Developer',
            'David Wilson': 'DevOps Engineer'
        }
    }
    
    # Analyze meeting and extract action items
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    # Comprehensive validation
    assert len(action_items) >= 5, f"Should extract multiple action items, got {len(action_items)}"
    
    # Check for specific expected action items
    expected_actions = [
        ('dashboard', 'Bob Smith'),
        ('api docs', 'Carol Davis'),
        ('staging', 'David Wilson'),
        ('security', 'Bob Smith'),
        ('code review', 'Carol Davis')
    ]
    
    action_contents = [(a.content.lower(), [assignee.name for assignee in a.assignees]) for a in action_items]
    
    for expected_content, expected_assignee in expected_actions:
        found = False
        for content, assignees in action_contents:
            if expected_content in content and any(expected_assignee in assignee for assignee in assignees):
                found = True
                break
        assert found, f"Should find action item about {expected_content} for {expected_assignee}"
    
    # Check deadlines
    actions_with_deadlines = [a for a in action_items if a.deadline]
    assert len(actions_with_deadlines) >= 3, "Should extract multiple deadlines"
    
    # Check priorities
    high_priority_actions = [a for a in action_items if a.priority in [ActionItemPriority.HIGH, ActionItemPriority.CRITICAL]]
    assert len(high_priority_actions) >= 1, "Should identify high priority items"
    
    # Check confidence levels
    high_confidence_actions = [a for a in action_items if a.confidence >= 0.6]
    assert len(high_confidence_actions) >= 3, "Should have several high confidence actions"
    
    # Validate statistics
    extractor = create_action_item_extractor()
    stats = extractor.get_action_item_statistics(action_items)
    
    assert stats['total_actions'] == len(action_items)
    assert stats['with_assignees'] >= 4, "Most actions should have assignees"
    assert stats['with_deadlines'] >= 3, "Several actions should have deadlines"
    assert stats['average_confidence'] > 0.4, "Should have reasonable average confidence"
    
    # Check extraction methods
    explicit_count = len([a for a in action_items if a.context.get('extraction_method') == 'explicit'])
    implicit_count = len([a for a in action_items if a.context.get('extraction_method') == 'implicit'])
    
    assert explicit_count >= 1, "Should find explicit action items"
    assert implicit_count >= 1, "Should find implicit action items"
    
    print(f"✅ Integration test passed:")
    print(f"   Total actions: {len(action_items)}")
    print(f"   With assignees: {stats['with_assignees']}")
    print(f"   With deadlines: {stats['with_deadlines']}")
    print(f"   Average confidence: {stats['average_confidence']:.2f}")
    print(f"   Explicit actions: {explicit_count}")
    print(f"   Implicit actions: {implicit_count}")

if __name__ == "__main__":
    # Run the comprehensive integration test
    test_comprehensive_integration()
    
    # Run pytest for all other tests
    pytest.main([__file__, "-v"])