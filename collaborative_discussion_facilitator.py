#!/usr/bin/env python3
"""
AI-Powered Discussion Facilitation Engine
Intelligent discussion guidance, topic suggestions, and participation balancing for collaborative sessions
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import re
from collections import defaultdict, deque

# Import existing infrastructure
from emotion_sentiment_detection import EmotionDetector, SentimentAnalyzer, MoodTracker
from speech_pattern_analysis import SpeechRateAnalyzer, ConfidenceAnalyzer
from advanced_content_intelligence import AdvancedContentIntelligence
from realtime_collaborative_transcription import CollaborativeTranscriptionEngine

# Enhanced integrations for comprehensive meeting intelligence
try:
    from action_item_extraction import ActionItemExtractor
    from hybrid_summarization_system import HybridSummarizationSystem
    MEETING_INTELLIGENCE_AVAILABLE = True
except ImportError:
    MEETING_INTELLIGENCE_AVAILABLE = False
    logger.warning("Meeting intelligence features not available - install action_item_extraction and hybrid_summarization_system")

logger = logging.getLogger(__name__)

class FacilitationMode(Enum):
    """Discussion facilitation modes"""
    BRAINSTORMING = "brainstorming"
    DECISION_MAKING = "decision_making"
    PROBLEM_SOLVING = "problem_solving"
    KNOWLEDGE_SHARING = "knowledge_sharing"
    CONFLICT_RESOLUTION = "conflict_resolution"

@dataclass
class DiscussionContext:
    """Context information for discussion facilitation"""
    session_id: str
    participants: List[str]
    topic: str
    mode: FacilitationMode
    duration_minutes: int
    objectives: List[str]
    current_phase: str
    metadata: Dict[str, Any]

@dataclass
class ParticipationMetrics:
    """Metrics for individual participant engagement"""
    user_id: str
    speaking_time: float
    contribution_count: int
    question_count: int
    agreement_signals: int
    disagreement_signals: int
    engagement_score: float
    confidence_level: float
    topic_relevance: float

@dataclass
class FacilitationSuggestion:
    """AI-generated facilitation suggestion"""
    suggestion_type: str
    priority: str  # high, medium, low
    message: str
    target_participants: List[str]
    timing: str  # immediate, next_pause, end_of_phase
    rationale: str
    expected_outcome: str

@dataclass
class TopicSuggestion:
    """AI-generated topic suggestion"""
    topic: str
    relevance_score: float
    reasoning: str
    suggested_questions: List[str]
    estimated_duration: int  # minutes
    prerequisites: List[str]

class DiscussionAnalyzer:
    """Analyze ongoing discussion patterns and dynamics"""
    
    def __init__(self):
        self.emotion_detector = EmotionDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.text_analyzer = AdvancedContentIntelligence()
        self.speech_analyzer = SpeechRateAnalyzer()
        
        # Discussion pattern recognition
        self.question_patterns = [
            r'\b(what|how|why|when|where|who)\b.*\?',
            r'\b(could|would|should|can|will)\b.*\?',
            r'\b(do you think|what if|how about)\b'
        ]
        
        self.agreement_patterns = [
            r'\b(yes|agree|exactly|right|correct|absolutely)\b',
            r'\b(i think so|that\'s true|good point)\b'
        ]
        
        self.disagreement_patterns = [
            r'\b(no|disagree|wrong|incorrect|but|however)\b',
            r'\b(i don\'t think|not sure|actually)\b'
        ]
        
    def analyze_participation(self, session_data: Dict[str, Any]) -> List[ParticipationMetrics]:
        """Analyze participation patterns for all users"""
        participants = {}
        
        # Process transcription segments
        for segment in session_data.get('segments', []):
            user_id = segment.get('user_id', 'unknown')
            text = segment.get('text', '')
            duration = segment.get('duration', 0)
            
            if user_id not in participants:
                participants[user_id] = {
                    'speaking_time': 0,
                    'contributions': [],
                    'questions': 0,
                    'agreements': 0,
                    'disagreements': 0
                }
            
            participants[user_id]['speaking_time'] += duration
            participants[user_id]['contributions'].append(text)
            
            # Count questions
            for pattern in self.question_patterns:
                participants[user_id]['questions'] += len(re.findall(pattern, text, re.IGNORECASE))
            
            # Count agreement/disagreement signals
            for pattern in self.agreement_patterns:
                participants[user_id]['agreements'] += len(re.findall(pattern, text, re.IGNORECASE))
            
            for pattern in self.disagreement_patterns:
                participants[user_id]['disagreements'] += len(re.findall(pattern, text, re.IGNORECASE))
        
        # Calculate metrics for each participant
        metrics = []
        total_speaking_time = sum(p['speaking_time'] for p in participants.values())
        
        for user_id, data in participants.items():
            # Calculate engagement score
            contribution_count = len(data['contributions'])
            speaking_ratio = data['speaking_time'] / total_speaking_time if total_speaking_time > 0 else 0
            interaction_score = (data['questions'] + data['agreements'] + data['disagreements']) / max(1, contribution_count)
            
            engagement_score = (speaking_ratio * 0.4 + 
                              min(1.0, contribution_count / 10) * 0.3 + 
                              min(1.0, interaction_score) * 0.3)
            
            # Estimate confidence level from speech patterns
            confidence_level = self._estimate_confidence(data['contributions'])
            
            # Calculate topic relevance
            topic_relevance = self._calculate_topic_relevance(
                data['contributions'], 
                session_data.get('topic', '')
            )
            
            metrics.append(ParticipationMetrics(
                user_id=user_id,
                speaking_time=data['speaking_time'],
                contribution_count=contribution_count,
                question_count=data['questions'],
                agreement_signals=data['agreements'],
                disagreement_signals=data['disagreements'],
                engagement_score=engagement_score,
                confidence_level=confidence_level,
                topic_relevance=topic_relevance
            ))
        
        return metrics 
   
    def _estimate_confidence(self, contributions: List[str]) -> float:
        """Estimate speaker confidence from text patterns"""
        if not contributions:
            return 0.5
        
        confidence_indicators = {
            'positive': [r'\b(definitely|certainly|absolutely|clearly)\b', 
                        r'\b(i believe|i think|in my opinion)\b'],
            'negative': [r'\b(maybe|perhaps|possibly|i guess)\b',
                        r'\b(um|uh|er|like)\b',
                        r'\b(sort of|kind of|i mean)\b']
        }
        
        total_text = ' '.join(contributions).lower()
        positive_count = sum(len(re.findall(pattern, total_text)) 
                           for pattern in confidence_indicators['positive'])
        negative_count = sum(len(re.findall(pattern, total_text)) 
                           for pattern in confidence_indicators['negative'])
        
        if positive_count + negative_count == 0:
            return 0.7  # Neutral confidence
        
        confidence = positive_count / (positive_count + negative_count)
        return max(0.1, min(0.9, confidence))
    
    def _calculate_topic_relevance(self, contributions: List[str], topic: str) -> float:
        """Calculate how relevant contributions are to the main topic"""
        if not contributions or not topic:
            return 0.5
        
        topic_words = set(topic.lower().split())
        total_relevance = 0
        
        for contribution in contributions:
            words = set(contribution.lower().split())
            overlap = len(topic_words.intersection(words))
            relevance = overlap / len(topic_words) if topic_words else 0
            total_relevance += relevance
        
        return min(1.0, total_relevance / len(contributions))

class FacilitationEngine:
    """Core AI facilitation engine"""
    
    def __init__(self):
        self.discussion_analyzer = DiscussionAnalyzer()
        self.facilitation_history = deque(maxlen=100)
        
        # Facilitation templates by mode
        self.facilitation_templates = {
            FacilitationMode.BRAINSTORMING: {
                'opening': "Let's generate as many ideas as possible. Remember, no idea is too wild!",
                'encouragement': "Great ideas so far! Who has a different perspective?",
                'redirect': "Let's build on that idea. How might we expand it further?",
                'closing': "Excellent brainstorming! Let's now prioritize these ideas."
            },
            FacilitationMode.DECISION_MAKING: {
                'opening': "We need to make a decision on {topic}. Let's review our options.",
                'encouragement': "Good points raised. What are the pros and cons?",
                'redirect': "Let's focus on the criteria for making this decision.",
                'closing': "Based on our discussion, what's our consensus?"
            },
            FacilitationMode.PROBLEM_SOLVING: {
                'opening': "Let's break down this problem systematically.",
                'encouragement': "Interesting approach! How would that work in practice?",
                'redirect': "Let's consider the root causes of this issue.",
                'closing': "What's our action plan moving forward?"
            }
        }
    
    def generate_facilitation_suggestions(self, 
                                        context: DiscussionContext,
                                        session_data: Dict[str, Any],
                                        participation_metrics: List[ParticipationMetrics]) -> List[FacilitationSuggestion]:
        """Generate AI-powered facilitation suggestions"""
        suggestions = []
        
        # Analyze current discussion state
        discussion_state = self._analyze_discussion_state(session_data, participation_metrics)
        
        # Generate participation balancing suggestions
        suggestions.extend(self._generate_participation_suggestions(
            participation_metrics, context
        ))
        
        # Generate topic guidance suggestions
        suggestions.extend(self._generate_topic_suggestions(
            discussion_state, context
        ))
        
        # Generate time management suggestions
        suggestions.extend(self._generate_time_management_suggestions(
            context, session_data
        ))
        
        # Generate conflict resolution suggestions if needed
        if discussion_state.get('conflict_detected', False):
            suggestions.extend(self._generate_conflict_resolution_suggestions(
                discussion_state, context
            ))
        
        # Sort by priority and relevance
        suggestions.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x.priority], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _analyze_discussion_state(self, session_data: Dict[str, Any], 
                                 participation_metrics: List[ParticipationMetrics]) -> Dict[str, Any]:
        """Analyze current state of discussion"""
        state = {
            'total_participants': len(participation_metrics),
            'active_participants': len([p for p in participation_metrics if p.engagement_score > 0.3]),
            'dominant_speaker': None,
            'quiet_participants': [],
            'conflict_detected': False,
            'energy_level': 0.5,
            'topic_drift': False
        }
        
        if participation_metrics:
            # Find dominant speaker
            max_speaking_time = max(p.speaking_time for p in participation_metrics)
            total_speaking_time = sum(p.speaking_time for p in participation_metrics)
            
            for participant in participation_metrics:
                if participant.speaking_time == max_speaking_time:
                    if participant.speaking_time > total_speaking_time * 0.4:  # Speaking >40% of time
                        state['dominant_speaker'] = participant.user_id
                
                # Identify quiet participants
                if participant.engagement_score < 0.2:
                    state['quiet_participants'].append(participant.user_id)
            
            # Detect potential conflict
            disagreement_ratio = sum(p.disagreement_signals for p in participation_metrics) / max(1, sum(p.contribution_count for p in participation_metrics))
            if disagreement_ratio > 0.3:
                state['conflict_detected'] = True
            
            # Calculate energy level
            avg_engagement = sum(p.engagement_score for p in participation_metrics) / len(participation_metrics)
            state['energy_level'] = avg_engagement
        
        return state
    
    def _generate_participation_suggestions(self, 
                                          participation_metrics: List[ParticipationMetrics],
                                          context: DiscussionContext) -> List[FacilitationSuggestion]:
        """Generate suggestions for balancing participation"""
        suggestions = []
        
        if not participation_metrics:
            return suggestions
        
        # Identify participation imbalances
        avg_engagement = sum(p.engagement_score for p in participation_metrics) / len(participation_metrics)
        
        # Encourage quiet participants
        quiet_participants = [p for p in participation_metrics if p.engagement_score < avg_engagement * 0.5]
        if quiet_participants:
            for participant in quiet_participants[:2]:  # Focus on top 2 quiet participants
                suggestions.append(FacilitationSuggestion(
                    suggestion_type="encourage_participation",
                    priority="medium",
                    message=f"Let's hear from {participant.user_id}. What are your thoughts on this?",
                    target_participants=[participant.user_id],
                    timing="next_pause",
                    rationale=f"Participant has low engagement score ({participant.engagement_score:.2f})",
                    expected_outcome="Increase participation balance"
                ))
        
        # Manage dominant speakers
        dominant_speakers = [p for p in participation_metrics if p.engagement_score > avg_engagement * 1.5]
        if dominant_speakers:
            for speaker in dominant_speakers:
                suggestions.append(FacilitationSuggestion(
                    suggestion_type="manage_dominance",
                    priority="low",
                    message=f"Thank you {speaker.user_id}. Let's hear other perspectives on this.",
                    target_participants=[speaker.user_id],
                    timing="immediate",
                    rationale=f"Participant is dominating discussion ({speaker.engagement_score:.2f})",
                    expected_outcome="Better participation balance"
                ))
        
        return suggestions
    
    def _generate_topic_suggestions(self, 
                                   discussion_state: Dict[str, Any],
                                   context: DiscussionContext) -> List[FacilitationSuggestion]:
        """Generate topic guidance suggestions"""
        suggestions = []
        
        # Suggest topic refocus if energy is low
        if discussion_state['energy_level'] < 0.4:
            suggestions.append(FacilitationSuggestion(
                suggestion_type="refocus_topic",
                priority="high",
                message="Let's refocus on our main objective. What specific aspects should we explore?",
                target_participants=[],
                timing="immediate",
                rationale="Low energy level detected, need to refocus discussion",
                expected_outcome="Increased engagement and focus"
            ))
        
        # Suggest deeper exploration for active discussions
        if discussion_state['energy_level'] > 0.7:
            suggestions.append(FacilitationSuggestion(
                suggestion_type="deepen_exploration",
                priority="medium",
                message="Great discussion! Let's dive deeper. What are the implications of this?",
                target_participants=[],
                timing="next_pause",
                rationale="High energy level, good time to explore deeper",
                expected_outcome="More thorough analysis"
            ))
        
        return suggestions
    
    def _generate_time_management_suggestions(self, 
                                            context: DiscussionContext,
                                            session_data: Dict[str, Any]) -> List[FacilitationSuggestion]:
        """Generate time management suggestions"""
        suggestions = []
        
        # Calculate elapsed time (actual implementation)
        try:
            # Get session start time from context or session data
            session_start = context.start_time if hasattr(context, 'start_time') else datetime.now()
            
            # Calculate elapsed time
            current_time = datetime.now()
            elapsed_time = current_time - session_start
            elapsed_minutes = elapsed_time.total_seconds() / 60
            
            # Calculate remaining time
            remaining_minutes = context.duration_minutes - elapsed_minutes
            
            # Ensure remaining time doesn't go negative
            remaining_minutes = max(0, remaining_minutes)
        except Exception as e:
            # Fallback to mock values if calculation fails
            logger.warning(f"Time calculation failed: {e}, using mock values")
            elapsed_minutes = 15
            remaining_minutes = context.duration_minutes - elapsed_minutes
        
        # Time warnings
        if remaining_minutes <= 10 and remaining_minutes > 5:
            suggestions.append(FacilitationSuggestion(
                suggestion_type="time_warning",
                priority="medium",
                message=f"We have {remaining_minutes} minutes remaining. Let's focus on key decisions.",
                target_participants=[],
                timing="immediate",
                rationale="Approaching time limit",
                expected_outcome="Better time management"
            ))
        elif remaining_minutes <= 5:
            suggestions.append(FacilitationSuggestion(
                suggestion_type="time_critical",
                priority="high",
                message="Final 5 minutes. Let's summarize our key conclusions.",
                target_participants=[],
                timing="immediate",
                rationale="Critical time remaining",
                expected_outcome="Clear conclusions"
            ))
        
        return suggestions
    
    def _generate_conflict_resolution_suggestions(self, 
                                                discussion_state: Dict[str, Any],
                                                context: DiscussionContext) -> List[FacilitationSuggestion]:
        """Generate conflict resolution suggestions"""
        suggestions = []
        
        if discussion_state.get('conflict_detected', False):
            suggestions.append(FacilitationSuggestion(
                suggestion_type="conflict_resolution",
                priority="high",
                message="I notice different viewpoints. Let's explore the common ground first.",
                target_participants=[],
                timing="immediate",
                rationale="Conflict detected in discussion patterns",
                expected_outcome="Reduced tension and better collaboration"
            ))
            
            suggestions.append(FacilitationSuggestion(
                suggestion_type="perspective_taking",
                priority="medium",
                message="Can each side summarize the other's position to ensure understanding?",
                target_participants=[],
                timing="next_pause",
                rationale="Help participants understand different perspectives",
                expected_outcome="Better mutual understanding"
            ))
        
        return suggestions

class TopicSuggestionEngine:
    """Generate intelligent topic suggestions based on discussion context"""
    
    def __init__(self):
        self.topic_templates = {
            'follow_up_questions': [
                "What are the potential risks of this approach?",
                "How would this work in practice?",
                "What resources would we need?",
                "Who would be responsible for implementation?",
                "What's our timeline for this?",
                "How do we measure success?"
            ],
            'exploration_prompts': [
                "What if we approached this differently?",
                "Are there any alternatives we haven't considered?",
                "What would our users/customers think about this?",
                "How does this align with our goals?",
                "What are the long-term implications?"
            ],
            'synthesis_questions': [
                "How do these ideas connect?",
                "What patterns are emerging?",
                "What's the core issue we're addressing?",
                "Where do we have consensus?",
                "What are our key takeaways?"
            ]
        }
    
    def generate_topic_suggestions(self, 
                                 context: DiscussionContext,
                                 session_data: Dict[str, Any],
                                 discussion_state: Dict[str, Any]) -> List[TopicSuggestion]:
        """Generate contextual topic suggestions"""
        suggestions = []
        
        # Analyze recent discussion content
        recent_segments = session_data.get('segments', [])[-10:]  # Last 10 segments
        recent_text = ' '.join([seg.get('text', '') for seg in recent_segments])
        
        # Generate suggestions based on discussion mode
        if context.mode == FacilitationMode.BRAINSTORMING:
            suggestions.extend(self._generate_brainstorming_topics(recent_text, context))
        elif context.mode == FacilitationMode.DECISION_MAKING:
            suggestions.extend(self._generate_decision_topics(recent_text, context))
        elif context.mode == FacilitationMode.PROBLEM_SOLVING:
            suggestions.extend(self._generate_problem_solving_topics(recent_text, context))
        
        # Add general exploration topics
        suggestions.extend(self._generate_exploration_topics(recent_text, discussion_state))
        
        return sorted(suggestions, key=lambda x: x.relevance_score, reverse=True)[:5]
    
    def _generate_brainstorming_topics(self, recent_text: str, context: DiscussionContext) -> List[TopicSuggestion]:
        """Generate brainstorming-specific topic suggestions"""
        suggestions = []
        
        # Encourage idea expansion
        suggestions.append(TopicSuggestion(
            topic="Idea Expansion",
            relevance_score=0.8,
            reasoning="Build on the ideas already shared",
            suggested_questions=[
                "How can we make this idea even better?",
                "What would the ideal version of this look like?",
                "How might we combine different ideas?"
            ],
            estimated_duration=10,
            prerequisites=["Some initial ideas shared"]
        ))
        
        # Alternative perspectives
        suggestions.append(TopicSuggestion(
            topic="Alternative Approaches",
            relevance_score=0.7,
            reasoning="Explore different angles and perspectives",
            suggested_questions=[
                "What would our competitors do?",
                "How would a child approach this?",
                "What if we had unlimited resources?"
            ],
            estimated_duration=15,
            prerequisites=["Initial problem understanding"]
        ))
        
        return suggestions
    
    def _generate_decision_topics(self, recent_text: str, context: DiscussionContext) -> List[TopicSuggestion]:
        """Generate decision-making topic suggestions"""
        suggestions = []
        
        # Criteria evaluation
        suggestions.append(TopicSuggestion(
            topic="Decision Criteria",
            relevance_score=0.9,
            reasoning="Establish clear criteria for making the decision",
            suggested_questions=[
                "What are our must-haves vs nice-to-haves?",
                "How do we prioritize different factors?",
                "What are our constraints?"
            ],
            estimated_duration=12,
            prerequisites=["Options identified"]
        ))
        
        # Risk assessment
        suggestions.append(TopicSuggestion(
            topic="Risk Analysis",
            relevance_score=0.8,
            reasoning="Evaluate potential risks and mitigation strategies",
            suggested_questions=[
                "What could go wrong with each option?",
                "How can we minimize risks?",
                "What's our backup plan?"
            ],
            estimated_duration=15,
            prerequisites=["Options and criteria defined"]
        ))
        
        return suggestions
    
    def _generate_problem_solving_topics(self, recent_text: str, context: DiscussionContext) -> List[TopicSuggestion]:
        """Generate problem-solving topic suggestions"""
        suggestions = []
        
        # Root cause analysis
        suggestions.append(TopicSuggestion(
            topic="Root Cause Analysis",
            relevance_score=0.9,
            reasoning="Identify the underlying causes of the problem",
            suggested_questions=[
                "Why is this problem occurring?",
                "What are the contributing factors?",
                "When did this problem first appear?"
            ],
            estimated_duration=20,
            prerequisites=["Problem clearly defined"]
        ))
        
        # Solution evaluation
        suggestions.append(TopicSuggestion(
            topic="Solution Evaluation",
            relevance_score=0.8,
            reasoning="Assess potential solutions systematically",
            suggested_questions=[
                "Which solutions address the root cause?",
                "What are the trade-offs for each solution?",
                "Which solution is most feasible?"
            ],
            estimated_duration=18,
            prerequisites=["Potential solutions identified"]
        ))
        
        return suggestions
    
    def _generate_exploration_topics(self, recent_text: str, discussion_state: Dict[str, Any]) -> List[TopicSuggestion]:
        """Generate general exploration topics"""
        suggestions = []
        
        # If discussion energy is low, suggest energizing topics
        if discussion_state.get('energy_level', 0.5) < 0.4:
            suggestions.append(TopicSuggestion(
                topic="Success Stories",
                relevance_score=0.6,
                reasoning="Share positive examples to boost energy",
                suggested_questions=[
                    "What similar challenges have we overcome before?",
                    "What's working well in related areas?",
                    "What would success look like?"
                ],
                estimated_duration=8,
                prerequisites=["Low energy discussion"]
            ))
        
        return suggestions

class CollaborativeDiscussionFacilitator:
    """Main facilitator class integrating all components"""
    
    def __init__(self, collaborative_engine: CollaborativeTranscriptionEngine):
        self.collaborative_engine = collaborative_engine
        self.facilitation_engine = FacilitationEngine()
        self.topic_engine = TopicSuggestionEngine()
        self.discussion_analyzer = DiscussionAnalyzer()
        
        # Active facilitation sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Collaborative Discussion Facilitator initialized")
    
    async def start_facilitated_session(self, 
                                      session_id: str,
                                      context: DiscussionContext) -> bool:
        """Start AI-facilitated collaborative session"""
        try:
            # Initialize session state
            self.active_sessions[session_id] = {
                'context': context,
                'start_time': datetime.now(),
                'facilitation_history': [],
                'last_analysis': None,
                'suggestion_queue': deque()
            }
            
            # Send opening facilitation message
            opening_message = self._get_opening_message(context)
            await self._send_facilitation_message(session_id, opening_message)
            
            # Start periodic analysis
            asyncio.create_task(self._periodic_analysis(session_id))
            
            logger.info(f"Started facilitated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting facilitated session: {e}")
            return False
    
    async def process_discussion_update(self, session_id: str, session_data: Dict[str, Any]):
        """Process real-time discussion updates and provide facilitation"""
        if session_id not in self.active_sessions:
            return
        
        try:
            session_state = self.active_sessions[session_id]
            context = session_state['context']
            
            # Analyze current participation
            participation_metrics = self.discussion_analyzer.analyze_participation(session_data)
            
            # Generate facilitation suggestions
            suggestions = self.facilitation_engine.generate_facilitation_suggestions(
                context, session_data, participation_metrics
            )
            
            # Process high-priority suggestions immediately
            for suggestion in suggestions:
                if suggestion.priority == "high" and suggestion.timing == "immediate":
                    await self._send_facilitation_message(session_id, suggestion.message)
                    session_state['facilitation_history'].append({
                        'timestamp': datetime.now(),
                        'suggestion': suggestion,
                        'applied': True
                    })
                else:
                    # Queue for later
                    session_state['suggestion_queue'].append(suggestion)
            
            # Update session state
            session_state['last_analysis'] = {
                'timestamp': datetime.now(),
                'participation_metrics': participation_metrics,
                'suggestions': suggestions
            }
            
        except Exception as e:
            logger.error(f"Error processing discussion update: {e}")
    
    async def _periodic_analysis(self, session_id: str):
        """Perform periodic analysis and facilitation"""
        while session_id in self.active_sessions:
            try:
                await asyncio.sleep(30)  # Analyze every 30 seconds
                
                if session_id not in self.active_sessions:
                    break
                
                session_state = self.active_sessions[session_id]
                context = session_state['context']
                
                # Get current session data from collaborative engine
                current_session_data = self.collaborative_engine.get_session_state(session_id)
                if not current_session_data:
                    continue
                
                # Generate topic suggestions
                discussion_state = {'energy_level': 0.6}  # Mock for now
                topic_suggestions = self.topic_engine.generate_topic_suggestions(
                    context, current_session_data, discussion_state
                )
                
                # Send topic suggestions if appropriate
                if topic_suggestions and len(session_state['suggestion_queue']) < 3:
                    top_suggestion = topic_suggestions[0]
                    message = f"Consider exploring: {top_suggestion.topic}. {top_suggestion.suggested_questions[0]}"
                    await self._send_facilitation_message(session_id, message)
                
                # Process queued suggestions
                if session_state['suggestion_queue']:
                    suggestion = session_state['suggestion_queue'].popleft()
                    if suggestion.timing in ["next_pause", "end_of_phase"]:
                        await self._send_facilitation_message(session_id, suggestion.message)
                
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _send_facilitation_message(self, session_id: str, message: str):
        """Send facilitation message to session participants"""
        try:
            # Create facilitation message
            facilitation_message = {
                "type": "facilitation",
                "session_id": session_id,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "source": "ai_facilitator"
            }
            
            # Broadcast to all session participants
            await self.collaborative_engine.broadcast_message(session_id, facilitation_message)
            
            logger.info(f"Sent facilitation message to session {session_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error sending facilitation message: {e}")
    
    def _get_opening_message(self, context: DiscussionContext) -> str:
        """Get appropriate opening message for the session"""
        templates = self.facilitation_engine.facilitation_templates.get(
            context.mode, 
            self.facilitation_engine.facilitation_templates[FacilitationMode.BRAINSTORMING]
        )
        
        opening = templates['opening'].format(topic=context.topic)
        
        if context.objectives:
            objectives_text = ", ".join(context.objectives)
            opening += f" Our objectives are: {objectives_text}."
        
        return opening
    
    def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a facilitated session"""
        if session_id not in self.active_sessions:
            return None
        
        session_state = self.active_sessions[session_id]
        
        analytics = {
            'session_id': session_id,
            'context': asdict(session_state['context']),
            'duration': (datetime.now() - session_state['start_time']).total_seconds() / 60,
            'facilitation_interventions': len(session_state['facilitation_history']),
            'last_analysis': session_state.get('last_analysis'),
            'active_suggestions': len(session_state['suggestion_queue'])
        }
        
        return analytics
    
    async def end_facilitated_session(self, session_id: str) -> Dict[str, Any]:
        """End facilitated session and return summary"""
        if session_id not in self.active_sessions:
            return {}
        
        try:
            session_state = self.active_sessions[session_id]
            
            # Send closing message
            closing_message = "Thank you for a productive discussion! Let's summarize our key outcomes."
            await self._send_facilitation_message(session_id, closing_message)
            
            # Generate session summary
            summary = {
                'session_id': session_id,
                'duration_minutes': (datetime.now() - session_state['start_time']).total_seconds() / 60,
                'facilitation_interventions': len(session_state['facilitation_history']),
                'context': asdict(session_state['context']),
                'final_analytics': self.get_session_analytics(session_id)
            }
            
            # Clean up
            del self.active_sessions[session_id]
            
            logger.info(f"Ended facilitated session {session_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error ending facilitated session: {e}")
            return {}

# Demo function
async def demo_discussion_facilitator():
    """Demonstrate the discussion facilitator"""
    print("🤖 AI-Powered Discussion Facilitator Demo")
    print("=" * 50)
    
    # Mock collaborative engine
    class MockCollaborativeEngine:
        def get_session_state(self, session_id):
            return {
                'segments': [
                    {'user_id': 'alice', 'text': 'I think we should focus on user experience', 'duration': 3.0},
                    {'user_id': 'bob', 'text': 'What about the technical constraints?', 'duration': 2.5},
                    {'user_id': 'alice', 'text': 'Good point, but users come first', 'duration': 2.0}
                ]
            }
        
        async def broadcast_message(self, session_id, message):
            print(f"📢 Facilitation: {message['message']}")
    
    # Initialize facilitator
    mock_engine = MockCollaborativeEngine()
    facilitator = CollaborativeDiscussionFacilitator(mock_engine)
    
    # Create discussion context
    context = DiscussionContext(
        session_id="demo_session",
        participants=["alice", "bob", "charlie"],
        topic="Product Feature Prioritization",
        mode=FacilitationMode.DECISION_MAKING,
        duration_minutes=30,
        objectives=["Prioritize top 3 features", "Align on timeline"],
        current_phase="discussion",
        metadata={}
    )
    
    print(f"Starting facilitated session: {context.topic}")
    print(f"Mode: {context.mode.value}")
    print(f"Participants: {', '.join(context.participants)}")
    
    # Start session
    await facilitator.start_facilitated_session("demo_session", context)
    
    # Simulate discussion updates
    print("\n📊 Processing discussion updates...")
    session_data = mock_engine.get_session_state("demo_session")
    await facilitator.process_discussion_update("demo_session", session_data)
    
    # Wait a bit for periodic analysis
    await asyncio.sleep(2)
    
    # Get analytics
    analytics = facilitator.get_session_analytics("demo_session")
    print(f"\n📈 Session Analytics:")
    print(f"   Duration: {analytics['duration']:.1f} minutes")
    print(f"   Facilitation interventions: {analytics['facilitation_interventions']}")
    
    # End session
    summary = await facilitator.end_facilitated_session("demo_session")
    print(f"\n✅ Session completed successfully!")
    print(f"   Total interventions: {summary['facilitation_interventions']}")

if __name__ == "__main__":
    asyncio.run(demo_discussion_facilitator())