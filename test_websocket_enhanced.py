#!/usr/bin/env python3
"""
Test script for WebSocket functionality with JWT authentication
"""

import asyncio
import websockets
import json
import httpx
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/api/v1/ws"


async def get_test_token():
    """Get a test JWT token by logging in"""
    async with httpx.AsyncClient() as client:
        # Register test user
        register_data = {
            "email": f"wstest_{int(datetime.now().timestamp())}@example.com",
            "username": f"wstest_{int(datetime.now().timestamp())}",
            "password": "testpass123",
            "full_name": "WebSocket Test User"
        }
        
        await client.post(f"{BASE_URL}/api/auth/register", json=register_data)
        
        # Login to get token
        login_data = {
            "username_or_email": register_data["username"],
            "password": register_data["password"]
        }
        
        response = await client.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()['data']['access_token']
        else:
            raise Exception(f"Failed to get token: {response.text}")


async def test_websocket_connection():
    """Test WebSocket connection and features"""
    print("=== WebSocket Connection Test ===\n")
    
    # Get authentication token
    print("1. Getting authentication token...")
    try:
        token = await get_test_token()
        print(f"✅ Got token: {token[:20]}...")
    except Exception as e:
        print(f"❌ Failed to get token: {e}")
        return
    
    # Connect to WebSocket
    print("\n2. Connecting to WebSocket...")
    uri = f"{WS_URL}?token={token}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            
            # Handle incoming messages
            async def receive_messages():
                try:
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        print(f"\n📨 Received: {data['type']}")
                        print(f"   Data: {json.dumps(data['data'], indent=2)}")
                        
                        # Store connection ID if received
                        if data['type'] == 'connection.established':
                            return data['data'].get('connection_id')
                            
                except websockets.exceptions.ConnectionClosed:
                    print("\n❌ WebSocket connection closed")
                except Exception as e:
                    print(f"\n❌ Error receiving message: {e}")
            
            # Start message receiver
            receive_task = asyncio.create_task(receive_messages())
            
            # Wait for connection established message
            await asyncio.sleep(1)
            connection_id = await receive_task
            print(f"\n   Connection ID: {connection_id}")
            
            # Start new receiver for remaining tests
            receive_task = asyncio.create_task(receive_messages())
            
            # Test ping/pong
            print("\n3. Testing ping/pong...")
            ping_msg = {"type": "ping", "data": {}}
            await websocket.send(json.dumps(ping_msg))
            print("📤 Sent: ping")
            await asyncio.sleep(1)
            
            # Test joining a room
            print("\n4. Testing room join...")
            room_id = "transcript:123"
            join_msg = {
                "type": "room.join",
                "data": {"room_id": room_id}
            }
            await websocket.send(json.dumps(join_msg))
            print(f"📤 Sent: room.join (room: {room_id})")
            await asyncio.sleep(1)
            
            # Test sending a transcript update
            print("\n5. Testing transcript update...")
            update_msg = {
                "type": "transcript.updated",
                "data": {
                    "transcript_id": 123,
                    "changes": {
                        "text": "Updated transcript text",
                        "word_count": 150
                    }
                }
            }
            await websocket.send(json.dumps(update_msg))
            print("📤 Sent: transcript.updated")
            await asyncio.sleep(1)
            
            # Test typing indicator
            print("\n6. Testing typing indicator...")
            typing_msg = {
                "type": "user.typing",
                "data": {"transcript_id": 123}
            }
            await websocket.send(json.dumps(typing_msg))
            print("📤 Sent: user.typing")
            await asyncio.sleep(1)
            
            # Test annotation
            print("\n7. Testing annotation...")
            annotation_msg = {
                "type": "annotation.added",
                "data": {
                    "transcript_id": 123,
                    "start_pos": 10,
                    "end_pos": 20,
                    "text": "Test annotation",
                    "type": "note"
                }
            }
            await websocket.send(json.dumps(annotation_msg))
            print("📤 Sent: annotation.added")
            await asyncio.sleep(1)
            
            # Test leaving room
            print("\n8. Testing room leave...")
            leave_msg = {
                "type": "room.leave",
                "data": {"room_id": room_id}
            }
            await websocket.send(json.dumps(leave_msg))
            print(f"📤 Sent: room.leave (room: {room_id})")
            await asyncio.sleep(1)
            
            # Test invalid message
            print("\n9. Testing error handling...")
            invalid_msg = {
                "type": "invalid.type",
                "data": {}
            }
            await websocket.send(json.dumps(invalid_msg))
            print("📤 Sent: invalid message")
            await asyncio.sleep(1)
            
            # Cancel receiver
            receive_task.cancel()
            
            print("\n✅ All tests completed")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def test_multiple_connections():
    """Test multiple concurrent WebSocket connections"""
    print("\n\n=== Multiple Connection Test ===\n")
    
    # Get tokens for multiple users
    print("1. Creating multiple users...")
    tokens = []
    for i in range(3):
        try:
            token = await get_test_token()
            tokens.append(token)
            print(f"✅ User {i+1} token obtained")
        except Exception as e:
            print(f"❌ Failed to create user {i+1}: {e}")
            return
    
    # Connect multiple clients
    print("\n2. Connecting multiple clients...")
    connections = []
    
    async def client_handler(client_id: int, token: str):
        """Handle a single client connection"""
        uri = f"{WS_URL}?token={token}"
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ Client {client_id} connected")
                
                # Join a shared room
                room_id = "transcript:shared"
                join_msg = {
                    "type": "room.join",
                    "data": {"room_id": room_id}
                }
                await websocket.send(json.dumps(join_msg))
                
                # Send a message
                msg = {
                    "type": "annotation.added",
                    "data": {
                        "transcript_id": "shared",
                        "text": f"Message from client {client_id}",
                        "start_pos": 0,
                        "end_pos": 10
                    }
                }
                await websocket.send(json.dumps(msg))
                print(f"📤 Client {client_id} sent annotation")
                
                # Receive messages
                for _ in range(5):
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(message)
                        print(f"📨 Client {client_id} received: {data['type']}")
                    except asyncio.TimeoutError:
                        break
                    except Exception:
                        break
                        
        except Exception as e:
            print(f"❌ Client {client_id} error: {e}")
    
    # Run all clients concurrently
    tasks = [
        client_handler(i+1, token)
        for i, token in enumerate(tokens)
    ]
    
    await asyncio.gather(*tasks)
    print("\n✅ Multiple connection test completed")


async def test_websocket_metrics():
    """Test WebSocket metrics endpoint"""
    print("\n\n=== WebSocket Metrics Test ===\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/v1/ws/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print("✅ WebSocket Metrics:")
            print(json.dumps(metrics, indent=2))
        else:
            print(f"❌ Failed to get metrics: {response.status_code}")


async def main():
    """Run all WebSocket tests"""
    print("Starting WebSocket tests...")
    print(f"API URL: {BASE_URL}")
    print(f"WebSocket URL: {WS_URL}")
    print("Make sure the API server is running with WebSocket support\n")
    
    try:
        # Basic connection test
        await test_websocket_connection()
        
        # Multiple connections test
        await test_multiple_connections()
        
        # Metrics test
        await test_websocket_metrics()
        
        print("\n=== All tests completed ===")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())