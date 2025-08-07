"""
Operational Transforms Service
Implements operational transforms for real-time collaborative editing with conflict resolution
and document synchronization.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import copy

from api.cache.redis_cache import redis_cache
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations in operational transforms"""
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"
    FORMAT = "format"
    ANNOTATION = "annotation"


class TransformResult(Enum):
    """Result of operation transformation"""
    APPLY = "apply"
    DISCARD = "discard"
    CONFLICT = "conflict"


@dataclass
class Operation:
    """Single operation in operational transforms"""
    type: OperationType
    position: int
    length: int = 0
    content: str = ""
    attributes: Dict[str, Any] = None
    timestamp: datetime = None
    user_id: int = None
    operation_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.operation_id is None:
            self.operation_id = str(uuid.uuid4())
        if self.attributes is None:
            self.attributes = {}


@dataclass
class DocumentState:
    """Document state with version control"""
    document_id: str
    content: str
    version: int
    last_modified: datetime
    operations_log: List[Operation]
    active_users: Dict[int, Dict[str, Any]]
    cursors: Dict[int, int]
    annotations: List[Dict[str, Any]]
    
    def __post_init__(self):
        if not hasattr(self, 'operations_log') or self.operations_log is None:
            self.operations_log = []
        if not hasattr(self, 'active_users') or self.active_users is None:
            self.active_users = {}
        if not hasattr(self, 'cursors') or self.cursors is None:
            self.cursors = {}
        if not hasattr(self, 'annotations') or self.annotations is None:
            self.annotations = []


@dataclass
class CollaborationSession:
    """Collaboration session for a document"""
    session_id: str
    document_id: str
    participants: Dict[int, Dict[str, Any]]
    created_at: datetime
    last_activity: datetime
    settings: Dict[str, Any]
    
    def __post_init__(self):
        if not hasattr(self, 'participants') or self.participants is None:
            self.participants = {}
        if not hasattr(self, 'settings') or self.settings is None:
            self.settings = {}


@dataclass
class TransformContext:
    """Context for operation transformation"""
    local_version: int
    remote_version: int
    local_operations: List[Operation]
    remote_operations: List[Operation]
    document_state: DocumentState


class OperationalTransformsService:
    """Service for operational transforms and real-time collaboration"""
    
    def __init__(self):
        self.document_states: Dict[str, DocumentState] = {}
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        self.operation_queue: Dict[str, List[Operation]] = {}
        self.conflict_resolution_strategies = {
            'last_writer_wins': self._last_writer_wins,
            'merge_changes': self._merge_changes,
            'user_priority': self._user_priority_resolution
        }
        
        # Performance settings
        self.max_operations_log = 1000
        self.session_timeout_minutes = 30
        self.operation_batch_size = 10
        
        # Start background tasks
        asyncio.create_task(self._cleanup_expired_sessions())
    
    async def create_collaboration_session(
        self, 
        document_id: str, 
        user_id: int,
        user_info: Dict[str, Any],
        initial_content: str = ""
    ) -> CollaborationSession:
        """
        Create a new collaboration session for a document
        
        Args:
            document_id: Document identifier
            user_id: User creating the session
            user_info: User information (name, avatar, etc.)
            initial_content: Initial document content
            
        Returns:
            CollaborationSession object
        """
        
        session_id = f"session_{document_id}_{uuid.uuid4().hex[:8]}"
        
        # Create or get existing document state
        if document_id not in self.document_states:
            self.document_states[document_id] = DocumentState(
                document_id=document_id,
                content=initial_content,
                version=0,
                last_modified=datetime.utcnow(),
                operations_log=[],
                active_users={},
                cursors={},
                annotations=[]
            )
        
        # Create collaboration session
        session = CollaborationSession(
            session_id=session_id,
            document_id=document_id,
            participants={user_id: user_info},
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            settings={
                'conflict_resolution': 'merge_changes',
                'auto_save_interval': 30,
                'max_participants': 10,
                'allow_anonymous': False
            }
        )
        
        self.collaboration_sessions[session_id] = session
        
        # Add user to document state
        doc_state = self.document_states[document_id]
        doc_state.active_users[user_id] = {
            **user_info,
            'joined_at': datetime.utcnow(),
            'last_seen': datetime.utcnow(),
            'session_id': session_id
        }
        doc_state.cursors[user_id] = 0
        
        # Cache session in Redis
        await self._cache_session(session)
        await self._cache_document_state(doc_state)
        
        # Log session creation
        audit_service.log_event(
            event_type=AuditEventType.COLLABORATION_SESSION_CREATED,
            action=f"Collaboration session created for document {document_id}",
            user_id=user_id,
            details={
                "session_id": session_id,
                "document_id": document_id
            }
        )
        
        return session
    
    async def join_session(
        self, 
        session_id: str, 
        user_id: int,
        user_info: Dict[str, Any]
    ) -> Tuple[CollaborationSession, DocumentState]:
        """
        Join an existing collaboration session
        
        Args:
            session_id: Session to join
            user_id: User joining
            user_info: User information
            
        Returns:
            Tuple of (session, document_state)
        """
        
        # Get session
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Check participant limits
        max_participants = session.settings.get('max_participants', 10)
        if len(session.participants) >= max_participants:
            raise ValueError("Session is full")
        
        # Add participant
        session.participants[user_id] = user_info
        session.last_activity = datetime.utcnow()
        
        # Update document state
        doc_state = await self._get_document_state(session.document_id)
        if doc_state:
            doc_state.active_users[user_id] = {
                **user_info,
                'joined_at': datetime.utcnow(),
                'last_seen': datetime.utcnow(),
                'session_id': session_id
            }
            doc_state.cursors[user_id] = len(doc_state.content)
        
        # Update cache
        await self._cache_session(session)
        if doc_state:
            await self._cache_document_state(doc_state)
        
        # Log join
        audit_service.log_event(
            event_type=AuditEventType.COLLABORATION_SESSION_JOINED,
            action=f"User joined collaboration session",
            user_id=user_id,
            details={
                "session_id": session_id,
                "document_id": session.document_id
            }
        )
        
        return session, doc_state
    
    async def leave_session(self, session_id: str, user_id: int):
        """
        Leave a collaboration session
        
        Args:
            session_id: Session to leave
            user_id: User leaving
        """
        
        session = await self._get_session(session_id)
        if not session:
            return
        
        # Remove participant
        if user_id in session.participants:
            del session.participants[user_id]
        
        # Update document state
        doc_state = await self._get_document_state(session.document_id)
        if doc_state:
            if user_id in doc_state.active_users:
                del doc_state.active_users[user_id]
            if user_id in doc_state.cursors:
                del doc_state.cursors[user_id]
        
        # Clean up empty session
        if len(session.participants) == 0:
            await self._cleanup_session(session_id)
        else:
            session.last_activity = datetime.utcnow()
            await self._cache_session(session)
        
        if doc_state:
            await self._cache_document_state(doc_state)
        
        # Log leave
        audit_service.log_event(
            event_type=AuditEventType.COLLABORATION_SESSION_LEFT,
            action=f"User left collaboration session",
            user_id=user_id,
            details={
                "session_id": session_id,
                "document_id": session.document_id if session else None
            }
        )
    
    async def apply_operation(
        self, 
        document_id: str, 
        operation: Operation,
        user_id: int
    ) -> Tuple[DocumentState, List[Operation]]:
        """
        Apply an operation to a document with operational transforms
        
        Args:
            document_id: Document to modify
            operation: Operation to apply
            user_id: User performing the operation
            
        Returns:
            Tuple of (updated_document_state, transformed_operations)
        """
        
        doc_state = await self._get_document_state(document_id)
        if not doc_state:
            raise ValueError("Document not found")
        
        # Set operation metadata
        operation.user_id = user_id
        operation.timestamp = datetime.utcnow()
        
        # Get concurrent operations since the operation was created
        concurrent_ops = self._get_concurrent_operations(doc_state, operation)
        
        # Transform the operation against concurrent operations
        transformed_ops = [operation]
        if concurrent_ops:
            transformed_ops = await self._transform_operations(
                [operation], 
                concurrent_ops,
                doc_state
            )
        
        # Apply transformed operations
        for op in transformed_ops:
            doc_state = self._apply_single_operation(doc_state, op)
        
        # Update document version and metadata
        doc_state.version += 1
        doc_state.last_modified = datetime.utcnow()
        doc_state.operations_log.extend(transformed_ops)
        
        # Trim operations log if too long
        if len(doc_state.operations_log) > self.max_operations_log:
            doc_state.operations_log = doc_state.operations_log[-self.max_operations_log:]
        
        # Update user activity
        if user_id in doc_state.active_users:
            doc_state.active_users[user_id]['last_seen'] = datetime.utcnow()
        
        # Cache updated state
        await self._cache_document_state(doc_state)
        
        # Log operation
        audit_service.log_event(
            event_type=AuditEventType.DOCUMENT_OPERATION_APPLIED,
            action=f"Operation applied to document: {operation.type.value}",
            user_id=user_id,
            details={
                "document_id": document_id,
                "operation_type": operation.type.value,
                "position": operation.position,
                "length": operation.length,
                "version": doc_state.version
            }
        )
        
        return doc_state, transformed_ops
    
    async def update_cursor_position(
        self, 
        document_id: str, 
        user_id: int, 
        position: int
    ):
        """
        Update user cursor position
        
        Args:
            document_id: Document ID
            user_id: User ID
            position: Cursor position
        """
        
        doc_state = await self._get_document_state(document_id)
        if doc_state and user_id in doc_state.active_users:
            doc_state.cursors[user_id] = max(0, min(position, len(doc_state.content)))
            doc_state.active_users[user_id]['last_seen'] = datetime.utcnow()
            await self._cache_document_state(doc_state)
    
    def _apply_single_operation(self, doc_state: DocumentState, operation: Operation) -> DocumentState:
        """Apply a single operation to document state"""
        
        content = doc_state.content
        
        if operation.type == OperationType.INSERT:
            # Insert text at position
            if 0 <= operation.position <= len(content):
                content = (content[:operation.position] + 
                          operation.content + 
                          content[operation.position:])
                
                # Update cursor positions for other users
                for user_id, cursor_pos in doc_state.cursors.items():
                    if cursor_pos > operation.position:
                        doc_state.cursors[user_id] = cursor_pos + len(operation.content)
        
        elif operation.type == OperationType.DELETE:
            # Delete text from position
            start = operation.position
            end = min(operation.position + operation.length, len(content))
            if 0 <= start < len(content) and start < end:
                deleted_length = end - start
                content = content[:start] + content[end:]
                
                # Update cursor positions for other users
                for user_id, cursor_pos in doc_state.cursors.items():
                    if cursor_pos > end:
                        doc_state.cursors[user_id] = cursor_pos - deleted_length
                    elif cursor_pos > start:
                        doc_state.cursors[user_id] = start
        
        elif operation.type == OperationType.FORMAT:
            # Apply formatting (stored in annotations)
            annotation = {
                'id': operation.operation_id,
                'type': 'format',
                'start': operation.position,
                'end': operation.position + operation.length,
                'attributes': operation.attributes,
                'user_id': operation.user_id,
                'created_at': operation.timestamp.isoformat()
            }
            doc_state.annotations.append(annotation)
        
        elif operation.type == OperationType.ANNOTATION:
            # Add annotation
            annotation = {
                'id': operation.operation_id,
                'type': 'annotation',
                'start': operation.position,
                'end': operation.position + operation.length,
                'content': operation.content,
                'attributes': operation.attributes,
                'user_id': operation.user_id,
                'created_at': operation.timestamp.isoformat()
            }
            doc_state.annotations.append(annotation)
        
        doc_state.content = content
        return doc_state
    
    def _get_concurrent_operations(
        self, 
        doc_state: DocumentState, 
        operation: Operation
    ) -> List[Operation]:
        """Get operations that were applied concurrently with the given operation"""
        
        # Find operations that were applied after the operation was created
        # but before it was received by the server
        concurrent_ops = []
        
        for logged_op in reversed(doc_state.operations_log):
            if logged_op.timestamp > operation.timestamp:
                concurrent_ops.append(logged_op)
            else:
                break
        
        return list(reversed(concurrent_ops))
    
    async def _transform_operations(
        self, 
        local_ops: List[Operation], 
        remote_ops: List[Operation],
        doc_state: DocumentState
    ) -> List[Operation]:
        """
        Transform operations using operational transform algorithms
        
        This implements a simplified operational transform that handles
        the most common cases for text editing.
        """
        
        if not remote_ops:
            return local_ops
        
        transformed_ops = []
        
        for local_op in local_ops:
            transformed_op = copy.deepcopy(local_op)
            
            # Transform against each remote operation
            for remote_op in remote_ops:
                transformed_op = self._transform_single_operation(
                    transformed_op, remote_op
                )
            
            # Check for conflicts and apply resolution strategy
            conflict_resolution = self._detect_conflicts(transformed_op, remote_ops)
            if conflict_resolution != TransformResult.DISCARD:
                if conflict_resolution == TransformResult.CONFLICT:
                    transformed_op = await self._resolve_conflict(
                        transformed_op, remote_ops, doc_state
                    )
                
                transformed_ops.append(transformed_op)
        
        return transformed_ops
    
    def _transform_single_operation(
        self, 
        local_op: Operation, 
        remote_op: Operation
    ) -> Operation:
        """
        Transform a local operation against a remote operation
        
        This implements the basic operational transform rules:
        - INSERT vs INSERT: Adjust position based on order
        - INSERT vs DELETE: Adjust positions accordingly  
        - DELETE vs DELETE: Handle overlapping deletes
        - etc.
        """
        
        transformed = copy.deepcopy(local_op)
        
        if local_op.type == OperationType.INSERT and remote_op.type == OperationType.INSERT:
            # Two inserts
            if remote_op.position <= local_op.position:
                # Remote insert is before local, shift local position
                transformed.position += len(remote_op.content)
            # If remote insert is after local, no change needed
        
        elif local_op.type == OperationType.INSERT and remote_op.type == OperationType.DELETE:
            # Local insert, remote delete
            remote_end = remote_op.position + remote_op.length
            
            if local_op.position > remote_end:
                # Local insert is after deleted region, shift left
                transformed.position -= remote_op.length
            elif local_op.position > remote_op.position:
                # Local insert is within deleted region, move to delete start
                transformed.position = remote_op.position
        
        elif local_op.type == OperationType.DELETE and remote_op.type == OperationType.INSERT:
            # Local delete, remote insert
            if remote_op.position <= local_op.position:
                # Remote insert is before delete region, shift delete right
                transformed.position += len(remote_op.content)
            elif remote_op.position < local_op.position + local_op.length:
                # Remote insert is within delete region, extend delete length
                transformed.length += len(remote_op.content)
        
        elif local_op.type == OperationType.DELETE and remote_op.type == OperationType.DELETE:
            # Two deletes - handle overlap
            local_end = local_op.position + local_op.length
            remote_end = remote_op.position + remote_op.length
            
            if remote_end <= local_op.position:
                # Remote delete is completely before local, shift local left
                transformed.position -= remote_op.length
            elif remote_op.position >= local_end:
                # Remote delete is completely after local, no change
                pass
            else:
                # Overlapping deletes - complex case
                overlap_start = max(local_op.position, remote_op.position)
                overlap_end = min(local_end, remote_end)
                overlap_length = max(0, overlap_end - overlap_start)
                
                if remote_op.position < local_op.position:
                    # Remote delete starts before local
                    transformed.position = remote_op.position
                    transformed.length = local_op.length - overlap_length
                else:
                    # Remote delete starts within or after local
                    transformed.length = local_op.length - overlap_length
        
        return transformed
    
    def _detect_conflicts(
        self, 
        local_op: Operation, 
        remote_ops: List[Operation]
    ) -> TransformResult:
        """Detect conflicts between operations"""
        
        for remote_op in remote_ops:
            # Check for conflicting operations
            if (local_op.type == OperationType.DELETE and 
                remote_op.type == OperationType.DELETE):
                
                # Check for overlapping deletes
                local_end = local_op.position + local_op.length
                remote_end = remote_op.position + remote_op.length
                
                overlap = not (local_end <= remote_op.position or 
                              remote_end <= local_op.position)
                
                if overlap and local_op.user_id != remote_op.user_id:
                    return TransformResult.CONFLICT
            
            elif (local_op.type == OperationType.FORMAT and 
                  remote_op.type == OperationType.FORMAT):
                
                # Check for overlapping format operations
                local_end = local_op.position + local_op.length
                remote_end = remote_op.position + remote_op.length
                
                overlap = not (local_end <= remote_op.position or 
                              remote_end <= local_op.position)
                
                if overlap and local_op.user_id != remote_op.user_id:
                    return TransformResult.CONFLICT
        
        return TransformResult.APPLY
    
    async def _resolve_conflict(
        self, 
        local_op: Operation, 
        remote_ops: List[Operation],
        doc_state: DocumentState
    ) -> Operation:
        """Resolve conflicts between operations"""
        
        # Get session to determine conflict resolution strategy
        session = None
        for sess in self.collaboration_sessions.values():
            if sess.document_id == doc_state.document_id:
                session = sess
                break
        
        strategy = 'merge_changes'
        if session:
            strategy = session.settings.get('conflict_resolution', 'merge_changes')
        
        resolver = self.conflict_resolution_strategies.get(
            strategy, 
            self._merge_changes
        )
        
        return await resolver(local_op, remote_ops, doc_state)
    
    async def _last_writer_wins(
        self, 
        local_op: Operation, 
        remote_ops: List[Operation],
        doc_state: DocumentState
    ) -> Operation:
        """Last writer wins conflict resolution"""
        
        # Keep the operation with the latest timestamp
        latest_remote = max(remote_ops, key=lambda op: op.timestamp)
        
        if local_op.timestamp > latest_remote.timestamp:
            return local_op
        else:
            # Discard local operation (return a no-op)
            return Operation(
                type=OperationType.RETAIN,
                position=0,
                length=0
            )
    
    async def _merge_changes(
        self, 
        local_op: Operation, 
        remote_ops: List[Operation],
        doc_state: DocumentState
    ) -> Operation:
        """Merge changes conflict resolution"""
        
        # For delete conflicts, merge the ranges
        if local_op.type == OperationType.DELETE:
            for remote_op in remote_ops:
                if remote_op.type == OperationType.DELETE:
                    # Merge delete ranges
                    merged_start = min(local_op.position, remote_op.position)
                    merged_end = max(
                        local_op.position + local_op.length,
                        remote_op.position + remote_op.length
                    )
                    
                    local_op.position = merged_start
                    local_op.length = merged_end - merged_start
        
        # For format conflicts, combine attributes
        elif local_op.type == OperationType.FORMAT:
            for remote_op in remote_ops:
                if remote_op.type == OperationType.FORMAT:
                    # Merge formatting attributes
                    merged_attrs = {**remote_op.attributes, **local_op.attributes}
                    local_op.attributes = merged_attrs
        
        return local_op
    
    async def _user_priority_resolution(
        self, 
        local_op: Operation, 
        remote_ops: List[Operation],
        doc_state: DocumentState
    ) -> Operation:
        """User priority-based conflict resolution"""
        
        # Simple priority: lower user_id wins
        for remote_op in remote_ops:
            if remote_op.user_id and local_op.user_id:
                if remote_op.user_id < local_op.user_id:
                    # Remote user has priority, discard local op
                    return Operation(
                        type=OperationType.RETAIN,
                        position=0,
                        length=0
                    )
        
        return local_op
    
    async def get_document_state(self, document_id: str) -> Optional[DocumentState]:
        """Get current document state"""
        return await self._get_document_state(document_id)
    
    async def get_active_sessions(self, document_id: str = None) -> List[CollaborationSession]:
        """Get active collaboration sessions"""
        
        sessions = []
        for session in self.collaboration_sessions.values():
            if document_id is None or session.document_id == document_id:
                # Check if session is still active
                if self._is_session_active(session):
                    sessions.append(session)
        
        return sessions
    
    async def get_user_sessions(self, user_id: int) -> List[CollaborationSession]:
        """Get sessions where user is a participant"""
        
        sessions = []
        for session in self.collaboration_sessions.values():
            if user_id in session.participants and self._is_session_active(session):
                sessions.append(session)
        
        return sessions
    
    def _is_session_active(self, session: CollaborationSession) -> bool:
        """Check if a session is still active"""
        
        timeout = timedelta(minutes=self.session_timeout_minutes)
        return (datetime.utcnow() - session.last_activity) < timeout
    
    async def _get_session(self, session_id: str) -> Optional[CollaborationSession]:
        """Get session from memory or cache"""
        
        # Try memory first
        if session_id in self.collaboration_sessions:
            return self.collaboration_sessions[session_id]
        
        # Try Redis cache
        try:
            cached_data = await redis_cache.get(f"collab_session:{session_id}")
            if cached_data:
                data = json.loads(cached_data)
                session = CollaborationSession(**data)
                self.collaboration_sessions[session_id] = session
                return session
        except Exception as e:
            logger.warning(f"Failed to load session from cache: {e}")
        
        return None
    
    async def _get_document_state(self, document_id: str) -> Optional[DocumentState]:
        """Get document state from memory or cache"""
        
        # Try memory first
        if document_id in self.document_states:
            return self.document_states[document_id]
        
        # Try Redis cache
        try:
            cached_data = await redis_cache.get(f"doc_state:{document_id}")
            if cached_data:
                data = json.loads(cached_data)
                
                # Reconstruct operations from dict
                operations_data = data.get('operations_log', [])
                operations = []
                for op_data in operations_data:
                    op = Operation(
                        type=OperationType(op_data['type']),
                        position=op_data['position'],
                        length=op_data.get('length', 0),
                        content=op_data.get('content', ''),
                        attributes=op_data.get('attributes', {}),
                        timestamp=datetime.fromisoformat(op_data['timestamp']),
                        user_id=op_data.get('user_id'),
                        operation_id=op_data.get('operation_id')
                    )
                    operations.append(op)
                
                data['operations_log'] = operations
                data['last_modified'] = datetime.fromisoformat(data['last_modified'])
                
                doc_state = DocumentState(**data)
                self.document_states[document_id] = doc_state
                return doc_state
        except Exception as e:
            logger.warning(f"Failed to load document state from cache: {e}")
        
        return None
    
    async def _cache_session(self, session: CollaborationSession):
        """Cache session to Redis"""
        
        try:
            # Convert to serializable format
            session_data = asdict(session)
            session_data['created_at'] = session.created_at.isoformat()
            session_data['last_activity'] = session.last_activity.isoformat()
            
            await redis_cache.set(
                f"collab_session:{session.session_id}",
                json.dumps(session_data, default=str),
                expiry=3600  # 1 hour
            )
        except Exception as e:
            logger.warning(f"Failed to cache session: {e}")
    
    async def _cache_document_state(self, doc_state: DocumentState):
        """Cache document state to Redis"""
        
        try:
            # Convert to serializable format
            state_data = asdict(doc_state)
            state_data['last_modified'] = doc_state.last_modified.isoformat()
            
            # Serialize operations
            ops_data = []
            for op in doc_state.operations_log:
                op_data = {
                    'type': op.type.value,
                    'position': op.position,
                    'length': op.length,
                    'content': op.content,
                    'attributes': op.attributes,
                    'timestamp': op.timestamp.isoformat(),
                    'user_id': op.user_id,
                    'operation_id': op.operation_id
                }
                ops_data.append(op_data)
            
            state_data['operations_log'] = ops_data
            
            await redis_cache.set(
                f"doc_state:{doc_state.document_id}",
                json.dumps(state_data, default=str),
                expiry=7200  # 2 hours
            )
        except Exception as e:
            logger.warning(f"Failed to cache document state: {e}")
    
    async def _cleanup_session(self, session_id: str):
        """Clean up a collaboration session"""
        
        try:
            # Remove from memory
            if session_id in self.collaboration_sessions:
                del self.collaboration_sessions[session_id]
            
            # Remove from cache
            await redis_cache.delete(f"collab_session:{session_id}")
            
            logger.info(f"Cleaned up session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions"""
        
        while True:
            try:
                expired_sessions = []
                
                for session_id, session in list(self.collaboration_sessions.items()):
                    if not self._is_session_active(session):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self._cleanup_session(session_id)
                
                # Sleep for 5 minutes before next cleanup
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


# Global operational transforms service instance
ot_service = OperationalTransformsService()