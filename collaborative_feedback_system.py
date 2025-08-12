#!/usr/bin/env python3
"""
Comprehensive Feedback System for Collaborative Intelligence
Real-time feedback collection, analysis, and improvement recommendations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback collected"""
    FACILITATION_QUALITY = "facilitation_quality"
    PARTICIPATION_BALANCE = "participation_balance"
    TOPIC_RELEVANCE = "topic_relevance"
    MEETING_EFFECTIVENESS = "meeting_effectiveness"
    AI_ACCURACY = "ai_accuracy"
    USER_SATISFACTION = "user_satisfaction"
    TECHNICAL_PERFORMANCE = "technical_performance"

class FeedbackSource(Enum):
    """Sources of feedback"""
    PARTICIPANT_EXPLICIT = "participant_explicit"  # Direct user feedback
    PARTICIPANT_IMPLICIT = "participant_implicit"  # Behavioral signals
    SYSTEM_METRICS = "system_metrics"              # Performance data
    AI_ANALYSIS = "ai_analysis"                    # AI-generated insights
    EXTERNAL_INTEGRATION = "external_integration"  # Third-party tools

@dataclass
class FeedbackEntry:
    """Individual feedback entry"""
    feedback_id: str
    session_id: str
    user_id: Optional[str]
    feedback_type: FeedbackType
    source: FeedbackSource
    rating: Optional[float]  # 1-5 scale
    text_feedback: Optional[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any]  # Session context when feedback was given
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'feedback_type': self.feedback_type.value,
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class FeedbackAnalytics:
    """Aggregated feedback analytics"""
    session_id: str
    total_feedback_count: int
    average_ratings: Dict[str, float]
    sentiment_distribution: Dict[str, float]
    improvement_areas: List[str]
    strengths: List[str]
    participant_satisfaction: float
    ai_effectiveness_score: float
    recommendations: List[str]
    trend_analysis: Dict[str, Any]
    generated_at: datetime

class ImplicitFeedbackCollector:
    """Collects implicit feedback from user behavior"""
    
    def __init__(self):
        self.behavior_patterns = defaultdict(list)
        self.engagement_metrics = {}
        
    def track_user_engagement(self, user_id: str, session_id: str, 
                            action: str, context: Dict[str, Any]) -> None:
        """Track user engagement signals"""
        engagement_signal = {
            'action': action,
            'timestamp': datetime.now(),
            'context': context,
            'session_id': session_id
        }
        
        self.behavior_patterns[user_id].append(engagement_signal)
        
        # Calculate engagement score
        self._update_engagement_score(user_id, action, context)
    
    def _update_engagement_score(self, user_id: str, action: str, 
                                context: Dict[str, Any]) -> None:
        """Update engagement score based on user actions"""
        if user_id not in self.engagement_metrics:
            self.engagement_metrics[user_id] = {
                'score': 0.5,  # Start neutral
                'interactions': 0,
                'positive_signals': 0,
                'negative_signals': 0
            }
        
        metrics = self.engagement_metrics[user_id]
        metrics['interactions'] += 1
        
        # Positive engagement signals
        positive_actions = [
            'message_sent', 'question_asked', 'suggestion_accepted',
            'active_participation', 'collaborative_edit', 'helpful_response'
        ]
        
        # Negative engagement signals  
        negative_actions = [
            'suggestion_dismissed', 'early_exit', 'minimal_participation',
            'distraction_detected', 'negative_feedback'
        ]
        
        if action in positive_actions:
            metrics['positive_signals'] += 1
            metrics['score'] = min(1.0, metrics['score'] + 0.1)
        elif action in negative_actions:
            metrics['negative_signals'] += 1
            metrics['score'] = max(0.0, metrics['score'] - 0.1)
    
    def generate_implicit_feedback(self, user_id: str, session_id: str) -> List[FeedbackEntry]:
        """Generate implicit feedback based on behavior patterns"""
        if user_id not in self.engagement_metrics:
            return []
        
        metrics = self.engagement_metrics[user_id]
        feedback_entries = []
        
        # Engagement-based feedback
        engagement_feedback = FeedbackEntry(
            feedback_id=f"implicit_{user_id}_{session_id}_engagement",
            session_id=session_id,
            user_id=user_id,
            feedback_type=FeedbackType.USER_SATISFACTION,
            source=FeedbackSource.PARTICIPANT_IMPLICIT,
            rating=metrics['score'] * 5,  # Convert to 1-5 scale
            text_feedback=None,
            metadata={
                'total_interactions': metrics['interactions'],
                'positive_signals': metrics['positive_signals'],
                'negative_signals': metrics['negative_signals'],
                'engagement_score': metrics['score']
            },
            timestamp=datetime.now(),
            context={'derived_from': 'behavioral_analysis'}
        )
        
        feedback_entries.append(engagement_feedback)
        return feedback_entries

class FeedbackAnalyzer:
    """Analyzes feedback to generate insights and recommendations"""
    
    def __init__(self):
        self.sentiment_analyzer = None
        try:
            from textblob import TextBlob
            self.sentiment_analyzer = TextBlob
        except ImportError:
            logger.warning("TextBlob not available for sentiment analysis")
    
    def analyze_session_feedback(self, session_id: str, 
                                feedback_entries: List[FeedbackEntry]) -> FeedbackAnalytics:
        """Analyze all feedback for a session"""
        if not feedback_entries:
            return self._empty_analytics(session_id)
        
        # Calculate average ratings by type
        ratings_by_type = defaultdict(list)
        for entry in feedback_entries:
            if entry.rating is not None:
                ratings_by_type[entry.feedback_type.value].append(entry.rating)
        
        average_ratings = {
            feedback_type: np.mean(ratings) 
            for feedback_type, ratings in ratings_by_type.items()
        }
        
        # Analyze text feedback sentiment
        sentiment_distribution = self._analyze_sentiment_distribution(feedback_entries)
        
        # Identify improvement areas and strengths
        improvement_areas = self._identify_improvement_areas(average_ratings, feedback_entries)
        strengths = self._identify_strengths(average_ratings, feedback_entries)
        
        # Calculate overall satisfaction
        participant_satisfaction = self._calculate_participant_satisfaction(feedback_entries)
        
        # Calculate AI effectiveness
        ai_effectiveness_score = self._calculate_ai_effectiveness(feedback_entries)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            average_ratings, improvement_areas, feedback_entries
        )
        
        # Trend analysis (simplified for now)
        trend_analysis = self._analyze_trends(feedback_entries)
        
        return FeedbackAnalytics(
            session_id=session_id,
            total_feedback_count=len(feedback_entries),
            average_ratings=average_ratings,
            sentiment_distribution=sentiment_distribution,
            improvement_areas=improvement_areas,
            strengths=strengths,
            participant_satisfaction=participant_satisfaction,
            ai_effectiveness_score=ai_effectiveness_score,
            recommendations=recommendations,
            trend_analysis=trend_analysis,
            generated_at=datetime.now()
        )
    
    def _analyze_sentiment_distribution(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, float]:
        """Analyze sentiment distribution of text feedback"""
        if not self.sentiment_analyzer:
            return {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
        
        sentiments = []
        for entry in feedback_entries:
            if entry.text_feedback:
                blob = self.sentiment_analyzer(entry.text_feedback)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    sentiments.append('positive')
                elif polarity < -0.1:
                    sentiments.append('negative')
                else:
                    sentiments.append('neutral')
        
        if not sentiments:
            return {'positive': 0.33, 'neutral': 0.34, 'negative': 0.33}
        
        total = len(sentiments)
        return {
            'positive': sentiments.count('positive') / total,
            'neutral': sentiments.count('neutral') / total,
            'negative': sentiments.count('negative') / total
        }
    
    def _identify_improvement_areas(self, average_ratings: Dict[str, float], 
                                  feedback_entries: List[FeedbackEntry]) -> List[str]:
        """Identify areas needing improvement"""
        improvement_areas = []
        
        # Low-rated areas
        for feedback_type, rating in average_ratings.items():
            if rating < 3.0:  # Below average on 1-5 scale
                improvement_areas.append(f"Low satisfaction with {feedback_type.replace('_', ' ')}")
        
        # Analyze text feedback for common complaints
        complaint_keywords = {
            'facilitation': ['interrupt', 'unhelpful', 'annoying', 'wrong'],
            'participation': ['unbalanced', 'dominated', 'quiet', 'ignored'],
            'technical': ['slow', 'lag', 'error', 'broken', 'crash'],
            'accuracy': ['incorrect', 'wrong', 'mistake', 'inaccurate']
        }
        
        complaint_counts = defaultdict(int)
        for entry in feedback_entries:
            if entry.text_feedback:
                text = entry.text_feedback.lower()
                for category, keywords in complaint_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        complaint_counts[category] += 1
        
        # Add frequent complaints to improvement areas
        for category, count in complaint_counts.items():
            if count >= 2:  # Multiple mentions
                improvement_areas.append(f"Multiple concerns about {category}")
        
        return improvement_areas[:5]  # Top 5 improvement areas
    
    def _identify_strengths(self, average_ratings: Dict[str, float], 
                          feedback_entries: List[FeedbackEntry]) -> List[str]:
        """Identify system strengths"""
        strengths = []
        
        # High-rated areas
        for feedback_type, rating in average_ratings.items():
            if rating >= 4.0:  # High satisfaction
                strengths.append(f"Excellent {feedback_type.replace('_', ' ')}")
        
        # Analyze text feedback for positive mentions
        positive_keywords = {
            'helpful': ['helpful', 'useful', 'great', 'excellent', 'amazing'],
            'accurate': ['accurate', 'correct', 'precise', 'right'],
            'smooth': ['smooth', 'seamless', 'easy', 'intuitive'],
            'engaging': ['engaging', 'interactive', 'collaborative']
        }
        
        positive_counts = defaultdict(int)
        for entry in feedback_entries:
            if entry.text_feedback:
                text = entry.text_feedback.lower()
                for category, keywords in positive_keywords.items():
                    if any(keyword in text for keyword in keywords):
                        positive_counts[category] += 1
        
        # Add frequent positive mentions to strengths
        for category, count in positive_counts.items():
            if count >= 2:
                strengths.append(f"Users appreciate {category} experience")
        
        return strengths[:5]  # Top 5 strengths
    
    def _calculate_participant_satisfaction(self, feedback_entries: List[FeedbackEntry]) -> float:
        """Calculate overall participant satisfaction"""
        satisfaction_ratings = []
        
        for entry in feedback_entries:
            if entry.feedback_type == FeedbackType.USER_SATISFACTION and entry.rating:
                satisfaction_ratings.append(entry.rating)
        
        if not satisfaction_ratings:
            # Estimate from other ratings
            all_ratings = [entry.rating for entry in feedback_entries if entry.rating]
            return np.mean(all_ratings) if all_ratings else 3.0
        
        return np.mean(satisfaction_ratings)
    
    def _calculate_ai_effectiveness(self, feedback_entries: List[FeedbackEntry]) -> float:
        """Calculate AI system effectiveness score"""
        ai_ratings = []
        
        ai_related_types = [
            FeedbackType.FACILITATION_QUALITY,
            FeedbackType.AI_ACCURACY,
            FeedbackType.TOPIC_RELEVANCE
        ]
        
        for entry in feedback_entries:
            if entry.feedback_type in ai_related_types and entry.rating:
                ai_ratings.append(entry.rating)
        
        return np.mean(ai_ratings) if ai_ratings else 3.0
    
    def _generate_recommendations(self, average_ratings: Dict[str, float], 
                                improvement_areas: List[str], 
                                feedback_entries: List[FeedbackEntry]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Recommendations based on low ratings
        if 'facilitation_quality' in average_ratings and average_ratings['facilitation_quality'] < 3.5:
            recommendations.append("Consider adjusting AI facilitation frequency and timing")
        
        if 'participation_balance' in average_ratings and average_ratings['participation_balance'] < 3.5:
            recommendations.append("Implement more proactive participation balancing strategies")
        
        if 'technical_performance' in average_ratings and average_ratings['technical_performance'] < 3.5:
            recommendations.append("Optimize system performance and reduce latency")
        
        # Recommendations based on improvement areas
        for area in improvement_areas:
            if 'technical' in area.lower():
                recommendations.append("Conduct technical performance audit and optimization")
            elif 'participation' in area.lower():
                recommendations.append("Enhance participation detection and balancing algorithms")
            elif 'facilitation' in area.lower():
                recommendations.append("Refine AI facilitation prompts and timing")
        
        # General recommendations
        if len(feedback_entries) < 5:
            recommendations.append("Encourage more participant feedback to improve insights")
        
        return recommendations[:7]  # Top 7 recommendations
    
    def _analyze_trends(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, Any]:
        """Analyze feedback trends over time"""
        # Simplified trend analysis
        recent_entries = [
            entry for entry in feedback_entries 
            if entry.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            'recent_feedback_count': len(recent_entries),
            'feedback_velocity': len(recent_entries) / max(1, len(feedback_entries)),
            'recent_average_rating': np.mean([
                entry.rating for entry in recent_entries if entry.rating
            ]) if recent_entries else None
        }
    
    def _empty_analytics(self, session_id: str) -> FeedbackAnalytics:
        """Return empty analytics when no feedback is available"""
        return FeedbackAnalytics(
            session_id=session_id,
            total_feedback_count=0,
            average_ratings={},
            sentiment_distribution={'positive': 0.33, 'neutral': 0.34, 'negative': 0.33},
            improvement_areas=["No feedback available for analysis"],
            strengths=[],
            participant_satisfaction=3.0,
            ai_effectiveness_score=3.0,
            recommendations=["Encourage participants to provide feedback"],
            trend_analysis={},
            generated_at=datetime.now()
        )

class ComprehensiveFeedbackSystem:
    """Main feedback system orchestrating all feedback collection and analysis"""
    
    def __init__(self):
        self.feedback_storage = defaultdict(list)  # In production, use proper database
        self.implicit_collector = ImplicitFeedbackCollector()
        self.analyzer = FeedbackAnalyzer()
        self.feedback_hooks = []  # Callbacks for real-time feedback processing
    
    async def collect_explicit_feedback(self, session_id: str, user_id: str,
                                      feedback_type: FeedbackType, rating: float,
                                      text_feedback: Optional[str] = None,
                                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Collect explicit feedback from participants"""
        feedback_entry = FeedbackEntry(
            feedback_id=f"explicit_{user_id}_{session_id}_{datetime.now().timestamp()}",
            session_id=session_id,
            user_id=user_id,
            feedback_type=feedback_type,
            source=FeedbackSource.PARTICIPANT_EXPLICIT,
            rating=rating,
            text_feedback=text_feedback,
            metadata=metadata or {},
            timestamp=datetime.now(),
            context={}
        )
        
        self.feedback_storage[session_id].append(feedback_entry)
        
        # Trigger real-time processing
        await self._process_feedback_hooks(feedback_entry)
        
        logger.info(f"Collected explicit feedback for session {session_id} from user {user_id}")
        return feedback_entry.feedback_id
    
    def track_implicit_feedback(self, user_id: str, session_id: str,
                              action: str, context: Dict[str, Any]) -> None:
        """Track implicit feedback signals"""
        self.implicit_collector.track_user_engagement(user_id, session_id, action, context)
    
    async def generate_session_analytics(self, session_id: str) -> FeedbackAnalytics:
        """Generate comprehensive analytics for a session"""
        # Collect all feedback
        explicit_feedback = self.feedback_storage.get(session_id, [])
        
        # Generate implicit feedback
        implicit_feedback = []
        for user_id in self.implicit_collector.engagement_metrics:
            implicit_feedback.extend(
                self.implicit_collector.generate_implicit_feedback(user_id, session_id)
            )
        
        # Combine all feedback
        all_feedback = explicit_feedback + implicit_feedback
        
        # Analyze and return
        analytics = self.analyzer.analyze_session_feedback(session_id, all_feedback)
        
        logger.info(f"Generated analytics for session {session_id}: "
                   f"{analytics.total_feedback_count} feedback entries, "
                   f"{analytics.participant_satisfaction:.2f} satisfaction score")
        
        return analytics
    
    def add_feedback_hook(self, callback) -> None:
        """Add callback for real-time feedback processing"""
        self.feedback_hooks.append(callback)
    
    async def _process_feedback_hooks(self, feedback_entry: FeedbackEntry) -> None:
        """Process real-time feedback hooks"""
        for hook in self.feedback_hooks:
            try:
                await hook(feedback_entry)
            except Exception as e:
                logger.error(f"Error in feedback hook: {e}")
    
    def get_session_feedback_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a quick summary of session feedback"""
        feedback_entries = self.feedback_storage.get(session_id, [])
        
        if not feedback_entries:
            return {
                'total_feedback': 0,
                'average_rating': None,
                'latest_feedback': None
            }
        
        ratings = [entry.rating for entry in feedback_entries if entry.rating]
        
        return {
            'total_feedback': len(feedback_entries),
            'average_rating': np.mean(ratings) if ratings else None,
            'latest_feedback': feedback_entries[-1].to_dict() if feedback_entries else None,
            'feedback_types': list(set(entry.feedback_type.value for entry in feedback_entries))
        }

# Export main classes
__all__ = [
    'ComprehensiveFeedbackSystem',
    'FeedbackType',
    'FeedbackSource', 
    'FeedbackEntry',
    'FeedbackAnalytics',
    'ImplicitFeedbackCollector',
    'FeedbackAnalyzer'
]