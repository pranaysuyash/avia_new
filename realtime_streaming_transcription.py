#!/usr/bin/env python3
"""
Real-time Streaming Transcription System
Implements WebRTC-based live audio capture with low-latency transcription,
multi-participant support, and live caption streaming
"""

import asyncio
import json
import logging
import hashlib
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from pathlib import Path
import wave
import struct
import threading
from collections import deque
import queue

# Audio processing
import sounddevice as sd
import soundfile as sf
import librosa
import webrtcvad

# WebSocket and streaming
import websockets
from websockets.server import WebSocketServerProtocol
import aiohttp
from aiohttp import web

# Transcription
import whisper
from faster_whisper import WhisperModel
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingMode(Enum):
    """Streaming transcription modes"""
    CONTINUOUS = "continuous"  # Continuous stream with no breaks
    VAD_BASED = "vad_based"    # Voice activity detection based
    FIXED_DURATION = "fixed_duration"  # Fixed duration chunks
    MANUAL = "manual"  # Manual start/stop


class TranscriptionEngine(Enum):
    """Available transcription engines"""
    WHISPER_API = "whisper_api"
    WHISPER_LOCAL = "whisper_local"
    FASTER_WHISPER = "faster_whisper"
    GOOGLE_SPEECH = "google_speech"
    AZURE_SPEECH = "azure_speech"


@dataclass
class StreamConfig:
    """Configuration for streaming session"""
    session_id: str
    language: str = "auto"
    engine: TranscriptionEngine = TranscriptionEngine.FASTER_WHISPER
    mode: StreamingMode = StreamingMode.VAD_BASED
    chunk_duration: float = 1.0  # seconds
    overlap_duration: float = 0.1  # seconds
    sample_rate: int = 16000
    channels: int = 1
    vad_aggressiveness: int = 2  # 0-3, higher is more aggressive
    min_speech_duration: float = 0.3  # minimum speech duration to process
    max_silence_duration: float = 1.0  # maximum silence before finalizing
    enable_punctuation: bool = True
    enable_formatting: bool = True
    custom_vocabulary: List[str] = field(default_factory=list)
    speaker_diarization: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionSegment:
    """Single transcription segment"""
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    is_final: bool = False
    language: Optional[str] = None
    words: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StreamingSession:
    """Active streaming session"""
    session_id: str
    config: StreamConfig
    start_time: datetime
    websocket: Optional[WebSocketServerProtocol] = None
    audio_buffer: deque = field(default_factory=lambda: deque(maxlen=100000))
    transcription_buffer: List[TranscriptionSegment] = field(default_factory=list)
    is_active: bool = True
    total_audio_duration: float = 0.0
    participant_count: int = 1
    error_count: int = 0


class AudioProcessor:
    """Process audio for streaming transcription"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_aggressiveness)
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.is_processing = False
        
    def process_audio_chunk(self, audio_data: bytes) -> Optional[bytes]:
        """Process raw audio chunk"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize audio
            audio_normalized = audio_array.astype(np.float32) / 32768.0
            
            # Apply noise reduction if needed
            if len(audio_normalized) > 0:
                audio_denoised = self._reduce_noise(audio_normalized)
                
                # Convert back to bytes
                audio_bytes = (audio_denoised * 32768).astype(np.int16).tobytes()
                return audio_bytes
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return None
    
    def _reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """Simple noise reduction"""
        # Apply spectral gating for noise reduction
        # This is simplified - production would use more sophisticated methods
        return audio
    
    def detect_voice_activity(self, audio_chunk: bytes) -> bool:
        """Detect if audio chunk contains speech"""
        try:
            # VAD expects 10, 20, or 30 ms chunks at 16kHz
            chunk_duration_ms = 30
            chunk_size = int(self.config.sample_rate * chunk_duration_ms / 1000) * 2
            
            # Process in VAD-compatible chunks
            for i in range(0, len(audio_chunk), chunk_size):
                chunk = audio_chunk[i:i + chunk_size]
                if len(chunk) == chunk_size:
                    if self.vad.is_speech(chunk, self.config.sample_rate):
                        return True
            return False
            
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False


class TranscriptionProcessor:
    """Handle transcription with multiple engines"""
    
    def __init__(self, engine: TranscriptionEngine = TranscriptionEngine.FASTER_WHISPER):
        self.engine = engine
        self.model = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize transcription model"""
        try:
            if self.engine == TranscriptionEngine.FASTER_WHISPER:
                self.model = WhisperModel("base", device="cpu", compute_type="int8")
            elif self.engine == TranscriptionEngine.WHISPER_LOCAL:
                self.model = whisper.load_model("base")
            # Add other engines as needed
            
            logger.info(f"Initialized {self.engine.value} transcription model")
            
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
    
    async def transcribe_chunk(
        self,
        audio_data: bytes,
        language: str = "auto",
        previous_context: Optional[str] = None
    ) -> TranscriptionSegment:
        """Transcribe audio chunk"""
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            # Write WAV header and data
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            
            try:
                if self.engine == TranscriptionEngine.FASTER_WHISPER:
                    result = await self._transcribe_faster_whisper(
                        tmp_file.name, language, previous_context
                    )
                elif self.engine == TranscriptionEngine.WHISPER_LOCAL:
                    result = await self._transcribe_whisper_local(
                        tmp_file.name, language
                    )
                elif self.engine == TranscriptionEngine.WHISPER_API:
                    result = await self._transcribe_whisper_api(
                        tmp_file.name, language
                    )
                else:
                    result = TranscriptionSegment(
                        text="[Unsupported engine]",
                        start_time=0,
                        end_time=0,
                        confidence=0
                    )
                
                return result
                
            finally:
                os.unlink(tmp_file.name)
    
    async def _transcribe_faster_whisper(
        self,
        audio_path: str,
        language: str,
        previous_context: Optional[str]
    ) -> TranscriptionSegment:
        """Transcribe using Faster Whisper"""
        
        # Detect language if auto
        if language == "auto":
            segments, info = self.model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=True
            )
            detected_language = info.language
        else:
            detected_language = language
        
        # Transcribe with context
        segments, info = self.model.transcribe(
            audio_path,
            language=None if language == "auto" else language,
            initial_prompt=previous_context,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True
        )
        
        # Collect results
        full_text = ""
        words = []
        start_time = None
        end_time = None
        
        for segment in segments:
            full_text += segment.text
            
            if start_time is None:
                start_time = segment.start
            end_time = segment.end
            
            if segment.words:
                for word in segment.words:
                    words.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.probability
                    })
        
        return TranscriptionSegment(
            text=full_text.strip(),
            start_time=start_time or 0,
            end_time=end_time or 0,
            confidence=info.language_probability if hasattr(info, 'language_probability') else 0.9,
            language=detected_language,
            words=words
        )
    
    async def _transcribe_whisper_local(
        self,
        audio_path: str,
        language: str
    ) -> TranscriptionSegment:
        """Transcribe using local Whisper model"""
        
        result = self.model.transcribe(
            audio_path,
            language=None if language == "auto" else language,
            word_timestamps=True
        )
        
        return TranscriptionSegment(
            text=result["text"].strip(),
            start_time=0,
            end_time=result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0,
            confidence=0.9,
            language=result.get("language", language),
            words=[]
        )
    
    async def _transcribe_whisper_api(
        self,
        audio_path: str,
        language: str
    ) -> TranscriptionSegment:
        """Transcribe using OpenAI Whisper API"""
        
        with open(audio_path, "rb") as audio_file:
            response = await asyncio.to_thread(
                openai.Audio.transcribe,
                model="whisper-1",
                file=audio_file,
                language=None if language == "auto" else language,
                response_format="verbose_json"
            )
        
        return TranscriptionSegment(
            text=response.text.strip(),
            start_time=0,
            end_time=response.duration if hasattr(response, 'duration') else 0,
            confidence=0.95,
            language=response.language if hasattr(response, 'language') else language,
            words=response.words if hasattr(response, 'words') else []
        )


class RealtimeStreamingTranscription:
    """Main real-time streaming transcription system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sessions: Dict[str, StreamingSession] = {}
        self.transcription_processor = TranscriptionProcessor(
            engine=TranscriptionEngine[self.config.get("engine", "FASTER_WHISPER")]
        )
        self.audio_processors: Dict[str, AudioProcessor] = {}
        self.websocket_server = None
        self.http_server = None
        
    async def start_session(
        self,
        session_config: StreamConfig
    ) -> StreamingSession:
        """Start a new streaming session"""
        
        session = StreamingSession(
            session_id=session_config.session_id,
            config=session_config,
            start_time=datetime.now()
        )
        
        self.sessions[session_config.session_id] = session
        self.audio_processors[session_config.session_id] = AudioProcessor(session_config)
        
        logger.info(f"Started streaming session: {session_config.session_id}")
        
        # Start processing loop for this session
        asyncio.create_task(self._process_session(session))
        
        return session
    
    async def _process_session(self, session: StreamingSession):
        """Process audio for a session"""
        
        audio_processor = self.audio_processors[session.session_id]
        buffer = bytearray()
        silence_duration = 0
        last_speech_time = time.time()
        previous_text = ""
        
        while session.is_active:
            try:
                # Check for audio in buffer
                if len(session.audio_buffer) > 0:
                    # Get audio chunk
                    audio_chunk = session.audio_buffer.popleft()
                    
                    # Process audio
                    processed_audio = audio_processor.process_audio_chunk(audio_chunk)
                    
                    if processed_audio:
                        # Detect voice activity
                        has_speech = audio_processor.detect_voice_activity(processed_audio)
                        
                        if has_speech:
                            buffer.extend(processed_audio)
                            last_speech_time = time.time()
                            silence_duration = 0
                        else:
                            silence_duration = time.time() - last_speech_time
                        
                        # Process based on mode
                        should_transcribe = False
                        
                        if session.config.mode == StreamingMode.VAD_BASED:
                            # Transcribe when we have enough speech or silence threshold reached
                            if len(buffer) > session.config.sample_rate * session.config.chunk_duration * 2:
                                if silence_duration > session.config.max_silence_duration:
                                    should_transcribe = True
                        
                        elif session.config.mode == StreamingMode.FIXED_DURATION:
                            # Transcribe at fixed intervals
                            if len(buffer) > session.config.sample_rate * session.config.chunk_duration * 2:
                                should_transcribe = True
                        
                        elif session.config.mode == StreamingMode.CONTINUOUS:
                            # Always transcribe available audio
                            if len(buffer) > session.config.sample_rate * 0.5 * 2:  # 0.5 second minimum
                                should_transcribe = True
                        
                        if should_transcribe and len(buffer) > 0:
                            # Transcribe buffer
                            segment = await self.transcription_processor.transcribe_chunk(
                                bytes(buffer),
                                session.config.language,
                                previous_text[-100:] if previous_text else None
                            )
                            
                            if segment.text:
                                # Update segment timing
                                segment.start_time = session.total_audio_duration
                                segment.end_time = session.total_audio_duration + len(buffer) / (session.config.sample_rate * 2)
                                segment.is_final = silence_duration > session.config.max_silence_duration
                                
                                # Add to transcription buffer
                                session.transcription_buffer.append(segment)
                                previous_text = segment.text
                                
                                # Send to clients
                                await self._broadcast_transcription(session, segment)
                                
                                # Update session stats
                                session.total_audio_duration = segment.end_time
                            
                            # Clear or reduce buffer
                            if session.config.mode == StreamingMode.VAD_BASED and segment.is_final:
                                buffer.clear()
                            else:
                                # Keep overlap for context
                                overlap_samples = int(session.config.sample_rate * session.config.overlap_duration * 2)
                                buffer = buffer[-overlap_samples:] if len(buffer) > overlap_samples else bytearray()
                
                else:
                    # No audio available, wait
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Session processing error: {e}")
                session.error_count += 1
                
                if session.error_count > 10:
                    logger.error(f"Too many errors, stopping session {session.session_id}")
                    session.is_active = False
    
    async def _broadcast_transcription(
        self,
        session: StreamingSession,
        segment: TranscriptionSegment
    ):
        """Broadcast transcription to connected clients"""
        
        if session.websocket:
            try:
                message = {
                    "type": "transcription",
                    "session_id": session.session_id,
                    "segment": {
                        "text": segment.text,
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "confidence": segment.confidence,
                        "is_final": segment.is_final,
                        "language": segment.language,
                        "speaker_id": segment.speaker_id,
                        "words": segment.words
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                await session.websocket.send(json.dumps(message))
                
            except Exception as e:
                logger.error(f"Failed to broadcast transcription: {e}")
    
    async def add_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes
    ):
        """Add audio chunk to session buffer"""
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.audio_buffer.append(audio_data)
        else:
            logger.warning(f"Session {session_id} not found")
    
    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """Stop a streaming session"""
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            
            # Wait for final processing
            await asyncio.sleep(0.5)
            
            # Compile final transcript
            full_transcript = " ".join([seg.text for seg in session.transcription_buffer])
            
            # Calculate statistics
            stats = {
                "session_id": session_id,
                "duration": (datetime.now() - session.start_time).total_seconds(),
                "audio_duration": session.total_audio_duration,
                "segment_count": len(session.transcription_buffer),
                "word_count": len(full_transcript.split()),
                "error_count": session.error_count,
                "participant_count": session.participant_count
            }
            
            # Clean up
            del self.sessions[session_id]
            del self.audio_processors[session_id]
            
            return {
                "transcript": full_transcript,
                "segments": [
                    {
                        "text": seg.text,
                        "start": seg.start_time,
                        "end": seg.end_time,
                        "confidence": seg.confidence,
                        "is_final": seg.is_final
                    }
                    for seg in session.transcription_buffer
                ],
                "statistics": stats
            }
        
        return {"error": "Session not found"}
    
    async def handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections"""
        
        session_id = None
        
        try:
            # Wait for initial configuration
            config_message = await websocket.recv()
            config_data = json.loads(config_message)
            
            # Create session configuration
            session_config = StreamConfig(
                session_id=config_data.get("session_id", str(hashlib.md5(str(time.time()).encode()).hexdigest())),
                language=config_data.get("language", "auto"),
                engine=TranscriptionEngine[config_data.get("engine", "FASTER_WHISPER")],
                mode=StreamingMode[config_data.get("mode", "VAD_BASED")],
                chunk_duration=config_data.get("chunk_duration", 1.0),
                speaker_diarization=config_data.get("speaker_diarization", False)
            )
            
            session_id = session_config.session_id
            
            # Start session
            session = await self.start_session(session_config)
            session.websocket = websocket
            
            # Send confirmation
            await websocket.send(json.dumps({
                "type": "session_started",
                "session_id": session_id,
                "config": {
                    "language": session_config.language,
                    "engine": session_config.engine.value,
                    "mode": session_config.mode.value
                }
            }))
            
            # Handle incoming audio
            async for message in websocket:
                if isinstance(message, bytes):
                    # Audio data
                    await self.add_audio_chunk(session_id, message)
                else:
                    # Control message
                    try:
                        control = json.loads(message)
                        
                        if control.get("type") == "stop":
                            break
                        elif control.get("type") == "update_config":
                            # Update session configuration
                            if "language" in control:
                                session.config.language = control["language"]
                                
                    except json.JSONDecodeError:
                        logger.warning("Invalid control message")
            
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for session {session_id}")
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            
        finally:
            # Stop session if still active
            if session_id and session_id in self.sessions:
                await self.stop_session(session_id)
    
    async def start_websocket_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start WebSocket server"""
        
        self.websocket_server = await websockets.serve(
            self.handle_websocket,
            host,
            port
        )
        
        logger.info(f"WebSocket server started on ws://{host}:{port}")
        
        await asyncio.Future()  # Run forever
    
    async def handle_http_audio(self, request: web.Request) -> web.Response:
        """Handle HTTP audio upload for streaming"""
        
        session_id = request.match_info.get('session_id')
        
        if not session_id or session_id not in self.sessions:
            return web.json_response({"error": "Invalid session"}, status=404)
        
        # Read audio data
        audio_data = await request.read()
        
        # Add to session buffer
        await self.add_audio_chunk(session_id, audio_data)
        
        return web.json_response({"status": "received", "bytes": len(audio_data)})
    
    async def handle_create_session(self, request: web.Request) -> web.Response:
        """Create new streaming session via HTTP"""
        
        data = await request.json()
        
        session_config = StreamConfig(
            session_id=data.get("session_id", str(hashlib.md5(str(time.time()).encode()).hexdigest())),
            language=data.get("language", "auto"),
            engine=TranscriptionEngine[data.get("engine", "FASTER_WHISPER")],
            mode=StreamingMode[data.get("mode", "VAD_BASED")]
        )
        
        session = await self.start_session(session_config)
        
        return web.json_response({
            "session_id": session.session_id,
            "status": "created",
            "config": {
                "language": session_config.language,
                "engine": session_config.engine.value,
                "mode": session_config.mode.value
            }
        })
    
    async def handle_stop_session(self, request: web.Request) -> web.Response:
        """Stop streaming session via HTTP"""
        
        session_id = request.match_info.get('session_id')
        
        result = await self.stop_session(session_id)
        
        if "error" in result:
            return web.json_response(result, status=404)
        
        return web.json_response(result)
    
    async def start_http_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start HTTP server for REST API"""
        
        app = web.Application()
        
        # Add routes
        app.router.add_post('/api/streaming/session', self.handle_create_session)
        app.router.add_post('/api/streaming/session/{session_id}/audio', self.handle_http_audio)
        app.router.add_post('/api/streaming/session/{session_id}/stop', self.handle_stop_session)
        
        # Add CORS middleware
        async def cors_middleware(app, handler):
            async def middleware_handler(request):
                response = await handler(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return response
            return middleware_handler
        
        app.middlewares.append(cors_middleware)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        self.http_server = web.TCPSite(runner, host, port)
        await self.http_server.start()
        
        logger.info(f"HTTP server started on http://{host}:{port}")
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions"""
        
        return [
            {
                "session_id": session.session_id,
                "start_time": session.start_time.isoformat(),
                "duration": (datetime.now() - session.start_time).total_seconds(),
                "audio_duration": session.total_audio_duration,
                "segment_count": len(session.transcription_buffer),
                "participant_count": session.participant_count,
                "language": session.config.language,
                "is_active": session.is_active
            }
            for session in self.sessions.values()
        ]


# Example usage
async def main():
    """Example usage of real-time streaming transcription"""
    
    # Initialize system
    streaming_system = RealtimeStreamingTranscription({
        "engine": "FASTER_WHISPER"
    })
    
    # Start servers
    await asyncio.gather(
        streaming_system.start_websocket_server(port=8765),
        streaming_system.start_http_server(port=8080)
    )


if __name__ == "__main__":
    asyncio.run(main())