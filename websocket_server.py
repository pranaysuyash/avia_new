"""
WebSocket Server for Real-time Collaboration
Handles WebSocket connections for live features
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import websocket libraries
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Install with: pip install fastapi websockets")

try:
    import socketio
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("SocketIO not available. Install with: pip install python-socketio")

from realtime_collaboration import (
    RealtimeCollaborationManager, CollaborationEventType, 
    CollaborationEvent, CollaborationSession
)
from security_manager import SecurityManager

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}  # session_id -> {user_id: websocket}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self.connection_metadata: Dict[str, Dict] = {}  # connection_id -> metadata
    
    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        self.active_connections[session_id][user_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(session_id)
        
        # Store metadata
        connection_id = f"{session_id}_{user_id}"
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }
        
        logger.info(f"WebSocket connected: {user_id} to session {session_id}")
    
    def disconnect(self, session_id: str, user_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                del self.active_connections[session_id][user_id]
                
                # Clean up empty sessions
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
        
        # Update user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(session_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove metadata
        connection_id = f"{session_id}_{user_id}"
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        
        logger.info(f"WebSocket disconnected: {user_id} from session {session_id}")
    
    async def send_to_user(self, session_id: str, user_id: str, message: dict):
        """Send message to specific user"""
        if session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                websocket = self.active_connections[session_id][user_id]
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    self.disconnect(session_id, user_id)
    
    async def broadcast_to_session(
        self,
        session_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """Broadcast message to all users in session"""
        if session_id in self.active_connections:
            disconnected_users = []
            
            for user_id, websocket in self.active_connections[session_id].items():
                if user_id == exclude_user:
                    continue
                
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected_users.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected_users:
                self.disconnect(session_id, user_id)
    
    async def send_to_users(self, session_id: str, user_ids: list, message: dict):
        """Send message to specific users"""
        for user_id in user_ids:
            await self.send_to_user(session_id, user_id, message)


# FastAPI WebSocket implementation
if FASTAPI_AVAILABLE:
    
    class FastAPIWebSocketServer:
        """FastAPI-based WebSocket server"""
        
        def __init__(self, app: FastAPI):
            self.app = app
            self.connection_manager = WebSocketConnectionManager()
            self.collab_manager = RealtimeCollaborationManager()
            self.security_manager = SecurityManager()
            
            # Register WebSocket endpoints
            self._register_endpoints()
            
            # Register collaboration event handlers
            self._register_event_handlers()
        
        def _register_endpoints(self):
            """Register WebSocket endpoints"""
            
            @self.app.websocket("/ws/collaborate/{session_id}")
            async def websocket_endpoint(
                websocket: WebSocket,
                session_id: str,
                token: str
            ):
                """WebSocket endpoint for collaboration"""
                user_id = None
                
                try:
                    # Authenticate user
                    user_id = self.security_manager.access_control.validate_token(token)
                    if not user_id:
                        await websocket.close(code=4001, reason="Invalid token")
                        return
                    
                    # Connect to WebSocket
                    await self.connection_manager.connect(websocket, session_id, user_id)
                    
                    # Join collaboration session
                    try:
                        await self.collab_manager.join_session(session_id, user_id)
                    except Exception as e:
                        await websocket.close(code=4002, reason=str(e))
                        return
                    
                    # Send initial session state
                    session_info = self.collab_manager.get_session_info(session_id)
                    await websocket.send_json({
                        "type": "session_state",
                        "data": session_info
                    })
                    
                    # Handle messages
                    while True:
                        data = await websocket.receive_json()
                        await self._handle_websocket_message(
                            session_id, user_id, data
                        )
                
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected: {user_id}")
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                finally:
                    if user_id:
                        self.connection_manager.disconnect(session_id, user_id)
                        await self.collab_manager.leave_session(session_id, user_id)
        
        async def _handle_websocket_message(
            self,
            session_id: str,
            user_id: str,
            message: dict
        ):
            """Handle incoming WebSocket message"""
            msg_type = message.get("type")
            data = message.get("data", {})
            
            try:
                if msg_type == "cursor_position":
                    await self.collab_manager.update_cursor_position(
                        session_id, user_id,
                        data["position"],
                        data.get("selection_start"),
                        data.get("selection_end")
                    )
                
                elif msg_type == "transcript_update":
                    await self.collab_manager.update_transcript(
                        session_id, user_id,
                        data["operation"],
                        data["position"],
                        data["content"],
                        data.get("length")
                    )
                
                elif msg_type == "add_comment":
                    comment_id = await self.collab_manager.add_comment(
                        session_id, user_id,
                        data["position"],
                        data["text"],
                        data.get("selection_start"),
                        data.get("selection_end")
                    )
                    
                    # Send confirmation
                    await self.connection_manager.send_to_user(
                        session_id, user_id,
                        {"type": "comment_added", "data": {"comment_id": comment_id}}
                    )
                
                elif msg_type == "typing_indicator":
                    await self.collab_manager.set_typing_indicator(
                        session_id, user_id, data["is_typing"]
                    )
                
                elif msg_type == "live_audio":
                    # Handle live audio streaming
                    audio_data = data.get("audio_chunk")
                    if audio_data:
                        text = await self.collab_manager.stream_live_transcription(
                            session_id, user_id,
                            audio_data,
                            data.get("is_final", False)
                        )
                        
                        if text:
                            await self.connection_manager.send_to_user(
                                session_id, user_id,
                                {"type": "transcription_result", "data": {"text": text}}
                            )
                
                elif msg_type == "create_version":
                    version_id = await self.collab_manager.create_version(
                        session_id, user_id,
                        data.get("name"),
                        data.get("description")
                    )
                    
                    await self.connection_manager.send_to_user(
                        session_id, user_id,
                        {"type": "version_created", "data": {"version_id": version_id}}
                    )
                
                elif msg_type == "ping":
                    # Handle ping/pong for connection keep-alive
                    await self.connection_manager.send_to_user(
                        session_id, user_id,
                        {"type": "pong", "data": {"timestamp": datetime.now().isoformat()}}
                    )
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
            
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await self.connection_manager.send_to_user(
                    session_id, user_id,
                    {"type": "error", "data": {"message": str(e)}}
                )
        
        def _register_event_handlers(self):
            """Register handlers for collaboration events"""
            
            async def handle_collaboration_event(event: CollaborationEvent):
                """Handle collaboration events and broadcast to WebSocket clients"""
                event_data = event.to_dict()
                
                # Determine message type based on event
                message = {
                    "type": event.event_type.value,
                    "data": event_data
                }
                
                # Broadcast to session
                await self.connection_manager.broadcast_to_session(
                    event.session_id,
                    message,
                    exclude_user=event.user_id if event.event_type in [
                        CollaborationEventType.CURSOR_POSITION,
                        CollaborationEventType.TYPING_INDICATOR
                    ] else None
                )
            
            # Register handler for all event types
            for event_type in CollaborationEventType:
                self.collab_manager.register_event_handler(
                    event_type,
                    handle_collaboration_event
                )


# Socket.IO implementation
if SOCKETIO_AVAILABLE:
    
    class SocketIOServer:
        """Socket.IO-based WebSocket server"""
        
        def __init__(self):
            self.sio = socketio.AsyncServer(
                async_mode='asgi',
                cors_allowed_origins='*'
            )
            self.app = socketio.ASGIApp(self.sio)
            self.collab_manager = RealtimeCollaborationManager()
            self.security_manager = SecurityManager()
            self.sessions: Dict[str, Dict[str, str]] = {}  # sid -> {user_id, session_id}
            
            # Register Socket.IO event handlers
            self._register_handlers()
        
        def _register_handlers(self):
            """Register Socket.IO event handlers"""
            
            @self.sio.event
            async def connect(sid, environ):
                """Handle client connection"""
                logger.info(f"Client connected: {sid}")
            
            @self.sio.event
            async def disconnect(sid):
                """Handle client disconnection"""
                if sid in self.sessions:
                    user_data = self.sessions[sid]
                    await self.collab_manager.leave_session(
                        user_data['session_id'],
                        user_data['user_id']
                    )
                    del self.sessions[sid]
                logger.info(f"Client disconnected: {sid}")
            
            @self.sio.event
            async def join_session(sid, data):
                """Join collaboration session"""
                try:
                    token = data.get('token')
                    session_id = data.get('session_id')
                    
                    # Authenticate
                    user_id = self.security_manager.access_control.validate_token(token)
                    if not user_id:
                        await self.sio.emit('error', {'message': 'Invalid token'}, to=sid)
                        return
                    
                    # Join session
                    await self.collab_manager.join_session(session_id, user_id)
                    
                    # Store session info
                    self.sessions[sid] = {
                        'user_id': user_id,
                        'session_id': session_id
                    }
                    
                    # Join Socket.IO room
                    await self.sio.enter_room(sid, session_id)
                    
                    # Send session state
                    session_info = self.collab_manager.get_session_info(session_id)
                    await self.sio.emit('session_state', session_info, to=sid)
                    
                except Exception as e:
                    await self.sio.emit('error', {'message': str(e)}, to=sid)
            
            @self.sio.event
            async def cursor_update(sid, data):
                """Handle cursor position update"""
                if sid in self.sessions:
                    user_data = self.sessions[sid]
                    await self.collab_manager.update_cursor_position(
                        user_data['session_id'],
                        user_data['user_id'],
                        data['position'],
                        data.get('selection_start'),
                        data.get('selection_end')
                    )
            
            @self.sio.event
            async def transcript_update(sid, data):
                """Handle transcript update"""
                if sid in self.sessions:
                    user_data = self.sessions[sid]
                    await self.collab_manager.update_transcript(
                        user_data['session_id'],
                        user_data['user_id'],
                        data['operation'],
                        data['position'],
                        data['content'],
                        data.get('length')
                    )
            
            @self.sio.event
            async def add_comment(sid, data):
                """Handle comment addition"""
                if sid in self.sessions:
                    user_data = self.sessions[sid]
                    comment_id = await self.collab_manager.add_comment(
                        user_data['session_id'],
                        user_data['user_id'],
                        data['position'],
                        data['text'],
                        data.get('selection_start'),
                        data.get('selection_end')
                    )
                    
                    await self.sio.emit(
                        'comment_added',
                        {'comment_id': comment_id},
                        to=sid
                    )
            
            @self.sio.event
            async def typing_indicator(sid, data):
                """Handle typing indicator"""
                if sid in self.sessions:
                    user_data = self.sessions[sid]
                    await self.collab_manager.set_typing_indicator(
                        user_data['session_id'],
                        user_data['user_id'],
                        data['is_typing']
                    )


def create_websocket_app():
    """Create WebSocket application"""
    if FASTAPI_AVAILABLE:
        # Create FastAPI app with WebSocket support
        app = FastAPI(
            title="Realtime Collaboration WebSocket Server",
            description="WebSocket server for real-time collaboration features"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create WebSocket server
        ws_server = FastAPIWebSocketServer(app)
        
        # Add health check endpoint
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "websocket": "ready"}
        
        return app
    
    elif SOCKETIO_AVAILABLE:
        # Create Socket.IO app
        server = SocketIOServer()
        return server.app
    
    else:
        raise RuntimeError("No WebSocket library available. Install fastapi or python-socketio")


# Example usage
if __name__ == "__main__":
    import uvicorn
    
    app = create_websocket_app()
    
    if FASTAPI_AVAILABLE:
        print("Starting FastAPI WebSocket server on http://localhost:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        print("WebSocket libraries not available. Please install dependencies.")