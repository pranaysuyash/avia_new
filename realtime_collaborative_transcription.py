#!/usr/bin/env python3
"""
Real-time Collaborative Transcription System
WebSocket-based live transcription with multi-user collaboration features
"""

import os
import json
import asyncio
import logging
import websockets
import threading
import queue
import time
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import uuid
from collections import defaultdict
import pyaudio
import wave
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Individual transcription segment"""
    id: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str]
    is_final: bool
    timestamp: datetime
    user_id: str  # Who contributed this segment

@dataclass
class CollaborativeEdit:
    """Collaborative edit operation"""
    edit_id: str
    segment_id: str
    user_id: str
    edit_type: str  # "insert", "delete", "replace"
    original_text: str
    new_text: str
    position: int
    timestamp: datetime
    applied: bool

@dataclass
class UserSession:
    """User session information"""
    user_id: str
    username: str
    websocket: Any
    role: str  # "transcriber", "editor", "viewer"
    permissions: Set[str]
    last_activity: datetime
    is_active: bool

@dataclass
class TranscriptionSession:
    """Collaborative transcription session"""
    session_id: str
    title: str
    created_by: str
    created_at: datetime
    is_active: bool
    users: Dict[str, UserSession]
    segments: List[TranscriptionSegment]
    edits: List[CollaborativeEdit]
    settings: Dict[str, Any]
    metadata: Dict[str, Any]

class AudioStreamProcessor:
    """Process real-time audio streams"""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_thread = None
        
        # Audio configuration
        self.format = pyaudio.paInt16
        self.channels = 1
        
        logger.info("Audio Stream Processor initialized")
    
    def start_recording(self, callback: Callable[[bytes], None]):
        """Start recording audio and call callback with audio data"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_callback = callback
        
        def record_audio():
            try:
                audio = pyaudio.PyAudio()
                stream = audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size
                )
                
                logger.info("Started audio recording")
                
                while self.is_recording:
                    try:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        if self.audio_callback:
                            self.audio_callback(data)
                    except Exception as e:
                        logger.error(f"Error reading audio: {e}")
                        break
                
                stream.stop_stream()
                stream.close()
                audio.terminate()
                
            except Exception as e:
                logger.error(f"Error in audio recording: {e}")
        
        self.audio_thread = threading.Thread(target=record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
        logger.info("Stopped audio recording")
    
    def process_audio_chunk(self, audio_data: bytes) -> Optional[str]:
        """Process audio chunk and return transcription (mock implementation)"""
        # In a real implementation, this would use Whisper API or similar
        # For demo purposes, we'll simulate transcription
        
        if len(audio_data) < 1000:  # Too short
            return None
        
        # Simulate processing delay
        time.sleep(0.1)
        
        # Mock transcription based on audio data characteristics
        mock_phrases = [
            "Hello everyone, welcome to our meeting.",
            "Let's discuss the quarterly results.",
            "The project is progressing well.",
            "We need to focus on customer feedback.",
            "Thank you for your attention.",
            "Any questions or comments?",
            "Let's move to the next topic.",
            "I think we should consider this option."
        ]
        
        # Use audio data hash to select consistent phrase
        data_hash = hashlib.md5(audio_data[:100]).hexdigest()
        phrase_index = int(data_hash[:2], 16) % len(mock_phrases)
        
        return mock_phrases[phrase_index]

class CollaborativeTranscriptionEngine:
    """Core engine for collaborative transcription"""
    
    def __init__(self):
        self.sessions: Dict[str, TranscriptionSession] = {}
        self.user_sessions: Dict[str, UserSession] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.audio_processor = AudioStreamProcessor()
        
        # Collaboration settings
        self.max_users_per_session = 10
        self.edit_conflict_resolution = "last_writer_wins"  # or "merge", "vote"
        
        logger.info("Collaborative Transcription Engine initialized")
    
    def create_session(self, title: str, created_by: str, settings: Dict[str, Any] = None) -> str:
        """Create a new collaborative transcription session"""
        session_id = str(uuid.uuid4())
        
        session = TranscriptionSession(
            session_id=session_id,
            title=title,
            created_by=created_by,
            created_at=datetime.now(),
            is_active=True,
            users={},
            segments=[],
            edits=[],
            settings=settings or {
                "language": "en",
                "auto_punctuation": True,
                "speaker_diarization": True,
                "real_time_editing": True,
                "edit_permissions": "all"  # "all", "moderators", "owner"
            },
            metadata={}
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created transcription session: {session_id}")
        
        return session_id
    
    def join_session(self, session_id: str, user_id: str, username: str, 
                    websocket: Any, role: str = "transcriber") -> bool:
        """Join a collaborative transcription session"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        if len(session.users) >= self.max_users_per_session:
            return False
        
        # Define permissions based on role
        permissions = set()
        if role == "owner":
            permissions = {"transcribe", "edit", "moderate", "manage"}
        elif role == "moderator":
            permissions = {"transcribe", "edit", "moderate"}
        elif role == "transcriber":
            permissions = {"transcribe", "edit"}
        elif role == "editor":
            permissions = {"edit"}
        else:  # viewer
            permissions = {"view"}
        
        user_session = UserSession(
            user_id=user_id,
            username=username,
            websocket=websocket,
            role=role,
            permissions=permissions,
            last_activity=datetime.now(),
            is_active=True
        )
        
        session.users[user_id] = user_session
        self.user_sessions[user_id] = user_session
        self.websocket_connections[user_id] = websocket
        
        logger.info(f"User {username} joined session {session_id} as {role}")
        
        # Notify other users
        asyncio.create_task(self.broadcast_user_joined(session_id, user_session))
        
        return True
    
    def leave_session(self, session_id: str, user_id: str):
        """Leave a collaborative transcription session"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        
        if user_id in session.users:
            user_session = session.users[user_id]
            user_session.is_active = False
            
            del session.users[user_id]
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            if user_id in self.websocket_connections:
                del self.websocket_connections[user_id]
            
            logger.info(f"User {user_session.username} left session {session_id}")
            
            # Notify other users
            asyncio.create_task(self.broadcast_user_left(session_id, user_session))
            
            # Clean up empty sessions
            if not session.users and not session.is_active:
                del self.sessions[session_id]
    
    async def process_audio_stream(self, session_id: str, user_id: str, audio_data: bytes):
        """Process incoming audio stream for transcription"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        user_session = session.users.get(user_id)
        
        if not user_session or "transcribe" not in user_session.permissions:
            return
        
        # Process audio chunk
        transcription = self.audio_processor.process_audio_chunk(audio_data)
        
        if transcription:
            # Create transcription segment
            segment = TranscriptionSegment(
                id=str(uuid.uuid4()),
                text=transcription,
                start_time=time.time(),
                end_time=time.time() + 2.0,  # Estimated duration
                confidence=0.85,  # Mock confidence
                speaker_id=user_id,
                is_final=False,  # Initially not final
                timestamp=datetime.now(),
                user_id=user_id
            )
            
            session.segments.append(segment)
            
            # Broadcast to all users in session
            await self.broadcast_transcription_update(session_id, segment)
    
    async def apply_edit(self, session_id: str, user_id: str, edit_data: Dict[str, Any]) -> bool:
        """Apply collaborative edit to transcription"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        user_session = session.users.get(user_id)
        
        if not user_session or "edit" not in user_session.permissions:
            return False
        
        # Create edit operation
        edit = CollaborativeEdit(
            edit_id=str(uuid.uuid4()),
            segment_id=edit_data.get("segment_id"),
            user_id=user_id,
            edit_type=edit_data.get("edit_type", "replace"),
            original_text=edit_data.get("original_text", ""),
            new_text=edit_data.get("new_text", ""),
            position=edit_data.get("position", 0),
            timestamp=datetime.now(),
            applied=False
        )
        
        # Apply edit based on conflict resolution strategy
        success = await self.resolve_edit_conflicts(session, edit)
        
        if success:
            session.edits.append(edit)
            await self.broadcast_edit_update(session_id, edit)
        
        return success
    
    async def resolve_edit_conflicts(self, session: TranscriptionSession, edit: CollaborativeEdit) -> bool:
        """Resolve edit conflicts using configured strategy"""
        
        # Find the target segment
        target_segment = None
        for segment in session.segments:
            if segment.id == edit.segment_id:
                target_segment = segment
                break
        
        if not target_segment:
            return False
        
        # Check for concurrent edits
        recent_edits = [
            e for e in session.edits 
            if e.segment_id == edit.segment_id 
            and (datetime.now() - e.timestamp).total_seconds() < 5.0
            and not e.applied
        ]
        
        if self.edit_conflict_resolution == "last_writer_wins":
            # Apply the edit directly
            if edit.edit_type == "replace":
                target_segment.text = edit.new_text
            elif edit.edit_type == "insert":
                pos = edit.position
                target_segment.text = target_segment.text[:pos] + edit.new_text + target_segment.text[pos:]
            elif edit.edit_type == "delete":
                pos = edit.position
                length = len(edit.original_text)
                target_segment.text = target_segment.text[:pos] + target_segment.text[pos + length:]
            
            edit.applied = True
            return True
        
        elif self.edit_conflict_resolution == "merge":
            # Implement operational transformation for merging
            # This is a simplified version
            edit.applied = True
            return True
        
        return False
    
    async def broadcast_transcription_update(self, session_id: str, segment: TranscriptionSegment):
        """Broadcast transcription update to all session users"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        message = {
            "type": "transcription_update",
            "session_id": session_id,
            "segment": asdict(segment),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all active users in session
        for user_id, user_session in session.users.items():
            if user_session.is_active and user_session.websocket:
                try:
                    await user_session.websocket.send(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast_edit_update(self, session_id: str, edit: CollaborativeEdit):
        """Broadcast edit update to all session users"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        message = {
            "type": "edit_update",
            "session_id": session_id,
            "edit": asdict(edit),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all active users except the editor
        for user_id, user_session in session.users.items():
            if user_session.is_active and user_session.websocket and user_id != edit.user_id:
                try:
                    await user_session.websocket.send(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error sending edit update to user {user_id}: {e}")
    
    async def broadcast_user_joined(self, session_id: str, user_session: UserSession):
        """Broadcast user joined notification"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        message = {
            "type": "user_joined",
            "session_id": session_id,
            "user": {
                "user_id": user_session.user_id,
                "username": user_session.username,
                "role": user_session.role
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all other users in session
        for user_id, other_user in session.users.items():
            if other_user.is_active and other_user.websocket and user_id != user_session.user_id:
                try:
                    await other_user.websocket.send(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error sending user joined notification to {user_id}: {e}")
    
    async def broadcast_user_left(self, session_id: str, user_session: UserSession):
        """Broadcast user left notification"""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        message = {
            "type": "user_left",
            "session_id": session_id,
            "user": {
                "user_id": user_session.user_id,
                "username": user_session.username,
                "role": user_session.role
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all remaining users in session
        for user_id, other_user in session.users.items():
            if other_user.is_active and other_user.websocket:
                try:
                    await other_user.websocket.send(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error sending user left notification to {user_id}: {e}")
    
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session.session_id,
            "title": session.title,
            "created_by": session.created_by,
            "created_at": session.created_at.isoformat(),
            "is_active": session.is_active,
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "role": user.role,
                    "is_active": user.is_active,
                    "last_activity": user.last_activity.isoformat()
                }
                for user in session.users.values()
            ],
            "segments": [asdict(segment) for segment in session.segments],
            "total_segments": len(session.segments),
            "settings": session.settings,
            "metadata": session.metadata
        }
    
    def export_session(self, session_id: str, format_type: str = "json") -> Optional[str]:
        """Export session data"""
        session_state = self.get_session_state(session_id)
        if not session_state:
            return None
        
        if format_type.lower() == "json":
            return json.dumps(session_state, indent=2, default=str)
        elif format_type.lower() == "text":
            # Export as plain text transcript
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            transcript_lines = []
            
            for segment in sorted(session.segments, key=lambda x: x.start_time):
                speaker = segment.speaker_id or "Unknown"
                timestamp = f"[{segment.start_time:.1f}s]"
                transcript_lines.append(f"{timestamp} {speaker}: {segment.text}")
            
            return "\\n".join(transcript_lines)
        
        return None

class WebSocketTranscriptionServer:
    """WebSocket server for real-time collaborative transcription"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.engine = CollaborativeTranscriptionEngine()
        
        logger.info(f"WebSocket Transcription Server initialized on {host}:{port}")
    
    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        client_id = str(uuid.uuid4())
        logger.info(f"New client connected: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.process_message(websocket, client_id, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await self.send_error(websocket, f"Processing error: {str(e)}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        
        finally:
            # Clean up client sessions
            await self.cleanup_client(client_id)
    
    async def process_message(self, websocket, client_id: str, data: Dict[str, Any]):
        """Process incoming WebSocket message"""
        message_type = data.get("type")
        
        if message_type == "create_session":
            session_id = self.engine.create_session(
                title=data.get("title", "Untitled Session"),
                created_by=data.get("user_id", client_id),
                settings=data.get("settings", {})
            )
            
            await websocket.send(json.dumps({
                "type": "session_created",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))
        
        elif message_type == "join_session":
            success = self.engine.join_session(
                session_id=data.get("session_id"),
                user_id=data.get("user_id", client_id),
                username=data.get("username", f"User_{client_id[:8]}"),
                websocket=websocket,
                role=data.get("role", "transcriber")
            )
            
            if success:
                # Send current session state
                session_state = self.engine.get_session_state(data.get("session_id"))
                await websocket.send(json.dumps({
                    "type": "session_joined",
                    "session_state": session_state,
                    "timestamp": datetime.now().isoformat()
                }))
            else:
                await self.send_error(websocket, "Failed to join session")
        
        elif message_type == "leave_session":
            self.engine.leave_session(
                session_id=data.get("session_id"),
                user_id=data.get("user_id", client_id)
            )
            
            await websocket.send(json.dumps({
                "type": "session_left",
                "timestamp": datetime.now().isoformat()
            }))
        
        elif message_type == "audio_data":
            # Process audio data for transcription
            import base64
            audio_bytes = base64.b64decode(data.get("audio_data", ""))
            
            await self.engine.process_audio_stream(
                session_id=data.get("session_id"),
                user_id=data.get("user_id", client_id),
                audio_data=audio_bytes
            )
        
        elif message_type == "edit_request":
            success = await self.engine.apply_edit(
                session_id=data.get("session_id"),
                user_id=data.get("user_id", client_id),
                edit_data=data.get("edit_data", {})
            )
            
            await websocket.send(json.dumps({
                "type": "edit_response",
                "success": success,
                "timestamp": datetime.now().isoformat()
            }))
        
        elif message_type == "get_session_state":
            session_state = self.engine.get_session_state(data.get("session_id"))
            
            await websocket.send(json.dumps({
                "type": "session_state",
                "session_state": session_state,
                "timestamp": datetime.now().isoformat()
            }))
        
        else:
            await self.send_error(websocket, f"Unknown message type: {message_type}")
    
    async def send_error(self, websocket, error_message: str):
        """Send error message to client"""
        await websocket.send(json.dumps({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }))
    
    async def cleanup_client(self, client_id: str):
        """Clean up client sessions when disconnected"""
        # Remove client from all sessions
        for session_id in list(self.engine.sessions.keys()):
            self.engine.leave_session(session_id, client_id)
    
    def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        start_server = websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

# Demo function
def demo_realtime_collaborative_transcription():
    """Demonstrate real-time collaborative transcription"""
    print("🎙️ Real-time Collaborative Transcription Demo")
    print("=" * 50)
    
    # Initialize the engine
    engine = CollaborativeTranscriptionEngine()
    
    print("Creating collaborative transcription session...")
    session_id = engine.create_session(
        title="Team Meeting Transcription",
        created_by="demo_user",
        settings={
            "language": "en",
            "auto_punctuation": True,
            "speaker_diarization": True,
            "real_time_editing": True
        }
    )
    print(f"✓ Session created: {session_id}")
    
    # Simulate multiple users joining
    print("\\nSimulating users joining session...")
    
    class MockWebSocket:
        def __init__(self, user_id):
            self.user_id = user_id
            self.messages = []
        
        async def send(self, message):
            self.messages.append(message)
    
    # User 1: Moderator
    ws1 = MockWebSocket("user1")
    success1 = engine.join_session(session_id, "user1", "Alice (Moderator)", ws1, "moderator")
    print(f"✓ Alice joined as moderator: {success1}")
    
    # User 2: Transcriber
    ws2 = MockWebSocket("user2")
    success2 = engine.join_session(session_id, "user2", "Bob (Transcriber)", ws2, "transcriber")
    print(f"✓ Bob joined as transcriber: {success2}")
    
    # User 3: Editor
    ws3 = MockWebSocket("user3")
    success3 = engine.join_session(session_id, "user3", "Charlie (Editor)", ws3, "editor")
    print(f"✓ Charlie joined as editor: {success3}")
    
    print(f"\\n📊 Session State:")
    session_state = engine.get_session_state(session_id)
    print(f"   Title: {session_state['title']}")
    print(f"   Active Users: {len(session_state['users'])}")
    print(f"   Total Segments: {session_state['total_segments']}")
    
    print(f"\\n👥 Active Users:")
    for user in session_state['users']:
        print(f"   - {user['username']} ({user['role']})")
    
    # Simulate audio processing and transcription
    print(f"\\n🎤 Simulating real-time transcription...")
    
    async def simulate_transcription():
        # Simulate audio chunks being processed
        mock_audio_chunks = [
            b"mock_audio_data_1" * 100,
            b"mock_audio_data_2" * 100,
            b"mock_audio_data_3" * 100
        ]
        
        for i, audio_chunk in enumerate(mock_audio_chunks):
            await engine.process_audio_stream(session_id, "user2", audio_chunk)
            print(f"   ✓ Processed audio chunk {i+1}")
            await asyncio.sleep(0.5)  # Simulate real-time delay
    
    # Run transcription simulation
    asyncio.run(simulate_transcription())
    
    # Check updated session state
    updated_state = engine.get_session_state(session_id)
    print(f"\\n📝 Transcription Results:")
    print(f"   Total Segments: {updated_state['total_segments']}")
    
    for i, segment in enumerate(updated_state['segments'][:3]):  # Show first 3
        print(f"   {i+1}. [{segment['start_time']:.1f}s] {segment['text']}")
        print(f"      Speaker: {segment['speaker_id']}, Confidence: {segment['confidence']:.2f}")
    
    # Simulate collaborative editing
    print(f"\\n✏️ Simulating collaborative editing...")
    
    async def simulate_editing():
        if updated_state['segments']:
            first_segment = updated_state['segments'][0]
            
            # Alice (moderator) makes an edit
            edit_success = await engine.apply_edit(session_id, "user1", {
                "segment_id": first_segment['id'],
                "edit_type": "replace",
                "original_text": first_segment['text'],
                "new_text": first_segment['text'] + " [Edited by Alice]",
                "position": 0
            })
            
            print(f"   ✓ Alice's edit applied: {edit_success}")
            
            # Charlie (editor) makes another edit
            edit_success2 = await engine.apply_edit(session_id, "user3", {
                "segment_id": first_segment['id'],
                "edit_type": "insert",
                "original_text": "",
                "new_text": " (Corrected)",
                "position": len(first_segment['text'])
            })
            
            print(f"   ✓ Charlie's edit applied: {edit_success2}")
    
    # Run editing simulation
    asyncio.run(simulate_editing())
    
    # Show final session state
    final_state = engine.get_session_state(session_id)
    print(f"\\n📋 Final Session Summary:")
    print(f"   Total Segments: {final_state['total_segments']}")
    print(f"   Total Edits: {len(final_state.get('edits', []))}")
    print(f"   Session Duration: {(datetime.now() - datetime.fromisoformat(final_state['created_at'])).total_seconds():.1f}s")
    
    # Export session
    print(f"\\n💾 Exporting session...")
    json_export = engine.export_session(session_id, "json")
    text_export = engine.export_session(session_id, "text")
    
    print(f"   ✓ JSON export: {len(json_export)} characters")
    print(f"   ✓ Text export: {len(text_export)} characters")
    
    print("\\n✅ Real-time collaborative transcription demo completed!")
    print("\\n💡 Integration Tips:")
    print("   • Use WebSocket server for real-time communication")
    print("   • Implement proper authentication and authorization")
    print("   • Add conflict resolution for simultaneous edits")
    print("   • Integrate with actual speech-to-text APIs")
    print("   • Add persistent storage for session data")

if __name__ == "__main__":
    demo_realtime_collaborative_transcription()