"""
Real-time Collaboration Manager
Implements WebSocket-based real-time features for collaborative transcription
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_manager import SessionManager
from security_manager import SecurityManager

# Configure logging
logger = logging.getLogger(__name__)


class CollaborationEventType(Enum):
    """Types of collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    TRANSCRIPT_UPDATE = "transcript_update"
    CURSOR_POSITION = "cursor_position"
    SELECTION_CHANGE = "selection_change"
    COMMENT_ADDED = "comment_added"
    COMMENT_RESOLVED = "comment_resolved"
    LIVE_TRANSCRIPTION = "live_transcription"
    STATUS_UPDATE = "status_update"
    NOTIFICATION = "notification"
    TYPING_INDICATOR = "typing_indicator"
    SAVE_POINT = "save_point"
    VERSION_CREATED = "version_created"


@dataclass
class CollaborationUser:
    """Represents a user in a collaboration session"""
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    color: str = "#007bff"
    cursor_position: Optional[int] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    is_typing: bool = False
    last_activity: datetime = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()
        if self.permissions is None:
            self.permissions = ["read"]


@dataclass
class CollaborationEvent:
    """Represents a collaboration event"""
    event_id: str
    event_type: CollaborationEventType
    session_id: str
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }


@dataclass
class CollaborationSession:
    """Represents a collaborative session"""
    session_id: str
    transcript_id: str
    created_by: str
    created_at: datetime
    users: Dict[str, CollaborationUser]
    is_active: bool = True
    allow_anonymous: bool = False
    max_users: int = 10
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {
                "auto_save": True,
                "save_interval": 30,  # seconds
                "show_cursors": True,
                "show_typing_indicators": True,
                "enable_comments": True,
                "enable_version_control": True
            }


class RealtimeCollaborationManager:
    """Manages real-time collaboration features"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.event_handlers: Dict[CollaborationEventType, List[Callable]] = {}
        self.session_manager = SessionManager()
        self.security_manager = SecurityManager()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        logger.info("Realtime collaboration manager initialized")
    
    async def create_session(
        self,
        transcript_id: str,
        user_id: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> CollaborationSession:
        """Create a new collaboration session"""
        # Check permissions
        if not self.security_manager.access_control.check_permission(user_id, "write"):
            raise PermissionError("User does not have write permission")
        
        session_id = f"collab_{transcript_id}_{uuid.uuid4().hex[:8]}"
        
        # Get user info
        user_info = self._get_user_info(user_id)
        user = CollaborationUser(
            user_id=user_id,
            display_name=user_info.get("display_name", user_id),
            avatar_url=user_info.get("avatar_url"),
            color=self._generate_user_color(user_id),
            permissions=["read", "write", "admin"]
        )
        
        session = CollaborationSession(
            session_id=session_id,
            transcript_id=transcript_id,
            created_by=user_id,
            created_at=datetime.now(),
            users={user_id: user},
            settings=settings
        )
        
        self.sessions[session_id] = session
        
        # Track user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(session_id)
        
        # Emit session created event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.STATUS_UPDATE,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data={
                "status": "session_created",
                "transcript_id": transcript_id,
                "settings": session.settings
            }
        ))
        
        logger.info(f"Created collaboration session {session_id} for transcript {transcript_id}")
        return session
    
    async def join_session(
        self,
        session_id: str,
        user_id: str,
        display_name: Optional[str] = None
    ) -> CollaborationUser:
        """Join an existing collaboration session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        
        # Check if session is full
        if len(session.users) >= session.max_users:
            raise ValueError("Session is full")
        
        # Check permissions
        if not session.allow_anonymous and not self.security_manager.access_control.check_permission(user_id, "read"):
            raise PermissionError("User does not have read permission")
        
        # Create user if not exists
        if user_id not in session.users:
            user_info = self._get_user_info(user_id)
            user = CollaborationUser(
                user_id=user_id,
                display_name=display_name or user_info.get("display_name", user_id),
                avatar_url=user_info.get("avatar_url"),
                color=self._generate_user_color(user_id),
                permissions=["read", "write"] if self.security_manager.access_control.check_permission(user_id, "write") else ["read"]
            )
            session.users[user_id] = user
            
            # Track user sessions
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = set()
            self.user_sessions[user_id].add(session_id)
            
            # Emit user joined event
            await self._emit_event(CollaborationEvent(
                event_id=self._generate_event_id(),
                event_type=CollaborationEventType.USER_JOINED,
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    "display_name": user.display_name,
                    "color": user.color,
                    "permissions": user.permissions
                }
            ))
            
            logger.info(f"User {user_id} joined session {session_id}")
        
        return session.users[user_id]
    
    async def leave_session(self, session_id: str, user_id: str):
        """Leave a collaboration session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        if user_id in session.users:
            del session.users[user_id]
            
            # Update user sessions
            if user_id in self.user_sessions:
                self.user_sessions[user_id].discard(session_id)
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            # Emit user left event
            await self._emit_event(CollaborationEvent(
                event_id=self._generate_event_id(),
                event_type=CollaborationEventType.USER_LEFT,
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={"display_name": user_id}
            ))
            
            # Clean up empty sessions
            if not session.users and session.is_active:
                await self.close_session(session_id)
            
            logger.info(f"User {user_id} left session {session_id}")
    
    async def update_cursor_position(
        self,
        session_id: str,
        user_id: str,
        position: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None
    ):
        """Update user's cursor position"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        if user_id not in session.users:
            return
        
        user = session.users[user_id]
        user.cursor_position = position
        user.selection_start = selection_start
        user.selection_end = selection_end
        user.last_activity = datetime.now()
        
        # Emit cursor position event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.CURSOR_POSITION,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data={
                "position": position,
                "selection_start": selection_start,
                "selection_end": selection_end
            }
        ))
    
    async def update_transcript(
        self,
        session_id: str,
        user_id: str,
        operation: str,
        position: int,
        content: str,
        length: Optional[int] = None
    ):
        """Update transcript content collaboratively"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        if user_id not in session.users:
            raise ValueError(f"User {user_id} not in session")
        
        # Check write permission
        if "write" not in session.users[user_id].permissions:
            raise PermissionError("User does not have write permission")
        
        # Create transcript update event
        update_data = {
            "operation": operation,  # insert, delete, replace
            "position": position,
            "content": content,
            "length": length,
            "user_color": session.users[user_id].color
        }
        
        # Apply operation to stored transcript
        await self._apply_transcript_operation(session.transcript_id, update_data)
        
        # Emit transcript update event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.TRANSCRIPT_UPDATE,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data=update_data
        ))
        
        # Update user activity
        session.users[user_id].last_activity = datetime.now()
    
    async def add_comment(
        self,
        session_id: str,
        user_id: str,
        position: int,
        comment_text: str,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None
    ) -> str:
        """Add a comment to the transcript"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        if not session.settings.get("enable_comments", True):
            raise ValueError("Comments are disabled for this session")
        
        comment_id = f"comment_{uuid.uuid4().hex[:8]}"
        
        comment_data = {
            "comment_id": comment_id,
            "text": comment_text,
            "position": position,
            "selection_start": selection_start,
            "selection_end": selection_end,
            "author": session.users[user_id].display_name,
            "author_color": session.users[user_id].color,
            "created_at": datetime.now().isoformat(),
            "resolved": False
        }
        
        # Store comment
        await self._store_comment(session.transcript_id, comment_data)
        
        # Emit comment added event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.COMMENT_ADDED,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data=comment_data
        ))
        
        return comment_id
    
    async def resolve_comment(self, session_id: str, user_id: str, comment_id: str):
        """Resolve a comment"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Update comment status
        await self._update_comment_status(self.sessions[session_id].transcript_id, comment_id, True)
        
        # Emit comment resolved event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.COMMENT_RESOLVED,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data={
                "comment_id": comment_id,
                "resolved_by": self.sessions[session_id].users[user_id].display_name
            }
        ))
    
    async def stream_live_transcription(
        self,
        session_id: str,
        user_id: str,
        audio_chunk: bytes,
        is_final: bool = False
    ) -> Optional[str]:
        """Stream live transcription updates"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Process audio chunk (placeholder - integrate with actual transcription)
        transcribed_text = await self._process_audio_chunk(audio_chunk)
        
        if transcribed_text:
            # Emit live transcription event
            await self._emit_event(CollaborationEvent(
                event_id=self._generate_event_id(),
                event_type=CollaborationEventType.LIVE_TRANSCRIPTION,
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    "text": transcribed_text,
                    "is_final": is_final,
                    "speaker": self.sessions[session_id].users[user_id].display_name
                }
            ))
        
        return transcribed_text
    
    async def set_typing_indicator(self, session_id: str, user_id: str, is_typing: bool):
        """Update typing indicator status"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        if user_id in session.users:
            session.users[user_id].is_typing = is_typing
            
            # Emit typing indicator event
            await self._emit_event(CollaborationEvent(
                event_id=self._generate_event_id(),
                event_type=CollaborationEventType.TYPING_INDICATOR,
                session_id=session_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    "is_typing": is_typing,
                    "display_name": session.users[user_id].display_name
                }
            ))
    
    async def create_version(
        self,
        session_id: str,
        user_id: str,
        version_name: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Create a version/snapshot of the current transcript"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        if not session.settings.get("enable_version_control", True):
            raise ValueError("Version control is disabled for this session")
        
        version_id = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        
        # Create version snapshot
        version_data = await self._create_transcript_version(
            session.transcript_id,
            version_id,
            version_name or f"Version {version_id}",
            description,
            user_id
        )
        
        # Emit version created event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.VERSION_CREATED,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data={
                "version_id": version_id,
                "version_name": version_name,
                "created_by": session.users[user_id].display_name
            }
        ))
        
        return version_id
    
    async def send_notification(
        self,
        session_id: str,
        user_id: str,
        message: str,
        notification_type: str = "info",
        target_users: Optional[List[str]] = None
    ):
        """Send notification to session users"""
        if session_id not in self.sessions:
            return
        
        # Emit notification event
        await self._emit_event(CollaborationEvent(
            event_id=self._generate_event_id(),
            event_type=CollaborationEventType.NOTIFICATION,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now(),
            data={
                "message": message,
                "type": notification_type,  # info, warning, error, success
                "target_users": target_users,
                "from_user": self.sessions[session_id].users.get(user_id, {}).get("display_name", user_id)
            }
        ))
    
    async def close_session(self, session_id: str):
        """Close a collaboration session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        session.is_active = False
        
        # Notify all users
        for user_id in list(session.users.keys()):
            await self.leave_session(session_id, user_id)
        
        # Clean up
        del self.sessions[session_id]
        logger.info(f"Closed collaboration session {session_id}")
    
    def register_event_handler(
        self,
        event_type: CollaborationEventType,
        handler: Callable[[CollaborationEvent], None]
    ):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "transcript_id": session.transcript_id,
            "created_by": session.created_by,
            "created_at": session.created_at.isoformat(),
            "user_count": len(session.users),
            "users": [
                {
                    "user_id": user.user_id,
                    "display_name": user.display_name,
                    "color": user.color,
                    "is_typing": user.is_typing,
                    "permissions": user.permissions
                }
                for user in session.users.values()
            ],
            "settings": session.settings,
            "is_active": session.is_active
        }
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all sessions for a user"""
        return list(self.user_sessions.get(user_id, set()))
    
    async def start_event_processor(self):
        """Start the event processing loop"""
        self._running = True
        logger.info("Starting collaboration event processor")
        
        while self._running:
            try:
                # Process events from queue
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                # Check for inactive sessions
                await self._cleanup_inactive_sessions()
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def stop_event_processor(self):
        """Stop the event processing loop"""
        self._running = False
        logger.info("Stopping collaboration event processor")
    
    # Private helper methods
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{uuid.uuid4().hex}"
    
    def _generate_user_color(self, user_id: str) -> str:
        """Generate consistent color for user"""
        colors = [
            "#007bff", "#28a745", "#dc3545", "#ffc107",
            "#17a2b8", "#6610f2", "#e83e8c", "#fd7e14"
        ]
        return colors[hash(user_id) % len(colors)]
    
    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information"""
        # This would integrate with user management system
        return {
            "display_name": user_id,
            "avatar_url": None
        }
    
    async def _emit_event(self, event: CollaborationEvent):
        """Emit an event to all handlers"""
        await self._event_queue.put(event)
    
    async def _process_event(self, event: CollaborationEvent):
        """Process a collaboration event"""
        # Call registered handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
        
        # Store event for history
        await self._store_event(event)
    
    async def _store_event(self, event: CollaborationEvent):
        """Store event in history"""
        # This would integrate with event storage system
        pass
    
    async def _apply_transcript_operation(
        self,
        transcript_id: str,
        operation: Dict[str, Any]
    ):
        """Apply an operation to the transcript"""
        # This would integrate with transcript storage
        pass
    
    async def _store_comment(self, transcript_id: str, comment: Dict[str, Any]):
        """Store a comment"""
        # This would integrate with comment storage
        pass
    
    async def _update_comment_status(
        self,
        transcript_id: str,
        comment_id: str,
        resolved: bool
    ):
        """Update comment status"""
        # This would integrate with comment storage
        pass
    
    async def _process_audio_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """Process audio chunk for live transcription"""
        # This would integrate with live transcription service
        return None
    
    async def _create_transcript_version(
        self,
        transcript_id: str,
        version_id: str,
        version_name: str,
        description: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:
        """Create a version snapshot"""
        # This would integrate with version control system
        return {
            "version_id": version_id,
            "version_name": version_name,
            "description": description,
            "created_by": user_id,
            "created_at": datetime.now().isoformat()
        }
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions"""
        now = datetime.now()
        inactive_timeout = 3600  # 1 hour
        
        for session_id, session in list(self.sessions.items()):
            if not session.is_active:
                continue
            
            # Check if all users are inactive
            all_inactive = all(
                (now - user.last_activity).total_seconds() > inactive_timeout
                for user in session.users.values()
            )
            
            if all_inactive:
                logger.info(f"Closing inactive session {session_id}")
                await self.close_session(session_id)


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize collaboration manager
        collab_manager = RealtimeCollaborationManager()
        
        # Create a session
        session = await collab_manager.create_session(
            transcript_id="test_transcript_123",
            user_id="user1"
        )
        
        print(f"Created session: {session.session_id}")
        
        # Join session
        user2 = await collab_manager.join_session(
            session.session_id,
            "user2",
            "User Two"
        )
        
        print(f"User joined: {user2.display_name}")
        
        # Update cursor position
        await collab_manager.update_cursor_position(
            session.session_id,
            "user2",
            position=100,
            selection_start=100,
            selection_end=150
        )
        
        # Add comment
        comment_id = await collab_manager.add_comment(
            session.session_id,
            "user2",
            position=100,
            comment_text="This needs clarification",
            selection_start=100,
            selection_end=150
        )
        
        print(f"Added comment: {comment_id}")
        
        # Get session info
        info = collab_manager.get_session_info(session.session_id)
        print(f"Session info: {json.dumps(info, indent=2)}")
        
        # Close session
        await collab_manager.close_session(session.session_id)
    
    # Run example
    asyncio.run(main())