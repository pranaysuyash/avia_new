"""
WebSocket Router
Handles real-time communication and collaboration features
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import logging

# Import auth utilities
from api.auth import get_current_active_user, get_current_admin_user
from api.database import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Import signaling server
from api.websocket.signaling_server import signaling_server

# ===========================
# WebSocket Connection Manager
# ===========================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected to session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.info(f"WebSocket disconnected from session {session_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_session(self, message: str, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove dead connections
                    self.active_connections[session_id].discard(connection)

manager = ConnectionManager()

# ===========================
# WebSocket Endpoints
# ===========================

@router.websocket("/ws/signaling")
async def websocket_signaling(websocket: WebSocket):
    """WebRTC signaling endpoint for real-time collaboration"""
    await signaling_server.handle_connection(websocket)

@router.get("/api/v1/rooms/{room_id}")
async def get_room_info(
    room_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get information about a collaboration room"""
    return signaling_server.get_room_info(room_id)

@router.get("/api/v1/rooms")
async def get_all_rooms(
    current_user: User = Depends(get_current_admin_user)
):
    """Get all active collaboration rooms (admin only)"""
    return signaling_server.get_all_rooms()

@router.websocket("/ws/collaboration/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket endpoint for collaborative editing"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to all connections in the session
            await manager.broadcast_to_session(data, session_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        await manager.broadcast_to_session(
            f"User left session {session_id}", 
            session_id
        )