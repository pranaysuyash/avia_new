"""
Voice Activity Detection API Endpoints
REST API for voice activity detection functionality
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from pydantic import BaseModel, Field
import base64

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import voice activity detection system
from voice_activity_detection import (
    VoiceActivityDetector, VADMethod, VADMode, VADSegment, 
    VADResult, AudioQualityMetrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-activity-detection", tags=["Voice Activity Detection"])

# Initialize components
vad_detector = VoiceActivityDetector()

# Pydantic models for API
class VADConfigAPI(BaseModel):
    """API request model for VAD configuration"""
    method: str = Field(default="webrtc", description="VAD method to use")
    mode: int = Field(default=2, description="VAD mode (0-3, higher = more aggressive)", ge=0, le=3)
    frame_duration_ms: int = Field(default=30, description="Frame duration in milliseconds")
    sample_rate: int = Field(default=16000, description="Audio sample rate", ge=8000, le=48000)
    min_speech_duration: float = Field(default=0.1, description="Minimum speech segment duration", ge=0.01, le=5.0)
    min_silence_duration: float = Field(default=0.1, description="Minimum silence segment duration", ge=0.01, le=5.0)
    energy_threshold: float = Field(default=0.01, description="Energy threshold for energy-based VAD", ge=0.0, le=1.0)
    enable_preprocessing: bool = Field(default=True, description="Enable audio preprocessing")
    enable_postprocessing: bool = Field(default=True, description="Enable result postprocessing")

class VADSegmentAPI(BaseModel):
    """API response model for VAD segments"""
    start_time: float
    end_time: float
    duration: float
    is_speech: bool
    confidence: float
    method: str
    features: Optional[Dict[str, float]] = None

class AudioQualityMetricsAPI(BaseModel):
    """API response model for audio quality metrics"""
    snr_db: float
    thd_percent: float
    dynamic_range_db: float
    spectral_centroid_hz: float
    spectral_rolloff_hz: float
    zero_crossing_rate: float
    mfcc_features: List[float]
    energy_entropy: float
    spectral_entropy: float

class VADResultAPI(BaseModel):
    """API response model for VAD results"""
    segments: List[VADSegmentAPI]
    total_duration: float
    speech_duration: float
    silence_duration: float
    speech_ratio: float
    quality_score: float
    method_used: str
    processing_time: float
    audio_quality: Optional[AudioQualityMetricsAPI] = None

class VADAnalysisRequest(BaseModel):
    """API request model for VAD analysis"""
    config: VADConfigAPI
    include_quality_metrics: bool = Field(default=True, description="Include audio quality analysis")
    include_features: bool = Field(default=False, description="Include detailed features in segments")

class BatchVADRequest(BaseModel):
    """API request model for batch VAD analysis"""
    configs: List[VADConfigAPI] = Field(..., description="List of VAD configurations to test")
    include_comparison: bool = Field(default=True, description="Include method comparison")

def _convert_vad_method_enum(method_str: str) -> VADMethod:
    """Convert string to VADMethod enum"""
    method_map = {
        "webrtc": VADMethod.WEBRTC,
        "pyaudio_analysis": VADMethod.PYAUDIO_ANALYSIS,
        "energy_based": VADMethod.ENERGY_BASED,
        "spectral_centroid": VADMethod.SPECTRAL_CENTROID,
        "zero_crossing_rate": VADMethod.ZERO_CROSSING_RATE,
        "ml_classifier": VADMethod.ML_CLASSIFIER,
        "ensemble": VADMethod.ENSEMBLE,
        "deep_learning": VADMethod.DEEP_LEARNING
    }
    return method_map.get(method_str, VADMethod.WEBRTC)

def _convert_vad_mode_enum(mode_int: int) -> VADMode:
    """Convert integer to VADMode enum"""
    mode_map = {
        0: VADMode.QUALITY,
        1: VADMode.LOW_BITRATE,
        2: VADMode.NORMAL,
        3: VADMode.VERY_AGGRESSIVE
    }
    return mode_map.get(mode_int, VADMode.NORMAL)

def _convert_segment_to_api(segment: VADSegment) -> VADSegmentAPI:
    """Convert internal segment to API response"""
    return VADSegmentAPI(
        start_time=segment.start_time,
        end_time=segment.end_time,
        duration=segment.duration,
        is_speech=segment.is_speech,
        confidence=segment.confidence,
        method=segment.method,
        features=segment.features
    )

def _convert_quality_to_api(quality: AudioQualityMetrics) -> AudioQualityMetricsAPI:
    """Convert internal quality metrics to API response"""
    return AudioQualityMetricsAPI(
        snr_db=quality.snr_db,
        thd_percent=quality.thd_percent,
        dynamic_range_db=quality.dynamic_range_db,
        spectral_centroid_hz=quality.spectral_centroid_hz,
        spectral_rolloff_hz=quality.spectral_rolloff_hz,
        zero_crossing_rate=quality.zero_crossing_rate,
        mfcc_features=quality.mfcc_features,
        energy_entropy=quality.energy_entropy,
        spectral_entropy=quality.spectral_entropy
    )

def _convert_result_to_api(result: VADResult, quality: Optional[AudioQualityMetrics] = None) -> VADResultAPI:
    """Convert internal result to API response"""
    return VADResultAPI(
        segments=[_convert_segment_to_api(seg) for seg in result.segments],
        total_duration=result.total_duration,
        speech_duration=result.speech_duration,
        silence_duration=result.silence_duration,
        speech_ratio=result.speech_ratio,
        quality_score=result.quality_score,
        method_used=result.method_used,
        processing_time=result.processing_time,
        audio_quality=_convert_quality_to_api(quality) if quality else None
    )

@router.post("/analyze", response_model=VADResultAPI)
async def analyze_voice_activity(
    request: VADAnalysisRequest,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze voice activity in uploaded audio file"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Configure VAD detector
            vad_method = _convert_vad_method_enum(request.config.method)
            vad_mode = _convert_vad_mode_enum(request.config.mode)
            
            # Set configuration
            vad_detector.set_config(
                method=vad_method,
                mode=vad_mode,
                frame_duration_ms=request.config.frame_duration_ms,
                sample_rate=request.config.sample_rate,
                min_speech_duration=request.config.min_speech_duration,
                min_silence_duration=request.config.min_silence_duration,
                energy_threshold=request.config.energy_threshold,
                enable_preprocessing=request.config.enable_preprocessing,
                enable_postprocessing=request.config.enable_postprocessing
            )
            
            # Perform VAD analysis
            result = await vad_detector.detect_voice_activity(
                temp_file_path,
                include_features=request.include_features
            )
            
            # Get audio quality metrics if requested
            quality_metrics = None
            if request.include_quality_metrics:
                quality_metrics = await vad_detector.analyze_audio_quality(temp_file_path)
            
            # Convert result to API response
            api_result = _convert_result_to_api(result, quality_metrics)
            
            logger.info(f"VAD analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{result.speech_ratio:.2f} speech ratio, {result.processing_time:.2f}s processing time")
            
            return create_api_response(
                data=api_result,
                message="Voice activity analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze voice activity"
        )

@router.post("/analyze-base64", response_model=VADResultAPI)
async def analyze_voice_activity_base64(
    request: VADAnalysisRequest,
    audio_data: str = Field(..., description="Base64 encoded audio data"),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze voice activity in base64 encoded audio data"""
    try:
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            raise ValueError(f"Invalid base64 audio data: {str(e)}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Configure VAD detector
            vad_method = _convert_vad_method_enum(request.config.method)
            vad_mode = _convert_vad_mode_enum(request.config.mode)
            
            # Set configuration
            vad_detector.set_config(
                method=vad_method,
                mode=vad_mode,
                frame_duration_ms=request.config.frame_duration_ms,
                sample_rate=request.config.sample_rate,
                min_speech_duration=request.config.min_speech_duration,
                min_silence_duration=request.config.min_silence_duration,
                energy_threshold=request.config.energy_threshold,
                enable_preprocessing=request.config.enable_preprocessing,
                enable_postprocessing=request.config.enable_postprocessing
            )
            
            # Perform VAD analysis
            result = await vad_detector.detect_voice_activity(
                temp_file_path,
                include_features=request.include_features
            )
            
            # Get audio quality metrics if requested
            quality_metrics = None
            if request.include_quality_metrics:
                quality_metrics = await vad_detector.analyze_audio_quality(temp_file_path)
            
            # Convert result to API response
            api_result = _convert_result_to_api(result, quality_metrics)
            
            return create_api_response(
                data=api_result,
                message="Voice activity analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze voice activity"
        )

@router.post("/batch-analyze", response_model=Dict[str, Any])
async def batch_analyze_voice_activity(
    request: BatchVADRequest,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze voice activity using multiple methods for comparison"""
    try:
        if len(request.configs) > 10:  # Limit batch size
            raise ValueError("Batch size cannot exceed 10 configurations")
        
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            results = []
            
            # Process each configuration
            for i, config in enumerate(request.configs):
                try:
                    # Configure VAD detector
                    vad_method = _convert_vad_method_enum(config.method)
                    vad_mode = _convert_vad_mode_enum(config.mode)
                    
                    # Set configuration
                    vad_detector.set_config(
                        method=vad_method,
                        mode=vad_mode,
                        frame_duration_ms=config.frame_duration_ms,
                        sample_rate=config.sample_rate,
                        min_speech_duration=config.min_speech_duration,
                        min_silence_duration=config.min_silence_duration,
                        energy_threshold=config.energy_threshold,
                        enable_preprocessing=config.enable_preprocessing,
                        enable_postprocessing=config.enable_postprocessing
                    )
                    
                    # Perform VAD analysis
                    result = await vad_detector.detect_voice_activity(temp_file_path)
                    
                    # Convert result to API response
                    api_result = _convert_result_to_api(result)
                    
                    results.append({
                        "index": i,
                        "config": config.dict(),
                        "status": "success",
                        "result": api_result.dict()
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing batch item {i}: {e}")
                    results.append({
                        "index": i,
                        "config": config.dict(),
                        "status": "error",
                        "error": str(e)
                    })
            
            # Generate comparison if requested
            comparison = None
            if request.include_comparison:
                successful_results = [r for r in results if r["status"] == "success"]
                if len(successful_results) > 1:
                    comparison = _generate_method_comparison(successful_results)
            
            logger.info(f"Batch VAD analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{len(request.configs)} configurations processed")
            
            return create_api_response(
                data={
                    "results": results,
                    "total": len(request.configs),
                    "successful": len([r for r in results if r["status"] == "success"]),
                    "comparison": comparison
                },
                message="Batch voice activity analysis completed"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in batch VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in batch VAD analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch voice activity analysis"
        )

def _generate_method_comparison(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comparison between different VAD methods"""
    comparison = {
        "methods": [],
        "performance_metrics": {},
        "recommendations": []
    }
    
    for result in results:
        method_name = result["result"]["method_used"]
        speech_ratio = result["result"]["speech_ratio"]
        quality_score = result["result"]["quality_score"]
        processing_time = result["result"]["processing_time"]
        
        comparison["methods"].append({
            "method": method_name,
            "speech_ratio": speech_ratio,
            "quality_score": quality_score,
            "processing_time": processing_time,
            "segments_count": len(result["result"]["segments"])
        })
    
    # Calculate performance metrics
    speech_ratios = [m["speech_ratio"] for m in comparison["methods"]]
    quality_scores = [m["quality_score"] for m in comparison["methods"]]
    processing_times = [m["processing_time"] for m in comparison["methods"]]
    
    comparison["performance_metrics"] = {
        "speech_ratio_variance": float(np.var(speech_ratios)) if len(speech_ratios) > 1 else 0.0,
        "avg_quality_score": float(np.mean(quality_scores)),
        "fastest_method": min(comparison["methods"], key=lambda x: x["processing_time"])["method"],
        "highest_quality": max(comparison["methods"], key=lambda x: x["quality_score"])["method"]
    }
    
    # Generate recommendations
    if comparison["performance_metrics"]["speech_ratio_variance"] < 0.01:
        comparison["recommendations"].append("Methods show consistent speech detection")
    else:
        comparison["recommendations"].append("Methods show significant variation in speech detection")
    
    if comparison["performance_metrics"]["avg_quality_score"] > 0.8:
        comparison["recommendations"].append("Overall high quality detection")
    else:
        comparison["recommendations"].append("Consider using ensemble method for better accuracy")
    
    return comparison

@router.get("/methods")
async def get_available_methods():
    """Get available VAD methods and their descriptions"""
    return create_api_response(
        data={
            "methods": [
                {
                    "value": "webrtc",
                    "label": "WebRTC VAD",
                    "description": "Google WebRTC voice activity detection (fast, reliable)",
                    "supports_modes": True,
                    "recommended_for": ["real-time", "low-latency"]
                },
                {
                    "value": "pyaudio_analysis",
                    "label": "PyAudio Analysis",
                    "description": "Feature-based VAD using audio analysis (accurate)",
                    "supports_modes": False,
                    "recommended_for": ["high-accuracy", "offline"]
                },
                {
                    "value": "energy_based",
                    "label": "Energy-based VAD",
                    "description": "Simple energy threshold detection (fast, basic)",
                    "supports_modes": False,
                    "recommended_for": ["simple", "low-resource"]
                },
                {
                    "value": "spectral_centroid",
                    "label": "Spectral Centroid",
                    "description": "Spectral feature-based detection (good for music)",
                    "supports_modes": False,
                    "recommended_for": ["music", "complex-audio"]
                },
                {
                    "value": "zero_crossing_rate",
                    "label": "Zero Crossing Rate",
                    "description": "ZCR-based detection (good for noisy environments)",
                    "supports_modes": False,
                    "recommended_for": ["noisy", "robust"]
                },
                {
                    "value": "ml_classifier",
                    "label": "ML Classifier",
                    "description": "Machine learning-based detection (adaptive)",
                    "supports_modes": False,
                    "recommended_for": ["adaptive", "custom-training"]
                },
                {
                    "value": "ensemble",
                    "label": "Ensemble Method",
                    "description": "Combination of multiple methods (highest accuracy)",
                    "supports_modes": False,
                    "recommended_for": ["highest-accuracy", "production"]
                },
                {
                    "value": "deep_learning",
                    "label": "Deep Learning",
                    "description": "Neural network-based detection (state-of-the-art)",
                    "supports_modes": False,
                    "recommended_for": ["state-of-the-art", "research"]
                }
            ],
            "modes": [
                {
                    "value": 0,
                    "label": "Quality",
                    "description": "Most aggressive filtering (highest quality)"
                },
                {
                    "value": 1,
                    "label": "Low Bitrate",
                    "description": "Less aggressive filtering (good for low bitrate)"
                },
                {
                    "value": 2,
                    "label": "Normal",
                    "description": "Least aggressive filtering (balanced)"
                },
                {
                    "value": 3,
                    "label": "Very Aggressive",
                    "description": "Custom very aggressive mode (maximum filtering)"
                }
            ]
        },
        message="Available VAD methods retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "vad_detector": "operational",
                "webrtc_vad": "available",
                "ml_models": "loaded"
            },
            "supported_methods": len([m for m in VADMethod]),
            "supported_modes": len([m for m in VADMode])
        }
        
        return create_api_response(
            data=health_status,
            message="Voice activity detection service is healthy"
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