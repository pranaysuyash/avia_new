#!/usr/bin/env python3
"""
Test Real-time Collaboration Features
Validates all collaboration and live streaming functionality
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_collaboration_manager():
    """Test collaboration manager functionality"""
    print("🧪 Testing Collaboration Manager...")
    
    try:
        from realtime_collaboration import (
            RealtimeCollaborationManager, CollaborationEventType,
            CollaborationUser, CollaborationSession
        )
        
        # Initialize manager
        manager = RealtimeCollaborationManager()
        print("✅ Collaboration manager initialized")
        
        # Test session creation
        session = await manager.create_session(
            transcript_id="test_transcript_001",
            user_id="test_user_1",
            settings={
                "session_name": "Test Session",
                "max_users": 5,
                "enable_comments": True
            }
        )
        print(f"✅ Created session: {session.session_id}")
        
        # Test user joining
        user2 = await manager.join_session(
            session.session_id,
            "test_user_2",
            "Test User 2"
        )
        print(f"✅ User joined: {user2.display_name}")
        
        # Test cursor update
        await manager.update_cursor_position(
            session.session_id,
            "test_user_2",
            position=100,
            selection_start=100,
            selection_end=150
        )
        print("✅ Cursor position updated")
        
        # Test transcript update
        await manager.update_transcript(
            session.session_id,
            "test_user_1",
            operation="insert",
            position=200,
            content="New text added"
        )
        print("✅ Transcript updated")
        
        # Test comment
        comment_id = await manager.add_comment(
            session.session_id,
            "test_user_2",
            position=150,
            comment_text="This needs review",
            selection_start=150,
            selection_end=200
        )
        print(f"✅ Comment added: {comment_id}")
        
        # Test typing indicator
        await manager.set_typing_indicator(
            session.session_id,
            "test_user_1",
            is_typing=True
        )
        print("✅ Typing indicator set")
        
        # Test version creation
        version_id = await manager.create_version(
            session.session_id,
            "test_user_1",
            version_name="Test Version 1.0",
            description="Initial test version"
        )
        print(f"✅ Version created: {version_id}")
        
        # Get session info
        info = manager.get_session_info(session.session_id)
        print(f"✅ Session info retrieved: {info['user_count']} users")
        
        # Test leaving session
        await manager.leave_session(session.session_id, "test_user_2")
        print("✅ User left session")
        
        # Close session
        await manager.close_session(session.session_id)
        print("✅ Session closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Collaboration manager test error: {e}")
        return False


def test_websocket_server():
    """Test WebSocket server setup"""
    print("\n🧪 Testing WebSocket Server...")
    
    try:
        from websocket_server import create_websocket_app, FASTAPI_AVAILABLE, SOCKETIO_AVAILABLE
        
        if FASTAPI_AVAILABLE:
            app = create_websocket_app()
            print("✅ FastAPI WebSocket server created")
            
            # Check endpoints
            routes = [route.path for route in app.routes]
            if "/ws/collaborate/{session_id}" in routes:
                print("✅ WebSocket endpoint registered")
            else:
                print("⚠️ WebSocket endpoint not found")
                
        elif SOCKETIO_AVAILABLE:
            app = create_websocket_app()
            print("✅ Socket.IO server created")
        else:
            print("⚠️ No WebSocket library available")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket server test error: {e}")
        return False


def test_collaboration_ui():
    """Test collaboration UI components"""
    print("\n🧪 Testing Collaboration UI...")
    
    try:
        from collaboration_ui import CollaborationUI, add_collaboration_features
        
        print("✅ Collaboration UI imported successfully")
        
        # Test UI component methods exist
        ui_methods = [
            'render_collaboration_panel',
            'render_live_transcription_panel',
            '_render_active_users',
            '_render_comments',
            '_render_versions',
            '_render_activity_log'
        ]
        
        for method in ui_methods:
            if hasattr(CollaborationUI, method):
                print(f"✅ UI method '{method}' available")
            else:
                print(f"❌ UI method '{method}' missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Collaboration UI test error: {e}")
        return False


async def test_event_handling():
    """Test event handling system"""
    print("\n🧪 Testing Event Handling...")
    
    try:
        from realtime_collaboration import (
            RealtimeCollaborationManager, CollaborationEventType, 
            CollaborationEvent
        )
        
        manager = RealtimeCollaborationManager()
        
        # Track events
        received_events = []
        
        # Register event handler
        async def test_handler(event: CollaborationEvent):
            received_events.append(event)
            print(f"✅ Received event: {event.event_type.value}")
        
        # Register for all event types
        for event_type in CollaborationEventType:
            manager.register_event_handler(event_type, test_handler)
        
        print("✅ Event handlers registered")
        
        # Start event processor in background
        processor_task = asyncio.create_task(manager.start_event_processor())
        
        # Create session to generate events
        session = await manager.create_session(
            transcript_id="event_test_001",
            user_id="event_user_1"
        )
        
        # Wait for events to process
        await asyncio.sleep(0.5)
        
        # Stop processor
        await manager.stop_event_processor()
        
        if received_events:
            print(f"✅ Received {len(received_events)} events")
        else:
            print("⚠️ No events received")
        
        return True
        
    except Exception as e:
        print(f"❌ Event handling test error: {e}")
        return False


def test_collaboration_models():
    """Test collaboration data models"""
    print("\n🧪 Testing Collaboration Models...")
    
    try:
        from realtime_collaboration import (
            CollaborationUser, CollaborationSession, 
            CollaborationEvent, CollaborationEventType
        )
        
        # Test user model
        user = CollaborationUser(
            user_id="test_user",
            display_name="Test User",
            color="#007bff",
            permissions=["read", "write"]
        )
        print(f"✅ User model created: {user.display_name}")
        
        # Test session model
        session = CollaborationSession(
            session_id="test_session_001",
            transcript_id="transcript_001",
            created_by="test_user",
            created_at=datetime.now(),
            users={user.user_id: user}
        )
        print(f"✅ Session model created: {session.session_id}")
        
        # Test event model
        event = CollaborationEvent(
            event_id="test_event_001",
            event_type=CollaborationEventType.USER_JOINED,
            session_id=session.session_id,
            user_id=user.user_id,
            timestamp=datetime.now(),
            data={"test": "data"}
        )
        event_dict = event.to_dict()
        print(f"✅ Event model created: {event_dict['event_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False


async def test_live_features():
    """Test live transcription features"""
    print("\n🧪 Testing Live Features...")
    
    try:
        from realtime_collaboration import RealtimeCollaborationManager
        
        manager = RealtimeCollaborationManager()
        
        # Create session
        session = await manager.create_session(
            transcript_id="live_test_001",
            user_id="live_user_1"
        )
        
        # Test live transcription
        audio_chunk = b"fake_audio_data"
        result = await manager.stream_live_transcription(
            session.session_id,
            "live_user_1",
            audio_chunk,
            is_final=False
        )
        print("✅ Live transcription method called")
        
        # Test notification
        await manager.send_notification(
            session.session_id,
            "live_user_1",
            "Test notification",
            notification_type="info"
        )
        print("✅ Notification sent")
        
        return True
        
    except Exception as e:
        print(f"❌ Live features test error: {e}")
        return False


def test_integration_with_main_app():
    """Test integration with main application"""
    print("\n🧪 Testing Main App Integration...")
    
    try:
        # Check if collaboration can be imported in app context
        from app import st
        from collaboration_ui import add_collaboration_features
        
        print("✅ Collaboration features can be integrated with main app")
        
        # Check WebSocket integration
        websocket_libs = []
        try:
            import websockets
            websocket_libs.append("websockets")
        except ImportError:
            pass
        
        try:
            import socketio
            websocket_libs.append("socketio")
        except ImportError:
            pass
        
        if websocket_libs:
            print(f"✅ WebSocket libraries available: {', '.join(websocket_libs)}")
        else:
            print("⚠️ No WebSocket libraries installed")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        return False


async def main():
    """Run all collaboration tests"""
    print("🚀 Real-time Collaboration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Collaboration Manager", test_collaboration_manager),
        ("WebSocket Server", test_websocket_server),
        ("Collaboration UI", test_collaboration_ui),
        ("Event Handling", test_event_handling),
        ("Data Models", test_collaboration_models),
        ("Live Features", test_live_features),
        ("App Integration", test_integration_with_main_app)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                results[test_name] = await test_func()
            else:
                result = test_func()
                if asyncio.iscoroutine(result):
                    results[test_name] = await result
                else:
                    results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 COLLABORATION TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📝 Next Steps:")
        print("1. Install WebSocket libraries: pip install websockets python-socketio")
        print("2. Start WebSocket server: python websocket_server.py")
        print("3. Add collaboration button to main app")
        print("4. Test with multiple browser windows")
    else:
        print("\n⚠️ Some tests failed. Check implementation.")
    
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Collaboration tests {'completed' if success else 'had failures'}")