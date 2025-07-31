"""
WebSocket client for testing and development
"""

import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket client for real-time communication"""
    
    def __init__(self, url: str, token: str):
        self.url = f"{url}?token={token}"
        self.websocket = None
        self.running = False
        self.handlers = {}
        self._ping_task = None
    
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.running = True
            logger.info("Connected to WebSocket server")
            
            # Start ping task
            self._ping_task = asyncio.create_task(self._ping_loop())
            
            # Start listening
            await self._listen()
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from server"""
        self.running = False
        
        if self._ping_task:
            self._ping_task.cancel()
        
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket server")
    
    async def send(self, event_type: str, data: Dict[str, Any]):
        """Send event to server"""
        if not self.websocket:
            raise RuntimeError("Not connected")
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket.send(json.dumps(message))
        logger.debug(f"Sent event: {event_type}")
    
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.handlers[event_type] = handler
        logger.debug(f"Registered handler for {event_type}")
    
    async def join_room(self, room_id: str):
        """Join a room"""
        await self.send("room.join", {"room_id": room_id})
    
    async def leave_room(self, room_id: str):
        """Leave a room"""
        await self.send("room.leave", {"room_id": room_id})
    
    async def _listen(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                if not self.running:
                    break
                
                try:
                    data = json.loads(message)
                    event_type = data.get("type")
                    
                    # Handle event
                    handler = self.handlers.get(event_type)
                    if handler:
                        await handler(data)
                    else:
                        logger.debug(f"No handler for event: {event_type}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.running = False
    
    async def _ping_loop(self):
        """Send periodic pings to keep connection alive"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await self.send("ping", {})
            except Exception as e:
                logger.error(f"Ping error: {e}")
                break


class WebSocketTestClient:
    """Test client with predefined handlers"""
    
    def __init__(self, base_url: str, token: str):
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.client = WebSocketClient(f"{ws_url}/api/v1/ws", token)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up default handlers"""
        
        async def on_connection_established(data):
            print(f"✅ Connected: {data['data']['message']}")
        
        async def on_pong(data):
            print(f"🏓 Pong received at {data['data']['timestamp']}")
        
        async def on_transcript_updated(data):
            print(f"📝 Transcript updated: {data['data']}")
        
        async def on_notification(data):
            print(f"🔔 Notification: {data['data']['title']} - {data['data']['message']}")
        
        async def on_annotation_added(data):
            annotation = data['data']
            print(f"📌 Annotation added by user {annotation['user_id']}: {annotation['text']}")
        
        async def on_processing_progress(data):
            progress = data['data']
            print(f"⚙️ Processing {progress['job_id']}: {progress['progress']}% - {progress['status']}")
        
        async def on_user_joined(data):
            print(f"👋 User {data['data']['user_id']} joined room {data['data']['room_id']}")
        
        async def on_error(data):
            print(f"❌ Error: {data['data']}")
        
        # Register handlers
        self.client.on("connection.established", on_connection_established)
        self.client.on("pong", on_pong)
        self.client.on("transcript.updated", on_transcript_updated)
        self.client.on("notification.new", on_notification)
        self.client.on("annotation.added", on_annotation_added)
        self.client.on("processing.progress", on_processing_progress)
        self.client.on("room.user_joined", on_user_joined)
        self.client.on("error", on_error)
    
    async def run_interactive(self):
        """Run interactive test session"""
        print("🚀 WebSocket Test Client")
        print("Commands: join <room_id>, leave <room_id>, ping, quit")
        print("-" * 50)
        
        # Connect in background
        connect_task = asyncio.create_task(self.client.connect())
        
        # Interactive loop
        while self.client.running:
            try:
                # Non-blocking input
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )
                
                if command == "quit":
                    break
                elif command == "ping":
                    await self.client.send("ping", {})
                elif command.startswith("join "):
                    room_id = command.split(" ", 1)[1]
                    await self.client.join_room(room_id)
                    print(f"Joining room: {room_id}")
                elif command.startswith("leave "):
                    room_id = command.split(" ", 1)[1]
                    await self.client.leave_room(room_id)
                    print(f"Leaving room: {room_id}")
                else:
                    print(f"Unknown command: {command}")
                    
            except Exception as e:
                print(f"Error: {e}")
        
        # Disconnect
        await self.client.disconnect()
        connect_task.cancel()


async def main():
    """Run test client"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python client.py <api_url> <jwt_token>")
        print("Example: python client.py http://localhost:8000 your_jwt_token")
        sys.exit(1)
    
    base_url = sys.argv[1]
    token = sys.argv[2]
    
    client = WebSocketTestClient(base_url, token)
    await client.run_interactive()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())