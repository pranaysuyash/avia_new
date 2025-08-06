"""
REST API endpoints for Audio Preprocessing System (Task 83)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Tuple
import base64
import io
import logging
from datetime import datetime
import tempfile
import os
import json
import uuid
import numpy as np
import soundfile as sf

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from database.connection import get_db
from sqlalchemy.orm import Session

# Import preprocessing functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from audio_preprocessing_system_fast import AudioPreprocessorFast, AudioPreprocessingConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/audio")

# Global preprocessor instance
audio_preprocessor = AudioPreprocessorFast()

# Pydantic models
class AudioPreprocessingRequest(BaseModel):
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Audio preprocessing configuration options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "base64_encoded_audio_here",
                "config": {
                    "enable_noise_reduction": True,
                    "enable_normalization": True,
                    "remove_silence": True,
                    "target_sample_rate": 16000,
                    "normalization_method": "peak"
                }
            }
        }

class AudioPreprocessingResponse(BaseModel):
    task_id: str
    status: str
    processed_audio: Optional[str] = None  # Base64 encoded
    original_audio: Optional[str] = None   # Base64 encoded  
    operations_applied: List[str] = []
    quality_metrics: Dict[str, float] = {}
    processing_time: float = 0.0
    sample_rate: int = 16000
    duration: Dict[str, float] = {}  # original, processed
    metadata: Dict[str, Any] = {}
    message: Optional[str] = None

class BatchAudioProcessingRequest(BaseModel):
    audio_files: List[str] = Field(..., description="List of base64 encoded audio files")
    config: Dict[str, Any] = Field(default_factory=dict)
    
class AudioAnalysisRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    analysis_type: str = Field("quality", description="Type of analysis: quality, vad, segments")

# In-memory task storage
audio_processing_tasks = {}

@router.post("/preprocess", response_model=AudioPreprocessingResponse)
async def preprocess_audio(
    request: AudioPreprocessingRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("audio_processing"))
):
    """
    Preprocess audio for optimal transcription and analysis
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate input
        if not request.audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # Create preprocessing config
        config = AudioPreprocessingConfig(**request.config)
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(request.audio_data)
            
            # Save to temporary file for processing
            temp_file = tempfile.mktemp(suffix='.wav')
            with open(temp_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Load audio to validate
            audio_data, sample_rate = sf.read(temp_file)
            os.unlink(temp_file)  # Clean up temp file
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid audio data: {str(e)}")
        
        # Initialize task
        audio_processing_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now(),
            "user_id": current_user.get("user_id") if current_user else "anonymous",
            "original_duration": len(audio_data) / sample_rate
        }
        
        # Start background processing
        background_tasks.add_task(
            process_audio_background,
            task_id,
            audio_data,
            sample_rate,
            config,
            request.audio_data
        )
        
        # Track API usage
        await track_api_call("audio_preprocessing", current_user)
        
        return AudioPreprocessingResponse(
            task_id=task_id,
            status="processing",
            sample_rate=config.target_sample_rate,
            message="Audio preprocessing started"
        )
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preprocess/upload")
async def preprocess_uploaded_audio(
    file: UploadFile = File(...),
    config: str = Form("{}"),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("audio_processing"))
):
    """
    Preprocess an uploaded audio file
    """
    try:
        # Validate file type
        allowed_types = ["audio/wav", "audio/mp3", "audio/flac", "audio/m4a", "audio/ogg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file
        audio_data = await file.read()
        if len(audio_data) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Parse config
        try:
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid config JSON")
        
        # Create request
        request = AudioPreprocessingRequest(
            audio_data=audio_base64,
            config=config_dict
        )
        
        return await preprocess_audio(request, background_tasks, current_user, quota_check)
        
    except Exception as e:
        logger.error(f"Audio file upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/preprocess")
async def batch_preprocess_audio(
    request: BatchAudioProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("batch_processing"))
):
    """
    Process multiple audio files in batch
    """
    try:
        if len(request.audio_files) > 20:  # Limit batch size for audio
            raise HTTPException(status_code=400, detail="Batch size too large. Maximum 20 files.")
        
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Process each audio file
        for i, audio_data in enumerate(request.audio_files):
            task_id = f"{batch_id}_audio_{i:03d}"
            task_ids.append(task_id)
            
            # Validate audio data
            try:
                audio_bytes = base64.b64decode(audio_data)
                temp_file = tempfile.mktemp(suffix='.wav')
                with open(temp_file, 'wb') as f:
                    f.write(audio_bytes)
                
                audio_array, sr = sf.read(temp_file)
                os.unlink(temp_file)
                
            except Exception:
                continue
            
            # Create config
            config = AudioPreprocessingConfig(**request.config)
            
            # Initialize task
            audio_processing_tasks[task_id] = {
                "status": "processing",
                "started_at": datetime.now(),
                "batch_id": batch_id,
                "user_id": current_user.get("user_id") if current_user else "anonymous"
            }
            
            # Start processing
            background_tasks.add_task(
                process_audio_background,
                task_id,
                audio_array,
                sr,
                config,
                audio_data
            )
        
        await track_api_call("batch_audio_processing", current_user)
        
        return {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "status": "processing",
            "total_files": len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Batch audio processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_audio(
    request: AudioAnalysisRequest,
    current_user=Depends(get_current_user)
):
    """
    Analyze audio quality and characteristics
    """
    try:
        # Decode audio
        audio_bytes = base64.b64decode(request.audio_data)
        temp_file = tempfile.mktemp(suffix='.wav')
        
        with open(temp_file, 'wb') as f:
            f.write(audio_bytes)
        
        audio_data, sample_rate = sf.read(temp_file)
        os.unlink(temp_file)
        
        if request.analysis_type == "quality":
            # Quality analysis
            quality_metrics = audio_preprocessor._assess_audio_quality_fast(audio_data, sample_rate)
            
            return {
                "analysis_type": "quality",
                "duration": len(audio_data) / sample_rate,
                "sample_rate": sample_rate,
                "channels": 1 if len(audio_data.shape) == 1 else audio_data.shape[1],
                "quality_metrics": quality_metrics.to_dict(),
                "recommendations": _get_quality_recommendations(quality_metrics)
            }
            
        elif request.analysis_type == "vad":
            # Voice Activity Detection analysis
            config = AudioPreprocessingConfig(enable_vad=True)
            
            # Perform basic VAD
            frame_length = int(0.025 * sample_rate)
            hop_length = int(0.010 * sample_rate)
            
            frames = np.array([audio_data[i:i+frame_length] 
                             for i in range(0, len(audio_data) - frame_length, hop_length)])
            energy = np.mean(frames**2, axis=1)
            energy_db = 10 * np.log10(energy + 1e-10)
            
            threshold = np.percentile(energy_db, 30)  # Simple threshold
            voice_frames = energy_db > threshold
            
            # Calculate voice segments
            voice_segments = []
            in_voice = False
            start_time = 0
            
            for i, is_voice in enumerate(voice_frames):
                time = i * hop_length / sample_rate
                
                if is_voice and not in_voice:
                    start_time = time
                    in_voice = True
                elif not is_voice and in_voice:
                    voice_segments.append({"start": start_time, "end": time})
                    in_voice = False
            
            if in_voice:
                voice_segments.append({"start": start_time, "end": len(audio_data) / sample_rate})
            
            total_voice_time = sum(seg["end"] - seg["start"] for seg in voice_segments)
            total_time = len(audio_data) / sample_rate
            
            return {
                "analysis_type": "vad",
                "total_duration": total_time,
                "voice_duration": total_voice_time,
                "silence_duration": total_time - total_voice_time,
                "voice_ratio": total_voice_time / total_time * 100,
                "voice_segments": voice_segments[:50],  # Limit segments returned
                "segment_count": len(voice_segments)
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis type")
            
    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=AudioPreprocessingResponse)
async def get_audio_processing_status(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of an audio preprocessing task
    """
    if task_id not in audio_processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = audio_processing_tasks[task_id]
    
    return AudioPreprocessingResponse(
        task_id=task_id,
        status=task["status"],
        processed_audio=task.get("processed_audio"),
        original_audio=task.get("original_audio"),
        operations_applied=task.get("operations_applied", []),
        quality_metrics=task.get("quality_metrics", {}),
        processing_time=task.get("processing_time", 0.0),
        sample_rate=task.get("sample_rate", 16000),
        duration=task.get("duration", {}),
        metadata=task.get("metadata", {}),
        message=task.get("message")
    )

@router.get("/presets")
async def get_audio_configuration_presets():
    """
    Get available audio preprocessing configuration presets
    """
    presets = {
        "transcription_optimized": {
            "target_sample_rate": 16000,
            "enable_noise_reduction": True,
            "noise_reduction_strength": 0.8,
            "enable_normalization": True,
            "normalization_method": "peak",
            "remove_silence": True,
            "silence_threshold": -35.0,
            "enable_high_pass_filter": True,
            "high_pass_cutoff": 80.0,
            "enable_low_pass_filter": True,
            "low_pass_cutoff": 8000.0
        },
        "podcast_quality": {
            "target_sample_rate": 44100,
            "enable_noise_reduction": True,
            "noise_reduction_strength": 0.6,
            "enable_normalization": True,
            "normalization_method": "rms",
            "remove_silence": False,
            "enable_high_pass_filter": True,
            "high_pass_cutoff": 60.0
        },
        "phone_quality": {
            "target_sample_rate": 8000,
            "enable_noise_reduction": True,
            "noise_reduction_strength": 0.9,
            "enable_normalization": True,
            "remove_silence": True,
            "silence_threshold": -30.0,
            "enable_high_pass_filter": True,
            "high_pass_cutoff": 300.0,
            "enable_low_pass_filter": True,
            "low_pass_cutoff": 3400.0
        },
        "fast_processing": {
            "target_sample_rate": 16000,
            "enable_noise_reduction": False,
            "enable_normalization": True,
            "normalization_method": "peak",
            "remove_silence": True,
            "silence_threshold": -40.0
        }
    }
    
    return {"presets": presets}

# Background processing function
async def process_audio_background(
    task_id: str, 
    audio_data: np.ndarray, 
    sample_rate: int,
    config: AudioPreprocessingConfig, 
    original_audio_data: str
):
    """
    Background task for audio processing
    """
    try:
        # Update task status
        audio_processing_tasks[task_id]["status"] = "processing"
        
        # Process audio
        result = audio_preprocessor.preprocess_audio((audio_data, sample_rate), config)
        
        # Encode processed audio
        temp_file = tempfile.mktemp(suffix='.wav')
        sf.write(temp_file, result.processed_audio, result.sample_rate)
        
        with open(temp_file, 'rb') as f:
            processed_audio_bytes = f.read()
        
        processed_audio_base64 = base64.b64encode(processed_audio_bytes).decode('utf-8')
        os.unlink(temp_file)
        
        # Update task with results
        audio_processing_tasks[task_id].update({
            "status": "completed",
            "processed_audio": processed_audio_base64,
            "original_audio": original_audio_data,
            "operations_applied": result.operations_applied,
            "quality_metrics": result.quality_metrics.to_dict(),
            "processing_time": result.processing_time,
            "sample_rate": result.sample_rate,
            "duration": {
                "original": len(result.original_audio) / result.original_sample_rate,
                "processed": len(result.processed_audio) / result.sample_rate
            },
            "metadata": result.metadata,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        # Update task with error
        audio_processing_tasks[task_id].update({
            "status": "failed",
            "message": str(e),
            "failed_at": datetime.now()
        })
        logger.error(f"Background audio processing failed for task {task_id}: {e}")

def _get_quality_recommendations(quality_metrics) -> List[str]:
    """Generate quality improvement recommendations"""
    recommendations = []
    
    if quality_metrics.snr < 10:
        recommendations.append("Apply noise reduction - low signal-to-noise ratio detected")
    
    if quality_metrics.dynamic_range < 10:
        recommendations.append("Consider audio enhancement - low dynamic range")
    
    if quality_metrics.energy < 0.1:
        recommendations.append("Increase audio levels - signal appears too quiet")
    elif quality_metrics.energy > 0.8:
        recommendations.append("Reduce audio levels - signal may be too loud")
    
    if quality_metrics.peak_level > 0.95:
        recommendations.append("Check for clipping - peak levels are very high")
    
    if not recommendations:
        recommendations.append("Audio quality appears good")
    
    return recommendations

@router.get("/health")
async def audio_health_check():
    """
    Health check for audio preprocessing service
    """
    return {
        "status": "healthy",
        "service": "audio_preprocessing",
        "active_tasks": len([t for t in audio_processing_tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(audio_processing_tasks),
        "timestamp": datetime.now().isoformat()
    }