#!/usr/bin/env python3
"""
MOM (Minutes of Meeting) Template Engine
Advanced template system for generating professional meeting minutes from extracted meeting data
"""

import re
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import os
import sys
from pathlib import Path
from jinja2 import Environment, BaseLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateSyntaxError

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_element_identification import (
    MeetingStructure,
    MeetingElement,
    MeetingElementType,
    ConfidenceLevel
)

from action_item_extraction_system import (
    ActionItem,
    ActionItemPriority,
    ActionItemStatus,
    DeadlineType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MOMFormat(Enum):
    """Supported MOM output formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    PLAIN_TEXT = "plain_text"
    JSON = "json"
    DOCX = "docx"
    PDF = "pdf"

class MOMStyle(Enum):
    """Different MOM styles/templates"""
    CORPORATE = "corporate"
    ACADEMIC = "academic"
    AGILE = "agile"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    SIMPLE = "simple"
    DETAILED = "detailed"

class TemplateValidationLevel(Enum):
    """Template validation levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"

@dataclass
class MOMConfiguration:
    """Configuration for MOM generation"""
    format: MOMFormat = MOMFormat.MARKDOWN
    style: MOMStyle = MOMStyle.CORPORATE
    include_timestamps: bool = True
    include_speaker_names: bool = True
    include_confidence_scores: bool = False
    group_by_topic: bool = True
    show_action_item_details: bool = True
    show_decision_rationale: bool = True
    include_attendance: bool = True
    include_summary: bool = True
    max_content_length: Optional[int] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    template_variables: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MOMSection:
    """Represents a section in the MOM"""
    title: str
    content: List[str] = field(default_factory=list)
    subsections: List['MOMSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    
    def add_content(self, content: str):
        """Add content to the section"""
        self.content.append(content)
    
    def add_subsection(self, subsection: 'MOMSection'):
        """Add a subsection"""
        self.subsections.append(subsection)
        # Sort subsections by order
        self.subsections.sort(key=lambda s: s.order)

@dataclass
class MOMDocument:
    """Complete MOM document structure"""
    title: str
    meeting_id: str
    date: Optional[datetime] = None
    duration: Optional[float] = None
    attendees: List[str] = field(default_factory=list)
    sections: List[MOMSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    
    def add_section(self, section: MOMSection):
        """Add a section to the document"""
        self.sections.append(section)
        # Sort sections by order
        self.sections.sort(key=lambda s: s.order)
    
    def get_section(self, title: str) -> Optional[MOMSection]:
        """Get a section by title"""
        for section in self.sections:
            if section.title == title:
                return section
        return None

class TemplateLoader(BaseLoader):
    """Custom template loader for MOM templates"""
    
    def __init__(self, template_dir: Optional[str] = None):
        self.template_dir = template_dir or os.path.join(os.path.dirname(__file__), 'templates')
        self.builtin_templates = self._load_builtin_templates()
    
    def get_source(self, environment, template):
        """Get template source"""
        # First try to load from file system
        if self.template_dir and os.path.exists(self.template_dir):
            template_path = os.path.join(self.template_dir, f"{template}.j2")
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    source = f.read()
                mtime = os.path.getmtime(template_path)
                return source, template_path, lambda: mtime == os.path.getmtime(template_path)
        
        # Fall back to builtin templates
        if template in self.builtin_templates:
            source = self.builtin_templates[template]
            return source, template, lambda: True
        
        raise TemplateError(f"Template '{template}' not found")
    
    def _load_builtin_templates(self) -> Dict[str, str]:
        """Load builtin templates"""
        return {
            'corporate_markdown': self._get_corporate_markdown_template(),
            'corporate_html': self._get_corporate_html_template(),
            'agile_markdown': self._get_agile_markdown_template(),
            'executive_markdown': self._get_executive_markdown_template(),
            'technical_markdown': self._get_technical_markdown_template(),
            'simple_plain_text': self._get_simple_plain_text_template(),
            'detailed_markdown': self._get_detailed_markdown_template()
        }
    
    def _get_corporate_markdown_template(self) -> str:
        """Corporate style markdown template"""
        return '''# Meeting Minutes: {{ title }}

**Meeting ID:** {{ meeting_id }}  
**Date:** {{ date.strftime('%B %d, %Y') if date else 'Not specified' }}  
**Time:** {{ date.strftime('%I:%M %p') if date else 'Not specified' }}  
{% if duration %}**Duration:** {{ "%.0f"|format(duration) }} minutes{% endif %}

## Attendees
{% for attendee in attendees %}
- {{ attendee }}
{% endfor %}

{% if summary_section %}
## Executive Summary
{{ summary_section.content | join('\\n\\n') }}
{% endif %}

{% if agenda_section %}
## Agenda Items Discussed
{% for item in agenda_section.content %}
{{ loop.index }}. {{ item }}
{% endfor %}
{% endif %}

{% if decisions_section %}
## Decisions Made
{% for decision in decisions_section.content %}
**Decision {{ loop.index }}:** {{ decision }}
{% endfor %}
{% endif %}

{% if action_items_section %}
## Action Items
{% for action in action_items_section.content %}
### {{ action.content }}
- **Assignee:** {{ action.assignees | map(attribute='name') | join(', ') if action.assignees else 'Unassigned' }}
- **Priority:** {{ action.priority.value.title() }}
{% if action.deadline %}
- **Deadline:** {{ action.deadline.original_text }}
{% endif %}
{% if action.tags %}
- **Tags:** {{ action.tags | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}

{% if discussions_section %}
## Key Discussion Points
{% for discussion in discussions_section.content %}
- {{ discussion }}
{% endfor %}
{% endif %}

{% if next_steps_section %}
## Next Steps
{{ next_steps_section.content | join('\\n\\n') }}
{% endif %}

---
*Minutes generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}*
'''
    
    def _get_corporate_html_template(self) -> str:
        """Corporate style HTML template"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Minutes: {{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .meeting-info { background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin-bottom: 25px; }
        .section h2 { color: #333; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
        .action-item { background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }
        .decision { background-color: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; }
        .priority-high { border-left-color: #dc3545; }
        .priority-medium { border-left-color: #ffc107; }
        .priority-low { border-left-color: #28a745; }
        .footer { margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Meeting Minutes: {{ title }}</h1>
    </div>
    
    <div class="meeting-info">
        <p><strong>Meeting ID:</strong> {{ meeting_id }}</p>
        <p><strong>Date:</strong> {{ date.strftime('%B %d, %Y') if date else 'Not specified' }}</p>
        <p><strong>Time:</strong> {{ date.strftime('%I:%M %p') if date else 'Not specified' }}</p>
        {% if duration %}<p><strong>Duration:</strong> {{ "%.0f"|format(duration) }} minutes</p>{% endif %}
    </div>
    
    <div class="section">
        <h2>Attendees</h2>
        <ul>
        {% for attendee in attendees %}
            <li>{{ attendee }}</li>
        {% endfor %}
        </ul>
    </div>
    
    {% if decisions_section %}
    <div class="section">
        <h2>Decisions Made</h2>
        {% for decision in decisions_section.content %}
        <div class="decision">
            <strong>Decision {{ loop.index }}:</strong> {{ decision }}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% if action_items_section %}
    <div class="section">
        <h2>Action Items</h2>
        {% for action in action_items_section.content %}
        <div class="action-item priority-{{ action.priority.value }}">
            <h3>{{ action.content }}</h3>
            <p><strong>Assignee:</strong> {{ action.assignees | map(attribute='name') | join(', ') if action.assignees else 'Unassigned' }}</p>
            <p><strong>Priority:</strong> {{ action.priority.value.title() }}</p>
            {% if action.deadline %}
            <p><strong>Deadline:</strong> {{ action.deadline.original_text }}</p>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <div class="footer">
        <p>Minutes generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}</p>
    </div>
</body>
</html>'''
    
    def _get_agile_markdown_template(self) -> str:
        """Agile/Scrum style markdown template"""
        return '''# 🚀 {{ title }}

**Sprint/Meeting:** {{ meeting_id }}  
**Date:** {{ date.strftime('%Y-%m-%d') if date else 'TBD' }}  
**Team:** {{ attendees | join(', ') }}

## 🎯 Sprint Goals & Objectives
{% if summary_section %}
{{ summary_section.content | join('\\n') }}
{% endif %}

## 📋 Backlog Items Discussed
{% if agenda_section %}
{% for item in agenda_section.content %}
- [ ] {{ item }}
{% endfor %}
{% endif %}

## ✅ Decisions & Commitments
{% if decisions_section %}
{% for decision in decisions_section.content %}
- ✅ {{ decision }}
{% endfor %}
{% endif %}

## 📝 Action Items & User Stories
{% if action_items_section %}
{% for action in action_items_section.content %}
### 🎫 {{ action.content }}
**Assignee:** @{{ action.assignees | map(attribute='name') | join(', @') if action.assignees else 'unassigned' }}  
**Priority:** {{ '🔴 HIGH' if action.priority.value == 'high' else '🟡 MEDIUM' if action.priority.value == 'medium' else '🟢 LOW' }}  
{% if action.deadline %}**Sprint Deadline:** {{ action.deadline.original_text }}{% endif %}

{% endfor %}
{% endif %}

## 🔄 Next Sprint Planning
{% if next_steps_section %}
{{ next_steps_section.content | join('\\n') }}
{% endif %}

---
*Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M') }} | Next standup: TBD*
'''
    
    def _get_executive_markdown_template(self) -> str:
        """Executive summary style template"""
        return '''# Executive Meeting Summary
## {{ title }}

**Date:** {{ date.strftime('%B %d, %Y') if date else 'Not specified' }}  
**Participants:** {{ attendees | length }} attendees  
{% if duration %}**Duration:** {{ "%.0f"|format(duration) }} minutes{% endif %}

### Key Outcomes
{% if decisions_section %}
{% for decision in decisions_section.content %}
• {{ decision }}
{% endfor %}
{% endif %}

### Critical Action Items
{% if action_items_section %}
{% for action in action_items_section.content %}
{% if action.priority.value in ['critical', 'high'] %}
**{{ action.content }}**  
Owner: {{ action.assignees | map(attribute='name') | join(', ') if action.assignees else 'TBD' }}  
{% if action.deadline %}Due: {{ action.deadline.original_text }}{% endif %}

{% endif %}
{% endfor %}
{% endif %}

### Strategic Discussion Points
{% if discussions_section %}
{% for discussion in discussions_section.content %}
- {{ discussion }}
{% endfor %}
{% endif %}

### Next Steps
{% if next_steps_section %}
{{ next_steps_section.content | join('\\n') }}
{% endif %}

---
*Confidential - Executive Summary*
'''
    
    def _get_technical_markdown_template(self) -> str:
        """Technical meeting template"""
        return '''# 🔧 Technical Meeting: {{ title }}

**Meeting ID:** `{{ meeting_id }}`  
**Date:** {{ date.strftime('%Y-%m-%d %H:%M UTC') if date else 'TBD' }}  
**Participants:** {{ attendees | join(', ') }}

## 📊 Technical Decisions
{% if decisions_section %}
{% for decision in decisions_section.content %}
```
DECISION: {{ decision }}
```
{% endfor %}
{% endif %}

## 🎯 Implementation Tasks
{% if action_items_section %}
{% for action in action_items_section.content %}
### `{{ action.content }}`
- **Assignee:** `{{ action.assignees | map(attribute='name') | join('`, `') if action.assignees else 'unassigned' }}`
- **Priority:** `{{ action.priority.value.upper() }}`
{% if action.deadline %}
- **Deadline:** `{{ action.deadline.original_text }}`
{% endif %}
{% if action.tags %}
- **Tags:** {{ action.tags | map('upper') | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}

## 🔍 Technical Discussion
{% if discussions_section %}
{% for discussion in discussions_section.content %}
- {{ discussion }}
{% endfor %}
{% endif %}

## 📋 Architecture & Design Notes
{% if agenda_section %}
{% for item in agenda_section.content %}
- {{ item }}
{% endfor %}
{% endif %}

---
*Technical documentation generated {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}*
'''
    
    def _get_simple_plain_text_template(self) -> str:
        """Simple plain text template"""
        return '''MEETING MINUTES: {{ title | upper }}

Meeting ID: {{ meeting_id }}
Date: {{ date.strftime('%B %d, %Y') if date else 'Not specified' }}
{% if duration %}Duration: {{ "%.0f"|format(duration) }} minutes{% endif %}

ATTENDEES:
{% for attendee in attendees %}
- {{ attendee }}
{% endfor %}

{% if decisions_section %}
DECISIONS:
{% for decision in decisions_section.content %}
{{ loop.index }}. {{ decision }}
{% endfor %}

{% endif %}
{% if action_items_section %}
ACTION ITEMS:
{% for action in action_items_section.content %}
{{ loop.index }}. {{ action.content }}
   Assignee: {{ action.assignees | map(attribute='name') | join(', ') if action.assignees else 'Unassigned' }}
   Priority: {{ action.priority.value.upper() }}
{% if action.deadline %}   Deadline: {{ action.deadline.original_text }}{% endif %}

{% endfor %}
{% endif %}
{% if discussions_section %}
DISCUSSION POINTS:
{% for discussion in discussions_section.content %}
- {{ discussion }}
{% endfor %}

{% endif %}
Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}
'''
    
    def _get_detailed_markdown_template(self) -> str:
        """Detailed comprehensive template"""
        return '''# 📋 Detailed Meeting Minutes: {{ title }}

## Meeting Information
- **Meeting ID:** {{ meeting_id }}
- **Date & Time:** {{ date.strftime('%A, %B %d, %Y at %I:%M %p') if date else 'Not specified' }}
{% if duration %}- **Duration:** {{ "%.0f"|format(duration) }} minutes ({{ "%.1f"|format(duration/60) }} hours){% endif %}
- **Meeting Type:** {{ metadata.get('meeting_type', 'Regular Meeting') }}
- **Location:** {{ metadata.get('location', 'Virtual/Online') }}

## 👥 Attendance ({{ attendees | length }} participants)
{% for attendee in attendees %}
- {{ attendee }}
{% endfor %}

{% if summary_section %}
## 📝 Executive Summary
{{ summary_section.content | join('\\n\\n') }}
{% endif %}

{% if agenda_section %}
## 📋 Agenda Items Covered
{% for item in agenda_section.content %}
### {{ loop.index }}. {{ item }}
{% if include_timestamps %}*Discussed at: [timestamp]*{% endif %}
{% endfor %}
{% endif %}

{% if decisions_section %}
## ✅ Decisions Made
{% for decision in decisions_section.content %}
### Decision {{ loop.index }}
**Resolution:** {{ decision }}
{% if show_decision_rationale %}
**Rationale:** [Decision reasoning would be captured here]
{% endif %}
**Status:** Approved
**Effective Date:** {{ date.strftime('%Y-%m-%d') if date else 'Immediate' }}

{% endfor %}
{% endif %}

{% if action_items_section %}
## 🎯 Action Items & Assignments
{% for action in action_items_section.content %}
### Action Item {{ loop.index }}: {{ action.content }}

| Field | Details |
|-------|---------|
| **Assignee(s)** | {{ action.assignees | map(attribute='name') | join(', ') if action.assignees else '⚠️ Unassigned' }} |
| **Priority** | {{ '🔴 ' + action.priority.value.title() if action.priority.value == 'high' else '🟡 ' + action.priority.value.title() if action.priority.value == 'medium' else '🟢 ' + action.priority.value.title() }} |
| **Status** | {{ action.status.value.title() }} |
{% if action.deadline %}| **Deadline** | {{ action.deadline.original_text }} |{% endif %}
{% if action.tags %}| **Tags** | {{ action.tags | join(', ') }} |{% endif %}
| **Confidence** | {{ "%.0f"|format(action.confidence * 100) }}% |

{% if action.dependencies %}
**Dependencies:** {{ action.dependencies | length }} related item(s)
{% endif %}

{% endfor %}
{% endif %}

{% if discussions_section %}
## 💬 Key Discussion Points
{% for discussion in discussions_section.content %}
- {{ discussion }}
{% endfor %}
{% endif %}

{% if next_steps_section %}
## 🔄 Next Steps & Follow-up
{{ next_steps_section.content | join('\\n\\n') }}
{% endif %}

## 📊 Meeting Statistics
- **Total Elements Identified:** {{ metadata.get('total_elements', 'N/A') }}
- **Action Items Created:** {{ action_items_section.content | length if action_items_section else 0 }}
- **Decisions Made:** {{ decisions_section.content | length if decisions_section else 0 }}
- **Average Confidence:** {{ "%.0f"|format((metadata.get('average_confidence', 0) * 100)) }}%

---
**Document Information:**
- *Generated:* {{ generated_at.strftime('%A, %B %d, %Y at %I:%M %p') }}
- *Generator:* MOM Template Engine v1.0
- *Format:* Detailed Markdown
{% if include_confidence_scores %}
- *Note:* Confidence scores indicate the reliability of automated extraction
{% endif %}
'''

class MOMTemplateEngine:
    """Main template engine for generating MOM documents"""
    
    def __init__(self, template_dir: Optional[str] = None, validation_level: TemplateValidationLevel = TemplateValidationLevel.MODERATE):
        self.template_loader = TemplateLoader(template_dir)
        self.validation_level = validation_level
        self.jinja_env = Environment(
            loader=self.template_loader,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_custom_filters()
        
        # Template cache
        self.template_cache = {}
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters"""
        
        def format_duration(minutes):
            """Format duration in minutes to human readable format"""
            if not minutes:
                return "N/A"
            
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            
            if hours > 0:
                return f"{hours}h {mins}m"
            else:
                return f"{mins}m"
        
        def format_priority(priority):
            """Format priority with icons"""
            priority_map = {
                'critical': '🔴 CRITICAL',
                'high': '🟠 HIGH',
                'medium': '🟡 MEDIUM',
                'low': '🟢 LOW',
                'unspecified': '⚪ UNSPECIFIED'
            }
            return priority_map.get(priority.lower(), priority.upper())
        
        def format_confidence(confidence):
            """Format confidence score"""
            if confidence >= 0.9:
                return f"🟢 {confidence:.0%}"
            elif confidence >= 0.7:
                return f"🟡 {confidence:.0%}"
            else:
                return f"🔴 {confidence:.0%}"
        
        def truncate_smart(text, length=100):
            """Smart truncation that respects word boundaries"""
            if len(text) <= length:
                return text
            
            truncated = text[:length]
            last_space = truncated.rfind(' ')
            if last_space > length * 0.8:  # If we can find a space in the last 20%
                truncated = truncated[:last_space]
            
            return truncated + "..."
        
        def group_by_priority(action_items):
            """Group action items by priority"""
            groups = {
                'critical': [],
                'high': [],
                'medium': [],
                'low': [],
                'unspecified': []
            }
            
            for item in action_items:
                priority = item.priority.value if hasattr(item, 'priority') else 'unspecified'
                groups[priority].append(item)
            
            return groups
        
        # Register filters
        self.jinja_env.filters['format_duration'] = format_duration
        self.jinja_env.filters['format_priority'] = format_priority
        self.jinja_env.filters['format_confidence'] = format_confidence
        self.jinja_env.filters['truncate_smart'] = truncate_smart
        self.jinja_env.filters['group_by_priority'] = group_by_priority
    
    def generate_mom(self, meeting: MeetingStructure, action_items: List[ActionItem], 
                     config: MOMConfiguration = None) -> MOMDocument:
        """Generate MOM document from meeting data"""
        
        config = config or MOMConfiguration()
        
        # Create MOM document structure
        mom_doc = MOMDocument(
            title=meeting.title or f"Meeting {meeting.meeting_id}",
            meeting_id=meeting.meeting_id,
            date=meeting.date,
            duration=meeting.duration,
            attendees=meeting.attendees,
            metadata={
                'total_elements': len(meeting.elements),
                'average_confidence': sum(e.confidence for e in meeting.elements) / len(meeting.elements) if meeting.elements else 0,
                'generation_config': config,
                'meeting_type': config.custom_fields.get('meeting_type', 'Regular Meeting'),
                'location': config.custom_fields.get('location', 'Virtual/Online')
            }
        )
        
        # Build sections
        self._build_sections(mom_doc, meeting, action_items, config)
        
        return mom_doc
    
    def _build_sections(self, mom_doc: MOMDocument, meeting: MeetingStructure, 
                       action_items: List[ActionItem], config: MOMConfiguration):
        """Build MOM sections from meeting data"""
        
        # Summary section
        if config.include_summary:
            summary_section = MOMSection(
                title="Summary",
                order=1,
                metadata={'type': 'summary'}
            )
            
            # Generate summary content
            summary_content = self._generate_summary(meeting, action_items)
            summary_section.add_content(summary_content)
            mom_doc.add_section(summary_section)
        
        # Agenda items section
        if meeting.agenda_items:
            agenda_section = MOMSection(
                title="Agenda Items",
                order=2,
                metadata={'type': 'agenda'}
            )
            
            for item in meeting.agenda_items:
                content = item.content
                if config.include_speaker_names and item.speaker:
                    content = f"{content} (Presented by: {item.speaker})"
                if config.include_timestamps and item.start_time:
                    content = f"{content} [{self._format_timestamp(item.start_time)}]"
                
                agenda_section.add_content(content)
            
            mom_doc.add_section(agenda_section)
        
        # Decisions section
        if meeting.decisions:
            decisions_section = MOMSection(
                title="Decisions Made",
                order=3,
                metadata={'type': 'decisions'}
            )
            
            for decision in meeting.decisions:
                content = decision.content
                if config.show_decision_rationale and config.include_speaker_names and decision.speaker:
                    content = f"{content} (Decided by: {decision.speaker})"
                
                decisions_section.add_content(content)
            
            mom_doc.add_section(decisions_section)
        
        # Action items section
        if action_items:
            action_items_section = MOMSection(
                title="Action Items",
                order=4,
                metadata={'type': 'action_items', 'items': action_items}
            )
            
            # Group action items if requested
            if config.group_by_topic:
                grouped_items = self._group_action_items_by_topic(action_items)
                for topic, items in grouped_items.items():
                    subsection = MOMSection(
                        title=topic,
                        order=len(action_items_section.subsections),
                        metadata={'type': 'action_group', 'items': items}
                    )
                    action_items_section.add_subsection(subsection)
            else:
                # Store action items in section metadata for template access
                action_items_section.content = action_items
            
            mom_doc.add_section(action_items_section)
        
        # Discussion points section
        if meeting.discussions:
            discussions_section = MOMSection(
                title="Discussion Points",
                order=5,
                metadata={'type': 'discussions'}
            )
            
            for discussion in meeting.discussions:
                content = discussion.content
                if config.include_speaker_names and discussion.speaker:
                    content = f"{content} ({discussion.speaker})"
                
                discussions_section.add_content(content)
            
            mom_doc.add_section(discussions_section)
        
        # Next steps section
        next_steps_section = MOMSection(
            title="Next Steps",
            order=6,
            metadata={'type': 'next_steps'}
        )
        
        # Generate next steps from follow-up elements and future action items
        follow_ups = meeting.get_elements_by_type(MeetingElementType.FOLLOW_UP)
        if follow_ups:
            for follow_up in follow_ups:
                next_steps_section.add_content(follow_up.content)
        
        # Add future meetings or deadlines
        future_deadlines = [a for a in action_items if a.deadline and not a.is_overdue()]
        if future_deadlines:
            next_steps_section.add_content(f"Upcoming deadlines: {len(future_deadlines)} action items due")
        
        if next_steps_section.content:
            mom_doc.add_section(next_steps_section)
    
    def _generate_summary(self, meeting: MeetingStructure, action_items: List[ActionItem]) -> str:
        """Generate executive summary"""
        summary_parts = []
        
        # Meeting overview
        if meeting.attendees:
            summary_parts.append(f"Meeting held with {len(meeting.attendees)} participants.")
        
        # Key outcomes
        if meeting.decisions:
            summary_parts.append(f"{len(meeting.decisions)} key decisions were made.")
        
        if action_items:
            high_priority_count = len([a for a in action_items if a.priority in [ActionItemPriority.CRITICAL, ActionItemPriority.HIGH]])
            summary_parts.append(f"{len(action_items)} action items assigned ({high_priority_count} high priority).")
        
        # Discussion topics
        if meeting.agenda_items:
            summary_parts.append(f"{len(meeting.agenda_items)} agenda items were discussed.")
        
        return " ".join(summary_parts)
    
    def _group_action_items_by_topic(self, action_items: List[ActionItem]) -> Dict[str, List[ActionItem]]:
        """Group action items by topic/category"""
        groups = {
            'Technical Tasks': [],
            'Business Tasks': [],
            'Communication Tasks': [],
            'Process Tasks': [],
            'Other Tasks': []
        }
        
        for item in action_items:
            # Categorize based on tags or content
            if any(tag.startswith('tech:') for tag in item.tags):
                groups['Technical Tasks'].append(item)
            elif any(tag.startswith('business:') for tag in item.tags):
                groups['Business Tasks'].append(item)
            elif any(tag.startswith('communication:') for tag in item.tags):
                groups['Communication Tasks'].append(item)
            elif any(tag.startswith('process:') for tag in item.tags):
                groups['Process Tasks'].append(item)
            else:
                groups['Other Tasks'].append(item)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _format_timestamp(self, minutes: float) -> str:
        """Format timestamp from minutes"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"
    
    def render_mom(self, mom_doc: MOMDocument, config: MOMConfiguration = None) -> str:
        """Render MOM document to specified format"""
        
        config = config or MOMConfiguration()
        
        # Determine template name
        template_name = f"{config.style.value}_{config.format.value}"
        
        try:
            # Get template
            template = self._get_template(template_name)
            
            # Prepare template context
            context = self._prepare_template_context(mom_doc, config)
            
            # Render template
            rendered = template.render(**context)
            
            # Post-process if needed
            rendered = self._post_process_output(rendered, config)
            
            return rendered
            
        except TemplateError as e:
            logger.error(f"Template error: {e}")
            # Fall back to simple template
            return self._render_fallback(mom_doc, config)
        except Exception as e:
            logger.error(f"Rendering error: {e}")
            raise
    
    def _get_template(self, template_name: str) -> Template:
        """Get template by name with caching"""
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        try:
            template = self.jinja_env.get_template(template_name)
            self.template_cache[template_name] = template
            return template
        except TemplateError:
            # Try fallback template names
            fallback_names = [
                f"simple_{template_name.split('_')[-1]}",  # simple_markdown
                "simple_plain_text"  # ultimate fallback
            ]
            
            for fallback in fallback_names:
                try:
                    template = self.jinja_env.get_template(fallback)
                    self.template_cache[template_name] = template
                    return template
                except TemplateError:
                    continue
            
            raise TemplateError(f"No suitable template found for {template_name}")
    
    def _prepare_template_context(self, mom_doc: MOMDocument, config: MOMConfiguration) -> Dict[str, Any]:
        """Prepare context for template rendering"""
        
        # Base context
        context = {
            'title': mom_doc.title,
            'meeting_id': mom_doc.meeting_id,
            'date': mom_doc.date,
            'duration': mom_doc.duration,
            'attendees': mom_doc.attendees,
            'generated_at': mom_doc.generated_at,
            'metadata': mom_doc.metadata,
            'config': config,
            'include_timestamps': config.include_timestamps,
            'include_speaker_names': config.include_speaker_names,
            'include_confidence_scores': config.include_confidence_scores,
            'show_action_item_details': config.show_action_item_details,
            'show_decision_rationale': config.show_decision_rationale
        }
        
        # Add sections
        for section in mom_doc.sections:
            section_key = f"{section.title.lower().replace(' ', '_')}_section"
            context[section_key] = section
        
        # Add custom template variables
        context.update(config.template_variables)
        
        return context
    
    def _post_process_output(self, rendered: str, config: MOMConfiguration) -> str:
        """Post-process rendered output"""
        
        # Trim excessive whitespace
        rendered = re.sub(r'\n\s*\n\s*\n', '\n\n', rendered)
        
        # Apply content length limit if specified
        if config.max_content_length and len(rendered) > config.max_content_length:
            rendered = rendered[:config.max_content_length] + "\n\n[Content truncated due to length limit]"
        
        return rendered.strip()
    
    def _render_fallback(self, mom_doc: MOMDocument, config: MOMConfiguration) -> str:
        """Render using fallback template when main template fails"""
        
        fallback_template = '''Meeting Minutes: {{ title }}

Meeting ID: {{ meeting_id }}
Date: {{ date.strftime('%Y-%m-%d') if date else 'Not specified' }}
Attendees: {{ attendees | join(', ') }}

{% if decisions_section %}
DECISIONS:
{% for decision in decisions_section.content %}
- {{ decision }}
{% endfor %}

{% endif %}
{% if action_items_section %}
ACTION ITEMS:
{% for action in action_items_section.content %}
- {{ action.content }} ({{ action.assignees | map(attribute='name') | join(', ') if action.assignees else 'Unassigned' }})
{% endfor %}

{% endif %}
Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }}
'''
        
        template = Template(fallback_template)
        context = self._prepare_template_context(mom_doc, config)
        return template.render(**context)
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template syntax and structure"""
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Parse template
            template = Template(template_content)
            
            # Check for required variables
            required_vars = ['title', 'meeting_id', 'date', 'attendees']
            template_vars = template.new_context().parent.keys()
            
            for var in required_vars:
                if var not in template_content:
                    validation_result['warnings'].append(f"Template may be missing required variable: {var}")
            
            # Check for common issues
            if '{{' in template_content and '}}' not in template_content:
                validation_result['errors'].append("Unclosed template variable")
                validation_result['valid'] = False
            
            if '{%' in template_content and '%}' not in template_content:
                validation_result['errors'].append("Unclosed template block")
                validation_result['valid'] = False
            
        except TemplateSyntaxError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Template syntax error: {e}")
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Template validation error: {e}")
        
        return validation_result
    
    def list_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """List all available templates"""
        
        templates = {}
        
        # Builtin templates
        for template_name in self.template_loader.builtin_templates.keys():
            style, format_type = template_name.split('_', 1)
            templates[template_name] = {
                'name': template_name,
                'style': style,
                'format': format_type,
                'builtin': True,
                'description': f"{style.title()} style {format_type.replace('_', ' ').title()} template"
            }
        
        # Custom templates from file system
        if self.template_loader.template_dir and os.path.exists(self.template_loader.template_dir):
            for filename in os.listdir(self.template_loader.template_dir):
                if filename.endswith('.j2'):
                    template_name = filename[:-3]  # Remove .j2 extension
                    templates[template_name] = {
                        'name': template_name,
                        'style': 'custom',
                        'format': 'custom',
                        'builtin': False,
                        'description': f"Custom template: {template_name}",
                        'path': os.path.join(self.template_loader.template_dir, filename)
                    }
        
        return templates

# Utility functions
def create_mom_template_engine(template_dir: Optional[str] = None) -> MOMTemplateEngine:
    """Create a MOM template engine"""
    return MOMTemplateEngine(template_dir)

def generate_mom_from_meeting(meeting: MeetingStructure, action_items: List[ActionItem], 
                             config: MOMConfiguration = None) -> str:
    """Generate MOM document from meeting data"""
    engine = create_mom_template_engine()
    mom_doc = engine.generate_mom(meeting, action_items, config)
    return engine.render_mom(mom_doc, config)

# Example usage
def example_usage():
    """Example usage of MOM template engine"""
    from meeting_element_identification import analyze_meeting_transcript
    from action_item_extraction_system import extract_action_items_from_meeting
    
    # Sample meeting transcript
    sample_transcript = """
[14:00] Project Manager: Welcome to our sprint planning meeting.
[14:02] Project Manager: Let's review our sprint goals and assign tasks.
[14:05] Developer: I can take on the user authentication feature.
[14:07] Project Manager: Great. John, can you implement the dashboard by Friday?
[14:08] John: Sure, I'll have the dashboard ready by Friday.
[14:10] Project Manager: We've decided to use React for the frontend.
[14:12] Designer: I'll create the UI mockups by Wednesday.
[14:15] Project Manager: Action item for Sarah - set up the testing environment.
[14:16] Sarah: I'll configure the test environment by Thursday.
[14:18] Project Manager: Any questions before we wrap up?
[14:20] Project Manager: Great. Next meeting is scheduled for next Monday.
    """
    
    # Analyze meeting
    context = {
        'meeting_id': 'sprint_planning_2024',
        'title': 'Sprint Planning Meeting',
        'date': datetime(2024, 1, 15, 14, 0)
    }
    
    meeting = analyze_meeting_transcript(sample_transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    # Generate MOM with different configurations
    configs = [
        MOMConfiguration(style=MOMStyle.CORPORATE, format=MOMFormat.MARKDOWN),
        MOMConfiguration(style=MOMStyle.AGILE, format=MOMFormat.MARKDOWN),
        MOMConfiguration(style=MOMStyle.EXECUTIVE, format=MOMFormat.MARKDOWN),
        MOMConfiguration(style=MOMStyle.TECHNICAL, format=MOMFormat.MARKDOWN)
    ]
    
    engine = create_mom_template_engine()
    
    for i, config in enumerate(configs, 1):
        print(f"\n{'='*60}")
        print(f"MOM EXAMPLE {i}: {config.style.value.upper()} STYLE")
        print(f"{'='*60}")
        
        mom_doc = engine.generate_mom(meeting, action_items, config)
        rendered = engine.render_mom(mom_doc, config)
        
        print(rendered)

if __name__ == "__main__":
    example_usage()