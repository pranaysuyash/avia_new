#!/usr/bin/env python3
"""
Simple test to verify WebSocket functionality
"""

import asyncio
import json
import logging
from websocket import WebSocketManager, EventType, Event, EventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_server():
    """Test basic WebSocket server functionality"""
    print("🔌 Testing WebSocket Functionality")
    print("=" * 50)
    
    try:
        # Create WebSocket manager
        print("\n1. Testing WebSocket manager creation...")
        manager = WebSocketManager()
        print(f"✅ WebSocket manager created successfully")
        
        # Test event creation
        print("\n2. Testing event system...")
        test_event = Event(
            type=EventType.MESSAGE,
            data={"message": "Hello WebSocket!"},
            room_id="test_room",
            user_id="test_user"
        )
        print(f"✅ Event created: {test_event.type}")
        
        # Test event handler
        print("\n3. Testing event handler...")
        
        class TestEventHandler(EventHandler):
            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.MESSAGE
            
            async def handle(self, event: Event) -> dict:
                logger.info(f"Handling event: {event.data}")
                return {"status": "success", "echo": event.data}
        
        handler = TestEventHandler()
        
        if handler.can_handle(test_event):
            result = await handler.handle(test_event)
            print(f"✅ Event handled successfully: {result}")
        
        print("\n4. Testing WebSocket event types...")
        for event_type in EventType:
            print(f"   - {event_type.value}")
        
        print("\n✅ WebSocket functionality test completed!")
        
    except ImportError as e:
        print(f"⚠️ WebSocket server not available: {e}")
        print("WebSocket functionality requires additional dependencies")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_websocket_server())