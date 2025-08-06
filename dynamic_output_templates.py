"""
Dynamic Output Templates and Formatting System
Provides customizable templates for different content types and smart formatting
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentMetadata:
    """Metadata for content being formatted"""
    title: str
    content_type: str  # meeting, interview, lecture, podcast, etc.
    duration: Optional[int] = None
    language: str = "en"
    speakers: Optional[List[str]] = None
    date_created: Optional[datetime] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    key_topics: Optional[List[str]] = None

@dataclass
class TranscriptSegment:
    """Individual transcript segment"""
    start_time: float
    end_time: float
    speaker: Optional[str]
    text: str
    confidence: Optional[float] = None
    
@dataclass
class ActionItem:
    """Action item extracted from content"""
    text: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"
    status: str = "pending"

@dataclass
class KeyPoint:
    """Key point or highlight from content"""
    text: str
    timestamp: Optional[float] = None
    importance: float = 1.0
    category: Optional[str] = None

@dataclass
class FormattedOutput:
    """Formatted output result"""
    content: str
    format_type: str
    template_name: str
    metadata: Dict[str, Any]
    generated_at: datetimeclass Tem
plateEngine:
    """Core template engine for dynamic output formatting"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_filters()
        
        # Load built-in templates
        self._create_builtin_templates()
    
    def _register_filters(self):
        """Register custom Jinja2 filters"""
        
        @self.jinja_env.filter('format_time')
        def format_time(seconds: float) -> str:
            """Format seconds to MM:SS or HH:MM:SS"""
            if seconds < 3600:
                return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"
            else:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        @self.jinja_env.filter('format_duration')
        def format_duration(seconds: int) -> str:
            """Format duration in human-readable format"""
            if seconds < 60:
                return f"{seconds} seconds"
            elif seconds < 3600:
                minutes = seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                if minutes > 0:
                    return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
                return f"{hours} hour{'s' if hours != 1 else ''}"
        
        @self.jinja_env.filter('capitalize_speaker')
        def capitalize_speaker(speaker: str) -> str:
            """Capitalize speaker name properly"""
            if not speaker:
                return "Unknown Speaker"
            return speaker.title() if speaker.lower() != speaker else speaker
        
        @self.jinja_env.filter('extract_sentences')
        def extract_sentences(text: str, max_sentences: int = 3) -> List[str]:
            """Extract first N sentences from text"""
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences[:max_sentences] if s.strip()]
        
        @self.jinja_env.filter('word_count')
        def word_count(text: str) -> int:
            """Count words in text"""
            return len(text.split())
    
    def _create_builtin_templates(self):
        """Create built-in templates if they don't exist"""
        builtin_templates = {
            'meeting_minutes.html': self._get_meeting_minutes_template(),
            'interview_summary.md': self._get_interview_summary_template(),
            'lecture_notes.md': self._get_lecture_notes_template(),
            'podcast_summary.html': self._get_podcast_summary_template(),
            'action_items.md': self._get_action_items_template(),
            'executive_summary.html': self._get_executive_summary_template(),
            'detailed_transcript.html': self._get_detailed_transcript_template(),
            'simple_transcript.txt': self._get_simple_transcript_template()
        }
        
        for template_name, template_content in builtin_templates.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                template_path.write_text(template_content)
                logger.info(f"Created built-in template: {template_name}")
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates with metadata"""
        templates = []
        
        for template_file in self.templates_dir.glob("*.html"):
            templates.append({
                'name': template_file.stem,
                'file': template_file.name,
                'format': 'html',
                'description': self._get_template_description(template_file.name)
            })
        
        for template_file in self.templates_dir.glob("*.md"):
            templates.append({
                'name': template_file.stem,
                'file': template_file.name,
                'format': 'markdown',
                'description': self._get_template_description(template_file.name)
            })
        
        for template_file in self.templates_dir.glob("*.txt"):
            templates.append({
                'name': template_file.stem,
                'file': template_file.name,
                'format': 'text',
                'description': self._get_template_description(template_file.name)
            })
        
        return templates
    
    def _get_template_description(self, template_name: str) -> str:
        """Get description for template"""
        descriptions = {
            'meeting_minutes.html': 'Professional meeting minutes with action items and decisions',
            'interview_summary.md': 'Interview summary with key insights and quotes',
            'lecture_notes.md': 'Structured lecture notes with topics and key points',
            'podcast_summary.html': 'Podcast episode summary with highlights and timestamps',
            'action_items.md': 'Extracted action items with assignments and deadlines',
            'executive_summary.html': 'Executive summary for leadership review',
            'detailed_transcript.html': 'Full transcript with speaker identification and timestamps',
            'simple_transcript.txt': 'Plain text transcript without formatting'
        }
        return descriptions.get(template_name, 'Custom template')    
def format_content(
        self,
        template_name: str,
        metadata: ContentMetadata,
        transcript_segments: List[TranscriptSegment],
        action_items: Optional[List[ActionItem]] = None,
        key_points: Optional[List[KeyPoint]] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> FormattedOutput:
        """Format content using specified template"""
        
        try:
            # Load template
            template = self.jinja_env.get_template(template_name)
            
            # Prepare template context
            context = {
                'metadata': metadata,
                'transcript_segments': transcript_segments,
                'action_items': action_items or [],
                'key_points': key_points or [],
                'custom_data': custom_data or {},
                'generated_at': datetime.now(),
                'total_segments': len(transcript_segments),
                'total_speakers': len(set(seg.speaker for seg in transcript_segments if seg.speaker)),
                'word_count': sum(len(seg.text.split()) for seg in transcript_segments)
            }
            
            # Add computed fields
            if transcript_segments:
                context['total_duration'] = max(seg.end_time for seg in transcript_segments)
                context['speakers_list'] = list(set(seg.speaker for seg in transcript_segments if seg.speaker))
            
            # Render template
            rendered_content = template.render(**context)
            
            # Determine format type
            format_type = self._get_format_type(template_name)
            
            return FormattedOutput(
                content=rendered_content,
                format_type=format_type,
                template_name=template_name,
                metadata=asdict(metadata),
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error formatting content with template {template_name}: {e}")
            raise
    
    def _get_format_type(self, template_name: str) -> str:
        """Determine format type from template name"""
        if template_name.endswith('.html'):
            return 'html'
        elif template_name.endswith('.md'):
            return 'markdown'
        elif template_name.endswith('.txt'):
            return 'text'
        else:
            return 'unknown'
    
    def create_custom_template(
        self,
        name: str,
        content: str,
        description: str = "",
        format_type: str = "html"
    ) -> bool:
        """Create a custom template"""
        try:
            # Validate template syntax
            Template(content)
            
            # Save template
            extension = f".{format_type}"
            template_path = self.templates_dir / f"{name}{extension}"
            template_path.write_text(content)
            
            # Save metadata
            metadata_path = self.templates_dir / f"{name}.meta.json"
            metadata = {
                'name': name,
                'description': description,
                'format_type': format_type,
                'created_at': datetime.now().isoformat(),
                'custom': True
            }
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            logger.info(f"Created custom template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating custom template {name}: {e}")
            return False
    
    def _get_meeting_minutes_template(self) -> str:
        """Get meeting minutes HTML template"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Meeting Minutes - {{ metadata.title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .action-item { background: #f0f8ff; padding: 10px; margin: 5px 0; border-left: 4px solid #007acc; }
        .speaker { font-weight: bold; color: #333; }
        .timestamp { color: #666; font-size: 0.9em; }
        .summary { background: #f9f9f9; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Meeting Minutes</h1>
        <h2>{{ metadata.title }}</h2>
        <p><strong>Date:</strong> {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}</p>
        <p><strong>Duration:</strong> {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}</p>
        <p><strong>Participants:</strong> {{ metadata.speakers | join(', ') if metadata.speakers else 'N/A' }}</p>
    </div>

    {% if metadata.summary %}
    <div class="section">
        <h3>Executive Summary</h3>
        <div class="summary">{{ metadata.summary }}</div>
    </div>
    {% endif %}

    {% if action_items %}
    <div class="section">
        <h3>Action Items</h3>
        {% for item in action_items %}
        <div class="action-item">
            <strong>{{ item.text }}</strong>
            {% if item.assignee %}<br><em>Assigned to:</em> {{ item.assignee }}{% endif %}
            {% if item.due_date %}<br><em>Due:</em> {{ item.due_date.strftime('%B %d, %Y') }}{% endif %}
            <br><em>Priority:</em> {{ item.priority.title() }}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if key_points %}
    <div class="section">
        <h3>Key Discussion Points</h3>
        <ul>
        {% for point in key_points %}
            <li>{{ point.text }}
            {% if point.timestamp %}<span class="timestamp">[{{ point.timestamp | format_time }}]</span>{% endif %}
            </li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="section">
        <h3>Full Transcript</h3>
        {% for segment in transcript_segments %}
        <p>
            <span class="timestamp">[{{ segment.start_time | format_time }}]</span>
            <span class="speaker">{{ segment.speaker | capitalize_speaker }}:</span>
            {{ segment.text }}
        </p>
        {% endfor %}
    </div>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 0.9em;">
        Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}
    </footer>
</body>
</html>'''    def _
get_interview_summary_template(self) -> str:
        """Get interview summary Markdown template"""
        return '''# Interview Summary: {{ metadata.title }}

**Date:** {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}  
**Duration:** {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}  
**Participants:** {{ metadata.speakers | join(', ') if metadata.speakers else 'N/A' }}

{% if metadata.summary %}
## Executive Summary

{{ metadata.summary }}
{% endif %}

{% if key_points %}
## Key Insights

{% for point in key_points %}
- **{{ point.text }}** {% if point.timestamp %}*[{{ point.timestamp | format_time }}]*{% endif %}
{% endfor %}
{% endif %}

{% if action_items %}
## Follow-up Actions

{% for item in action_items %}
- [ ] {{ item.text }}
  {% if item.assignee %}- **Assigned to:** {{ item.assignee }}{% endif %}
  {% if item.due_date %}- **Due:** {{ item.due_date.strftime('%B %d, %Y') }}{% endif %}
  - **Priority:** {{ item.priority.title() }}
{% endfor %}
{% endif %}

## Notable Quotes

{% for segment in transcript_segments %}
{% if segment.text | length > 100 %}
> "{{ segment.text }}"  
> — {{ segment.speaker | capitalize_speaker }} *[{{ segment.start_time | format_time }}]*

{% endif %}
{% endfor %}

## Full Transcript

{% for segment in transcript_segments %}
**{{ segment.speaker | capitalize_speaker }}** *[{{ segment.start_time | format_time }}]*: {{ segment.text }}

{% endfor %}

---
*Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}*'''

    def _get_lecture_notes_template(self) -> str:
        """Get lecture notes Markdown template"""
        return '''# Lecture Notes: {{ metadata.title }}

**Date:** {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}  
**Duration:** {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}  
**Instructor:** {{ metadata.speakers[0] if metadata.speakers else 'N/A' }}

{% if metadata.summary %}
## Overview

{{ metadata.summary }}
{% endif %}

{% if metadata.key_topics %}
## Topics Covered

{% for topic in metadata.key_topics %}
- {{ topic }}
{% endfor %}
{% endif %}

{% if key_points %}
## Key Points

{% for point in key_points %}
### {{ point.category or 'Important Point' }}
{{ point.text }}
{% if point.timestamp %}*Discussed at {{ point.timestamp | format_time }}*{% endif %}

{% endfor %}
{% endif %}

{% if action_items %}
## Assignments & Tasks

{% for item in action_items %}
- [ ] {{ item.text }}
  {% if item.due_date %}- **Due:** {{ item.due_date.strftime('%B %d, %Y') }}{% endif %}
{% endfor %}
{% endif %}

## Detailed Notes

{% for segment in transcript_segments %}
{% if segment.speaker %}
**{{ segment.start_time | format_time }}** - {{ segment.text }}

{% endif %}
{% endfor %}

---
*Notes generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}*'''

    def _get_podcast_summary_template(self) -> str:
        """Get podcast summary HTML template"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>{{ metadata.title }} - Podcast Summary</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .highlight { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }
        .timestamp-link { color: #007acc; text-decoration: none; font-weight: bold; }
        .speaker-segment { margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎙️ {{ metadata.title }}</h1>
        <p><strong>Duration:</strong> {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}</p>
        <p><strong>Hosts:</strong> {{ metadata.speakers | join(', ') if metadata.speakers else 'N/A' }}</p>
    </div>

    {% if metadata.summary %}
    <div class="highlight">
        <h3>Episode Summary</h3>
        {{ metadata.summary }}
    </div>
    {% endif %}

    {% if key_points %}
    <h3>🎯 Key Highlights</h3>
    {% for point in key_points %}
    <div class="highlight">
        {{ point.text }}
        {% if point.timestamp %}
        <br><a href="#" class="timestamp-link">[Jump to {{ point.timestamp | format_time }}]</a>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}

    <h3>📝 Full Transcript</h3>
    {% for segment in transcript_segments %}
    <div class="speaker-segment">
        <strong>{{ segment.speaker | capitalize_speaker }}</strong> 
        <span style="color: #666;">[{{ segment.start_time | format_time }}]</span>
        <br>{{ segment.text }}
    </div>
    {% endfor %}

    <footer style="margin-top: 50px; text-align: center; color: #666;">
        Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}
    </footer>
</body>
</html>''' 
   def _get_action_items_template(self) -> str:
        """Get action items Markdown template"""
        return '''# Action Items: {{ metadata.title }}

**Generated from:** {{ metadata.content_type.title() }}  
**Date:** {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}

{% if action_items %}
## Pending Actions

{% for item in action_items %}
### {{ loop.index }}. {{ item.text }}

- **Status:** {{ item.status.title() }}
- **Priority:** {{ item.priority.title() }}
{% if item.assignee %}- **Assigned to:** {{ item.assignee }}{% endif %}
{% if item.due_date %}- **Due Date:** {{ item.due_date.strftime('%B %d, %Y') }}{% endif %}

{% endfor %}

## Summary

- **Total Actions:** {{ action_items | length }}
- **High Priority:** {{ action_items | selectattr('priority', 'equalto', 'high') | list | length }}
- **Medium Priority:** {{ action_items | selectattr('priority', 'equalto', 'medium') | list | length }}
- **Low Priority:** {{ action_items | selectattr('priority', 'equalto', 'low') | list | length }}

{% else %}
No action items were identified in this content.
{% endif %}

---
*Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}*'''

    def _get_executive_summary_template(self) -> str:
        """Get executive summary HTML template"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Executive Summary - {{ metadata.title }}</title>
    <style>
        body { font-family: 'Times New Roman', serif; margin: 60px; line-height: 1.8; color: #333; }
        .header { text-align: center; border-bottom: 3px solid #333; padding-bottom: 20px; margin-bottom: 40px; }
        .executive-summary { background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 30px 0; }
        .key-metrics { display: flex; justify-content: space-around; margin: 30px 0; }
        .metric { text-align: center; padding: 15px; background: #e9ecef; border-radius: 5px; }
        .recommendations { background: #d4edda; padding: 20px; border-left: 5px solid #28a745; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Executive Summary</h1>
        <h2>{{ metadata.title }}</h2>
        <p>{{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}</p>
    </div>

    <div class="key-metrics">
        <div class="metric">
            <h4>Duration</h4>
            <p>{{ metadata.duration | format_duration if metadata.duration else 'N/A' }}</p>
        </div>
        <div class="metric">
            <h4>Participants</h4>
            <p>{{ metadata.speakers | length if metadata.speakers else 0 }}</p>
        </div>
        <div class="metric">
            <h4>Key Points</h4>
            <p>{{ key_points | length }}</p>
        </div>
        <div class="metric">
            <h4>Action Items</h4>
            <p>{{ action_items | length }}</p>
        </div>
    </div>

    {% if metadata.summary %}
    <div class="executive-summary">
        <h3>Summary</h3>
        {{ metadata.summary }}
    </div>
    {% endif %}

    {% if key_points %}
    <h3>Key Findings</h3>
    <ul>
    {% for point in key_points %}
        <li>{{ point.text }}</li>
    {% endfor %}
    </ul>
    {% endif %}

    {% if action_items %}
    <div class="recommendations">
        <h3>Recommended Actions</h3>
        <ol>
        {% for item in action_items %}
            <li>{{ item.text }}
            {% if item.assignee %} ({{ item.assignee }}){% endif %}
            {% if item.due_date %} - Due: {{ item.due_date.strftime('%B %d, %Y') }}{% endif %}
            </li>
        {% endfor %}
        </ol>
    </div>
    {% endif %}

    <footer style="margin-top: 60px; text-align: center; font-size: 0.9em; color: #666;">
        <p>This executive summary was generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}</p>
        <p>Total word count: {{ word_count }} words</p>
    </footer>
</body>
</html>'''

    def _get_detailed_transcript_template(self) -> str:
        """Get detailed transcript HTML template"""
        return '''<!DOCTYPE html>
<html>
<head>
    <title>Detailed Transcript - {{ metadata.title }}</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 40px; line-height: 1.5; }
        .header { border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 30px; }
        .segment { margin: 10px 0; padding: 8px; border-left: 3px solid #ddd; }
        .speaker { font-weight: bold; color: #0066cc; }
        .timestamp { color: #666; font-size: 0.9em; margin-right: 10px; }
        .confidence { color: #999; font-size: 0.8em; float: right; }
        .high-confidence { color: #28a745; }
        .medium-confidence { color: #ffc107; }
        .low-confidence { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Detailed Transcript</h1>
        <h2>{{ metadata.title }}</h2>
        <p><strong>Total Duration:</strong> {{ total_duration | format_time if total_duration else 'N/A' }}</p>
        <p><strong>Speakers:</strong> {{ speakers_list | join(', ') if speakers_list else 'N/A' }}</p>
        <p><strong>Total Segments:</strong> {{ total_segments }}</p>
        <p><strong>Word Count:</strong> {{ word_count }}</p>
    </div>

    {% for segment in transcript_segments %}
    <div class="segment">
        <span class="timestamp">[{{ segment.start_time | format_time }} - {{ segment.end_time | format_time }}]</span>
        <span class="speaker">{{ segment.speaker | capitalize_speaker }}:</span>
        {{ segment.text }}
        {% if segment.confidence %}
        <span class="confidence {% if segment.confidence > 0.8 %}high-confidence{% elif segment.confidence > 0.6 %}medium-confidence{% else %}low-confidence{% endif %}">
            ({{ (segment.confidence * 100) | round(1) }}%)
        </span>
        {% endif %}
    </div>
    {% endfor %}

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 0.9em;">
        Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}
    </footer>
</body>
</html>'''

    def _get_simple_transcript_template(self) -> str:
        """Get simple transcript text template"""
        return '''{{ metadata.title }}
{{ '=' * metadata.title|length }}

Date: {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}
Duration: {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}
Speakers: {{ metadata.speakers | join(', ') if metadata.speakers else 'N/A' }}

{% for segment in transcript_segments %}
[{{ segment.start_time | format_time }}] {{ segment.speaker | capitalize_speaker }}: {{ segment.text }}

{% endfor %}

---
Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}'''cl
ass SmartFormatter:
    """Smart formatting engine with content analysis"""
    
    def __init__(self, template_engine: TemplateEngine):
        self.template_engine = template_engine
    
    def analyze_content_type(self, transcript_segments: List[TranscriptSegment]) -> str:
        """Analyze content to determine the most appropriate type"""
        if not transcript_segments:
            return "unknown"
        
        # Analyze text patterns
        all_text = " ".join(seg.text.lower() for seg in transcript_segments)
        
        # Meeting indicators
        meeting_keywords = ["agenda", "action item", "follow up", "meeting", "decision", "vote"]
        meeting_score = sum(1 for keyword in meeting_keywords if keyword in all_text)
        
        # Interview indicators
        interview_keywords = ["question", "answer", "tell me about", "experience", "background"]
        interview_score = sum(1 for keyword in interview_keywords if keyword in all_text)
        
        # Lecture indicators
        lecture_keywords = ["today we will", "chapter", "assignment", "homework", "exam", "study"]
        lecture_score = sum(1 for keyword in lecture_keywords if keyword in all_text)
        
        # Podcast indicators
        podcast_keywords = ["episode", "welcome back", "sponsor", "subscribe", "listener"]
        podcast_score = sum(1 for keyword in podcast_keywords if keyword in all_text)
        
        # Determine type based on highest score
        scores = {
            "meeting": meeting_score,
            "interview": interview_score,
            "lecture": lecture_score,
            "podcast": podcast_score
        }
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
    
    def extract_action_items(self, transcript_segments: List[TranscriptSegment]) -> List[ActionItem]:
        """Extract action items from transcript"""
        action_items = []
        
        # Action item patterns
        patterns = [
            r"action item:?\s*(.+?)(?:\.|$)",
            r"(?:we need to|should|must|will)\s+(.+?)(?:\.|$)",
            r"(?:follow up|follow-up)\s+(?:on|with)?\s*(.+?)(?:\.|$)",
            r"(?:assign|assigned to)\s+(\w+)\s+to\s+(.+?)(?:\.|$)",
            r"(?:by|due)\s+(\w+day|\d+/\d+|\w+\s+\d+)\s*(.+?)(?:\.|$)"
        ]
        
        for segment in transcript_segments:
            text = segment.text.lower()
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        action_text = match[-1].strip()
                    else:
                        action_text = match.strip()
                    
                    if len(action_text) > 10:  # Filter out very short matches
                        action_items.append(ActionItem(
                            text=action_text,
                            priority="medium"
                        ))
        
        return action_items[:10]  # Limit to top 10
    
    def extract_key_points(self, transcript_segments: List[TranscriptSegment]) -> List[KeyPoint]:
        """Extract key points from transcript"""
        key_points = []
        
        # Key point indicators
        indicators = [
            "important", "key", "crucial", "essential", "main point",
            "remember", "note that", "emphasis", "highlight", "significant"
        ]
        
        for segment in transcript_segments:
            text = segment.text.lower()
            
            # Check for key point indicators
            for indicator in indicators:
                if indicator in text:
                    # Extract sentence containing the indicator
                    sentences = re.split(r'[.!?]+', segment.text)
                    for sentence in sentences:
                        if indicator in sentence.lower() and len(sentence.strip()) > 20:
                            key_points.append(KeyPoint(
                                text=sentence.strip(),
                                timestamp=segment.start_time,
                                importance=1.0
                            ))
                            break
        
        # Also extract longer segments as potentially important
        for segment in transcript_segments:
            if len(segment.text.split()) > 30:  # Long segments might be important
                key_points.append(KeyPoint(
                    text=segment.text,
                    timestamp=segment.start_time,
                    importance=0.7
                ))
        
        # Sort by importance and return top points
        key_points.sort(key=lambda x: x.importance, reverse=True)
        return key_points[:8]  # Limit to top 8
    
    def auto_format(
        self,
        transcript_segments: List[TranscriptSegment],
        metadata: Optional[ContentMetadata] = None,
        preferred_format: Optional[str] = None
    ) -> FormattedOutput:
        """Automatically format content with smart template selection"""
        
        # Analyze content if metadata not provided
        if not metadata:
            content_type = self.analyze_content_type(transcript_segments)
            metadata = ContentMetadata(
                title="Untitled Content",
                content_type=content_type,
                date_created=datetime.now()
            )
        
        # Extract additional data
        action_items = self.extract_action_items(transcript_segments)
        key_points = self.extract_key_points(transcript_segments)
        
        # Select appropriate template
        template_name = self._select_template(metadata.content_type, preferred_format)
        
        return self.template_engine.format_content(
            template_name=template_name,
            metadata=metadata,
            transcript_segments=transcript_segments,
            action_items=action_items,
            key_points=key_points
        )
    
    def _select_template(self, content_type: str, preferred_format: Optional[str] = None) -> str:
        """Select the most appropriate template"""
        format_suffix = f".{preferred_format}" if preferred_format else ".html"
        
        template_mapping = {
            "meeting": f"meeting_minutes{format_suffix}",
            "interview": f"interview_summary{'.md' if not preferred_format else format_suffix}",
            "lecture": f"lecture_notes{'.md' if not preferred_format else format_suffix}",
            "podcast": f"podcast_summary{format_suffix}",
            "general": f"detailed_transcript{format_suffix}"
        }
        
        return template_mapping.get(content_type, f"detailed_transcript{format_suffix}")

class TemplateManager:
    """Manager for template operations and customization"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.template_engine = TemplateEngine(templates_dir)
        self.smart_formatter = SmartFormatter(self.template_engine)
    
    def get_template_preview(self, template_name: str) -> str:
        """Get a preview of what a template looks like"""
        # Create sample data
        sample_metadata = ContentMetadata(
            title="Sample Content",
            content_type="meeting",
            duration=1800,
            speakers=["John Doe", "Jane Smith"],
            date_created=datetime.now(),
            summary="This is a sample summary of the content."
        )
        
        sample_segments = [
            TranscriptSegment(0, 30, "John Doe", "Welcome everyone to today's meeting."),
            TranscriptSegment(30, 60, "Jane Smith", "Thank you John. Let's start with the agenda."),
            TranscriptSegment(60, 120, "John Doe", "We need to follow up on the action items from last week.")
        ]
        
        sample_action_items = [
            ActionItem("Review quarterly reports", "Jane Smith", datetime.now() + timedelta(days=7), "high"),
            ActionItem("Schedule team building event", "John Doe", datetime.now() + timedelta(days=14), "medium")
        ]
        
        sample_key_points = [
            KeyPoint("Budget approval needed for Q4", 90, 1.0),
            KeyPoint("New team member starting next month", 150, 0.8)
        ]
        
        try:
            result = self.template_engine.format_content(
                template_name=template_name,
                metadata=sample_metadata,
                transcript_segments=sample_segments,
                action_items=sample_action_items,
                key_points=sample_key_points
            )
            return result.content
        except Exception as e:
            return f"Error generating preview: {str(e)}"
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template syntax and structure"""
        try:
            # Test template compilation
            template = Template(template_content)
            
            # Test with sample data
            sample_data = {
                'metadata': ContentMetadata("Test", "test"),
                'transcript_segments': [],
                'action_items': [],
                'key_points': [],
                'generated_at': datetime.now()
            }
            
            template.render(**sample_data)
            
            return {
                'valid': True,
                'message': 'Template is valid'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Template validation failed: {str(e)}'
            }
    
    def export_template(self, template_name: str) -> Optional[str]:
        """Export template content for sharing"""
        try:
            template_path = self.template_engine.templates_dir / template_name
            if template_path.exists():
                return template_path.read_text()
            return None
        except Exception as e:
            logger.error(f"Error exporting template {template_name}: {e}")
            return None
    
    def import_template(self, name: str, content: str, overwrite: bool = False) -> bool:
        """Import template from external source"""
        try:
            template_path = self.template_engine.templates_dir / name
            
            if template_path.exists() and not overwrite:
                logger.warning(f"Template {name} already exists. Use overwrite=True to replace.")
                return False
            
            # Validate before importing
            validation = self.validate_template(content)
            if not validation['valid']:
                logger.error(f"Template validation failed: {validation['message']}")
                return False
            
            template_path.write_text(content)
            logger.info(f"Successfully imported template: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing template {name}: {e}")
            return False 
                           key_points.append(KeyPoint(
                                text=sentence.strip(),
                                timestamp=segment.start_time,
                                importance=0.8
                            ))
                            break
        
        return key_points[:15]  # Limit to top 15
    
    def auto_format(
        self,
        transcript_segments: List[TranscriptSegment],
        metadata: ContentMetadata,
        preferred_format: str = "html"
    ) -> FormattedOutput:
        """Automatically format content with best template"""
        
        # Analyze content type if not specified
        if not metadata.content_type or metadata.content_type == "general":
            metadata.content_type = self.analyze_content_type(transcript_segments)
        
        # Extract additional data
        action_items = self.extract_action_items(transcript_segments)
        key_points = self.extract_key_points(transcript_segments)
        
        # Select best template based on content type and format
        template_mapping = {
            "meeting": f"meeting_minutes.{preferred_format}",
            "interview": f"interview_summary.{preferred_format}",
            "lecture": f"lecture_notes.{preferred_format}",
            "podcast": f"podcast_summary.{preferred_format}",
            "general": f"detailed_transcript.{preferred_format}"
        }
        
        template_name = template_mapping.get(metadata.content_type, f"detailed_transcript.{preferred_format}")
        
        # Format content
        return self.template_engine.format_content(
            template_name=template_name,
            metadata=metadata,
            transcript_segments=transcript_segments,
            action_items=action_items,
            key_points=key_points
        )

class TemplateManager:
    """High-level template management system"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.template_engine = TemplateEngine(templates_dir)
        self.smart_formatter = SmartFormatter(self.template_engine)
    
    def get_template_preview(self, template_name: str) -> str:
        """Generate preview of template with sample data"""
        
        # Sample data for preview
        sample_metadata = ContentMetadata(
            title="Sample Content Preview",
            content_type="meeting",
            duration=1800,
            speakers=["Alice Johnson", "Bob Smith", "Carol Davis"],
            date_created=datetime.now(),
            summary="This is a sample preview of the template with placeholder content.",
            key_topics=["Topic 1", "Topic 2", "Topic 3"]
        )
        
        sample_segments = [
            TranscriptSegment(0, 30, "Alice Johnson", "Welcome everyone to today's meeting. Let's start with the agenda review."),
            TranscriptSegment(30, 75, "Bob Smith", "Thanks Alice. I'd like to discuss the budget allocation for the next quarter."),
            TranscriptSegment(75, 120, "Carol Davis", "That's a great point Bob. We need to consider the new project requirements."),
            TranscriptSegment(120, 180, "Alice Johnson", "Agreed. Let's make sure we allocate sufficient resources for the implementation phase.")
        ]
        
        sample_action_items = [
            ActionItem("Review budget proposal", "Bob Smith", datetime.now() + timedelta(days=3), "high"),
            ActionItem("Prepare resource allocation plan", "Carol Davis", datetime.now() + timedelta(days=5), "medium")
        ]
        
        sample_key_points = [
            KeyPoint("Budget allocation needs review", 30, 1.0),
            KeyPoint("New project requirements identified", 75, 0.9)
        ]
        
        try:
            result = self.template_engine.format_content(
                template_name=template_name,
                metadata=sample_metadata,
                transcript_segments=sample_segments,
                action_items=sample_action_items,
                key_points=sample_key_points
            )
            return result.content
        except Exception as e:
            return f"Error generating preview: {str(e)}"
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template syntax"""
        try:
            from jinja2 import Template
            Template(template_content)
            return {"valid": True, "message": "Template is valid"}
        except Exception as e:
            return {"valid": False, "message": str(e)}
    
    def export_template(self, template_name: str) -> Optional[str]:
        """Export template content"""
        try:
            template_path = self.template_engine.templates_dir / template_name
            if template_path.exists():
                return template_path.read_text()
            return None
        except Exception:
            return None
    
    def delete_template(self, template_name: str) -> bool:
        """Delete custom template"""
        try:
            template_path = self.template_engine.templates_dir / template_name
            meta_path = self.template_engine.templates_dir / f"{template_name.split('.')[0]}.meta.json"
            
            if template_path.exists():
                template_path.unlink()
            
            if meta_path.exists():
                meta_path.unlink()
            
            return True
        except Exception:
            return False
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get template usage statistics"""
        templates = self.template_engine.get_available_templates()
        
        stats = {
            "total_templates": len(templates),
            "by_format": {},
            "custom_templates": 0,
            "builtin_templates": 0
        }
        
        for template in templates:
            format_type = template['format']
            stats["by_format"][format_type] = stats["by_format"].get(format_type, 0) + 1
            
            # Check if custom template
            meta_path = self.template_engine.templates_dir / f"{template['name']}.meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                    if metadata.get('custom', False):
                        stats["custom_templates"] += 1
                    else:
                        stats["builtin_templates"] += 1
                except Exception:
                    stats["builtin_templates"] += 1
            else:
                stats["builtin_templates"] += 1
        
        return stats

# Utility functions for template system
def create_sample_content() -> Dict[str, Any]:
    """Create sample content for testing templates"""
    return {
        'metadata': ContentMetadata(
            title="Sample Meeting - Q4 Planning",
            content_type="meeting",
            duration=3600,
            speakers=["John Doe", "Jane Smith", "Mike Johnson"],
            date_created=datetime.now(),
            summary="Quarterly planning meeting to discuss goals, budget, and resource allocation for Q4.",
            key_topics=["Budget Planning", "Resource Allocation", "Timeline Review"]
        ),
        'transcript_segments': [
            TranscriptSegment(0, 45, "John Doe", "Good morning team. Let's begin our Q4 planning session."),
            TranscriptSegment(45, 120, "Jane Smith", "I've prepared the budget analysis. We're looking at a 15% increase in operational costs."),
            TranscriptSegment(120, 200, "Mike Johnson", "That's significant. We need to identify areas where we can optimize spending."),
            TranscriptSegment(200, 280, "John Doe", "Agreed. Jane, can you break down the cost increases by category?"),
            TranscriptSegment(280, 360, "Jane Smith", "Certainly. The main increases are in personnel costs and technology infrastructure."),
            TranscriptSegment(360, 450, "Mike Johnson", "For technology, we should consider cloud migration to reduce long-term costs."),
            TranscriptSegment(450, 520, "John Doe", "That's a good point. Let's schedule a follow-up meeting to discuss the migration plan.")
        ],
        'action_items': [
            ActionItem("Prepare detailed budget breakdown", "Jane Smith", datetime.now() + timedelta(days=3), "high"),
            ActionItem("Research cloud migration options", "Mike Johnson", datetime.now() + timedelta(days=7), "medium"),
            ActionItem("Schedule migration planning meeting", "John Doe", datetime.now() + timedelta(days=5), "medium")
        ],
        'key_points': [
            KeyPoint("15% increase in operational costs identified", 45, 1.0, "Budget"),
            KeyPoint("Personnel and technology are main cost drivers", 280, 0.9, "Analysis"),
            KeyPoint("Cloud migration proposed as cost optimization", 360, 0.8, "Solution")
        ]
    }

def format_time_duration(seconds: float) -> str:
    """Format time duration in human-readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''}"

def extract_text_statistics(transcript_segments: List[TranscriptSegment]) -> Dict[str, Any]:
    """Extract text statistics from transcript segments"""
    if not transcript_segments:
        return {}
    
    all_text = " ".join(seg.text for seg in transcript_segments)
    words = all_text.split()
    
    return {
        "total_words": len(words),
        "total_characters": len(all_text),
        "average_words_per_segment": len(words) / len(transcript_segments),
        "total_segments": len(transcript_segments),
        "unique_speakers": len(set(seg.speaker for seg in transcript_segments if seg.speaker)),
        "total_duration": max(seg.end_time for seg in transcript_segments) if transcript_segments else 0
    }

# Export main classes for external use
__all__ = [
    'TemplateEngine',
    'SmartFormatter', 
    'TemplateManager',
    'ContentMetadata',
    'TranscriptSegment',
    'ActionItem',
    'KeyPoint',
    'FormattedOutput',
    'create_sample_content',
    'format_time_duration',
    'extract_text_statistics'
]