"""
Collaborative Editing API Endpoints
Supports real-time collaborative transcript editing with version control
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uuid

# Import existing services
try:
    from services.operational_transforms_service import (
        OperationalTransformsService,
        Operation,
        OperationType,
        DocumentState
    )
    from versioning.version_manager import VersionManager
    from notifications.notification_manager import NotificationManager
except ImportError:
    # Fallback if services not available
    OperationalTransformsService = None
    VersionManager = None
    NotificationManager = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/collaborative-editing", tags=["collaborative-editing"])

# Global services
_ot_service: Optional[OperationalTransformsService] = None
_version_manager: Optional[VersionManager] = None
_notification_manager: Optional[NotificationManager] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_info: Dict[str, Any]):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        self.user_sessions[f"{session_id}_{user_info['user_id']}"] = {
            "websocket": websocket,
            "user_info": user_info,
            "session_id": session_id
        }

    def disconnect(self, websocket: WebSocket, session_id: str, user_id: int):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        session_key = f"{session_id}_{user_id}"
        if session_key in self.user_sessions:
            del self.user_sessions[session_key]

    async def send_to_session(self, session_id: str, message: Dict[str, Any], exclude_user: Optional[int] = None):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    # Find user info for this connection
                    user_info = None
                    for key, session_data in self.user_sessions.items():
                        if session_data["websocket"] == connection:
                            user_info = session_data["user_info"]
                            break
                    
                    # Skip if this is the excluded user
                    if exclude_user and user_info and user_info["user_id"] == exclude_user:
                        continue
                        
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message: {e}")

    def get_session_users(self, session_id: str) -> List[Dict[str, Any]]:
        users = []
        for key, session_data in self.user_sessions.items():
            if session_data["session_id"] == session_id:
                users.append(session_data["user_info"])
        return users

manager = ConnectionManager()

# Request/Response Models
class TranscriptSegment(BaseModel):
    id: str
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    confidence: Optional[float] = None

class CollaborativeEdit(BaseModel):
    segment_id: str
    original_text: str
    new_text: str
    user_id: int
    edit_type: str = "manual"
    timestamp: Optional[str] = None

class VersionCreateRequest(BaseModel):
    description: str
    segments: List[TranscriptSegment]
    created_by: int

class VersionResponse(BaseModel):
    version_id: str
    description: str
    created_at: str
    created_by: int
    segment_count: int

def get_services():
    """Get or create service instances"""
    global _ot_service, _version_manager, _notification_manager
    
    if not _ot_service and OperationalTransformsService:
        _ot_service = OperationalTransformsService()
    
    # Version manager and notification manager would need database session
    # For now, return None if not available
    
    return _ot_service, _version_manager, _notification_manager

@router.websocket("/ws/transcript/{transcript_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, transcript_id: str, session_id: str):
    """
    WebSocket endpoint for real-time collaborative editing
    """
    user_info = None
    
    try:
        # Wait for initial user info
        await websocket.accept()
        initial_message = await websocket.receive_text()
        initial_data = json.loads(initial_message)
        
        if initial_data.get("type") == "user_join":
            user_info = initial_data.get("user")
            await manager.connect(websocket, session_id, user_info)
            
            # Notify other users about new user
            await manager.send_to_session(session_id, {
                "type": "user_joined",
                "user": user_info,
                "timestamp": datetime.now().isoformat()
            }, exclude_user=user_info["user_id"])
            
            # Send current session users to new user
            session_users = manager.get_session_users(session_id)
            await websocket.send_text(json.dumps({
                "type": "session_users",
                "users": session_users,
                "timestamp": datetime.now().isoformat()
            }))
        
        # Handle messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            
            # Process different message types
            if data["type"] == "segment_edit_start":
                await manager.send_to_session(session_id, {
                    "type": "segment_edit_start",
                    "segment_id": data["segment_id"],
                    "user_id": data["user_id"],
                    "timestamp": data["timestamp"]
                }, exclude_user=data["user_id"])
                
            elif data["type"] == "segment_edit_end":
                await manager.send_to_session(session_id, {
                    "type": "segment_edit_end",
                    "segment_id": data["segment_id"],
                    "user_id": data["user_id"],
                    "timestamp": data["timestamp"]
                }, exclude_user=data["user_id"])
                
            elif data["type"] == "segment_updated":
                # Apply operational transforms if available
                ot_service, _, _ = get_services()
                
                if ot_service:
                    # Create operation
                    operation = Operation(
                        type=OperationType.INSERT,  # Simplified for demo
                        position=0,
                        content=data["new_text"],
                        user_id=data["user_id"],
                        timestamp=datetime.now()
                    )
                    
                    # Apply operation (in real implementation, this would handle conflicts)
                    # For now, just broadcast the change
                
                await manager.send_to_session(session_id, {
                    "type": "segment_updated",
                    "segment_id": data["segment_id"],
                    "original_text": data["original_text"],
                    "new_text": data["new_text"],
                    "user_id": data["user_id"],
                    "edit_type": data.get("edit_type", "manual"),
                    "timestamp": data["timestamp"]
                }, exclude_user=data["user_id"])
                
            elif data["type"] == "version_created":
                await manager.send_to_session(session_id, {
                    "type": "version_created",
                    "version": data["version"],
                    "user_id": data["user_id"],
                    "timestamp": data["timestamp"]
                }, exclude_user=data["user_id"])
                
    except WebSocketDisconnect:
        if user_info:
            manager.disconnect(websocket, session_id, user_info["user_id"])
            await manager.send_to_session(session_id, {
                "type": "user_left",
                "user_id": user_info["user_id"],
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user_info:
            manager.disconnect(websocket, session_id, user_info["user_id"])

@router.post("/transcripts/{transcript_id}/versions", response_model=VersionResponse)
async def create_version(
    transcript_id: str,
    request: VersionCreateRequest
):
    """
    Create a new version of the transcript
    """
    try:
        _, version_manager, _ = get_services()
        
        # Create version ID
        version_id = str(uuid.uuid4())
        
        # In a real implementation, this would save to database
        version_data = {
            "version_id": version_id,
            "transcript_id": transcript_id,
            "description": request.description,
            "segments": [segment.dict() for segment in request.segments],
            "created_by": request.created_by,
            "created_at": datetime.now().isoformat(),
            "segment_count": len(request.segments)
        }
        
        # For demo purposes, return the version data
        return VersionResponse(
            version_id=version_id,
            description=request.description,
            created_at=version_data["created_at"],
            created_by=request.created_by,
            segment_count=len(request.segments)
        )
        
    except Exception as e:
        logger.error(f"Failed to create version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")

@router.get("/transcripts/{transcript_id}/versions")
async def get_version_history(transcript_id: str):
    """
    Get version history for a transcript
    """
    try:
        # In a real implementation, this would query the database
        # For demo purposes, return mock data
        versions = [
            {
                "version_id": "version_1",
                "description": "Initial version",
                "created_at": "2023-12-21T10:00:00Z",
                "created_by": 1,
                "segment_count": 10
            },
            {
                "version_id": "version_2", 
                "description": "Collaborative edits",
                "created_at": "2023-12-21T11:30:00Z",
                "created_by": 2,
                "segment_count": 12
            }
        ]
        
        return versions
        
    except Exception as e:
        logger.error(f"Failed to get version history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get version history: {str(e)}")

@router.get("/transcripts/{transcript_id}/versions/{version_id}")
async def get_version(transcript_id: str, version_id: str):
    """
    Get a specific version of the transcript
    """
    try:
        # In a real implementation, this would query the database
        # For demo purposes, return mock data
        version = {
            "version_id": version_id,
            "transcript_id": transcript_id,
            "description": "Sample version",
            "created_at": "2023-12-21T10:00:00Z",
            "created_by": 1,
            "segments": [
                {
                    "id": "segment_1",
                    "text": "Hello, this is a sample transcript.",
                    "start_time": 0.0,
                    "end_time": 3.0,
                    "speaker": "Speaker 1",
                    "confidence": 0.95
                }
            ]
        }
        
        return version
        
    except Exception as e:
        logger.error(f"Failed to get version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")

@router.post("/transcripts/{transcript_id}/apply-operation")
async def apply_operation(
    transcript_id: str,
    operation_data: Dict[str, Any]
):
    """
    Apply an operational transform operation
    """
    try:
        ot_service, _, _ = get_services()
        
        if not ot_service:
            raise HTTPException(status_code=503, detail="Operational transforms service not available")
        
        # Create operation from request data
        operation = Operation(
            type=OperationType(operation_data["type"]),
            position=operation_data["position"],
            length=operation_data.get("length", 0),
            content=operation_data.get("content", ""),
            user_id=operation_data["user_id"],
            timestamp=datetime.now()
        )
        
        # Apply operation (simplified for demo)
        result = await ot_service.apply_operation(transcript_id, operation)
        
        return {
            "success": True,
            "operation_id": operation.operation_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to apply operation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply operation: {str(e)}")

@router.get("/sessions/{session_id}/users")
async def get_session_users(session_id: str):
    """
    Get active users in a collaborative session
    """
    try:
        users = manager.get_session_users(session_id)
        return {
            "session_id": session_id,
            "users": users,
            "user_count": len(users)
        }
        
    except Exception as e:
        logger.error(f"Failed to get session users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session users: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        ot_service, version_manager, notification_manager = get_services()
        
        return {
            "status": "healthy",
            "services": {
                "operational_transforms": ot_service is not None,
                "version_manager": version_manager is not None,
                "notification_manager": notification_manager is not None
            },
            "active_sessions": len(manager.active_connections),
            "total_connections": sum(len(connections) for connections in manager.active_connections.values())
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }