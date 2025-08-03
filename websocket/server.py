"""
WebSocket server implementation
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from typing import Dict, Set, Optional, List
import json
import logging
import asyncio
from datetime import datetime
import uuid

from api.auth_service import jwt_auth_service
from database import get_db_session, User
from .events import Event, EventType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        # Active connections: {user_id: {connection_id: websocket}}
        self.active_connections: Dict[int, Dict[str, WebSocket]] = {}
        # Room subscriptions: {room_id: set(user_ids)}
        self.rooms: Dict[str, Set[int]] = {}
        # User to rooms mapping: {user_id: set(room_ids)}
        self.user_rooms: Dict[int, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, connection_id: str):
        """Accept and register a new connection"""
        await websocket.accept()
        
        # Initialize user connections if needed
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
        
        # Add connection
        self.active_connections[user_id][connection_id] = websocket
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        
        # Send welcome message
        await self.send_personal_message(
            Event(
                type=EventType.CONNECTION_ESTABLISHED,
                data={
                    "connection_id": connection_id,
                    "message": "Connected to real-time service"
                }
            ),
            user_id,
            connection_id
        )
    
    def disconnect(self, user_id: int, connection_id: str):
        """Remove a connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].pop(connection_id, None)
            
            # Remove user dict if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Leave all rooms
                if user_id in self.user_rooms:
                    for room_id in self.user_rooms[user_id]:
                        self.rooms[room_id].discard(user_id)
                    del self.user_rooms[user_id]
        
        # Remove metadata
        self.connection_metadata.pop(connection_id, None)
        
        logger.info(f"User {user_id} disconnected (connection {connection_id})")
    
    async def join_room(self, room_id: str, user_id: int):
        """Join a room for group messaging"""
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        
        self.rooms[room_id].add(user_id)
        
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        
        self.user_rooms[user_id].add(room_id)
        
        logger.info(f"User {user_id} joined room {room_id}")
        
        # Notify room members
        await self.broadcast_to_room(
            Event(
                type=EventType.USER_JOINED_ROOM,
                data={
                    "user_id": user_id,
                    "room_id": room_id
                }
            ),
            room_id,
            exclude_user=user_id
        )
    
    async def leave_room(self, room_id: str, user_id: int):
        """Leave a room"""
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)
        
        logger.info(f"User {user_id} left room {room_id}")
        
        # Notify room members
        await self.broadcast_to_room(
            Event(
                type=EventType.USER_LEFT_ROOM,
                data={
                    "user_id": user_id,
                    "room_id": room_id
                }
            ),
            room_id
        )
    
    async def send_personal_message(
        self,
        event: Event,
        user_id: int,
        connection_id: Optional[str] = None
    ):
        """Send message to specific user"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id]
            
            if connection_id:
                # Send to specific connection
                websocket = connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send_json(event.to_dict())
                    except Exception as e:
                        logger.error(f"Error sending to connection {connection_id}: {e}")
            else:
                # Send to all user connections
                for conn_id, websocket in connections.items():
                    try:
                        await websocket.send_json(event.to_dict())
                    except Exception as e:
                        logger.error(f"Error sending to connection {conn_id}: {e}")
    
    async def broadcast_to_room(
        self,
        event: Event,
        room_id: str,
        exclude_user: Optional[int] = None
    ):
        """Broadcast message to all users in a room"""
        if room_id in self.rooms:
            for user_id in self.rooms[room_id]:
                if user_id != exclude_user:
                    await self.send_personal_message(event, user_id)
    
    async def broadcast_to_users(self, event: Event, user_ids: List[int]):
        """Broadcast message to specific users"""
        for user_id in user_ids:
            await self.send_personal_message(event, user_id)
    
    async def broadcast_all(self, event: Event, exclude_user: Optional[int] = None):
        """Broadcast message to all connected users"""
        for user_id in self.active_connections:
            if user_id != exclude_user:
                await self.send_personal_message(event, user_id)
    
    async def handle_ping(self, user_id: int, connection_id: str):
        """Handle ping message to keep connection alive"""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
        
        # Send pong
        await self.send_personal_message(
            Event(type=EventType.PONG, data={"timestamp": datetime.utcnow().isoformat()}),
            user_id,
            connection_id
        )
    
    def get_user_connections(self, user_id: int) -> int:
        """Get number of active connections for a user"""
        return len(self.active_connections.get(user_id, {}))
    
    def get_room_users(self, room_id: str) -> Set[int]:
        """Get users in a room"""
        return self.rooms.get(room_id, set())
    
    def get_online_users(self) -> List[int]:
        """Get list of online user IDs"""
        return list(self.active_connections.keys())


class WebSocketManager:
    """Main WebSocket manager with event handling"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.event_handlers = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        # Import handlers to avoid circular imports
        from .handlers import (
            TranscriptEventHandler,
            NotificationEventHandler,
            CollaborationEventHandler,
            ProcessingEventHandler
        )
        
        # Register handlers
        self.register_handler(EventType.TRANSCRIPT_UPDATED, TranscriptEventHandler())
        self.register_handler(EventType.NOTIFICATION_NEW, NotificationEventHandler())
        self.register_handler(EventType.ANNOTATION_ADDED, CollaborationEventHandler())
        self.register_handler(EventType.PROCESSING_PROGRESS, ProcessingEventHandler())
    
    def register_handler(self, event_type: EventType, handler):
        """Register an event handler"""
        self.event_handlers[event_type] = handler
    
    async def handle_connection(self, websocket: WebSocket, token: str):
        """Handle a new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        user_id = None
        
        try:
            # Verify token and get user
            user_info = jwt_auth_service.validate_token(token)
            
            if not user_info:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
            
            user_id = user_info['user_id']
            
            # Connect
            await self.connection_manager.connect(websocket, user_id, connection_id)
            
            # Listen for messages
            while True:
                data = await websocket.receive_text()
                await self.handle_message(user_id, connection_id, data)
                
        except WebSocketDisconnect:
            if user_id:
                self.connection_manager.disconnect(user_id, connection_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if user_id:
                self.connection_manager.disconnect(user_id, connection_id)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    
    async def handle_message(self, user_id: int, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            event_type = EventType(data.get("type"))
            event_data = data.get("data", {})
            
            # Handle special events
            if event_type == EventType.PING:
                await self.connection_manager.handle_ping(user_id, connection_id)
                return
            
            elif event_type == EventType.JOIN_ROOM:
                room_id = event_data.get("room_id")
                if room_id:
                    await self.connection_manager.join_room(room_id, user_id)
                return
            
            elif event_type == EventType.LEAVE_ROOM:
                room_id = event_data.get("room_id")
                if room_id:
                    await self.connection_manager.leave_room(room_id, user_id)
                return
            
            # Handle other events with registered handlers
            handler = self.event_handlers.get(event_type)
            if handler:
                await handler.handle(
                    event=Event(type=event_type, data=event_data),
                    user_id=user_id,
                    connection_manager=self.connection_manager
                )
            else:
                logger.warning(f"No handler for event type: {event_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from user {user_id}: {message}")
        except ValueError as e:
            logger.error(f"Invalid event type from user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {e}")
    
    async def broadcast_event(self, event: Event, target: Optional[Dict] = None):
        """Broadcast an event to specific targets"""
        if not target:
            # Broadcast to all
            await self.connection_manager.broadcast_all(event)
        elif "room_id" in target:
            # Broadcast to room
            await self.connection_manager.broadcast_to_room(
                event,
                target["room_id"],
                exclude_user=target.get("exclude_user")
            )
        elif "user_ids" in target:
            # Broadcast to specific users
            await self.connection_manager.broadcast_to_users(
                event,
                target["user_ids"]
            )
        elif "user_id" in target:
            # Send to specific user
            await self.connection_manager.send_personal_message(
                event,
                target["user_id"]
            )


# Global WebSocket manager instance
websocket_manager = WebSocketManager()