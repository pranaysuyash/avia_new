#!/usr/bin/env python3
"""
Test script to demonstrate WebSocket functionality
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketTester:
    """Test WebSocket functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        self.token = None
        self.session = None
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession()
        
        # Login to get token
        login_data = {
            "email": "test@example.com",
            "password": "password"
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=login_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.token = data["access_token"]
                logger.info("Login successful")
            else:
                logger.error(f"Login failed: {await resp.text()}")
                raise Exception("Failed to login")
    
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
    
    async def test_websocket_connection(self):
        """Test basic WebSocket connection"""
        logger.info("\n📋 Test 1: WebSocket Connection")
        
        ws_url = f"{self.ws_url}/api/v1/ws?token={self.token}"
        
        async with self.session.ws_connect(ws_url) as ws:
            logger.info("✅ Connected to WebSocket")
            
            # Wait for connection established message
            msg = await ws.receive()
            data = json.loads(msg.data)
            logger.info(f"Received: {data['type']} - {data['data']['message']}")
            
            # Test ping/pong
            await ws.send_json({"type": "ping", "data": {}})
            logger.info("Sent: ping")
            
            msg = await ws.receive()
            data = json.loads(msg.data)
            logger.info(f"Received: {data['type']} - timestamp: {data['data']['timestamp']}")
            
            await ws.close()
            logger.info("✅ Connection test passed")
    
    async def test_room_functionality(self):
        """Test room join/leave"""
        logger.info("\n📋 Test 2: Room Functionality")
        
        ws_url = f"{self.ws_url}/api/v1/ws?token={self.token}"
        
        async with self.session.ws_connect(ws_url) as ws:
            # Skip connection message
            await ws.receive()
            
            # Join room
            room_id = "transcript_123"
            await ws.send_json({
                "type": "room.join",
                "data": {"room_id": room_id}
            })
            logger.info(f"Sent: join room {room_id}")
            
            # Simulate another user joining (would need second connection)
            logger.info("Note: Room events would be received from other users")
            
            # Leave room
            await ws.send_json({
                "type": "room.leave",
                "data": {"room_id": room_id}
            })
            logger.info(f"Sent: leave room {room_id}")
            
            await ws.close()
            logger.info("✅ Room test completed")
    
    async def test_concurrent_connections(self):
        """Test multiple concurrent connections"""
        logger.info("\n📋 Test 3: Concurrent Connections")
        
        ws_url = f"{self.ws_url}/api/v1/ws?token={self.token}"
        
        # Create multiple connections
        connections = []
        for i in range(3):
            ws = await self.session.ws_connect(ws_url)
            connections.append(ws)
            logger.info(f"✅ Connection {i+1} established")
        
        # Test broadcasting
        room_id = "test_room"
        
        # All join same room
        for i, ws in enumerate(connections):
            await ws.send_json({
                "type": "room.join",
                "data": {"room_id": room_id}
            })
        
        logger.info(f"All connections joined room: {room_id}")
        
        # Close connections
        for ws in connections:
            await ws.close()
        
        logger.info("✅ Concurrent connections test passed")
    
    async def simulate_real_usage(self):
        """Simulate real application usage"""
        logger.info("\n📋 Test 4: Real Usage Simulation")
        
        ws_url = f"{self.ws_url}/api/v1/ws?token={self.token}"
        
        async with self.session.ws_connect(ws_url) as ws:
            # Skip connection message
            await ws.receive()
            
            # Join transcript room
            transcript_id = 123
            await ws.send_json({
                "type": "room.join",
                "data": {"room_id": f"transcript_{transcript_id}"}
            })
            logger.info(f"Joined transcript room: transcript_{transcript_id}")
            
            # Simulate events that would come from other users/system
            logger.info("\nSimulated events that would be received:")
            
            # Transcript update
            logger.info("- transcript.updated: Title changed to 'Updated Meeting Notes'")
            
            # Annotation added
            logger.info("- annotation.added: User 2 added note at position 100-150")
            
            # Processing progress
            logger.info("- processing.progress: Job abc123 at 50% complete")
            
            # Notification
            logger.info("- notification.new: 'John shared a transcript with you'")
            
            # Keep connection alive for a bit
            await asyncio.sleep(2)
            
            await ws.close()
            logger.info("\n✅ Real usage simulation completed")
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        try:
            await self.setup()
            
            await self.test_websocket_connection()
            await self.test_room_functionality()
            await self.test_concurrent_connections()
            await self.simulate_real_usage()
            
            logger.info("\n✅ All WebSocket tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
        finally:
            await self.cleanup()


def print_usage_examples():
    """Print usage examples"""
    print("\n📚 WebSocket Usage Examples")
    print("=" * 50)
    
    print("\n1. JavaScript/Browser Client:")
    print("""
    const token = 'your_jwt_token';
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);
    
    ws.onopen = () => {
        console.log('Connected');
        
        // Join a transcript room
        ws.send(JSON.stringify({
            type: 'room.join',
            data: { room_id: 'transcript_123' }
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data.type, data.data);
        
        // Handle different event types
        switch(data.type) {
            case 'transcript.updated':
                updateTranscriptUI(data.data);
                break;
            case 'annotation.added':
                addAnnotationToUI(data.data);
                break;
            // ... handle other events
        }
    };
    """)
    
    print("\n2. Python Client:")
    print("""
    from websocket.client import WebSocketClient
    
    client = WebSocketClient('ws://localhost:8000/api/v1/ws', token)
    
    # Register handlers
    client.on('transcript.updated', handle_transcript_update)
    client.on('notification.new', handle_notification)
    
    # Connect and join room
    await client.connect()
    await client.join_room('transcript_123')
    """)
    
    print("\n3. Integration in API Endpoints:")
    print("""
    from websocket.integration import WebSocketIntegration
    
    # In your API endpoint
    @router.put("/transcripts/{id}")
    async def update_transcript(id: int, ...):
        # Update transcript
        
        # Notify via WebSocket
        await WebSocketIntegration.notify_transcript_update(
            transcript_id=id,
            user_id=current_user.id,
            changes={'title': new_title}
        )
    """)


async def main():
    """Run WebSocket tests"""
    print("🚀 WebSocket Testing Suite")
    print("=" * 50)
    
    # Check if API is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/api/v1/health") as resp:
                if resp.status != 200:
                    print("❌ API is not running. Start it with: python run_api.py")
                    return
    except:
        print("❌ Cannot connect to API. Make sure it's running on http://localhost:8000")
        return
    
    # Run tests
    tester = WebSocketTester()
    await tester.run_all_tests()
    
    # Print usage examples
    print_usage_examples()


if __name__ == "__main__":
    asyncio.run(main())