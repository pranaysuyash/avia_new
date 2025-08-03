"""
Enhanced WebSocket routes with JWT authentication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, Request
from typing import Optional
import logging

from websocket.enhanced_server import enhanced_websocket_manager

logger = logging.getLogger(__name__)

# Router setup
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    request: Request = None
):
    """
    Enhanced WebSocket endpoint with JWT authentication
    
    Connect with: ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN
    
    Message Format:
    {
        "type": "event_type",
        "data": {
            // Event-specific data
        }
    }
    
    Connection Events:
    - Send: {"type": "ping", "data": {}}
    - Receive: {"type": "pong", "data": {"timestamp": "2024-01-01T00:00:00"}}
    
    Room Management:
    - Send: {"type": "room.join", "data": {"room_id": "transcript:123"}}
    - Send: {"type": "room.leave", "data": {"room_id": "transcript:123"}}
    
    Transcript Events:
    - Send: {"type": "transcript.updated", "data": {"transcript_id": 123, "changes": {}}}
    - Receive: Updates from other users in the same transcript
    
    Collaboration:
    - Send: {"type": "user.typing", "data": {"transcript_id": 123}}
    - Send: {"type": "annotation.added", "data": {"transcript_id": 123, "start_pos": 0, "end_pos": 10, "text": "Note"}}
    
    Processing Updates:
    - Receive: {"type": "processing.progress", "data": {"job_id": "job_123", "progress": 50}}
    - Receive: {"type": "processing.completed", "data": {"job_id": "job_123", "result": {}}}
    
    Notifications:
    - Receive: {"type": "notification.new", "data": {"title": "New share", "message": "..."}}
    """
    # Extract connection info
    user_agent = request.headers.get('User-Agent') if request else None
    ip_address = request.client.host if request and request.client else None
    
    # Handle connection
    await enhanced_websocket_manager.handle_connection(
        websocket=websocket,
        token=token,
        user_agent=user_agent,
        ip_address=ip_address
    )


@websocket_router.get("/ws/metrics")
async def get_websocket_metrics():
    """Get WebSocket server metrics"""
    return enhanced_websocket_manager.get_metrics()


@websocket_router.get("/ws/connections/{user_id}")
async def get_user_connections(user_id: int):
    """Get information about a user's WebSocket connections"""
    return enhanced_websocket_manager.get_user_connections(user_id)


# WebSocket event emitter for use in other parts of the application
class WebSocketEventEmitter:
    """Helper class to emit WebSocket events from other parts of the application"""
    
    @staticmethod
    async def emit_transcript_update(transcript_id: int, user_id: int, changes: dict):
        """Emit transcript update event"""
        from websocket.events import Event, EventType
        
        event = Event(
            type=EventType.TRANSCRIPT_UPDATED,
            data={
                "transcript_id": transcript_id,
                "user_id": user_id,
                "changes": changes
            },
            user_id=user_id
        )
        
        await enhanced_websocket_manager.broadcast_event(
            event,
            target={"room_id": f"transcript:{transcript_id}", "exclude_user": user_id}
        )
    
    @staticmethod
    async def emit_processing_progress(job_id: str, user_id: int, progress: int, message: str = ""):
        """Emit processing progress event"""
        from websocket.events import Event, EventType
        
        event = Event(
            type=EventType.PROCESSING_PROGRESS,
            data={
                "job_id": job_id,
                "progress": progress,
                "status": "processing",
                "message": message
            }
        )
        
        await enhanced_websocket_manager.broadcast_event(
            event,
            target={"user_id": user_id}
        )
    
    @staticmethod
    async def emit_processing_complete(job_id: str, user_id: int, result: dict):
        """Emit processing complete event"""
        from websocket.events import Event, EventType
        
        event = Event(
            type=EventType.PROCESSING_COMPLETED,
            data={
                "job_id": job_id,
                "result": result,
                "status": "completed"
            }
        )
        
        await enhanced_websocket_manager.broadcast_event(
            event,
            target={"user_id": user_id}
        )
    
    @staticmethod
    async def emit_notification(user_id: int, title: str, message: str, notification_type: str = "info"):
        """Emit notification event"""
        from websocket.events import Event, EventType
        
        event = Event(
            type=EventType.NOTIFICATION_NEW,
            data={
                "title": title,
                "message": message,
                "type": notification_type,
                "target_user_id": user_id
            }
        )
        
        await enhanced_websocket_manager.broadcast_event(
            event,
            target={"user_id": user_id}
        )
    
    @staticmethod
    async def emit_team_update(team_id: int, update_type: str, data: dict):
        """Emit team update event"""
        from websocket.events import Event, EventType
        
        event_type_map = {
            "member_added": EventType.TEAM_MEMBER_ADDED,
            "member_removed": EventType.TEAM_MEMBER_REMOVED,
            "team_updated": EventType.TEAM_UPDATED
        }
        
        event = Event(
            type=event_type_map.get(update_type, EventType.TEAM_UPDATED),
            data={
                "team_id": team_id,
                **data
            }
        )
        
        # This will be handled by TeamEventHandler which will find all team members
        await enhanced_websocket_manager.broadcast_event(event)
    
    @staticmethod
    async def emit_system_announcement(message: str, severity: str = "info"):
        """Emit system-wide announcement"""
        from websocket.events import Event, EventType
        
        event = Event(
            type=EventType.SYSTEM_ANNOUNCEMENT,
            data={
                "message": message,
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        await enhanced_websocket_manager.broadcast_event(event)


# Export the event emitter for use in other modules
ws_event_emitter = WebSocketEventEmitter()