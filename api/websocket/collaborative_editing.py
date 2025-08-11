"""
Real-time Collaborative Editing WebSocket Manager
Enables multiple users to collaboratively edit transcripts and documents in real-time
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Set, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from fastapi import WebSocket, WebSocketDisconnect
import redis
from collections import defaultdict

logger = logging.getLogger(__name__)

class OperationType(str, Enum):
    """Types of collaborative operations"""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    CURSOR_MOVE = "cursor_move"
    SELECTION = "selection"
    COMMENT = "comment"
    ANNOTATION = "annotation"
    FORMAT = "format"
    UNDO = "undo"
    REDO = "redo"

class CollaborationEventType(str, Enum):
    """Types of collaboration events"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_TYPING = "user_typing"
    USER_IDLE = "user_idle"
    DOCUMENT_UPDATED = "document_updated"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    CURSOR_UPDATE = "cursor_update"
    SELECTION_UPDATE = "selection_update"
    CONFLICT_RESOLVED = "conflict_resolved"
    SAVE_STATUS = "save_status"

@dataclass
class User:
    """Collaborative user representation"""
    user_id: str
    username: str
    email: str
    avatar: Optional[str] = None
    color: str = "#3B82F6"  # Default blue
    role: str = "editor"  # editor, reviewer, viewer
    joined_at: datetime = None
    last_seen: datetime = None
    is_typing: bool = False
    cursor_position: int = 0
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None

@dataclass
class Operation:
    """Represents a collaborative editing operation"""
    operation_id: str
    user_id: str
    operation_type: OperationType
    position: int
    content: str = ""
    length: int = 0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    applied: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Comment:
    """Represents a comment on the document"""
    comment_id: str
    user_id: str
    username: str
    content: str
    position: int
    selection_start: int
    selection_end: int
    timestamp: datetime
    replies: List['Comment'] = None
    resolved: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.replies is None:
            self.replies = []
        if self.tags is None:
            self.tags = []

@dataclass
class Document:
    """Represents a collaborative document"""
    document_id: str
    content: str
    version: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = ""
    title: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

class OperationalTransform:
    """Operational Transform implementation for conflict resolution"""
    
    @staticmethod
    def transform_operation(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """Transform two concurrent operations to resolve conflicts"""
        
        if op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.INSERT:
            if op1.position <= op2.position:
                # op2 position shifts right
                op2_transformed = Operation(
                    operation_id=op2.operation_id,
                    user_id=op2.user_id,
                    operation_type=op2.operation_type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    timestamp=op2.timestamp,
                    metadata=op2.metadata
                )
                return op1, op2_transformed
            else:
                # op1 stays the same, op2 stays the same
                return op1, op2
                
        elif op1.operation_type == OperationType.DELETE and op2.operation_type == OperationType.DELETE:
            if op1.position + op1.length <= op2.position:
                # op2 position shifts left
                op2_transformed = Operation(
                    operation_id=op2.operation_id,
                    user_id=op2.user_id,
                    operation_type=op2.operation_type,
                    position=op2.position - op1.length,
                    content=op2.content,
                    length=op2.length,
                    timestamp=op2.timestamp,
                    metadata=op2.metadata
                )
                return op1, op2_transformed
            elif op2.position + op2.length <= op1.position:
                # op1 position shifts left
                op1_transformed = Operation(
                    operation_id=op1.operation_id,
                    user_id=op1.user_id,
                    operation_type=op1.operation_type,
                    position=op1.position - op2.length,
                    content=op1.content,
                    length=op1.length,
                    timestamp=op1.timestamp,
                    metadata=op1.metadata
                )
                return op1_transformed, op2
            else:
                # Overlapping deletes - more complex resolution needed
                return OperationalTransform._resolve_overlapping_deletes(op1, op2)
                
        elif op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.DELETE:
            if op1.position <= op2.position:
                # Delete position shifts right
                op2_transformed = Operation(
                    operation_id=op2.operation_id,
                    user_id=op2.user_id,
                    operation_type=op2.operation_type,
                    position=op2.position + len(op1.content),
                    content=op2.content,
                    length=op2.length,
                    timestamp=op2.timestamp,
                    metadata=op2.metadata
                )
                return op1, op2_transformed
            else:
                # Insert position shifts left if within delete range
                if op1.position <= op2.position + op2.length:
                    op1_transformed = Operation(
                        operation_id=op1.operation_id,
                        user_id=op1.user_id,
                        operation_type=op1.operation_type,
                        position=op2.position,
                        content=op1.content,
                        timestamp=op1.timestamp,
                        metadata=op1.metadata
                    )
                    return op1_transformed, op2
                else:
                    op1_transformed = Operation(
                        operation_id=op1.operation_id,
                        user_id=op1.user_id,
                        operation_type=op1.operation_type,
                        position=op1.position - op2.length,
                        content=op1.content,
                        timestamp=op1.timestamp,
                        metadata=op1.metadata
                    )
                    return op1_transformed, op2
                    
        elif op1.operation_type == OperationType.DELETE and op2.operation_type == OperationType.INSERT:
            return OperationalTransform.transform_operation(op2, op1)[::-1]  # Swap and reverse
            
        return op1, op2
    
    @staticmethod
    def _resolve_overlapping_deletes(op1: Operation, op2: Operation) -> tuple[Operation, Operation]:
        """Resolve overlapping delete operations"""
        # Simple resolution: merge the deletes
        start = min(op1.position, op2.position)
        end1 = op1.position + op1.length
        end2 = op2.position + op2.length
        end = max(end1, end2)
        
        merged_delete = Operation(
            operation_id=f"{op1.operation_id}_{op2.operation_id}",
            user_id=op1.user_id,  # Use first user's ID
            operation_type=OperationType.DELETE,
            position=start,
            length=end - start,
            timestamp=min(op1.timestamp, op2.timestamp),
            metadata={"merged": True, "original_ops": [op1.operation_id, op2.operation_id]}
        )
        
        # Return the merged operation and a no-op
        no_op = Operation(
            operation_id=op2.operation_id,
            user_id=op2.user_id,
            operation_type=OperationType.DELETE,
            position=0,
            length=0,
            timestamp=op2.timestamp,
            metadata={"no_op": True}
        )
        
        return merged_delete, no_op

class CollaborativeEditingManager:
    """Manages real-time collaborative editing sessions"""
    
    def __init__(self, redis_client=None):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # document_id -> session_data
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)  # user_id -> websockets
        self.document_connections: Dict[str, Set[WebSocket]] = defaultdict(set)  # document_id -> websockets
        self.documents: Dict[str, Document] = {}
        self.operation_history: Dict[str, List[Operation]] = defaultdict(list)
        self.comments: Dict[str, List[Comment]] = defaultdict(list)  # document_id -> comments
        self.redis_client = redis_client
        self.cleanup_task = None
        
        # Start cleanup task
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
    
    async def connect_user(self, websocket: WebSocket, document_id: str, user: User):
        """Connect a user to a collaborative editing session"""
        await websocket.accept()
        
        # Initialize session if it doesn't exist
        if document_id not in self.active_sessions:
            self.active_sessions[document_id] = {
                "users": {},
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow()
            }
        
        # Add user to session
        user.joined_at = datetime.utcnow()
        user.last_seen = datetime.utcnow()
        self.active_sessions[document_id]["users"][user.user_id] = user
        
        # Track connections
        self.user_connections[user.user_id].add(websocket)
        self.document_connections[document_id].add(websocket)
        
        # Load or create document
        if document_id not in self.documents:
            self.documents[document_id] = Document(
                document_id=document_id,
                content="",
                title=f"Collaborative Document {document_id[:8]}"
            )
        
        # Notify other users
        await self._broadcast_event(document_id, {
            "type": CollaborationEventType.USER_JOINED,
            "user": asdict(user),
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user.user_id)
        
        # Send initial state to the new user
        await self._send_to_websocket(websocket, {
            "type": "initial_state",
            "document": asdict(self.documents[document_id]),
            "users": [asdict(u) for u in self.active_sessions[document_id]["users"].values()],
            "comments": [asdict(c) for c in self.comments[document_id]],
            "user_id": user.user_id
        })
        
        logger.info(f"User {user.username} connected to document {document_id}")
    
    async def disconnect_user(self, websocket: WebSocket, document_id: str, user_id: str):
        """Disconnect a user from collaborative editing session"""
        # Remove connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        self.document_connections[document_id].discard(websocket)
        
        # Remove user from session
        if document_id in self.active_sessions and user_id in self.active_sessions[document_id]["users"]:
            user = self.active_sessions[document_id]["users"][user_id]
            del self.active_sessions[document_id]["users"][user_id]
            
            # Notify other users
            await self._broadcast_event(document_id, {
                "type": CollaborationEventType.USER_LEFT,
                "user_id": user_id,
                "username": user.username,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"User {user.username} disconnected from document {document_id}")
        
        # Clean up empty sessions
        if document_id in self.active_sessions and not self.active_sessions[document_id]["users"]:
            del self.active_sessions[document_id]
            if not self.document_connections[document_id]:
                del self.document_connections[document_id]
    
    async def handle_operation(self, document_id: str, user_id: str, operation_data: Dict[str, Any]):
        """Handle a collaborative editing operation"""
        try:
            operation = Operation(
                operation_id=operation_data.get("operation_id", str(uuid.uuid4())),
                user_id=user_id,
                operation_type=OperationType(operation_data["operation_type"]),
                position=operation_data["position"],
                content=operation_data.get("content", ""),
                length=operation_data.get("length", 0),
                metadata=operation_data.get("metadata", {})
            )
            
            # Apply operational transform with concurrent operations
            transformed_operation = await self._apply_operational_transform(document_id, operation)
            
            # Apply operation to document
            await self._apply_operation_to_document(document_id, transformed_operation)
            
            # Store in history
            self.operation_history[document_id].append(transformed_operation)
            
            # Update session activity
            if document_id in self.active_sessions:
                self.active_sessions[document_id]["last_activity"] = datetime.utcnow()
            
            # Broadcast to other users
            await self._broadcast_event(document_id, {
                "type": CollaborationEventType.DOCUMENT_UPDATED,
                "operation": asdict(transformed_operation),
                "document_version": self.documents[document_id].version,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_user=user_id)
            
            # Auto-save periodically
            await self._auto_save_document(document_id)
            
        except Exception as e:
            logger.error(f"Error handling operation: {e}")
            await self._send_error_to_user(user_id, f"Failed to process operation: {str(e)}")
    
    async def handle_cursor_update(self, document_id: str, user_id: str, cursor_data: Dict[str, Any]):
        """Handle cursor position updates"""
        if document_id in self.active_sessions and user_id in self.active_sessions[document_id]["users"]:
            user = self.active_sessions[document_id]["users"][user_id]
            user.cursor_position = cursor_data.get("position", 0)
            user.selection_start = cursor_data.get("selection_start")
            user.selection_end = cursor_data.get("selection_end")
            user.last_seen = datetime.utcnow()
            
            # Broadcast cursor update
            await self._broadcast_event(document_id, {
                "type": CollaborationEventType.CURSOR_UPDATE,
                "user_id": user_id,
                "cursor_position": user.cursor_position,
                "selection_start": user.selection_start,
                "selection_end": user.selection_end,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_user=user_id)
    
    async def handle_typing_status(self, document_id: str, user_id: str, is_typing: bool):
        """Handle typing status updates"""
        if document_id in self.active_sessions and user_id in self.active_sessions[document_id]["users"]:
            user = self.active_sessions[document_id]["users"][user_id]
            user.is_typing = is_typing
            user.last_seen = datetime.utcnow()
            
            # Broadcast typing status
            await self._broadcast_event(document_id, {
                "type": CollaborationEventType.USER_TYPING if is_typing else CollaborationEventType.USER_IDLE,
                "user_id": user_id,
                "username": user.username,
                "timestamp": datetime.utcnow().isoformat()
            }, exclude_user=user_id)
    
    async def add_comment(self, document_id: str, user_id: str, comment_data: Dict[str, Any]) -> str:
        """Add a comment to the document"""
        if document_id not in self.active_sessions:
            raise ValueError("Document session not found")
        
        user = self.active_sessions[document_id]["users"].get(user_id)
        if not user:
            raise ValueError("User not found in session")
        
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            user_id=user_id,
            username=user.username,
            content=comment_data["content"],
            position=comment_data["position"],
            selection_start=comment_data["selection_start"],
            selection_end=comment_data["selection_end"],
            timestamp=datetime.utcnow(),
            tags=comment_data.get("tags", [])
        )
        
        self.comments[document_id].append(comment)
        
        # Broadcast comment addition
        await self._broadcast_event(document_id, {
            "type": CollaborationEventType.COMMENT_ADDED,
            "comment": asdict(comment),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return comment.comment_id
    
    async def resolve_comment(self, document_id: str, comment_id: str, user_id: str):
        """Resolve a comment"""
        for comment in self.comments[document_id]:
            if comment.comment_id == comment_id:
                comment.resolved = True
                
                # Broadcast comment resolution
                await self._broadcast_event(document_id, {
                    "type": CollaborationEventType.COMMENT_UPDATED,
                    "comment_id": comment_id,
                    "resolved": True,
                    "resolved_by": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                break
    
    async def _apply_operational_transform(self, document_id: str, new_operation: Operation) -> Operation:
        """Apply operational transform to resolve conflicts"""
        # Get concurrent operations (operations that happened after the same document version)
        recent_operations = [
            op for op in self.operation_history[document_id]
            if not op.applied and op.user_id != new_operation.user_id
        ]
        
        transformed_operation = new_operation
        
        # Transform against each concurrent operation
        for existing_op in recent_operations:
            transformed_operation, _ = OperationalTransform.transform_operation(
                transformed_operation, existing_op
            )
        
        return transformed_operation
    
    async def _apply_operation_to_document(self, document_id: str, operation: Operation):
        """Apply an operation to the document content"""
        if document_id not in self.documents:
            return
        
        document = self.documents[document_id]
        content = document.content
        
        if operation.operation_type == OperationType.INSERT:
            document.content = (
                content[:operation.position] + 
                operation.content + 
                content[operation.position:]
            )
        elif operation.operation_type == OperationType.DELETE:
            end_pos = operation.position + operation.length
            document.content = (
                content[:operation.position] + 
                content[end_pos:]
            )
        elif operation.operation_type == OperationType.REPLACE:
            end_pos = operation.position + operation.length
            document.content = (
                content[:operation.position] + 
                operation.content + 
                content[end_pos:]
            )
        
        # Update document version and timestamp
        document.version += 1
        document.updated_at = datetime.utcnow()
        operation.applied = True
    
    async def _broadcast_event(self, document_id: str, event: Dict[str, Any], exclude_user: str = None):
        """Broadcast an event to all connected users in a document"""
        if document_id not in self.document_connections:
            return
        
        message = json.dumps(event)
        disconnected_websockets = set()
        
        for websocket in self.document_connections[document_id]:
            try:
                # Find the user for this websocket to check exclusion
                user_id_for_ws = None
                for uid, ws_set in self.user_connections.items():
                    if websocket in ws_set:
                        user_id_for_ws = uid
                        break
                
                if user_id_for_ws != exclude_user:
                    await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected_websockets.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected_websockets.add(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected_websockets:
            self.document_connections[document_id].discard(ws)
    
    async def _send_to_websocket(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send data to a specific websocket"""
        try:
            await websocket.send_text(json.dumps(data))
        except WebSocketDisconnect:
            pass  # Connection already closed
        except Exception as e:
            logger.error(f"Error sending to websocket: {e}")
    
    async def _send_error_to_user(self, user_id: str, error_message: str):
        """Send error message to a specific user"""
        if user_id not in self.user_connections:
            return
        
        error_data = {
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for websocket in self.user_connections[user_id]:
            await self._send_to_websocket(websocket, error_data)
    
    async def _auto_save_document(self, document_id: str):
        """Auto-save document periodically"""
        # Simple auto-save logic - save every 10 operations or 30 seconds
        operation_count = len(self.operation_history[document_id])
        
        if operation_count % 10 == 0:  # Save every 10 operations
            await self._save_document(document_id)
    
    async def _save_document(self, document_id: str):
        """Save document to persistent storage"""
        if document_id not in self.documents:
            return
        
        document = self.documents[document_id]
        
        # Here you would save to database
        # For now, we'll just broadcast save status
        await self._broadcast_event(document_id, {
            "type": CollaborationEventType.SAVE_STATUS,
            "status": "saved",
            "version": document.version,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Document {document_id} auto-saved (version {document.version})")
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions periodically"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.utcnow()
                inactive_sessions = []
                
                for document_id, session in self.active_sessions.items():
                    last_activity = session.get("last_activity", session.get("created_at"))
                    if current_time - last_activity > timedelta(hours=1):  # 1 hour timeout
                        inactive_sessions.append(document_id)
                
                for document_id in inactive_sessions:
                    logger.info(f"Cleaning up inactive session: {document_id}")
                    # Save document before cleanup
                    await self._save_document(document_id)
                    
                    # Remove session
                    if document_id in self.active_sessions:
                        del self.active_sessions[document_id]
                    if document_id in self.document_connections:
                        # Close remaining connections
                        for websocket in self.document_connections[document_id]:
                            try:
                                await websocket.close()
                            except:
                                pass
                        del self.document_connections[document_id]
                        
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

# Global manager instance
collaborative_editing_manager = CollaborativeEditingManager()