"""
Data models for the Transcription API Python SDK
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class TranscriptStatus(str, Enum):
    """Status of a transcription job"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUEUED = "queued"


class TeamRole(str, Enum):
    """Team member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserRole(str, Enum):
    """User roles in the system"""
    USER = "user"
    ADMIN = "admin"
    ENTERPRISE = "enterprise"


@dataclass
class TranscriptionOptions:
    """Options for transcription requests"""
    language: str = "auto"
    method: str = "basic"  # "basic" or "advanced"
    team_id: Optional[int] = None
    speaker_detection: bool = False
    sentiment_analysis: bool = False
    entity_extraction: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        return {
            "language": self.language,
            "method": self.method,
            "team_id": self.team_id,
            "speaker_detection": self.speaker_detection,
            "sentiment_analysis": self.sentiment_analysis,
            "entity_extraction": self.entity_extraction
        }


@dataclass
class AnalysisOptions:
    """Options for content analysis"""
    extract_entities: bool = True
    sentiment_analysis: bool = True
    topic_modeling: bool = False
    summarization: bool = True
    action_items: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        return {
            "extract_entities": self.extract_entities,
            "sentiment_analysis": self.sentiment_analysis,
            "topic_modeling": self.topic_modeling,
            "summarization": self.summarization,
            "action_items": self.action_items
        }


@dataclass
class Transcript:
    """Represents a transcription"""
    id: str
    title: str
    status: TranscriptStatus
    created_at: datetime
    duration: Optional[float] = None
    text: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    confidence: Optional[float] = None
    language: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    team_id: Optional[int] = None
    summary: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    speakers: Optional[List[Dict[str, Any]]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transcript':
        """Create Transcript from API response"""
        # Parse datetime
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Parse entities if it's a string
        entities = data.get("entities")
        if isinstance(entities, str):
            import json
            try:
                entities = json.loads(entities)
            except (json.JSONDecodeError, TypeError):
                entities = None
        
        return cls(
            id=str(data["id"]),
            title=data["title"],
            status=TranscriptStatus(data["status"]),
            created_at=created_at,
            duration=data.get("duration"),
            text=data.get("text"),
            entities=entities,
            confidence=data.get("confidence"),
            language=data.get("language"),
            file_name=data.get("file_name"),
            file_size=data.get("file_size"),
            team_id=data.get("team_id"),
            summary=data.get("summary"),
            sentiment=data.get("sentiment"),
            speakers=data.get("speakers")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "duration": self.duration,
            "text": self.text,
            "entities": self.entities,
            "confidence": self.confidence,
            "language": self.language,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "team_id": self.team_id,
            "summary": self.summary,
            "sentiment": self.sentiment,
            "speakers": self.speakers
        }
    
    @property
    def is_completed(self) -> bool:
        """Check if transcription is completed"""
        return self.status == TranscriptStatus.COMPLETED
    
    @property
    def is_processing(self) -> bool:
        """Check if transcription is still processing"""
        return self.status in [TranscriptStatus.PROCESSING, TranscriptStatus.QUEUED]
    
    @property
    def has_failed(self) -> bool:
        """Check if transcription has failed"""
        return self.status == TranscriptStatus.FAILED


@dataclass
class User:
    """Represents a user"""
    id: int
    email: str
    name: str
    role: UserRole
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from API response"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            email=data["email"],
            name=data["name"],
            role=UserRole(data["role"]),
            created_at=created_at
        )


@dataclass
class TeamMember:
    """Represents a team member"""
    id: int
    user_id: int
    team_id: int
    role: TeamRole
    joined_at: datetime
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create TeamMember from API response"""
        joined_at = data.get("joined_at")
        if isinstance(joined_at, str):
            joined_at = datetime.fromisoformat(joined_at.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            team_id=data["team_id"],
            role=TeamRole(data["role"]),
            joined_at=joined_at,
            user_email=data.get("user_email"),
            user_name=data.get("user_name")
        )


@dataclass
class Team:
    """Represents a team"""
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    member_count: int = 0
    members: List[TeamMember] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        """Create Team from API response"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        # Parse members if present
        members = []
        if "members" in data:
            members = [TeamMember.from_dict(m) for m in data["members"]]
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            owner_id=data["owner_id"],
            created_at=created_at,
            member_count=data.get("member_count", 0),
            members=members
        )


@dataclass
class WebhookEvent:
    """Represents a webhook event"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookEvent':
        """Create WebhookEvent from webhook payload"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return cls(
            event_type=data["event_type"],
            timestamp=timestamp,
            data=data.get("data", {})
        )


@dataclass
class APIKey:
    """Represents an API key"""
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKey':
        """Create APIKey from API response"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        expires_at = data.get("expires_at")
        if expires_at and isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        last_used_at = data.get("last_used_at")
        if last_used_at and isinstance(last_used_at, str):
            last_used_at = datetime.fromisoformat(last_used_at.replace('Z', '+00:00'))
        
        return cls(
            id=data["id"],
            name=data["name"],
            key_prefix=data.get("key_prefix", ""),
            created_at=created_at,
            expires_at=expires_at,
            last_used_at=last_used_at,
            is_active=data.get("is_active", True)
        )


@dataclass
class UsageStats:
    """Represents usage statistics"""
    total_requests: int
    total_transcription_minutes: float
    current_month_requests: int
    current_month_minutes: float
    rate_limit_remaining: int
    quota_remaining: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageStats':
        """Create UsageStats from API response"""
        return cls(
            total_requests=data.get("total_requests", 0),
            total_transcription_minutes=data.get("total_transcription_minutes", 0.0),
            current_month_requests=data.get("current_month_requests", 0),
            current_month_minutes=data.get("current_month_minutes", 0.0),
            rate_limit_remaining=data.get("rate_limit_remaining", 0),
            quota_remaining=data.get("quota_remaining")
        )


@dataclass
class SearchResult:
    """Represents a search result"""
    transcript_id: str
    title: str
    snippet: str
    score: float
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Create SearchResult from API response"""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        
        return cls(
            transcript_id=str(data["transcript_id"]),
            title=data["title"],
            snippet=data["snippet"],
            score=data["score"],
            created_at=created_at
        )


@dataclass
class AnalysisResult:
    """Represents analysis results"""
    transcript_id: str
    entities: Dict[str, List[str]]
    sentiment: Dict[str, Any]
    topics: List[str]
    summary: str
    action_items: List[str]
    confidence: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from API response"""
        return cls(
            transcript_id=str(data["transcript_id"]),
            entities=data.get("entities", {}),
            sentiment=data.get("sentiment", {}),
            topics=data.get("topics", []),
            summary=data.get("summary", ""),
            action_items=data.get("action_items", []),
            confidence=data.get("confidence", 0.0)
        )