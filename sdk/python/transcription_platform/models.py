#!/usr/bin/env python3
"""
Transcription Platform Models
Data models for SDK responses
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Speaker:
    """Speaker in a transcript"""
    id: str
    name: Optional[str] = None
    
@dataclass
class TranscriptSegment:
    """Segment of a transcript"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class Transcript:
    """Transcript object"""
    id: str
    status: str
    created_at: str
    language: str
    duration: Optional[float] = None
    completed_at: Optional[str] = None
    title: Optional[str] = None
    audio_url: Optional[str] = None
    text: Optional[str] = None
    speakers: List[Speaker] = field(default_factory=list)
    segments: List[TranscriptSegment] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def __post_init__(self):
        """Convert nested data to objects"""
        if self.speakers and isinstance(self.speakers[0], dict):
            self.speakers = [Speaker(**s) for s in self.speakers]
        
        if self.segments and isinstance(self.segments[0], dict):
            self.segments = [TranscriptSegment(**s) for s in self.segments]
    
    @property
    def is_complete(self) -> bool:
        """Check if transcript is complete"""
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """Check if transcript failed"""
        return self.status == 'failed'
    
    @property
    def word_count(self) -> int:
        """Get word count"""
        if self.text:
            return len(self.text.split())
        return sum(len(s.text.split()) for s in self.segments)

@dataclass
class TeamMember:
    """Team member"""
    id: int
    username: str
    email: str
    role: str
    joined_at: str

@dataclass
class Team:
    """Team object"""
    id: int
    name: str
    created_at: str
    description: Optional[str] = None
    members: List[TeamMember] = field(default_factory=list)
    
    def __post_init__(self):
        """Convert nested data to objects"""
        if self.members and isinstance(self.members[0], dict):
            self.members = [TeamMember(**m) for m in self.members]

@dataclass
class Usage:
    """Usage statistics"""
    period: Dict[str, str]
    usage: Dict[str, Dict[str, Any]]
    limits: Dict[str, int]
    
    def get_usage(self, usage_type: str) -> Dict[str, Any]:
        """Get usage for specific type"""
        return self.usage.get(usage_type, {})
    
    def get_limit(self, usage_type: str) -> int:
        """Get limit for specific type"""
        return self.limits.get(usage_type, 0)
    
    def get_remaining(self, usage_type: str) -> int:
        """Get remaining quota for specific type"""
        usage = self.get_usage(usage_type)
        limit = self.get_limit(usage_type)
        current = usage.get('current', 0)
        return max(0, limit - current)

@dataclass
class Webhook:
    """Webhook configuration"""
    id: int
    name: str
    url: str
    events: List[str]
    status: str
    created_at: str
    secret: Optional[str] = None
    last_triggered_at: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0

@dataclass
class WebhookEvent:
    """Webhook event payload"""
    id: str
    type: str
    created: str
    data: Dict[str, Any]
    
    @classmethod
    def from_request(cls, request_body: Dict[str, Any]) -> 'WebhookEvent':
        """Create WebhookEvent from request body"""
        return cls(**request_body)