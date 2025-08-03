"""
Enhanced WebSocket server with JWT authentication and advanced features
"""

from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, Optional
import json
import logging
import asyncio
from datetime import datetime
import uuid
import os

from api.auth_service import jwt_auth_service
from .events import Event, EventType
from .connection_manager import EnhancedConnectionManager
from .handlers import (
    TranscriptEventHandler,
    NotificationEventHandler,
    CollaborationEventHandler,
    ProcessingEventHandler,
    TeamEventHandler,
    SystemEventHandler
)

logger = logging.getLogger(__name__)


class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with advanced features"""
    
    def __init__(self, use_redis: bool = False):
        # Initialize connection manager
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.connection_manager = EnhancedConnectionManager(
            use_redis=use_redis,
            redis_url=redis_url
        )
        
        # Event handlers registry
        self.event_handlers = {}
        self._register_default_handlers()
        
        # Metrics
        self.metrics = {
            'total_connections': 0,
            'failed_connections': 0,
            'messages_processed': 0,
            'errors': 0
        }
        
        # Configuration
        self.config = {
            'max_message_size': 65536,  # 64KB
            'heartbeat_interval': 30,   # seconds
            'connection_timeout': 300,  # 5 minutes
        }
    
    async def start(self):
        """Start the WebSocket manager"""
        await self.connection_manager.start()
        logger.info("Enhanced WebSocket manager started")
    
    async def stop(self):
        """Stop the WebSocket manager"""
        await self.connection_manager.stop()
        logger.info("Enhanced WebSocket manager stopped")
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler(EventType.TRANSCRIPT_UPDATED, TranscriptEventHandler())
        self.register_handler(EventType.TRANSCRIPT_DELETED, TranscriptEventHandler())
        self.register_handler(EventType.TRANSCRIPT_SHARED, TranscriptEventHandler())
        
        self.register_handler(EventType.NOTIFICATION_NEW, NotificationEventHandler())
        self.register_handler(EventType.NOTIFICATION_READ, NotificationEventHandler())
        
        self.register_handler(EventType.ANNOTATION_ADDED, CollaborationEventHandler())
        self.register_handler(EventType.ANNOTATION_UPDATED, CollaborationEventHandler())
        self.register_handler(EventType.COMMENT_ADDED, CollaborationEventHandler())
        self.register_handler(EventType.USER_TYPING, CollaborationEventHandler())
        
        self.register_handler(EventType.PROCESSING_STARTED, ProcessingEventHandler())
        self.register_handler(EventType.PROCESSING_PROGRESS, ProcessingEventHandler())
        self.register_handler(EventType.PROCESSING_COMPLETED, ProcessingEventHandler())
        self.register_handler(EventType.PROCESSING_FAILED, ProcessingEventHandler())
        
        self.register_handler(EventType.TEAM_MEMBER_ADDED, TeamEventHandler())
        self.register_handler(EventType.TEAM_MEMBER_REMOVED, TeamEventHandler())
        self.register_handler(EventType.TEAM_UPDATED, TeamEventHandler())
        
        self.register_handler(EventType.SYSTEM_ANNOUNCEMENT, SystemEventHandler())
        self.register_handler(EventType.SYSTEM_MAINTENANCE, SystemEventHandler())
    
    def register_handler(self, event_type: EventType, handler):
        """Register an event handler"""
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for {event_type.value}")
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Handle a new WebSocket connection with JWT authentication"""
        connection_id = str(uuid.uuid4())
        user_id = None
        
        try:
            # Increment connection attempts
            self.metrics['total_connections'] += 1
            
            # Verify JWT token
            user_info = jwt_auth_service.validate_token(token)
            
            if not user_info:
                logger.warning(f"Invalid token provided for WebSocket connection")
                self.metrics['failed_connections'] += 1
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Invalid authentication token"
                )
                return
            
            user_id = user_info['user_id']
            username = user_info.get('username', f'User {user_id}')
            
            # Check if user is active
            if not user_info.get('is_active', True):
                logger.warning(f"Inactive user {user_id} attempted WebSocket connection")
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="User account is inactive"
                )
                return
            
            # Connect
            connected = await self.connection_manager.connect(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            if not connected:
                self.metrics['failed_connections'] += 1
                return
            
            logger.info(f"User {username} (ID: {user_id}) connected via WebSocket")
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(connection_id)
            )
            
            # Listen for messages
            while True:
                try:
                    # Set timeout for receiving messages
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=self.config['connection_timeout']
                    )
                    
                    # Check message size
                    if len(message) > self.config['max_message_size']:
                        await self._send_error(
                            connection_id,
                            "Message too large",
                            {"max_size": self.config['max_message_size']}
                        )
                        continue
                    
                    # Process message
                    await self.handle_message(user_id, connection_id, message)
                    self.metrics['messages_processed'] += 1
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Connection {connection_id} timed out")
                    break
                except WebSocketDisconnect:
                    logger.info(f"User {username} disconnected normally")
                    break
                except json.JSONDecodeError as e:
                    await self._send_error(
                        connection_id,
                        "Invalid JSON format",
                        {"error": str(e)}
                    )
                except Exception as e:
                    logger.error(f"Error in WebSocket connection: {e}")
                    self.metrics['errors'] += 1
                    break
            
            # Cancel heartbeat
            heartbeat_task.cancel()
            
        except Exception as e:
            logger.error(f"Fatal WebSocket error: {e}")
            self.metrics['errors'] += 1
        finally:
            # Disconnect
            if user_id and connection_id:
                self.connection_manager.disconnect(connection_id)
                logger.info(f"Cleaned up connection {connection_id} for user {user_id}")
    
    async def handle_message(self, user_id: int, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            # Parse message
            data = json.loads(message)
            
            # Validate message structure
            if 'type' not in data:
                await self._send_error(
                    connection_id,
                    "Missing 'type' field in message"
                )
                return
            
            # Parse event type
            try:
                event_type = EventType(data['type'])
            except ValueError:
                await self._send_error(
                    connection_id,
                    f"Invalid event type: {data['type']}"
                )
                return
            
            event_data = data.get('data', {})
            
            # Handle special connection events
            if event_type == EventType.PING:
                await self.connection_manager.handle_ping(connection_id)
                return
            
            elif event_type == EventType.JOIN_ROOM:
                room_id = event_data.get('room_id')
                if room_id:
                    self.connection_manager.join_room(room_id, user_id)
                    await self._send_room_joined(connection_id, room_id)
                return
            
            elif event_type == EventType.LEAVE_ROOM:
                room_id = event_data.get('room_id')
                if room_id:
                    self.connection_manager.leave_room(room_id, user_id)
                    await self._send_room_left(connection_id, room_id)
                return
            
            # Create event object
            event = Event(
                type=event_type,
                data=event_data,
                user_id=user_id
            )
            
            # Handle with registered handler
            handler = self.event_handlers.get(event_type)
            if handler:
                try:
                    await handler.handle(event, user_id, self.connection_manager)
                except Exception as e:
                    logger.error(f"Handler error for {event_type.value}: {e}")
                    await self._send_error(
                        connection_id,
                        f"Error processing {event_type.value}",
                        {"error": str(e)}
                    )
            else:
                logger.warning(f"No handler for event type: {event_type.value}")
                await self._send_error(
                    connection_id,
                    f"Unsupported event type: {event_type.value}"
                )
                
        except json.JSONDecodeError:
            await self._send_error(
                connection_id,
                "Invalid JSON message"
            )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(
                connection_id,
                "Internal error processing message"
            )
    
    async def broadcast_event(self, event: Event, target: Optional[Dict] = None):
        """Broadcast an event to specific targets"""
        if not target:
            # Broadcast to all
            await self.connection_manager.broadcast_all(event)
        elif "room_id" in target:
            # Broadcast to room
            await self.connection_manager.broadcast_to_room(
                target["room_id"],
                event,
                exclude_user=target.get("exclude_user")
            )
        elif "user_ids" in target:
            # Broadcast to specific users
            await self.connection_manager.broadcast_to_users(
                target["user_ids"],
                event
            )
        elif "user_id" in target:
            # Send to specific user
            await self.connection_manager.send_to_user(
                target["user_id"],
                event
            )
    
    async def _heartbeat_loop(self, connection_id: str):
        """Send periodic heartbeat to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(self.config['heartbeat_interval'])
                
                # Send heartbeat
                heartbeat_event = Event(
                    type=EventType.PING,
                    data={"timestamp": datetime.utcnow().isoformat()}
                )
                
                success = await self.connection_manager.send_to_connection(
                    connection_id,
                    heartbeat_event
                )
                
                if not success:
                    logger.warning(f"Failed to send heartbeat to {connection_id}")
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
    
    async def _send_error(self, connection_id: str, message: str, details: Optional[Dict] = None):
        """Send error message to connection"""
        error_event = Event(
            type=EventType.ERROR,
            data={
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await self.connection_manager.send_to_connection(connection_id, error_event)
    
    async def _send_room_joined(self, connection_id: str, room_id: str):
        """Send room joined confirmation"""
        event = Event(
            type=EventType.USER_JOINED_ROOM,
            data={
                "room_id": room_id,
                "joined_at": datetime.utcnow().isoformat()
            }
        )
        await self.connection_manager.send_to_connection(connection_id, event)
    
    async def _send_room_left(self, connection_id: str, room_id: str):
        """Send room left confirmation"""
        event = Event(
            type=EventType.USER_LEFT_ROOM,
            data={
                "room_id": room_id,
                "left_at": datetime.utcnow().isoformat()
            }
        )
        await self.connection_manager.send_to_connection(connection_id, event)
    
    def get_metrics(self) -> Dict:
        """Get WebSocket metrics"""
        return {
            **self.metrics,
            **self.connection_manager.get_metrics()
        }
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """Get information about a specific connection"""
        return self.connection_manager.get_connection_info(connection_id)
    
    def get_user_connections(self, user_id: int) -> Dict:
        """Get information about a user's connections"""
        return self.connection_manager.get_user_info(user_id)


# Global WebSocket manager instance
enhanced_websocket_manager = EnhancedWebSocketManager(
    use_redis=os.getenv('WEBSOCKET_USE_REDIS', 'false').lower() == 'true'
)