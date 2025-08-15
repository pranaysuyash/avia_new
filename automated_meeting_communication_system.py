#!/usr/bin/env python3
"""
Automated Meeting and Communication System
Task 237: Automatic meeting summary and MOM generation, email integration,
calendar integration, follow-up task creation, and project management integration.
"""

import asyncio
import json
import os
import sqlite3
import smtplib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingType(Enum):
    """Types of meetings."""
    STANDUP = "standup"
    PLANNING = "planning"
    RETROSPECTIVE = "retrospective"
    REVIEW = "review"
    ONE_ON_ONE = "one_on_one"
    ALL_HANDS = "all_hands"
    CLIENT_MEETING = "client_meeting"
    INTERVIEW = "interview"
    TRAINING = "training"
    BRAINSTORM = "brainstorm"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(Enum):
    """Task status options."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class IntegrationType(Enum):
    """Project management integration types."""
    JIRA = "jira"
    ASANA = "asana"
    TRELLO = "trello"
    MONDAY = "monday"
    GITHUB = "github"
    SLACK = "slack"
    TEAMS = "teams"

@dataclass
class MeetingParticipant:
    """Meeting participant information."""
    participant_id: str
    name: str
    email: str
    role: str
    department: Optional[str] = None
    attendance_status: str = "present"  # present, absent, late
    speaking_time: float = 0.0
    contribution_score: float = 0.0
    action_items_assigned: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ActionItem:
    """Action item extracted from meeting."""
    item_id: str
    description: str
    assigned_to: str
    assignee_email: str
    due_date: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.OPEN
    category: str = "general"
    meeting_timestamp: Optional[float] = None
    context: str = ""
    estimated_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MeetingDecision:
    """Decision made during meeting."""
    decision_id: str
    description: str
    decision_maker: str
    rationale: str
    impact: str = "medium"  # low, medium, high
    timestamp: Optional[float] = None
    context: str = ""
    affected_stakeholders: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MeetingInsight:
    """Key insight from meeting."""
    insight_id: str
    category: str  # problem, opportunity, risk, idea
    description: str
    importance: str = "medium"
    speaker: Optional[str] = None
    timestamp: Optional[float] = None
    related_topics: List[str] = field(default_factory=list)
    actionable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MeetingMinutes:
    """Complete meeting minutes (MOM)."""
    meeting_id: str
    title: str
    meeting_type: MeetingType
    date: datetime
    duration: float
    participants: List[MeetingParticipant]
    agenda_items: List[str]
    key_discussions: List[str]
    action_items: List[ActionItem]
    decisions: List[MeetingDecision]
    insights: List[MeetingInsight]
    next_meeting: Optional[datetime] = None
    summary: str = ""
    transcript_highlights: List[str] = field(default_factory=list)
    attendance_summary: Dict[str, int] = field(default_factory=dict)
    meeting_effectiveness_score: float = 0.0
    follow_up_required: bool = False
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmailTemplate:
    """Email template for different communication types."""
    template_id: str
    name: str
    subject_template: str
    body_template: str
    recipient_type: str  # all_participants, assignees, managers
    include_attachments: bool = True
    send_delay_minutes: int = 0  # Delay before sending
    auto_send: bool = False

@dataclass
class CalendarEvent:
    """Calendar event for scheduling."""
    event_id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    meeting_link: Optional[str] = None
    agenda: List[str] = field(default_factory=list)
    preparation_materials: List[str] = field(default_factory=list)
    event_type: str = "meeting"
    recurrence: Optional[str] = None
    reminders: List[int] = field(default_factory=lambda: [15, 5])  # minutes before

class MeetingAnalyzer:
    """Analyzes meeting content and extracts structured information."""
    
    def __init__(self):
        self.analysis_patterns = self._initialize_analysis_patterns()
    
    def _initialize_analysis_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for meeting analysis."""
        return {
            'action_items': {
                'patterns': [
                    r'action item[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:will|should|need to|must)\s+(.+?)(?=\.|by|before)',
                    r'(?:assigned to|assign to|responsible for)\s+(\w+)',
                    r'(?:due|deadline|by)\s+(\d{1,2}[\/\-]\d{1,2}|\w+day)',
                    r'(?:todo|to do|task)[:\-\s]*(.+?)(?=\.|$)'
                ],
                'assignee_patterns': [
                    r'(\w+)\s+(?:will|should|needs? to)',
                    r'assigned to\s+(\w+)',
                    r'(\w+)\s+is responsible',
                    r'(\w+),?\s+can you'
                ]
            },
            'decisions': {
                'patterns': [
                    r'(?:decided|decision|conclude|agreed)\s+(?:that\s+)?(.+?)(?=\.|$)',
                    r'(?:final|unanimous|majority)\s+decision[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:resolved|settled|determined)\s+(?:that\s+)?(.+?)(?=\.|$)'
                ]
            },
            'insights': {
                'patterns': [
                    r'(?:important|key|crucial|critical|significant)\s+(?:point|issue|concern)[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:problem|challenge|risk)[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:opportunity|idea|suggestion)[:\-\s]*(.+?)(?=\.|$)'
                ]
            },
            'questions': {
                'patterns': [
                    r'(?:question|clarify|understand)[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:what|how|when|where|why|who)\s+(.+?)\?',
                    r'(?:can|could|should|would)\s+(?:we|you|they)\s+(.+?)\?'
                ]
            },
            'next_steps': {
                'patterns': [
                    r'next step[s]?[:\-\s]*(.+?)(?=\.|$)',
                    r'(?:follow up|follow-up)[:\-\s]*(.+?)(?=\.|$)',
                    r'next meeting[:\-\s]*(.+?)(?=\.|$)'
                ]
            }
        }
    
    def analyze_meeting_transcript(self, transcript: str, participants: List[str],
                                 meeting_duration: float) -> Tuple[List[ActionItem], List[MeetingDecision], List[MeetingInsight]]:
        """Analyze meeting transcript for action items, decisions, and insights."""
        
        # Split transcript by speaker if available
        segments = self._split_by_speaker(transcript)
        
        # Extract action items
        action_items = self._extract_action_items(segments, participants)
        
        # Extract decisions
        decisions = self._extract_decisions(segments, participants)
        
        # Extract insights
        insights = self._extract_insights(segments, participants)
        
        return action_items, decisions, insights
    
    def _split_by_speaker(self, transcript: str) -> List[Dict[str, str]]:
        """Split transcript by speaker."""
        segments = []
        lines = transcript.split('\n')
        
        current_speaker = "Unknown"
        current_text = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for speaker pattern (SPEAKER: text)
            speaker_match = re.match(r'^([A-Z_\s]+):\s*(.*)$', line)
            if speaker_match:
                # Save previous segment
                if current_text:
                    segments.append({
                        'speaker': current_speaker,
                        'text': current_text.strip()
                    })
                
                # Start new segment
                current_speaker = speaker_match.group(1).strip()
                current_text = speaker_match.group(2)
            else:
                # Continue current segment
                current_text += " " + line
        
        # Save final segment
        if current_text:
            segments.append({
                'speaker': current_speaker,
                'text': current_text.strip()
            })
        
        return segments
    
    def _extract_action_items(self, segments: List[Dict[str, str]], 
                            participants: List[str]) -> List[ActionItem]:
        """Extract action items from meeting segments."""
        action_items = []
        
        for segment in segments:
            text = segment['text'].lower()
            speaker = segment['speaker']
            
            # Look for action item patterns
            for pattern in self.analysis_patterns['action_items']['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = ' '.join(match)
                    
                    if len(match.strip()) < 10:  # Skip very short matches
                        continue
                    
                    # Try to extract assignee
                    assignee = self._extract_assignee(text, participants)
                    if not assignee:
                        assignee = speaker  # Default to speaker
                    
                    # Extract due date
                    due_date = self._extract_due_date(text)
                    
                    # Determine priority
                    priority = self._determine_priority(match)
                    
                    action_item = ActionItem(
                        item_id=str(uuid.uuid4()),
                        description=match.strip(),
                        assigned_to=assignee,
                        assignee_email=f"{assignee.lower().replace(' ', '.')}@company.com",
                        due_date=due_date,
                        priority=priority,
                        context=segment['text'][:200],
                        category=self._categorize_action_item(match),
                        tags=self._extract_tags(match)
                    )
                    action_items.append(action_item)
        
        return action_items
    
    def _extract_decisions(self, segments: List[Dict[str, str]], 
                         participants: List[str]) -> List[MeetingDecision]:
        """Extract decisions from meeting segments."""
        decisions = []
        
        for segment in segments:
            text = segment['text'].lower()
            speaker = segment['speaker']
            
            for pattern in self.analysis_patterns['decisions']['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if len(match.strip()) < 15:  # Skip very short matches
                        continue
                    
                    decision = MeetingDecision(
                        decision_id=str(uuid.uuid4()),
                        description=match.strip(),
                        decision_maker=speaker,
                        rationale=self._extract_rationale(segment['text'], match),
                        impact=self._assess_impact(match),
                        context=segment['text'][:200],
                        affected_stakeholders=self._extract_stakeholders(segment['text'], participants)
                    )
                    decisions.append(decision)
        
        return decisions
    
    def _extract_insights(self, segments: List[Dict[str, str]], 
                        participants: List[str]) -> List[MeetingInsight]:
        """Extract insights from meeting segments."""
        insights = []
        
        for segment in segments:
            text = segment['text'].lower()
            speaker = segment['speaker']
            
            for pattern in self.analysis_patterns['insights']['patterns']:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if len(match.strip()) < 10:
                        continue
                    
                    # Determine category
                    category = self._categorize_insight(text)
                    
                    insight = MeetingInsight(
                        insight_id=str(uuid.uuid4()),
                        category=category,
                        description=match.strip(),
                        importance=self._assess_importance(text),
                        speaker=speaker,
                        context=segment['text'][:200],
                        actionable=self._is_actionable(match),
                        related_topics=self._extract_topics(match)
                    )
                    insights.append(insight)
        
        return insights
    
    def _extract_assignee(self, text: str, participants: List[str]) -> Optional[str]:
        """Extract assignee from text."""
        for pattern in self.analysis_patterns['action_items']['assignee_patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if match is a known participant
                for participant in participants:
                    if match.lower() in participant.lower() or participant.lower() in match.lower():
                        return participant
        return None
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from text."""
        # Simple date extraction - in real implementation, use more sophisticated parsing
        date_patterns = [
            r'(?:due|by|before)\s+(\w+day)',
            r'(?:due|by|before)\s+(\d{1,2}[\/\-]\d{1,2})',
            r'(?:due|by|before)\s+(next week|this week|tomorrow)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                date_str = match.group(1)
                if 'tomorrow' in date_str:
                    return datetime.now() + timedelta(days=1)
                elif 'next week' in date_str:
                    return datetime.now() + timedelta(days=7)
                elif 'this week' in date_str:
                    return datetime.now() + timedelta(days=3)
                elif 'monday' in date_str:
                    # Find next Monday
                    today = datetime.now()
                    days_ahead = 0 - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)
        
        return None
    
    def _determine_priority(self, text: str) -> TaskPriority:
        """Determine priority from text content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'critical', 'asap', 'immediately']):
            return TaskPriority.URGENT
        elif any(word in text_lower for word in ['important', 'high', 'priority', 'crucial']):
            return TaskPriority.HIGH
        elif any(word in text_lower for word in ['low', 'minor', 'when possible']):
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM
    
    def _categorize_action_item(self, text: str) -> str:
        """Categorize action item."""
        text_lower = text.lower()
        
        categories = {
            'development': ['develop', 'code', 'implement', 'build', 'create'],
            'research': ['research', 'investigate', 'analyze', 'study'],
            'communication': ['email', 'call', 'meeting', 'discuss', 'notify'],
            'documentation': ['document', 'write', 'update', 'record'],
            'testing': ['test', 'verify', 'validate', 'check'],
            'deployment': ['deploy', 'release', 'launch', 'publish']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        text_lower = text.lower()
        tags = []
        
        # Technology tags
        tech_keywords = ['api', 'database', 'frontend', 'backend', 'mobile', 'web']
        tags.extend([keyword for keyword in tech_keywords if keyword in text_lower])
        
        # Process tags
        process_keywords = ['planning', 'design', 'implementation', 'testing', 'review']
        tags.extend([keyword for keyword in process_keywords if keyword in text_lower])
        
        return tags
    
    def _extract_rationale(self, full_text: str, decision: str) -> str:
        """Extract rationale for a decision."""
        # Look for explanation patterns around the decision
        decision_index = full_text.lower().find(decision.lower())
        if decision_index == -1:
            return ""
        
        # Look for context before and after
        context_start = max(0, decision_index - 200)
        context_end = min(len(full_text), decision_index + 200)
        context = full_text[context_start:context_end]
        
        # Look for rationale patterns
        rationale_patterns = [
            r'because\s+(.+?)(?=\.|$)',
            r'since\s+(.+?)(?=\.|$)',
            r'due to\s+(.+?)(?=\.|$)',
            r'reason\s+(.+?)(?=\.|$)'
        ]
        
        for pattern in rationale_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _assess_impact(self, decision: str) -> str:
        """Assess the impact level of a decision."""
        decision_lower = decision.lower()
        
        if any(word in decision_lower for word in ['strategic', 'major', 'significant', 'critical']):
            return 'high'
        elif any(word in decision_lower for word in ['minor', 'small', 'simple']):
            return 'low'
        else:
            return 'medium'
    
    def _extract_stakeholders(self, text: str, participants: List[str]) -> List[str]:
        """Extract affected stakeholders."""
        stakeholders = []
        text_lower = text.lower()
        
        for participant in participants:
            if participant.lower() in text_lower:
                stakeholders.append(participant)
        
        return stakeholders
    
    def _categorize_insight(self, text: str) -> str:
        """Categorize insight type."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['problem', 'issue', 'challenge', 'concern']):
            return 'problem'
        elif any(word in text_lower for word in ['opportunity', 'potential', 'possibility']):
            return 'opportunity'
        elif any(word in text_lower for word in ['risk', 'danger', 'threat']):
            return 'risk'
        elif any(word in text_lower for word in ['idea', 'suggestion', 'proposal']):
            return 'idea'
        else:
            return 'observation'
    
    def _assess_importance(self, text: str) -> str:
        """Assess importance level of insight."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'crucial', 'vital', 'essential']):
            return 'high'
        elif any(word in text_lower for word in ['minor', 'small', 'slight']):
            return 'low'
        else:
            return 'medium'
    
    def _is_actionable(self, insight: str) -> bool:
        """Determine if insight is actionable."""
        actionable_indicators = ['should', 'could', 'need', 'must', 'recommend', 'suggest']
        return any(indicator in insight.lower() for indicator in actionable_indicators)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract related topics from text."""
        # Simple topic extraction - in real implementation, use NLP topic modeling
        topics = []
        
        topic_keywords = {
            'technology': ['software', 'system', 'platform', 'api', 'database'],
            'process': ['workflow', 'process', 'procedure', 'methodology'],
            'team': ['team', 'people', 'resources', 'staff'],
            'customer': ['client', 'customer', 'user', 'stakeholder'],
            'business': ['revenue', 'cost', 'profit', 'budget', 'strategy']
        }
        
        text_lower = text.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics

class MeetingSummarizer:
    """Generates meeting summaries and minutes."""
    
    def __init__(self):
        self.summary_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[MeetingType, str]:
        """Initialize summary templates for different meeting types."""
        return {
            MeetingType.STANDUP: """
Daily Standup Meeting Summary
============================

**Date:** {date}
**Duration:** {duration} minutes
**Participants:** {participants}

**Progress Updates:**
{progress_updates}

**Blockers & Challenges:**
{blockers}

**Action Items:**
{action_items}

**Next Standup:** {next_meeting}
""",
            
            MeetingType.PLANNING: """
Planning Meeting Summary
=======================

**Date:** {date}
**Duration:** {duration} minutes
**Participants:** {participants}

**Objectives Discussed:**
{objectives}

**Key Decisions:**
{decisions}

**Action Items:**
{action_items}

**Timeline & Milestones:**
{timeline}

**Next Steps:**
{next_steps}
""",
            
            MeetingType.CLIENT_MEETING: """
Client Meeting Minutes
=====================

**Date:** {date}
**Duration:** {duration} minutes
**Attendees:** {participants}

**Meeting Purpose:**
{purpose}

**Key Discussion Points:**
{discussions}

**Client Requirements:**
{requirements}

**Decisions Made:**
{decisions}

**Action Items:**
{action_items}

**Follow-up Required:**
{follow_up}
"""
        }
    
    def generate_summary(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate meeting summary based on type."""
        template = self.summary_templates.get(meeting_minutes.meeting_type)
        
        if not template:
            return self._generate_generic_summary(meeting_minutes)
        
        # Format template with meeting data
        return template.format(
            date=meeting_minutes.date.strftime("%Y-%m-%d %H:%M"),
            duration=int(meeting_minutes.duration / 60),
            participants=", ".join([p.name for p in meeting_minutes.participants]),
            action_items=self._format_action_items(meeting_minutes.action_items),
            decisions=self._format_decisions(meeting_minutes.decisions),
            discussions="\n".join(f"- {discussion}" for discussion in meeting_minutes.key_discussions),
            next_meeting=meeting_minutes.next_meeting.strftime("%Y-%m-%d") if meeting_minutes.next_meeting else "TBD",
            objectives="",  # Would be filled from meeting context
            timeline="",    # Would be extracted from action items
            next_steps=self._format_next_steps(meeting_minutes.action_items),
            progress_updates="",  # For standups
            blockers="",          # For standups
            purpose="",           # For client meetings
            requirements="",      # For client meetings
            follow_up="Yes" if meeting_minutes.follow_up_required else "No"
        )
    
    def _generate_generic_summary(self, meeting_minutes: MeetingMinutes) -> str:
        """Generate generic meeting summary."""
        return f"""
Meeting Summary: {meeting_minutes.title}
{'=' * (17 + len(meeting_minutes.title))}

**Date:** {meeting_minutes.date.strftime("%Y-%m-%d %H:%M")}
**Duration:** {int(meeting_minutes.duration / 60)} minutes
**Type:** {meeting_minutes.meeting_type.value.replace('_', ' ').title()}
**Participants:** {len(meeting_minutes.participants)} attendees

**Key Discussions:**
{chr(10).join(f'- {discussion}' for discussion in meeting_minutes.key_discussions)}

**Decisions Made:**
{self._format_decisions(meeting_minutes.decisions)}

**Action Items:**
{self._format_action_items(meeting_minutes.action_items)}

**Key Insights:**
{self._format_insights(meeting_minutes.insights)}

**Meeting Effectiveness Score:** {meeting_minutes.meeting_effectiveness_score:.1f}/10

**Summary:**
{meeting_minutes.summary}
"""
    
    def _format_action_items(self, action_items: List[ActionItem]) -> str:
        """Format action items for summary."""
        if not action_items:
            return "- No action items recorded"
        
        formatted = []
        for item in action_items:
            due_str = f" (Due: {item.due_date.strftime('%Y-%m-%d')})" if item.due_date else ""
            priority_str = f"[{item.priority.value.upper()}]" if item.priority != TaskPriority.MEDIUM else ""
            formatted.append(f"- {item.description} - Assigned to: {item.assigned_to}{due_str} {priority_str}")
        
        return "\n".join(formatted)
    
    def _format_decisions(self, decisions: List[MeetingDecision]) -> str:
        """Format decisions for summary."""
        if not decisions:
            return "- No major decisions recorded"
        
        formatted = []
        for decision in decisions:
            impact_str = f"[{decision.impact.upper()} IMPACT]" if decision.impact != "medium" else ""
            formatted.append(f"- {decision.description} {impact_str}")
            if decision.rationale:
                formatted.append(f"  Rationale: {decision.rationale}")
        
        return "\n".join(formatted)
    
    def _format_insights(self, insights: List[MeetingInsight]) -> str:
        """Format insights for summary."""
        if not insights:
            return "- No key insights recorded"
        
        formatted = []
        for insight in insights:
            category_str = f"[{insight.category.upper()}]"
            actionable_str = " (Actionable)" if insight.actionable else ""
            formatted.append(f"- {category_str} {insight.description}{actionable_str}")
        
        return "\n".join(formatted)
    
    def _format_next_steps(self, action_items: List[ActionItem]) -> str:
        """Format next steps from action items."""
        high_priority_items = [item for item in action_items if item.priority in [TaskPriority.HIGH, TaskPriority.URGENT]]
        
        if not high_priority_items:
            return "Continue with assigned action items"
        
        return "\n".join(f"- {item.description}" for item in high_priority_items[:3])

class EmailCommunicationManager:
    """Manages automated email communications."""
    
    def __init__(self, smtp_server: str = "localhost", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_templates = self._initialize_email_templates()
    
    def _initialize_email_templates(self) -> Dict[str, EmailTemplate]:
        """Initialize email templates."""
        return {
            'meeting_summary': EmailTemplate(
                template_id='meeting_summary',
                name='Meeting Summary Distribution',
                subject_template='Meeting Summary: {meeting_title} - {date}',
                body_template="""
Dear Team,

Please find attached the summary of our meeting held on {date}.

**Meeting Details:**
- Duration: {duration} minutes
- Participants: {participant_count} attendees

**Key Highlights:**
{key_highlights}

**Action Items Summary:**
{action_items_count} action items were assigned. Please review your individual assignments below.

**Next Steps:**
{next_steps}

The full meeting minutes are attached to this email.

Best regards,
Meeting Assistant
                """,
                recipient_type='all_participants',
                include_attachments=True
            ),
            
            'action_item_assignment': EmailTemplate(
                template_id='action_item_assignment',
                name='Action Item Assignment',
                subject_template='Action Item Assigned: {action_item_title}',
                body_template="""
Hello {assignee_name},

You have been assigned a new action item from the meeting "{meeting_title}" held on {date}.

**Action Item Details:**
- Description: {action_item_description}
- Priority: {priority}
- Due Date: {due_date}
- Category: {category}

**Context:**
{context}

**Meeting Context:**
This action item was discussed during: {meeting_title}

Please confirm receipt and let us know if you have any questions.

Best regards,
Meeting Assistant
                """,
                recipient_type='assignees',
                include_attachments=False,
                auto_send=True
            ),
            
            'follow_up_reminder': EmailTemplate(
                template_id='follow_up_reminder',
                name='Follow-up Reminder',
                subject_template='Follow-up Required: {meeting_title}',
                body_template="""
Hello {recipient_name},

This is a follow-up regarding the meeting "{meeting_title}" held on {date}.

**Items Requiring Follow-up:**
{follow_up_items}

**Upcoming Deadlines:**
{upcoming_deadlines}

**Status Check:**
Please provide updates on your assigned action items at your earliest convenience.

Best regards,
Meeting Assistant
                """,
                recipient_type='assignees',
                send_delay_minutes=1440  # 24 hours
            )
        }
    
    async def send_meeting_summary(self, meeting_minutes: MeetingMinutes, 
                                 summary_text: str, sender_email: str) -> Dict[str, bool]:
        """Send meeting summary to all participants."""
        template = self.email_templates['meeting_summary']
        results = {}
        
        # Prepare email content
        subject = template.subject_template.format(
            meeting_title=meeting_minutes.title,
            date=meeting_minutes.date.strftime("%Y-%m-%d")
        )
        
        key_highlights = self._extract_key_highlights(meeting_minutes)
        next_steps = self._extract_next_steps(meeting_minutes)
        
        body = template.body_template.format(
            date=meeting_minutes.date.strftime("%Y-%m-%d %H:%M"),
            duration=int(meeting_minutes.duration / 60),
            participant_count=len(meeting_minutes.participants),
            key_highlights=key_highlights,
            action_items_count=len(meeting_minutes.action_items),
            next_steps=next_steps
        )
        
        # Send to all participants
        for participant in meeting_minutes.participants:
            try:
                success = await self._send_email(
                    sender_email,
                    participant.email,
                    subject,
                    body,
                    attachments=[('meeting_summary.txt', summary_text)]
                )
                results[participant.email] = success
                logger.info(f"Meeting summary sent to {participant.email}: {'Success' if success else 'Failed'}")
            except Exception as e:
                logger.error(f"Failed to send meeting summary to {participant.email}: {str(e)}")
                results[participant.email] = False
        
        return results
    
    async def send_action_item_notifications(self, meeting_minutes: MeetingMinutes, 
                                           sender_email: str) -> Dict[str, bool]:
        """Send individual action item notifications."""
        template = self.email_templates['action_item_assignment']
        results = {}
        
        # Group action items by assignee
        items_by_assignee = {}
        for item in meeting_minutes.action_items:
            if item.assignee_email not in items_by_assignee:
                items_by_assignee[item.assignee_email] = []
            items_by_assignee[item.assignee_email].append(item)
        
        # Send notifications
        for assignee_email, items in items_by_assignee.items():
            try:
                for item in items:
                    subject = template.subject_template.format(
                        action_item_title=item.description[:50] + "..." if len(item.description) > 50 else item.description
                    )
                    
                    body = template.body_template.format(
                        assignee_name=item.assigned_to,
                        meeting_title=meeting_minutes.title,
                        date=meeting_minutes.date.strftime("%Y-%m-%d"),
                        action_item_description=item.description,
                        priority=item.priority.value.title(),
                        due_date=item.due_date.strftime("%Y-%m-%d") if item.due_date else "Not specified",
                        category=item.category.title(),
                        context=item.context
                    )
                    
                    success = await self._send_email(sender_email, assignee_email, subject, body)
                    results[f"{assignee_email}_{item.item_id}"] = success
            
            except Exception as e:
                logger.error(f"Failed to send action item notification to {assignee_email}: {str(e)}")
                results[assignee_email] = False
        
        return results
    
    async def _send_email(self, sender_email: str, recipient_email: str, 
                         subject: str, body: str, attachments: List[Tuple[str, str]] = None) -> bool:
        """Send email (mock implementation)."""
        try:
            # Mock email sending - in real implementation, use actual SMTP
            logger.info(f"Mock Email Sent:")
            logger.info(f"  From: {sender_email}")
            logger.info(f"  To: {recipient_email}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Body length: {len(body)} characters")
            if attachments:
                logger.info(f"  Attachments: {len(attachments)} files")
            
            # Simulate send delay
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _extract_key_highlights(self, meeting_minutes: MeetingMinutes) -> str:
        """Extract key highlights from meeting."""
        highlights = []
        
        if meeting_minutes.decisions:
            highlights.append(f"- {len(meeting_minutes.decisions)} key decisions made")
        
        if meeting_minutes.action_items:
            highlights.append(f"- {len(meeting_minutes.action_items)} action items assigned")
        
        if meeting_minutes.insights:
            high_importance = [i for i in meeting_minutes.insights if i.importance == 'high']
            if high_importance:
                highlights.append(f"- {len(high_importance)} high-importance insights identified")
        
        return "\n".join(highlights) if highlights else "- Meeting completed successfully"
    
    def _extract_next_steps(self, meeting_minutes: MeetingMinutes) -> str:
        """Extract next steps from meeting."""
        urgent_items = [item for item in meeting_minutes.action_items if item.priority == TaskPriority.URGENT]
        high_items = [item for item in meeting_minutes.action_items if item.priority == TaskPriority.HIGH]
        
        next_steps = []
        
        if urgent_items:
            next_steps.append(f"- Address {len(urgent_items)} urgent action items immediately")
        
        if high_items:
            next_steps.append(f"- Complete {len(high_items)} high-priority items")
        
        if meeting_minutes.next_meeting:
            next_steps.append(f"- Next meeting scheduled for {meeting_minutes.next_meeting.strftime('%Y-%m-%d')}")
        
        return "\n".join(next_steps) if next_steps else "- Continue with assigned tasks"

class CalendarIntegration:
    """Handles calendar integration and event scheduling."""
    
    def __init__(self):
        self.calendar_providers = ['google', 'outlook', 'office365']
    
    async def create_follow_up_event(self, meeting_minutes: MeetingMinutes, 
                                   follow_up_date: datetime) -> CalendarEvent:
        """Create follow-up meeting event."""
        
        # Determine follow-up agenda based on current meeting
        agenda = self._generate_follow_up_agenda(meeting_minutes)
        
        event = CalendarEvent(
            event_id=str(uuid.uuid4()),
            title=f"Follow-up: {meeting_minutes.title}",
            description=f"Follow-up meeting to review action items and progress from {meeting_minutes.date.strftime('%Y-%m-%d')}",
            start_time=follow_up_date,
            end_time=follow_up_date + timedelta(minutes=60),
            attendees=[p.email for p in meeting_minutes.participants],
            agenda=agenda,
            event_type="follow_up_meeting",
            preparation_materials=[
                "Previous meeting minutes",
                "Action item status updates",
                "Progress reports"
            ]
        )
        
        logger.info(f"Created follow-up event: {event.title} for {follow_up_date}")
        return event
    
    def _generate_follow_up_agenda(self, meeting_minutes: MeetingMinutes) -> List[str]:
        """Generate agenda for follow-up meeting."""
        agenda = [
            "Review action items from previous meeting",
            "Status updates from team members"
        ]
        
        # Add specific items based on previous meeting
        if meeting_minutes.decisions:
            agenda.append("Review implementation of decisions")
        
        if any(item.priority == TaskPriority.URGENT for item in meeting_minutes.action_items):
            agenda.append("Address urgent items status")
        
        agenda.extend([
            "Identify any blockers or challenges",
            "Plan next steps",
            "Schedule next check-in if needed"
        ])
        
        return agenda
    
    async def schedule_recurring_meetings(self, base_meeting: MeetingMinutes, 
                                        recurrence_pattern: str) -> List[CalendarEvent]:
        """Schedule recurring meetings based on pattern."""
        events = []
        
        # Parse recurrence pattern (simplified)
        if recurrence_pattern == "weekly":
            next_date = meeting_minutes.date + timedelta(weeks=1)
            for i in range(8):  # Next 8 weeks
                event = CalendarEvent(
                    event_id=str(uuid.uuid4()),
                    title=base_meeting.title,
                    description=f"Recurring {base_meeting.meeting_type.value} meeting",
                    start_time=next_date + timedelta(weeks=i),
                    end_time=next_date + timedelta(weeks=i, hours=1),
                    attendees=[p.email for p in base_meeting.participants],
                    event_type="recurring_meeting",
                    recurrence="weekly"
                )
                events.append(event)
        
        return events

class ProjectManagementIntegration:
    """Integrates with project management tools."""
    
    def __init__(self):
        self.integrations = {
            IntegrationType.JIRA: self._jira_integration,
            IntegrationType.ASANA: self._asana_integration,
            IntegrationType.TRELLO: self._trello_integration,
        }
    
    async def create_tasks(self, action_items: List[ActionItem], 
                          integration_type: IntegrationType,
                          project_id: str) -> Dict[str, Any]:
        """Create tasks in project management system."""
        
        if integration_type not in self.integrations:
            logger.error(f"Integration type {integration_type} not supported")
            return {"success": False, "error": "Integration not supported"}
        
        integration_func = self.integrations[integration_type]
        return await integration_func(action_items, project_id, "create_tasks")
    
    async def _jira_integration(self, action_items: List[ActionItem], 
                              project_key: str, operation: str) -> Dict[str, Any]:
        """Mock JIRA integration."""
        logger.info(f"JIRA Integration: {operation}")
        
        created_issues = []
        for item in action_items:
            # Mock JIRA issue creation
            issue_data = {
                "key": f"{project_key}-{len(created_issues) + 1}",
                "summary": item.description,
                "assignee": item.assigned_to,
                "priority": self._map_priority_to_jira(item.priority),
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "labels": item.tags
            }
            created_issues.append(issue_data)
            logger.info(f"Created JIRA issue: {issue_data['key']} - {item.description[:50]}...")
        
        return {
            "success": True,
            "created_issues": created_issues,
            "integration": "jira"
        }
    
    async def _asana_integration(self, action_items: List[ActionItem], 
                               project_id: str, operation: str) -> Dict[str, Any]:
        """Mock Asana integration."""
        logger.info(f"Asana Integration: {operation}")
        
        created_tasks = []
        for item in action_items:
            task_data = {
                "gid": str(uuid.uuid4()),
                "name": item.description,
                "assignee": item.assigned_to,
                "due_on": item.due_date.date().isoformat() if item.due_date else None,
                "priority": item.priority.value,
                "project": project_id
            }
            created_tasks.append(task_data)
            logger.info(f"Created Asana task: {task_data['gid']} - {item.description[:50]}...")
        
        return {
            "success": True,
            "created_tasks": created_tasks,
            "integration": "asana"
        }
    
    async def _trello_integration(self, action_items: List[ActionItem], 
                                board_id: str, operation: str) -> Dict[str, Any]:
        """Mock Trello integration."""
        logger.info(f"Trello Integration: {operation}")
        
        created_cards = []
        for item in action_items:
            card_data = {
                "id": str(uuid.uuid4()),
                "name": item.description,
                "desc": f"Priority: {item.priority.value}\nDue: {item.due_date if item.due_date else 'Not set'}",
                "due": item.due_date.isoformat() if item.due_date else None,
                "board": board_id
            }
            created_cards.append(card_data)
            logger.info(f"Created Trello card: {card_data['id']} - {item.description[:50]}...")
        
        return {
            "success": True,
            "created_cards": created_cards,
            "integration": "trello"
        }
    
    def _map_priority_to_jira(self, priority: TaskPriority) -> str:
        """Map internal priority to JIRA priority."""
        mapping = {
            TaskPriority.LOW: "Low",
            TaskPriority.MEDIUM: "Medium",
            TaskPriority.HIGH: "High",
            TaskPriority.URGENT: "Highest"
        }
        return mapping.get(priority, "Medium")

class MeetingDatabase:
    """SQLite database for storing meeting information."""
    
    def __init__(self, db_path: str = "meetings.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Meeting minutes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_minutes (
                    meeting_id TEXT PRIMARY KEY,
                    title TEXT,
                    meeting_type TEXT,
                    date TIMESTAMP,
                    duration REAL,
                    summary TEXT,
                    effectiveness_score REAL,
                    follow_up_required BOOLEAN,
                    created_by TEXT,
                    metadata TEXT
                )
            """)
            
            # Participants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meeting_id TEXT,
                    participant_id TEXT,
                    name TEXT,
                    email TEXT,
                    role TEXT,
                    attendance_status TEXT,
                    speaking_time REAL,
                    FOREIGN KEY (meeting_id) REFERENCES meeting_minutes (meeting_id)
                )
            """)
            
            # Action items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_items (
                    item_id TEXT PRIMARY KEY,
                    meeting_id TEXT,
                    description TEXT,
                    assigned_to TEXT,
                    assignee_email TEXT,
                    due_date TIMESTAMP,
                    priority TEXT,
                    status TEXT,
                    category TEXT,
                    created_at TIMESTAMP,
                    FOREIGN KEY (meeting_id) REFERENCES meeting_minutes (meeting_id)
                )
            """)
            
            # Decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_decisions (
                    decision_id TEXT PRIMARY KEY,
                    meeting_id TEXT,
                    description TEXT,
                    decision_maker TEXT,
                    rationale TEXT,
                    impact TEXT,
                    timestamp REAL,
                    FOREIGN KEY (meeting_id) REFERENCES meeting_minutes (meeting_id)
                )
            """)
            
            conn.commit()
    
    def store_meeting_minutes(self, meeting_minutes: MeetingMinutes):
        """Store complete meeting minutes."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store meeting
            cursor.execute("""
                INSERT OR REPLACE INTO meeting_minutes
                (meeting_id, title, meeting_type, date, duration, summary,
                 effectiveness_score, follow_up_required, created_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_minutes.meeting_id, meeting_minutes.title,
                meeting_minutes.meeting_type.value, meeting_minutes.date,
                meeting_minutes.duration, meeting_minutes.summary,
                meeting_minutes.meeting_effectiveness_score,
                meeting_minutes.follow_up_required, meeting_minutes.created_by,
                json.dumps(meeting_minutes.metadata)
            ))
            
            # Store participants
            for participant in meeting_minutes.participants:
                cursor.execute("""
                    INSERT INTO meeting_participants
                    (meeting_id, participant_id, name, email, role, attendance_status, speaking_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    meeting_minutes.meeting_id, participant.participant_id,
                    participant.name, participant.email, participant.role,
                    participant.attendance_status, participant.speaking_time
                ))
            
            # Store action items
            for item in meeting_minutes.action_items:
                cursor.execute("""
                    INSERT OR REPLACE INTO action_items
                    (item_id, meeting_id, description, assigned_to, assignee_email,
                     due_date, priority, status, category, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.item_id, meeting_minutes.meeting_id, item.description,
                    item.assigned_to, item.assignee_email, item.due_date,
                    item.priority.value, item.status.value, item.category,
                    item.created_at
                ))
            
            # Store decisions
            for decision in meeting_minutes.decisions:
                cursor.execute("""
                    INSERT OR REPLACE INTO meeting_decisions
                    (decision_id, meeting_id, description, decision_maker,
                     rationale, impact, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision.decision_id, meeting_minutes.meeting_id,
                    decision.description, decision.decision_maker,
                    decision.rationale, decision.impact, decision.timestamp
                ))
            
            conn.commit()

class AutomatedMeetingCommunicationSystem:
    """Main system for automated meeting and communication features."""
    
    def __init__(self, smtp_server: str = "localhost", db_path: str = "meetings.db"):
        self.meeting_analyzer = MeetingAnalyzer()
        self.meeting_summarizer = MeetingSummarizer()
        self.email_manager = EmailCommunicationManager(smtp_server)
        self.calendar_integration = CalendarIntegration()
        self.project_integration = ProjectManagementIntegration()
        self.database = MeetingDatabase(db_path)
        
        logger.info("Automated Meeting Communication System initialized")
    
    async def process_meeting(self, 
                            title: str,
                            meeting_type: MeetingType,
                            transcript: str,
                            participants: List[Dict[str, str]],
                            meeting_date: datetime,
                            duration: float,
                            sender_email: str = "meetings@company.com") -> MeetingMinutes:
        """Process complete meeting workflow."""
        try:
            meeting_id = str(uuid.uuid4())
            logger.info(f"Processing meeting: {title}")
            
            # 1. Create participant objects
            meeting_participants = []
            participant_names = []
            
            for p_data in participants:
                participant = MeetingParticipant(
                    participant_id=str(uuid.uuid4()),
                    name=p_data['name'],
                    email=p_data['email'],
                    role=p_data.get('role', 'participant'),
                    department=p_data.get('department'),
                    attendance_status=p_data.get('status', 'present')
                )
                meeting_participants.append(participant)
                participant_names.append(p_data['name'])
            
            # 2. Analyze transcript
            action_items, decisions, insights = self.meeting_analyzer.analyze_meeting_transcript(
                transcript, participant_names, duration
            )
            
            # 3. Generate key discussions (mock extraction)
            key_discussions = self._extract_key_discussions(transcript)
            
            # 4. Calculate effectiveness score
            effectiveness_score = self._calculate_effectiveness_score(
                action_items, decisions, insights, duration, len(meeting_participants)
            )
            
            # 5. Create meeting minutes
            meeting_minutes = MeetingMinutes(
                meeting_id=meeting_id,
                title=title,
                meeting_type=meeting_type,
                date=meeting_date,
                duration=duration,
                participants=meeting_participants,
                agenda_items=self._extract_agenda_items(transcript),
                key_discussions=key_discussions,
                action_items=action_items,
                decisions=decisions,
                insights=insights,
                summary="",  # Will be generated next
                meeting_effectiveness_score=effectiveness_score,
                follow_up_required=len(action_items) > 0 or any(d.follow_up_required for d in decisions)
            )
            
            # 6. Generate summary
            summary = self.meeting_summarizer.generate_summary(meeting_minutes)
            meeting_minutes.summary = summary
            
            # 7. Store in database
            self.database.store_meeting_minutes(meeting_minutes)
            
            # 8. Send communications
            await self._send_automated_communications(meeting_minutes, summary, sender_email)
            
            logger.info(f"Meeting processed successfully: {len(action_items)} action items, "
                       f"{len(decisions)} decisions, effectiveness: {effectiveness_score:.1f}/10")
            
            return meeting_minutes
            
        except Exception as e:
            logger.error(f"Failed to process meeting: {str(e)}")
            raise
    
    async def _send_automated_communications(self, meeting_minutes: MeetingMinutes, 
                                          summary: str, sender_email: str):
        """Send all automated communications."""
        
        # Send meeting summary to all participants
        summary_results = await self.email_manager.send_meeting_summary(
            meeting_minutes, summary, sender_email
        )
        
        successful_summaries = sum(1 for success in summary_results.values() if success)
        logger.info(f"Meeting summaries sent: {successful_summaries}/{len(summary_results)}")
        
        # Send action item notifications
        if meeting_minutes.action_items:
            notification_results = await self.email_manager.send_action_item_notifications(
                meeting_minutes, sender_email
            )
            successful_notifications = sum(1 for success in notification_results.values() if success)
            logger.info(f"Action item notifications sent: {successful_notifications}/{len(notification_results)}")
    
    async def create_project_tasks(self, meeting_id: str, integration_type: IntegrationType,
                                 project_id: str) -> Dict[str, Any]:
        """Create tasks in project management system."""
        
        # Get meeting from database (simplified - would implement proper retrieval)
        # For demo, we'll create mock data
        mock_action_items = [
            ActionItem(
                item_id=str(uuid.uuid4()),
                description="Update API documentation",
                assigned_to="John Smith",
                assignee_email="john.smith@company.com",
                priority=TaskPriority.HIGH,
                category="documentation",
                due_date=datetime.now() + timedelta(days=7)
            ),
            ActionItem(
                item_id=str(uuid.uuid4()),
                description="Review security implementation",
                assigned_to="Sarah Jones",
                assignee_email="sarah.jones@company.com",
                priority=TaskPriority.MEDIUM,
                category="security",
                due_date=datetime.now() + timedelta(days=5)
            )
        ]
        
        return await self.project_integration.create_tasks(
            mock_action_items, integration_type, project_id
        )
    
    async def schedule_follow_up_meeting(self, meeting_id: str, 
                                       days_ahead: int = 7) -> CalendarEvent:
        """Schedule follow-up meeting."""
        follow_up_date = datetime.now() + timedelta(days=days_ahead)
        
        # For demo, create mock meeting minutes
        mock_meeting = MeetingMinutes(
            meeting_id=meeting_id,
            title="Sample Meeting",
            meeting_type=MeetingType.PLANNING,
            date=datetime.now(),
            duration=3600,
            participants=[
                MeetingParticipant("1", "John Smith", "john@company.com", "manager"),
                MeetingParticipant("2", "Sarah Jones", "sarah@company.com", "developer")
            ],
            agenda_items=[],
            key_discussions=[],
            action_items=[],
            decisions=[],
            insights=[]
        )
        
        return await self.calendar_integration.create_follow_up_event(
            mock_meeting, follow_up_date
        )
    
    def _extract_key_discussions(self, transcript: str) -> List[str]:
        """Extract key discussion points."""
        # Simple extraction - in real implementation, use more sophisticated NLP
        sentences = transcript.split('.')
        discussions = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(keyword in sentence.lower() for keyword in 
                                        ['discuss', 'talk about', 'important', 'key', 'main']):
                discussions.append(sentence)
                if len(discussions) >= 5:  # Limit to top 5
                    break
        
        return discussions
    
    def _extract_agenda_items(self, transcript: str) -> List[str]:
        """Extract agenda items."""
        # Mock agenda extraction
        agenda_patterns = [
            r'agenda item[:\-\s]*(.+?)(?=\.|$)',
            r'first[,\s]+(.+?)(?=\.|$)',
            r'second[,\s]+(.+?)(?=\.|$)',
            r'next[,\s]+(.+?)(?=\.|$)'
        ]
        
        agenda_items = []
        for pattern in agenda_patterns:
            matches = re.findall(pattern, transcript.lower())
            for match in matches:
                if len(match.strip()) > 10:
                    agenda_items.append(match.strip().title())
        
        return agenda_items[:5]  # Limit to 5 items
    
    def _calculate_effectiveness_score(self, action_items: List[ActionItem], 
                                     decisions: List[MeetingDecision],
                                     insights: List[MeetingInsight], 
                                     duration: float, participant_count: int) -> float:
        """Calculate meeting effectiveness score (0-10)."""
        
        score = 5.0  # Base score
        
        # Positive factors
        if action_items:
            score += min(2.0, len(action_items) * 0.3)  # Max +2 for action items
        
        if decisions:
            score += min(1.5, len(decisions) * 0.5)  # Max +1.5 for decisions
        
        if insights:
            high_value_insights = [i for i in insights if i.importance == 'high']
            score += min(1.0, len(high_value_insights) * 0.3)  # Max +1 for insights
        
        # Duration factor (optimal 30-90 minutes)
        duration_minutes = duration / 60
        if 30 <= duration_minutes <= 90:
            score += 0.5
        elif duration_minutes > 120:
            score -= 1.0  # Penalty for very long meetings
        
        # Participant engagement (mock calculation)
        if participant_count > 1:
            score += 0.5
        
        return min(10.0, max(1.0, score))

# Demo function
async def demo_automated_meeting_system():
    """Demonstrate automated meeting and communication system."""
    print("📅 Automated Meeting & Communication System Demo")
    print("=" * 55)
    
    # Initialize system
    system = AutomatedMeetingCommunicationSystem()
    
    # Sample meeting data
    sample_transcript = """
JOHN SMITH: Good morning everyone. Let's start today's planning meeting. We have three main agenda items to cover.

SARAH JONES: Thanks John. Before we begin, I want to mention that we've completed the user authentication module ahead of schedule.

JOHN SMITH: That's great news! For today's meeting, we need to discuss the API development timeline, review the security requirements, and plan the next sprint.

MIKE WILSON: Regarding the API, I think we should prioritize the user management endpoints first. They're critical for the mobile app integration.

SARAH JONES: I agree with Mike. Also, we need to address the security vulnerabilities we found in the last code review. I can take the lead on that.

JOHN SMITH: Perfect. Let's make that an action item. Sarah, can you complete the security review by Friday? It's high priority.

SARAH JONES: Absolutely. I'll also update the security documentation while I'm at it.

MIKE WILSON: For the API development, we should set up automated testing. That's crucial for maintaining quality as we scale.

JOHN SMITH: Good point Mike. Can you handle setting up the testing infrastructure? Let's target next Tuesday for completion.

SARAH JONES: One more important issue - we need to decide on the database migration strategy. The current approach might cause downtime.

JOHN SMITH: That's a critical decision. After reviewing the options, I think we should go with the blue-green deployment approach. It minimizes risk and downtime.

MIKE WILSON: Agreed. That decision makes sense given our infrastructure constraints.

JOHN SMITH: Great! Any questions before we wrap up? Next meeting is scheduled for next Thursday to review progress on these action items.
    """
    
    participants = [
        {"name": "John Smith", "email": "john.smith@company.com", "role": "manager", "department": "engineering"},
        {"name": "Sarah Jones", "email": "sarah.jones@company.com", "role": "developer", "department": "engineering"},
        {"name": "Mike Wilson", "email": "mike.wilson@company.com", "role": "developer", "department": "engineering"}
    ]
    
    meeting_date = datetime.now() - timedelta(hours=1)
    duration = 1800  # 30 minutes
    
    print(f"📝 Sample Meeting:")
    print(f"   Title: Sprint Planning Meeting")
    print(f"   Participants: {len(participants)} attendees")
    print(f"   Duration: {duration/60:.0f} minutes")
    print(f"   Date: {meeting_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Test 1: Process complete meeting
    print(f"\n🔄 Test 1: Processing Complete Meeting")
    print("-" * 35)
    
    meeting_minutes = await system.process_meeting(
        title="Sprint Planning Meeting",
        meeting_type=MeetingType.PLANNING,
        transcript=sample_transcript,
        participants=participants,
        meeting_date=meeting_date,
        duration=duration,
        sender_email="meetings@company.com"
    )
    
    print(f"✅ Meeting processed: {meeting_minutes.meeting_id}")
    print(f"   Action items: {len(meeting_minutes.action_items)} identified")
    print(f"   Decisions: {len(meeting_minutes.decisions)} recorded")
    print(f"   Insights: {len(meeting_minutes.insights)} extracted")
    print(f"   Effectiveness score: {meeting_minutes.meeting_effectiveness_score:.1f}/10")
    
    # Test 2: Action items analysis
    print(f"\n📋 Test 2: Action Items Extracted")
    print("-" * 30)
    
    for i, item in enumerate(meeting_minutes.action_items, 1):
        due_str = f" (Due: {item.due_date.strftime('%Y-%m-%d')})" if item.due_date else ""
        print(f"   {i}. {item.description}")
        print(f"      Assigned to: {item.assigned_to} | Priority: {item.priority.value.title()}{due_str}")
    
    # Test 3: Decisions analysis
    print(f"\n⚖️  Test 3: Decisions Made")
    print("-" * 25)
    
    for i, decision in enumerate(meeting_minutes.decisions, 1):
        print(f"   {i}. {decision.description}")
        print(f"      Decision maker: {decision.decision_maker} | Impact: {decision.impact}")
        if decision.rationale:
            print(f"      Rationale: {decision.rationale}")
    
    # Test 4: Meeting summary generation
    print(f"\n📄 Test 4: Generated Meeting Summary")
    print("-" * 35)
    
    summary_preview = meeting_minutes.summary.split('\n')[:10]  # First 10 lines
    for line in summary_preview:
        if line.strip():
            print(f"   {line}")
    print("   ... (truncated)")
    
    # Test 5: Project management integration
    print(f"\n🔗 Test 5: Project Management Integration")
    print("-" * 40)
    
    # Test JIRA integration
    jira_result = await system.create_project_tasks(
        meeting_minutes.meeting_id, IntegrationType.JIRA, "PROJ"
    )
    
    if jira_result['success']:
        print(f"   ✅ JIRA Integration: {len(jira_result['created_issues'])} issues created")
        for issue in jira_result['created_issues'][:2]:  # Show first 2
            print(f"      - {issue['key']}: {issue['summary'][:50]}...")
    
    # Test Asana integration
    asana_result = await system.create_project_tasks(
        meeting_minutes.meeting_id, IntegrationType.ASANA, "12345"
    )
    
    if asana_result['success']:
        print(f"   ✅ Asana Integration: {len(asana_result['created_tasks'])} tasks created")
        for task in asana_result['created_tasks'][:2]:  # Show first 2
            print(f"      - {task['name'][:50]}...")
    
    # Test 6: Calendar integration
    print(f"\n📅 Test 6: Calendar Integration")
    print("-" * 30)
    
    follow_up_event = await system.schedule_follow_up_meeting(
        meeting_minutes.meeting_id, days_ahead=7
    )
    
    print(f"   ✅ Follow-up meeting scheduled:")
    print(f"      Title: {follow_up_event.title}")
    print(f"      Date: {follow_up_event.start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"      Attendees: {len(follow_up_event.attendees)} people")
    print(f"      Agenda items: {len(follow_up_event.agenda)}")
    
    # Test 7: Meeting insights
    print(f"\n💡 Test 7: Meeting Insights")
    print("-" * 25)
    
    for i, insight in enumerate(meeting_minutes.insights, 1):
        actionable_str = " (Actionable)" if insight.actionable else ""
        print(f"   {i}. [{insight.category.upper()}] {insight.description}")
        print(f"      Importance: {insight.importance} | Speaker: {insight.speaker}{actionable_str}")
    
    # Test 8: Effectiveness analysis
    print(f"\n📊 Test 8: Meeting Effectiveness Analysis")
    print("-" * 40)
    
    effectiveness = meeting_minutes.meeting_effectiveness_score
    
    if effectiveness >= 8:
        rating = "Excellent"
    elif effectiveness >= 6:
        rating = "Good"
    elif effectiveness >= 4:
        rating = "Average"
    else:
        rating = "Needs Improvement"
    
    print(f"   Overall Score: {effectiveness:.1f}/10 ({rating})")
    print(f"   Factors contributing to score:")
    print(f"   - Action items generated: {len(meeting_minutes.action_items)}")
    print(f"   - Decisions made: {len(meeting_minutes.decisions)}")
    print(f"   - Duration: {duration/60:.0f} minutes (optimal: 30-90 min)")
    print(f"   - Participant engagement: Active")
    print(f"   - Follow-up required: {'Yes' if meeting_minutes.follow_up_required else 'No'}")
    
    # Cleanup
    print(f"\n🧹 Cleanup")
    print("-" * 30)
    
    try:
        os.remove("meetings.db")
        print("Database cleaned up")
    except Exception as e:
        print(f"Cleanup note: {str(e)}")
    
    print(f"\n✅ Automated meeting system demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_automated_meeting_system())