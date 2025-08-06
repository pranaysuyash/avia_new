"""
Real-Time Transcription System
Implements live streaming transcription using multiple engines including Whisper API,
Mozilla DeepSpeech, and Vosk with WebSocket support for real-time audio streaming
"""

import os
import logging
import asyncio
import json
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
import websockets
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import openai
from pydantic import BaseModel
import torch
import torchaudio
from collections import deque
import wave
import pyaudio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionEngine(Enum):
    WHISPER_API = "whisper_api"
    WHISPER_LOCAL = "whisper_local"
    DEEPSPEECH = "deepspeech"
    VOSK = "vosk"
    GOOGLE_SPEECH = "google_speech"
    AZURE_SPEECH = "azure_speech"

class StreamingMode(Enum):
    CONTINUOUS = "continuous"
    PUSH_TO_TALK = "push_to_talk"
    VOICE_ACTIVITY = "voice_activity"

@dataclass
class TranscriptionSegment:
    text: str
    start_time: float
    end_time: float
    confidence: float
    is_final: bool
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    engine: Optional[str] = None

@dataclass
class StreamingConfig:
    engine: TranscriptionEngine
    language: str = "en"
    sample_rate: int = 16000
    chunk_duration: float = 1.0  # seconds
    buffer_duration: float = 5.0  # seconds
    overlap_duration: float = 0.5  # seconds
    confidence_threshold: float = 0.7
    enable_vad: bool = True
    enable_speaker_diarization: bool = False
    streaming_mode: StreamingMode = StreamingMode.CONTINUOUS

@dataclass
class StreamingStats:
    total_audio_duration: float = 0.0
    total_processing_time: float = 0.0
    segments_processed: int = 0
    average_latency: float = 0.0
    confidence_scores: List[float] = None
    error_count: int = 0
    
    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = []

class AudioBuffer:
    """Circular buffer for audio data with overlap management"""
    
    def __init__(self, max_duration: float, sample_rate: int, overlap_duration: float = 0.5):
        self.max_duration = max_duration
        self.sample_rate = sample_rate
        self.overlap_duration = overlap_duration
        self.max_samples = int(max_duration * sample_rate)
        self.overlap_samples = int(overlap_duration * sample_rate)
        
        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.write_pos = 0
        self.total_samples = 0
        self.lock = threading.Lock()
    
    def add_audio(self, audio_data: np.ndarray):
        """Add audio data to the buffer"""
        with self.lock:
            audio_data = audio_data.astype(np.float32)
            samples_to_add = len(audio_data)
            
            if samples_to_add > self.max_samples:
                # If audio is longer than buffer, take the last part
                audio_data = audio_data[-self.max_samples:]
                samples_to_add = self.max_samples
            
            # Handle circular buffer
            if self.write_pos + samples_to_add <= self.max_samples:
                self.buffer[self.write_pos:self.write_pos + samples_to_add] = audio_data
            else:
                # Wrap around
                first_part = self.max_samples - self.write_pos
                self.buffer[self.write_pos:] = audio_data[:first_part]
                self.buffer[:samples_to_add - first_part] = audio_data[first_part:]
            
            self.write_pos = (self.write_pos + samples_to_add) % self.max_samples
            self.total_samples += samples_to_add
    
    def get_audio_chunk(self, duration: float) -> np.ndarray:
        """Get audio chunk of specified duration"""
        with self.lock:
            chunk_samples = int(duration * self.sample_rate)
            chunk_samples = min(chunk_samples, min(self.total_samples, self.max_samples))
            
            if chunk_samples == 0:
                return np.array([], dtype=np.float32)
            
            # Get the most recent audio
            start_pos = (self.write_pos - chunk_samples) % self.max_samples
            
            if start_pos + chunk_samples <= self.max_samples:
                return self.buffer[start_pos:start_pos + chunk_samples].copy()
            else:
                # Handle wrap around
                first_part = self.max_samples - start_pos
                second_part = chunk_samples - first_part
                return np.concatenate([
                    self.buffer[start_pos:],
                    self.buffer[:second_part]
                ])
    
    def get_overlapped_chunk(self, duration: float) -> np.ndarray:
        """Get audio chunk with overlap for better transcription continuity"""
        total_duration = duration + self.overlap_duration
        return self.get_audio_chunk(total_duration)

class WhisperTranscriber:
    """Whisper-based transcription engine"""
    
    def __init__(self, use_api: bool = True, model_name: str = "whisper-1"):
        self.use_api = use_api
        self.model_name = model_name
        self.client = None
        self.local_model = None
        
        if use_api:
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            try:
                import whisper
                self.local_model = whisper.load_model(model_name)
            except ImportError:
                logger.error("Whisper not installed for local transcription")
    
    async def transcribe_chunk(self, audio_data: np.ndarray, sample_rate: int, 
                              language: str = "en") -> TranscriptionSegment:
        """Transcribe audio chunk"""
        try:
            if self.use_api and self.client:
                return await self._transcribe_with_api(audio_data, sample_rate, language)
            elif self.local_model:
                return await self._transcribe_with_local(audio_data, sample_rate, language)
            else:
                raise ValueError("No Whisper transcription method available")
                
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return TranscriptionSegment("", 0.0, 0.0, 0.0, True, engine="whisper")
    
    async def _transcribe_with_api(self, audio_data: np.ndarray, sample_rate: int, 
                                  language: str) -> TranscriptionSegment:
        """Transcribe using OpenAI Whisper API"""
        # Save audio to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            
            try:
                with open(tmp_file.name, 'rb') as audio_file:
                    response = await asyncio.to_thread(
                        self.client.audio.transcriptions.create,
                        model=self.model_name,
                        file=audio_file,
                        language=language,
                        response_format="verbose_json"
                    )
                
                duration = len(audio_data) / sample_rate
                confidence = getattr(response, 'confidence', 0.8)  # Default confidence
                
                return TranscriptionSegment(
                    text=response.text,
                    start_time=0.0,
                    end_time=duration,
                    confidence=confidence,
                    is_final=True,
                    engine="whisper_api"
                )
                
            finally:
                os.unlink(tmp_file.name)
    
    async def _transcribe_with_local(self, audio_data: np.ndarray, sample_rate: int, 
                                    language: str) -> TranscriptionSegment:
        """Transcribe using local Whisper model"""
        try:
            # Resample if necessary
            if sample_rate != 16000:
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
            
            result = await asyncio.to_thread(
                self.local_model.transcribe, 
                audio_data, 
                language=language
            )
            
            duration = len(audio_data) / sample_rate
            
            return TranscriptionSegment(
                text=result["text"],
                start_time=0.0,
                end_time=duration,
                confidence=0.8,  # Whisper doesn't provide confidence scores
                is_final=True,
                engine="whisper_local"
            )
            
        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            return TranscriptionSegment("", 0.0, 0.0, 0.0, True, engine="whisper_local")

class VoskTranscriber:
    """Vosk-based transcription engine for streaming"""
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.recognizer = None
        
        try:
            import vosk
            if model_path and os.path.exists(model_path):
                self.model = vosk.Model(model_path)
            else:
                # Try to use default model
                logger.warning("Vosk model path not provided or doesn't exist")
                
        except ImportError:
            logger.error("Vosk not installed")
    
    def initialize_recognizer(self, sample_rate: int):
        """Initialize recognizer for streaming"""
        if self.model:
            import vosk
            self.recognizer = vosk.KaldiRecognizer(self.model, sample_rate)
            self.recognizer.SetWords(True)
    
    async def transcribe_chunk(self, audio_data: np.ndarray, sample_rate: int, 
                              is_final: bool = False) -> TranscriptionSegment:
        """Transcribe audio chunk with Vosk"""
        try:
            if not self.recognizer:
                self.initialize_recognizer(sample_rate)
            
            if not self.recognizer:
                return TranscriptionSegment("", 0.0, 0.0, 0.0, True, engine="vosk")
            
            # Convert to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            if is_final:
                self.recognizer.AcceptWaveform(audio_bytes)
                result = json.loads(self.recognizer.FinalResult())
            else:
                if self.recognizer.AcceptWaveform(audio_bytes):
                    result = json.loads(self.recognizer.Result())
                else:
                    result = json.loads(self.recognizer.PartialResult())
            
            text = result.get('text', '')
            confidence = result.get('confidence', 0.7)
            
            duration = len(audio_data) / sample_rate
            
            return TranscriptionSegment(
                text=text,
                start_time=0.0,
                end_time=duration,
                confidence=confidence,
                is_final=is_final,
                engine="vosk"
            )
            
        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            return TranscriptionSegment("", 0.0, 0.0, 0.0, True, engine="vosk")

class RealTimeTranscriptionSystem:
    """Main real-time transcription system"""
    
    def __init__(self, config: StreamingConfig, db_path: str = "realtime_transcription.db"):
        self.config = config
        self.db_path = db_path
        
        # Audio processing
        self.audio_buffer = AudioBuffer(
            max_duration=config.buffer_duration,
            sample_rate=config.sample_rate,
            overlap_duration=config.overlap_duration
        )
        
        # Transcription engines
        self.whisper_transcriber = WhisperTranscriber(
            use_api=(config.engine == TranscriptionEngine.WHISPER_API)
        )
        self.vosk_transcriber = VoskTranscriber()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Processing state
        self.is_streaming = False
        self.processing_queue = asyncio.Queue()
        self.stats = StreamingStats()
        
        # Initialize database
        self.init_database()
        
        # Start processing task
        self.processing_task = None
    
    def init_database(self):
        """Initialize the transcription database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Transcription sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcription_sessions (
                id TEXT PRIMARY KEY,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                config TEXT,
                stats TEXT,
                total_duration REAL,
                total_segments INTEGER
            )
        ''')
        
        # Transcription segments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcription_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                text TEXT,
                start_time REAL,
                end_time REAL,
                confidence REAL,
                is_final BOOLEAN,
                speaker_id TEXT,
                language TEXT,
                engine TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES transcription_sessions (id)
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                latency REAL,
                processing_time REAL,
                audio_duration REAL,
                confidence REAL,
                engine TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES transcription_sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Real-time transcription database initialized")
    
    async def start_streaming(self, session_id: str = None):
        """Start real-time transcription streaming"""
        if self.is_streaming:
            logger.warning("Streaming already active")
            return
        
        self.is_streaming = True
        self.session_id = session_id or f"session_{int(time.time())}"
        
        # Store session in database
        self.store_session_start()
        
        # Start processing task
        self.processing_task = asyncio.create_task(self._process_audio_stream())
        
        logger.info(f"Started real-time transcription session: {self.session_id}")
    
    async def stop_streaming(self):
        """Stop real-time transcription streaming"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Store session end
        self.store_session_end()
        
        logger.info(f"Stopped real-time transcription session: {self.session_id}")
    
    async def add_audio_data(self, audio_data: np.ndarray):
        """Add audio data to the processing buffer"""
        if not self.is_streaming:
            return
        
        self.audio_buffer.add_audio(audio_data)
        self.stats.total_audio_duration += len(audio_data) / self.config.sample_rate
    
    async def _process_audio_stream(self):
        """Main audio processing loop"""
        last_process_time = time.time()
        
        while self.is_streaming:
            try:
                current_time = time.time()
                
                # Check if it's time to process a chunk
                if current_time - last_process_time >= self.config.chunk_duration:
                    # Get audio chunk with overlap
                    audio_chunk = self.audio_buffer.get_overlapped_chunk(
                        self.config.chunk_duration
                    )
                    
                    if len(audio_chunk) > 0:
                        # Process the chunk
                        await self._process_audio_chunk(audio_chunk)
                    
                    last_process_time = current_time
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                self.stats.error_count += 1
    
    async def _process_audio_chunk(self, audio_chunk: np.ndarray):
        """Process a single audio chunk"""
        start_time = time.time()
        
        try:
            # Apply VAD if enabled
            if self.config.enable_vad:
                # Simple energy-based VAD
                energy = np.mean(audio_chunk ** 2)
                if energy < 0.001:  # Silence threshold
                    return
            
            # Transcribe based on selected engine
            if self.config.engine == TranscriptionEngine.WHISPER_API:
                segment = await self.whisper_transcriber.transcribe_chunk(
                    audio_chunk, self.config.sample_rate, self.config.language
                )
            elif self.config.engine == TranscriptionEngine.VOSK:
                segment = await self.vosk_transcriber.transcribe_chunk(
                    audio_chunk, self.config.sample_rate, is_final=False
                )
            else:
                # Default to Whisper API
                segment = await self.whisper_transcriber.transcribe_chunk(
                    audio_chunk, self.config.sample_rate, self.config.language
                )
            
            # Filter by confidence threshold
            if segment.confidence < self.config.confidence_threshold:
                return
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats.total_processing_time += processing_time
            self.stats.segments_processed += 1
            self.stats.confidence_scores.append(segment.confidence)
            
            # Calculate latency
            audio_duration = len(audio_chunk) / self.config.sample_rate
            latency = processing_time
            self.stats.average_latency = (
                (self.stats.average_latency * (self.stats.segments_processed - 1) + latency) /
                self.stats.segments_processed
            )
            
            # Store segment in database
            self.store_transcription_segment(segment)
            
            # Store performance metrics
            self.store_performance_metrics(latency, processing_time, audio_duration, segment.confidence)
            
            # Broadcast to WebSocket clients
            await self.broadcast_transcription(segment)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            self.stats.error_count += 1
    
    async def connect_websocket(self, websocket: WebSocket):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect_websocket(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast_transcription(self, segment: TranscriptionSegment):
        """Broadcast transcription to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message = {
            "type": "transcription",
            "data": {
                "text": segment.text,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "confidence": segment.confidence,
                "is_final": segment.is_final,
                "speaker_id": segment.speaker_id,
                "language": segment.language,
                "engine": segment.engine,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # Send to all connected clients
        disconnected_clients = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected_clients.append(websocket)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.disconnect_websocket(client)
    
    def store_session_start(self):
        """Store session start in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transcription_sessions (id, config)
                VALUES (?, ?)
            ''', (self.session_id, json.dumps(asdict(self.config))))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store session start: {e}")
    
    def store_session_end(self):
        """Store session end in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE transcription_sessions 
                SET end_time = CURRENT_TIMESTAMP, stats = ?, 
                    total_duration = ?, total_segments = ?
                WHERE id = ?
            ''', (
                json.dumps(asdict(self.stats)),
                self.stats.total_audio_duration,
                self.stats.segments_processed,
                self.session_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store session end: {e}")
    
    def store_transcription_segment(self, segment: TranscriptionSegment):
        """Store transcription segment in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transcription_segments 
                (session_id, text, start_time, end_time, confidence, is_final, 
                 speaker_id, language, engine)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.session_id, segment.text, segment.start_time, segment.end_time,
                segment.confidence, segment.is_final, segment.speaker_id,
                segment.language, segment.engine
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store transcription segment: {e}")
    
    def store_performance_metrics(self, latency: float, processing_time: float, 
                                 audio_duration: float, confidence: float):
        """Store performance metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (session_id, latency, processing_time, audio_duration, confidence, engine)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.session_id, latency, processing_time, audio_duration,
                confidence, self.config.engine.value
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store performance metrics: {e}")
    
    def get_session_statistics(self, session_id: str = None) -> Dict[str, Any]:
        """Get statistics for a transcription session"""
        try:
            target_session = session_id or self.session_id
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute('''
                SELECT * FROM transcription_sessions WHERE id = ?
            ''', (target_session,))
            session_data = cursor.fetchone()
            
            # Get segments count
            cursor.execute('''
                SELECT COUNT(*), AVG(confidence) FROM transcription_segments 
                WHERE session_id = ?
            ''', (target_session,))
            segment_stats = cursor.fetchone()
            
            # Get performance metrics
            cursor.execute('''
                SELECT AVG(latency), AVG(processing_time), SUM(audio_duration)
                FROM performance_metrics WHERE session_id = ?
            ''', (target_session,))
            perf_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                "session_id": target_session,
                "session_data": session_data,
                "total_segments": segment_stats[0] if segment_stats else 0,
                "average_confidence": segment_stats[1] if segment_stats else 0,
                "average_latency": perf_stats[0] if perf_stats else 0,
                "average_processing_time": perf_stats[1] if perf_stats else 0,
                "total_audio_duration": perf_stats[2] if perf_stats else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {}

# FastAPI application for WebSocket server
app = FastAPI(title="Real-Time Transcription API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global transcription system instance
transcription_system = None

@app.on_event("startup")
async def startup_event():
    """Initialize transcription system on startup"""
    global transcription_system
    
    config = StreamingConfig(
        engine=TranscriptionEngine.WHISPER_API,
        language="en",
        sample_rate=16000,
        chunk_duration=2.0,
        buffer_duration=10.0,
        confidence_threshold=0.5
    )
    
    transcription_system = RealTimeTranscriptionSystem(config)
    logger.info("Real-time transcription system initialized")

@app.websocket("/ws/transcription")
async def websocket_transcription_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    await transcription_system.connect_websocket(websocket)
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()
            
            # Convert bytes to numpy array (assuming 16-bit PCM)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Add to transcription system
            await transcription_system.add_audio_data(audio_data)
            
    except WebSocketDisconnect:
        await transcription_system.disconnect_websocket(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await transcription_system.disconnect_websocket(websocket)

@app.post("/api/transcription/start")
async def start_transcription_session():
    """Start a new transcription session"""
    session_id = f"session_{int(time.time())}"
    await transcription_system.start_streaming(session_id)
    return {"session_id": session_id, "status": "started"}

@app.post("/api/transcription/stop")
async def stop_transcription_session():
    """Stop the current transcription session"""
    await transcription_system.stop_streaming()
    return {"status": "stopped"}

@app.get("/api/transcription/stats/{session_id}")
async def get_transcription_stats(session_id: str):
    """Get statistics for a transcription session"""
    stats = transcription_system.get_session_statistics(session_id)
    return stats

@app.get("/api/transcription/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "is_streaming": transcription_system.is_streaming if transcription_system else False,
        "active_connections": len(transcription_system.active_connections) if transcription_system else 0
    }

if __name__ == "__main__":
    # Run the WebSocket server
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")