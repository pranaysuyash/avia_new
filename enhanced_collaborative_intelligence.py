#!/usr/bin/env python3
"""
Enhanced Collaborative Intelligence System
Integrates discussion facilitation, MoM creation, action items, and comprehensive feedback
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json

# Import core systems
from collaborative_discussion_facilitator import (
    CollaborativeDiscussionFacilitator, DiscussionContext, FacilitationMode
)
from collaborative_feedback_system import (
    ComprehensiveFeedbackSystem, FeedbackType, FeedbackSource
)

# Import meeting intelligence components
try:
    from action_item_extraction import ActionItemExtractor
    from hybrid_summarization_system import HybridSummarizationSystem
    MEETING_INTELLIGENCE_AVAILABLE = True
except ImportError:
    MEETING_INTELLIGENCE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Meeting intelligence components not available")

logger = logging.getLogger(__name__)

@dataclass
class MeetingOutcome:
    """Comprehensive meeting outcome with all generated artifacts"""
    session_id: str
    summary: str
    key_decisions: List[str]
    action_items: List[Dict[str, Any]]
    discussion_highlights: List[str]
    participant_insights: Dict[str, Any]
    facilitation_effectiveness: float
    next_steps: List[str]
    meeting_artifacts: Dict[str, Any]
    feedback_analytics: Dict[str, Any]
    generated_at: datetime

class EnhancedCollaborativeIntelligence:
    """
    Enhanced collaborative intelligence system that combines:
    - AI-powered discussion facilitation
    - Real-time meeting intelligence (MoM, action items)
    - Comprehensive feedback collection and analysis
    - Advanced spaCy models for better NLP
    """
    
    def __init__(self, collaborative_engine):
        self.collaborative_engine = collaborative_engine
        self.discussion_facilitator = CollaborativeDiscussionFacilitator(collaborative_engine)
        self.feedback_system = ComprehensiveFeedbackSystem()
        
        # Initialize meeting intelligence components
        if MEETING_INTELLIGENCE_AVAILABLE:
            self.action_extractor = ActionItemExtractor()
            self.summarization_system = HybridSummarizationSystem()
        else:
            self.action_extractor = None
            self.summarization_system = None
        
        # Enhanced NLP setup
        self.nlp_model = None
        self._setup_enhanced_nlp()
        
        # Session tracking
        self.active_sessions = {}
        self.session_artifacts = {}
        
        # Setup feedback hooks
        self._setup_feedback_integration()
    
    def _setup_enhanced_nlp(self):
        """Setup enhanced spaCy models"""
        try:
            import spacy
            # Try to load transformer-based model first
            try:
                self.nlp_model = spacy.load("en_core_web_trf")
                logger.info("Loaded transformer-based spaCy model (en_core_web_trf)")
            except OSError:
                try:
                    self.nlp_model = spacy.load("en_core_web_lg")
                    logger.info("Loaded large spaCy model (en_core_web_lg)")
                except OSError:
                    self.nlp_model = spacy.load("en_core_web_sm")
                    logger.warning("Using small spaCy model (en_core_web_sm) - consider installing larger models")
        except ImportError:
            logger.error("spaCy not available - NLP features will be limited")
    
    def _setup_feedback_integration(self):
        """Setup feedback system integration with facilitation"""
        async def facilitation_feedback_hook(feedback_entry):
            """Process feedback to improve facilitation"""
            if feedback_entry.feedback_type == FeedbackType.FACILITATION_QUALITY:
                if feedback_entry.rating and feedback_entry.rating < 3.0:
                    # Adjust facilitation strategy for low ratings
                    await self._adjust_facilitation_strategy(
                        feedback_entry.session_id, 
                        feedback_entry.text_feedback
                    )
        
        self.feedback_system.add_feedback_hook(facilitation_feedback_hook)
    
    async def start_enhanced_session(self, session_id: str, context: DiscussionContext,
                                   enable_mom: bool = True, 
                                   enable_action_tracking: bool = True,
                                   enable_real_time_feedback: bool = True) -> Dict[str, Any]:
        """Start an enhanced collaborative session with all intelligence features"""
        
        # Start core facilitation
        facilitation_success = await self.discussion_facilitator.start_facilitated_session(
            session_id, context
        )
        
        if not facilitation_success:
            return {'success': False, 'error': 'Failed to start facilitation'}
        
        # Initialize session tracking
        self.active_sessions[session_id] = {
            'context': context,
            'start_time': datetime.now(),
            'enable_mom': enable_mom,
            'enable_action_tracking': enable_action_tracking,
            'enable_real_time_feedback': enable_real_time_feedback,
            'artifacts': {
                'transcripts': [],
                'decisions': [],
                'action_items': [],
                'key_moments': []
            }
        }
        
        logger.info(f"Started enhanced collaborative session {session_id} with features: "
                   f"MoM={enable_mom}, Actions={enable_action_tracking}, Feedback={enable_real_time_feedback}")
        
        return {
            'success': True,
            'session_id': session_id,
            'features_enabled': {
                'facilitation': True,
                'mom_creation': enable_mom,
                'action_tracking': enable_action_tracking,
                'real_time_feedback': enable_real_time_feedback,
                'enhanced_nlp': self.nlp_model is not None,
                'meeting_intelligence': MEETING_INTELLIGENCE_AVAILABLE
            },
            'started_at': datetime.now().isoformat()
        }
    
    async def process_enhanced_discussion_update(self, session_id: str, 
                                               session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process discussion update with enhanced intelligence"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session_info = self.active_sessions[session_id]
        
        # Core facilitation processing
        await self.discussion_facilitator.process_discussion_update(session_id, session_data)
        
        # Enhanced processing
        results = {
            'facilitation_processed': True,
            'artifacts_generated': {}
        }
        
        # Extract and track action items in real-time
        if session_info['enable_action_tracking'] and self.action_extractor:
            new_action_items = await self._extract_action_items(session_data)
            if new_action_items:
                session_info['artifacts']['action_items'].extend(new_action_items)
                results['artifacts_generated']['action_items'] = len(new_action_items)
        
        # Track key decisions and moments
        key_moments = await self._identify_key_moments(session_data)
        if key_moments:
            session_info['artifacts']['key_moments'].extend(key_moments)
            results['artifacts_generated']['key_moments'] = len(key_moments)
        
        # Real-time sentiment and engagement tracking
        engagement_metrics = await self._analyze_real_time_engagement(session_data)
        if engagement_metrics:
            results['engagement_metrics'] = engagement_metrics
        
        # Store transcript segments
        if 'segments' in session_data:
            session_info['artifacts']['transcripts'].extend(session_data['segments'])
        
        return results
    
    async def collect_participant_feedback(self, session_id: str, user_id: str,
                                         feedback_type: str, rating: float,
                                         text_feedback: Optional[str] = None) -> str:
        """Collect participant feedback during the session"""
        feedback_type_enum = FeedbackType(feedback_type)
        
        feedback_id = await self.feedback_system.collect_explicit_feedback(
            session_id=session_id,
            user_id=user_id,
            feedback_type=feedback_type_enum,
            rating=rating,
            text_feedback=text_feedback
        )
        
        # Track implicit feedback signal
        self.feedback_system.track_implicit_feedback(
            user_id=user_id,
            session_id=session_id,
            action='feedback_provided',
            context={'feedback_type': feedback_type, 'rating': rating}
        )
        
        return feedback_id
    
    async def generate_comprehensive_mom(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive Minutes of Meeting with all artifacts"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session_info = self.active_sessions[session_id]
        
        if not session_info['enable_mom']:
            return {'error': 'MoM generation not enabled for this session'}
        
        # Get session data
        session_data = self.collaborative_engine.get_session_state(session_id)
        
        mom_content = {
            'session_info': {
                'session_id': session_id,
                'topic': session_info['context'].topic,
                'participants': session_info['context'].participants,
                'start_time': session_info['start_time'].isoformat(),
                'duration': str(datetime.now() - session_info['start_time']),
                'facilitation_mode': session_info['context'].mode.value
            },
            'executive_summary': '',
            'key_decisions': session_info['artifacts']['decisions'],
            'action_items': session_info['artifacts']['action_items'],
            'discussion_highlights': [],
            'participant_contributions': {},
            'next_steps': [],
            'attachments': []
        }
        
        # Generate executive summary using hybrid summarization
        if self.summarization_system and session_data.get('segments'):
            full_transcript = ' '.join([seg.get('text', '') for seg in session_data['segments']])
            summary_result = await self.summarization_system.generate_hybrid_summary(
                full_transcript, 
                summary_type='executive',
                max_length=200
            )
            mom_content['executive_summary'] = summary_result.get('summary', '')
        
        # Extract discussion highlights using enhanced NLP
        if self.nlp_model and session_data.get('segments'):
            highlights = await self._extract_discussion_highlights(session_data['segments'])
            mom_content['discussion_highlights'] = highlights
        
        # Analyze participant contributions
        participant_analysis = await self._analyze_participant_contributions(session_data)
        mom_content['participant_contributions'] = participant_analysis
        
        # Generate next steps from action items
        next_steps = self._generate_next_steps(session_info['artifacts']['action_items'])
        mom_content['next_steps'] = next_steps
        
        # Store MoM
        self.session_artifacts[session_id] = mom_content
        
        logger.info(f"Generated comprehensive MoM for session {session_id}")
        return mom_content
    
    async def end_enhanced_session(self, session_id: str) -> MeetingOutcome:
        """End session and generate comprehensive meeting outcome"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # End core facilitation
        facilitation_summary = await self.discussion_facilitator.end_facilitated_session(session_id)
        
        # Generate comprehensive feedback analytics
        feedback_analytics = await self.feedback_system.generate_session_analytics(session_id)
        
        # Generate MoM if enabled
        mom_content = {}
        if self.active_sessions[session_id]['enable_mom']:
            mom_content = await self.generate_comprehensive_mom(session_id)
        
        # Create comprehensive meeting outcome
        session_info = self.active_sessions[session_id]
        
        outcome = MeetingOutcome(
            session_id=session_id,
            summary=mom_content.get('executive_summary', ''),
            key_decisions=session_info['artifacts']['decisions'],
            action_items=session_info['artifacts']['action_items'],
            discussion_highlights=mom_content.get('discussion_highlights', []),
            participant_insights=mom_content.get('participant_contributions', {}),
            facilitation_effectiveness=feedback_analytics.ai_effectiveness_score,
            next_steps=mom_content.get('next_steps', []),
            meeting_artifacts={
                'mom': mom_content,
                'facilitation_summary': facilitation_summary,
                'key_moments': session_info['artifacts']['key_moments']
            },
            feedback_analytics=asdict(feedback_analytics),
            generated_at=datetime.now()
        )
        
        # Cleanup
        del self.active_sessions[session_id]
        
        logger.info(f"Ended enhanced session {session_id} with comprehensive outcome generation")
        return outcome
    
    async def _extract_action_items(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract action items from recent discussion"""
        if not self.action_extractor or not session_data.get('segments'):
            return []
        
        # Get recent segments (last 5 minutes worth)
        recent_segments = session_data['segments'][-10:]  # Simplified
        recent_text = ' '.join([seg.get('text', '') for seg in recent_segments])
        
        try:
            action_items = await self.action_extractor.extract_action_items(recent_text)
            return action_items
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []
    
    async def _identify_key_moments(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify key moments in the discussion"""
        key_moments = []
        
        if not session_data.get('segments'):
            return key_moments
        
        # Look for decision-making language
        decision_keywords = ['decide', 'agreed', 'consensus', 'vote', 'choose', 'final']
        
        for segment in session_data['segments'][-5:]:  # Check recent segments
            text = segment.get('text', '').lower()
            if any(keyword in text for keyword in decision_keywords):
                key_moments.append({
                    'type': 'decision',
                    'text': segment.get('text', ''),
                    'speaker': segment.get('user_id', 'unknown'),
                    'timestamp': segment.get('timestamp', datetime.now().isoformat())
                })
        
        return key_moments
    
    async def _analyze_real_time_engagement(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze real-time engagement metrics"""
        if not session_data.get('segments'):
            return {}
        
        recent_segments = session_data['segments'][-10:]
        
        # Calculate speaking distribution
        speaker_counts = {}
        for segment in recent_segments:
            speaker = segment.get('user_id', 'unknown')
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        # Calculate engagement score
        total_segments = len(recent_segments)
        unique_speakers = len(speaker_counts)
        
        engagement_score = min(1.0, unique_speakers / max(1, total_segments / 2))
        
        return {
            'engagement_score': engagement_score,
            'active_speakers': unique_speakers,
            'total_contributions': total_segments,
            'speaker_distribution': speaker_counts
        }
    
    async def _extract_discussion_highlights(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Extract key discussion highlights using enhanced NLP"""
        if not self.nlp_model:
            return []
        
        highlights = []
        
        # Combine segments into larger chunks for analysis
        text_chunks = []
        current_chunk = ""
        
        for segment in segments:
            current_chunk += segment.get('text', '') + " "
            if len(current_chunk) > 500:  # Process in chunks
                text_chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if current_chunk:
            text_chunks.append(current_chunk.strip())
        
        # Extract highlights from each chunk
        for chunk in text_chunks:
            doc = self.nlp_model(chunk)
            
            # Extract sentences with high importance (simplified)
            important_sentences = []
            for sent in doc.sents:
                # Look for sentences with key entities or important verbs
                has_entities = len(sent.ents) > 0
                has_important_verbs = any(token.pos_ == 'VERB' and token.lemma_ in 
                                        ['decide', 'agree', 'conclude', 'determine'] 
                                        for token in sent)
                
                if has_entities or has_important_verbs:
                    important_sentences.append(sent.text.strip())
            
            highlights.extend(important_sentences[:2])  # Top 2 per chunk
        
        return highlights[:10]  # Top 10 overall
    
    async def _analyze_participant_contributions(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual participant contributions"""
        if not session_data.get('segments'):
            return {}
        
        participant_stats = {}
        
        for segment in session_data['segments']:
            user_id = segment.get('user_id', 'unknown')
            text = segment.get('text', '')
            
            if user_id not in participant_stats:
                participant_stats[user_id] = {
                    'total_contributions': 0,
                    'total_words': 0,
                    'key_contributions': [],
                    'questions_asked': 0,
                    'decisions_influenced': 0
                }
            
            stats = participant_stats[user_id]
            stats['total_contributions'] += 1
            stats['total_words'] += len(text.split())
            
            # Count questions
            if '?' in text:
                stats['questions_asked'] += 1
            
            # Identify key contributions (simplified)
            if any(keyword in text.lower() for keyword in ['important', 'key', 'critical', 'suggest']):
                stats['key_contributions'].append(text[:100] + '...' if len(text) > 100 else text)
        
        return participant_stats
    
    def _generate_next_steps(self, action_items: List[Dict[str, Any]]) -> List[str]:
        """Generate next steps from action items"""
        next_steps = []
        
        for item in action_items:
            if isinstance(item, dict):
                task = item.get('task', '')
                assignee = item.get('assignee', 'team')
                due_date = item.get('due_date', 'TBD')
                
                next_step = f"{assignee} to {task}"
                if due_date != 'TBD':
                    next_step += f" by {due_date}"
                
                next_steps.append(next_step)
        
        return next_steps
    
    async def _adjust_facilitation_strategy(self, session_id: str, feedback_text: Optional[str]):
        """Adjust facilitation strategy based on feedback"""
        # This would implement dynamic facilitation adjustment
        # For now, just log the feedback for analysis
        logger.info(f"Received facilitation feedback for session {session_id}: {feedback_text}")
        
        # In a full implementation, this would:
        # 1. Analyze the feedback text
        # 2. Identify specific issues (too frequent, not helpful, etc.)
        # 3. Adjust facilitation parameters accordingly
        # 4. Update the facilitation engine's behavior
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive status of an active session"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session_info = self.active_sessions[session_id]
        facilitation_analytics = self.discussion_facilitator.get_session_analytics(session_id)
        feedback_summary = self.feedback_system.get_session_feedback_summary(session_id)
        
        return {
            'session_id': session_id,
            'status': 'active',
            'duration': str(datetime.now() - session_info['start_time']),
            'features_enabled': {
                'mom_creation': session_info['enable_mom'],
                'action_tracking': session_info['enable_action_tracking'],
                'real_time_feedback': session_info['enable_real_time_feedback']
            },
            'artifacts_count': {
                'action_items': len(session_info['artifacts']['action_items']),
                'decisions': len(session_info['artifacts']['decisions']),
                'key_moments': len(session_info['artifacts']['key_moments']),
                'transcript_segments': len(session_info['artifacts']['transcripts'])
            },
            'facilitation_analytics': facilitation_analytics,
            'feedback_summary': feedback_summary
        }

# Export main class
__all__ = ['EnhancedCollaborativeIntelligence', 'MeetingOutcome']