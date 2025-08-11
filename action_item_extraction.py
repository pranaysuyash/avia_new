"""
Action Item Extraction System

This module implements intelligent action item extraction from meeting transcripts,
creating structured outputs that transform conversations into actionable outcomes.
This is our key differentiator for the Meeting Intelligence ICP.

Requirements addressed:
- Meeting Intelligence workflow: Ingest → Review → Extract → Export
- Structured outputs as first-class artifacts
- Measurable outcomes for user value
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import openai
from openai import OpenAI
import spacy
from textblob import TextBlob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionItemPriority(Enum):
    """Priority levels for action items"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ActionItemStatus(Enum):
    """Status of action items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class ActionItem:
    """Represents an extracted action item"""
    id: str
    text: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: ActionItemPriority = ActionItemPriority.MEDIUM
    status: ActionItemStatus = ActionItemStatus.PENDING
    context: str = ""
    confidence_score: float = 0.0
    source_segment: str = ""
    timestamp: Optional[float] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['due_date'] = self.due_date.isoformat() if self.due_date else None
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

@dataclass
class MeetingInsights:
    """Comprehensive meeting analysis results"""
    action_items: List[ActionItem]
    key_decisions: List[str]
    topics_discussed: List[str]
    participants: List[str]
    meeting_summary: str
    next_meeting_date: Optional[datetime] = None
    follow_up_required: List[str] = None
    
    def __post_init__(self):
        if self.follow_up_required is None:
            self.follow_up_required = []c
lass ActionItemExtractor:
    """Advanced action item extraction using multiple AI approaches"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the action item extractor"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not provided, using local NLP only")
        
        # Initialize spaCy for local processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, some features may be limited")
            self.nlp = None
        
        # Action item patterns for rule-based extraction
        self.action_patterns = [
            r"(?:will|should|need to|must|has to|going to)\s+(.+?)(?:\.|$)",
            r"(?:action item|todo|task):\s*(.+?)(?:\.|$)",
            r"(?:assigned to|responsible for)\s+(\w+):\s*(.+?)(?:\.|$)",
            r"(?:by|due|deadline)\s+(\w+\s+\d+|\d+/\d+|\d+-\d+-\d+):\s*(.+?)(?:\.|$)",
            r"(?:follow up|follow-up)\s+(?:with|on)\s+(.+?)(?:\.|$)",
            r"(?:next steps?|action steps?):\s*(.+?)(?:\.|$)"
        ]
        
        # Decision patterns
        self.decision_patterns = [
            r"(?:decided|agreed|concluded|determined)\s+(?:that|to)\s+(.+?)(?:\.|$)",
            r"(?:decision|resolution):\s*(.+?)(?:\.|$)",
            r"(?:we will|the team will|it was decided)\s+(.+?)(?:\.|$)"
        ]
        
        # Date patterns for deadline extraction
        self.date_patterns = [
            r"(?:by|due|deadline|before)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(?:by|due|deadline|before)\s+(\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
            r"(?:by|due|deadline|before)\s+(\d{1,2}-\d{1,2}(?:-\d{2,4})?)",
            r"(?:by|due|deadline|before)\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
            r"(?:next week|this week|end of week|eow)",
            r"(?:next month|end of month|eom)"
        ]
    
    async def extract_action_items(
        self, 
        transcript: str, 
        participants: List[str] = None,
        use_ai: bool = True
    ) -> MeetingInsights:
        """
        Extract action items and meeting insights from transcript
        
        Args:
            transcript: Meeting transcript text
            participants: List of participant names
            use_ai: Whether to use AI-powered extraction
            
        Returns:
            MeetingInsights with extracted action items and analysis
        """
        try:
            logger.info("Starting action item extraction")
            
            # Clean and preprocess transcript
            cleaned_transcript = self._preprocess_transcript(transcript)
            
            # Extract using multiple approaches
            if use_ai and self.openai_client:
                ai_results = await self._extract_with_ai(cleaned_transcript, participants)
            else:
                ai_results = None
            
            rule_based_results = self._extract_with_rules(cleaned_transcript, participants)
            
            # Combine and deduplicate results
            combined_results = self._combine_extraction_results(ai_results, rule_based_results)
            
            # Enhance with additional analysis
            enhanced_results = self._enhance_meeting_insights(combined_results, cleaned_transcript)
            
            logger.info(f"Extracted {len(enhanced_results.action_items)} action items")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error extracting action items: {str(e)}")
            # Return basic results on error
            return MeetingInsights(
                action_items=[],
                key_decisions=[],
                topics_discussed=[],
                participants=participants or [],
                meeting_summary="Error occurred during extraction"
            )
    
    def _preprocess_transcript(self, transcript: str) -> str:
        """Clean and preprocess transcript text"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', transcript.strip())
        
        # Remove speaker labels if present (e.g., "John: " or "Speaker 1: ")
        cleaned = re.sub(r'^[A-Za-z\s\d]+:\s*', '', cleaned, flags=re.MULTILINE)
        
        # Fix common transcription issues
        cleaned = cleaned.replace(' um ', ' ').replace(' uh ', ' ')
        cleaned = re.sub(r'\b(yeah|yes|okay|ok|right|sure)\b\s*', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    async def _extract_with_ai(
        self, 
        transcript: str, 
        participants: List[str] = None
    ) -> Optional[MeetingInsights]:
        """Extract action items using OpenAI GPT"""
        try:
            participant_context = f"Participants: {', '.join(participants)}" if participants else ""
            
            prompt = f"""
            Analyze this meeting transcript and extract structured information:

            {participant_context}

            Transcript:
            {transcript}

            Please extract and return a JSON object with:
            1. action_items: Array of objects with:
               - text: Clear, actionable description
               - assignee: Person responsible (if mentioned)
               - due_date: Deadline if mentioned (ISO format)
               - priority: low/medium/high/urgent
               - confidence_score: 0.0-1.0 confidence in extraction
               - context: Surrounding context from transcript
               - tags: Relevant tags/categories

            2. key_decisions: Array of important decisions made
            3. topics_discussed: Array of main topics covered
            4. meeting_summary: Brief 2-3 sentence summary
            5. next_meeting_date: If mentioned (ISO format)
            6. follow_up_required: Array of follow-up items needed

            Focus on clear, actionable items. Be conservative - only extract items you're confident about.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert meeting analyst. Extract actionable items and insights from meeting transcripts. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse AI response
            ai_data = json.loads(response.choices[0].message.content)
            
            # Convert to ActionItem objects
            action_items = []
            for item_data in ai_data.get('action_items', []):
                action_item = ActionItem(
                    id=f"ai_{hash(item_data['text'])}_{int(datetime.now().timestamp())}",
                    text=item_data['text'],
                    assignee=item_data.get('assignee'),
                    due_date=datetime.fromisoformat(item_data['due_date']) if item_data.get('due_date') else None,
                    priority=ActionItemPriority(item_data.get('priority', 'medium')),
                    confidence_score=item_data.get('confidence_score', 0.8),
                    context=item_data.get('context', ''),
                    tags=item_data.get('tags', [])
                )
                action_items.append(action_item)
            
            return MeetingInsights(
                action_items=action_items,
                key_decisions=ai_data.get('key_decisions', []),
                topics_discussed=ai_data.get('topics_discussed', []),
                participants=participants or [],
                meeting_summary=ai_data.get('meeting_summary', ''),
                next_meeting_date=datetime.fromisoformat(ai_data['next_meeting_date']) if ai_data.get('next_meeting_date') else None,
                follow_up_required=ai_data.get('follow_up_required', [])
            )
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            return None
    
    def _extract_with_rules(
        self, 
        transcript: str, 
        participants: List[str] = None
    ) -> MeetingInsights:
        """Extract action items using rule-based patterns"""
        action_items = []
        key_decisions = []
        topics_discussed = []
        
        # Split transcript into sentences
        sentences = self._split_into_sentences(transcript)
        
        for i, sentence in enumerate(sentences):
            # Extract action items
            for pattern in self.action_patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    action_text = match.group(1).strip()
                    if len(action_text) > 10:  # Filter out very short items
                        
                        # Try to extract assignee
                        assignee = self._extract_assignee(sentence, participants)
                        
                        # Try to extract due date
                        due_date = self._extract_due_date(sentence)
                        
                        # Determine priority based on keywords
                        priority = self._determine_priority(sentence)
                        
                        action_item = ActionItem(
                            id=f"rule_{hash(action_text)}_{i}",
                            text=action_text,
                            assignee=assignee,
                            due_date=due_date,
                            priority=priority,
                            confidence_score=0.6,  # Lower confidence for rule-based
                            context=sentence,
                            source_segment=sentence
                        )
                        action_items.append(action_item)
            
            # Extract decisions
            for pattern in self.decision_patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 10:
                        key_decisions.append(decision_text)
        
        # Extract topics using NLP if available
        if self.nlp:
            topics_discussed = self._extract_topics_nlp(transcript)
        else:
            topics_discussed = self._extract_topics_simple(transcript)
        
        # Generate simple summary
        meeting_summary = self._generate_simple_summary(transcript, len(action_items), len(key_decisions))
        
        return MeetingInsights(
            action_items=action_items,
            key_decisions=key_decisions,
            topics_discussed=topics_discussed,
            participants=participants or [],
            meeting_summary=meeting_summary
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]
    
    def _extract_assignee(self, sentence: str, participants: List[str] = None) -> Optional[str]:
        """Extract assignee from sentence"""
        if not participants:
            return None
        
        sentence_lower = sentence.lower()
        
        # Look for assignment patterns
        for participant in participants:
            participant_lower = participant.lower()
            if (f"{participant_lower} will" in sentence_lower or 
                f"{participant_lower} should" in sentence_lower or
                f"assigned to {participant_lower}" in sentence_lower or
                f"{participant_lower} is responsible" in sentence_lower):
                return participant
        
        return None
    
    def _extract_due_date(self, sentence: str) -> Optional[datetime]:
        """Extract due date from sentence"""
        sentence_lower = sentence.lower()
        
        # Simple date extraction
        if "next week" in sentence_lower:
            return datetime.now() + timedelta(weeks=1)
        elif "this week" in sentence_lower or "end of week" in sentence_lower:
            return datetime.now() + timedelta(days=7 - datetime.now().weekday())
        elif "next month" in sentence_lower:
            return datetime.now() + timedelta(days=30)
        elif "tomorrow" in sentence_lower:
            return datetime.now() + timedelta(days=1)
        
        # Look for specific date patterns
        for pattern in self.date_patterns:
            match = re.search(pattern, sentence_lower)
            if match:
                # Simple heuristic - return next week for now
                return datetime.now() + timedelta(weeks=1)
        
        return None
    
    def _determine_priority(self, sentence: str) -> ActionItemPriority:
        """Determine priority based on keywords"""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['urgent', 'asap', 'immediately', 'critical']):
            return ActionItemPriority.URGENT
        elif any(word in sentence_lower for word in ['important', 'priority', 'must']):
            return ActionItemPriority.HIGH
        elif any(word in sentence_lower for word in ['should', 'need to']):
            return ActionItemPriority.MEDIUM
        else:
            return ActionItemPriority.LOW
    
    def _extract_topics_nlp(self, transcript: str) -> List[str]:
        """Extract topics using spaCy NLP"""
        try:
            doc = self.nlp(transcript)
            
            # Extract noun phrases as topics
            topics = []
            for chunk in doc.noun_chunks:
                if len(chunk.text) > 3 and chunk.text.lower() not in ['we', 'they', 'it', 'this', 'that']:
                    topics.append(chunk.text.strip())
            
            # Get most common topics
            from collections import Counter
            topic_counts = Counter(topics)
            return [topic for topic, count in topic_counts.most_common(10)]
            
        except Exception as e:
            logger.error(f"NLP topic extraction failed: {str(e)}")
            return self._extract_topics_simple(transcript)
    
    def _extract_topics_simple(self, transcript: str) -> List[str]:
        """Simple topic extraction using keywords"""
        # Common business/meeting topics
        topic_keywords = {
            'Budget': ['budget', 'cost', 'expense', 'financial', 'money'],
            'Timeline': ['timeline', 'schedule', 'deadline', 'date', 'time'],
            'Team': ['team', 'staff', 'employee', 'member', 'person'],
            'Project': ['project', 'initiative', 'program', 'work'],
            'Strategy': ['strategy', 'plan', 'approach', 'direction'],
            'Marketing': ['marketing', 'campaign', 'promotion', 'advertising'],
            'Sales': ['sales', 'revenue', 'customer', 'client'],
            'Product': ['product', 'feature', 'development', 'launch'],
            'Operations': ['operations', 'process', 'workflow', 'system']
        }
        
        transcript_lower = transcript.lower()
        found_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in transcript_lower for keyword in keywords):
                found_topics.append(topic)
        
        return found_topics
    
    def _generate_simple_summary(self, transcript: str, action_count: int, decision_count: int) -> str:
        """Generate a simple meeting summary"""
        word_count = len(transcript.split())
        
        summary = f"Meeting discussion covered {word_count} words of conversation. "
        
        if action_count > 0:
            summary += f"Identified {action_count} action items for follow-up. "
        
        if decision_count > 0:
            summary += f"Made {decision_count} key decisions. "
        
        if action_count == 0 and decision_count == 0:
            summary += "This appears to be an informational discussion with no specific action items identified."
        
        return summary
    
    def _combine_extraction_results(
        self, 
        ai_results: Optional[MeetingInsights], 
        rule_results: MeetingInsights
    ) -> MeetingInsights:
        """Combine AI and rule-based extraction results"""
        if not ai_results:
            return rule_results
        
        # Combine action items, preferring AI results for duplicates
        combined_action_items = ai_results.action_items.copy()
        
        # Add rule-based items that don't duplicate AI items
        for rule_item in rule_results.action_items:
            is_duplicate = False
            for ai_item in ai_results.action_items:
                if self._are_similar_action_items(rule_item.text, ai_item.text):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                combined_action_items.append(rule_item)
        
        # Combine other insights
        combined_decisions = list(set(ai_results.key_decisions + rule_results.key_decisions))
        combined_topics = list(set(ai_results.topics_discussed + rule_results.topics_discussed))
        
        return MeetingInsights(
            action_items=combined_action_items,
            key_decisions=combined_decisions,
            topics_discussed=combined_topics,
            participants=ai_results.participants or rule_results.participants,
            meeting_summary=ai_results.meeting_summary or rule_results.meeting_summary,
            next_meeting_date=ai_results.next_meeting_date,
            follow_up_required=ai_results.follow_up_required
        )
    
    def _are_similar_action_items(self, text1: str, text2: str, threshold: float = 0.7) -> bool:
        """Check if two action items are similar enough to be considered duplicates"""
        # Simple similarity check using word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def _enhance_meeting_insights(
        self, 
        insights: MeetingInsights, 
        transcript: str
    ) -> MeetingInsights:
        """Enhance meeting insights with additional analysis"""
        # Add tags to action items based on content
        for action_item in insights.action_items:
            action_item.tags = self._generate_action_item_tags(action_item.text)
        
        # Sort action items by priority and confidence
        insights.action_items.sort(
            key=lambda x: (x.priority.value, -x.confidence_score)
        )
        
        return insights
    
    def _generate_action_item_tags(self, action_text: str) -> List[str]:
        """Generate relevant tags for an action item"""
        tags = []
        text_lower = action_text.lower()
        
        tag_keywords = {
            'research': ['research', 'investigate', 'analyze', 'study'],
            'communication': ['email', 'call', 'contact', 'reach out', 'notify'],
            'documentation': ['document', 'write', 'create', 'draft', 'prepare'],
            'review': ['review', 'check', 'verify', 'validate', 'approve'],
            'meeting': ['schedule', 'meet', 'discuss', 'present'],
            'development': ['develop', 'build', 'implement', 'code', 'create'],
            'testing': ['test', 'validate', 'verify', 'qa'],
            'deployment': ['deploy', 'release', 'launch', 'publish']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags[:3]  # Limit to 3 tags

# Utility functions for integration
def extract_action_items_from_transcript(
    transcript: str, 
    participants: List[str] = None,
    openai_api_key: str = None
) -> MeetingInsights:
    """
    Convenience function to extract action items from a transcript
    
    Args:
        transcript: Meeting transcript text
        participants: List of participant names
        openai_api_key: OpenAI API key for enhanced extraction
        
    Returns:
        MeetingInsights with extracted action items
    """
    extractor = ActionItemExtractor(openai_api_key)
    return asyncio.run(extractor.extract_action_items(transcript, participants))

def format_action_items_for_export(insights: MeetingInsights) -> Dict[str, Any]:
    """
    Format meeting insights for export to various formats
    
    Args:
        insights: MeetingInsights object
        
    Returns:
        Dictionary formatted for export
    """
    return {
        'meeting_summary': insights.meeting_summary,
        'action_items': [item.to_dict() for item in insights.action_items],
        'key_decisions': insights.key_decisions,
        'topics_discussed': insights.topics_discussed,
        'participants': insights.participants,
        'next_meeting_date': insights.next_meeting_date.isoformat() if insights.next_meeting_date else None,
        'follow_up_required': insights.follow_up_required,
        'extraction_timestamp': datetime.now().isoformat(),
        'total_action_items': len(insights.action_items),
        'high_priority_items': len([item for item in insights.action_items if item.priority in [ActionItemPriority.HIGH, ActionItemPriority.URGENT]])
    }

# Example usage
async def example_usage():
    """Example usage of the action item extraction system"""
    sample_transcript = """
    John: Thanks everyone for joining today's project kickoff meeting. Let's start by reviewing our timeline.
    
    Sarah: I think we need to finalize the requirements by next Friday. John, can you send out the requirements document to the team by Wednesday?
    
    Mike: That sounds good. I'll review the technical specifications and get back to you with feedback by Thursday.
    
    John: Perfect. Sarah, please schedule a follow-up meeting with the stakeholders for next week to discuss the budget.
    
    Sarah: Will do. Also, we decided that Mike will be responsible for the database design, and I'll handle the frontend mockups.
    
    Mike: I'll need to research the best database solution for our needs. This is urgent since it affects the entire architecture.
    
    John: Great. Let's also make sure to document all our decisions in the project wiki. Sarah, can you take care of that?
    
    Sarah: Absolutely. I'll create the documentation by end of week.
    """
    
    participants = ["John", "Sarah", "Mike"]
    
    extractor = ActionItemExtractor()
    insights = await extractor.extract_action_items(sample_transcript, participants)
    
    print("Extracted Action Items:")
    for item in insights.action_items:
        print(f"- {item.text} (Assignee: {item.assignee}, Priority: {item.priority.value})")
    
    print(f"\nKey Decisions:")
    for decision in insights.key_decisions:
        print(f"- {decision}")
    
    print(f"\nMeeting Summary: {insights.meeting_summary}")

if __name__ == "__main__":
    asyncio.run(example_usage())