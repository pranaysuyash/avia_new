#!/usr/bin/env python3
"""
Action Item Extraction and Assignment System
Advanced system for extracting, analyzing, and assigning action items from meeting transcripts
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from collections import defaultdict
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_element_identification import (
    MeetingElementIdentifier,
    MeetingStructure,
    MeetingElement,
    MeetingElementType,
    ConfidenceLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionItemPriority(Enum):
    """Priority levels for action items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSPECIFIED = "unspecified"

class ActionItemStatus(Enum):
    """Status of action items"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class DeadlineType(Enum):
    """Types of deadlines"""
    SPECIFIC_DATE = "specific_date"
    RELATIVE_TIME = "relative_time"
    MEETING_BASED = "meeting_based"
    UNSPECIFIED = "unspecified"

@dataclass
class ActionItemDeadline:
    """Represents a deadline for an action item"""
    deadline_type: DeadlineType
    original_text: str
    parsed_date: Optional[datetime] = None
    relative_days: Optional[int] = None
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def is_overdue(self, current_date: datetime = None) -> bool:
        """Check if the deadline is overdue"""
        if not current_date:
            current_date = datetime.now()
        
        if self.parsed_date:
            return current_date > self.parsed_date
        
        return False
    
    def days_until_deadline(self, current_date: datetime = None) -> Optional[int]:
        """Calculate days until deadline"""
        if not current_date:
            current_date = datetime.now()
        
        if self.parsed_date:
            delta = self.parsed_date - current_date
            return delta.days
        
        return None

@dataclass
class ActionItemAssignee:
    """Represents an assignee for an action item"""
    name: str
    role: Optional[str] = None
    email: Optional[str] = None
    confidence: float = 0.0
    assignment_method: str = "explicit"  # explicit, implicit, inferred
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionItem:
    """Represents a complete action item with all details"""
    id: str
    content: str
    assignees: List[ActionItemAssignee] = field(default_factory=list)
    deadline: Optional[ActionItemDeadline] = None
    priority: ActionItemPriority = ActionItemPriority.UNSPECIFIED
    status: ActionItemStatus = ActionItemStatus.PENDING
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    source_element: Optional[MeetingElement] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
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
    
    def add_assignee(self, assignee: ActionItemAssignee):
        """Add an assignee to the action item"""
        self.assignees.append(assignee)
        self.updated_at = datetime.now()
    
    def set_deadline(self, deadline: ActionItemDeadline):
        """Set the deadline for the action item"""
        self.deadline = deadline
        self.updated_at = datetime.now()
    
    def update_status(self, status: ActionItemStatus):
        """Update the status of the action item"""
        self.status = status
        self.updated_at = datetime.now()
    
    def is_overdue(self) -> bool:
        """Check if the action item is overdue"""
        if self.deadline:
            return self.deadline.is_overdue()
        return False
    
    def get_primary_assignee(self) -> Optional[ActionItemAssignee]:
        """Get the primary assignee (highest confidence)"""
        if not self.assignees:
            return None
        return max(self.assignees, key=lambda a: a.confidence)

class DeadlineParser:
    """Parser for extracting and parsing deadlines from text"""
    
    def __init__(self):
        self.date_patterns = self._initialize_date_patterns()
        self.relative_patterns = self._initialize_relative_patterns()
        self.meeting_patterns = self._initialize_meeting_patterns()
    
    def _initialize_date_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for specific dates"""
        return [
            {
                'pattern': r'(?i)(?:by|before|due)\s*(?:on\s*)?(\w+day),?\s*(\w+)\s*(\d{1,2})(?:st|nd|rd|th)?',
                'type': DeadlineType.SPECIFIC_DATE,
                'confidence': 0.8
            },
            {
                'pattern': r'(?i)(?:by|before|due)\s*(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})',
                'type': DeadlineType.SPECIFIC_DATE,
                'confidence': 0.9
            },
            {
                'pattern': r'(?i)(?:by|before|due)\s*(\w+)\s*(\d{1,2})(?:st|nd|rd|th)?',
                'type': DeadlineType.SPECIFIC_DATE,
                'confidence': 0.7
            },
            {
                'pattern': r'(?i)(?:by|before|due)\s*(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s*)?(\w+)',
                'type': DeadlineType.SPECIFIC_DATE,
                'confidence': 0.7
            }
        ]
    
    def _initialize_relative_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for relative time deadlines"""
        return [
            {
                'pattern': r'(?i)(?:by|before|within|in)\s*(\d+)\s*(day|week|month)s?',
                'type': DeadlineType.RELATIVE_TIME,
                'confidence': 0.8
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(tomorrow|today)',
                'type': DeadlineType.RELATIVE_TIME,
                'confidence': 0.9
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(next\s+\w+day)',
                'type': DeadlineType.RELATIVE_TIME,
                'confidence': 0.8
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(this\s+\w+day)',
                'type': DeadlineType.RELATIVE_TIME,
                'confidence': 0.8
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(?:the\s+)?end\s+of\s+(?:this\s+|next\s+)?(week|month|quarter)',
                'type': DeadlineType.RELATIVE_TIME,
                'confidence': 0.7
            }
        ]
    
    def _initialize_meeting_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for meeting-based deadlines"""
        return [
            {
                'pattern': r'(?i)(?:by|before)\s*(?:the\s+)?next\s+meeting',
                'type': DeadlineType.MEETING_BASED,
                'confidence': 0.8
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(?:our\s+)?(?:next\s+)?(?:weekly|monthly|quarterly)\s+meeting',
                'type': DeadlineType.MEETING_BASED,
                'confidence': 0.7
            },
            {
                'pattern': r'(?i)(?:by|before)\s*(?:the\s+)?follow[- ]?up\s+meeting',
                'type': DeadlineType.MEETING_BASED,
                'confidence': 0.8
            }
        ]
    
    def parse_deadline(self, text: str, context: Dict[str, Any] = None) -> Optional[ActionItemDeadline]:
        """Parse deadline from text"""
        context = context or {}
        
        # Try specific date patterns first
        for pattern_info in self.date_patterns:
            match = re.search(pattern_info['pattern'], text)
            if match:
                deadline = self._parse_specific_date(match, pattern_info, text, context)
                if deadline:
                    return deadline
        
        # Try relative time patterns
        for pattern_info in self.relative_patterns:
            match = re.search(pattern_info['pattern'], text)
            if match:
                deadline = self._parse_relative_time(match, pattern_info, text, context)
                if deadline:
                    return deadline
        
        # Try meeting-based patterns
        for pattern_info in self.meeting_patterns:
            match = re.search(pattern_info['pattern'], text)
            if match:
                deadline = self._parse_meeting_based(match, pattern_info, text, context)
                if deadline:
                    return deadline
        
        return None
    
    def _parse_specific_date(self, match, pattern_info, text, context) -> Optional[ActionItemDeadline]:
        """Parse specific date deadline"""
        try:
            groups = match.groups()
            current_year = datetime.now().year
            
            # Handle different date formats
            if len(groups) == 3:
                if groups[0].isdigit():  # MM/DD/YYYY format
                    month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                    if year < 100:
                        year += 2000
                else:  # Weekday, Month Day format
                    # This would need more sophisticated parsing
                    return None
            elif len(groups) == 2:
                # Month Day or Day Month format
                if groups[0].isdigit():
                    day, month_name = int(groups[0]), groups[1]
                else:
                    month_name, day = groups[0], int(groups[1])
                
                month = self._parse_month_name(month_name)
                if not month:
                    return None
                year = current_year
            else:
                return None
            
            parsed_date = datetime(year, month, day)
            
            # If the date is in the past, assume next year
            if parsed_date < datetime.now():
                parsed_date = parsed_date.replace(year=year + 1)
            
            return ActionItemDeadline(
                deadline_type=pattern_info['type'],
                original_text=match.group(0),
                parsed_date=parsed_date,
                confidence=pattern_info['confidence'],
                context={'pattern': pattern_info['pattern'], 'groups': groups}
            )
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse specific date: {e}")
            return None
    
    def _parse_relative_time(self, match, pattern_info, text, context) -> Optional[ActionItemDeadline]:
        """Parse relative time deadline"""
        try:
            groups = match.groups()
            current_date = datetime.now()
            
            if 'tomorrow' in match.group(0).lower():
                parsed_date = current_date + timedelta(days=1)
                relative_days = 1
            elif 'today' in match.group(0).lower():
                parsed_date = current_date
                relative_days = 0
            elif len(groups) >= 2:
                number = int(groups[0])
                unit = groups[1].lower()
                
                if unit.startswith('day'):
                    parsed_date = current_date + timedelta(days=number)
                    relative_days = number
                elif unit.startswith('week'):
                    parsed_date = current_date + timedelta(weeks=number)
                    relative_days = number * 7
                elif unit.startswith('month'):
                    # Approximate month as 30 days
                    parsed_date = current_date + timedelta(days=number * 30)
                    relative_days = number * 30
                else:
                    return None
            elif 'next' in match.group(0).lower():
                # Handle "next Monday", "next week", etc.
                relative_days = 7  # Default to next week
                parsed_date = current_date + timedelta(days=relative_days)
            elif 'this' in match.group(0).lower():
                # Handle "this Friday", "this week", etc.
                relative_days = 3  # Default to later this week
                parsed_date = current_date + timedelta(days=relative_days)
            else:
                return None
            
            return ActionItemDeadline(
                deadline_type=pattern_info['type'],
                original_text=match.group(0),
                parsed_date=parsed_date,
                relative_days=relative_days,
                confidence=pattern_info['confidence'],
                context={'pattern': pattern_info['pattern'], 'groups': groups}
            )
        
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse relative time: {e}")
            return None
    
    def _parse_meeting_based(self, match, pattern_info, text, context) -> Optional[ActionItemDeadline]:
        """Parse meeting-based deadline"""
        # For meeting-based deadlines, we can't determine exact dates without more context
        # But we can still create a deadline object with the information we have
        
        return ActionItemDeadline(
            deadline_type=pattern_info['type'],
            original_text=match.group(0),
            confidence=pattern_info['confidence'],
            context={'pattern': pattern_info['pattern'], 'meeting_context': context}
        )
    
    def _parse_month_name(self, month_name: str) -> Optional[int]:
        """Parse month name to number"""
        month_map = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        return month_map.get(month_name.lower())

class AssigneeExtractor:
    """Extractor for identifying assignees from action items"""
    
    def __init__(self):
        self.assignment_patterns = self._initialize_assignment_patterns()
        self.name_patterns = self._initialize_name_patterns()
    
    def _initialize_assignment_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for explicit assignments"""
        return [
            {
                'pattern': r'(?i)([A-Za-z\s]+)\s+(?:will|should|needs?\s+to|must)\s+(.+)',
                'confidence': 0.8,
                'method': 'explicit'
            },
            {
                'pattern': r'(?i)(?:action\s+item\s+for\s+|assign(?:ed)?\s+to\s+)([A-Za-z\s]+)',
                'confidence': 0.9,
                'method': 'explicit'
            },
            {
                'pattern': r'(?i)([A-Za-z\s]+),?\s+(?:can\s+you|could\s+you|please)\s+(.+)',
                'confidence': 0.7,
                'method': 'explicit'
            },
            {
                'pattern': r'(?i)([A-Za-z\s]+)\s+is\s+responsible\s+for\s+(.+)',
                'confidence': 0.8,
                'method': 'explicit'
            },
            {
                'pattern': r'(?i)([A-Za-z\s]+)\s+(?:owns|takes|handles)\s+(.+)',
                'confidence': 0.7,
                'method': 'explicit'
            }
        ]
    
    def _initialize_name_patterns(self) -> List[str]:
        """Initialize patterns for identifying names"""
        return [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # First Last
            r'^[A-Z][a-z]+$',  # Single name
            r'^[A-Z][a-z]+\s+[A-Z]\.$',  # First M.
            r'^[A-Z]\.\s+[A-Z][a-z]+$'  # F. Last
        ]
    
    def extract_assignees(self, text: str, context: Dict[str, Any] = None) -> List[ActionItemAssignee]:
        """Extract assignees from text"""
        context = context or {}
        assignees = []
        
        for pattern_info in self.assignment_patterns:
            matches = re.finditer(pattern_info['pattern'], text)
            
            for match in matches:
                name = match.group(1).strip()
                
                # Validate that it looks like a name
                if self._is_valid_name(name):
                    assignee = ActionItemAssignee(
                        name=name,
                        confidence=pattern_info['confidence'],
                        assignment_method=pattern_info['method'],
                        context={
                            'pattern': pattern_info['pattern'],
                            'matched_text': match.group(0),
                            'full_context': text
                        }
                    )
                    
                    # Try to infer role from context
                    role = self._infer_role(name, context)
                    if role:
                        assignee.role = role
                        assignee.confidence += 0.1  # Boost confidence if role found
                    
                    assignees.append(assignee)
        
        # Remove duplicates and merge similar names
        assignees = self._deduplicate_assignees(assignees)
        
        return assignees
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if the extracted text looks like a valid name"""
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Check against common non-name words
        non_names = {
            'we', 'they', 'someone', 'anyone', 'everyone', 'team', 'group',
            'department', 'committee', 'board', 'management', 'staff'
        }
        
        if name.lower() in non_names:
            return False
        
        # Check if it matches name patterns
        for pattern in self.name_patterns:
            if re.match(pattern, name):
                return True
        
        # If it contains only letters and spaces, it's probably a name
        return re.match(r'^[A-Za-z\s]+$', name) is not None
    
    def _infer_role(self, name: str, context: Dict[str, Any]) -> Optional[str]:
        """Try to infer role from context"""
        # Check if we have attendee information with roles
        attendees = context.get('attendees', [])
        for attendee in attendees:
            if isinstance(attendee, dict) and attendee.get('name') == name:
                return attendee.get('role')
        
        # Check for role indicators in the text
        role_patterns = {
            r'(?i)manager\s+([A-Za-z\s]+)': 'Manager',
            r'(?i)director\s+([A-Za-z\s]+)': 'Director',
            r'(?i)ceo\s+([A-Za-z\s]+)': 'CEO',
            r'(?i)developer\s+([A-Za-z\s]+)': 'Developer',
            r'(?i)designer\s+([A-Za-z\s]+)': 'Designer',
            r'(?i)analyst\s+([A-Za-z\s]+)': 'Analyst'
        }
        
        full_text = context.get('full_text', '')
        for pattern, role in role_patterns.items():
            if re.search(pattern.replace('([A-Za-z\\s]+)', re.escape(name)), full_text):
                return role
        
        return None
    
    def _deduplicate_assignees(self, assignees: List[ActionItemAssignee]) -> List[ActionItemAssignee]:
        """Remove duplicate assignees and merge similar ones"""
        if not assignees:
            return []
        
        # Group by name (case-insensitive)
        name_groups = defaultdict(list)
        for assignee in assignees:
            name_groups[assignee.name.lower()].append(assignee)
        
        # Keep the highest confidence assignee for each name
        deduplicated = []
        for name_group in name_groups.values():
            best_assignee = max(name_group, key=lambda a: a.confidence)
            deduplicated.append(best_assignee)
        
        return deduplicated

class PriorityClassifier:
    """Classifier for determining action item priority"""
    
    def __init__(self):
        self.priority_indicators = self._initialize_priority_indicators()
    
    def _initialize_priority_indicators(self) -> Dict[ActionItemPriority, List[str]]:
        """Initialize priority indicator keywords"""
        return {
            ActionItemPriority.CRITICAL: [
                'urgent', 'critical', 'asap', 'immediately', 'emergency',
                'blocker', 'blocking', 'showstopper', 'must have'
            ],
            ActionItemPriority.HIGH: [
                'important', 'priority', 'high priority', 'soon',
                'needed', 'required', 'essential', 'key'
            ],
            ActionItemPriority.MEDIUM: [
                'should', 'would be good', 'helpful', 'nice to have',
                'when possible', 'if time permits'
            ],
            ActionItemPriority.LOW: [
                'eventually', 'someday', 'low priority', 'minor',
                'optional', 'if we have time', 'backlog'
            ]
        }
    
    def classify_priority(self, text: str, context: Dict[str, Any] = None) -> ActionItemPriority:
        """Classify the priority of an action item"""
        text_lower = text.lower()
        context = context or {}
        
        # Check for explicit priority indicators
        for priority, indicators in self.priority_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return priority
        
        # Check deadline urgency
        deadline = context.get('deadline')
        if deadline and isinstance(deadline, ActionItemDeadline):
            days_until = deadline.days_until_deadline()
            if days_until is not None:
                if days_until <= 1:
                    return ActionItemPriority.CRITICAL
                elif days_until <= 3:
                    return ActionItemPriority.HIGH
                elif days_until <= 7:
                    return ActionItemPriority.MEDIUM
        
        # Check speaker role (managers/executives might indicate higher priority)
        speaker_role = context.get('speaker_role', '') or ''
        if speaker_role and any(role in speaker_role.lower() for role in ['ceo', 'director', 'manager', 'lead']):
            return ActionItemPriority.HIGH
        
        # Default to medium priority
        return ActionItemPriority.MEDIUM

class ActionItemExtractor:
    """Main class for extracting and analyzing action items"""
    
    def __init__(self):
        self.deadline_parser = DeadlineParser()
        self.assignee_extractor = AssigneeExtractor()
        self.priority_classifier = PriorityClassifier()
        self.action_patterns = self._initialize_action_patterns()
    
    def _initialize_action_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for identifying action items"""
        return [
            {
                'pattern': r'(?i)action\s+item[:\s]*(.+?)(?=\.|$|action\s+item)',
                'confidence': 0.9,
                'type': 'explicit'
            },
            {
                'pattern': r'(?i)(?:todo|to-do|task)[:\s]*(.+?)(?=\.|$)',
                'confidence': 0.8,
                'type': 'explicit'
            },
            {
                'pattern': r'(?i)([A-Za-z\s]+)\s+(?:will|should|needs?\s+to|must)\s+(.+?)(?:by|before|until)\s+(.+?)(?=\.|$)',
                'confidence': 0.7,
                'type': 'commitment'
            },
            {
                'pattern': r'(?i)([A-Za-z\s]+),?\s+(?:can\s+you|could\s+you|please)\s+(.+?)(?=\.|$)',
                'confidence': 0.6,
                'type': 'request'
            },
            {
                'pattern': r'(?i)(?:we\s+need\s+to|let\'s|someone\s+should)\s+(.+?)(?=\.|$)',
                'confidence': 0.5,
                'type': 'general'
            }
        ]
    
    def extract_action_items(self, meeting: MeetingStructure, context: Dict[str, Any] = None) -> List[ActionItem]:
        """Extract action items from a meeting structure"""
        context = context or {}
        action_items = []
        
        # First, get explicit action items from meeting elements
        explicit_actions = meeting.get_elements_by_type(MeetingElementType.ACTION_ITEM)
        
        for element in explicit_actions:
            action_item = self._process_action_element(element, context)
            if action_item:
                action_items.append(action_item)
        
        # Then, look for implicit action items in other elements
        other_elements = [
            e for e in meeting.elements 
            if e.element_type not in [MeetingElementType.ACTION_ITEM]
        ]
        
        for element in other_elements:
            implicit_actions = self._extract_implicit_actions(element, context)
            action_items.extend(implicit_actions)
        
        # Post-process to remove duplicates and enhance details
        action_items = self._post_process_action_items(action_items, meeting, context)
        
        logger.info(f"Extracted {len(action_items)} action items from meeting")
        return action_items
    
    def _process_action_element(self, element: MeetingElement, context: Dict[str, Any]) -> Optional[ActionItem]:
        """Process an explicit action item element"""
        content = element.content
        
        # Extract assignees
        assignees = self.assignee_extractor.extract_assignees(content, {
            **context,
            'speaker': element.speaker,
            'full_text': content
        })
        
        # Extract deadline
        deadline = self.deadline_parser.parse_deadline(content, context)
        
        # Classify priority
        priority = self.priority_classifier.classify_priority(content, {
            **context,
            'deadline': deadline,
            'speaker_role': context.get('speaker_roles', {}).get(element.speaker)
        })
        
        # Generate unique ID
        action_id = f"action_{hash(content + str(element.start_time or 0))}_{len(assignees)}"
        
        # Create action item
        action_item = ActionItem(
            id=action_id,
            content=content,
            assignees=assignees,
            deadline=deadline,
            priority=priority,
            confidence=element.confidence,
            source_element=element,
            context={
                'extraction_method': 'explicit',
                'original_element_type': element.element_type.value,
                'speaker': element.speaker,
                'timestamp': element.start_time
            }
        )
        
        # Add tags based on content analysis
        tags = self._extract_tags(content)
        action_item.tags = tags
        
        return action_item
    
    def _extract_implicit_actions(self, element: MeetingElement, context: Dict[str, Any]) -> List[ActionItem]:
        """Extract implicit action items from non-action elements"""
        content = element.content
        implicit_actions = []
        
        for pattern_info in self.action_patterns:
            matches = re.finditer(pattern_info['pattern'], content)
            
            for match in matches:
                # Extract the action content
                if pattern_info['type'] == 'commitment' and len(match.groups()) >= 2:
                    assignee_text = match.group(1).strip()
                    action_content = match.group(2).strip()
                    deadline_text = match.group(3).strip() if len(match.groups()) >= 3 else None
                elif pattern_info['type'] == 'request' and len(match.groups()) >= 2:
                    assignee_text = match.group(1).strip()
                    action_content = match.group(2).strip()
                    deadline_text = None
                else:
                    action_content = match.group(1).strip() if match.groups() else match.group(0).strip()
                    assignee_text = None
                    deadline_text = None
                
                # Skip very short or generic actions
                if len(action_content) < 10 or any(word in action_content.lower() for word in ['this', 'that', 'it']):
                    continue
                
                # Extract assignees
                assignees = []
                if assignee_text:
                    # Create assignee from matched text
                    if self.assignee_extractor._is_valid_name(assignee_text):
                        assignees.append(ActionItemAssignee(
                            name=assignee_text,
                            confidence=pattern_info['confidence'],
                            assignment_method='implicit'
                        ))
                else:
                    # Try to extract from action content
                    assignees = self.assignee_extractor.extract_assignees(action_content, {
                        **context,
                        'speaker': element.speaker,
                        'full_text': content
                    })
                
                # Extract deadline
                deadline = None
                if deadline_text:
                    deadline = self.deadline_parser.parse_deadline(deadline_text, context)
                else:
                    deadline = self.deadline_parser.parse_deadline(action_content, context)
                
                # Classify priority (lower confidence for implicit actions)
                priority = self.priority_classifier.classify_priority(action_content, {
                    **context,
                    'deadline': deadline,
                    'speaker_role': context.get('speaker_roles', {}).get(element.speaker)
                })
                
                # Generate unique ID
                action_id = f"implicit_{hash(action_content + str(element.start_time or 0))}_{len(assignees)}"
                
                # Create action item with reduced confidence
                confidence = min(element.confidence * pattern_info['confidence'], 0.8)
                
                action_item = ActionItem(
                    id=action_id,
                    content=action_content,
                    assignees=assignees,
                    deadline=deadline,
                    priority=priority,
                    confidence=confidence,
                    source_element=element,
                    context={
                        'extraction_method': 'implicit',
                        'pattern_type': pattern_info['type'],
                        'original_element_type': element.element_type.value,
                        'speaker': element.speaker,
                        'timestamp': element.start_time,
                        'matched_text': match.group(0)
                    }
                )
                
                # Add tags
                tags = self._extract_tags(action_content)
                action_item.tags = tags
                
                implicit_actions.append(action_item)
        
        return implicit_actions
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from action item content"""
        tags = []
        content_lower = content.lower()
        
        # Technical tags
        tech_keywords = ['code', 'development', 'bug', 'feature', 'api', 'database', 'testing']
        for keyword in tech_keywords:
            if keyword in content_lower:
                tags.append(f'tech:{keyword}')
        
        # Business tags
        business_keywords = ['budget', 'finance', 'marketing', 'sales', 'strategy', 'planning']
        for keyword in business_keywords:
            if keyword in content_lower:
                tags.append(f'business:{keyword}')
        
        # Process tags
        process_keywords = ['review', 'approve', 'analyze', 'research', 'document', 'report']
        for keyword in process_keywords:
            if keyword in content_lower:
                tags.append(f'process:{keyword}')
        
        # Communication tags
        comm_keywords = ['email', 'call', 'meeting', 'presentation', 'demo', 'update']
        for keyword in comm_keywords:
            if keyword in content_lower:
                tags.append(f'communication:{keyword}')
        
        return tags
    
    def _post_process_action_items(self, action_items: List[ActionItem], meeting: MeetingStructure, context: Dict[str, Any]) -> List[ActionItem]:
        """Post-process action items to remove duplicates and enhance details"""
        if not action_items:
            return []
        
        # Remove duplicates based on content similarity
        unique_actions = []
        seen_content = set()
        
        for action in action_items:
            content_key = action.content.lower().strip()
            if content_key not in seen_content:
                unique_actions.append(action)
                seen_content.add(content_key)
            else:
                # If duplicate, merge with existing if this one has higher confidence
                existing_idx = next(
                    i for i, a in enumerate(unique_actions)
                    if a.content.lower().strip() == content_key
                )
                if action.confidence > unique_actions[existing_idx].confidence:
                    unique_actions[existing_idx] = action
        
        # Sort by confidence and priority
        unique_actions.sort(key=lambda a: (a.priority.value, -a.confidence))
        
        # Enhance with meeting context
        for action in unique_actions:
            self._enhance_with_meeting_context(action, meeting, context)
        
        return unique_actions
    
    def _enhance_with_meeting_context(self, action: ActionItem, meeting: MeetingStructure, context: Dict[str, Any]):
        """Enhance action item with additional meeting context"""
        # Add meeting information to context
        action.context.update({
            'meeting_id': meeting.meeting_id,
            'meeting_title': meeting.title,
            'meeting_date': meeting.date.isoformat() if meeting.date else None,
            'total_attendees': len(meeting.attendees)
        })
        
        # Try to identify dependencies from other action items
        dependencies = []
        for other_action in context.get('all_actions', []):
            if other_action.id != action.id:
                # Simple dependency detection based on content similarity
                if any(word in action.content.lower() for word in other_action.content.lower().split()[:3]):
                    dependencies.append(other_action.id)
        
        action.dependencies = dependencies[:3]  # Limit to 3 dependencies
    
    def get_action_item_statistics(self, action_items: List[ActionItem]) -> Dict[str, Any]:
        """Get statistics about extracted action items"""
        if not action_items:
            return {
                'total_actions': 0,
                'by_priority': {},
                'by_status': {},
                'with_assignees': 0,
                'with_deadlines': 0,
                'average_confidence': 0.0,
                'overdue_count': 0
            }
        
        stats = {
            'total_actions': len(action_items),
            'by_priority': defaultdict(int),
            'by_status': defaultdict(int),
            'by_confidence_level': defaultdict(int),
            'with_assignees': 0,
            'with_deadlines': 0,
            'average_confidence': 0.0,
            'overdue_count': 0,
            'by_extraction_method': defaultdict(int),
            'common_tags': defaultdict(int)
        }
        
        total_confidence = 0
        for action in action_items:
            stats['by_priority'][action.priority.value] += 1
            stats['by_status'][action.status.value] += 1
            stats['by_confidence_level'][action.confidence_level.value] += 1
            
            if action.assignees:
                stats['with_assignees'] += 1
            
            if action.deadline:
                stats['with_deadlines'] += 1
                if action.is_overdue():
                    stats['overdue_count'] += 1
            
            total_confidence += action.confidence
            
            extraction_method = action.context.get('extraction_method', 'unknown')
            stats['by_extraction_method'][extraction_method] += 1
            
            for tag in action.tags:
                stats['common_tags'][tag] += 1
        
        stats['average_confidence'] = total_confidence / len(action_items)
        
        # Convert defaultdicts to regular dicts
        for key in ['by_priority', 'by_status', 'by_confidence_level', 'by_extraction_method', 'common_tags']:
            stats[key] = dict(stats[key])
        
        return stats

# Utility functions
def create_action_item_extractor() -> ActionItemExtractor:
    """Create an action item extractor"""
    return ActionItemExtractor()

def extract_action_items_from_meeting(meeting: MeetingStructure, context: Dict[str, Any] = None) -> List[ActionItem]:
    """Extract action items from a meeting structure"""
    extractor = create_action_item_extractor()
    return extractor.extract_action_items(meeting, context)

# Example usage
def example_usage():
    """Example usage of action item extraction"""
    from meeting_element_identification import analyze_meeting_transcript
    
    # Sample meeting transcript with action items
    sample_transcript = """
[14:00] John Smith: Welcome everyone to today's project planning meeting.
[14:02] John Smith: First agenda item - reviewing the current sprint progress.
[14:05] Sarah Johnson: We've completed 80% of the user stories. The remaining ones need more work.
[14:07] Mike Davis: I have a concern about the API integration. It's more complex than expected.
[14:10] John Smith: Good point Mike. Can you prepare a detailed analysis by next Wednesday?
[14:11] Mike Davis: Absolutely. I'll have the technical assessment ready by Wednesday morning.
[14:13] Sarah Johnson: We also need someone to update the documentation.
[14:15] John Smith: Sarah, could you handle the documentation update? It's high priority.
[14:16] Sarah Johnson: Sure, I can do that. When do you need it?
[14:17] John Smith: By end of this week would be great.
[14:19] Lisa Chen: Action item for me - I'll coordinate with the QA team for testing.
[14:21] Lisa Chen: I'll set up the testing schedule by tomorrow.
[14:23] John Smith: Perfect. Any other urgent tasks we need to assign?
[14:25] Mike Davis: We should review the security requirements. It's critical for the launch.
[14:27] John Smith: Agreed. Mike, can you also include security analysis in your assessment?
[14:28] Mike Davis: Will do. I'll make it part of the Wednesday deliverable.
[14:30] John Smith: Great. Follow up meeting next Friday to review all progress.
[14:31] John Smith: Thank you everyone. Meeting adjourned.
    """
    
    # Analyze the meeting first
    context = {
        'meeting_id': 'project_planning_2024',
        'title': 'Project Planning Meeting',
        'date': datetime(2024, 1, 15, 14, 0),
        'speaker_roles': {
            'John Smith': 'Project Manager',
            'Sarah Johnson': 'Developer',
            'Mike Davis': 'Technical Lead',
            'Lisa Chen': 'QA Manager'
        }
    }
    
    meeting = analyze_meeting_transcript(sample_transcript, context)
    
    # Extract action items
    extractor = create_action_item_extractor()
    action_items = extractor.extract_action_items(meeting, context)
    
    # Print results
    print(f"Action Item Extraction Results:")
    print(f"Total Action Items: {len(action_items)}")
    print()
    
    for i, action in enumerate(action_items, 1):
        print(f"{i}. {action.content}")
        print(f"   Priority: {action.priority.value.title()}")
        print(f"   Confidence: {action.confidence:.2f} ({action.confidence_level.value})")
        
        if action.assignees:
            assignee_names = [a.name for a in action.assignees]
            print(f"   Assignees: {', '.join(assignee_names)}")
        
        if action.deadline:
            if action.deadline.parsed_date:
                print(f"   Deadline: {action.deadline.parsed_date.strftime('%Y-%m-%d')} ({action.deadline.original_text})")
            else:
                print(f"   Deadline: {action.deadline.original_text}")
        
        if action.tags:
            print(f"   Tags: {', '.join(action.tags)}")
        
        print(f"   Method: {action.context.get('extraction_method', 'unknown')}")
        print()
    
    # Get statistics
    stats = extractor.get_action_item_statistics(action_items)
    print(f"Statistics:")
    print(f"  Total Actions: {stats['total_actions']}")
    print(f"  With Assignees: {stats['with_assignees']}")
    print(f"  With Deadlines: {stats['with_deadlines']}")
    print(f"  Average Confidence: {stats['average_confidence']:.2f}")
    print(f"  Overdue: {stats['overdue_count']}")
    
    print(f"\nBy Priority:")
    for priority, count in stats['by_priority'].items():
        print(f"  {priority.title()}: {count}")
    
    print(f"\nBy Extraction Method:")
    for method, count in stats['by_extraction_method'].items():
        print(f"  {method.title()}: {count}")

if __name__ == "__main__":
    example_usage()