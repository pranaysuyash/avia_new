#!/usr/bin/env python3
"""
Test Suite for Real-time Collaborative Transcription System
"""

import unittest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from realtime_collaborative_transcription import (
    CollaborativeTranscriptionEngine, AudioStreamProcessor, WebSocketTranscriptionServer,
    TranscriptionSegment, CollaborativeEdit, UserSession, TranscriptionSession
)

class TestAudioStreamProcessor(unittest.TestCase):
    """Test audio stream processing functionality"""
    
    def setUp(self):
        self.processor = AudioStreamProcessor()
    
    def test_processor_initialization(self):
        """Test processor initializes correctly"""
        self.assertEqual(self.processor.sample_rate, 16000)
        self.assertEqual(self.processor.chunk_size, 1024)
        self.assertFalse(self.processor.is_recording)
        self.assertIsNone(self.processor.audio_thread)
    
    def test_audio_chunk_processing(self):
        """Test audio chunk processing"""
        # Test with sufficient audio data
        audio_data = b"mock_audio_data" * 100  # Make it long enough
        result = self.processor.process_audio_chunk(audio_data)
        
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
        # Test with insufficient audio data
        short_audio = b"short"
        result_short = self.processor.process_audio_chunk(short_audio)
        self.assertIsNone(result_short)
    
    def test_recording_state_management(self):
        """Test recording state management"""
        self.assertFalse(self.processor.is_recording)
        
        # Mock callback
        callback = Mock()
        
        # Start recording (will fail without actual audio device, but state should change)
        try:
            self.processor.start_recording(callback)
            # Give it a moment to start
            time.sleep(0.1)
            self.assertTrue(self.processor.is_recording)
        except Exception:
            # Expected to fail in test environment without audio device
            pass
        
        # Stop recording
        self.processor.stop_recording()
        self.assertFalse(self.processor.is_recording)

class TestCollaborativeTranscriptionEngine(unittest.TestCase):
    """Test the collaborative transcription engine"""
    
    def setUp(self):
        self.engine = CollaborativeTranscriptionEngine()
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine.sessions, dict)
        self.assertIsInstance(self.engine.user_sessions, dict)
        self.assertIsInstance(self.engine.websocket_connections, dict)
        self.assertEqual(self.engine.max_users_per_session, 10)
        self.assertEqual(self.engine.edit_conflict_resolution, "last_writer_wins")
    
    def test_session_creation(self):
        """Test creating transcription sessions"""
        session_id = self.engine.create_session(
            title="Test Session",
            created_by="test_user",
            settings={"language": "en"}
        )
        
        self.assertIsInstance(session_id, str)
        self.assertIn(session_id, self.engine.sessions)
        
        session = self.engine.sessions[session_id]
        self.assertEqual(session.title, "Test Session")
        self.assertEqual(session.created_by, "test_user")
        self.assertTrue(session.is_active)
        self.assertEqual(len(session.users), 0)
        self.assertEqual(len(session.segments), 0)
    
    def test_user_session_joining(self):
        """Test users joining sessions"""
        # Create session
        session_id = self.engine.create_session("Test Session", "owner")
        
        # Mock websocket
        mock_websocket = Mock()
        
        # Join session
        success = self.engine.join_session(
            session_id=session_id,
            user_id="user1",
            username="Alice",
            websocket=mock_websocket,
            role="transcriber"
        )
        
        self.assertTrue(success)
        
        session = self.engine.sessions[session_id]
        self.assertIn("user1", session.users)
        
        user_session = session.users["user1"]
        self.assertEqual(user_session.username, "Alice")
        self.assertEqual(user_session.role, "transcriber")
        self.assertIn("transcribe", user_session.permissions)
        self.assertIn("edit", user_session.permissions)
    
    def test_user_permissions(self):
        """Test user permission assignment"""
        session_id = self.engine.create_session("Test Session", "owner")
        mock_websocket = Mock()
        
        # Test different roles and their permissions
        roles_permissions = [
            ("owner", {"transcribe", "edit", "moderate", "manage"}),
            ("moderator", {"transcribe", "edit", "moderate"}),
            ("transcriber", {"transcribe", "edit"}),
            ("editor", {"edit"}),
            ("viewer", {"view"})
        ]
        
        for i, (role, expected_permissions) in enumerate(roles_permissions):
            user_id = f"user{i}"
            self.engine.join_session(session_id, user_id, f"User{i}", mock_websocket, role)
            
            session = self.engine.sessions[session_id]
            user_session = session.users[user_id]
            self.assertEqual(user_session.permissions, expected_permissions)
    
    def test_user_session_leaving(self):
        """Test users leaving sessions"""
        session_id = self.engine.create_session("Test Session", "owner")
        mock_websocket = Mock()
        
        # Join session
        self.engine.join_session(session_id, "user1", "Alice", mock_websocket, "transcriber")
        
        # Verify user is in session
        session = self.engine.sessions[session_id]
        self.assertIn("user1", session.users)
        
        # Leave session
        self.engine.leave_session(session_id, "user1")
        
        # Verify user is removed
        self.assertNotIn("user1", session.users)
        self.assertNotIn("user1", self.engine.user_sessions)
    
    def test_session_state_retrieval(self):
        """Test getting session state"""
        session_id = self.engine.create_session("Test Session", "owner")
        mock_websocket = Mock()
        
        # Add users
        self.engine.join_session(session_id, "user1", "Alice", mock_websocket, "moderator")
        self.engine.join_session(session_id, "user2", "Bob", mock_websocket, "transcriber")
        
        # Get session state
        state = self.engine.get_session_state(session_id)
        
        self.assertIsInstance(state, dict)
        self.assertEqual(state["session_id"], session_id)
        self.assertEqual(state["title"], "Test Session")
        self.assertEqual(len(state["users"]), 2)
        self.assertEqual(state["total_segments"], 0)
        
        # Test non-existent session
        invalid_state = self.engine.get_session_state("invalid_id")
        self.assertIsNone(invalid_state)

class TestAsyncFunctionality(unittest.TestCase):
    """Test async functionality of the transcription engine"""
    
    def setUp(self):
        self.engine = CollaborativeTranscriptionEngine()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_audio_stream_processing(self):
        """Test async audio stream processing"""
        async def run_test():
            # Create session and add user
            session_id = self.engine.create_session("Test Session", "owner")
            mock_websocket = AsyncMock()
            
            self.engine.join_session(session_id, "user1", "Alice", mock_websocket, "transcriber")
            
            # Process audio stream
            audio_data = b"mock_audio_data" * 100
            await self.engine.process_audio_stream(session_id, "user1", audio_data)
            
            # Check if segment was created
            session = self.engine.sessions[session_id]
            self.assertGreater(len(session.segments), 0)
            
            segment = session.segments[0]
            self.assertEqual(segment.speaker_id, "user1")
            self.assertEqual(segment.user_id, "user1")
            self.assertFalse(segment.is_final)
        
        self.loop.run_until_complete(run_test())
    
    def test_collaborative_editing(self):
        """Test collaborative editing functionality"""
        async def run_test():
            # Create session and add users
            session_id = self.engine.create_session("Test Session", "owner")
            mock_websocket = AsyncMock()
            
            self.engine.join_session(session_id, "user1", "Alice", mock_websocket, "editor")
            
            # Add a segment first
            session = self.engine.sessions[session_id]
            segment = TranscriptionSegment(
                id="segment1",
                text="Original text",
                start_time=0.0,
                end_time=2.0,
                confidence=0.9,
                speaker_id="user1",
                is_final=False,
                timestamp=datetime.now(),
                user_id="user1"
            )
            session.segments.append(segment)
            
            # Apply edit
            edit_data = {
                "segment_id": "segment1",
                "edit_type": "replace",
                "original_text": "Original text",
                "new_text": "Edited text",
                "position": 0
            }
            
            success = await self.engine.apply_edit(session_id, "user1", edit_data)
            self.assertTrue(success)
            
            # Check if edit was applied
            updated_segment = session.segments[0]
            self.assertEqual(updated_segment.text, "Edited text")
            
            # Check if edit was recorded
            self.assertGreater(len(session.edits), 0)
            edit = session.edits[0]
            self.assertEqual(edit.segment_id, "segment1")
            self.assertEqual(edit.user_id, "user1")
            self.assertTrue(edit.applied)
        
        self.loop.run_until_complete(run_test())
    
    def test_edit_permissions(self):
        """Test edit permissions enforcement"""
        async def run_test():
            # Create session and add viewer (no edit permissions)
            session_id = self.engine.create_session("Test Session", "owner")
            mock_websocket = AsyncMock()
            
            self.engine.join_session(session_id, "user1", "Viewer", mock_websocket, "viewer")
            
            # Add a segment
            session = self.engine.sessions[session_id]
            segment = TranscriptionSegment(
                id="segment1",
                text="Original text",
                start_time=0.0,
                end_time=2.0,
                confidence=0.9,
                speaker_id="user1",
                is_final=False,
                timestamp=datetime.now(),
                user_id="user1"
            )
            session.segments.append(segment)
            
            # Try to apply edit (should fail due to permissions)
            edit_data = {
                "segment_id": "segment1",
                "edit_type": "replace",
                "original_text": "Original text",
                "new_text": "Edited text",
                "position": 0
            }
            
            success = await self.engine.apply_edit(session_id, "user1", edit_data)
            self.assertFalse(success)
            
            # Verify text wasn't changed
            unchanged_segment = session.segments[0]
            self.assertEqual(unchanged_segment.text, "Original text")
        
        self.loop.run_until_complete(run_test())

class TestWebSocketServer(unittest.TestCase):
    """Test WebSocket server functionality"""
    
    def setUp(self):
        self.server = WebSocketTranscriptionServer()
    
    def test_server_initialization(self):
        """Test server initializes correctly"""
        self.assertEqual(self.server.host, "localhost")
        self.assertEqual(self.server.port, 8765)
        self.assertIsInstance(self.server.engine, CollaborativeTranscriptionEngine)
    
    def test_message_processing(self):
        """Test WebSocket message processing"""
        async def run_test():
            mock_websocket = AsyncMock()
            client_id = "test_client"
            
            # Test session creation message
            create_message = {
                "type": "create_session",
                "title": "Test Session",
                "user_id": "test_user"
            }
            
            await self.server.process_message(mock_websocket, client_id, create_message)
            
            # Verify websocket.send was called
            mock_websocket.send.assert_called()
            
            # Get the sent message
            sent_message = mock_websocket.send.call_args[0][0]
            response = json.loads(sent_message)
            
            self.assertEqual(response["type"], "session_created")
            self.assertIn("session_id", response)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()
    
    def test_error_handling(self):
        """Test error message handling"""
        async def run_test():
            mock_websocket = AsyncMock()
            
            await self.server.send_error(mock_websocket, "Test error message")
            
            # Verify error message was sent
            mock_websocket.send.assert_called()
            sent_message = mock_websocket.send.call_args[0][0]
            response = json.loads(sent_message)
            
            self.assertEqual(response["type"], "error")
            self.assertEqual(response["message"], "Test error message")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_test())
        finally:
            loop.close()

class TestDataStructures(unittest.TestCase):
    """Test data structure functionality"""
    
    def test_transcription_segment(self):
        """Test TranscriptionSegment data structure"""
        segment = TranscriptionSegment(
            id="test_id",
            text="Test transcription",
            start_time=0.0,
            end_time=2.5,
            confidence=0.95,
            speaker_id="speaker1",
            is_final=True,
            timestamp=datetime.now(),
            user_id="user1"
        )
        
        self.assertEqual(segment.id, "test_id")
        self.assertEqual(segment.text, "Test transcription")
        self.assertEqual(segment.confidence, 0.95)
        self.assertTrue(segment.is_final)
    
    def test_collaborative_edit(self):
        """Test CollaborativeEdit data structure"""
        edit = CollaborativeEdit(
            edit_id="edit_id",
            segment_id="segment_id",
            user_id="user1",
            edit_type="replace",
            original_text="Original",
            new_text="Modified",
            position=0,
            timestamp=datetime.now(),
            applied=True
        )
        
        self.assertEqual(edit.edit_type, "replace")
        self.assertEqual(edit.original_text, "Original")
        self.assertEqual(edit.new_text, "Modified")
        self.assertTrue(edit.applied)
    
    def test_user_session(self):
        """Test UserSession data structure"""
        mock_websocket = Mock()
        permissions = {"transcribe", "edit"}
        
        user_session = UserSession(
            user_id="user1",
            username="Alice",
            websocket=mock_websocket,
            role="transcriber",
            permissions=permissions,
            last_activity=datetime.now(),
            is_active=True
        )
        
        self.assertEqual(user_session.username, "Alice")
        self.assertEqual(user_session.role, "transcriber")
        self.assertEqual(user_session.permissions, permissions)
        self.assertTrue(user_session.is_active)

class TestIntegrationScenarios(unittest.TestCase):
    """Test real-world integration scenarios"""
    
    def setUp(self):
        self.engine = CollaborativeTranscriptionEngine()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def test_multi_user_collaboration_scenario(self):
        """Test multi-user collaboration scenario"""
        async def run_test():
            # Create session
            session_id = self.engine.create_session("Team Meeting", "moderator")
            
            # Add multiple users with different roles
            users = [
                ("mod1", "Moderator Alice", "moderator"),
                ("trans1", "Transcriber Bob", "transcriber"),
                ("edit1", "Editor Charlie", "editor"),
                ("view1", "Viewer Dave", "viewer")
            ]
            
            mock_websockets = {}
            for user_id, username, role in users:
                mock_websockets[user_id] = AsyncMock()
                success = self.engine.join_session(
                    session_id, user_id, username, mock_websockets[user_id], role
                )
                self.assertTrue(success)
            
            # Simulate transcription by transcriber
            audio_data = b"meeting_audio_data" * 100
            await self.engine.process_audio_stream(session_id, "trans1", audio_data)
            
            # Verify segment was created
            session = self.engine.sessions[session_id]
            self.assertEqual(len(session.segments), 1)
            
            # Simulate editing by editor
            segment = session.segments[0]
            edit_data = {
                "segment_id": segment.id,
                "edit_type": "replace",
                "original_text": segment.text,
                "new_text": segment.text + " [Corrected]",
                "position": 0
            }
            
            edit_success = await self.engine.apply_edit(session_id, "edit1", edit_data)
            self.assertTrue(edit_success)
            
            # Verify edit was applied
            self.assertIn("[Corrected]", session.segments[0].text)
            
            # Try editing as viewer (should fail)
            viewer_edit_success = await self.engine.apply_edit(session_id, "view1", edit_data)
            self.assertFalse(viewer_edit_success)
            
            # Get final session state
            final_state = self.engine.get_session_state(session_id)
            self.assertEqual(len(final_state["users"]), 4)
            self.assertEqual(final_state["total_segments"], 1)
        
        self.loop.run_until_complete(run_test())
    
    def test_session_export_scenario(self):
        """Test session export functionality"""
        # Create session with data
        session_id = self.engine.create_session("Export Test", "user1")
        mock_websocket = Mock()
        
        self.engine.join_session(session_id, "user1", "Alice", mock_websocket, "transcriber")
        
        # Add some segments
        session = self.engine.sessions[session_id]
        segments = [
            TranscriptionSegment(
                id=f"seg{i}",
                text=f"Segment {i} text",
                start_time=i * 2.0,
                end_time=(i + 1) * 2.0,
                confidence=0.9,
                speaker_id="user1",
                is_final=True,
                timestamp=datetime.now(),
                user_id="user1"
            )
            for i in range(3)
        ]
        session.segments.extend(segments)
        
        # Test JSON export
        json_export = self.engine.export_session(session_id, "json")
        self.assertIsInstance(json_export, str)
        
        # Verify JSON is valid
        parsed_json = json.loads(json_export)
        self.assertEqual(parsed_json["session_id"], session_id)
        self.assertEqual(len(parsed_json["segments"]), 3)
        
        # Test text export
        text_export = self.engine.export_session(session_id, "text")
        self.assertIsInstance(text_export, str)
        self.assertIn("Segment 0 text", text_export)
        self.assertIn("Segment 1 text", text_export)
        self.assertIn("Segment 2 text", text_export)

if __name__ == "__main__":
    unittest.main(verbosity=2)