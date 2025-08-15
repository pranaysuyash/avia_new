#!/usr/bin/env python3
"""
Meeting Element Identification Engine
Automatically identifies and extracts meeting elements from transcribed content
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingElementType(Enum):
    """Types of meeting elements that can be identified"""
    AGENDA_ITEM = "agenda_item"
    DECISION = "decision"
    ACTION_ITEM = "action_item"
    DISCUSSION_POINT = "discussion_point"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    ATTENDEE_INTRODUCTION = "attendee_introduction"
    MEETING_OPENING = "meeting_opening"
    MEETING_CLOSING = "meeting_closing"
    VOTE = "vote"
    PRESENTATION = "presentation"
    OBJECTION = "objection"
    AGREEMENT = "agreement"

class ConfidenceLevel(Enum):
    """Confidence levels for element identification"""
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"           # 75-89%
    MEDIUM = "medium"       # 50-74%
    LOW = "low"            # 25-49%
    VERY_LOW = "very_low"   # 0-24%

@dataclass
class MeetingElement:
    """Represents an identified meeting element"""
    element_type: MeetingElementType
    content: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    speaker: Optional[str] = None
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    context: Dict[str, Any] = field(default_factory=dict)
    related_elements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set confidence level based on confidence score"""
        if self.confidence >= 0.9:
            self.confidence_level = ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.75:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            self.confidence_level = ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.25:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.VERY_LOW

@dataclass
class MeetingStructure:
    """Represents the overall structure of a meeting"""
    meeting_id: str
    title: Optional[str] = None
    date: Optional[datetime] = None
    duration: Optional[float] = None
    attendees: List[str] = field(default_factory=list)
    elements: List[MeetingElement] = field(default_factory=list)
    agenda_items: List[MeetingElement] = field(default_factory=list)
    decisions: List[MeetingElement] = field(default_factory=list)
    action_items: List[MeetingElement] = field(default_factory=list)
    discussions: List[MeetingElement] = field(default_factory=list)
    
    def add_element(self, element: MeetingElement):
        """Add an element and categorize it"""
        self.elements.append(element)
        
        # Categorize elements
        if element.element_type == MeetingElementType.AGENDA_ITEM:
            self.agenda_items.append(element)
        elif element.element_type == MeetingElementType.DECISION:
            self.decisions.append(element)
        elif element.element_type == MeetingElementType.ACTION_ITEM:
            self.action_items.append(element)
        elif element.element_type == MeetingElementType.DISCUSSION_POINT:
            self.discussions.append(element)
    
    def get_elements_by_type(self, element_type: MeetingElementType) -> List[MeetingElement]:
        """Get all elements of a specific type"""
        return [e for e in self.elements if e.element_type == element_type]
    
    def get_high_confidence_elements(self, min_confidence: float = 0.75) -> List[MeetingElement]:
        """Get elements with high confidence scores"""
        return [e for e in self.elements if e.confidence >= min_confidence]

class MeetingPatternMatcher:
    """Pattern matching for different meeting elements"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.contextual_indicators = self._initialize_contextual_indicators()
    
    def _initialize_patterns(self) -> Dict[MeetingElementType, List[Dict[str, Any]]]:
        """Initialize regex patterns for different meeting elements"""
        return {
            MeetingElementType.AGENDA_ITEM: [
                {
                    'pattern': r'(?i)(?:agenda item|item)\s*(?:#?\d+)?[:\s]*(.+?)(?=\.|$|next|moving)',
                    'confidence_boost': 0.3,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:let\'s discuss|we need to talk about|next topic|moving on to)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.2,
                    'context_required': True
                },
                {
                    'pattern': r'(?i)(?:first|second|third|next|finally),?\s*(?:we\'ll|let\'s|we need to)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.25,
                    'context_required': False
                }
            ],
            
            MeetingElementType.DECISION: [
                {
                    'pattern': r'(?i)(?:we\'ve decided|decision|it\'s decided|we agree|consensus)\s*(?:that|to|on)?\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.4,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:approved|rejected|accepted|denied|voted)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.35,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:final decision|conclusion)\s*(?:is|was)?\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.3,
                    'context_required': False
                }
            ],
            
            MeetingElementType.ACTION_ITEM: [
                {
                    'pattern': r'(?i)(?:action item|todo|task|assignment)\s*(?:for)?\s*([^.]+?)(?:by|due|deadline)\s*([^.]+?)(?=\.|$)',
                    'confidence_boost': 0.4,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)([A-Za-z]+)\s*(?:will|should|needs to|must)\s*(.+?)(?:by|before|until)\s*([^.]+?)(?=\.|$)',
                    'confidence_boost': 0.35,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:please|can you|could you)\s*([^,]+),?\s*(.+?)(?:by|before)\s*([^.]+?)(?=\.|$)',
                    'confidence_boost': 0.3,
                    'context_required': True
                }
            ],
            
            MeetingElementType.QUESTION: [
                {
                    'pattern': r'(?i)(.+?\?)(?=\s|$)',
                    'confidence_boost': 0.2,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:question|ask|wondering)\s*(?:about|is)?\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.25,
                    'context_required': True
                }
            ],
            
            MeetingElementType.AGREEMENT: [
                {
                    'pattern': r'(?i)(?:agreed|agree|consensus|unanimous|everyone agrees?)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.3,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:sounds good|that works|perfect|exactly|absolutely)\s*(.*)(?=\.|$)',
                    'confidence_boost': 0.2,
                    'context_required': True
                }
            ],
            
            MeetingElementType.OBJECTION: [
                {
                    'pattern': r'(?i)(?:disagree|object|concern|problem|issue)\s*(?:with|about)?\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.3,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:but|however|wait|hold on)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.15,
                    'context_required': True
                }
            ],
            
            MeetingElementType.FOLLOW_UP: [
                {
                    'pattern': r'(?i)(?:follow up|follow-up|next steps?)\s*(?:on|with|is|are)?\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.35,
                    'context_required': False
                },
                {
                    'pattern': r'(?i)(?:we\'ll|let\'s)\s*(?:revisit|check back|circle back)\s*(.+?)(?=\.|$)',
                    'confidence_boost': 0.25,
                    'context_required': False
                }
            ]
        }
    
    def _initialize_contextual_indicators(self) -> Dict[str, List[str]]:
        """Initialize contextual indicators that boost confidence"""
        return {
            'meeting_start': [
                'welcome everyone', 'let\'s get started', 'good morning', 'good afternoon',
                'thank you for joining', 'let\'s begin', 'first item', 'agenda'
            ],
            'meeting_end': [
                'that concludes', 'thank you everyone', 'meeting adjourned', 'see you next',
                'any other business', 'closing remarks', 'wrap up'
            ],
            'decision_context': [
                'vote', 'consensus', 'majority', 'unanimous', 'approved', 'rejected',
                'motion', 'seconded', 'carried', 'defeated'
            ],
            'action_context': [
                'responsible', 'owner', 'assignee', 'deadline', 'due date', 'by when',
                'timeline', 'deliverable', 'milestone'
            ],
            'discussion_context': [
                'thoughts', 'opinions', 'feedback', 'input', 'perspective', 'view',
                'concerns', 'questions', 'comments'
            ]
        }
    
    def match_patterns(self, text: str, context: Dict[str, Any] = None) -> List[Tuple[MeetingElementType, str, float]]:
        """Match patterns in text and return potential meeting elements"""
        matches = []
        context = context or {}
        
        for element_type, pattern_list in self.patterns.items():
            for pattern_info in pattern_list:
                pattern = pattern_info['pattern']
                confidence_boost = pattern_info['confidence_boost']
                context_required = pattern_info['context_required']
                
                # Find all matches for this pattern
                regex_matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                
                for match in regex_matches:
                    matched_text = match.group(1) if match.groups() else match.group(0)
                    matched_text = matched_text.strip()
                    
                    if len(matched_text) < 3:  # Skip very short matches
                        continue
                    
                    # Calculate confidence
                    confidence = confidence_boost
                    
                    # Boost confidence based on context
                    confidence += self._calculate_context_boost(element_type, text, context)
                    
                    # Reduce confidence if context is required but missing
                    if context_required and not self._has_relevant_context(element_type, text):
                        confidence *= 0.7
                    
                    # Boost confidence for longer, more detailed matches
                    if len(matched_text) > 50:
                        confidence += 0.1
                    elif len(matched_text) > 20:
                        confidence += 0.05
                    
                    # Cap confidence at 1.0
                    confidence = min(confidence, 1.0)
                    
                    matches.append((element_type, matched_text, confidence))
        
        return matches
    
    def _calculate_context_boost(self, element_type: MeetingElementType, text: str, context: Dict[str, Any]) -> float:
        """Calculate confidence boost based on context"""
        boost = 0.0
        text_lower = text.lower()
        
        # Check for contextual indicators
        context_map = {
            MeetingElementType.DECISION: 'decision_context',
            MeetingElementType.ACTION_ITEM: 'action_context',
            MeetingElementType.DISCUSSION_POINT: 'discussion_context'
        }
        
        if element_type in context_map:
            indicators = self.contextual_indicators.get(context_map[element_type], [])
            for indicator in indicators:
                if indicator in text_lower:
                    boost += 0.1
                    break
        
        # Boost based on speaker context
        if context.get('speaker_role') == 'facilitator':
            if element_type in [MeetingElementType.AGENDA_ITEM, MeetingElementType.DECISION]:
                boost += 0.15
        
        # Boost based on meeting phase
        meeting_phase = context.get('meeting_phase', 'middle')
        if meeting_phase == 'opening' and element_type == MeetingElementType.AGENDA_ITEM:
            boost += 0.2
        elif meeting_phase == 'closing' and element_type == MeetingElementType.FOLLOW_UP:
            boost += 0.2
        
        return min(boost, 0.3)  # Cap boost at 0.3
    
    def _has_relevant_context(self, element_type: MeetingElementType, text: str) -> bool:
        """Check if text has relevant context for the element type"""
        text_lower = text.lower()
        
        context_keywords = {
            MeetingElementType.ACTION_ITEM: ['will', 'should', 'must', 'need', 'responsible', 'by', 'due'],
            MeetingElementType.DECISION: ['decide', 'agree', 'vote', 'approve', 'reject'],
            MeetingElementType.AGENDA_ITEM: ['discuss', 'topic', 'item', 'next', 'moving'],
            MeetingElementType.QUESTION: ['?', 'ask', 'wonder', 'question'],
            MeetingElementType.FOLLOW_UP: ['follow', 'next', 'later', 'future']
        }
        
        keywords = context_keywords.get(element_type, [])
        return any(keyword in text_lower for keyword in keywords)

class MeetingElementIdentifier:
    """Main class for identifying meeting elements from transcribed content"""
    
    def __init__(self):
        self.pattern_matcher = MeetingPatternMatcher()
        self.speaker_patterns = self._initialize_speaker_patterns()
        self.time_patterns = self._initialize_time_patterns()
    
    def _initialize_speaker_patterns(self) -> List[str]:
        """Initialize patterns for identifying speakers"""
        return [
            r'^([A-Za-z\s]+):\s*(.+)$',  # "John Smith: content"
            r'^\[([A-Za-z\s]+)\]\s*(.+)$',  # "[John Smith] content"
            r'^([A-Za-z\s]+)\s*-\s*(.+)$',  # "John Smith - content"
            r'^>>\s*([A-Za-z\s]+):\s*(.+)$'  # ">> John Smith: content"
        ]
    
    def _initialize_time_patterns(self) -> List[str]:
        """Initialize patterns for identifying timestamps"""
        return [
            r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]',  # [14:30:15] or [14:30]
            r'(\d{1,2}:\d{2}(?::\d{2})?)\s*-',   # 14:30:15 - or 14:30 -
            r'@(\d{1,2}:\d{2}(?::\d{2})?)',      # @14:30:15 or @14:30
            r'\((\d{1,2}:\d{2}(?::\d{2})?)\)'    # (14:30:15) or (14:30)
        ]
    
    def identify_elements(self, transcript: str, context: Dict[str, Any] = None) -> MeetingStructure:
        """Identify meeting elements from transcript"""
        context = context or {}
        meeting_id = context.get('meeting_id', f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Create meeting structure
        meeting = MeetingStructure(
            meeting_id=meeting_id,
            title=context.get('title'),
            date=context.get('date'),
            duration=context.get('duration')
        )
        
        # Parse transcript into segments
        segments = self._parse_transcript_segments(transcript)
        
        # Identify attendees
        meeting.attendees = self._identify_attendees(segments)
        
        # Process each segment
        for segment in segments:
            elements = self._process_segment(segment, context)
            for element in elements:
                meeting.add_element(element)
        
        # Post-process to improve accuracy
        self._post_process_elements(meeting)
        
        logger.info(f"Identified {len(meeting.elements)} meeting elements")
        return meeting
    
    def _parse_transcript_segments(self, transcript: str) -> List[Dict[str, Any]]:
        """Parse transcript into segments with speaker and timing information"""
        segments = []
        lines = transcript.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            segment = {
                'line_number': line_num,
                'original_text': line,
                'speaker': None,
                'timestamp': None,
                'content': line
            }
            
            # Extract timestamp
            timestamp = self._extract_timestamp(line)
            if timestamp:
                segment['timestamp'] = timestamp
                # Remove timestamp from content
                for pattern in self.time_patterns:
                    line = re.sub(pattern, '', line).strip()
                segment['content'] = line
            
            # Extract speaker
            speaker, content = self._extract_speaker(line)
            if speaker:
                segment['speaker'] = speaker
                segment['content'] = content
            
            segments.append(segment)
        
        return segments
    
    def _extract_timestamp(self, text: str) -> Optional[str]:
        """Extract timestamp from text"""
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def _extract_speaker(self, text: str) -> Tuple[Optional[str], str]:
        """Extract speaker name from text"""
        for pattern in self.speaker_patterns:
            match = re.match(pattern, text)
            if match:
                speaker = match.group(1).strip()
                content = match.group(2).strip()
                return speaker, content
        return None, text
    
    def _identify_attendees(self, segments: List[Dict[str, Any]]) -> List[str]:
        """Identify meeting attendees from segments"""
        attendees = set()
        
        for segment in segments:
            if segment['speaker']:
                attendees.add(segment['speaker'])
        
        # Also look for introduction patterns
        intro_patterns = [
            r'(?i)(?:i\'m|my name is|this is)\s+([A-Za-z\s]+)',
            r'(?i)([A-Za-z\s]+)\s+(?:here|present|joining)',
            r'(?i)welcome\s+([A-Za-z\s]+)'
        ]
        
        for segment in segments:
            content = segment['content']
            for pattern in intro_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    name = match.group(1).strip()
                    if len(name.split()) <= 3:  # Reasonable name length
                        attendees.add(name)
        
        return list(attendees)
    
    def _process_segment(self, segment: Dict[str, Any], context: Dict[str, Any]) -> List[MeetingElement]:
        """Process a single segment to identify meeting elements"""
        content = segment['content']
        speaker = segment['speaker']
        timestamp = segment['timestamp']
        
        # Create segment context
        segment_context = context.copy()
        segment_context.update({
            'speaker': speaker,
            'timestamp': timestamp,
            'line_number': segment['line_number']
        })
        
        # Match patterns
        pattern_matches = self.pattern_matcher.match_patterns(content, segment_context)
        
        elements = []
        for element_type, matched_text, confidence in pattern_matches:
            # Skip very low confidence matches
            if confidence < 0.1:
                continue
            
            element = MeetingElement(
                element_type=element_type,
                content=matched_text,
                speaker=speaker,
                confidence=confidence,
                context={
                    'original_text': content,
                    'line_number': segment['line_number'],
                    'timestamp': timestamp
                }
            )
            
            # Convert timestamp to float if possible
            if timestamp:
                try:
                    time_parts = timestamp.split(':')
                    if len(time_parts) >= 2:
                        minutes = int(time_parts[0]) * 60 + int(time_parts[1])
                        if len(time_parts) == 3:
                            minutes += int(time_parts[2]) / 60
                        element.start_time = minutes
                except (ValueError, IndexError):
                    pass
            
            elements.append(element)
        
        return elements
    
    def _post_process_elements(self, meeting: MeetingStructure):
        """Post-process elements to improve accuracy and remove duplicates"""
        
        # Remove duplicate elements
        unique_elements = []
        seen_content = set()
        
        for element in meeting.elements:
            content_key = f"{element.element_type.value}:{element.content.lower()}"
            if content_key not in seen_content:
                unique_elements.append(element)
                seen_content.add(content_key)
            else:
                # If duplicate, keep the one with higher confidence
                existing_idx = next(
                    i for i, e in enumerate(unique_elements)
                    if f"{e.element_type.value}:{e.content.lower()}" == content_key
                )
                if element.confidence > unique_elements[existing_idx].confidence:
                    unique_elements[existing_idx] = element
        
        # Update meeting elements
        meeting.elements = unique_elements
        
        # Re-categorize elements
        meeting.agenda_items = [e for e in meeting.elements if e.element_type == MeetingElementType.AGENDA_ITEM]
        meeting.decisions = [e for e in meeting.elements if e.element_type == MeetingElementType.DECISION]
        meeting.action_items = [e for e in meeting.elements if e.element_type == MeetingElementType.ACTION_ITEM]
        meeting.discussions = [e for e in meeting.elements if e.element_type == MeetingElementType.DISCUSSION_POINT]
        
        # Sort elements by confidence
        meeting.elements.sort(key=lambda x: x.confidence, reverse=True)
    
    def get_element_statistics(self, meeting: MeetingStructure) -> Dict[str, Any]:
        """Get statistics about identified elements"""
        stats = {
            'total_elements': len(meeting.elements),
            'by_type': defaultdict(int),
            'by_confidence_level': defaultdict(int),
            'average_confidence': 0.0,
            'high_confidence_count': 0,
            'attendee_count': len(meeting.attendees),
            'elements_with_speakers': 0,
            'elements_with_timestamps': 0
        }
        
        if meeting.elements:
            total_confidence = 0
            for element in meeting.elements:
                stats['by_type'][element.element_type.value] += 1
                stats['by_confidence_level'][element.confidence_level.value] += 1
                total_confidence += element.confidence
                
                if element.confidence >= 0.75:
                    stats['high_confidence_count'] += 1
                
                if element.speaker:
                    stats['elements_with_speakers'] += 1
                
                if element.start_time is not None:
                    stats['elements_with_timestamps'] += 1
            
            stats['average_confidence'] = total_confidence / len(meeting.elements)
        
        return dict(stats)

# Utility functions
def create_meeting_identifier() -> MeetingElementIdentifier:
    """Create a meeting element identifier"""
    return MeetingElementIdentifier()

def analyze_meeting_transcript(transcript: str, context: Dict[str, Any] = None) -> MeetingStructure:
    """Analyze a meeting transcript and return identified elements"""
    identifier = create_meeting_identifier()
    return identifier.identify_elements(transcript, context)

# Example usage
def example_usage():
    """Example usage of meeting element identification"""
    
    # Sample meeting transcript
    sample_transcript = """
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
    
    # Analyze the transcript
    context = {
        'meeting_id': 'quarterly_planning_2024',
        'title': 'Quarterly Planning Meeting',
        'date': datetime.now()
    }
    
    meeting = analyze_meeting_transcript(sample_transcript, context)
    
    # Print results
    print(f"Meeting Analysis Results:")
    print(f"Meeting ID: {meeting.meeting_id}")
    print(f"Title: {meeting.title}")
    print(f"Attendees: {', '.join(meeting.attendees)}")
    print(f"Total Elements: {len(meeting.elements)}")
    
    print(f"\nAgenda Items ({len(meeting.agenda_items)}):")
    for item in meeting.agenda_items:
        print(f"  - {item.content} (confidence: {item.confidence:.2f})")
    
    print(f"\nDecisions ({len(meeting.decisions)}):")
    for decision in meeting.decisions:
        print(f"  - {decision.content} (confidence: {decision.confidence:.2f})")
    
    print(f"\nAction Items ({len(meeting.action_items)}):")
    for action in meeting.action_items:
        print(f"  - {action.content} (confidence: {action.confidence:.2f})")
    
    # Get statistics
    identifier = create_meeting_identifier()
    stats = identifier.get_element_statistics(meeting)
    print(f"\nStatistics:")
    print(f"  Average confidence: {stats['average_confidence']:.2f}")
    print(f"  High confidence elements: {stats['high_confidence_count']}")
    print(f"  Elements with speakers: {stats['elements_with_speakers']}")
    print(f"  Elements with timestamps: {stats['elements_with_timestamps']}")

if __name__ == "__main__":
    example_usage()