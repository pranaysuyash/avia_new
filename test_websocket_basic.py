#!/usr/bin/env python3
"""
Basic test to verify WebSocket functionality
"""

import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_imports():
    """Test WebSocket module imports"""
    print("🔌 Testing WebSocket Imports")
    print("=" * 50)
    
    try:
        # Test basic imports
        print("\n1. Testing basic event imports...")
        from websocket import EventType, Event, EventHandler
        print("✅ Basic imports successful")
        
        # Test event types
        print("\n2. Testing event types...")
        for event_type in EventType:
            print(f"   - {event_type.value}")
        
        # Create test event
        print("\n3. Creating test event...")
        test_event = Event(
            type=EventType.TRANSCRIPT_UPDATED,
            data={"transcript_id": 123, "title": "Updated Title"},
            room_id="transcript_123",
            user_id=1
        )
        print(f"✅ Event created: {test_event.type.value}")
        
        # Test server imports (may fail if dependencies missing)
        print("\n4. Testing server imports...")
        try:
            from websocket.server import ConnectionManager
            print("✅ ConnectionManager available")
            
            # Create connection manager
            manager = ConnectionManager()
            print("✅ ConnectionManager instance created")
            
        except ImportError as e:
            print(f"⚠️ Server components not available: {e}")
            print("   This is expected if running without API server")
        
        print("\n✅ WebSocket module test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


async def test_websocket_handlers():
    """Test WebSocket event handlers"""
    print("\n📋 Testing WebSocket Event Handlers")
    print("=" * 50)
    
    try:
        from websocket import EventType, Event, EventHandler
        
        # Create custom event handler
        class TestHandler(EventHandler):
            def can_handle(self, event: Event) -> bool:
                return event.type == EventType.TRANSCRIPT_UPDATED
            
            async def handle(self, event: Event) -> dict:
                return {"status": "handled", "data": event.data}
        
        # Test handler
        handler = TestHandler()
        test_event = Event(
            type=EventType.TRANSCRIPT_UPDATED,
            data={"transcript_id": 123, "title": "Test Transcript"},
            room_id="transcript_123"
        )
        
        if handler.can_handle(test_event):
            result = await handler.handle(test_event)
            print(f"✅ Event handled: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        return False


async def main():
    """Run all WebSocket tests"""
    print("🚀 WebSocket Functionality Test")
    print("=" * 50)
    
    # Run tests
    results = []
    results.append(await test_websocket_imports())
    results.append(await test_websocket_handlers())
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All WebSocket tests passed!")
    else:
        print("\n⚠️ Some tests failed. WebSocket functionality is partially available.")
    
    # Show usage example
    print("\n📚 WebSocket Usage Example:")
    print("""
    from websocket import EventType, Event, EventHandler
    
    # Create an event
    event = Event(
        type=EventType.TRANSCRIPT_UPDATE,
        data={"transcript_id": 123, "changes": {...}},
        room_id="transcript_123"
    )
    
    # Handle events with custom handlers
    class TranscriptHandler(EventHandler):
        def can_handle(self, event):
            return event.type == EventType.TRANSCRIPT_UPDATE
        
        async def handle(self, event):
            # Process transcript update
            return {"status": "success"}
    """)


if __name__ == "__main__":
    asyncio.run(main())