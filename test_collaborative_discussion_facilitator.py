#!/usr/bin/env python3
"""
Test suite for Collaborative Discussion Facilitator
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from collaborative_discussion_facilitator import (
    CollaborativeDiscussionFacilitator,
    DiscussionContext,
    FacilitationMode,
    DiscussionAnalyzer,
    FacilitationEngine,
    TopicSuggestionEngine,
    ParticipationMetrics
)

class TestDiscussionAnalyzer:
    """Test the discussion analyzer component"""
    
    def setup_method(self):
        self.analyzer = DiscussionAnalyzer()
    
    def test_analyze_participation_basic(self):
        """Test basic participation analysis"""
        session_data = {
            'segments': [
                {'user_id': 'alice', 'text': 'I think this is a great idea!', 'duration': 3.0},
                {'user_id': 'bob', 'text': 'What about the costs?', 'duration': 2.0},
                {'user_id': 'alice', 'text': 'Good point, we should consider that', 'duration': 2.5}
            ]
        }
        
        metrics = self.analyzer.analyze_participation(session_data)
        
        assert len(metrics) == 2  # Two participants
        assert any(m.user_id == 'alice' for m in metrics)
        assert any(m.user_id == 'bob' for m in metrics)
        
        # Alice should have more speaking time
        alice_metrics = next(m for m in metrics if m.user_id == 'alice')
        bob_metrics = next(m for m in metrics if m.user_id == 'bob')
        
        assert alice_metrics.speaking_time > bob_metrics.speaking_time
        assert bob_metrics.question_count > 0  # Bob asked a question
    
    def test_confidence_estimation(self):
        """Test confidence level estimation"""
        high_confidence = ['I definitely think this is the right approach']
        low_confidence = ['Um, maybe we could, like, sort of try this?']
        
        high_score = self.analyzer._estimate_confidence(high_confidence)
        low_score = self.analyzer._estimate_confidence(low_confidence)
        
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1
    
    def test_topic_relevance_calculation(self):
        """Test topic relevance calculation"""
        topic = "user experience design"
        relevant_contributions = ["The user experience is crucial", "Design should be user-centered"]
        irrelevant_contributions = ["What's for lunch?", "Nice weather today"]
        
        relevant_score = self.analyzer._calculate_topic_relevance(relevant_contributions, topic)
        irrelevant_score = self.analyzer._calculate_topic_relevance(irrelevant_contributions, topic)
        
        assert relevant_score > irrelevant_score

class TestFacilitationEngine:
    """Test the facilitation engine"""
    
    def setup_method(self):
        self.engine = FacilitationEngine()
    
    def test_generate_participation_suggestions(self):
        """Test participation balancing suggestions"""
        # Create mock participation metrics
        metrics = [
            ParticipationMetrics('alice', 10.0, 5, 2, 3, 1, 0.8, 0.7, 0.9),  # High engagement
            ParticipationMetrics('bob', 2.0, 1, 0, 1, 0, 0.2, 0.5, 0.6),     # Low engagement
            ParticipationMetrics('charlie', 5.0, 3, 1, 2, 0, 0.5, 0.6, 0.8)  # Medium engagement
        ]
        
        context = DiscussionContext(
            session_id="test",
            participants=["alice", "bob", "charlie"],
            topic="Test Topic",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=30,
            objectives=[],
            current_phase="discussion",
            metadata={}
        )
        
        suggestions = self.engine._generate_participation_suggestions(metrics, context)
        
        # Should suggest encouraging quiet participants
        encourage_suggestions = [s for s in suggestions if s.suggestion_type == "encourage_participation"]
        assert len(encourage_suggestions) > 0
        
        # Should target low-engagement participants
        bob_targeted = any('bob' in s.target_participants for s in encourage_suggestions)
        assert bob_targeted
    
    def test_discussion_state_analysis(self):
        """Test discussion state analysis"""
        session_data = {'segments': []}
        metrics = [
            ParticipationMetrics('alice', 15.0, 8, 2, 3, 1, 0.9, 0.8, 0.9),  # Dominant
            ParticipationMetrics('bob', 3.0, 2, 1, 1, 0, 0.3, 0.5, 0.7),     # Quiet
        ]
        
        state = self.engine._analyze_discussion_state(session_data, metrics)
        
        assert state['total_participants'] == 2
        assert state['dominant_speaker'] == 'alice'  # Alice speaks >40% of time
        assert 'bob' in state['quiet_participants']

class TestTopicSuggestionEngine:
    """Test the topic suggestion engine"""
    
    def setup_method(self):
        self.engine = TopicSuggestionEngine()
    
    def test_generate_brainstorming_topics(self):
        """Test brainstorming topic generation"""
        context = DiscussionContext(
            session_id="test",
            participants=["alice", "bob"],
            topic="Product Innovation",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=30,
            objectives=[],
            current_phase="ideation",
            metadata={}
        )
        
        session_data = {'segments': []}
        discussion_state = {'energy_level': 0.6}
        
        suggestions = self.engine.generate_topic_suggestions(context, session_data, discussion_state)
        
        assert len(suggestions) > 0
        assert all(s.relevance_score > 0 for s in suggestions)
        assert all(len(s.suggested_questions) > 0 for s in suggestions)
    
    def test_decision_making_topics(self):
        """Test decision-making topic generation"""
        context = DiscussionContext(
            session_id="test",
            participants=["alice", "bob"],
            topic="Budget Allocation",
            mode=FacilitationMode.DECISION_MAKING,
            duration_minutes=45,
            objectives=["Decide on budget priorities"],
            current_phase="evaluation",
            metadata={}
        )
        
        suggestions = self.engine._generate_decision_topics("", context)
        
        # Should include decision-specific topics
        topic_names = [s.topic for s in suggestions]
        assert any("criteria" in topic.lower() for topic in topic_names)

class TestCollaborativeDiscussionFacilitator:
    """Test the main facilitator class"""
    
    def setup_method(self):
        # Mock the collaborative engine
        self.mock_engine = Mock()
        self.mock_engine.get_session_state = Mock(return_value={'segments': []})
        self.mock_engine.broadcast_message = AsyncMock()
        
        self.facilitator = CollaborativeDiscussionFacilitator(self.mock_engine)
    
    @pytest.mark.asyncio
    async def test_start_facilitated_session(self):
        """Test starting a facilitated session"""
        context = DiscussionContext(
            session_id="test_session",
            participants=["alice", "bob"],
            topic="Team Planning",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=30,
            objectives=["Generate ideas", "Prioritize actions"],
            current_phase="start",
            metadata={}
        )
        
        result = await self.facilitator.start_facilitated_session("test_session", context)
        
        assert result is True
        assert "test_session" in self.facilitator.active_sessions
        
        # Should have sent opening message
        self.mock_engine.broadcast_message.assert_called()
        
        # Clean up
        if "test_session" in self.facilitator.active_sessions:
            del self.facilitator.active_sessions["test_session"]
    
    @pytest.mark.asyncio
    async def test_process_discussion_update(self):
        """Test processing discussion updates"""
        # First start a session
        context = DiscussionContext(
            session_id="test_session",
            participants=["alice", "bob"],
            topic="Project Review",
            mode=FacilitationMode.DECISION_MAKING,
            duration_minutes=30,
            objectives=[],
            current_phase="discussion",
            metadata={}
        )
        
        await self.facilitator.start_facilitated_session("test_session", context)
        
        # Process an update
        session_data = {
            'segments': [
                {'user_id': 'alice', 'text': 'I disagree with that approach', 'duration': 3.0},
                {'user_id': 'bob', 'text': 'No, I think you are wrong', 'duration': 2.0}
            ]
        }
        
        await self.facilitator.process_discussion_update("test_session", session_data)
        
        # Should have updated session state
        session_state = self.facilitator.active_sessions["test_session"]
        assert session_state['last_analysis'] is not None
        
        # Clean up
        del self.facilitator.active_sessions["test_session"]
    
    def test_get_session_analytics(self):
        """Test getting session analytics"""
        # Create a mock session
        context = DiscussionContext(
            session_id="analytics_test",
            participants=["alice"],
            topic="Test",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=30,
            objectives=[],
            current_phase="test",
            metadata={}
        )
        
        self.facilitator.active_sessions["analytics_test"] = {
            'context': context,
            'start_time': datetime.now(),
            'facilitation_history': [{'test': 'data'}],
            'suggestion_queue': []
        }
        
        analytics = self.facilitator.get_session_analytics("analytics_test")
        
        assert analytics is not None
        assert analytics['session_id'] == "analytics_test"
        assert 'duration' in analytics
        assert analytics['facilitation_interventions'] == 1
        
        # Clean up
        del self.facilitator.active_sessions["analytics_test"]
    
    @pytest.mark.asyncio
    async def test_end_facilitated_session(self):
        """Test ending a facilitated session"""
        # Start a session first
        context = DiscussionContext(
            session_id="end_test",
            participants=["alice"],
            topic="Test",
            mode=FacilitationMode.BRAINSTORMING,
            duration_minutes=30,
            objectives=[],
            current_phase="test",
            metadata={}
        )
        
        await self.facilitator.start_facilitated_session("end_test", context)
        
        # End the session
        summary = await self.facilitator.end_facilitated_session("end_test")
        
        assert summary['session_id'] == "end_test"
        assert 'duration_minutes' in summary
        assert "end_test" not in self.facilitator.active_sessions

# Integration test
@pytest.mark.asyncio
async def test_full_facilitation_workflow():
    """Test complete facilitation workflow"""
    # Mock collaborative engine
    mock_engine = Mock()
    mock_engine.get_session_state = Mock(return_value={
        'segments': [
            {'user_id': 'alice', 'text': 'What do you think about this idea?', 'duration': 2.0},
            {'user_id': 'bob', 'text': 'I think it has potential', 'duration': 1.5}
        ]
    })
    mock_engine.broadcast_message = AsyncMock()
    
    facilitator = CollaborativeDiscussionFacilitator(mock_engine)
    
    # Create context
    context = DiscussionContext(
        session_id="integration_test",
        participants=["alice", "bob"],
        topic="Product Strategy",
        mode=FacilitationMode.BRAINSTORMING,
        duration_minutes=20,
        objectives=["Generate ideas", "Build consensus"],
        current_phase="ideation",
        metadata={}
    )
    
    # Full workflow
    start_result = await facilitator.start_facilitated_session("integration_test", context)
    assert start_result is True
    
    # Process updates
    session_data = mock_engine.get_session_state("integration_test")
    await facilitator.process_discussion_update("integration_test", session_data)
    
    # Get analytics
    analytics = facilitator.get_session_analytics("integration_test")
    assert analytics is not None
    
    # End session
    summary = await facilitator.end_facilitated_session("integration_test")
    assert summary['session_id'] == "integration_test"
    
    # Verify broadcast was called multiple times (opening + facilitation messages)
    assert mock_engine.broadcast_message.call_count >= 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])