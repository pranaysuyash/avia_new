"""
API Endpoints for Multi-Channel Audio Engine

FastAPI endpoints providing REST API access to multi-channel audio processing,
routing, spatial audio, and latency optimization capabilities.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import numpy as np
import json
import tempfile
import os
import time
from io import BytesIO
import wave

from multi_channel_audio_engine import (
    MultiChannelAudioEngine, MultiChannelAudio, AudioChannel, RoutingMatrix,
    ProcessingConfig, LatencyRequirements, AudioFormat, ChannelLayout,
    ProcessingMode, HighResolutionAudioProcessor, RealTimeMonitor,
    SpatialMetadata
)

# Create router
router = APIRouter(prefix="/api/v1/multichannel", tags=["Multi-Channel Audio"])

# Global engine instance
engine = MultiChannelAudioEngine(max_channels=32)
hr_processor = HighResolutionAudioProcessor()
monitor = RealTimeMonitor()

# Pydantic models for API
class AudioChannelModel(BaseModel):
    channel_id: int
    sample_rate: int
    bit_depth: int
    gain: float = 1.0
    muted: bool = False
    solo: bool = False
    pan: float = 0.0

class MultiChannelAudioModel(BaseModel):
    channel_count: int
    sample_rate: int
    bit_depth: int
    format: str
    channel_layout: str
    duration: float
    has_spatial_metadata: bool = False

class ProcessingConfigModel(BaseModel):
    mode: str = "realtime"
    buffer_size: int = Field(256, ge=64, le=4096)
    max_latency_ms: float = Field(10.0, ge=1.0, le=100.0)
    enable_monitoring: bool = True
    thread_count: int = Field(4, ge=1, le=16)
    enable_gpu_acceleration: bool = False
    quality_priority: bool = False

class LatencyRequirementsModel(BaseModel):
    max_input_latency_ms: float = Field(5.0, ge=0.1, le=50.0)
    max_processing_latency_ms: float = Field(3.0, ge=0.1, le=50.0)
    max_output_latency_ms: float = Field(2.0, ge=0.1, le=50.0)
    max_total_latency_ms: float = Field(10.0, ge=0.1, le=100.0)
    jitter_tolerance_ms: float = Field(1.0, ge=0.1, le=10.0)

class SpatialConfigModel(BaseModel):
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    orientation_azimuth: float = 0.0
    orientation_elevation: float = 0.0
    distance: float = Field(1.0, ge=0.1, le=100.0)
    room_size: float = Field(1.0, ge=0.1, le=10.0)
    reverb_level: float = Field(0.0, ge=0.0, le=1.0)

class RoutingMatrixModel(BaseModel):
    name: str
    input_channels: List[int]
    output_channels: List[int]
    routing_map: Dict[int, List[tuple]] = {}

class ChannelControlsModel(BaseModel):
    channel_id: int
    gain: float = Field(1.0, ge=0.0, le=2.0)
    muted: bool = False
    solo: bool = False
    pan: float = Field(0.0, ge=-1.0, le=1.0)

class AudioGenerationModel(BaseModel):
    channels: int = Field(4, ge=1, le=32)
    sample_rate: int = Field(48000, ge=8000, le=192000)
    duration: float = Field(2.0, ge=0.1, le=60.0)
    signal_type: str = "sine"
    bit_depth: int = Field(32, ge=16, le=32)

# In-memory storage for audio sessions
audio_sessions: Dict[str, MultiChannelAudio] = {}
routing_matrices: Dict[str, RoutingMatrix] = {}

def create_session_id() -> str:
    """Create unique session ID"""
    return f"session_{int(time.time() * 1000)}"

def numpy_to_audio_channel(data: np.ndarray, channel_id: int, sample_rate: int, bit_depth: int) -> AudioChannel:
    """Convert numpy array to AudioChannel"""
    return AudioChannel(
        channel_id=channel_id,
        data=data.astype(np.float32),
        sample_rate=sample_rate,
        bit_depth=bit_depth
    )

def audio_channel_to_dict(channel: AudioChannel) -> Dict[str, Any]:
    """Convert AudioChannel to dictionary"""
    return {
        "channel_id": channel.channel_id,
        "sample_rate": channel.sample_rate,
        "bit_depth": channel.bit_depth,
        "gain": channel.gain,
        "muted": channel.muted,
        "solo": channel.solo,
        "pan": channel.pan,
        "data_length": len(channel.data)
    }

def multichannel_audio_to_dict(audio: MultiChannelAudio) -> Dict[str, Any]:
    """Convert MultiChannelAudio to dictionary"""
    return {
        "channel_count": audio.channel_count,
        "sample_rate": audio.sample_rate,
        "bit_depth": audio.bit_depth,
        "format": audio.format.value,
        "channel_layout": audio.channel_layout.value,
        "duration": audio.duration,
        "channels": [audio_channel_to_dict(ch) for ch in audio.channels],
        "has_spatial_metadata": audio.spatial_metadata is not None,
        "processing_operations": len(audio.processing_history.operations)
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "engine_max_channels": engine.max_channels,
        "active_sessions": len(audio_sessions),
        "routing_matrices": len(routing_matrices)
    }

@router.post("/generate-audio")
async def generate_test_audio(config: AudioGenerationModel):
    """Generate test audio for demonstration"""
    try:
        session_id = create_session_id()
        
        # Generate test signals
        samples = int(config.sample_rate * config.duration)
        t = np.linspace(0, config.duration, samples)
        
        channel_data = []
        for i in range(config.channels):
            if config.signal_type == "sine":
                frequency = 440 * (2 ** (i / 12))  # Musical intervals
                signal = np.sin(2 * np.pi * frequency * t) * 0.3
            elif config.signal_type == "noise":
                signal = np.random.normal(0, 0.1, samples)
            elif config.signal_type == "sweep":
                f_start = 20 + i * 100
                f_end = f_start + 1000
                signal = np.sin(2 * np.pi * (f_start + (f_end - f_start) * t / config.duration) * t) * 0.3
            else:
                signal = np.zeros(samples)
            
            channel_data.append(signal)
        
        # Create multi-channel audio
        audio = engine.create_multichannel_audio(
            channel_data, config.sample_rate, config.bit_depth,
            AudioFormat.FLOAT_32, ChannelLayout.CUSTOM
        )
        
        # Store in session
        audio_sessions[session_id] = audio
        
        return {
            "session_id": session_id,
            "audio_info": multichannel_audio_to_dict(audio),
            "message": f"Generated {config.channels}-channel test audio"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

@router.get("/sessions/{session_id}")
async def get_audio_session(session_id: str):
    """Get audio session information"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    audio = audio_sessions[session_id]
    return {
        "session_id": session_id,
        "audio_info": multichannel_audio_to_dict(audio)
    }

@router.get("/sessions")
async def list_audio_sessions():
    """List all active audio sessions"""
    sessions = []
    for session_id, audio in audio_sessions.items():
        sessions.append({
            "session_id": session_id,
            "audio_info": multichannel_audio_to_dict(audio)
        })
    
    return {
        "active_sessions": len(sessions),
        "sessions": sessions
    }

@router.delete("/sessions/{session_id}")
async def delete_audio_session(session_id: str):
    """Delete audio session"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    del audio_sessions[session_id]
    return {"message": f"Session {session_id} deleted"}

@router.post("/sessions/{session_id}/process")
async def process_audio(session_id: str, config: ProcessingConfigModel):
    """Process audio with specified configuration"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Convert config to internal format
        processing_config = ProcessingConfig(
            mode=ProcessingMode(config.mode),
            buffer_size=config.buffer_size,
            max_latency_ms=config.max_latency_ms,
            enable_monitoring=config.enable_monitoring,
            thread_count=config.thread_count,
            enable_gpu_acceleration=config.enable_gpu_acceleration,
            quality_priority=config.quality_priority
        )
        
        # Process audio
        start_time = time.perf_counter()
        processed_audio = engine.process_multichannel_audio(audio, processing_config)
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Update session
        audio_sessions[session_id] = processed_audio
        
        return {
            "session_id": session_id,
            "processing_time_ms": processing_time,
            "audio_info": multichannel_audio_to_dict(processed_audio),
            "message": "Audio processing completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

@router.post("/sessions/{session_id}/channels/controls")
async def update_channel_controls(session_id: str, controls: List[ChannelControlsModel]):
    """Update channel controls (gain, mute, solo, pan)"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Update channel controls
        modified_channels = []
        for channel in audio.channels:
            # Find matching control
            control = next((c for c in controls if c.channel_id == channel.channel_id), None)
            
            if control:
                modified_channel = AudioChannel(
                    channel_id=channel.channel_id,
                    data=channel.data,
                    sample_rate=channel.sample_rate,
                    bit_depth=channel.bit_depth,
                    gain=control.gain,
                    muted=control.muted,
                    solo=control.solo,
                    pan=control.pan
                )
            else:
                modified_channel = channel
            
            modified_channels.append(modified_channel)
        
        # Create updated audio
        updated_audio = MultiChannelAudio(
            channels=modified_channels,
            sample_rate=audio.sample_rate,
            bit_depth=audio.bit_depth,
            format=audio.format,
            channel_layout=audio.channel_layout,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
        
        updated_audio.processing_history.add_operation(
            "channel_controls_update",
            {"updated_channels": len(controls)}
        )
        
        # Update session
        audio_sessions[session_id] = updated_audio
        
        return {
            "session_id": session_id,
            "updated_channels": len(controls),
            "audio_info": multichannel_audio_to_dict(updated_audio),
            "message": "Channel controls updated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Channel control update failed: {str(e)}")

@router.post("/routing-matrices")
async def create_routing_matrix(matrix: RoutingMatrixModel):
    """Create new routing matrix"""
    try:
        router_instance = engine.channel_router
        
        # Create routing matrix
        routing_matrix = router_instance.create_routing_matrix(
            matrix.name, matrix.input_channels, matrix.output_channels
        )
        
        # Add routing connections
        for input_ch, routes in matrix.routing_map.items():
            for output_ch, gain in routes:
                routing_matrix.add_route(input_ch, output_ch, gain)
        
        # Store matrix
        routing_matrices[matrix.name] = routing_matrix
        
        return {
            "matrix_name": matrix.name,
            "input_channels": len(matrix.input_channels),
            "output_channels": len(matrix.output_channels),
            "routing_connections": sum(len(routes) for routes in matrix.routing_map.values()),
            "message": f"Routing matrix '{matrix.name}' created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing matrix creation failed: {str(e)}")

@router.get("/routing-matrices")
async def list_routing_matrices():
    """List all routing matrices"""
    matrices = []
    for name, matrix in routing_matrices.items():
        matrices.append({
            "name": name,
            "input_channels": matrix.input_channels,
            "output_channels": matrix.output_channels,
            "routing_connections": len(matrix.routing_map)
        })
    
    return {
        "matrices_count": len(matrices),
        "matrices": matrices
    }

@router.post("/sessions/{session_id}/route")
async def apply_routing(session_id: str, matrix_name: str = Form(...)):
    """Apply routing matrix to audio session"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    if matrix_name not in routing_matrices:
        raise HTTPException(status_code=404, detail="Routing matrix not found")
    
    try:
        audio = audio_sessions[session_id]
        router_instance = engine.channel_router
        
        # Apply routing
        router_instance.routing_matrices[matrix_name] = routing_matrices[matrix_name]
        routed_audio = router_instance.route_audio(audio, matrix_name)
        
        # Update session
        audio_sessions[session_id] = routed_audio
        
        return {
            "session_id": session_id,
            "matrix_name": matrix_name,
            "original_channels": audio.channel_count,
            "routed_channels": routed_audio.channel_count,
            "audio_info": multichannel_audio_to_dict(routed_audio),
            "message": f"Routing matrix '{matrix_name}' applied"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing application failed: {str(e)}")

@router.post("/sessions/{session_id}/spatial")
async def apply_spatial_processing(session_id: str, spatial_config: SpatialConfigModel):
    """Apply spatial audio processing"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Convert config to dictionary
        config_dict = spatial_config.dict()
        
        # Apply spatial processing
        spatial_audio = engine.handle_spatial_audio(audio, config_dict)
        
        # Update session
        audio_sessions[session_id] = spatial_audio
        
        return {
            "session_id": session_id,
            "spatial_config": config_dict,
            "audio_info": multichannel_audio_to_dict(spatial_audio),
            "message": "Spatial audio processing applied"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spatial processing failed: {str(e)}")

@router.post("/sessions/{session_id}/optimize-latency")
async def optimize_latency(session_id: str, requirements: LatencyRequirementsModel):
    """Optimize audio for latency requirements"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Convert requirements
        latency_req = LatencyRequirements(
            max_input_latency_ms=requirements.max_input_latency_ms,
            max_processing_latency_ms=requirements.max_processing_latency_ms,
            max_output_latency_ms=requirements.max_output_latency_ms,
            max_total_latency_ms=requirements.max_total_latency_ms,
            jitter_tolerance_ms=requirements.jitter_tolerance_ms
        )
        
        # Optimize for latency
        optimized_stream = engine.optimize_latency(audio, latency_req)
        
        # Calculate theoretical latency
        buffer_latency_ms = (optimized_stream.buffer_size / audio.sample_rate) * 1000
        
        return {
            "session_id": session_id,
            "requirements": requirements.dict(),
            "optimized_buffer_size": optimized_stream.buffer_size,
            "estimated_latency_ms": buffer_latency_ms,
            "meets_requirements": buffer_latency_ms <= requirements.max_processing_latency_ms,
            "message": "Latency optimization completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Latency optimization failed: {str(e)}")

@router.post("/sessions/{session_id}/high-resolution")
async def convert_to_high_resolution(
    session_id: str,
    target_sample_rate: int = Form(96000),
    target_bit_depth: int = Form(32)
):
    """Convert audio to high-resolution format"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Convert to high-resolution
        start_time = time.perf_counter()
        hr_audio = hr_processor.convert_to_high_res(audio, target_sample_rate, target_bit_depth)
        conversion_time = (time.perf_counter() - start_time) * 1000
        
        # Validate lossless processing
        validation = hr_processor.validate_lossless_processing(audio, hr_audio)
        
        # Update session
        audio_sessions[session_id] = hr_audio
        
        return {
            "session_id": session_id,
            "original_specs": {
                "sample_rate": audio.sample_rate,
                "bit_depth": audio.bit_depth
            },
            "high_res_specs": {
                "sample_rate": hr_audio.sample_rate,
                "bit_depth": hr_audio.bit_depth
            },
            "conversion_time_ms": conversion_time,
            "validation": validation,
            "audio_info": multichannel_audio_to_dict(hr_audio),
            "message": "High-resolution conversion completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"High-resolution conversion failed: {str(e)}")

@router.get("/sessions/{session_id}/monitor")
async def monitor_audio_levels(session_id: str):
    """Get real-time audio monitoring information"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    try:
        audio = audio_sessions[session_id]
        
        # Get current levels
        levels = monitor.get_current_levels(audio)
        
        # Analyze frequency spectrum
        spectra = monitor.analyze_frequency_spectrum(audio)
        
        # Convert spectra to serializable format
        spectrum_data = {}
        for ch_id, spectrum in spectra.items():
            freqs = np.fft.rfftfreq(len(audio.channels[ch_id].data), 1/audio.sample_rate)
            
            # Find dominant frequencies
            peak_indices = np.argsort(spectrum)[-5:]  # Top 5 peaks
            dominant_freqs = [
                {"frequency": float(freqs[idx]), "magnitude": float(spectrum[idx])}
                for idx in peak_indices[::-1]
            ]
            
            spectrum_data[ch_id] = {
                "dominant_frequencies": dominant_freqs,
                "frequency_range": {"min": float(freqs[1]), "max": float(freqs[-1])},
                "spectrum_length": len(spectrum)
            }
        
        return {
            "session_id": session_id,
            "levels": levels,
            "spectrum_analysis": spectrum_data,
            "monitoring_timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio monitoring failed: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_processing_history(session_id: str):
    """Get processing history for audio session"""
    if session_id not in audio_sessions:
        raise HTTPException(status_code=404, detail="Audio session not found")
    
    audio = audio_sessions[session_id]
    
    operations = []
    for op in audio.processing_history.operations:
        operations.append({
            "operation": op["operation"],
            "timestamp": op["timestamp"],
            "parameters": op["parameters"]
        })
    
    return {
        "session_id": session_id,
        "total_operations": len(operations),
        "operations": operations,
        "processing_history_timestamp": audio.processing_history.timestamp
    }

@router.get("/performance")
async def get_performance_stats():
    """Get engine performance statistics"""
    stats = engine.get_performance_stats()
    
    return {
        "performance_stats": stats,
        "active_sessions": len(audio_sessions),
        "routing_matrices": len(routing_matrices),
        "engine_max_channels": engine.max_channels,
        "timestamp": time.time()
    }

@router.post("/performance/reset")
async def reset_performance_stats():
    """Reset engine performance statistics"""
    engine.reset_performance_stats()
    
    return {
        "message": "Performance statistics reset",
        "timestamp": time.time()
    }

@router.delete("/sessions")
async def clear_all_sessions():
    """Clear all audio sessions"""
    session_count = len(audio_sessions)
    audio_sessions.clear()
    
    return {
        "message": f"Cleared {session_count} audio sessions",
        "timestamp": time.time()
    }

@router.delete("/routing-matrices")
async def clear_routing_matrices():
    """Clear all routing matrices"""
    matrix_count = len(routing_matrices)
    routing_matrices.clear()
    
    return {
        "message": f"Cleared {matrix_count} routing matrices",
        "timestamp": time.time()
    }

# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid value: {str(exc)}"}
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )