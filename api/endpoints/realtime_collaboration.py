"""
Real-time Collaboration API Endpoints
Provides REST API for operational transforms and collaborative editing
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio
import logging

from api.database import get_db, User, Transcript
from api.auth import get_current_active_user
from services.operational_transforms_service import (
    ot_service,
    Operation,
    OperationType,
    CollaborationSession,
    DocumentState
)
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/collaboration",
    tags=["collaboration"],
    responses={404: {"description": "Not found"}},
)


# Pydantic models
class OperationRequest(BaseModel):
    """Operation request model"""
    type: OperationType = Field(..., description="Operation type")
    position: int = Field(..., ge=0, description="Operation position")
    length: int = Field(default=0, ge=0, description="Operation length")
    content: str = Field(default="", description="Content to insert")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Operation attributes")


class CreateSessionRequest(BaseModel):
    """Create collaboration session request"""
    document_id: str = Field(..., description="Document identifier")
    initial_content: str = Field(default="", description="Initial document content")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Session settings")


class JoinSessionRequest(BaseModel):
    """Join session request"""
    session_id: str = Field(..., description="Session to join")


class UpdateCursorRequest(BaseModel):
    """Update cursor position request"""
    document_id: str = Field(..., description="Document ID")
    position: int = Field(..., ge=0, description="Cursor position")


class CollaborationSessionResponse(BaseModel):
    """Collaboration session response"""
    session_id: str
    document_id: str
    participants: Dict[str, Dict[str, Any]]
    created_at: str
    last_activity: str
    settings: Dict[str, Any]


class DocumentStateResponse(BaseModel):
    """Document state response"""
    document_id: str
    content: str
    version: int
    last_modified: str
    active_users: Dict[str, Dict[str, Any]]
    cursors: Dict[str, int]
    annotations: List[Dict[str, Any]]


class OperationResponse(BaseModel):
    """Operation response"""
    operation_id: str
    success: bool
    document_version: int
    transformed_operations: List[Dict[str, Any]]


# Connection manager for WebSocket connections
class CollaborationConnectionManager:
    """Manages WebSocket connections for collaboration"""
    
    def __init__(self):
        # session_id -> List[WebSocket connections]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # websocket -> user_info
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        user_id: int,
        username: str
    ):
        """Accept WebSocket connection and add to session"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        
        self.active_connections[session_id].append(websocket)
        self.connection_info[websocket] = {
            'session_id': session_id,
            'user_id': user_id,
            'username': username,
            'connected_at': datetime.utcnow()
        }
        
        logger.info(f"User {username} connected to session {session_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.connection_info:
            info = self.connection_info[websocket]
            session_id = info['session_id']
            
            # Remove from active connections
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)
                
                # Clean up empty session connections
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            del self.connection_info[websocket]
            
            logger.info(f"User {info['username']} disconnected from session {session_id}")
    
    async def broadcast_to_session(
        self, 
        session_id: str, 
        message: Dict[str, Any],
        exclude_websocket: WebSocket = None
    ):
        """Broadcast message to all connections in a session"""
        if session_id not in self.active_connections:
            return
        
        connections = self.active_connections[session_id].copy()
        for connection in connections:
            if connection != exclude_websocket:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to connection: {e}")
                    # Remove failed connection
                    self.disconnect(connection)
    
    async def send_to_user(
        self, 
        session_id: str, 
        user_id: int, 
        message: Dict[str, Any]
    ):
        """Send message to specific user in session"""
        if session_id not in self.active_connections:
            return
        
        for connection in self.active_connections[session_id]:
            if connection in self.connection_info:
                if self.connection_info[connection]['user_id'] == user_id:
                    try:
                        await connection.send_text(json.dumps(message))
                    except Exception as e:
                        logger.warning(f"Failed to send message to user {user_id}: {e}")
                        self.disconnect(connection)
    
    def get_session_connections(self, session_id: str) -> List[WebSocket]:
        """Get all connections for a session"""
        return self.active_connections.get(session_id, [])


# Global connection manager
connection_manager = CollaborationConnectionManager()


# REST API Endpoints
@router.post("/sessions", response_model=CollaborationSessionResponse)
async def create_collaboration_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new collaboration session
    
    Creates a new real-time collaboration session for a document.
    The creator becomes the first participant.
    """
    try:
        # Verify document exists and user has access
        if request.document_id.isdigit():
            transcript = db.query(Transcript).filter(
                Transcript.id == int(request.document_id),
                Transcript.user_id == current_user.id
            ).first()
            
            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found or access denied"
                )
            
            initial_content = request.initial_content or transcript.content or ""
        else:
            # Non-transcript document
            initial_content = request.initial_content
        
        # Create session
        user_info = {
            'user_id': current_user.id,
            'username': current_user.username,
            'full_name': current_user.full_name,
            'email': current_user.email
        }
        
        session = await ot_service.create_collaboration_session(
            document_id=request.document_id,
            user_id=current_user.id,
            user_info=user_info,
            initial_content=initial_content
        )
        
        # Update session settings if provided
        if request.settings:
            session.settings.update(request.settings)
            # Re-cache with updated settings
            await ot_service._cache_session(session)
        
        return CollaborationSessionResponse(
            session_id=session.session_id,
            document_id=session.document_id,
            participants={str(k): v for k, v in session.participants.items()},
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            settings=session.settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create collaboration session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collaboration session: {str(e)}"
        )


@router.post("/sessions/{session_id}/join", response_model=CollaborationSessionResponse)
async def join_collaboration_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Join an existing collaboration session
    
    Adds the current user as a participant in the session.
    """
    try:
        user_info = {
            'user_id': current_user.id,
            'username': current_user.username,
            'full_name': current_user.full_name,
            'email': current_user.email
        }
        
        session, doc_state = await ot_service.join_session(
            session_id=session_id,
            user_id=current_user.id,
            user_info=user_info
        )
        
        # Notify other participants via WebSocket
        join_message = {
            'type': 'user_joined',
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.utcnow().isoformat(),
            'active_users': {str(k): v for k, v in doc_state.active_users.items()} if doc_state else {}
        }
        
        await connection_manager.broadcast_to_session(session_id, join_message)
        
        return CollaborationSessionResponse(
            session_id=session.session_id,
            document_id=session.document_id,
            participants={str(k): v for k, v in session.participants.items()},
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            settings=session.settings
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to join session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join session: {str(e)}"
        )


@router.post("/sessions/{session_id}/leave")
async def leave_collaboration_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Leave a collaboration session
    
    Removes the current user from the session participants.
    """
    try:
        await ot_service.leave_session(session_id, current_user.id)
        
        # Notify other participants via WebSocket
        leave_message = {
            'type': 'user_left',
            'user_id': current_user.id,
            'username': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await connection_manager.broadcast_to_session(session_id, leave_message)
        
        return {"status": "success", "message": "Left session"}
        
    except Exception as e:
        logger.error(f"Failed to leave session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave session: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=CollaborationSessionResponse)
async def get_collaboration_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get collaboration session details
    
    Returns session information if user is a participant.
    """
    try:
        session = await ot_service._get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if user is participant
        if current_user.id not in session.participants:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        return CollaborationSessionResponse(
            session_id=session.session_id,
            document_id=session.document_id,
            participants={str(k): v for k, v in session.participants.items()},
            created_at=session.created_at.isoformat(),
            last_activity=session.last_activity.isoformat(),
            settings=session.settings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/documents/{document_id}/state", response_model=DocumentStateResponse)
async def get_document_state(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current document state
    
    Returns the current state of a collaborative document.
    """
    try:
        # Verify access to document
        if document_id.isdigit():
            transcript = db.query(Transcript).filter(
                Transcript.id == int(document_id),
                Transcript.user_id == current_user.id
            ).first()
            
            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found or access denied"
                )
        
        doc_state = await ot_service.get_document_state(document_id)
        
        if not doc_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document state not found"
            )
        
        return DocumentStateResponse(
            document_id=doc_state.document_id,
            content=doc_state.content,
            version=doc_state.version,
            last_modified=doc_state.last_modified.isoformat(),
            active_users={str(k): v for k, v in doc_state.active_users.items()},
            cursors={str(k): v for k, v in doc_state.cursors.items()},
            annotations=doc_state.annotations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document state: {str(e)}"
        )


@router.post("/documents/{document_id}/operations", response_model=OperationResponse)
async def apply_operation(
    document_id: str,
    operation: OperationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Apply an operation to a document
    
    Applies an operational transform to a collaborative document
    and broadcasts the change to all participants.
    """
    try:
        # Verify access to document
        if document_id.isdigit():
            transcript = db.query(Transcript).filter(
                Transcript.id == int(document_id),
                Transcript.user_id == current_user.id
            ).first()
            
            if not transcript:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found or access denied"
                )
        
        # Create operation object
        op = Operation(
            type=operation.type,
            position=operation.position,
            length=operation.length,
            content=operation.content,
            attributes=operation.attributes,
            user_id=current_user.id
        )
        
        # Apply operation with operational transforms
        doc_state, transformed_ops = await ot_service.apply_operation(
            document_id=document_id,
            operation=op,
            user_id=current_user.id
        )
        
        # Update database if this is a transcript
        if document_id.isdigit() and transcript:
            transcript.content = doc_state.content
            transcript.updated_at = datetime.utcnow()
            db.commit()
        
        # Broadcast operation to all session participants
        operation_message = {
            'type': 'operation_applied',
            'document_id': document_id,
            'operations': [
                {
                    'operation_id': top.operation_id,
                    'type': top.type.value,
                    'position': top.position,
                    'length': top.length,
                    'content': top.content,
                    'attributes': top.attributes,
                    'user_id': top.user_id,
                    'timestamp': top.timestamp.isoformat()
                } for top in transformed_ops
            ],
            'document_version': doc_state.version,
            'user_id': current_user.id,
            'username': current_user.username
        }
        
        # Find active sessions for this document and broadcast
        active_sessions = await ot_service.get_active_sessions(document_id)
        for session in active_sessions:
            await connection_manager.broadcast_to_session(
                session.session_id, 
                operation_message
            )
        
        return OperationResponse(
            operation_id=op.operation_id,
            success=True,
            document_version=doc_state.version,
            transformed_operations=[
                {
                    'operation_id': top.operation_id,
                    'type': top.type.value,
                    'position': top.position,
                    'length': top.length,
                    'content': top.content,
                    'attributes': top.attributes,
                    'timestamp': top.timestamp.isoformat()
                } for top in transformed_ops
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply operation: {str(e)}"
        )


@router.post("/documents/{document_id}/cursor")
async def update_cursor_position(
    document_id: str,
    request: UpdateCursorRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update user cursor position
    
    Updates the cursor position for the current user in a collaborative document.
    """
    try:
        await ot_service.update_cursor_position(
            document_id=document_id,
            user_id=current_user.id,
            position=request.position
        )
        
        # Broadcast cursor update to session participants
        cursor_message = {
            'type': 'cursor_update',
            'document_id': document_id,
            'user_id': current_user.id,
            'username': current_user.username,
            'position': request.position,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Find active sessions for this document and broadcast
        active_sessions = await ot_service.get_active_sessions(document_id)
        for session in active_sessions:
            await connection_manager.broadcast_to_session(
                session.session_id, 
                cursor_message
            )
        
        return {"status": "success", "message": "Cursor position updated"}
        
    except Exception as e:
        logger.error(f"Failed to update cursor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cursor: {str(e)}"
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's active collaboration sessions
    
    Returns all active sessions where the current user is a participant.
    """
    try:
        sessions = await ot_service.get_user_sessions(current_user.id)
        
        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "document_id": session.document_id,
                    "participants": {str(k): v for k, v in session.participants.items()},
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                } for session in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user sessions: {str(e)}"
        )


# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/{session_id}")
async def collaboration_websocket(
    websocket: WebSocket, 
    session_id: str,
    token: str = None
):
    """
    WebSocket endpoint for real-time collaboration
    
    Provides real-time communication for collaborative editing.
    Handles operations, cursor updates, and user presence.
    """
    
    # Basic token validation (in production, use proper JWT validation)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # For simplicity, decode token to get user info
        # In production, use proper JWT validation
        import base64
        user_info = json.loads(base64.b64decode(token).decode())
        user_id = user_info.get('user_id')
        username = user_info.get('username', f'User{user_id}')
        
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect to session
    await connection_manager.connect(websocket, session_id, user_id, username)
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            'type': 'connection_confirmed',
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }))
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get('type')
                
                if message_type == 'ping':
                    # Respond to ping
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat()
                    }))
                
                elif message_type == 'operation':
                    # Handle real-time operation
                    try:
                        op_data = message.get('operation', {})
                        document_id = message.get('document_id')
                        
                        if not document_id:
                            continue
                        
                        # Create and apply operation
                        op = Operation(
                            type=OperationType(op_data.get('type')),
                            position=op_data.get('position', 0),
                            length=op_data.get('length', 0),
                            content=op_data.get('content', ''),
                            attributes=op_data.get('attributes', {}),
                            user_id=user_id
                        )
                        
                        # Apply operation
                        doc_state, transformed_ops = await ot_service.apply_operation(
                            document_id=document_id,
                            operation=op,
                            user_id=user_id
                        )
                        
                        # Broadcast to other participants (exclude sender)
                        operation_message = {
                            'type': 'operation_applied',
                            'document_id': document_id,
                            'operations': [
                                {
                                    'operation_id': top.operation_id,
                                    'type': top.type.value,
                                    'position': top.position,
                                    'length': top.length,
                                    'content': top.content,
                                    'attributes': top.attributes,
                                    'user_id': top.user_id,
                                    'timestamp': top.timestamp.isoformat()
                                } for top in transformed_ops
                            ],
                            'document_version': doc_state.version,
                            'user_id': user_id,
                            'username': username
                        }
                        
                        await connection_manager.broadcast_to_session(
                            session_id, 
                            operation_message,
                            exclude_websocket=websocket
                        )
                        
                        # Send acknowledgment to sender
                        await websocket.send_text(json.dumps({
                            'type': 'operation_ack',
                            'operation_id': op.operation_id,
                            'document_version': doc_state.version,
                            'success': True
                        }))
                        
                    except Exception as e:
                        logger.error(f"Failed to handle operation: {e}")
                        await websocket.send_text(json.dumps({
                            'type': 'operation_error',
                            'error': str(e)
                        }))
                
                elif message_type == 'cursor_update':
                    # Handle cursor position update
                    document_id = message.get('document_id')
                    position = message.get('position', 0)
                    
                    if document_id:
                        await ot_service.update_cursor_position(
                            document_id=document_id,
                            user_id=user_id,
                            position=position
                        )
                        
                        # Broadcast cursor update to other participants
                        cursor_message = {
                            'type': 'cursor_update',
                            'document_id': document_id,
                            'user_id': user_id,
                            'username': username,
                            'position': position,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        await connection_manager.broadcast_to_session(
                            session_id, 
                            cursor_message,
                            exclude_websocket=websocket
                        )
                
                elif message_type == 'presence_update':
                    # Handle user presence update (typing indicators, etc.)
                    status = message.get('status', 'active')
                    
                    presence_message = {
                        'type': 'presence_update',
                        'user_id': user_id,
                        'username': username,
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    await connection_manager.broadcast_to_session(
                        session_id,
                        presence_message,
                        exclude_websocket=websocket
                    )
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Invalid JSON message'
                }))
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                await websocket.send_text(json.dumps({
                    'type': 'error',
                    'message': 'Message processing failed'
                }))
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        connection_manager.disconnect(websocket)
        
        # Leave the session
        try:
            await ot_service.leave_session(session_id, user_id)
        except Exception as e:
            logger.error(f"Failed to leave session on disconnect: {e}")


# Health check
@router.get("/health")
async def collaboration_health_check():
    """
    Collaboration service health check
    """
    try:
        active_sessions = await ot_service.get_active_sessions()
        total_connections = sum(len(connections) for connections in connection_manager.active_connections.values())
        
        return {
            "status": "healthy",
            "active_sessions": len(active_sessions),
            "total_websocket_connections": total_connections,
            "session_timeout_minutes": ot_service.session_timeout_minutes,
            "max_operations_log": ot_service.max_operations_log
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }