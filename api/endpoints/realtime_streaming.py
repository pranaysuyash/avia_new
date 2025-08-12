#!/usr/bin/env python3
"""
API endpoints for Real-time Streaming Transcription
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import json
import logging
import asyncio
from datetime import datetime
import hashlib
import time

from realtime_streaming_transcription import (
    RealtimeStreamingTranscription,
    StreamConfig,
    StreamingMode,
    TranscriptionEngine
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/streaming", tags=["streaming"])

# Global streaming system instance
streaming_system = RealtimeStreamingTranscription()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time streaming transcription"""
    
    await websocket.accept()
    
    try:
        # Wait for configuration
        config_data = await websocket.receive_json()
        
        # Create session configuration
        session_config = StreamConfig(
            session_id=session_id,
            language=config_data.get("language", "auto"),
            engine=TranscriptionEngine[config_data.get("engine", "FASTER_WHISPER")],
            mode=StreamingMode[config_data.get("mode", "VAD_BASED")],
            chunk_duration=config_data.get("chunk_duration", 1.0),
            overlap_duration=config_data.get("overlap_duration", 0.1),
            sample_rate=config_data.get("sample_rate", 16000),
            channels=config_data.get("channels", 1),
            vad_aggressiveness=config_data.get("vad_aggressiveness", 2),
            min_speech_duration=config_data.get("min_speech_duration", 0.3),
            max_silence_duration=config_data.get("max_silence_duration", 1.0),
            enable_punctuation=config_data.get("enable_punctuation", True),
            enable_formatting=config_data.get("enable_formatting", True),
            custom_vocabulary=config_data.get("custom_vocabulary", []),
            speaker_diarization=config_data.get("speaker_diarization", False)
        )
        
        # Start session
        session = await streaming_system.start_session(session_config)
        session.websocket = websocket
        
        # Send confirmation
        await websocket.send_json({
            "type": "session_started",
            "session_id": session_id,
            "config": {
                "language": session_config.language,
                "engine": session_config.engine.value,
                "mode": session_config.mode.value,
                "sample_rate": session_config.sample_rate
            }
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                # Audio data received
                await streaming_system.add_audio_chunk(session_id, data["bytes"])
                
            elif "text" in data:
                # Control message
                try:
                    control = json.loads(data["text"])
                    
                    if control.get("type") == "stop":
                        break
                    elif control.get("type") == "pause":
                        session.is_active = False
                        await websocket.send_json({"type": "paused"})
                    elif control.get("type") == "resume":
                        session.is_active = True
                        await websocket.send_json({"type": "resumed"})
                    elif control.get("type") == "update_config":
                        # Update configuration
                        if "language" in control:
                            session.config.language = control["language"]
                        if "speaker_diarization" in control:
                            session.config.speaker_diarization = control["speaker_diarization"]
                        await websocket.send_json({
                            "type": "config_updated",
                            "config": control
                        })
                        
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid control message"
                    })
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        
    finally:
        # Stop session if exists
        if session_id in streaming_system.sessions:
            result = await streaming_system.stop_session(session_id)
            
            # Send final transcript
            try:
                await websocket.send_json({
                    "type": "session_ended",
                    "transcript": result.get("transcript", ""),
                    "statistics": result.get("statistics", {})
                })
            except:
                pass


@router.post("/session/create")
async def create_session(config: Dict[str, Any]) -> JSONResponse:
    """Create a new streaming session"""
    
    try:
        # Generate session ID if not provided
        session_id = config.get("session_id")
        if not session_id:
            session_id = hashlib.md5(str(time.time()).encode()).hexdigest()
        
        # Create session configuration
        session_config = StreamConfig(
            session_id=session_id,
            language=config.get("language", "auto"),
            engine=TranscriptionEngine[config.get("engine", "FASTER_WHISPER")],
            mode=StreamingMode[config.get("mode", "VAD_BASED")],
            chunk_duration=config.get("chunk_duration", 1.0),
            sample_rate=config.get("sample_rate", 16000),
            speaker_diarization=config.get("speaker_diarization", False)
        )
        
        # Start session
        session = await streaming_system.start_session(session_config)
        
        return JSONResponse({
            "session_id": session_id,
            "status": "created",
            "config": {
                "language": session_config.language,
                "engine": session_config.engine.value,
                "mode": session_config.mode.value,
                "sample_rate": session_config.sample_rate
            },
            "websocket_url": f"ws://localhost:8000/api/v1/streaming/ws/{session_id}"
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/session/{session_id}/audio")
async def upload_audio(session_id: str, audio_data: bytes) -> JSONResponse:
    """Upload audio chunk to session"""
    
    if session_id not in streaming_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Add audio to session buffer
        await streaming_system.add_audio_chunk(session_id, audio_data)
        
        return JSONResponse({
            "status": "received",
            "session_id": session_id,
            "bytes_received": len(audio_data)
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/session/{session_id}/stop")
async def stop_session(session_id: str) -> JSONResponse:
    """Stop a streaming session and get final transcript"""
    
    if session_id not in streaming_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Stop session and get results
        result = await streaming_system.stop_session(session_id)
        
        return JSONResponse({
            "session_id": session_id,
            "transcript": result.get("transcript", ""),
            "segments": result.get("segments", []),
            "statistics": result.get("statistics", {})
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions")
async def list_sessions() -> JSONResponse:
    """List all active streaming sessions"""
    
    sessions = streaming_system.get_active_sessions()
    
    return JSONResponse({
        "sessions": sessions,
        "total": len(sessions)
    })


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str) -> JSONResponse:
    """Get status of a specific session"""
    
    if session_id not in streaming_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = streaming_system.sessions[session_id]
    
    return JSONResponse({
        "session_id": session_id,
        "is_active": session.is_active,
        "start_time": session.start_time.isoformat(),
        "duration": (datetime.now() - session.start_time).total_seconds(),
        "audio_duration": session.total_audio_duration,
        "segment_count": len(session.transcription_buffer),
        "participant_count": session.participant_count,
        "error_count": session.error_count,
        "config": {
            "language": session.config.language,
            "engine": session.config.engine.value,
            "mode": session.config.mode.value,
            "speaker_diarization": session.config.speaker_diarization
        }
    })


@router.get("/session/{session_id}/transcript")
async def get_partial_transcript(session_id: str, last_n: Optional[int] = None) -> JSONResponse:
    """Get partial transcript from active session"""
    
    if session_id not in streaming_system.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = streaming_system.sessions[session_id]
    
    # Get segments
    segments = session.transcription_buffer
    if last_n:
        segments = segments[-last_n:]
    
    # Format transcript
    transcript_text = " ".join([seg.text for seg in segments])
    
    formatted_segments = [
        {
            "text": seg.text,
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "confidence": seg.confidence,
            "is_final": seg.is_final,
            "speaker_id": seg.speaker_id,
            "language": seg.language
        }
        for seg in segments
    ]
    
    return JSONResponse({
        "session_id": session_id,
        "transcript": transcript_text,
        "segments": formatted_segments,
        "total_segments": len(session.transcription_buffer)
    })


@router.post("/batch/transcribe")
async def batch_transcribe(files: List[Dict[str, Any]], config: Dict[str, Any]) -> JSONResponse:
    """Batch transcribe multiple audio files"""
    
    try:
        results = []
        
        for file_info in files:
            # Create session for each file
            session_id = hashlib.md5(file_info["path"].encode()).hexdigest()
            
            session_config = StreamConfig(
                session_id=session_id,
                language=config.get("language", "auto"),
                engine=TranscriptionEngine[config.get("engine", "FASTER_WHISPER")],
                mode=StreamingMode.CONTINUOUS
            )
            
            # Process file (simplified - in production would stream file)
            session = await streaming_system.start_session(session_config)
            
            # Add file audio (would need actual file reading)
            # await streaming_system.add_audio_chunk(session_id, file_audio)
            
            # Stop and get results
            result = await streaming_system.stop_session(session_id)
            
            results.append({
                "file": file_info["path"],
                "transcript": result.get("transcript", ""),
                "statistics": result.get("statistics", {})
            })
        
        return JSONResponse({
            "results": results,
            "total_files": len(files)
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/engines")
async def list_engines() -> JSONResponse:
    """List available transcription engines"""
    
    engines = [
        {
            "name": engine.value,
            "description": f"Transcription using {engine.value}",
            "supported_languages": ["auto", "en", "es", "fr", "de", "zh", "ja", "ko"]
        }
        for engine in TranscriptionEngine
    ]
    
    return JSONResponse({"engines": engines})


@router.get("/modes")
async def list_streaming_modes() -> JSONResponse:
    """List available streaming modes"""
    
    modes = [
        {
            "name": mode.value,
            "description": f"Streaming in {mode.value} mode"
        }
        for mode in StreamingMode
    ]
    
    return JSONResponse({"modes": modes})