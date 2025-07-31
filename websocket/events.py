"""
WebSocket event definitions
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
import json


class EventType(Enum):
    """WebSocket event types"""
    
    # Connection events
    CONNECTION_ESTABLISHED = "connection.established"
    CONNECTION_CLOSED = "connection.closed"
    PING = "ping"
    PONG = "pong"
    
    # Room events
    JOIN_ROOM = "room.join"
    LEAVE_ROOM = "room.leave"
    USER_JOINED_ROOM = "room.user_joined"
    USER_LEFT_ROOM = "room.user_left"
    
    # Transcript events
    TRANSCRIPT_UPDATED = "transcript.updated"
    TRANSCRIPT_DELETED = "transcript.deleted"
    TRANSCRIPT_SHARED = "transcript.shared"
    TRANSCRIPT_VERSION_CREATED = "transcript.version_created"
    
    # Collaboration events
    ANNOTATION_ADDED = "annotation.added"
    ANNOTATION_UPDATED = "annotation.updated"
    ANNOTATION_DELETED = "annotation.deleted"
    COMMENT_ADDED = "comment.added"
    USER_TYPING = "user.typing"
    USER_STOPPED_TYPING = "user.stopped_typing"
    
    # Processing events
    PROCESSING_STARTED = "processing.started"
    PROCESSING_PROGRESS = "processing.progress"
    PROCESSING_COMPLETED = "processing.completed"
    PROCESSING_FAILED = "processing.failed"
    
    # Notification events
    NOTIFICATION_NEW = "notification.new"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_CLEARED = "notification.cleared"
    
    # Team events
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"
    TEAM_UPDATED = "team.updated"
    
    # System events
    SYSTEM_ANNOUNCEMENT = "system.announcement"
    SYSTEM_MAINTENANCE = "system.maintenance"
    ERROR = "error"


class Event(BaseModel):
    """WebSocket event model"""
    
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = None
    id: Optional[str] = None
    user_id: Optional[int] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "id": self.id,
            "user_id": self.user_id
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create from dictionary"""
        data['type'] = EventType(data['type'])
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EventHandler:
    """Base class for event handlers"""
    
    async def handle(self, event: Event, user_id: int, connection_manager):
        """Handle an event"""
        raise NotImplementedError


class TranscriptUpdatedEvent(Event):
    """Transcript updated event"""
    
    def __init__(self, transcript_id: int, user_id: int, changes: Dict[str, Any]):
        super().__init__(
            type=EventType.TRANSCRIPT_UPDATED,
            data={
                "transcript_id": transcript_id,
                "user_id": user_id,
                "changes": changes
            },
            user_id=user_id
        )


class AnnotationAddedEvent(Event):
    """Annotation added event"""
    
    def __init__(
        self,
        transcript_id: int,
        annotation_id: int,
        user_id: int,
        start_pos: int,
        end_pos: int,
        text: str,
        annotation_type: str
    ):
        super().__init__(
            type=EventType.ANNOTATION_ADDED,
            data={
                "transcript_id": transcript_id,
                "annotation_id": annotation_id,
                "user_id": user_id,
                "start_pos": start_pos,
                "end_pos": end_pos,
                "text": text,
                "type": annotation_type
            },
            user_id=user_id
        )


class ProcessingProgressEvent(Event):
    """Processing progress event"""
    
    def __init__(self, job_id: str, progress: int, status: str, message: str = ""):
        super().__init__(
            type=EventType.PROCESSING_PROGRESS,
            data={
                "job_id": job_id,
                "progress": progress,
                "status": status,
                "message": message
            }
        )


class NotificationEvent(Event):
    """New notification event"""
    
    def __init__(
        self,
        notification_id: int,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        action_url: Optional[str] = None
    ):
        super().__init__(
            type=EventType.NOTIFICATION_NEW,
            data={
                "notification_id": notification_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "action_url": action_url
            },
            user_id=user_id
        )