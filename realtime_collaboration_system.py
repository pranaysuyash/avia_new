"""
Real-time Collaboration System
Enables multi-user collaborative editing, presence indicators, and real-time updates
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import yjs
from y_py import YDoc, YText, YMap, YArray
import logging
from collections import defaultdict
import hashlib
import time

logger = logging.getLogger(__name__)

class CollaborationType(Enum):
    """Types of collaboration activities"""
    EDIT = "edit"
    COMMENT = "comment"
    ANNOTATION = "annotation"
    CURSOR = "cursor"
    SELECTION = "selection"
    PRESENCE = "presence"
    TYPING = "typing"

class UserRole(Enum):
    """User roles in collaboration"""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"

@dataclass
class User:
    """Represents a collaborative user"""
    id: str
    name: str
    email: str
    avatar: Optional[str]
    role: UserRole
    color: str
    cursor_position: Optional[Dict[str, int]] = None
    selection: Optional[Dict[str, Any]] = None
    is_typing: bool = False
    last_activity: datetime = None
    
    def __post_init__(self):
        if not self.last_activity:
            self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'avatar': self.avatar,
            'role': self.role.value,
            'color': self.color,
            'cursor_position': self.cursor_position,
            'selection': self.selection,
            'is_typing': self.is_typing,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

@dataclass
class CollaborationEvent:
    """Represents a collaboration event"""
    id: str
    type: CollaborationType
    user_id: str
    session_id: str
    timestamp: datetime
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }

@dataclass
class Comment:
    """Represents a comment in collaborative editing"""
    id: str
    user_id: str
    text: str
    timestamp: datetime
    position: Dict[str, int]
    resolved: bool = False
    replies: List[Dict] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []

class CollaborationSession:
    """Manages a single collaboration session"""
    
    def __init__(self, session_id: str, document_id: str):
        self.session_id = session_id
        self.document_id = document_id
        self.users: Dict[str, User] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.ydoc = YDoc()
        self.ytext = self.ydoc.get_text('content')
        self.ymeta = self.ydoc.get_map('metadata')
        self.ycomments = self.ydoc.get_array('comments')
        self.yannotations = self.ydoc.get_array('annotations')
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_locked = False
        self.lock_holder: Optional[str] = None
        self.version = 0
        self.history: List[CollaborationEvent] = []
        
    def add_user(self, user: User, websocket: WebSocket):
        """Add a user to the session"""
        self.users[user.id] = user
        self.websockets[user.id] = websocket
        self.last_activity = datetime.utcnow()
        
    def remove_user(self, user_id: str):
        """Remove a user from the session"""
        if user_id in self.users:
            del self.users[user_id]
        if user_id in self.websockets:
            del self.websockets[user_id]
        self.last_activity = datetime.utcnow()
        
    def get_active_users(self) -> List[User]:
        """Get list of active users"""
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        return [
            user for user in self.users.values()
            if user.last_activity > cutoff
        ]
        
    def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        if user_id in self.users:
            self.users[user_id].last_activity = datetime.utcnow()
            self.last_activity = datetime.utcnow()
            
    def can_edit(self, user_id: str) -> bool:
        """Check if user can edit the document"""
        if user_id not in self.users:
            return False
        user = self.users[user_id]
        return user.role in [UserRole.OWNER, UserRole.EDITOR]
        
    def acquire_lock(self, user_id: str, duration: int = 30) -> bool:
        """Acquire edit lock for a user"""
        if self.is_locked and self.lock_holder != user_id:
            return False
        self.is_locked = True
        self.lock_holder = user_id
        return True
        
    def release_lock(self, user_id: str) -> bool:
        """Release edit lock"""
        if self.lock_holder == user_id:
            self.is_locked = False
            self.lock_holder = None
            return True
        return False
        
    def add_event(self, event: CollaborationEvent):
        """Add an event to history"""
        self.history.append(event)
        self.version += 1
        self.last_activity = datetime.utcnow()

class RealtimeCollaborationSystem:
    """Main system for managing real-time collaboration"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self.event_handlers: Dict[CollaborationType, List[Callable]] = defaultdict(list)
        self._running = False
        self._cleanup_task = None
        
    async def initialize(self):
        """Initialize the collaboration system"""
        if not self.redis_client:
            self.redis_client = await redis.from_url("redis://localhost:6379")
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        logger.info("Real-time collaboration system initialized")
        
    async def shutdown(self):
        """Shutdown the collaboration system"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Real-time collaboration system shutdown")
        
    async def create_session(self, document_id: str, creator: User) -> str:
        """Create a new collaboration session"""
        session_id = str(uuid.uuid4())
        session = CollaborationSession(session_id, document_id)
        session.add_user(creator, None)
        
        self.sessions[session_id] = session
        self.user_sessions[creator.id].add(session_id)
        
        # Store in Redis for persistence
        if self.redis_client:
            await self.redis_client.hset(
                f"collab:session:{session_id}",
                mapping={
                    'document_id': document_id,
                    'creator_id': creator.id,
                    'created_at': session.created_at.isoformat(),
                    'version': 0
                }
            )
            
        logger.info(f"Created collaboration session {session_id} for document {document_id}")
        return session_id
        
    async def join_session(
        self,
        session_id: str,
        user: User,
        websocket: WebSocket
    ) -> bool:
        """Join an existing collaboration session"""
        if session_id not in self.sessions:
            # Try to load from Redis
            if self.redis_client:
                session_data = await self.redis_client.hgetall(f"collab:session:{session_id}")
                if session_data:
                    document_id = session_data.get(b'document_id', b'').decode()
                    self.sessions[session_id] = CollaborationSession(session_id, document_id)
                else:
                    return False
            else:
                return False
                
        session = self.sessions[session_id]
        session.add_user(user, websocket)
        self.user_sessions[user.id].add(session_id)
        
        # Notify other users
        await self._broadcast_event(
            session_id,
            CollaborationEvent(
                id=str(uuid.uuid4()),
                type=CollaborationType.PRESENCE,
                user_id=user.id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                data={'action': 'join', 'user': user.to_dict()}
            ),
            exclude_user=user.id
        )
        
        # Send current state to joining user
        await self._send_session_state(session_id, user.id)
        
        logger.info(f"User {user.id} joined session {session_id}")
        return True
        
    async def leave_session(self, session_id: str, user_id: str):
        """Leave a collaboration session"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        session.remove_user(user_id)
        self.user_sessions[user_id].discard(session_id)
        
        # Release any locks held by the user
        session.release_lock(user_id)
        
        # Notify other users
        await self._broadcast_event(
            session_id,
            CollaborationEvent(
                id=str(uuid.uuid4()),
                type=CollaborationType.PRESENCE,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                data={'action': 'leave', 'user_id': user_id}
            )
        )
        
        # Clean up empty sessions
        if not session.users:
            await self._save_session_state(session_id)
            del self.sessions[session_id]
            
        logger.info(f"User {user_id} left session {session_id}")
        
    async def handle_websocket(self, websocket: WebSocket, session_id: str, user_id: str):
        """Handle WebSocket connection for a user"""
        try:
            while True:
                data = await websocket.receive_json()
                await self._process_message(session_id, user_id, data)
        except WebSocketDisconnect:
            await self.leave_session(session_id, user_id)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            await self.leave_session(session_id, user_id)
            
    async def _process_message(self, session_id: str, user_id: str, data: Dict):
        """Process incoming WebSocket message"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        session.update_user_activity(user_id)
        
        message_type = data.get('type')
        
        if message_type == 'edit':
            await self._handle_edit(session_id, user_id, data)
        elif message_type == 'cursor':
            await self._handle_cursor(session_id, user_id, data)
        elif message_type == 'selection':
            await self._handle_selection(session_id, user_id, data)
        elif message_type == 'comment':
            await self._handle_comment(session_id, user_id, data)
        elif message_type == 'annotation':
            await self._handle_annotation(session_id, user_id, data)
        elif message_type == 'typing':
            await self._handle_typing(session_id, user_id, data)
        elif message_type == 'sync':
            await self._handle_sync(session_id, user_id, data)
        elif message_type == 'lock':
            await self._handle_lock(session_id, user_id, data)
            
    async def _handle_edit(self, session_id: str, user_id: str, data: Dict):
        """Handle document edit"""
        session = self.sessions[session_id]
        
        if not session.can_edit(user_id):
            await self._send_error(session_id, user_id, "Permission denied")
            return
            
        # Apply edit to CRDT
        operation = data.get('operation')
        if operation:
            # Apply to Yjs document
            if operation['type'] == 'insert':
                session.ytext.insert(operation['index'], operation['text'])
            elif operation['type'] == 'delete':
                session.ytext.delete(operation['index'], operation['length'])
                
        # Create event
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            type=CollaborationType.EDIT,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            data={'operation': operation}
        )
        
        session.add_event(event)
        
        # Broadcast to other users
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
        # Trigger event handlers
        await self._trigger_handlers(CollaborationType.EDIT, event)
        
    async def _handle_cursor(self, session_id: str, user_id: str, data: Dict):
        """Handle cursor position update"""
        session = self.sessions[session_id]
        
        if user_id in session.users:
            session.users[user_id].cursor_position = data.get('position')
            
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            type=CollaborationType.CURSOR,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            data={'position': data.get('position')}
        )
        
        # Broadcast to other users
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
    async def _handle_selection(self, session_id: str, user_id: str, data: Dict):
        """Handle text selection update"""
        session = self.sessions[session_id]
        
        if user_id in session.users:
            session.users[user_id].selection = data.get('selection')
            
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            type=CollaborationType.SELECTION,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            data={'selection': data.get('selection')}
        )
        
        # Broadcast to other users
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
    async def _handle_comment(self, session_id: str, user_id: str, data: Dict):
        """Handle comment creation/update"""
        session = self.sessions[session_id]
        
        action = data.get('action')
        if action == 'create':
            comment = Comment(
                id=str(uuid.uuid4()),
                user_id=user_id,
                text=data.get('text', ''),
                timestamp=datetime.utcnow(),
                position=data.get('position', {})
            )
            
            # Add to CRDT
            session.ycomments.append(asdict(comment))
            
            event = CollaborationEvent(
                id=str(uuid.uuid4()),
                type=CollaborationType.COMMENT,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                data={'action': 'create', 'comment': asdict(comment)}
            )
            
        elif action == 'resolve':
            comment_id = data.get('comment_id')
            # Update comment in CRDT
            event = CollaborationEvent(
                id=str(uuid.uuid4()),
                type=CollaborationType.COMMENT,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                data={'action': 'resolve', 'comment_id': comment_id}
            )
            
        elif action == 'reply':
            comment_id = data.get('comment_id')
            reply_text = data.get('text', '')
            # Add reply to comment in CRDT
            event = CollaborationEvent(
                id=str(uuid.uuid4()),
                type=CollaborationType.COMMENT,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                data={
                    'action': 'reply',
                    'comment_id': comment_id,
                    'reply': {
                        'id': str(uuid.uuid4()),
                        'user_id': user_id,
                        'text': reply_text,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
            )
            
        session.add_event(event)
        await self._broadcast_event(session_id, event)
        await self._trigger_handlers(CollaborationType.COMMENT, event)
        
    async def _handle_annotation(self, session_id: str, user_id: str, data: Dict):
        """Handle annotation creation/update"""
        session = self.sessions[session_id]
        
        annotation = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': data.get('annotation_type', 'highlight'),
            'start': data.get('start'),
            'end': data.get('end'),
            'color': data.get('color', '#ffeb3b'),
            'note': data.get('note', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add to CRDT
        session.yannotations.append(annotation)
        
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            type=CollaborationType.ANNOTATION,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            data={'annotation': annotation}
        )
        
        session.add_event(event)
        await self._broadcast_event(session_id, event)
        await self._trigger_handlers(CollaborationType.ANNOTATION, event)
        
    async def _handle_typing(self, session_id: str, user_id: str, data: Dict):
        """Handle typing indicator"""
        session = self.sessions[session_id]
        
        if user_id in session.users:
            session.users[user_id].is_typing = data.get('is_typing', False)
            
        event = CollaborationEvent(
            id=str(uuid.uuid4()),
            type=CollaborationType.TYPING,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            data={'is_typing': data.get('is_typing', False)}
        )
        
        # Broadcast to other users
        await self._broadcast_event(session_id, event, exclude_user=user_id)
        
    async def _handle_sync(self, session_id: str, user_id: str, data: Dict):
        """Handle document sync request"""
        await self._send_session_state(session_id, user_id)
        
    async def _handle_lock(self, session_id: str, user_id: str, data: Dict):
        """Handle lock request"""
        session = self.sessions[session_id]
        
        action = data.get('action')
        if action == 'acquire':
            success = session.acquire_lock(user_id)
            await self._send_to_user(
                session_id,
                user_id,
                {
                    'type': 'lock_response',
                    'success': success,
                    'lock_holder': session.lock_holder
                }
            )
            
            if success:
                # Notify others
                event = CollaborationEvent(
                    id=str(uuid.uuid4()),
                    type=CollaborationType.EDIT,
                    user_id=user_id,
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    data={'lock_acquired': True}
                )
                await self._broadcast_event(session_id, event, exclude_user=user_id)
                
        elif action == 'release':
            success = session.release_lock(user_id)
            if success:
                # Notify others
                event = CollaborationEvent(
                    id=str(uuid.uuid4()),
                    type=CollaborationType.EDIT,
                    user_id=user_id,
                    session_id=session_id,
                    timestamp=datetime.utcnow(),
                    data={'lock_released': True}
                )
                await self._broadcast_event(session_id, event)
                
    async def _broadcast_event(
        self,
        session_id: str,
        event: CollaborationEvent,
        exclude_user: Optional[str] = None
    ):
        """Broadcast event to all users in session"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        message = json.dumps(event.to_dict())
        
        for user_id, websocket in session.websockets.items():
            if user_id != exclude_user and websocket:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send to user {user_id}: {e}")
                    
    async def _send_to_user(self, session_id: str, user_id: str, data: Dict):
        """Send message to specific user"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        if user_id in session.websockets and session.websockets[user_id]:
            try:
                await session.websockets[user_id].send_json(data)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                
    async def _send_error(self, session_id: str, user_id: str, error: str):
        """Send error message to user"""
        await self._send_to_user(
            session_id,
            user_id,
            {'type': 'error', 'message': error}
        )
        
    async def _send_session_state(self, session_id: str, user_id: str):
        """Send current session state to user"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        
        # Get document state from CRDT
        doc_state = {
            'content': str(session.ytext),
            'metadata': dict(session.ymeta),
            'comments': list(session.ycomments),
            'annotations': list(session.yannotations),
            'version': session.version,
            'users': [u.to_dict() for u in session.get_active_users()],
            'is_locked': session.is_locked,
            'lock_holder': session.lock_holder
        }
        
        await self._send_to_user(
            session_id,
            user_id,
            {'type': 'sync', 'state': doc_state}
        )
        
    async def _save_session_state(self, session_id: str):
        """Save session state to Redis"""
        if not self.redis_client or session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        
        # Save document state
        state = {
            'content': str(session.ytext),
            'metadata': json.dumps(dict(session.ymeta)),
            'comments': json.dumps(list(session.ycomments)),
            'annotations': json.dumps(list(session.yannotations)),
            'version': session.version,
            'last_activity': session.last_activity.isoformat()
        }
        
        await self.redis_client.hset(
            f"collab:state:{session_id}",
            mapping=state
        )
        
        # Save history (last 100 events)
        history = [e.to_dict() for e in session.history[-100:]]
        await self.redis_client.set(
            f"collab:history:{session_id}",
            json.dumps(history)
        )
        
        # Set expiry (7 days)
        await self.redis_client.expire(f"collab:state:{session_id}", 604800)
        await self.redis_client.expire(f"collab:history:{session_id}", 604800)
        
    async def _cleanup_inactive_sessions(self):
        """Periodically clean up inactive sessions"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                cutoff = datetime.utcnow() - timedelta(hours=1)
                sessions_to_remove = []
                
                for session_id, session in self.sessions.items():
                    if not session.users and session.last_activity < cutoff:
                        sessions_to_remove.append(session_id)
                        
                for session_id in sessions_to_remove:
                    await self._save_session_state(session_id)
                    del self.sessions[session_id]
                    logger.info(f"Cleaned up inactive session {session_id}")
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                
    def register_handler(self, event_type: CollaborationType, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
        
    async def _trigger_handlers(self, event_type: CollaborationType, event: CollaborationEvent):
        """Trigger registered event handlers"""
        for handler in self.event_handlers[event_type]:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    async def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a session"""
        if session_id not in self.sessions:
            return {}
            
        session = self.sessions[session_id]
        
        # Calculate analytics
        edit_count = sum(1 for e in session.history if e.type == CollaborationType.EDIT)
        comment_count = sum(1 for e in session.history if e.type == CollaborationType.COMMENT)
        annotation_count = sum(1 for e in session.history if e.type == CollaborationType.ANNOTATION)
        
        user_activity = defaultdict(int)
        for event in session.history:
            user_activity[event.user_id] += 1
            
        return {
            'session_id': session_id,
            'document_id': session.document_id,
            'created_at': session.created_at.isoformat(),
            'last_activity': session.last_activity.isoformat(),
            'version': session.version,
            'active_users': len(session.get_active_users()),
            'total_users': len(session.users),
            'edit_count': edit_count,
            'comment_count': comment_count,
            'annotation_count': annotation_count,
            'user_activity': dict(user_activity),
            'duration': (session.last_activity - session.created_at).total_seconds()
        }
        
    async def export_session_history(self, session_id: str) -> List[Dict]:
        """Export session history"""
        if session_id not in self.sessions:
            # Try to load from Redis
            if self.redis_client:
                history_data = await self.redis_client.get(f"collab:history:{session_id}")
                if history_data:
                    return json.loads(history_data)
            return []
            
        session = self.sessions[session_id]
        return [e.to_dict() for e in session.history]

# Conflict resolution strategies
class ConflictResolution:
    """Handles conflict resolution in collaborative editing"""
    
    @staticmethod
    def operational_transform(op1: Dict, op2: Dict) -> Dict:
        """Apply operational transformation to resolve conflicts"""
        # Simple OT implementation for text operations
        if op1['type'] == 'insert' and op2['type'] == 'insert':
            if op1['index'] < op2['index']:
                return op2
            elif op1['index'] > op2['index']:
                op2['index'] += len(op1['text'])
                return op2
            else:
                # Same position - use timestamp or user ID for ordering
                if op1['timestamp'] < op2['timestamp']:
                    op2['index'] += len(op1['text'])
                return op2
                
        elif op1['type'] == 'delete' and op2['type'] == 'insert':
            if op1['index'] < op2['index']:
                op2['index'] -= op1['length']
            return op2
            
        elif op1['type'] == 'insert' and op2['type'] == 'delete':
            if op1['index'] <= op2['index']:
                op2['index'] += len(op1['text'])
            return op2
            
        elif op1['type'] == 'delete' and op2['type'] == 'delete':
            if op1['index'] < op2['index']:
                op2['index'] -= op1['length']
            elif op1['index'] > op2['index']:
                pass
            else:
                # Overlapping deletes
                if op1['index'] + op1['length'] > op2['index']:
                    op2['length'] -= (op1['index'] + op1['length'] - op2['index'])
                    op2['index'] = op1['index']
            return op2
            
        return op2
        
    @staticmethod
    def three_way_merge(base: str, version1: str, version2: str) -> str:
        """Perform three-way merge for conflict resolution"""
        # Simple implementation - in production, use diff3 or similar
        if version1 == version2:
            return version1
        elif version1 == base:
            return version2
        elif version2 == base:
            return version1
        else:
            # Both changed - need more sophisticated merge
            # For now, concatenate with conflict markers
            return f"<<<<<<< Version 1\n{version1}\n=======\n{version2}\n>>>>>>> Version 2"

# Usage example
async def demo_collaboration():
    """Demonstrate collaboration system"""
    system = RealtimeCollaborationSystem()
    await system.initialize()
    
    # Create users
    user1 = User(
        id="user1",
        name="Alice",
        email="alice@example.com",
        avatar=None,
        role=UserRole.EDITOR,
        color="#ff0000"
    )
    
    user2 = User(
        id="user2",
        name="Bob",
        email="bob@example.com",
        avatar=None,
        role=UserRole.EDITOR,
        color="#00ff00"
    )
    
    # Create session
    session_id = await system.create_session("doc123", user1)
    
    # Simulate joining
    await system.join_session(session_id, user2, None)
    
    # Get analytics
    analytics = await system.get_session_analytics(session_id)
    print(f"Session analytics: {analytics}")
    
    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_collaboration())