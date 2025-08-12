#!/usr/bin/env python3
"""
Event Extraction and Temporal Analysis System
Implements automatic event detection, temporal relationship analysis,
timeline visualization, action item extraction, and deadline detection
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from datetime import datetime, timedelta, date
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import pandas as pd
import json

# NLP libraries
import spacy
from spacy.tokens import Doc, Span, Token
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag

# Date parsing
import dateparser
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import parsedatetime as pdt

# Machine Learning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

# Transformers
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

# Visualization
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import networkx as nx

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events"""
    MEETING = "meeting"
    DEADLINE = "deadline"
    ACTION = "action"
    DECISION = "decision"
    MILESTONE = "milestone"
    ANNOUNCEMENT = "announcement"
    CHANGE = "change"
    ISSUE = "issue"
    TASK = "task"
    GENERAL = "general"


class TemporalRelation(Enum):
    """Temporal relationships between events"""
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    OVERLAPS = "overlaps"
    STARTS = "starts"
    FINISHES = "finishes"
    EQUALS = "equals"
    CONTAINS = "contains"
    SIMULTANEOUS = "simultaneous"


class Priority(Enum):
    """Priority levels for action items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TimeExpression:
    """Temporal expression in text"""
    text: str
    start_pos: int
    end_pos: int
    parsed_time: Optional[datetime] = None
    time_type: str = "DATE"  # DATE, TIME, DURATION, RELATIVE
    confidence: float = 0.0


@dataclass
class Event:
    """Extracted event"""
    event_id: str
    text: str
    event_type: EventType
    timestamp: Optional[datetime] = None
    duration: Optional[timedelta] = None
    participants: List[str] = field(default_factory=list)
    location: Optional[str] = None
    description: Optional[str] = None
    confidence: float = 0.0
    source_sentence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionItem:
    """Action item extracted from text"""
    action_id: str
    text: str
    assignee: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)
    context: Optional[str] = None
    confidence: float = 0.0


@dataclass
class TemporalLink:
    """Temporal relationship between events"""
    source_event: str
    target_event: str
    relation: TemporalRelation
    confidence: float = 0.0
    evidence: Optional[str] = None


@dataclass
class Timeline:
    """Timeline of events"""
    events: List[Event]
    links: List[TemporalLink]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    resolution: str = "day"  # hour, day, week, month
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventExtractionResult:
    """Complete event extraction result"""
    events: List[Event]
    action_items: List[ActionItem]
    timeline: Timeline
    temporal_expressions: List[TimeExpression]
    statistics: Dict[str, Any]
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventExtractor:
    """Main event extraction and temporal analysis system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize NLP models
        self._initialize_models()
        
        # Event patterns
        self.event_patterns = self._compile_event_patterns()
        
        # Temporal patterns
        self.temporal_patterns = self._compile_temporal_patterns()
        
        # Action patterns
        self.action_patterns = self._compile_action_patterns()
        
        # Initialize date parser
        self.date_parser = pdt.Calendar()
        
    def _initialize_models(self):
        """Initialize NLP models"""
        try:
            # SpaCy model with custom components
            self.nlp = spacy.load("en_core_web_sm")
            
            # Add custom entity ruler for events
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                patterns = self._get_entity_patterns()
                ruler.add_patterns(patterns)
            
            # Transformer models for advanced extraction
            if self.config.get('use_transformers', False):
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple"
                )
            
            logger.info("Event extraction models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    def _compile_event_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for event detection"""
        return {
            'meeting': re.compile(
                r'\b(meeting|conference|call|discussion|presentation|workshop|seminar)\b',
                re.IGNORECASE
            ),
            'deadline': re.compile(
                r'\b(deadline|due|expire|submit|deliver|complete by)\b',
                re.IGNORECASE
            ),
            'action': re.compile(
                r'\b(will|shall|must|need to|have to|should|action|task|todo|follow up)\b',
                re.IGNORECASE
            ),
            'decision': re.compile(
                r'\b(decided|agreed|approved|rejected|confirmed|resolved)\b',
                re.IGNORECASE
            ),
            'milestone': re.compile(
                r'\b(milestone|achievement|completion|launch|release|deployment)\b',
                re.IGNORECASE
            ),
            'change': re.compile(
                r'\b(change|update|modify|revise|alter|switch|transition)\b',
                re.IGNORECASE
            )
        }
    
    def _compile_temporal_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for temporal expressions"""
        return {
            'date': re.compile(
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
            ),
            'time': re.compile(
                r'\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\b',
                re.IGNORECASE
            ),
            'relative': re.compile(
                r'\b(today|tomorrow|yesterday|next|last|this|coming|following|previous)\s+\w+',
                re.IGNORECASE
            ),
            'duration': re.compile(
                r'\b(\d+)\s*(hour|day|week|month|year)s?\b',
                re.IGNORECASE
            ),
            'temporal_signal': re.compile(
                r'\b(before|after|during|while|when|until|since|by|at|on|in)\b',
                re.IGNORECASE
            )
        }
    
    def _compile_action_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for action item detection"""
        return {
            'action_verb': re.compile(
                r'\b(complete|finish|submit|review|prepare|send|create|update|check|verify|test|implement)\b',
                re.IGNORECASE
            ),
            'assignment': re.compile(
                r'(@\w+|\b(?:assigned to|owner:|responsible:)\s*\w+)',
                re.IGNORECASE
            ),
            'priority': re.compile(
                r'\b(urgent|critical|high priority|low priority|asap|important)\b',
                re.IGNORECASE
            )
        }
    
    def _get_entity_patterns(self) -> List[Dict[str, Any]]:
        """Get entity patterns for SpaCy entity ruler"""
        return [
            {"label": "EVENT", "pattern": [{"LOWER": "meeting"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "deadline"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "milestone"}]},
            {"label": "ACTION", "pattern": [{"LOWER": "action"}, {"LOWER": "item"}]},
            {"label": "ACTION", "pattern": [{"LOWER": "todo"}]},
            {"label": "ACTION", "pattern": [{"LOWER": "task"}]},
        ]
    
    async def extract_events(
        self,
        text: str,
        extract_actions: bool = True,
        build_timeline: bool = True,
        reference_date: Optional[datetime] = None
    ) -> EventExtractionResult:
        """Extract events and temporal information from text"""
        
        import time
        start_time = time.time()
        
        # Set reference date
        if reference_date is None:
            reference_date = datetime.now()
        
        # Extract temporal expressions
        temporal_expressions = self._extract_temporal_expressions(text, reference_date)
        
        # Extract events
        events = await self._extract_events(text, temporal_expressions, reference_date)
        
        # Extract action items
        action_items = []
        if extract_actions:
            action_items = self._extract_action_items(text, temporal_expressions, reference_date)
        
        # Build timeline
        timeline = None
        if build_timeline and events:
            timeline = self._build_timeline(events)
            
            # Analyze temporal relationships
            temporal_links = self._analyze_temporal_relations(events)
            timeline.links = temporal_links
        
        # Calculate statistics
        statistics = self._calculate_statistics(
            events,
            action_items,
            temporal_expressions
        )
        
        processing_time = time.time() - start_time
        
        return EventExtractionResult(
            events=events,
            action_items=action_items,
            timeline=timeline,
            temporal_expressions=temporal_expressions,
            statistics=statistics,
            processing_time=processing_time,
            metadata={
                'reference_date': reference_date.isoformat(),
                'text_length': len(text)
            }
        )
    
    def _extract_temporal_expressions(
        self,
        text: str,
        reference_date: datetime
    ) -> List[TimeExpression]:
        """Extract temporal expressions from text"""
        
        expressions = []
        
        # Extract dates using dateparser
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            # Try dateparser
            parsed = dateparser.search.search_dates(
                sentence,
                settings={
                    'RELATIVE_BASE': reference_date,
                    'PREFER_DATES_FROM': 'future'
                }
            )
            
            if parsed:
                for date_str, date_obj in parsed:
                    # Find position in original text
                    pos = text.find(date_str)
                    if pos != -1:
                        expressions.append(TimeExpression(
                            text=date_str,
                            start_pos=pos,
                            end_pos=pos + len(date_str),
                            parsed_time=date_obj,
                            time_type="DATE",
                            confidence=0.9
                        ))
            
            # Try parsedatetime
            time_struct, parse_status = self.date_parser.parse(
                sentence,
                sourceTime=reference_date
            )
            
            if parse_status > 0:
                # Convert to datetime
                parsed_dt = datetime(*time_struct[:6])
                
                # Find the temporal expression in the sentence
                for pattern_name, pattern in self.temporal_patterns.items():
                    matches = pattern.finditer(sentence)
                    for match in matches:
                        pos = text.find(match.group())
                        if pos != -1:
                            expressions.append(TimeExpression(
                                text=match.group(),
                                start_pos=pos,
                                end_pos=pos + len(match.group()),
                                parsed_time=parsed_dt,
                                time_type=pattern_name.upper(),
                                confidence=0.7
                            ))
        
        # Extract relative time expressions
        relative_pattern = self.temporal_patterns['relative']
        for match in relative_pattern.finditer(text):
            date_str = match.group()
            parsed = dateparser.parse(
                date_str,
                settings={'RELATIVE_BASE': reference_date}
            )
            
            if parsed:
                expressions.append(TimeExpression(
                    text=date_str,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    parsed_time=parsed,
                    time_type="RELATIVE",
                    confidence=0.8
                ))
        
        # Remove duplicates
        seen = set()
        unique_expressions = []
        for expr in expressions:
            key = (expr.start_pos, expr.end_pos)
            if key not in seen:
                seen.add(key)
                unique_expressions.append(expr)
        
        return sorted(unique_expressions, key=lambda x: x.start_pos)
    
    async def _extract_events(
        self,
        text: str,
        temporal_expressions: List[TimeExpression],
        reference_date: datetime
    ) -> List[Event]:
        """Extract events from text"""
        
        events = []
        doc = self.nlp(text)
        
        # Extract events from sentences
        for sent in doc.sents:
            # Check for event patterns
            event_type = self._detect_event_type(sent.text)
            
            if event_type:
                # Extract event details
                event = Event(
                    event_id=self._generate_id(),
                    text=sent.text.strip(),
                    event_type=event_type,
                    source_sentence=sent.text,
                    confidence=0.8
                )
                
                # Find associated time
                event_time = self._find_event_time(
                    sent.text,
                    temporal_expressions,
                    sent.start_char
                )
                if event_time:
                    event.timestamp = event_time
                
                # Extract participants (named entities)
                participants = []
                for ent in sent.ents:
                    if ent.label_ in ['PERSON', 'ORG']:
                        participants.append(ent.text)
                event.participants = participants
                
                # Extract location
                for ent in sent.ents:
                    if ent.label_ in ['LOC', 'GPE', 'FAC']:
                        event.location = ent.text
                        break
                
                events.append(event)
        
        # Extract events using NER pipeline if available
        if hasattr(self, 'ner_pipeline'):
            ner_results = self.ner_pipeline(text)
            
            for entity in ner_results:
                if entity['entity_group'] == 'EVENT':
                    # Check if not already extracted
                    if not any(entity['word'] in e.text for e in events):
                        events.append(Event(
                            event_id=self._generate_id(),
                            text=entity['word'],
                            event_type=EventType.GENERAL,
                            confidence=entity['score']
                        ))
        
        return events
    
    def _detect_event_type(self, text: str) -> Optional[EventType]:
        """Detect type of event from text"""
        
        text_lower = text.lower()
        
        # Check patterns
        if self.event_patterns['meeting'].search(text_lower):
            return EventType.MEETING
        elif self.event_patterns['deadline'].search(text_lower):
            return EventType.DEADLINE
        elif self.event_patterns['decision'].search(text_lower):
            return EventType.DECISION
        elif self.event_patterns['milestone'].search(text_lower):
            return EventType.MILESTONE
        elif self.event_patterns['change'].search(text_lower):
            return EventType.CHANGE
        elif self.event_patterns['action'].search(text_lower):
            return EventType.ACTION
        
        return None
    
    def _find_event_time(
        self,
        event_text: str,
        temporal_expressions: List[TimeExpression],
        offset: int = 0
    ) -> Optional[datetime]:
        """Find time associated with event"""
        
        # Look for temporal expression in or near event text
        for expr in temporal_expressions:
            # Check if expression is within event text
            if expr.start_pos >= offset and expr.end_pos <= offset + len(event_text):
                return expr.parsed_time
            
            # Check if expression is nearby (within 50 characters)
            if abs(expr.start_pos - offset) < 50:
                return expr.parsed_time
        
        return None
    
    def _extract_action_items(
        self,
        text: str,
        temporal_expressions: List[TimeExpression],
        reference_date: datetime
    ) -> List[ActionItem]:
        """Extract action items from text"""
        
        action_items = []
        doc = self.nlp(text)
        
        for sent in doc.sents:
            # Check for action patterns
            if self.action_patterns['action_verb'].search(sent.text):
                action = ActionItem(
                    action_id=self._generate_id(),
                    text=sent.text.strip(),
                    context=sent.text,
                    confidence=0.7
                )
                
                # Extract assignee
                assignee_match = self.action_patterns['assignment'].search(sent.text)
                if assignee_match:
                    action.assignee = assignee_match.group().strip('@').strip()
                else:
                    # Look for person entities
                    for ent in sent.ents:
                        if ent.label_ == 'PERSON':
                            action.assignee = ent.text
                            break
                
                # Extract deadline
                deadline = self._find_event_time(
                    sent.text,
                    temporal_expressions,
                    sent.start_char
                )
                if deadline:
                    action.deadline = deadline
                
                # Determine priority
                if self.action_patterns['priority'].search(sent.text.lower()):
                    if 'critical' in sent.text.lower() or 'urgent' in sent.text.lower():
                        action.priority = Priority.CRITICAL
                    elif 'high' in sent.text.lower():
                        action.priority = Priority.HIGH
                    elif 'low' in sent.text.lower():
                        action.priority = Priority.LOW
                
                action_items.append(action)
        
        # Extract from bullet points or numbered lists
        list_pattern = re.compile(r'^[\s]*[-*•]\s+(.+)$', re.MULTILINE)
        numbered_pattern = re.compile(r'^[\s]*\d+[.)]\s+(.+)$', re.MULTILINE)
        
        for pattern in [list_pattern, numbered_pattern]:
            for match in pattern.finditer(text):
                item_text = match.group(1)
                
                # Check if it's an action
                if self.action_patterns['action_verb'].search(item_text):
                    action = ActionItem(
                        action_id=self._generate_id(),
                        text=item_text.strip(),
                        confidence=0.8
                    )
                    
                    # Find deadline in item
                    for expr in temporal_expressions:
                        if expr.text in item_text and expr.parsed_time:
                            action.deadline = expr.parsed_time
                            break
                    
                    action_items.append(action)
        
        return action_items
    
    def _build_timeline(self, events: List[Event]) -> Timeline:
        """Build timeline from events"""
        
        # Filter events with timestamps
        timed_events = [e for e in events if e.timestamp]
        
        if not timed_events:
            return Timeline(events=events, links=[])
        
        # Sort by timestamp
        timed_events.sort(key=lambda e: e.timestamp)
        
        # Determine timeline range
        start_date = min(e.timestamp for e in timed_events)
        end_date = max(e.timestamp for e in timed_events)
        
        # Determine appropriate resolution
        duration = end_date - start_date
        
        if duration.days < 1:
            resolution = "hour"
        elif duration.days < 30:
            resolution = "day"
        elif duration.days < 365:
            resolution = "week"
        else:
            resolution = "month"
        
        return Timeline(
            events=timed_events,
            links=[],
            start_date=start_date,
            end_date=end_date,
            resolution=resolution
        )
    
    def _analyze_temporal_relations(
        self,
        events: List[Event]
    ) -> List[TemporalLink]:
        """Analyze temporal relationships between events"""
        
        links = []
        
        # Only analyze events with timestamps
        timed_events = [e for e in events if e.timestamp]
        
        for i, event1 in enumerate(timed_events):
            for event2 in timed_events[i+1:]:
                # Determine relationship
                relation = self._determine_temporal_relation(
                    event1.timestamp,
                    event2.timestamp,
                    event1.duration,
                    event2.duration
                )
                
                if relation:
                    links.append(TemporalLink(
                        source_event=event1.event_id,
                        target_event=event2.event_id,
                        relation=relation,
                        confidence=0.9
                    ))
        
        return links
    
    def _determine_temporal_relation(
        self,
        time1: datetime,
        time2: datetime,
        duration1: Optional[timedelta] = None,
        duration2: Optional[timedelta] = None
    ) -> TemporalRelation:
        """Determine temporal relationship between two time points"""
        
        if time1 == time2:
            return TemporalRelation.EQUALS
        elif time1 < time2:
            if duration1 and time1 + duration1 > time2:
                return TemporalRelation.OVERLAPS
            else:
                return TemporalRelation.BEFORE
        else:
            if duration2 and time2 + duration2 > time1:
                return TemporalRelation.OVERLAPS
            else:
                return TemporalRelation.AFTER
    
    def _calculate_statistics(
        self,
        events: List[Event],
        action_items: List[ActionItem],
        temporal_expressions: List[TimeExpression]
    ) -> Dict[str, Any]:
        """Calculate extraction statistics"""
        
        # Event statistics
        event_types = Counter(e.event_type.value for e in events)
        
        # Action item statistics
        priority_dist = Counter(a.priority.value for a in action_items)
        assigned_count = sum(1 for a in action_items if a.assignee)
        deadline_count = sum(1 for a in action_items if a.deadline)
        
        # Temporal statistics
        time_types = Counter(t.time_type for t in temporal_expressions)
        
        return {
            'event_count': len(events),
            'event_type_distribution': dict(event_types),
            'events_with_time': sum(1 for e in events if e.timestamp),
            'action_item_count': len(action_items),
            'priority_distribution': dict(priority_dist),
            'assigned_actions': assigned_count,
            'actions_with_deadline': deadline_count,
            'temporal_expression_count': len(temporal_expressions),
            'temporal_type_distribution': dict(time_types),
            'avg_confidence': np.mean([e.confidence for e in events]) if events else 0
        }
    
    def visualize_timeline(
        self,
        timeline: Timeline,
        output_path: Optional[str] = None,
        show_labels: bool = True
    ) -> plt.Figure:
        """Visualize event timeline"""
        
        if not timeline or not timeline.events:
            logger.warning("No events to visualize")
            return None
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Group events by type
        event_groups = defaultdict(list)
        for event in timeline.events:
            if event.timestamp:
                event_groups[event.event_type.value].append(event)
        
        # Assign colors to event types
        colors = plt.cm.Set3(np.linspace(0, 1, len(event_groups)))
        color_map = {event_type: colors[i] for i, event_type in enumerate(event_groups.keys())}
        
        # Plot events
        y_positions = {}
        y_counter = 0
        
        for event_type, events in event_groups.items():
            for event in events:
                # Assign y position
                if event_type not in y_positions:
                    y_positions[event_type] = y_counter
                    y_counter += 1
                
                y_pos = y_positions[event_type]
                
                # Plot event
                ax.scatter(
                    event.timestamp,
                    y_pos,
                    s=200,
                    c=[color_map[event_type]],
                    alpha=0.7,
                    edgecolors='black',
                    linewidth=1
                )
                
                # Add label if requested
                if show_labels:
                    label_text = event.text[:30] + "..." if len(event.text) > 30 else event.text
                    ax.annotate(
                        label_text,
                        (event.timestamp, y_pos),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=8,
                        alpha=0.7
                    )
        
        # Configure plot
        ax.set_yticks(list(y_positions.values()))
        ax.set_yticklabels(list(y_positions.keys()))
        ax.set_xlabel('Time')
        ax.set_title('Event Timeline')
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], s=100, c=color, alpha=0.7, label=event_type)
            for event_type, color in color_map.items()
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Add grid
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save or show
        if output_path:
            plt.savefig(output_path, dpi=100, bbox_inches='tight')
        
        return fig
    
    def export_calendar(
        self,
        events: List[Event],
        action_items: List[ActionItem],
        format: str = "ics"
    ) -> str:
        """Export events and actions to calendar format"""
        
        if format == "ics":
            # Generate iCalendar format
            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Event Extraction System//EN"
            ]
            
            # Add events
            for event in events:
                if event.timestamp:
                    lines.extend([
                        "BEGIN:VEVENT",
                        f"UID:{event.event_id}",
                        f"DTSTART:{event.timestamp.strftime('%Y%m%dT%H%M%S')}",
                        f"SUMMARY:{event.text[:50]}",
                        f"DESCRIPTION:{event.text}",
                        f"CATEGORIES:{event.event_type.value}",
                    ])
                    
                    if event.location:
                        lines.append(f"LOCATION:{event.location}")
                    
                    if event.participants:
                        lines.append(f"ATTENDEE:{';'.join(event.participants)}")
                    
                    lines.append("END:VEVENT")
            
            # Add action items as todos
            for action in action_items:
                lines.extend([
                    "BEGIN:VTODO",
                    f"UID:{action.action_id}",
                    f"SUMMARY:{action.text[:50]}",
                    f"DESCRIPTION:{action.text}",
                    f"PRIORITY:{self._priority_to_ical(action.priority)}",
                ])
                
                if action.deadline:
                    lines.append(f"DUE:{action.deadline.strftime('%Y%m%dT%H%M%S')}")
                
                if action.assignee:
                    lines.append(f"ORGANIZER:{action.assignee}")
                
                lines.append("END:VTODO")
            
            lines.append("END:VCALENDAR")
            
            return '\n'.join(lines)
        
        elif format == "json":
            # Export as JSON
            data = {
                'events': [
                    {
                        'id': e.event_id,
                        'text': e.text,
                        'type': e.event_type.value,
                        'timestamp': e.timestamp.isoformat() if e.timestamp else None,
                        'participants': e.participants,
                        'location': e.location
                    }
                    for e in events
                ],
                'action_items': [
                    {
                        'id': a.action_id,
                        'text': a.text,
                        'assignee': a.assignee,
                        'deadline': a.deadline.isoformat() if a.deadline else None,
                        'priority': a.priority.value,
                        'status': a.status
                    }
                    for a in action_items
                ]
            }
            
            return json.dumps(data, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _priority_to_ical(self, priority: Priority) -> int:
        """Convert priority to iCalendar priority value"""
        mapping = {
            Priority.CRITICAL: 1,
            Priority.HIGH: 3,
            Priority.MEDIUM: 5,
            Priority.LOW: 7
        }
        return mapping.get(priority, 5)
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())[:8]


# Example usage
async def main():
    """Example usage of event extraction system"""
    
    # Initialize extractor
    extractor = EventExtractor()
    
    # Sample text with events and temporal information
    text = """
    The quarterly review meeting is scheduled for next Monday at 2 PM in the main conference room.
    John and Sarah will present the Q3 results. The deadline for submitting the financial report
    is October 15th, 2024.
    
    Action items from today's discussion:
    - Sarah needs to complete the market analysis by Friday
    - John will review the budget proposal before the end of the week
    - The team must submit their timesheets by tomorrow 5 PM
    
    We agreed to launch the new product on November 1st. This is a critical milestone for
    our company. The marketing campaign will start two weeks before the launch date.
    
    Yesterday's security incident has been resolved. The system was down for 2 hours but
    is now fully operational. We decided to implement additional monitoring going forward.
    """
    
    # Extract events
    result = await extractor.extract_events(
        text,
        extract_actions=True,
        build_timeline=True,
        reference_date=datetime(2024, 10, 1)
    )
    
    # Print results
    print(f"Extracted {len(result.events)} events:")
    for event in result.events:
        print(f"  - {event.event_type.value}: {event.text[:50]}...")
        if event.timestamp:
            print(f"    Time: {event.timestamp}")
        if event.participants:
            print(f"    Participants: {', '.join(event.participants)}")
    
    print(f"\nExtracted {len(result.action_items)} action items:")
    for action in result.action_items:
        print(f"  - {action.text[:50]}...")
        if action.assignee:
            print(f"    Assignee: {action.assignee}")
        if action.deadline:
            print(f"    Deadline: {action.deadline}")
        print(f"    Priority: {action.priority.value}")
    
    print(f"\nTemporal expressions found: {len(result.temporal_expressions)}")
    for expr in result.temporal_expressions:
        print(f"  - '{expr.text}' -> {expr.parsed_time}")
    
    print(f"\nStatistics:")
    for key, value in result.statistics.items():
        print(f"  {key}: {value}")
    
    # Visualize timeline
    if result.timeline:
        fig = extractor.visualize_timeline(result.timeline, "event_timeline.png")
        print("\nTimeline visualization saved")
    
    # Export to calendar
    ics_content = extractor.export_calendar(
        result.events,
        result.action_items,
        format="ics"
    )
    print(f"\nCalendar export generated ({len(ics_content)} characters)")


if __name__ == "__main__":
    asyncio.run(main())