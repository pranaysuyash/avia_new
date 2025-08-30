"""
API endpoints for Advanced Noise Reduction System

FastAPI endpoints providing RESTful access to advanced noise reduction and audio
restoration capabilities including noise analysis, artifact removal, spectral
enhancement, and AI-powered reconstruction.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import numpy as np
import librosa
import soundfile as sf
import io
import tempfile
import os
import logging
from enum import Enum

# Import the noise reduction system
import sys
sys.path.append('..')
from advanced_noise_reduction_system import (
    AdvancedNoiseReductionSystem,
    RestorationSettings,
    NoiseType,
    ArtifactType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/noise-reduction", tags=["Advanced Noise Reduction"])

# Global system instance
noise_reduction_system = AdvancedNoiseReductionSystem()

# Pydantic models for API
class ProcessingModeEnum(str, Enum):
    adaptive = "adaptive"
    conservative = "conservative"
    aggressive = "aggressive"

class NoiseTypeEnum(str, Enum):
    broadband = "broadband"
    tonal = "tonal"
    impulsive = "impulsive"
    stationary = "stationary"
    non_stationary = "non_stationary"
    wind = "wind"
    traffic = "traffic"
    electrical = "electrical"

class ArtifactTypeEnum(str, Enum):
    clicks = "clicks"
    pops = "pops"
    crackles = "crackles"
    hums = "hums"
    buzzes = "buzzes"
    distortion = "distortion"
    clipping = "clipping"

class RestorationSettingsModel(BaseModel):
    noise_reduction_strength: float = Field(0.7, ge=0.0, le=1.0, description="Noise reduction strength (0-1)")
    preserve_speech_quality: bool = Field(True, description="Preserve speech quality during processing")
    artifact_removal_sensitivity: float = Field(0.8, ge=0.0, le=1.0, description="Artifact detection sensitivity (0-1)")
    spectral_enhancement: bool = Field(True, description="Apply spectral enhancement")
    dynamic_range_optimization: bool = Field(True, description="Optimize dynamic range")
    ai_reconstruction: bool = Field(True, description="Use AI-powered reconstruction")
    processing_mode: ProcessingModeEnum = Field(ProcessingModeEnum.adaptive, description="Processing mode")

class NoiseProfileModel(BaseModel):
    noise_type: NoiseTypeEnum
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_reduction: float = Field(ge=0.0, le=1.0)
    temporal_characteristics: Dict[str, float]
    frequency_bands: List[float]

class ArtifactDetectionModel(BaseModel):
    artifact_type: ArtifactTypeEnum
    count: int = Field(ge=0)
    locations: List[Dict[str, Any]]
    severity: float = Field(ge=0.0, le=1.0)

class ProcessingResultModel(BaseModel):
    processing_time: float = Field(ge=0.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    noise_reduction_applied: float = Field(ge=0.0, le=1.0)
    artifacts_removed: List[ArtifactTypeEnum]
    quality_improvement: Dict[str, Any]
    audio_duration: float = Field(ge=0.0)
    sample_rate: int = Field(gt=0)

class AudioAnalysisModel(BaseModel):
    noise_profile: NoiseProfileModel
    detected_artifacts: List[ArtifactDetectionModel]
    quality_metrics: Dict[str, float]
    recommendations: Dict[str, Any]

# Helper functions
def load_audio_from_upload(file: UploadFile) -> tuple[np.ndarray, int]:
    """Load audio from uploaded file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = file.file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Load audio
        audio, sr = librosa.load(tmp_file_path, sr=None)
        
        # Clean up
        os.unlink(tmp_file_path)
        
        return audio, sr
        
    except Exception as e:
        logger.error(f"Error loading audio: {e}")
        raise HTTPException(status_code=400, detail=f"Error loading audio file: {str(e)}")

def audio_to_bytes(audio: np.ndarray, sr: int, format: str = 'wav') -> bytes:
    """Convert audio array to bytes"""
    try:
        buffer = io.BytesIO()
        sf.write(buffer, audio, sr, format=format.upper())
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error converting audio to bytes: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

def convert_noise_profile_to_model(noise_profile) -> NoiseProfileModel:
    """Convert noise profile to Pydantic model"""
    return NoiseProfileModel(
        noise_type=NoiseTypeEnum(noise_profile.noise_type.value),
        confidence=noise_profile.confidence,
        recommended_reduction=noise_profile.recommended_reduction,
        temporal_characteristics=noise_profile.temporal_characteristics,
        frequency_bands=noise_profile.frequency_profile.tolist()[:10]  # First 10 bands for API
    )

def convert_artifacts_to_models(artifacts: Dict) -> List[ArtifactDetectionModel]:
    """Convert detected artifacts to Pydantic models"""
    artifact_models = []
    
    for artifact_type, locations in artifacts.items():
        # Calculate severity based on number of detections
        severity = min(len(locations) / 10.0, 1.0)  # Normalize to 0-1
        
        # Convert locations to serializable format
        serializable_locations = []
        for location in locations[:5]:  # Limit to first 5 for API response
            if isinstance(location, (list, tuple)):
                if len(location) == 2:
                    serializable_locations.append({"start": location[0], "end": location[1]})
                else:
                    serializable_locations.append({"indices": location})
            elif isinstance(location, (int, float)):
                serializable_locations.append({"frequency": location})
            else:
                serializable_locations.append({"value": str(location)})
        
        artifact_models.append(ArtifactDetectionModel(
            artifact_type=ArtifactTypeEnum(artifact_type.value),
            count=len(locations),
            locations=serializable_locations,
            severity=severity
        ))
    
    return artifact_models

# API Endpoints

@router.post("/analyze", response_model=AudioAnalysisModel)
async def analyze_audio(
    file: UploadFile = File(..., description="Audio file to analyze"),
):
    """
    Analyze audio for noise characteristics and artifacts
    
    Performs comprehensive analysis of uploaded audio including:
    - Noise type detection and profiling
    - Artifact detection (clicks, pops, hums, etc.)
    - Quality metrics calculation
    - Processing recommendations
    """
    try:
        # Load audio
        audio, sr = load_audio_from_upload(file)
        
        if len(audio) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Analyze noise profile
        noise_profile = noise_reduction_system.noise_reducer.analyze_noise_profile(audio, sr)
        
        # Detect artifacts
        artifacts = noise_reduction_system.artifact_remover.detect_artifacts(audio, sr)
        
        # Calculate quality metrics
        quality_metrics = {
            "rms_energy": float(np.sqrt(np.mean(audio**2))),
            "peak_amplitude": float(np.max(np.abs(audio))),
            "duration_seconds": float(len(audio) / sr),
            "sample_rate": int(sr),
            "dynamic_range_db": float(20 * np.log10(np.max(np.abs(audio)) / (np.sqrt(np.mean(audio**2)) + 1e-10)))
        }
        
        # Generate recommendations
        recommendations = {
            "recommended_noise_reduction": noise_profile.recommended_reduction,
            "processing_priority": "high" if len(artifacts) > 3 else "medium" if len(artifacts) > 0 else "low",
            "suggested_settings": {
                "noise_reduction_strength": noise_profile.recommended_reduction,
                "artifact_removal_sensitivity": 0.8 if len(artifacts) > 0 else 0.5,
                "spectral_enhancement": len(artifacts) > 0 or noise_profile.confidence > 0.7
            }
        }
        
        return AudioAnalysisModel(
            noise_profile=convert_noise_profile_to_model(noise_profile),
            detected_artifacts=convert_artifacts_to_models(artifacts),
            quality_metrics=quality_metrics,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/process", response_model=ProcessingResultModel)
async def process_audio(
    file: UploadFile = File(..., description="Audio file to process"),
    settings: str = Form(..., description="JSON string of restoration settings"),
    return_audio: bool = Form(False, description="Whether to return processed audio")
):
    """
    Process audio with noise reduction and restoration
    
    Applies comprehensive audio processing including:
    - Adaptive noise reduction
    - Artifact removal
    - Spectral enhancement
    - Dynamic range optimization
    - AI-powered reconstruction
    """
    try:
        # Parse settings
        import json
        settings_dict = json.loads(settings)
        restoration_settings = RestorationSettings(**settings_dict)
        
        # Load audio
        audio, sr = load_audio_from_upload(file)
        
        if len(audio) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Process audio
        result = noise_reduction_system.process_audio(audio, sr, restoration_settings)
        
        # Store processed audio in session/cache if needed for download
        if return_audio:
            # In a real implementation, you'd store this in a cache/database
            # For now, we'll include it in the response headers or separate endpoint
            pass
        
        return ProcessingResultModel(
            processing_time=result.processing_time,
            confidence_score=result.confidence_score,
            noise_reduction_applied=result.noise_reduction_applied,
            artifacts_removed=[ArtifactTypeEnum(art.value) for art in result.artifacts_removed],
            quality_improvement=result.quality_improvement,
            audio_duration=len(audio) / sr,
            sample_rate=sr
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid settings JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio processing: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/process-and-download")
async def process_and_download_audio(
    file: UploadFile = File(..., description="Audio file to process"),
    settings: str = Form(..., description="JSON string of restoration settings"),
    output_format: str = Form("wav", description="Output audio format")
):
    """
    Process audio and return the processed audio file for download
    """
    try:
        # Parse settings
        import json
        settings_dict = json.loads(settings)
        restoration_settings = RestorationSettings(**settings_dict)
        
        # Load audio
        audio, sr = load_audio_from_upload(file)
        
        if len(audio) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Process audio
        result = noise_reduction_system.process_audio(audio, sr, restoration_settings)
        
        # Convert to bytes
        audio_bytes = audio_to_bytes(result.restored_audio, sr, output_format)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type=f"audio/{output_format}",
            headers={
                "Content-Disposition": f"attachment; filename=processed_audio.{output_format}",
                "X-Processing-Time": str(result.processing_time),
                "X-Confidence-Score": str(result.confidence_score),
                "X-Noise-Reduction": str(result.noise_reduction_applied)
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid settings JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio processing and download: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/presets")
async def get_processing_presets():
    """
    Get predefined processing presets for different scenarios
    """
    presets = {
        "podcast_cleanup": {
            "name": "Podcast Cleanup",
            "description": "Optimized for speech content with background noise",
            "settings": {
                "noise_reduction_strength": 0.7,
                "preserve_speech_quality": True,
                "artifact_removal_sensitivity": 0.8,
                "spectral_enhancement": True,
                "dynamic_range_optimization": True,
                "ai_reconstruction": False,
                "processing_mode": "adaptive"
            }
        },
        "music_restoration": {
            "name": "Music Restoration",
            "description": "Gentle processing for musical content",
            "settings": {
                "noise_reduction_strength": 0.5,
                "preserve_speech_quality": False,
                "artifact_removal_sensitivity": 0.6,
                "spectral_enhancement": True,
                "dynamic_range_optimization": False,
                "ai_reconstruction": True,
                "processing_mode": "conservative"
            }
        },
        "forensic_enhancement": {
            "name": "Forensic Enhancement",
            "description": "Maximum enhancement for forensic analysis",
            "settings": {
                "noise_reduction_strength": 0.9,
                "preserve_speech_quality": True,
                "artifact_removal_sensitivity": 1.0,
                "spectral_enhancement": True,
                "dynamic_range_optimization": True,
                "ai_reconstruction": True,
                "processing_mode": "aggressive"
            }
        },
        "broadcast_ready": {
            "name": "Broadcast Ready",
            "description": "Professional broadcast standards",
            "settings": {
                "noise_reduction_strength": 0.6,
                "preserve_speech_quality": True,
                "artifact_removal_sensitivity": 0.9,
                "spectral_enhancement": True,
                "dynamic_range_optimization": True,
                "ai_reconstruction": False,
                "processing_mode": "adaptive"
            }
        }
    }
    
    return {"presets": presets}

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported audio formats for input and output
    """
    return {
        "input_formats": ["wav", "mp3", "flac", "m4a", "ogg", "aiff"],
        "output_formats": ["wav", "flac", "mp3"],
        "max_file_size_mb": 100,
        "max_duration_minutes": 30,
        "supported_sample_rates": [16000, 22050, 44100, 48000, 96000]
    }

@router.get("/system-info")
async def get_system_info():
    """
    Get information about the noise reduction system capabilities
    """
    return {
        "version": "1.0.0",
        "capabilities": {
            "noise_types": [nt.value for nt in NoiseType],
            "artifact_types": [at.value for at in ArtifactType],
            "processing_modes": [pm.value for pm in ProcessingModeEnum],
            "max_channels": 32,
            "real_time_processing": True,
            "ai_reconstruction": True,
            "spectral_enhancement": True
        },
        "performance": {
            "typical_processing_speed": "2-5x real-time",
            "memory_usage": "Low to moderate",
            "cpu_optimization": "Multi-threaded",
            "gpu_acceleration": "Optional"
        }
    }

@router.post("/batch-process")
async def batch_process_audio(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Multiple audio files to process"),
    settings: str = Form(..., description="JSON string of restoration settings")
):
    """
    Process multiple audio files in batch mode
    """
    try:
        # Parse settings
        import json
        settings_dict = json.loads(settings)
        restoration_settings = RestorationSettings(**settings_dict)
        
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
        
        # Start background processing
        batch_id = f"batch_{int(time.time())}"
        
        # In a real implementation, you'd use a task queue like Celery
        # For now, we'll return a batch ID and process synchronously
        
        results = []
        for i, file in enumerate(files):
            try:
                audio, sr = load_audio_from_upload(file)
                result = noise_reduction_system.process_audio(audio, sr, restoration_settings)
                
                results.append({
                    "file_index": i,
                    "filename": file.filename,
                    "status": "completed",
                    "processing_time": result.processing_time,
                    "confidence_score": result.confidence_score
                })
                
            except Exception as e:
                results.append({
                    "file_index": i,
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "batch_id": batch_id,
            "total_files": len(files),
            "results": results,
            "status": "completed"
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid settings JSON")
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Advanced Noise Reduction System",
        "version": "1.0.0",
        "timestamp": time.time()
    }

# Add the router to your main FastAPI app
# app.include_router(router)