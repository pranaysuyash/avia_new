"""
WebSocket routes for the API
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
import logging

from websocket.server import websocket_manager

logger = logging.getLogger(__name__)

# Router setup
websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time communication
    
    Connect with: ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN
    
    Events:
    - Send: {"type": "ping", "data": {}}
    - Receive: {"type": "pong", "data": {"timestamp": "..."}}
    
    - Send: {"type": "room.join", "data": {"room_id": "transcript_123"}}
    - Send: {"type": "room.leave", "data": {"room_id": "transcript_123"}}
    
    Broadcast events will be received automatically based on permissions
    """
    await websocket_manager.handle_connection(websocket, token)