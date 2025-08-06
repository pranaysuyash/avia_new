#!/usr/bin/env python3
"""
Meeting Automation System (Task 64)
Comprehensive meeting management with automatic summaries, MOM generation,
email/calendar integration, and project management tool connections
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from jinja2 import Template
import icalendar
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import msal
from collections import defaultdict

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class MeetingType(Enum):
    STANDUP = "standup"
    PLANNING = "planning"
    REVIEW = "review"
    RETROSPECTIVE = "retrospective"
    ONE_ON_ONE = "one_on_one"
    ALL_HANDS = "all_hands"
    CLIENT_MEETING = "client_meeting"
    BRAINSTORMING = "brainstorming"
    GENERAL = "general"

@dataclass
class Attendee:
    """Meeting attendee information"""
    name: str
    email: str
    role: str = "participant"
    attendance: bool = True
    speaking_time: float = 0.0
    contributions: List[str] = field(default_factory=list)

@dataclass
class ActionItem:
    """Action item from meeting"""
    description: str
    assignee: str
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Decision:
    """Decision made during meeting"""
    description: str
    rationale: str
    made_by: str
    timestamp: datetime
    impact: str = "medium"
    stakeholders: List[str] = field(default_factory=list)

@dataclass
class MeetingMinutes:
    """Comprehensive meeting minutes structure"""
    meeting_id: str
    title: str
    date: datetime
    duration: float
    meeting_type: MeetingType
    attendees: List[Attendee]
    agenda: List[str]
    discussion_points: List[Dict[str, Any]]
    decisions: List[Decision]
    action_items: List[ActionItem]
    key_insights: List[str]
    next_meeting: Optional[datetime] = None
    recording_url: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "meeting_id": self.meeting_id,
            "title": self.title,
            "date": self.date.isoformat(),
            "duration": self.duration,
            "meeting_type": self.meeting_type.value,
            "attendees": [asdict(a) for a in self.attendees],
            "agenda": self.agenda,
            "discussion_points": self.discussion_points,
            "decisions": [asdict(d) for d in self.decisions],
            "action_items": [asdict(a) for a in self.action_items],
            "key_insights": self.key_insights,
            "next_meeting": self.next_meeting.isoformat() if self.next_meeting else None,
            "recording_url": self.recording_url,
            "attachments": self.attachments
        }


class MeetingAnalyzer:
    """Analyze transcripts to extract meeting information"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def analyze_meeting(self, transcript: Dict[str, Any], 
                       metadata: Optional[Dict[str, Any]] = None) -> MeetingMinutes:
        """Analyze transcript and generate comprehensive meeting minutes"""
        
        # Extract basic information
        segments = transcript.get('segments', [])
        full_text = ' '.join([s.get('text', '') for s in segments])
        
        # Detect meeting type
        meeting_type = self._detect_meeting_type(full_text, metadata)
        
        # Extract attendees
        attendees = self._extract_attendees(segments, transcript.get('speakers', {}))
        
        # Extract agenda items
        agenda = self._extract_agenda(full_text)
        
        # Extract discussion points
        discussion_points = self._extract_discussion_points(segments)
        
        # Extract decisions
        decisions = self._extract_decisions(segments, attendees)
        
        # Extract action items
        action_items = self._extract_action_items(segments, attendees)
        
        # Extract key insights
        key_insights = self._extract_key_insights(full_text)
        
        # Generate title if not provided
        title = metadata.get('title') or self._generate_meeting_title(
            full_text, meeting_type, agenda
        )
        
        # Calculate duration
        duration = segments[-1].get('end', 0) if segments else 0
        
        return MeetingMinutes(
            meeting_id=self._generate_meeting_id(),
            title=title,
            date=datetime.now(),
            duration=duration,
            meeting_type=meeting_type,
            attendees=attendees,
            agenda=agenda,
            discussion_points=discussion_points,
            decisions=decisions,
            action_items=action_items,
            key_insights=key_insights,
            recording_url=metadata.get('recording_url')
        )
    
    def _detect_meeting_type(self, text: str, metadata: Optional[Dict] = None) -> MeetingType:
        """Detect the type of meeting from content"""
        text_lower = text.lower()
        
        # Check metadata first
        if metadata and 'meeting_type' in metadata:
            try:
                return MeetingType(metadata['meeting_type'])
            except ValueError:
                pass
        
        # Pattern matching for meeting types
        if any(word in text_lower for word in ['standup', 'stand-up', 'daily']):
            return MeetingType.STANDUP
        elif any(word in text_lower for word in ['planning', 'sprint planning']):
            return MeetingType.PLANNING
        elif any(word in text_lower for word in ['review', 'demo', 'showcase']):
            return MeetingType.REVIEW
        elif any(word in text_lower for word in ['retrospective', 'retro']):
            return MeetingType.RETROSPECTIVE
        elif any(word in text_lower for word in ['one-on-one', '1:1', 'one on one']):
            return MeetingType.ONE_ON_ONE
        elif any(word in text_lower for word in ['all hands', 'town hall']):
            return MeetingType.ALL_HANDS
        elif any(word in text_lower for word in ['client', 'customer', 'vendor']):
            return MeetingType.CLIENT_MEETING
        elif any(word in text_lower for word in ['brainstorm', 'ideation', 'workshop']):
            return MeetingType.BRAINSTORMING
        
        return MeetingType.GENERAL
    
    def _extract_attendees(self, segments: List[Dict], speaker_info: Dict) -> List[Attendee]:
        """Extract meeting attendees from segments"""
        attendees = {}
        
        for segment in segments:
            speaker_id = segment.get('speaker', 'Unknown')
            speaker_name = speaker_info.get(speaker_id, f"Speaker {speaker_id}")
            
            if speaker_name not in attendees:
                attendees[speaker_name] = Attendee(
                    name=speaker_name,
                    email=f"{speaker_name.lower().replace(' ', '.')}@example.com"
                )
            
            # Add speaking time
            duration = segment.get('end', 0) - segment.get('start', 0)
            attendees[speaker_name].speaking_time += duration
            
            # Add contribution
            text = segment.get('text', '').strip()
            if text:
                attendees[speaker_name].contributions.append(text)
        
        return list(attendees.values())
    
    def _extract_agenda(self, text: str) -> List[str]:
        """Extract agenda items from meeting text"""
        agenda = []
        
        # Look for agenda patterns
        agenda_patterns = [
            r"agenda:?\s*([^\n]+)",
            r"topics?:?\s*([^\n]+)",
            r"we'll discuss:?\s*([^\n]+)",
            r"today we'll cover:?\s*([^\n]+)"
        ]
        
        for pattern in agenda_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            agenda.extend(matches)
        
        # Look for numbered items
        numbered_pattern = r"^\d+[\.\)]\s*(.+)$"
        for line in text.split('\n'):
            match = re.match(numbered_pattern, line.strip())
            if match:
                agenda.append(match.group(1))
        
        return list(set(agenda))[:10]  # Limit to 10 items
    
    def _extract_discussion_points(self, segments: List[Dict]) -> List[Dict[str, Any]]:
        """Extract key discussion points with timestamps"""
        discussion_points = []
        current_topic = None
        topic_segments = []
        
        for segment in segments:
            text = segment.get('text', '').strip()
            
            # Detect topic changes
            if self._is_topic_change(text):
                if current_topic and topic_segments:
                    discussion_points.append({
                        'topic': current_topic,
                        'start_time': topic_segments[0].get('start', 0),
                        'end_time': topic_segments[-1].get('end', 0),
                        'summary': self._summarize_segments(topic_segments),
                        'speakers': list(set([s.get('speaker', 'Unknown') for s in topic_segments]))
                    })
                current_topic = text
                topic_segments = [segment]
            else:
                topic_segments.append(segment)
        
        # Add last topic
        if current_topic and topic_segments:
            discussion_points.append({
                'topic': current_topic,
                'start_time': topic_segments[0].get('start', 0),
                'end_time': topic_segments[-1].get('end', 0),
                'summary': self._summarize_segments(topic_segments),
                'speakers': list(set([s.get('speaker', 'Unknown') for s in topic_segments]))
            })
        
        return discussion_points
    
    def _extract_decisions(self, segments: List[Dict], attendees: List[Attendee]) -> List[Decision]:
        """Extract decisions made during the meeting"""
        decisions = []
        decision_keywords = [
            'decided', 'decision', 'agreed', 'concluded', 'resolved',
            'will go with', 'chosen', 'selected', 'approved'
        ]
        
        for segment in segments:
            text = segment.get('text', '').lower()
            if any(keyword in text for keyword in decision_keywords):
                speaker = next((a.name for a in attendees 
                              if a.name == segment.get('speaker', '')), 'Unknown')
                
                decisions.append(Decision(
                    description=segment.get('text', ''),
                    rationale=self._extract_rationale(segments, segment),
                    made_by=speaker,
                    timestamp=datetime.now() + timedelta(seconds=segment.get('start', 0))
                ))
        
        return decisions
    
    def _extract_action_items(self, segments: List[Dict], 
                            attendees: List[Attendee]) -> List[ActionItem]:
        """Extract action items from meeting"""
        action_items = []
        action_patterns = [
            r"(?:I'll|I will|will) (.+)",
            r"(?:you'll|you will) (.+)",
            r"(?:we'll|we will) (.+)",
            r"action item:? (.+)",
            r"todo:? (.+)",
            r"task:? (.+)",
            r"(?:need to|needs to|should) (.+)",
            r"(?:follow up|followup) (?:on|with) (.+)"
        ]
        
        for segment in segments:
            text = segment.get('text', '')
            speaker = segment.get('speaker', 'Unknown')
            
            for pattern in action_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Extract assignee
                    assignee = self._extract_assignee(match, speaker, attendees)
                    
                    # Extract due date
                    due_date = self._extract_due_date(match)
                    
                    # Extract priority
                    priority = self._extract_priority(match)
                    
                    action_items.append(ActionItem(
                        description=match.strip(),
                        assignee=assignee,
                        due_date=due_date,
                        priority=priority
                    ))
        
        return action_items
    
    def _extract_key_insights(self, text: str) -> List[str]:
        """Extract key insights from meeting"""
        insights = []
        
        # Use AI if available
        if self.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Extract 3-5 key insights from this meeting transcript. Focus on important decisions, discoveries, or strategic points."
                        },
                        {
                            "role": "user",
                            "content": text[:3000]  # Limit for API
                        }
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                insights_text = response.choices[0].message.content
                insights = [line.strip() for line in insights_text.split('\n') if line.strip()]
                
            except Exception as e:
                logger.error(f"Error extracting insights with AI: {e}")
        
        # Fallback to pattern matching
        if not insights:
            insight_patterns = [
                r"(?:key point|important|crucial|critical):? (.+)",
                r"(?:learned|discovered|found out) (?:that )?(.+)",
                r"(?:main takeaway|takeaway):? (.+)"
            ]
            
            for pattern in insight_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                insights.extend(matches)
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_meeting_title(self, text: str, meeting_type: MeetingType, 
                               agenda: List[str]) -> str:
        """Generate a meaningful meeting title"""
        if agenda:
            return f"{meeting_type.value.replace('_', ' ').title()}: {agenda[0]}"
        
        # Extract first meaningful sentence
        sentences = text.split('.')
        for sentence in sentences:
            if len(sentence.strip()) > 10:
                return f"{meeting_type.value.replace('_', ' ').title()}: {sentence.strip()[:50]}..."
        
        return f"{meeting_type.value.replace('_', ' ').title()} Meeting"
    
    def _generate_meeting_id(self) -> str:
        """Generate unique meeting ID"""
        return f"MTG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _is_topic_change(self, text: str) -> bool:
        """Detect if text indicates a topic change"""
        topic_indicators = [
            'next topic', 'moving on', 'let\'s discuss', 'now about',
            'another point', 'switching to', 'regarding'
        ]
        return any(indicator in text.lower() for indicator in topic_indicators)
    
    def _summarize_segments(self, segments: List[Dict]) -> str:
        """Summarize a group of segments"""
        texts = [s.get('text', '') for s in segments]
        full_text = ' '.join(texts)
        
        # Simple summarization - take first and last meaningful sentences
        sentences = [s.strip() for s in full_text.split('.') if len(s.strip()) > 10]
        if len(sentences) > 2:
            return f"{sentences[0]}... {sentences[-1]}"
        return full_text[:200] + "..." if len(full_text) > 200 else full_text
    
    def _extract_rationale(self, segments: List[Dict], decision_segment: Dict) -> str:
        """Extract rationale for a decision"""
        # Look for "because", "since", "due to" in nearby segments
        decision_index = segments.index(decision_segment)
        context_range = 3
        
        for i in range(max(0, decision_index - context_range), 
                      min(len(segments), decision_index + context_range)):
            text = segments[i].get('text', '').lower()
            if any(word in text for word in ['because', 'since', 'due to', 'reason']):
                return segments[i].get('text', '')
        
        return "Rationale not explicitly stated"
    
    def _extract_assignee(self, text: str, speaker: str, 
                         attendees: List[Attendee]) -> str:
        """Extract assignee from action item text"""
        # Check for explicit assignment
        assignment_patterns = [
            r"(?:assign(?:ed)? to |@)(\w+)",
            r"(\w+) (?:will|should|to) (?:handle|take care of|do)"
        ]
        
        for pattern in assignment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Match with attendees
                for attendee in attendees:
                    if name.lower() in attendee.name.lower():
                        return attendee.name
        
        # Default to speaker
        return speaker
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from action item text"""
        date_patterns = [
            r"(?:by|before|until) (\w+ \d+)",
            r"(?:due|deadline):? (\w+ \d+)",
            r"(?:end of|eod) (\w+)",
            r"(\w+) deadline"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Simple date parsing - in production use dateutil
                try:
                    if 'tomorrow' in date_str.lower():
                        return datetime.now() + timedelta(days=1)
                    elif 'week' in date_str.lower():
                        return datetime.now() + timedelta(weeks=1)
                    elif 'month' in date_str.lower():
                        return datetime.now() + timedelta(days=30)
                except:
                    pass
        
        return None
    
    def _extract_priority(self, text: str) -> TaskPriority:
        """Extract priority from action item text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'asap', 'critical', 'immediately']):
            return TaskPriority.URGENT
        elif any(word in text_lower for word in ['high priority', 'important']):
            return TaskPriority.HIGH
        elif any(word in text_lower for word in ['low priority', 'when possible']):
            return TaskPriority.LOW
        
        return TaskPriority.MEDIUM


class EmailIntegration:
    """Email integration for sending meeting summaries"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        self.smtp_config = smtp_config or {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'use_tls': True
        }
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates')
        os.makedirs(self.template_path, exist_ok=True)
    
    def send_meeting_summary(self, meeting_minutes: MeetingMinutes, 
                           recipients: List[str],
                           attachments: Optional[List[str]] = None) -> bool:
        """Send meeting summary email to recipients"""
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Meeting Minutes: {meeting_minutes.title}"
            msg['From'] = self.smtp_config['username']
            msg['To'] = ', '.join(recipients)
            
            # Create HTML content
            html_content = self._generate_html_email(meeting_minutes)
            
            # Create plain text version
            text_content = self._generate_text_email(meeting_minutes)
            
            # Attach parts
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Meeting summary sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _generate_html_email(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate HTML email content"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #4a5568; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
        .content { background: #f7fafc; padding: 20px; border-radius: 0 0 8px 8px; }
        .section { margin-bottom: 20px; padding: 15px; background: white; border-radius: 4px; }
        .section h3 { color: #2d3748; margin-top: 0; }
        .attendee { display: inline-block; margin: 2px; padding: 4px 8px; background: #e2e8f0; border-radius: 4px; }
        .action-item { margin: 10px 0; padding: 10px; background: #fff5f5; border-left: 4px solid #fc8181; }
        .decision { margin: 10px 0; padding: 10px; background: #f0fff4; border-left: 4px solid #68d391; }
        .priority-urgent { border-left-color: #f56565; }
        .priority-high { border-left-color: #ed8936; }
        .priority-medium { border-left-color: #ecc94b; }
        .priority-low { border-left-color: #48bb78; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Meeting Minutes</h1>
            <h2>{{ meeting.title }}</h2>
            <p>{{ meeting.date.strftime('%B %d, %Y at %I:%M %p') }} | Duration: {{ (meeting.duration / 60)|round(1) }} minutes</p>
        </div>
        
        <div class="content">
            <!-- Attendees -->
            <div class="section">
                <h3>👥 Attendees</h3>
                <div>
                    {% for attendee in meeting.attendees %}
                    <span class="attendee">{{ attendee.name }}</span>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Agenda -->
            {% if meeting.agenda %}
            <div class="section">
                <h3>📋 Agenda</h3>
                <ol>
                    {% for item in meeting.agenda %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ol>
            </div>
            {% endif %}
            
            <!-- Key Decisions -->
            {% if meeting.decisions %}
            <div class="section">
                <h3>✅ Key Decisions</h3>
                {% for decision in meeting.decisions %}
                <div class="decision">
                    <strong>{{ decision.description }}</strong><br>
                    <em>Decided by: {{ decision.made_by }}</em>
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Action Items -->
            {% if meeting.action_items %}
            <div class="section">
                <h3>📌 Action Items</h3>
                {% for item in meeting.action_items %}
                <div class="action-item priority-{{ item.priority.value }}">
                    <strong>{{ item.description }}</strong><br>
                    Assigned to: {{ item.assignee }}
                    {% if item.due_date %}
                    | Due: {{ item.due_date.strftime('%B %d, %Y') }}
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <!-- Key Insights -->
            {% if meeting.key_insights %}
            <div class="section">
                <h3>💡 Key Insights</h3>
                <ul>
                    {% for insight in meeting.key_insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            <!-- Next Meeting -->
            {% if meeting.next_meeting %}
            <div class="section">
                <h3>📅 Next Meeting</h3>
                <p>{{ meeting.next_meeting.strftime('%B %d, %Y at %I:%M %p') }}</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""
        
        from jinja2 import Template
        tmpl = Template(template)
        return tmpl.render(meeting=meeting_minutes)
    
    def _generate_text_email(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate plain text email content"""
        lines = [
            f"MEETING MINUTES: {meeting_minutes.title}",
            "=" * 50,
            f"Date: {meeting_minutes.date.strftime('%B %d, %Y at %I:%M %p')}",
            f"Duration: {meeting_minutes.duration / 60:.1f} minutes",
            "",
            "ATTENDEES:",
            ", ".join([a.name for a in meeting_minutes.attendees]),
            ""
        ]
        
        if meeting_minutes.agenda:
            lines.extend([
                "AGENDA:",
                *[f"- {item}" for item in meeting_minutes.agenda],
                ""
            ])
        
        if meeting_minutes.decisions:
            lines.extend([
                "KEY DECISIONS:",
                *[f"- {d.description} (by {d.made_by})" for d in meeting_minutes.decisions],
                ""
            ])
        
        if meeting_minutes.action_items:
            lines.extend([
                "ACTION ITEMS:",
                *[f"- {a.description} (assigned to: {a.assignee})" for a in meeting_minutes.action_items],
                ""
            ])
        
        if meeting_minutes.key_insights:
            lines.extend([
                "KEY INSIGHTS:",
                *[f"- {insight}" for insight in meeting_minutes.key_insights],
                ""
            ])
        
        return "\n".join(lines)
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to email"""
        try:
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                msg.attach(part)
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {e}")


class CalendarIntegration:
    """Calendar integration for Google Calendar and Outlook"""
    
    def __init__(self):
        self.google_creds = self._load_google_credentials()
        self.outlook_creds = self._load_outlook_credentials()
    
    def _load_google_credentials(self) -> Optional[Credentials]:
        """Load Google Calendar credentials"""
        try:
            # In production, implement proper OAuth2 flow
            # This is a placeholder
            return None
        except Exception as e:
            logger.error(f"Error loading Google credentials: {e}")
            return None
    
    def _load_outlook_credentials(self) -> Optional[Dict[str, str]]:
        """Load Outlook credentials"""
        try:
            return {
                'client_id': os.getenv('OUTLOOK_CLIENT_ID'),
                'client_secret': os.getenv('OUTLOOK_CLIENT_SECRET'),
                'tenant_id': os.getenv('OUTLOOK_TENANT_ID')
            }
        except Exception as e:
            logger.error(f"Error loading Outlook credentials: {e}")
            return None
    
    def create_follow_up_meeting(self, meeting_minutes: MeetingMinutes,
                               calendar_type: str = "google") -> Optional[str]:
        """Create a follow-up meeting in calendar"""
        
        if meeting_minutes.next_meeting:
            event_data = {
                'summary': f"Follow-up: {meeting_minutes.title}",
                'description': self._generate_event_description(meeting_minutes),
                'start': meeting_minutes.next_meeting,
                'end': meeting_minutes.next_meeting + timedelta(hours=1),
                'attendees': [a.email for a in meeting_minutes.attendees]
            }
            
            if calendar_type == "google":
                return self._create_google_event(event_data)
            elif calendar_type == "outlook":
                return self._create_outlook_event(event_data)
        
        return None
    
    def _generate_event_description(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate calendar event description"""
        lines = [
            "This is a follow-up to the previous meeting.",
            "",
            "Previous Meeting Summary:",
            f"- Date: {meeting_minutes.date.strftime('%B %d, %Y')}",
            f"- Key Decisions: {len(meeting_minutes.decisions)}",
            f"- Action Items: {len(meeting_minutes.action_items)}",
            "",
            "Outstanding Action Items:"
        ]
        
        for item in meeting_minutes.action_items:
            if item.status != "completed":
                lines.append(f"- {item.description} (assigned to: {item.assignee})")
        
        return "\n".join(lines)
    
    def _create_google_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Create event in Google Calendar"""
        try:
            if not self.google_creds:
                logger.warning("Google credentials not configured")
                return None
            
            service = build('calendar', 'v3', credentials=self.google_creds)
            
            event = {
                'summary': event_data['summary'],
                'description': event_data['description'],
                'start': {
                    'dateTime': event_data['start'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data['end'].isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in event_data['attendees']],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }
            
            event = service.events().insert(calendarId='primary', body=event).execute()
            return event.get('htmlLink')
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return None
    
    def _create_outlook_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Create event in Outlook Calendar"""
        try:
            if not self.outlook_creds:
                logger.warning("Outlook credentials not configured")
                return None
            
            # Get access token
            app = msal.ConfidentialClientApplication(
                self.outlook_creds['client_id'],
                authority=f"https://login.microsoftonline.com/{self.outlook_creds['tenant_id']}",
                client_credential=self.outlook_creds['client_secret']
            )
            
            result = app.acquire_token_silent(["https://graph.microsoft.com/.default"], account=None)
            if not result:
                result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
            
            if "access_token" in result:
                # Create event
                headers = {'Authorization': f"Bearer {result['access_token']}"}
                
                event = {
                    "subject": event_data['summary'],
                    "body": {
                        "contentType": "text",
                        "content": event_data['description']
                    },
                    "start": {
                        "dateTime": event_data['start'].isoformat(),
                        "timeZone": "UTC"
                    },
                    "end": {
                        "dateTime": event_data['end'].isoformat(),
                        "timeZone": "UTC"
                    },
                    "attendees": [
                        {
                            "emailAddress": {"address": email},
                            "type": "required"
                        } for email in event_data['attendees']
                    ]
                }
                
                response = requests.post(
                    "https://graph.microsoft.com/v1.0/me/events",
                    headers=headers,
                    json=event
                )
                
                if response.status_code == 201:
                    return response.json().get('webLink')
            
        except Exception as e:
            logger.error(f"Error creating Outlook event: {e}")
            return None


class ProjectManagementIntegration:
    """Integration with project management tools (Jira, Asana, Trello)"""
    
    def __init__(self):
        self.jira_config = {
            'url': os.getenv('JIRA_URL'),
            'username': os.getenv('JIRA_USERNAME'),
            'api_token': os.getenv('JIRA_API_TOKEN'),
            'project_key': os.getenv('JIRA_PROJECT_KEY', 'PROJ')
        }
        
        self.asana_config = {
            'access_token': os.getenv('ASANA_ACCESS_TOKEN'),
            'workspace_id': os.getenv('ASANA_WORKSPACE_ID')
        }
        
        self.trello_config = {
            'api_key': os.getenv('TRELLO_API_KEY'),
            'token': os.getenv('TRELLO_TOKEN'),
            'board_id': os.getenv('TRELLO_BOARD_ID')
        }
    
    def create_tasks_from_action_items(self, action_items: List[ActionItem],
                                     platform: str = "jira") -> List[str]:
        """Create tasks in project management tool from action items"""
        
        task_ids = []
        
        for item in action_items:
            if platform == "jira":
                task_id = self._create_jira_issue(item)
            elif platform == "asana":
                task_id = self._create_asana_task(item)
            elif platform == "trello":
                task_id = self._create_trello_card(item)
            else:
                logger.warning(f"Unknown platform: {platform}")
                continue
            
            if task_id:
                task_ids.append(task_id)
        
        return task_ids
    
    def _create_jira_issue(self, action_item: ActionItem) -> Optional[str]:
        """Create Jira issue from action item"""
        try:
            if not all([self.jira_config['url'], self.jira_config['username'], 
                       self.jira_config['api_token']]):
                logger.warning("Jira configuration incomplete")
                return None
            
            auth = (self.jira_config['username'], self.jira_config['api_token'])
            headers = {'Content-Type': 'application/json'}
            
            # Map priority
            jira_priority = {
                TaskPriority.URGENT: "Highest",
                TaskPriority.HIGH: "High",
                TaskPriority.MEDIUM: "Medium",
                TaskPriority.LOW: "Low"
            }.get(action_item.priority, "Medium")
            
            issue_data = {
                "fields": {
                    "project": {"key": self.jira_config['project_key']},
                    "summary": action_item.description[:255],
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": action_item.description
                                    }
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": "Task"},
                    "priority": {"name": jira_priority},
                    "labels": action_item.tags
                }
            }
            
            # Add due date if available
            if action_item.due_date:
                issue_data["fields"]["duedate"] = action_item.due_date.strftime("%Y-%m-%d")
            
            response = requests.post(
                f"{self.jira_config['url']}/rest/api/3/issue",
                auth=auth,
                headers=headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issue_key = response.json()['key']
                logger.info(f"Created Jira issue: {issue_key}")
                return issue_key
            else:
                logger.error(f"Failed to create Jira issue: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            
        return None
    
    def _create_asana_task(self, action_item: ActionItem) -> Optional[str]:
        """Create Asana task from action item"""
        try:
            if not all([self.asana_config['access_token'], self.asana_config['workspace_id']]):
                logger.warning("Asana configuration incomplete")
                return None
            
            headers = {
                'Authorization': f"Bearer {self.asana_config['access_token']}",
                'Content-Type': 'application/json'
            }
            
            task_data = {
                "data": {
                    "name": action_item.description,
                    "notes": f"Assignee: {action_item.assignee}\nPriority: {action_item.priority.value}",
                    "workspace": self.asana_config['workspace_id'],
                    "projects": []  # Add project IDs if needed
                }
            }
            
            # Add due date
            if action_item.due_date:
                task_data["data"]["due_on"] = action_item.due_date.strftime("%Y-%m-%d")
            
            response = requests.post(
                "https://app.asana.com/api/1.0/tasks",
                headers=headers,
                json=task_data
            )
            
            if response.status_code == 201:
                task_gid = response.json()['data']['gid']
                logger.info(f"Created Asana task: {task_gid}")
                return task_gid
            else:
                logger.error(f"Failed to create Asana task: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating Asana task: {e}")
            
        return None
    
    def _create_trello_card(self, action_item: ActionItem) -> Optional[str]:
        """Create Trello card from action item"""
        try:
            if not all([self.trello_config['api_key'], self.trello_config['token'],
                       self.trello_config['board_id']]):
                logger.warning("Trello configuration incomplete")
                return None
            
            # Get lists on board
            lists_url = f"https://api.trello.com/1/boards/{self.trello_config['board_id']}/lists"
            lists_response = requests.get(lists_url, params={
                'key': self.trello_config['api_key'],
                'token': self.trello_config['token']
            })
            
            if lists_response.status_code != 200:
                logger.error("Failed to get Trello lists")
                return None
            
            lists = lists_response.json()
            if not lists:
                logger.error("No lists found on Trello board")
                return None
            
            # Use first list (usually "To Do")
            list_id = lists[0]['id']
            
            # Create card
            card_data = {
                'key': self.trello_config['api_key'],
                'token': self.trello_config['token'],
                'idList': list_id,
                'name': action_item.description[:256],
                'desc': f"Assignee: {action_item.assignee}\nPriority: {action_item.priority.value}"
            }
            
            # Add due date
            if action_item.due_date:
                card_data['due'] = action_item.due_date.isoformat()
            
            # Add labels based on priority
            # This would require fetching available labels first
            
            response = requests.post(
                "https://api.trello.com/1/cards",
                params=card_data
            )
            
            if response.status_code == 200:
                card_id = response.json()['id']
                logger.info(f"Created Trello card: {card_id}")
                return card_id
            else:
                logger.error(f"Failed to create Trello card: {response.text}")
                
        except Exception as e:
            logger.error(f"Error creating Trello card: {e}")
            
        return None


class CollaborationIntegration:
    """Integration with collaboration tools (Slack, Teams)"""
    
    def __init__(self):
        self.slack_config = {
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
            'bot_token': os.getenv('SLACK_BOT_TOKEN')
        }
        
        self.teams_config = {
            'webhook_url': os.getenv('TEAMS_WEBHOOK_URL')
        }
    
    def share_meeting_summary(self, meeting_minutes: MeetingMinutes,
                            platform: str = "slack",
                            channel: Optional[str] = None) -> bool:
        """Share meeting summary to collaboration platform"""
        
        if platform == "slack":
            return self._share_to_slack(meeting_minutes, channel)
        elif platform == "teams":
            return self._share_to_teams(meeting_minutes)
        else:
            logger.warning(f"Unknown platform: {platform}")
            return False
    
    def _share_to_slack(self, meeting_minutes: MeetingMinutes,
                       channel: Optional[str] = None) -> bool:
        """Share meeting summary to Slack"""
        try:
            if not self.slack_config['webhook_url']:
                logger.warning("Slack webhook URL not configured")
                return False
            
            # Create rich message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📋 {meeting_minutes.title}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:* {meeting_minutes.date.strftime('%B %d, %Y')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:* {meeting_minutes.duration / 60:.1f} minutes"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Attendees:* {', '.join([a.name for a in meeting_minutes.attendees])}"
                    }
                }
            ]
            
            # Add decisions
            if meeting_minutes.decisions:
                blocks.append({"type": "divider"})
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*✅ Key Decisions:*\n" + "\n".join([
                            f"• {d.description}" for d in meeting_minutes.decisions[:3]
                        ])
                    }
                })
            
            # Add action items
            if meeting_minutes.action_items:
                blocks.append({"type": "divider"})
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📌 Action Items:*\n" + "\n".join([
                            f"• {a.description} (assigned to: {a.assignee})"
                            for a in meeting_minutes.action_items[:5]
                        ])
                    }
                })
            
            # Send message
            payload = {
                "blocks": blocks
            }
            
            if channel:
                payload["channel"] = channel
            
            response = requests.post(self.slack_config['webhook_url'], json=payload)
            
            if response.status_code == 200:
                logger.info("Meeting summary shared to Slack")
                return True
            else:
                logger.error(f"Failed to share to Slack: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sharing to Slack: {e}")
            return False
    
    def _share_to_teams(self, meeting_minutes: MeetingMinutes) -> bool:
        """Share meeting summary to Microsoft Teams"""
        try:
            if not self.teams_config['webhook_url']:
                logger.warning("Teams webhook URL not configured")
                return False
            
            # Create adaptive card
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": f"Meeting Minutes: {meeting_minutes.title}",
                "sections": [
                    {
                        "activityTitle": f"📋 {meeting_minutes.title}",
                        "facts": [
                            {
                                "name": "Date:",
                                "value": meeting_minutes.date.strftime('%B %d, %Y')
                            },
                            {
                                "name": "Duration:",
                                "value": f"{meeting_minutes.duration / 60:.1f} minutes"
                            },
                            {
                                "name": "Attendees:",
                                "value": ", ".join([a.name for a in meeting_minutes.attendees])
                            }
                        ]
                    }
                ]
            }
            
            # Add decisions section
            if meeting_minutes.decisions:
                card["sections"].append({
                    "activityTitle": "✅ Key Decisions",
                    "text": "\n\n".join([d.description for d in meeting_minutes.decisions[:3]])
                })
            
            # Add action items section
            if meeting_minutes.action_items:
                action_text = []
                for item in meeting_minutes.action_items[:5]:
                    action_text.append(
                        f"**{item.description}**\n\n"
                        f"Assigned to: {item.assignee} | "
                        f"Priority: {item.priority.value}"
                    )
                
                card["sections"].append({
                    "activityTitle": "📌 Action Items",
                    "text": "\n\n".join(action_text)
                })
            
            # Send to Teams
            response = requests.post(self.teams_config['webhook_url'], json=card)
            
            if response.status_code == 200:
                logger.info("Meeting summary shared to Teams")
                return True
            else:
                logger.error(f"Failed to share to Teams: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sharing to Teams: {e}")
            return False


class MeetingAutomationSystem:
    """Main system orchestrating all meeting automation features"""
    
    def __init__(self):
        self.analyzer = MeetingAnalyzer()
        self.email_integration = EmailIntegration()
        self.calendar_integration = CalendarIntegration()
        self.pm_integration = ProjectManagementIntegration()
        self.collab_integration = CollaborationIntegration()
    
    def process_meeting(self, transcript: Dict[str, Any],
                       metadata: Optional[Dict[str, Any]] = None,
                       options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process meeting transcript and execute automation"""
        
        options = options or {}
        results = {
            'status': 'success',
            'meeting_minutes': None,
            'email_sent': False,
            'calendar_event': None,
            'tasks_created': [],
            'collaboration_shared': False,
            'errors': []
        }
        
        try:
            # Analyze meeting
            logger.info("Analyzing meeting transcript...")
            meeting_minutes = self.analyzer.analyze_meeting(transcript, metadata)
            results['meeting_minutes'] = meeting_minutes.to_dict()
            
            # Send email summary
            if options.get('send_email') and options.get('email_recipients'):
                logger.info("Sending email summary...")
                email_sent = self.email_integration.send_meeting_summary(
                    meeting_minutes,
                    options['email_recipients']
                )
                results['email_sent'] = email_sent
            
            # Create calendar event
            if options.get('create_calendar_event'):
                logger.info("Creating calendar event...")
                calendar_type = options.get('calendar_type', 'google')
                event_link = self.calendar_integration.create_follow_up_meeting(
                    meeting_minutes,
                    calendar_type
                )
                results['calendar_event'] = event_link
            
            # Create project management tasks
            if options.get('create_tasks') and meeting_minutes.action_items:
                logger.info("Creating project management tasks...")
                pm_platform = options.get('pm_platform', 'jira')
                task_ids = self.pm_integration.create_tasks_from_action_items(
                    meeting_minutes.action_items,
                    pm_platform
                )
                results['tasks_created'] = task_ids
            
            # Share to collaboration platform
            if options.get('share_to_collaboration'):
                logger.info("Sharing to collaboration platform...")
                collab_platform = options.get('collab_platform', 'slack')
                shared = self.collab_integration.share_meeting_summary(
                    meeting_minutes,
                    collab_platform,
                    options.get('collab_channel')
                )
                results['collaboration_shared'] = shared
            
        except Exception as e:
            logger.error(f"Error processing meeting: {e}")
            results['status'] = 'error'
            results['errors'].append(str(e))
        
        return results
    
    def generate_meeting_report(self, meeting_minutes: MeetingMinutes,
                              format: str = "html") -> str:
        """Generate meeting report in specified format"""
        
        if format == "html":
            return self._generate_html_report(meeting_minutes)
        elif format == "markdown":
            return self._generate_markdown_report(meeting_minutes)
        elif format == "pdf":
            # Would require additional PDF generation library
            return self._generate_pdf_report(meeting_minutes)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html_report(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate comprehensive HTML report"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Meeting Report - {{ meeting.title }}</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .report-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .report-header h1 { margin: 0 0 10px 0; }
        .metadata { 
            display: flex;
            gap: 30px;
            font-size: 0.9em;
            opacity: 0.9;
        }
        .section {
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #4a5568;
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .attendee-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .attendee-card {
            background: #f7fafc;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }
        .action-item {
            background: #fef5e7;
            border-left: 4px solid #f39c12;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .decision-item {
            background: #e8f8f5;
            border-left: 4px solid #27ae60;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .priority-urgent { border-left-color: #e74c3c; background: #ffeee9; }
        .priority-high { border-left-color: #f39c12; }
        .priority-medium { border-left-color: #3498db; background: #ebf5fb; }
        .priority-low { border-left-color: #95a5a6; background: #f8f9fa; }
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        .timeline-item {
            position: relative;
            padding-bottom: 20px;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -21px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
        }
        .timeline-item::after {
            content: '';
            position: absolute;
            left: -15px;
            top: 17px;
            bottom: -20px;
            width: 1px;
            background: #e2e8f0;
        }
        .timeline-item:last-child::after { display: none; }
        @media (max-width: 768px) {
            .metadata { flex-direction: column; gap: 10px; }
            .attendee-grid { grid-template-columns: 1fr; }
        }
        @media print {
            body { background: white; }
            .section { box-shadow: none; border: 1px solid #ddd; }
        }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>{{ meeting.title }}</h1>
        <div class="metadata">
            <div>📅 {{ meeting.date.strftime('%B %d, %Y at %I:%M %p') }}</div>
            <div>⏱️ {{ (meeting.duration / 60)|round(1) }} minutes</div>
            <div>👥 {{ meeting.attendees|length }} attendees</div>
            <div>📋 {{ meeting.meeting_type.value.replace('_', ' ').title() }}</div>
        </div>
    </div>
    
    <!-- Attendees Section -->
    <div class="section">
        <h2>Attendees</h2>
        <div class="attendee-grid">
            {% for attendee in meeting.attendees %}
            <div class="attendee-card">
                <strong>{{ attendee.name }}</strong><br>
                <small>{{ attendee.email }}</small><br>
                <small>Speaking time: {{ (attendee.speaking_time / 60)|round(1) }} min</small>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <!-- Agenda Section -->
    {% if meeting.agenda %}
    <div class="section">
        <h2>Agenda</h2>
        <ol>
            {% for item in meeting.agenda %}
            <li>{{ item }}</li>
            {% endfor %}
        </ol>
    </div>
    {% endif %}
    
    <!-- Discussion Timeline -->
    {% if meeting.discussion_points %}
    <div class="section">
        <h2>Discussion Timeline</h2>
        <div class="timeline">
            {% for point in meeting.discussion_points %}
            <div class="timeline-item">
                <strong>{{ point.topic }}</strong><br>
                <small>{{ (point.start_time / 60)|round(1) }} - {{ (point.end_time / 60)|round(1) }} min</small><br>
                <p>{{ point.summary }}</p>
                <small>Speakers: {{ point.speakers|join(', ') }}</small>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    
    <!-- Decisions Section -->
    {% if meeting.decisions %}
    <div class="section">
        <h2>Key Decisions</h2>
        {% for decision in meeting.decisions %}
        <div class="decision-item">
            <strong>{{ decision.description }}</strong><br>
            <small>Decided by: {{ decision.made_by }} | Impact: {{ decision.impact }}</small><br>
            {% if decision.rationale %}
            <em>Rationale: {{ decision.rationale }}</em>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Action Items Section -->
    {% if meeting.action_items %}
    <div class="section">
        <h2>Action Items</h2>
        {% for item in meeting.action_items %}
        <div class="action-item priority-{{ item.priority.value }}">
            <strong>{{ item.description }}</strong><br>
            <small>
                Assigned to: {{ item.assignee }} | 
                Priority: {{ item.priority.value.upper() }}
                {% if item.due_date %}
                | Due: {{ item.due_date.strftime('%B %d, %Y') }}
                {% endif %}
            </small>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Key Insights Section -->
    {% if meeting.key_insights %}
    <div class="section">
        <h2>Key Insights</h2>
        <ul>
            {% for insight in meeting.key_insights %}
            <li>{{ insight }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <!-- Next Steps -->
    {% if meeting.next_meeting %}
    <div class="section">
        <h2>Next Steps</h2>
        <p><strong>Next Meeting:</strong> {{ meeting.next_meeting.strftime('%B %d, %Y at %I:%M %p') }}</p>
    </div>
    {% endif %}
    
    <div style="text-align: center; margin-top: 40px; color: #718096;">
        <small>Generated on {{ datetime.now().strftime('%B %d, %Y at %I:%M %p') }}</small>
    </div>
</body>
</html>
"""
        
        from jinja2 import Template
        import datetime
        tmpl = Template(template)
        return tmpl.render(meeting=meeting_minutes, datetime=datetime)
    
    def _generate_markdown_report(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate Markdown report"""
        lines = [
            f"# Meeting Minutes: {meeting_minutes.title}",
            "",
            f"**Date:** {meeting_minutes.date.strftime('%B %d, %Y at %I:%M %p')}  ",
            f"**Duration:** {meeting_minutes.duration / 60:.1f} minutes  ",
            f"**Type:** {meeting_minutes.meeting_type.value.replace('_', ' ').title()}  ",
            "",
            "## Attendees",
            ""
        ]
        
        for attendee in meeting_minutes.attendees:
            lines.append(f"- **{attendee.name}** ({attendee.email}) - Speaking time: {attendee.speaking_time / 60:.1f} min")
        
        if meeting_minutes.agenda:
            lines.extend(["", "## Agenda", ""])
            for i, item in enumerate(meeting_minutes.agenda, 1):
                lines.append(f"{i}. {item}")
        
        if meeting_minutes.decisions:
            lines.extend(["", "## Key Decisions", ""])
            for decision in meeting_minutes.decisions:
                lines.extend([
                    f"### ✅ {decision.description}",
                    f"- **Decided by:** {decision.made_by}",
                    f"- **Rationale:** {decision.rationale}",
                    ""
                ])
        
        if meeting_minutes.action_items:
            lines.extend(["", "## Action Items", ""])
            for item in meeting_minutes.action_items:
                due_date = f" - Due: {item.due_date.strftime('%B %d, %Y')}" if item.due_date else ""
                lines.append(
                    f"- [ ] **{item.description}** (Assigned to: {item.assignee}, "
                    f"Priority: {item.priority.value.upper()}{due_date})"
                )
        
        if meeting_minutes.key_insights:
            lines.extend(["", "## Key Insights", ""])
            for insight in meeting_minutes.key_insights:
                lines.append(f"- {insight}")
        
        if meeting_minutes.next_meeting:
            lines.extend([
                "",
                "## Next Meeting",
                f"Scheduled for: {meeting_minutes.next_meeting.strftime('%B %d, %Y at %I:%M %p')}"
            ])
        
        return "\n".join(lines)
    
    def _generate_pdf_report(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate PDF report (placeholder - would require reportlab or similar)"""
        # This would require a PDF generation library like reportlab
        # For now, return HTML that can be converted to PDF
        return self._generate_html_report(meeting_minutes)


def demonstrate_meeting_automation():
    """Demonstrate the meeting automation system"""
    
    # Sample meeting transcript
    sample_transcript = {
        'segments': [
            {'text': "Let's start our sprint planning meeting.", 'speaker': 'John', 'start': 0, 'end': 3},
            {'text': "Today we'll cover the upcoming sprint tasks and priorities.", 'speaker': 'John', 'start': 3, 'end': 7},
            {'text': "First, let's review the backlog items.", 'speaker': 'John', 'start': 7, 'end': 10},
            {'text': "I think we should prioritize the authentication feature.", 'speaker': 'Sarah', 'start': 10, 'end': 14},
            {'text': "Agreed. I'll take the lead on implementing OAuth integration.", 'speaker': 'Mike', 'start': 14, 'end': 18},
            {'text': "Great. That needs to be done by end of next week.", 'speaker': 'John', 'start': 18, 'end': 22},
            {'text': "We've decided to go with OAuth 2.0 for better security.", 'speaker': 'Sarah', 'start': 22, 'end': 26},
            {'text': "I'll create the Jira tickets for this task.", 'speaker': 'Mike', 'start': 26, 'end': 29},
            {'text': "Also, we need to follow up on the database optimization.", 'speaker': 'Sarah', 'start': 29, 'end': 33},
            {'text': "Let's schedule our next meeting for Monday at 10 AM.", 'speaker': 'John', 'start': 33, 'end': 37}
        ],
        'speakers': {
            'John': 'John Smith',
            'Sarah': 'Sarah Johnson',
            'Mike': 'Mike Wilson'
        }
    }
    
    # Initialize system
    system = MeetingAutomationSystem()
    
    # Process meeting with various options
    options = {
        'send_email': True,
        'email_recipients': ['team@example.com'],
        'create_calendar_event': True,
        'calendar_type': 'google',
        'create_tasks': True,
        'pm_platform': 'jira',
        'share_to_collaboration': True,
        'collab_platform': 'slack',
        'collab_channel': '#team-updates'
    }
    
    # Process the meeting
    results = system.process_meeting(sample_transcript, options=options)
    
    # Display results
    print("Meeting Automation Results")
    print("=" * 50)
    print(f"Status: {results['status']}")
    
    if results['meeting_minutes']:
        minutes = MeetingMinutes(**results['meeting_minutes'])
        print(f"\nMeeting Title: {minutes.title}")
        print(f"Duration: {minutes.duration / 60:.1f} minutes")
        print(f"Attendees: {', '.join([a.name for a in minutes.attendees])}")
        print(f"Action Items: {len(minutes.action_items)}")
        print(f"Decisions: {len(minutes.decisions)}")
    
    print(f"\nEmail sent: {results['email_sent']}")
    print(f"Calendar event: {results['calendar_event']}")
    print(f"Tasks created: {len(results['tasks_created'])}")
    print(f"Shared to collaboration: {results['collaboration_shared']}")
    
    # Generate reports
    if results['meeting_minutes']:
        html_report = system.generate_meeting_report(minutes, format="html")
        markdown_report = system.generate_meeting_report(minutes, format="markdown")
        
        # Save reports
        with open('meeting_report.html', 'w') as f:
            f.write(html_report)
        
        with open('meeting_report.md', 'w') as f:
            f.write(markdown_report)
        
        print("\nReports generated: meeting_report.html, meeting_report.md")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demonstration
    demonstrate_meeting_automation()