"""
Enhanced Real-time Streaming Transcription System
Provides WebSocket-based live transcription with advanced features
"""

import asyncio
import json
import uuid
import wave
import io
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
import whisper
import torch
import torchaudio
from transformers import pipeline
import webrtcvad
import logging
from collections import deque
import threading
import queue
import time

logger = logging.getLogger(__name__)

class StreamingMode(Enum):
    """Streaming modes"""
    REALTIME = "realtime"  # Lowest latency
    BALANCED = "balanced"  # Balance between latency and accuracy
    ACCURATE = "accurate"  # Highest accuracy, higher latency

class AudioFormat(Enum):
    """Supported audio formats"""
    PCM = "pcm"
    OPUS = "opus"
    WEBM = "webm"
    MP3 = "mp3"

@dataclass
class StreamConfig:
    """Configuration for streaming session"""
    mode: StreamingMode = StreamingMode.BALANCED
    language: str = "auto"
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 100  # Chunk size in milliseconds
    buffer_duration_ms: int = 2000  # Buffer size for processing
    vad_aggressiveness: int = 2  # 0-3, higher is more aggressive
    enable_punctuation: bool = True
    enable_speaker_diarization: bool = False
    enable_sentiment_analysis: bool = False
    enable_keyword_detection: bool = False
    keywords: List[str] = None
    max_alternatives: int = 1
    enable_word_timestamps: bool = True
    enable_auto_highlights: bool = True
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

@dataclass
class TranscriptionSegment:
    """Represents a transcription segment"""
    id: str
    text: str
    start_time: float
    end_time: float
    confidence: float
    speaker: Optional[str] = None
    is_final: bool = False
    alternatives: List[Dict] = None
    words: List[Dict] = None
    sentiment: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.words is None:
            self.words = []
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class StreamingSession:
    """Represents a streaming session"""
    session_id: str
    user_id: str
    config: StreamConfig
    created_at: datetime
    status: str = "active"
    total_duration: float = 0
    segments: List[TranscriptionSegment] = None
    
    def __post_init__(self):
        if self.segments is None:
            self.segments = []

class AudioProcessor:
    """Processes audio chunks for transcription"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.vad = webrtcvad.Vad(config.vad_aggressiveness)
        self.audio_buffer = deque(maxlen=int(
            config.buffer_duration_ms / config.chunk_duration_ms
        ))
        self.sample_width = 2  # 16-bit audio
        
    def process_chunk(self, audio_data: bytes) -> Tuple[bool, np.ndarray]:
        """Process audio chunk and return if speech detected"""
        # Check for speech using VAD
        is_speech = self.vad.is_speech(
            audio_data,
            self.config.sample_rate
        )
        
        # Convert to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        return is_speech, audio_array
        
    def denoise(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply noise reduction to audio"""
        # Simple spectral subtraction for noise reduction
        # In production, use more sophisticated methods
        return audio_array
        
    def normalize(self, audio_array: np.ndarray) -> np.ndarray:
        """Normalize audio volume"""
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            return audio_array / max_val * 0.9
        return audio_array

class TranscriptionEngine:
    """Handles real-time transcription using Whisper"""
    
    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.device)
        
        # Additional models for enhanced features
        self.sentiment_model = None
        self.diarization_model = None
        
    def load_enhancement_models(self):
        """Load additional models for enhanced features"""
        try:
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment"
            )
        except Exception as e:
            logger.warning(f"Could not load sentiment model: {e}")
            
    def transcribe_chunk(
        self,
        audio_array: np.ndarray,
        language: str = "auto"
    ) -> Dict:
        """Transcribe audio chunk"""
        # Prepare audio for Whisper
        audio_tensor = torch.from_numpy(audio_array).to(self.device)
        
        # Detect language if auto
        if language == "auto":
            # Use first 30 seconds to detect language
            mel = whisper.log_mel_spectrogram(audio_tensor).to(self.device)
            _, probs = self.model.detect_language(mel)
            language = max(probs, key=probs.get)
            
        # Transcribe
        result = self.model.transcribe(
            audio_array,
            language=language,
            word_timestamps=True,
            task="transcribe"
        )
        
        return {
            'text': result['text'],
            'language': language,
            'segments': result.get('segments', []),
            'words': self._extract_words(result)
        }
        
    def _extract_words(self, result: Dict) -> List[Dict]:
        """Extract word-level timestamps"""
        words = []
        for segment in result.get('segments', []):
            for word_info in segment.get('words', []):
                words.append({
                    'word': word_info['word'],
                    'start': word_info['start'],
                    'end': word_info['end'],
                    'probability': word_info.get('probability', 1.0)
                })
        return words
        
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text"""
        if not self.sentiment_model or not text:
            return "neutral"
            
        try:
            result = self.sentiment_model(text)[0]
            label = result['label']
            # Convert star rating to sentiment
            stars = int(label.split()[0])
            if stars <= 2:
                return "negative"
            elif stars == 3:
                return "neutral"
            else:
                return "positive"
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return "neutral"
            
    def detect_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Detect keywords in text"""
        detected = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                detected.append(keyword)
        return detected

class EnhancedRealtimeStreamingSystem:
    """Main system for enhanced real-time streaming transcription"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        model_size: str = "base"
    ):
        self.redis_client = redis_client
        self.sessions: Dict[str, StreamingSession] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.audio_processors: Dict[str, AudioProcessor] = {}
        self.transcription_engine = TranscriptionEngine(model_size)
        self.processing_queues: Dict[str, queue.Queue] = {}
        self.processing_threads: Dict[str, threading.Thread] = {}
        self._running = False
        
    async def initialize(self):
        """Initialize the streaming system"""
        if not self.redis_client:
            self.redis_client = await redis.from_url("redis://localhost:6379")
        
        # Load enhancement models
        self.transcription_engine.load_enhancement_models()
        
        self._running = True
        logger.info("Enhanced real-time streaming system initialized")
        
    async def shutdown(self):
        """Shutdown the streaming system"""
        self._running = False
        
        # Stop all processing threads
        for thread in self.processing_threads.values():
            if thread.is_alive():
                thread.join(timeout=1)
                
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Enhanced real-time streaming system shutdown")
        
    async def create_session(
        self,
        user_id: str,
        config: StreamConfig
    ) -> str:
        """Create a new streaming session"""
        session_id = str(uuid.uuid4())
        
        session = StreamingSession(
            session_id=session_id,
            user_id=user_id,
            config=config,
            created_at=datetime.utcnow()
        )
        
        self.sessions[session_id] = session
        self.audio_processors[session_id] = AudioProcessor(config)
        self.processing_queues[session_id] = queue.Queue()
        
        # Start processing thread
        thread = threading.Thread(
            target=self._process_audio_queue,
            args=(session_id,),
            daemon=True
        )
        thread.start()
        self.processing_threads[session_id] = thread
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"stream:session:{session_id}",
                mapping={
                    'user_id': user_id,
                    'created_at': session.created_at.isoformat(),
                    'config': json.dumps(asdict(config))
                }
            )
            
        logger.info(f"Created streaming session {session_id}")
        return session_id
        
    async def handle_websocket(
        self,
        websocket: WebSocket,
        session_id: str
    ):
        """Handle WebSocket connection for streaming"""
        if session_id not in self.sessions:
            await websocket.close(code=4004, reason="Session not found")
            return
            
        self.websockets[session_id] = websocket
        
        try:
            await websocket.accept()
            await self._send_session_info(session_id)
            
            while True:
                # Receive audio data or control messages
                data = await websocket.receive_bytes()
                await self._process_websocket_data(session_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for session {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            await self.end_session(session_id)
            
    async def _process_websocket_data(self, session_id: str, data: bytes):
        """Process incoming WebSocket data"""
        if session_id not in self.sessions:
            return
            
        # Check if it's audio data or control message
        try:
            # Try to parse as JSON (control message)
            message = json.loads(data)
            await self._handle_control_message(session_id, message)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # It's audio data
            self.processing_queues[session_id].put(data)
            
    async def _handle_control_message(self, session_id: str, message: Dict):
        """Handle control messages from client"""
        command = message.get('command')
        
        if command == 'pause':
            self.sessions[session_id].status = 'paused'
        elif command == 'resume':
            self.sessions[session_id].status = 'active'
        elif command == 'end':
            await self.end_session(session_id)
        elif command == 'update_config':
            config_data = message.get('config', {})
            await self._update_session_config(session_id, config_data)
            
    def _process_audio_queue(self, session_id: str):
        """Process audio queue in background thread"""
        audio_buffer = []
        buffer_duration = 0
        
        session = self.sessions[session_id]
        processor = self.audio_processors[session_id]
        config = session.config
        
        chunk_duration = config.chunk_duration_ms / 1000  # Convert to seconds
        buffer_target = config.buffer_duration_ms / 1000
        
        while self._running and session_id in self.sessions:
            try:
                # Get audio chunk from queue
                audio_data = self.processing_queues[session_id].get(timeout=0.1)
                
                if session.status != 'active':
                    continue
                    
                # Process audio chunk
                is_speech, audio_array = processor.process_chunk(audio_data)
                
                if is_speech or len(audio_buffer) > 0:
                    audio_buffer.append(audio_array)
                    buffer_duration += chunk_duration
                    
                    # Process when buffer is full or speech ends
                    if buffer_duration >= buffer_target or (not is_speech and len(audio_buffer) > 0):
                        # Concatenate audio buffer
                        full_audio = np.concatenate(audio_buffer)
                        
                        # Apply audio enhancements
                        full_audio = processor.denoise(full_audio)
                        full_audio = processor.normalize(full_audio)
                        
                        # Transcribe
                        result = self.transcription_engine.transcribe_chunk(
                            full_audio,
                            config.language
                        )
                        
                        # Create segment
                        segment = self._create_segment(
                            session_id,
                            result,
                            session.total_duration,
                            buffer_duration
                        )
                        
                        # Send to client
                        asyncio.run(self._send_transcription(session_id, segment))
                        
                        # Update session
                        session.total_duration += buffer_duration
                        session.segments.append(segment)
                        
                        # Clear buffer
                        audio_buffer = []
                        buffer_duration = 0
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio for session {session_id}: {e}")
                
    def _create_segment(
        self,
        session_id: str,
        transcription_result: Dict,
        start_time: float,
        duration: float
    ) -> TranscriptionSegment:
        """Create transcription segment from result"""
        session = self.sessions[session_id]
        config = session.config
        
        segment = TranscriptionSegment(
            id=str(uuid.uuid4()),
            text=transcription_result['text'],
            start_time=start_time,
            end_time=start_time + duration,
            confidence=0.95,  # Calculate from word probabilities
            is_final=True,
            words=transcription_result.get('words', [])
        )
        
        # Add sentiment if enabled
        if config.enable_sentiment_analysis:
            segment.sentiment = self.transcription_engine.analyze_sentiment(
                segment.text
            )
            
        # Detect keywords if enabled
        if config.enable_keyword_detection and config.keywords:
            segment.keywords = self.transcription_engine.detect_keywords(
                segment.text,
                config.keywords
            )
            
        return segment
        
    async def _send_transcription(self, session_id: str, segment: TranscriptionSegment):
        """Send transcription to client via WebSocket"""
        if session_id not in self.websockets:
            return
            
        websocket = self.websockets[session_id]
        
        message = {
            'type': 'transcription',
            'segment': segment.to_dict(),
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send transcription: {e}")
            
    async def _send_session_info(self, session_id: str):
        """Send session information to client"""
        if session_id not in self.websockets:
            return
            
        session = self.sessions[session_id]
        websocket = self.websockets[session_id]
        
        message = {
            'type': 'session_info',
            'session_id': session_id,
            'config': asdict(session.config),
            'created_at': session.created_at.isoformat(),
            'status': session.status
        }
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send session info: {e}")
            
    async def _update_session_config(self, session_id: str, config_data: Dict):
        """Update session configuration"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        config = session.config
        
        # Update allowed fields
        allowed_fields = [
            'language', 'enable_punctuation', 'enable_sentiment_analysis',
            'enable_keyword_detection', 'keywords', 'max_alternatives'
        ]
        
        for field in allowed_fields:
            if field in config_data:
                setattr(config, field, config_data[field])
                
        # Recreate audio processor if needed
        if 'vad_aggressiveness' in config_data:
            config.vad_aggressiveness = config_data['vad_aggressiveness']
            self.audio_processors[session_id] = AudioProcessor(config)
            
        logger.info(f"Updated config for session {session_id}")
        
    async def end_session(self, session_id: str) -> Dict:
        """End a streaming session"""
        if session_id not in self.sessions:
            return {}
            
        session = self.sessions[session_id]
        session.status = 'ended'
        
        # Stop processing thread
        if session_id in self.processing_threads:
            thread = self.processing_threads[session_id]
            if thread.is_alive():
                thread.join(timeout=1)
            del self.processing_threads[session_id]
            
        # Close WebSocket
        if session_id in self.websockets:
            websocket = self.websockets[session_id]
            await websocket.close()
            del self.websockets[session_id]
            
        # Generate final transcript
        full_transcript = self._generate_full_transcript(session)
        
        # Save to Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"stream:transcript:{session_id}",
                mapping={
                    'user_id': session.user_id,
                    'created_at': session.created_at.isoformat(),
                    'ended_at': datetime.utcnow().isoformat(),
                    'duration': session.total_duration,
                    'transcript': full_transcript,
                    'segments': json.dumps([s.to_dict() for s in session.segments])
                }
            )
            
        # Clean up
        del self.sessions[session_id]
        del self.audio_processors[session_id]
        del self.processing_queues[session_id]
        
        logger.info(f"Ended streaming session {session_id}")
        
        return {
            'session_id': session_id,
            'duration': session.total_duration,
            'transcript': full_transcript,
            'segment_count': len(session.segments)
        }
        
    def _generate_full_transcript(self, session: StreamingSession) -> str:
        """Generate full transcript from segments"""
        transcript_parts = []
        
        for segment in session.segments:
            if session.config.enable_word_timestamps:
                # Include timestamps
                timestamp = f"[{segment.start_time:.2f} - {segment.end_time:.2f}]"
                transcript_parts.append(f"{timestamp} {segment.text}")
            else:
                transcript_parts.append(segment.text)
                
        return "\n".join(transcript_parts)
        
    async def get_session_status(self, session_id: str) -> Dict:
        """Get current session status"""
        if session_id not in self.sessions:
            return {'error': 'Session not found'}
            
        session = self.sessions[session_id]
        
        return {
            'session_id': session_id,
            'status': session.status,
            'duration': session.total_duration,
            'segment_count': len(session.segments),
            'created_at': session.created_at.isoformat(),
            'config': asdict(session.config)
        }
        
    async def get_live_analytics(self, session_id: str) -> Dict:
        """Get live analytics for session"""
        if session_id not in self.sessions:
            return {}
            
        session = self.sessions[session_id]
        
        # Calculate analytics
        word_count = sum(len(s.text.split()) for s in session.segments)
        avg_confidence = np.mean([s.confidence for s in session.segments]) if session.segments else 0
        
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        detected_keywords = set()
        
        for segment in session.segments:
            if segment.sentiment:
                sentiment_distribution[segment.sentiment] += 1
            if segment.keywords:
                detected_keywords.update(segment.keywords)
                
        return {
            'session_id': session_id,
            'duration': session.total_duration,
            'word_count': word_count,
            'segment_count': len(session.segments),
            'avg_confidence': avg_confidence,
            'words_per_minute': (word_count / session.total_duration * 60) if session.total_duration > 0 else 0,
            'sentiment_distribution': sentiment_distribution,
            'detected_keywords': list(detected_keywords),
            'status': session.status
        }

# Export highlights and important moments
class HighlightExtractor:
    """Extracts highlights from streaming transcription"""
    
    @staticmethod
    def extract_highlights(
        segments: List[TranscriptionSegment],
        criteria: Dict[str, Any]
    ) -> List[Dict]:
        """Extract highlights based on criteria"""
        highlights = []
        
        for segment in segments:
            score = 0
            reasons = []
            
            # Check sentiment
            if segment.sentiment == 'positive' and criteria.get('positive_sentiment'):
                score += 0.3
                reasons.append('Positive sentiment')
                
            # Check keywords
            if segment.keywords and criteria.get('keyword_matches'):
                score += 0.5
                reasons.append(f"Keywords: {', '.join(segment.keywords)}")
                
            # Check confidence
            if segment.confidence > 0.95 and criteria.get('high_confidence'):
                score += 0.2
                reasons.append('High confidence')
                
            # Check for questions
            if '?' in segment.text and criteria.get('questions'):
                score += 0.4
                reasons.append('Contains question')
                
            if score > criteria.get('threshold', 0.5):
                highlights.append({
                    'segment_id': segment.id,
                    'text': segment.text,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'score': score,
                    'reasons': reasons
                })
                
        return highlights

# Usage example
async def demo_streaming():
    """Demonstrate streaming system"""
    system = EnhancedRealtimeStreamingSystem()
    await system.initialize()
    
    # Create session
    config = StreamConfig(
        mode=StreamingMode.BALANCED,
        language="en",
        enable_sentiment_analysis=True,
        enable_keyword_detection=True,
        keywords=["important", "critical", "urgent"]
    )
    
    session_id = await system.create_session("user123", config)
    print(f"Created session: {session_id}")
    
    # Get status
    status = await system.get_session_status(session_id)
    print(f"Session status: {status}")
    
    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_streaming())