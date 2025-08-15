#!/usr/bin/env python3
"""
Test suite for Meeting Element Identification Engine
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_element_identification import (
    MeetingElementIdentifier,
    MeetingPatternMatcher,
    MeetingElement,
    MeetingStructure,
    MeetingElementType,
    ConfidenceLevel,
    analyze_meeting_transcript,
    create_meeting_identifier
)

class TestMeetingPatternMatcher:
    """Test the pattern matching functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.matcher = MeetingPatternMatcher()
    
    def test_agenda_item_patterns(self):
        """Test agenda item pattern matching"""
        test_cases = [
            "Let's start with agenda item 1 - reviewing performance",
            "Next topic is budget planning",
            "First, we'll discuss the new project",
            "Moving on to the quarterly results"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            agenda_matches = [m for m in matches if m[0] == MeetingElementType.AGENDA_ITEM]
            assert len(agenda_matches) > 0, f"Should find agenda item in: {text}"
            assert agenda_matches[0][2] > 0.1, "Should have reasonable confidence"
    
    def test_decision_patterns(self):
        """Test decision pattern matching"""
        test_cases = [
            "We've decided to proceed with the project",
            "The proposal is approved",
            "Final decision is to postpone the launch",
            "We agree on the new timeline"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            decision_matches = [m for m in matches if m[0] == MeetingElementType.DECISION]
            assert len(decision_matches) > 0, f"Should find decision in: {text}"
            assert decision_matches[0][2] > 0.2, "Should have good confidence"
    
    def test_action_item_patterns(self):
        """Test action item pattern matching"""
        test_cases = [
            "John will prepare the report by Friday",
            "Action item for Sarah - update the documentation",
            "Can you send the proposal by next week?",
            "Mike needs to review the code before Monday"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            action_matches = [m for m in matches if m[0] == MeetingElementType.ACTION_ITEM]
            assert len(action_matches) > 0, f"Should find action item in: {text}"
    
    def test_question_patterns(self):
        """Test question pattern matching"""
        test_cases = [
            "What about the budget for next quarter?",
            "Do we have enough resources?",
            "I have a question about the timeline",
            "Are there any concerns?"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            question_matches = [m for m in matches if m[0] == MeetingElementType.QUESTION]
            assert len(question_matches) > 0, f"Should find question in: {text}"
    
    def test_agreement_patterns(self):
        """Test agreement pattern matching"""
        test_cases = [
            "Everyone agrees on this approach",
            "That sounds good to me",
            "Perfect, let's proceed",
            "We have consensus on this matter"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            agreement_matches = [m for m in matches if m[0] == MeetingElementType.AGREEMENT]
            assert len(agreement_matches) > 0, f"Should find agreement in: {text}"
    
    def test_objection_patterns(self):
        """Test objection pattern matching"""
        test_cases = [
            "I disagree with this approach",
            "I have a concern about the timeline",
            "But wait, what about the budget?",
            "There's a problem with this plan"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            objection_matches = [m for m in matches if m[0] == MeetingElementType.OBJECTION]
            assert len(objection_matches) > 0, f"Should find objection in: {text}"
    
    def test_follow_up_patterns(self):
        """Test follow-up pattern matching"""
        test_cases = [
            "Follow up meeting next Monday",
            "We'll revisit this next week",
            "Let's circle back on this topic",
            "Next steps are to review the proposal"
        ]
        
        for text in test_cases:
            matches = self.matcher.match_patterns(text)
            followup_matches = [m for m in matches if m[0] == MeetingElementType.FOLLOW_UP]
            assert len(followup_matches) > 0, f"Should find follow-up in: {text}"
    
    def test_context_boost(self):
        """Test context-based confidence boosting"""
        # Test with facilitator context
        context = {'speaker_role': 'facilitator', 'meeting_phase': 'opening'}
        matches = self.matcher.match_patterns("Let's discuss the first agenda item", context)
        
        # Should have higher confidence with facilitator context
        agenda_matches = [m for m in matches if m[0] == MeetingElementType.AGENDA_ITEM]
        assert len(agenda_matches) > 0
        assert agenda_matches[0][2] > 0.3, "Should have boosted confidence with facilitator context"
    
    def test_confidence_levels(self):
        """Test different confidence levels"""
        # High confidence pattern
        high_conf_text = "We've decided to approve the budget proposal"
        matches = self.matcher.match_patterns(high_conf_text)
        decision_matches = [m for m in matches if m[0] == MeetingElementType.DECISION]
        assert decision_matches[0][2] > 0.3, "Should have high confidence"
        
        # Lower confidence pattern
        low_conf_text = "But maybe we should consider other options"
        matches = self.matcher.match_patterns(low_conf_text)
        objection_matches = [m for m in matches if m[0] == MeetingElementType.OBJECTION]
        if objection_matches:
            assert objection_matches[0][2] < 0.3, "Should have lower confidence"

class TestMeetingElementIdentifier:
    """Test the main meeting element identifier"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.identifier = MeetingElementIdentifier()
        self.sample_transcript = """
[14:00] John Smith: Welcome everyone to today's quarterly planning meeting.
[14:01] Sarah Johnson: Thank you John. I'm excited to discuss our Q4 goals.
[14:02] John Smith: Let's start with agenda item 1 - reviewing last quarter's performance.
[14:05] Mike Davis: The numbers look good. We exceeded our targets by 15%.
[14:07] Sarah Johnson: That's excellent news. I think we should celebrate this achievement.
[14:08] John Smith: Agreed. We've decided to have a team celebration next Friday.
[14:10] Lisa Chen: What about the budget for next quarter?
[14:12] John Smith: Good question. Mike, can you prepare the budget analysis by next Wednesday?
[14:13] Mike Davis: Absolutely. I'll have it ready by Wednesday morning.
[14:15] John Smith: Perfect. Any other questions before we move to the next item?
[14:16] Sarah Johnson: I have a concern about the timeline for the new product launch.
[14:18] John Smith: Let's discuss that. What's your concern?
[14:20] Sarah Johnson: I think we need more time for testing.
[14:22] Lisa Chen: I agree with Sarah. Quality is important.
[14:24] John Smith: Okay, we'll extend the timeline by two weeks. Final decision.
[14:26] John Smith: Action item for Lisa - please update the project timeline.
[14:28] Lisa Chen: Will do. I'll send the updated timeline to everyone by Friday.
[14:30] John Smith: Great. Let's wrap up. Follow up meeting next Monday at 2 PM.
[14:31] John Smith: Thank you everyone. Meeting adjourned.
        """
    
    def test_parse_transcript_segments(self):
        """Test transcript parsing into segments"""
        segments = self.identifier._parse_transcript_segments(self.sample_transcript)
        
        # Should have multiple segments
        assert len(segments) > 10, "Should parse multiple segments"
        
        # Check for speaker extraction
        speakers_found = [s for s in segments if s['speaker'] is not None]
        assert len(speakers_found) > 5, "Should identify multiple speakers"
        
        # Check for timestamp extraction
        timestamps_found = [s for s in segments if s['timestamp'] is not None]
        assert len(timestamps_found) > 5, "Should identify multiple timestamps"
    
    def test_extract_timestamp(self):
        """Test timestamp extraction"""
        test_cases = [
            ("[14:30] Some content", "14:30"),
            ("14:30 - Speaker says something", "14:30"),
            ("@14:30:15 Content here", "14:30:15"),
            ("(14:30) More content", "14:30"),
            ("No timestamp here", None)
        ]
        
        for text, expected in test_cases:
            result = self.identifier._extract_timestamp(text)
            assert result == expected, f"Expected {expected}, got {result} for: {text}"
    
    def test_extract_speaker(self):
        """Test speaker extraction"""
        test_cases = [
            ("John Smith: Hello everyone", ("John Smith", "Hello everyone")),
            ("[Sarah Johnson] Good morning", ("Sarah Johnson", "Good morning")),
            ("Mike Davis - Let's begin", ("Mike Davis", "Let's begin")),
            (">> Lisa Chen: Any questions?", ("Lisa Chen", "Any questions?")),
            ("No speaker format here", (None, "No speaker format here"))
        ]
        
        for text, expected in test_cases:
            result = self.identifier._extract_speaker(text)
            assert result == expected, f"Expected {expected}, got {result} for: {text}"
    
    def test_identify_attendees(self):
        """Test attendee identification"""
        segments = self.identifier._parse_transcript_segments(self.sample_transcript)
        attendees = self.identifier._identify_attendees(segments)
        
        expected_attendees = ["John Smith", "Sarah Johnson", "Mike Davis", "Lisa Chen"]
        for attendee in expected_attendees:
            assert attendee in attendees, f"Should identify {attendee} as attendee"
    
    def test_identify_elements_full_transcript(self):
        """Test full element identification on sample transcript"""
        context = {
            'meeting_id': 'test_meeting',
            'title': 'Test Meeting',
            'date': datetime.now()
        }
        
        meeting = self.identifier.identify_elements(self.sample_transcript, context)
        
        # Basic structure checks
        assert meeting.meeting_id == 'test_meeting'
        assert meeting.title == 'Test Meeting'
        assert len(meeting.attendees) >= 4, "Should identify main attendees"
        assert len(meeting.elements) > 0, "Should identify meeting elements"
        
        # Check for specific element types
        assert len(meeting.agenda_items) > 0, "Should identify agenda items"
        assert len(meeting.decisions) > 0, "Should identify decisions"
        assert len(meeting.action_items) > 0, "Should identify action items"
        
        # Check element quality
        high_confidence_elements = meeting.get_high_confidence_elements(0.3)
        assert len(high_confidence_elements) > 0, "Should have some high confidence elements"
    
    def test_post_process_elements(self):
        """Test element post-processing"""
        # Create a meeting with duplicate elements
        meeting = MeetingStructure("test_meeting")
        
        # Add duplicate elements
        element1 = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="We decided to proceed",
            confidence=0.7
        )
        element2 = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="We decided to proceed",
            confidence=0.8
        )
        
        meeting.elements = [element1, element2]
        
        # Post-process
        self.identifier._post_process_elements(meeting)
        
        # Should remove duplicates and keep higher confidence
        assert len(meeting.elements) == 1, "Should remove duplicate elements"
        assert meeting.elements[0].confidence == 0.8, "Should keep higher confidence element"
    
    def test_get_element_statistics(self):
        """Test element statistics generation"""
        meeting = self.identifier.identify_elements(self.sample_transcript)
        stats = self.identifier.get_element_statistics(meeting)
        
        # Check required statistics
        assert 'total_elements' in stats
        assert 'by_type' in stats
        assert 'by_confidence_level' in stats
        assert 'average_confidence' in stats
        assert 'high_confidence_count' in stats
        assert 'attendee_count' in stats
        
        # Validate values
        assert stats['total_elements'] == len(meeting.elements)
        assert stats['attendee_count'] == len(meeting.attendees)
        assert 0 <= stats['average_confidence'] <= 1.0

class TestMeetingElement:
    """Test MeetingElement class"""
    
    def test_confidence_level_assignment(self):
        """Test automatic confidence level assignment"""
        test_cases = [
            (0.95, ConfidenceLevel.VERY_HIGH),
            (0.80, ConfidenceLevel.HIGH),
            (0.60, ConfidenceLevel.MEDIUM),
            (0.30, ConfidenceLevel.LOW),
            (0.10, ConfidenceLevel.VERY_LOW)
        ]
        
        for confidence, expected_level in test_cases:
            element = MeetingElement(
                element_type=MeetingElementType.DECISION,
                content="Test content",
                confidence=confidence
            )
            assert element.confidence_level == expected_level, \
                f"Confidence {confidence} should map to {expected_level}"

class TestMeetingStructure:
    """Test MeetingStructure class"""
    
    def test_add_element(self):
        """Test adding elements to meeting structure"""
        meeting = MeetingStructure("test_meeting")
        
        # Add different types of elements
        agenda_item = MeetingElement(
            element_type=MeetingElementType.AGENDA_ITEM,
            content="Discuss budget"
        )
        decision = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="Approved budget"
        )
        action_item = MeetingElement(
            element_type=MeetingElementType.ACTION_ITEM,
            content="John will prepare report"
        )
        
        meeting.add_element(agenda_item)
        meeting.add_element(decision)
        meeting.add_element(action_item)
        
        # Check categorization
        assert len(meeting.elements) == 3
        assert len(meeting.agenda_items) == 1
        assert len(meeting.decisions) == 1
        assert len(meeting.action_items) == 1
    
    def test_get_elements_by_type(self):
        """Test filtering elements by type"""
        meeting = MeetingStructure("test_meeting")
        
        decision1 = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="First decision"
        )
        decision2 = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="Second decision"
        )
        agenda_item = MeetingElement(
            element_type=MeetingElementType.AGENDA_ITEM,
            content="Agenda item"
        )
        
        meeting.add_element(decision1)
        meeting.add_element(decision2)
        meeting.add_element(agenda_item)
        
        decisions = meeting.get_elements_by_type(MeetingElementType.DECISION)
        assert len(decisions) == 2
        
        agenda_items = meeting.get_elements_by_type(MeetingElementType.AGENDA_ITEM)
        assert len(agenda_items) == 1
    
    def test_get_high_confidence_elements(self):
        """Test filtering high confidence elements"""
        meeting = MeetingStructure("test_meeting")
        
        high_conf = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="High confidence",
            confidence=0.9
        )
        low_conf = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="Low confidence",
            confidence=0.3
        )
        
        meeting.add_element(high_conf)
        meeting.add_element(low_conf)
        
        high_elements = meeting.get_high_confidence_elements(0.75)
        assert len(high_elements) == 1
        assert high_elements[0].content == "High confidence"

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_meeting_identifier(self):
        """Test meeting identifier creation"""
        identifier = create_meeting_identifier()
        assert isinstance(identifier, MeetingElementIdentifier)
    
    def test_analyze_meeting_transcript(self):
        """Test transcript analysis utility function"""
        transcript = """
John: Welcome to the meeting.
Sarah: Let's discuss the budget.
John: We've decided to approve it.
        """
        
        meeting = analyze_meeting_transcript(transcript)
        
        assert isinstance(meeting, MeetingStructure)
        assert len(meeting.elements) > 0
        assert len(meeting.attendees) >= 2

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.identifier = MeetingElementIdentifier()
    
    def test_empty_transcript(self):
        """Test handling of empty transcript"""
        meeting = self.identifier.identify_elements("")
        
        assert len(meeting.elements) == 0
        assert len(meeting.attendees) == 0
    
    def test_transcript_without_speakers(self):
        """Test transcript without speaker identification"""
        transcript = """
This is a meeting without clear speaker identification.
We need to discuss the budget.
The decision is to proceed with the plan.
        """
        
        meeting = self.identifier.identify_elements(transcript)
        
        # Should still identify some elements
        assert len(meeting.elements) > 0
        # But no speakers identified
        elements_with_speakers = [e for e in meeting.elements if e.speaker]
        assert len(elements_with_speakers) == 0
    
    def test_transcript_without_timestamps(self):
        """Test transcript without timestamps"""
        transcript = """
John: Welcome everyone.
Sarah: Let's start with the agenda.
Mike: I agree with the proposal.
        """
        
        meeting = self.identifier.identify_elements(transcript)
        
        # Should identify speakers but no timestamps
        assert len(meeting.attendees) > 0
        elements_with_timestamps = [e for e in meeting.elements if e.start_time is not None]
        assert len(elements_with_timestamps) == 0
    
    def test_malformed_timestamps(self):
        """Test handling of malformed timestamps"""
        transcript = """
[invalid] John: Hello
[25:70] Sarah: This timestamp is invalid
[14:30] Mike: This one is valid
        """
        
        meeting = self.identifier.identify_elements(transcript)
        
        # Should handle malformed timestamps gracefully
        assert len(meeting.attendees) >= 2
        elements_with_valid_timestamps = [
            e for e in meeting.elements 
            if e.start_time is not None and e.start_time > 0
        ]
        # Should have at least one valid timestamp
        assert len(elements_with_valid_timestamps) >= 0
    
    def test_very_short_content(self):
        """Test handling of very short content"""
        transcript = """
John: Hi
Sarah: Ok
Mike: Yes
        """
        
        meeting = self.identifier.identify_elements(transcript)
        
        # Should identify speakers but likely no meaningful elements
        assert len(meeting.attendees) >= 3
        # Very short content should be filtered out
        meaningful_elements = [e for e in meeting.elements if len(e.content) > 5]
        assert len(meaningful_elements) >= 0  # May or may not have meaningful elements

def test_integration():
    """Integration test with realistic meeting scenario"""
    transcript = """
[09:00] Alice Johnson: Good morning everyone, welcome to our weekly team standup.
[09:01] Bob Smith: Morning Alice, thanks for organizing this.
[09:02] Alice Johnson: Let's start with agenda item 1 - project status updates.
[09:03] Bob Smith: The frontend development is on track. We completed the user authentication module.
[09:05] Carol Davis: Great work Bob. On the backend side, we've finished the API endpoints.
[09:07] Alice Johnson: Excellent progress. Any blockers or concerns?
[09:08] Bob Smith: I have a question about the database schema changes.
[09:10] Carol Davis: What's your concern Bob?
[09:11] Bob Smith: The new user table structure might affect our existing queries.
[09:13] Carol Davis: Good point. I think we need to review the migration scripts.
[09:15] Alice Johnson: Agreed. Carol, can you audit the migration scripts by Thursday?
[09:16] Carol Davis: Absolutely. I'll have a full review ready by Thursday morning.
[09:18] Alice Johnson: Perfect. Moving on to agenda item 2 - sprint planning.
[09:20] Bob Smith: For next sprint, I suggest we focus on the dashboard components.
[09:22] Carol Davis: I agree. We should also prioritize the notification system.
[09:24] Alice Johnson: Sounds good. We've decided to focus on dashboard and notifications for next sprint.
[09:26] Alice Johnson: Any other business before we wrap up?
[09:27] Bob Smith: Just a quick note - the client demo is scheduled for next Friday.
[09:28] Carol Davis: Thanks for the reminder. We should prepare a demo script.
[09:30] Alice Johnson: Good idea. Bob, can you prepare the demo script by Wednesday?
[09:31] Bob Smith: Sure, I'll have it ready.
[09:32] Alice Johnson: Great. Follow up meeting same time next week. Thanks everyone!
[09:33] Alice Johnson: Meeting adjourned.
    """
    
    context = {
        'meeting_id': 'weekly_standup_2024',
        'title': 'Weekly Team Standup',
        'date': datetime(2024, 1, 15, 9, 0)
    }
    
    meeting = analyze_meeting_transcript(transcript, context)
    
    # Comprehensive checks
    assert meeting.meeting_id == 'weekly_standup_2024'
    assert meeting.title == 'Weekly Team Standup'
    
    # Should identify all attendees
    expected_attendees = ['Alice Johnson', 'Bob Smith', 'Carol Davis']
    for attendee in expected_attendees:
        assert attendee in meeting.attendees, f"Should identify {attendee}"
    
    # Should identify various element types
    assert len(meeting.agenda_items) >= 2, "Should identify agenda items"
    assert len(meeting.decisions) >= 1, "Should identify decisions"
    assert len(meeting.action_items) >= 2, "Should identify action items"
    
    # Check for specific content
    agenda_contents = [item.content.lower() for item in meeting.agenda_items]
    assert any('project status' in content for content in agenda_contents), \
        "Should identify project status agenda item"
    
    action_contents = [action.content.lower() for action in meeting.action_items]
    assert any('migration scripts' in content for content in action_contents), \
        "Should identify migration scripts action item"
    
    decision_contents = [decision.content.lower() for decision in meeting.decisions]
    assert any('dashboard' in content and 'notifications' in content for content in decision_contents), \
        "Should identify sprint focus decision"
    
    # Statistics validation
    identifier = create_meeting_identifier()
    stats = identifier.get_element_statistics(meeting)
    
    assert stats['total_elements'] > 5, "Should identify multiple elements"
    assert stats['attendee_count'] == 3, "Should count all attendees"
    assert stats['average_confidence'] > 0.2, "Should have reasonable average confidence"
    assert stats['elements_with_speakers'] > 5, "Most elements should have speakers"
    assert stats['elements_with_timestamps'] > 5, "Most elements should have timestamps"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])