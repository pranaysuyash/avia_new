"""
Enhanced WebSocket Connection Manager
Provides advanced features for real-time communication
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import redis
from fastapi import WebSocket

from .events import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    connection_id: str
    user_id: int
    websocket: WebSocket
    connected_at: datetime
    last_ping: datetime
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = None


class RedisConnectionManager:
    """
    Redis-backed connection manager for scaling across multiple servers
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.local_connections: Dict[str, ConnectionInfo] = {}
        self._subscription_task = None
        
    async def start(self):
        """Start the Redis subscription listener"""
        self._subscription_task = asyncio.create_task(self._listen_redis())
        
    async def stop(self):
        """Stop the Redis subscription listener"""
        if self._subscription_task:
            self._subscription_task.cancel()
            await self._subscription_task
    
    async def _listen_redis(self):
        """Listen for Redis pub/sub messages"""
        try:
            await self.pubsub.subscribe("websocket:broadcast")
            
            while True:
                message = await asyncio.to_thread(self.pubsub.get_message, timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_redis_message(message['data'])
                    
        except asyncio.CancelledError:
            await self.pubsub.unsubscribe("websocket:broadcast")
            raise
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def _handle_redis_message(self, data: str):
        """Handle incoming Redis message"""
        try:
            message = json.loads(data)
            event = Event.from_dict(message['event'])
            target_users = message.get('target_users', [])
            
            # Send to local connections
            for conn_id, conn_info in self.local_connections.items():
                if conn_info.user_id in target_users:
                    try:
                        await conn_info.websocket.send_json(event.to_dict())
                    except Exception as e:
                        logger.error(f"Error sending to connection {conn_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
    
    async def register_connection(self, conn_info: ConnectionInfo):
        """Register a new connection"""
        self.local_connections[conn_info.connection_id] = conn_info
        
        # Store in Redis
        conn_data = {
            'user_id': conn_info.user_id,
            'connection_id': conn_info.connection_id,
            'server_id': self._get_server_id(),
            'connected_at': conn_info.connected_at.isoformat()
        }
        
        # Add to user's connection set
        self.redis_client.sadd(f"user:{conn_info.user_id}:connections", conn_info.connection_id)
        self.redis_client.hset(f"connection:{conn_info.connection_id}", mapping=conn_data)
        self.redis_client.expire(f"connection:{conn_info.connection_id}", 3600)  # 1 hour TTL
        
    def unregister_connection(self, connection_id: str):
        """Unregister a connection"""
        conn_info = self.local_connections.pop(connection_id, None)
        if conn_info:
            # Remove from Redis
            self.redis_client.srem(f"user:{conn_info.user_id}:connections", connection_id)
            self.redis_client.delete(f"connection:{connection_id}")
    
    async def broadcast_to_users(self, event: Event, user_ids: List[int]):
        """Broadcast event to specific users across all servers"""
        # Send to local connections
        for conn_info in self.local_connections.values():
            if conn_info.user_id in user_ids:
                try:
                    await conn_info.websocket.send_json(event.to_dict())
                except Exception as e:
                    logger.error(f"Error sending to local connection: {e}")
        
        # Publish to Redis for other servers
        message = {
            'event': event.to_dict(),
            'target_users': user_ids
        }
        self.redis_client.publish("websocket:broadcast", json.dumps(message))
    
    def get_user_connections(self, user_id: int) -> Set[str]:
        """Get all connection IDs for a user"""
        return set(self.redis_client.smembers(f"user:{user_id}:connections"))
    
    def _get_server_id(self) -> str:
        """Get unique server identifier"""
        import socket
        return f"{socket.gethostname()}:{os.getpid()}"


class EnhancedConnectionManager:
    """
    Enhanced connection manager with additional features
    """
    
    def __init__(self, use_redis: bool = False, redis_url: Optional[str] = None):
        self.use_redis = use_redis
        
        if use_redis:
            self.redis_manager = RedisConnectionManager(redis_url or "redis://localhost:6379")
        
        # Local connection tracking
        self.connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        self.rooms: Dict[str, Set[int]] = defaultdict(set)
        self.user_rooms: Dict[int, Set[str]] = defaultdict(set)
        
        # Metrics
        self.metrics = {
            'total_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }
        
        # Connection limits
        self.max_connections_per_user = 5
        self.connection_timeout = timedelta(minutes=30)
        
    async def start(self):
        """Start the connection manager"""
        if self.use_redis:
            await self.redis_manager.start()
        
        # Start periodic cleanup
        asyncio.create_task(self._periodic_cleanup())
    
    async def stop(self):
        """Stop the connection manager"""
        if self.use_redis:
            await self.redis_manager.stop()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        connection_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Accept and register a new connection
        Returns True if successful, False if rejected
        """
        # Check connection limit
        if len(self.user_connections[user_id]) >= self.max_connections_per_user:
            logger.warning(f"User {user_id} exceeded connection limit")
            await websocket.close(code=4008, reason="Connection limit exceeded")
            return False
        
        # Accept connection
        await websocket.accept()
        
        # Create connection info
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            websocket=websocket,
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            user_agent=user_agent,
            ip_address=ip_address,
            metadata={}
        )
        
        # Register connection
        self.connections[connection_id] = conn_info
        self.user_connections[user_id].add(connection_id)
        
        if self.use_redis:
            await self.redis_manager.register_connection(conn_info)
        
        # Update metrics
        self.metrics['total_connections'] += 1
        
        # Send welcome message
        await self._send_welcome_message(conn_info)
        
        logger.info(f"User {user_id} connected (connection: {connection_id})")
        return True
    
    def disconnect(self, connection_id: str):
        """Remove a connection"""
        conn_info = self.connections.pop(connection_id, None)
        if not conn_info:
            return
        
        user_id = conn_info.user_id
        self.user_connections[user_id].discard(connection_id)
        
        # Clean up empty user entry
        if not self.user_connections[user_id]:
            del self.user_connections[user_id]
            
            # Leave all rooms
            for room_id in list(self.user_rooms[user_id]):
                self.leave_room(room_id, user_id)
            del self.user_rooms[user_id]
        
        if self.use_redis:
            self.redis_manager.unregister_connection(connection_id)
        
        logger.info(f"User {user_id} disconnected (connection: {connection_id})")
    
    def join_room(self, room_id: str, user_id: int):
        """Join a room"""
        self.rooms[room_id].add(user_id)
        self.user_rooms[user_id].add(room_id)
        logger.debug(f"User {user_id} joined room {room_id}")
    
    def leave_room(self, room_id: str, user_id: int):
        """Leave a room"""
        self.rooms[room_id].discard(user_id)
        self.user_rooms[user_id].discard(room_id)
        
        # Clean up empty room
        if not self.rooms[room_id]:
            del self.rooms[room_id]
        
        logger.debug(f"User {user_id} left room {room_id}")
    
    async def send_to_connection(self, connection_id: str, event: Event) -> bool:
        """
        Send event to specific connection
        Returns True if successful
        """
        conn_info = self.connections.get(connection_id)
        if not conn_info:
            return False
        
        try:
            await conn_info.websocket.send_json(event.to_dict())
            self.metrics['messages_sent'] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            self.metrics['errors'] += 1
            return False
    
    async def send_to_user(self, user_id: int, event: Event):
        """Send event to all connections of a user"""
        connection_ids = list(self.user_connections.get(user_id, []))
        
        for conn_id in connection_ids:
            await self.send_to_connection(conn_id, event)
    
    async def broadcast_to_room(
        self,
        room_id: str,
        event: Event,
        exclude_user: Optional[int] = None
    ):
        """Broadcast event to all users in a room"""
        user_ids = [
            user_id for user_id in self.rooms.get(room_id, [])
            if user_id != exclude_user
        ]
        
        if self.use_redis:
            await self.redis_manager.broadcast_to_users(event, user_ids)
        else:
            for user_id in user_ids:
                await self.send_to_user(user_id, event)
    
    async def broadcast_to_users(self, user_ids: List[int], event: Event):
        """Broadcast event to specific users"""
        if self.use_redis:
            await self.redis_manager.broadcast_to_users(event, user_ids)
        else:
            for user_id in user_ids:
                await self.send_to_user(user_id, event)
    
    async def broadcast_all(self, event: Event, exclude_user: Optional[int] = None):
        """Broadcast event to all connected users"""
        user_ids = [
            user_id for user_id in self.user_connections.keys()
            if user_id != exclude_user
        ]
        await self.broadcast_to_users(user_ids, event)
    
    async def handle_ping(self, connection_id: str):
        """Handle ping to keep connection alive"""
        conn_info = self.connections.get(connection_id)
        if conn_info:
            conn_info.last_ping = datetime.utcnow()
            
            pong_event = Event(
                type=EventType.PONG,
                data={"timestamp": datetime.utcnow().isoformat()}
            )
            await self.send_to_connection(connection_id, pong_event)
    
    async def _send_welcome_message(self, conn_info: ConnectionInfo):
        """Send welcome message to new connection"""
        welcome_event = Event(
            type=EventType.CONNECTION_ESTABLISHED,
            data={
                "connection_id": conn_info.connection_id,
                "user_id": conn_info.user_id,
                "server_time": datetime.utcnow().isoformat(),
                "features": {
                    "rooms": True,
                    "notifications": True,
                    "collaboration": True,
                    "real_time_updates": True
                }
            }
        )
        await self.send_to_connection(conn_info.connection_id, welcome_event)
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.utcnow()
                stale_connections = []
                
                for conn_id, conn_info in self.connections.items():
                    if now - conn_info.last_ping > self.connection_timeout:
                        stale_connections.append(conn_id)
                
                for conn_id in stale_connections:
                    logger.warning(f"Removing stale connection: {conn_id}")
                    self.disconnect(conn_id)
                    
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection metrics"""
        return {
            **self.metrics,
            'active_connections': len(self.connections),
            'active_users': len(self.user_connections),
            'active_rooms': len(self.rooms)
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a connection"""
        conn_info = self.connections.get(connection_id)
        if not conn_info:
            return None
        
        return {
            'connection_id': conn_info.connection_id,
            'user_id': conn_info.user_id,
            'connected_at': conn_info.connected_at.isoformat(),
            'last_ping': conn_info.last_ping.isoformat(),
            'user_agent': conn_info.user_agent,
            'ip_address': conn_info.ip_address
        }
    
    def get_user_info(self, user_id: int) -> Dict[str, Any]:
        """Get information about a user's connections"""
        return {
            'user_id': user_id,
            'connection_count': len(self.user_connections.get(user_id, [])),
            'connection_ids': list(self.user_connections.get(user_id, [])),
            'rooms': list(self.user_rooms.get(user_id, []))
        }