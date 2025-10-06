"""
FastAPI endpoints for Intelligent Audio Enhancement and Clarity Optimization

This module provides RESTful API endpoints for the intelligent audio enhancement system,
enabling integration with external applications and services.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import numpy as np
import librosa
import soundfile as sf
import io
import tempfile
import os
import logging
from enum import Enum

# Import the enhancement system
from intelligent_audio_enhancement import (
    IntelligentAudioEnhancer, EnhancementMode, QualityMetric,
    SpectralEnhancementConfig, DynamicRangeConfig, SpeechClarityConfig,
    QualityAssessment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/audio-enhancement", tags=["Audio Enhancement"])

# Pydantic models for API
class EnhancementModeEnum(str, Enum):
    automatic = "automatic"
    speech_focused = "speech_focused"
    music_focused = "music_focused"
    broadcast = "broadcast"
    custom = "custom"

class UserPreferences(BaseModel):
    spectral_intensity: Optional[float] = Field(1.0, ge=0.1, le=3.0)
    dynamic_intensity: Optional[float] = Field(1.0, ge=0.1, le=3.0)
    clarity_intensity: Optional[float] = Field(1.0, ge=0.1, le=3.0)
    disable_spectral: Optional[bool] = False
    disable_dynamic: Optional[bool] = False
    disable_clarity: Optional[bool] = False
    target_lufs: Optional[float] = Field(-23.0, ge=-40.0, le=-10.0)
    compression_ratio: Optional[float] = Field(2.5, ge=1.0, le=10.0)

class EnhancementRequest(BaseModel):
    mode: EnhancementModeEnum = EnhancementModeEnum.automatic
    user_preferences: Optional[UserPreferences] = None

class QualityMetricResponse(BaseModel):
    signal_to_noise_ratio: float
    total_harmonic_distortion: float
    speech_clarity: float
    perceived_loudness: float
    dynamic_range: float
    frequency_balance: float

class QualityAssessmentResponse(BaseModel):
    overall_score: float
    metrics: QualityMetricResponse
    recommendations: List[str]
    processing_confidence: float

class EnhancementResponse(BaseModel):
    success: bool
    message: str
    initial_assessment: QualityAssessmentResponse
    final_assessment: QualityAssessmentResponse
    improvement: float
    processing_steps: List[str]
    audio_info: Dict[str, Any]

class AudioAnalysisResponse(BaseModel):
    success: bool
    message: str
    duration: float
    sample_rate: int
    channels: int
    quality_assessment: QualityAssessmentResponse

# Global enhancer instance
enhancer = IntelligentAudioEnhancer()

def convert_quality_assessment(assessment: QualityAssessment) -> QualityAssessmentResponse:
    """Convert internal QualityAssessment to API response model"""
    metrics = QualityMetricResponse(
        signal_to_noise_ratio=assessment.metrics.get(QualityMetric.SNR, 0.0),
        total_harmonic_distortion=assessment.metrics.get(QualityMetric.THD, 0.0),
        speech_clarity=assessment.metrics.get(QualityMetric.CLARITY, 0.0),
        perceived_loudness=assessment.metrics.get(QualityMetric.LOUDNESS, 0.0),
        dynamic_range=assessment.metrics.get(QualityMetric.DYNAMIC_RANGE, 0.0),
        frequency_balance=assessment.metrics.get(QualityMetric.FREQUENCY_BALANCE, 0.0)
    )
    
    return QualityAssessmentResponse(
        overall_score=assessment.overall_score,
        metrics=metrics,
        recommendations=assessment.recommendations,
        processing_confidence=assessment.processing_confidence
    )

def load_audio_from_upload(upload_file: UploadFile) -> tuple[np.ndarray, int]:
    """Load audio data from uploaded file"""
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = upload_file.file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Load audio using librosa
        audio_data, sample_rate = librosa.load(tmp_file_path, sr=None)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return audio_data, sample_rate
        
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        raise HTTPException(status_code=400, detail=f"Error loading audio file: {str(e)}")

def create_audio_response(audio_data: np.ndarray, sample_rate: int, 
                         filename: str = "enhanced_audio.wav") -> StreamingResponse:
    """Create streaming response for audio data"""
    try:
        # Convert audio to bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format='WAV')
        buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(buffer.read()),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error creating audio response: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating audio response: {str(e)}")

@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file and return quality assessment
    """
    try:
        logger.info(f"Analyzing audio file: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Load audio
        audio_data, sample_rate = load_audio_from_upload(file)
        
        # Perform quality assessment
        assessment = enhancer.quality_assessor.assess_quality(audio_data, sample_rate)
        
        # Prepare response
        response = AudioAnalysisResponse(
            success=True,
            message="Audio analysis completed successfully",
            duration=len(audio_data) / sample_rate,
            sample_rate=sample_rate,
            channels=1 if audio_data.ndim == 1 else audio_data.shape[1],
            quality_assessment=convert_quality_assessment(assessment)
        )
        
        logger.info(f"Audio analysis completed for {file.filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/enhance", response_model=EnhancementResponse)
async def enhance_audio_metadata(
    file: UploadFile = File(...),
    mode: EnhancementModeEnum = EnhancementModeEnum.automatic,
    spectral_intensity: Optional[float] = 1.0,
    dynamic_intensity: Optional[float] = 1.0,
    clarity_intensity: Optional[float] = 1.0,
    disable_spectral: Optional[bool] = False,
    disable_dynamic: Optional[bool] = False,
    disable_clarity: Optional[bool] = False,
    target_lufs: Optional[float] = -23.0,
    compression_ratio: Optional[float] = 2.5
):
    """
    Enhance uploaded audio file and return enhancement metadata
    """
    try:
        logger.info(f"Enhancing audio file: {file.filename} with mode: {mode}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Load audio
        audio_data, sample_rate = load_audio_from_upload(file)
        
        # Prepare user preferences
        user_preferences = {
            'spectral_intensity': spectral_intensity,
            'dynamic_intensity': dynamic_intensity,
            'clarity_intensity': clarity_intensity,
            'disable_spectral': disable_spectral,
            'disable_dynamic': disable_dynamic,
            'disable_clarity': disable_clarity,
            'target_lufs': target_lufs,
            'compression_ratio': compression_ratio
        }
        
        # Convert mode
        enhancement_mode = EnhancementMode(mode.value)
        
        # Perform enhancement
        results = enhancer.enhance_audio(
            audio_data, sample_rate, enhancement_mode, user_preferences
        )
        
        # Prepare response
        response = EnhancementResponse(
            success=True,
            message="Audio enhancement completed successfully",
            initial_assessment=convert_quality_assessment(results['initial_assessment']),
            final_assessment=convert_quality_assessment(results['final_assessment']),
            improvement=results['improvement'],
            processing_steps=results['processing_steps'],
            audio_info={
                'duration': len(audio_data) / sample_rate,
                'sample_rate': sample_rate,
                'channels': 1 if audio_data.ndim == 1 else audio_data.shape[1],
                'original_filename': file.filename
            }
        )
        
        logger.info(f"Audio enhancement completed for {file.filename}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio enhancement: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/enhance-download")
async def enhance_audio_download(
    file: UploadFile = File(...),
    mode: EnhancementModeEnum = EnhancementModeEnum.automatic,
    spectral_intensity: Optional[float] = 1.0,
    dynamic_intensity: Optional[float] = 1.0,
    clarity_intensity: Optional[float] = 1.0,
    disable_spectral: Optional[bool] = False,
    disable_dynamic: Optional[bool] = False,
    disable_clarity: Optional[bool] = False,
    target_lufs: Optional[float] = -23.0,
    compression_ratio: Optional[float] = 2.5
):
    """
    Enhance uploaded audio file and return enhanced audio for download
    """
    try:
        logger.info(f"Enhancing audio file for download: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Load audio
        audio_data, sample_rate = load_audio_from_upload(file)
        
        # Prepare user preferences
        user_preferences = {
            'spectral_intensity': spectral_intensity,
            'dynamic_intensity': dynamic_intensity,
            'clarity_intensity': clarity_intensity,
            'disable_spectral': disable_spectral,
            'disable_dynamic': disable_dynamic,
            'disable_clarity': disable_clarity,
            'target_lufs': target_lufs,
            'compression_ratio': compression_ratio
        }
        
        # Convert mode
        enhancement_mode = EnhancementMode(mode.value)
        
        # Perform enhancement
        results = enhancer.enhance_audio(
            audio_data, sample_rate, enhancement_mode, user_preferences
        )
        
        # Create filename for enhanced audio
        base_name = os.path.splitext(file.filename)[0]
        enhanced_filename = f"{base_name}_enhanced.wav"
        
        # Return enhanced audio as download
        return create_audio_response(
            results['enhanced_audio'], 
            sample_rate, 
            enhanced_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in audio enhancement download: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/modes")
async def get_enhancement_modes():
    """
    Get available enhancement modes and their descriptions
    """
    modes = {
        "automatic": {
            "name": "Automatic",
            "description": "AI-driven enhancement based on audio analysis",
            "use_cases": ["General audio improvement", "Unknown content type"]
        },
        "speech_focused": {
            "name": "Speech Focused",
            "description": "Optimized for voice recordings and podcasts",
            "use_cases": ["Podcasts", "Voice recordings", "Interviews"]
        },
        "music_focused": {
            "name": "Music Focused",
            "description": "Tailored for musical content and instruments",
            "use_cases": ["Music recordings", "Instrumental audio", "Songs"]
        },
        "broadcast": {
            "name": "Broadcast",
            "description": "Compliant with broadcast standards and regulations",
            "use_cases": ["Radio", "TV", "Streaming", "Professional broadcast"]
        },
        "custom": {
            "name": "Custom",
            "description": "Full control over all enhancement parameters",
            "use_cases": ["Specific requirements", "Fine-tuned control"]
        }
    }
    
    return {
        "success": True,
        "modes": modes
    }

@router.get("/quality-metrics")
async def get_quality_metrics_info():
    """
    Get information about quality metrics used in assessment
    """
    metrics = {
        "signal_to_noise_ratio": {
            "name": "Signal-to-Noise Ratio",
            "description": "Ratio of signal power to noise power",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Indicates audio clarity and noise levels"
        },
        "total_harmonic_distortion": {
            "name": "Total Harmonic Distortion",
            "description": "Measure of audio distortion and artifacts",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Lower distortion means cleaner audio"
        },
        "speech_clarity": {
            "name": "Speech Clarity",
            "description": "Intelligibility and clarity of speech content",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Critical for voice recordings and podcasts"
        },
        "perceived_loudness": {
            "name": "Perceived Loudness",
            "description": "Loudness level compliance with standards",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Ensures consistent playback levels"
        },
        "dynamic_range": {
            "name": "Dynamic Range",
            "description": "Difference between loudest and quietest parts",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Preserves musical and emotional expression"
        },
        "frequency_balance": {
            "name": "Frequency Balance",
            "description": "Even distribution of energy across frequencies",
            "range": "0.0 - 1.0 (higher is better)",
            "importance": "Ensures natural and balanced sound"
        }
    }
    
    return {
        "success": True,
        "metrics": metrics
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the audio enhancement service
    """
    try:
        # Test basic functionality
        test_audio = np.random.normal(0, 0.1, 1000)
        assessment = enhancer.quality_assessor.assess_quality(test_audio, 44100)
        
        return {
            "status": "healthy",
            "service": "Intelligent Audio Enhancement",
            "version": "1.0.0",
            "capabilities": [
                "Spectral Enhancement",
                "Dynamic Range Optimization", 
                "Speech Clarity Enhancement",
                "Quality Assessment"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Note: Exception handlers are typically added at the FastAPI app level, not router level
# These would be added in the main FastAPI application setup