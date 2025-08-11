"""
Real-Time Transcription API Endpoints
REST API and WebSocket endpoints for real-time transcription functionality
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import real-time transcription system
from real_time_transcription import (
    RealTimeTranscriber, StreamingConfig, TranscriptionEngine, 
    StreamingMode, TranscriptionSegment, StreamingStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/realtime-transcription", tags=["Real-time Transcription"])

# Initialize components
real_time_transcriber = RealTimeTranscriber()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic models for API
class StreamingConfigAPI(BaseModel):
    """API request model for streaming configuration"""
    engine: str = Field(default="whisper_api", description="Transcription engine")
    language: str = Field(default="en", description="Language code")
    sample_rate: int = Field(default=16000, description="Audio sample rate", ge=8000, le=48000)
    chunk_duration: float = Field(default=1.0, description="Chunk duration in seconds", ge=0.1, le=5.0)
    buffer_duration: float = Field(default=5.0, description="Buffer duration in seconds", ge=1.0, le=30.0)
    overlap_duration: float = Field(default=0.5, description="Overlap duration in seconds", ge=0.0, le=2.0)
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold", ge=0.0, le=1.0)
    enable_vad: bool = Field(default=True, description="Enable voice activity detection")
    enable_speaker_diarization: bool = Field(default=False, description="Enable speaker diarization")
    streaming_mode: str = Field(default="continuous", description="Streaming mode")

class TranscriptionSegmentAPI(BaseModel):
    """API response model for transcription segments"""
    text: str
    start_time: float
    end_time: float
    confidence: float
    is_final: bool
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    engine: Optional[str] = None

class StreamingStatsAPI(BaseModel):
    """API response model for streaming statistics"""
    total_audio_duration: float
    total_processing_time: float
    segments_processed: int
    average_latency: float
    confidence_scores: List[float]
    error_count: int

class SessionCreateRequest(BaseModel):
    """API request model for creating a streaming session"""
    config: StreamingConfigAPI
    session_name: Optional[str] = Field(None, description="Optional session name")

class SessionResponse(BaseModel):
    """API response model for session operations"""
    session_id: str
    status: str
    config: StreamingConfigAPI
    created_at: datetime
    stats: Optional[StreamingStatsAPI] = None

def _convert_engine_enum(engine_str: str) -> TranscriptionEngine:
    """Convert string to TranscriptionEngine enum"""
    engine_map = {
        "whisper_api": TranscriptionEngine.WHISPER_API,
        "whisper_local": TranscriptionEngine.WHISPER_LOCAL,
        "deepspeech": TranscriptionEngine.DEEPSPEECH,
        "vosk": TranscriptionEngine.VOSK,
        "google_speech": TranscriptionEngine.GOOGLE_SPEECH,
        "azure_speech": TranscriptionEngine.AZURE_SPEECH
    }
    return engine_map.get(engine_str, TranscriptionEngine.WHISPER_API)

def _convert_streaming_mode_enum(mode_str: str) -> StreamingMode:
    """Convert string to StreamingMode enum"""
    mode_map = {
        "continuous": StreamingMode.CONTINUOUS,
        "push_to_talk": StreamingMode.PUSH_TO_TALK,
        "voice_activity": StreamingMode.VOICE_ACTIVITY
    }
    return mode_map.get(mode_str, StreamingMode.CONTINUOUS)

def _convert_config_to_internal(config_api: StreamingConfigAPI) -> StreamingConfig:
    """Convert API config to internal config"""
    return StreamingConfig(
        engine=_convert_engine_enum(config_api.engine),
        language=config_api.language,
        sample_rate=config_api.sample_rate,
        chunk_duration=config_api.chunk_duration,
        buffer_duration=config_api.buffer_duration,
        overlap_duration=config_api.overlap_duration,
        confidence_threshold=config_api.confidence_threshold,
        enable_vad=config_api.enable_vad,
        enable_speaker_diarization=config_api.enable_speaker_diarization,
        streaming_mode=_convert_streaming_mode_enum(config_api.streaming_mode)
    )

def _convert_segment_to_api(segment: TranscriptionSegment) -> TranscriptionSegmentAPI:
    """Convert internal segment to API response"""
    return TranscriptionSegmentAPI(
        text=segment.text,
        start_time=segment.start_time,
        end_time=segment.end_time,
        confidence=segment.confidence,
        is_final=segment.is_final,
        speaker_id=segment.speaker_id,
        language=segment.language,
        engine=segment.engine
    )

def _convert_stats_to_api(stats: StreamingStats) -> StreamingStatsAPI:
    """Convert internal stats to API response"""
    return StreamingStatsAPI(
        total_audio_duration=stats.total_audio_duration,
        total_processing_time=stats.total_processing_time,
        segments_processed=stats.segments_processed,
        average_latency=stats.average_latency,
        confidence_scores=stats.confidence_scores,
        error_count=stats.error_count
    )

@router.post("/sessions", response_model=SessionResponse)
async def create_streaming_session(
    request: SessionCreateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new real-time transcription session"""
    try:
        # Convert API config to internal config
        internal_config = _convert_config_to_internal(request.config)
        
        # Create session
        session_id = await real_time_transcriber.create_session(
            config=internal_config,
            user_id=current_user.get('user_id', 'unknown')
        )
        
        # Store session info
        active_sessions[session_id] = {
            'user_id': current_user.get('user_id'),
            'config': request.config,
            'created_at': datetime.now(),
            'status': 'created'
        }
        
        logger.info(f"Created streaming session {session_id} for user {current_user.get('user_id', 'unknown')}")
        
        return create_api_response(
            data=SessionResponse(
                session_id=session_id,
                status="created",
                config=request.config,
                created_at=datetime.now()
            ),
            message="Streaming session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating streaming session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create streaming session"
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_streaming_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get streaming session details"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_info = active_sessions[session_id]
        
        # Check if user owns the session
        if session_info['user_id'] != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Get session stats
        stats = await real_time_transcriber.get_session_stats(session_id)
        stats_api = _convert_stats_to_api(stats) if stats else None
        
        return create_api_response(
            data=SessionResponse(
                session_id=session_id,
                status=session_info['status'],
                config=session_info['config'],
                created_at=session_info['created_at'],
                stats=stats_api
            ),
            message="Session details retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )

@router.delete("/sessions/{session_id}")
async def delete_streaming_session(
    session_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a streaming session"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session_info = active_sessions[session_id]
        
        # Check if user owns the session
        if session_info['user_id'] != current_user.get('user_id'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Stop and cleanup session
        await real_time_transcriber.stop_session(session_id)
        
        # Remove from active sessions
        del active_sessions[session_id]
        
        # Close WebSocket connection if exists
        if session_id in active_connections:
            await active_connections[session_id].close()
            del active_connections[session_id]
        
        logger.info(f"Deleted streaming session {session_id}")
        
        return create_api_response(
            data={"session_id": session_id},
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

@router.get("/sessions")
async def list_streaming_sessions(
    current_user: dict = Depends(get_current_active_user)
):
    """List user's streaming sessions"""
    try:
        user_id = current_user.get('user_id')
        user_sessions = []
        
        for session_id, session_info in active_sessions.items():
            if session_info['user_id'] == user_id:
                # Get session stats
                stats = await real_time_transcriber.get_session_stats(session_id)
                stats_api = _convert_stats_to_api(stats) if stats else None
                
                user_sessions.append(SessionResponse(
                    session_id=session_id,
                    status=session_info['status'],
                    config=session_info['config'],
                    created_at=session_info['created_at'],
                    stats=stats_api
                ))
        
        return create_api_response(
            data={"sessions": user_sessions, "total": len(user_sessions)},
            message="Sessions retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )

@router.get("/engines")
async def get_available_engines():
    """Get available transcription engines"""
    return create_api_response(
        data={
            "engines": [
                {
                    "value": "whisper_api",
                    "label": "Whisper API",
                    "description": "OpenAI Whisper API (cloud-based, high accuracy)",
                    "supports_streaming": True,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                },
                {
                    "value": "whisper_local",
                    "label": "Whisper Local",
                    "description": "Local Whisper model (offline, good accuracy)",
                    "supports_streaming": True,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                },
                {
                    "value": "vosk",
                    "label": "Vosk",
                    "description": "Vosk speech recognition (offline, fast)",
                    "supports_streaming": True,
                    "languages": ["en", "es", "fr", "de", "ru"]
                },
                {
                    "value": "google_speech",
                    "label": "Google Speech-to-Text",
                    "description": "Google Cloud Speech API (cloud-based, high accuracy)",
                    "supports_streaming": True,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                },
                {
                    "value": "azure_speech",
                    "label": "Azure Speech Services",
                    "description": "Microsoft Azure Speech API (cloud-based, high accuracy)",
                    "supports_streaming": True,
                    "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
                }
            ],
            "streaming_modes": [
                {
                    "value": "continuous",
                    "label": "Continuous",
                    "description": "Continuous transcription of all audio"
                },
                {
                    "value": "push_to_talk",
                    "label": "Push to Talk",
                    "description": "Transcribe only when explicitly activated"
                },
                {
                    "value": "voice_activity",
                    "label": "Voice Activity Detection",
                    "description": "Transcribe only when voice is detected"
                }
            ]
        },
        message="Available engines retrieved successfully"
    )

@router.websocket("/ws/{session_id}")
async def websocket_transcription_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming and transcription"""
    await websocket.accept()
    
    try:
        # Verify session exists
        if session_id not in active_sessions:
            await websocket.send_json({
                "type": "error",
                "message": "Session not found"
            })
            await websocket.close()
            return
        
        # Store connection
        active_connections[session_id] = websocket
        active_sessions[session_id]['status'] = 'connected'
        
        logger.info(f"WebSocket connected for session {session_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "WebSocket connection established"
        })
        
        # Start transcription session
        await real_time_transcriber.start_session(session_id)
        active_sessions[session_id]['status'] = 'active'
        
        # Handle incoming messages
        async for message in websocket.iter_json():
            try:
                message_type = message.get("type")
                
                if message_type == "audio_data":
                    # Process audio data
                    audio_data = message.get("data")  # Base64 encoded audio
                    if audio_data:
                        # Decode and process audio
                        segments = await real_time_transcriber.process_audio_chunk(
                            session_id, audio_data
                        )
                        
                        # Send transcription results
                        for segment in segments:
                            segment_api = _convert_segment_to_api(segment)
                            await websocket.send_json({
                                "type": "transcription",
                                "data": segment_api.dict()
                            })
                
                elif message_type == "start_recording":
                    # Start recording signal
                    await websocket.send_json({
                        "type": "recording_started",
                        "message": "Recording started"
                    })
                
                elif message_type == "stop_recording":
                    # Stop recording signal
                    await websocket.send_json({
                        "type": "recording_stopped",
                        "message": "Recording stopped"
                    })
                
                elif message_type == "get_stats":
                    # Send current session stats
                    stats = await real_time_transcriber.get_session_stats(session_id)
                    if stats:
                        stats_api = _convert_stats_to_api(stats)
                        await websocket.send_json({
                            "type": "stats",
                            "data": stats_api.dict()
                        })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Error processing message"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Cleanup
        if session_id in active_connections:
            del active_connections[session_id]
        
        if session_id in active_sessions:
            active_sessions[session_id]['status'] = 'disconnected'
        
        # Stop transcription session
        try:
            await real_time_transcriber.stop_session(session_id)
        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "real_time_transcriber": "operational",
                "websocket_server": "operational"
            },
            "active_sessions": len(active_sessions),
            "active_connections": len(active_connections),
            "supported_engines": len([e for e in TranscriptionEngine])
        }
        
        return create_api_response(
            data=health_status,
            message="Real-time transcription service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=create_error_response(
                error="Service unhealthy",
                details=str(e)
            )
        )