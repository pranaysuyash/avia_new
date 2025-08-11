"""
Audio Enhancement Pipeline API Endpoints
REST API for comprehensive audio enhancement and processing
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List, Dict, Any, Union
import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import audio enhancement pipeline
from audio_enhancement_pipeline import (
    AudioEnhancementPipeline, EnhancementConfig, AudioQualityMetrics,
    NoiseReductionConfig, NormalizationConfig, AudioRepairConfig,
    EnhancementResult, AudioAnalysisResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio-enhancement", tags=["Audio Enhancement"])

# Initialize components
enhancement_pipeline = AudioEnhancementPipeline()

# Pydantic models for API
class EnhancementConfigAPI(BaseModel):
    """API request model for audio enhancement configuration"""
    enable_noise_reduction: bool = Field(default=True, description="Enable noise reduction")
    enable_normalization: bool = Field(default=True, description="Enable audio normalization")
    enable_compression: bool = Field(default=False, description="Enable dynamic range compression")
    enable_eq: bool = Field(default=False, description="Enable equalization")
    enable_repair: bool = Field(default=True, description="Enable audio repair")
    target_sample_rate: int = Field(default=16000, description="Target sample rate", ge=8000, le=48000)
    target_bit_depth: int = Field(default=16, description="Target bit depth")
    noise_reduction_strength: float = Field(default=0.7, description="Noise reduction strength", ge=0.0, le=1.0)
    normalization_target: float = Field(default=-20.0, description="Normalization target (dB)", ge=-60.0, le=0.0)
    compression_ratio: float = Field(default=2.0, description="Compression ratio", ge=1.0, le=10.0)
    high_pass_freq: float = Field(default=80.0, description="High-pass filter frequency", ge=20.0, le=1000.0)
    low_pass_freq: float = Field(default=8000.0, description="Low-pass filter frequency", ge=1000.0, le=20000.0)

class AudioQualityMetricsAPI(BaseModel):
    """API response model for audio quality metrics"""
    overall_quality_score: float
    snr_db: float
    thd_percent: float
    dynamic_range_db: float
    peak_level_db: float
    rms_level_db: float
    spectral_centroid: float
    spectral_rolloff: float
    zero_crossing_rate: float
    silence_ratio: float
    clipping_detected: bool
    noise_level_db: float
    frequency_response_score: float
    stereo_balance: Optional[float] = None

class EnhancementResultAPI(BaseModel):
    """API response model for enhancement results"""
    original_metrics: AudioQualityMetricsAPI
    enhanced_metrics: AudioQualityMetricsAPI
    improvement_score: float
    processing_time: float
    file_size_original: int
    file_size_enhanced: int
    enhancements_applied: List[str]
    recommendations: List[str]
    config_used: EnhancementConfigAPI

class AudioAnalysisAPI(BaseModel):
    """API response model for audio analysis"""
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    file_format: str
    file_size_bytes: int
    quality_metrics: AudioQualityMetricsAPI
    spectral_analysis: Dict[str, Any]
    temporal_analysis: Dict[str, Any]
    recommendations: List[str]

class BatchEnhancementAPI(BaseModel):
    """API response model for batch enhancement"""
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    total_processing_time: float

@router.post("/enhance", response_model=EnhancementResultAPI)
async def enhance_audio(
    audio_file: UploadFile = File(...),
    config: str = Form(...),
    return_enhanced_file: bool = Form(default=True),
    current_user: dict = Depends(get_current_active_user)
):
    """Enhance audio file with comprehensive processing pipeline"""
    try:
        # Parse config from JSON string
        import json
        config_dict = json.loads(config)
        request_config = EnhancementConfigAPI(**config_dict)
        
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Configure enhancement pipeline
            enhancement_config = EnhancementConfig(
                enable_noise_reduction=request_config.enable_noise_reduction,
                enable_normalization=request_config.enable_normalization,
                enable_compression=request_config.enable_compression,
                enable_eq=request_config.enable_eq,
                enable_repair=request_config.enable_repair,
                target_sample_rate=request_config.target_sample_rate,
                target_bit_depth=request_config.target_bit_depth,
                noise_reduction_strength=request_config.noise_reduction_strength,
                normalization_target=request_config.normalization_target,
                compression_ratio=request_config.compression_ratio,
                high_pass_freq=request_config.high_pass_freq,
                low_pass_freq=request_config.low_pass_freq
            )
            
            # Perform audio enhancement
            enhancement_result = await enhancement_pipeline.enhance_audio(
                input_file_path=temp_file_path,
                config=enhancement_config,
                return_enhanced_file=return_enhanced_file
            )
            
            # Convert quality metrics to API response
            def convert_metrics(metrics: AudioQualityMetrics) -> AudioQualityMetricsAPI:
                return AudioQualityMetricsAPI(
                    overall_quality_score=float(metrics.overall_quality_score),
                    snr_db=float(metrics.snr_db),
                    thd_percent=float(metrics.thd_percent),
                    dynamic_range_db=float(metrics.dynamic_range_db),
                    peak_level_db=float(metrics.peak_level_db),
                    rms_level_db=float(metrics.rms_level_db),
                    spectral_centroid=float(metrics.spectral_centroid),
                    spectral_rolloff=float(metrics.spectral_rolloff),
                    zero_crossing_rate=float(metrics.zero_crossing_rate),
                    silence_ratio=float(metrics.silence_ratio),
                    clipping_detected=bool(metrics.clipping_detected),
                    noise_level_db=float(metrics.noise_level_db),
                    frequency_response_score=float(metrics.frequency_response_score),
                    stereo_balance=float(metrics.stereo_balance) if metrics.stereo_balance is not None else None
                )
            
            # Convert to API response
            api_result = EnhancementResultAPI(
                original_metrics=convert_metrics(enhancement_result.original_metrics),
                enhanced_metrics=convert_metrics(enhancement_result.enhanced_metrics),
                improvement_score=float(enhancement_result.improvement_score),
                processing_time=float(enhancement_result.processing_time),
                file_size_original=enhancement_result.file_size_original,
                file_size_enhanced=enhancement_result.file_size_enhanced,
                enhancements_applied=enhancement_result.enhancements_applied,
                recommendations=enhancement_result.recommendations,
                config_used=request_config
            )
            
            logger.info(f"Audio enhancement completed for user {current_user.get('user_id', 'unknown')}: "
                       f"improvement score {enhancement_result.improvement_score:.2f}, "
                       f"{enhancement_result.processing_time:.2f}s processing time")
            
            # Store enhanced file path for download if requested
            if return_enhanced_file and hasattr(enhancement_result, 'enhanced_file_path'):
                # Store file path in session or database for later retrieval
                pass
            
            return create_api_response(
                data=api_result,
                message="Audio enhancement completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in audio enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in audio enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enhance audio"
        )

@router.post("/analyze", response_model=AudioAnalysisAPI)
async def analyze_audio(
    audio_file: UploadFile = File(...),
    detailed_analysis: bool = Form(default=True),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze audio file quality and characteristics"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Perform audio analysis
            analysis_result = await enhancement_pipeline.analyze_audio(
                file_path=temp_file_path,
                detailed_analysis=detailed_analysis
            )
            
            # Convert quality metrics to API response
            quality_metrics = AudioQualityMetricsAPI(
                overall_quality_score=float(analysis_result.quality_metrics.overall_quality_score),
                snr_db=float(analysis_result.quality_metrics.snr_db),
                thd_percent=float(analysis_result.quality_metrics.thd_percent),
                dynamic_range_db=float(analysis_result.quality_metrics.dynamic_range_db),
                peak_level_db=float(analysis_result.quality_metrics.peak_level_db),
                rms_level_db=float(analysis_result.quality_metrics.rms_level_db),
                spectral_centroid=float(analysis_result.quality_metrics.spectral_centroid),
                spectral_rolloff=float(analysis_result.quality_metrics.spectral_rolloff),
                zero_crossing_rate=float(analysis_result.quality_metrics.zero_crossing_rate),
                silence_ratio=float(analysis_result.quality_metrics.silence_ratio),
                clipping_detected=bool(analysis_result.quality_metrics.clipping_detected),
                noise_level_db=float(analysis_result.quality_metrics.noise_level_db),
                frequency_response_score=float(analysis_result.quality_metrics.frequency_response_score),
                stereo_balance=float(analysis_result.quality_metrics.stereo_balance) if analysis_result.quality_metrics.stereo_balance is not None else None
            )
            
            # Convert to API response
            api_result = AudioAnalysisAPI(
                duration_seconds=float(analysis_result.duration_seconds),
                sample_rate=analysis_result.sample_rate,
                channels=analysis_result.channels,
                bit_depth=analysis_result.bit_depth,
                file_format=analysis_result.file_format,
                file_size_bytes=analysis_result.file_size_bytes,
                quality_metrics=quality_metrics,
                spectral_analysis=analysis_result.spectral_analysis,
                temporal_analysis=analysis_result.temporal_analysis,
                recommendations=analysis_result.recommendations
            )
            
            logger.info(f"Audio analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"quality score {analysis_result.quality_metrics.overall_quality_score:.2f}")
            
            return create_api_response(
                data=api_result,
                message="Audio analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in audio analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze audio"
        )

@router.post("/batch-enhance")
async def batch_enhance_audio(
    files: List[UploadFile] = File(...),
    config: EnhancementConfigAPI = Depends(),
    current_user: dict = Depends(get_current_active_user)
):
    """Batch enhance multiple audio files"""
    try:
        if len(files) > 10:  # Limit batch size
            raise ValueError("Batch size cannot exceed 10 files")
        
        results = []
        total_processing_time = 0.0
        successful = 0
        failed = 0
        
        for i, file in enumerate(files):
            try:
                # Validate file type
                allowed_types = {
                    'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
                    'audio/ogg', 'audio/webm', 'audio/aac'
                }
                
                if file.content_type not in allowed_types:
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "error",
                        "error": f"Unsupported file type: {file.content_type}"
                    })
                    failed += 1
                    continue
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # Configure enhancement pipeline
                    enhancement_config = EnhancementConfig(
                        enable_noise_reduction=config.enable_noise_reduction,
                        enable_normalization=config.enable_normalization,
                        enable_compression=config.enable_compression,
                        enable_eq=config.enable_eq,
                        enable_repair=config.enable_repair,
                        target_sample_rate=config.target_sample_rate,
                        target_bit_depth=config.target_bit_depth,
                        noise_reduction_strength=config.noise_reduction_strength,
                        normalization_target=config.normalization_target,
                        compression_ratio=config.compression_ratio,
                        high_pass_freq=config.high_pass_freq,
                        low_pass_freq=config.low_pass_freq
                    )
                    
                    # Perform enhancement
                    enhancement_result = await enhancement_pipeline.enhance_audio(
                        input_file_path=temp_file_path,
                        config=enhancement_config,
                        return_enhanced_file=False
                    )
                    
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "success",
                        "result": {
                            "improvement_score": enhancement_result.improvement_score,
                            "processing_time": enhancement_result.processing_time,
                            "enhancements_applied": enhancement_result.enhancements_applied,
                            "original_quality": enhancement_result.original_metrics.overall_quality_score,
                            "enhanced_quality": enhancement_result.enhanced_metrics.overall_quality_score
                        }
                    })
                    
                    total_processing_time += enhancement_result.processing_time
                    successful += 1
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
            except Exception as e:
                logger.error(f"Error processing batch item {i}: {e}")
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e)
                })
                failed += 1
        
        # Calculate summary statistics
        successful_results = [r for r in results if r["status"] == "success"]
        avg_improvement = sum(r["result"]["improvement_score"] for r in successful_results) / len(successful_results) if successful_results else 0
        
        summary = {
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "average_improvement_score": avg_improvement,
            "total_processing_time": total_processing_time
        }
        
        api_result = BatchEnhancementAPI(
            results=results,
            summary=summary,
            total_processing_time=total_processing_time
        )
        
        logger.info(f"Batch audio enhancement completed for user {current_user.get('user_id', 'unknown')}: "
                   f"{successful} successful, {failed} failed")
        
        return create_api_response(
            data=api_result,
            message=f"Batch enhancement completed: {successful} successful, {failed} failed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in batch enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in batch enhancement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch audio enhancement"
        )

@router.post("/noise-reduction")
async def reduce_noise(
    audio_file: UploadFile = File(...),
    strength: float = Form(default=0.7, ge=0.0, le=1.0),
    stationary: bool = Form(default=True),
    current_user: dict = Depends(get_current_active_user)
):
    """Apply noise reduction to audio file"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Apply noise reduction
            result = await enhancement_pipeline.reduce_noise(
                input_file_path=temp_file_path,
                strength=strength,
                stationary=stationary
            )
            
            logger.info(f"Noise reduction completed for user {current_user.get('user_id', 'unknown')}")
            
            return create_api_response(
                data=result,
                message="Noise reduction completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in noise reduction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reduce noise"
        )

@router.post("/normalize")
async def normalize_audio(
    audio_file: UploadFile = File(...),
    target_db: float = Form(default=-20.0, ge=-60.0, le=0.0),
    current_user: dict = Depends(get_current_active_user)
):
    """Normalize audio file to target level"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Apply normalization
            result = await enhancement_pipeline.normalize_audio(
                input_file_path=temp_file_path,
                target_db=target_db
            )
            
            logger.info(f"Audio normalization completed for user {current_user.get('user_id', 'unknown')}")
            
            return create_api_response(
                data=result,
                message="Audio normalization completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in audio normalization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to normalize audio"
        )

@router.get("/presets")
async def get_enhancement_presets():
    """Get predefined enhancement presets"""
    return create_api_response(
        data={
            "presets": [
                {
                    "name": "Voice Recording",
                    "description": "Optimized for voice recordings and podcasts",
                    "config": {
                        "enable_noise_reduction": True,
                        "enable_normalization": True,
                        "enable_compression": True,
                        "enable_eq": True,
                        "enable_repair": True,
                        "target_sample_rate": 16000,
                        "noise_reduction_strength": 0.8,
                        "normalization_target": -16.0,
                        "compression_ratio": 3.0,
                        "high_pass_freq": 100.0,
                        "low_pass_freq": 8000.0
                    }
                },
                {
                    "name": "Music Recording",
                    "description": "Optimized for music and high-fidelity audio",
                    "config": {
                        "enable_noise_reduction": True,
                        "enable_normalization": True,
                        "enable_compression": False,
                        "enable_eq": False,
                        "enable_repair": True,
                        "target_sample_rate": 44100,
                        "noise_reduction_strength": 0.5,
                        "normalization_target": -14.0,
                        "compression_ratio": 1.5,
                        "high_pass_freq": 20.0,
                        "low_pass_freq": 20000.0
                    }
                },
                {
                    "name": "Phone Call",
                    "description": "Optimized for phone call recordings",
                    "config": {
                        "enable_noise_reduction": True,
                        "enable_normalization": True,
                        "enable_compression": True,
                        "enable_eq": True,
                        "enable_repair": True,
                        "target_sample_rate": 8000,
                        "noise_reduction_strength": 0.9,
                        "normalization_target": -12.0,
                        "compression_ratio": 4.0,
                        "high_pass_freq": 300.0,
                        "low_pass_freq": 3400.0
                    }
                },
                {
                    "name": "Broadcast",
                    "description": "Optimized for broadcast and streaming",
                    "config": {
                        "enable_noise_reduction": True,
                        "enable_normalization": True,
                        "enable_compression": True,
                        "enable_eq": True,
                        "enable_repair": True,
                        "target_sample_rate": 48000,
                        "noise_reduction_strength": 0.7,
                        "normalization_target": -23.0,
                        "compression_ratio": 2.5,
                        "high_pass_freq": 80.0,
                        "low_pass_freq": 15000.0
                    }
                },
                {
                    "name": "Minimal Processing",
                    "description": "Light enhancement preserving original character",
                    "config": {
                        "enable_noise_reduction": True,
                        "enable_normalization": True,
                        "enable_compression": False,
                        "enable_eq": False,
                        "enable_repair": True,
                        "target_sample_rate": 44100,
                        "noise_reduction_strength": 0.3,
                        "normalization_target": -18.0,
                        "compression_ratio": 1.2,
                        "high_pass_freq": 40.0,
                        "low_pass_freq": 18000.0
                    }
                }
            ]
        },
        message="Enhancement presets retrieved successfully"
    )

@router.get("/supported-formats")
async def get_supported_formats():
    """Get supported audio formats and their capabilities"""
    return create_api_response(
        data={
            "input_formats": [
                {
                    "format": "WAV",
                    "extensions": [".wav"],
                    "mime_types": ["audio/wav", "audio/wave"],
                    "description": "Uncompressed audio format, best quality",
                    "max_sample_rate": 192000,
                    "max_bit_depth": 32
                },
                {
                    "format": "MP3",
                    "extensions": [".mp3"],
                    "mime_types": ["audio/mpeg", "audio/mp3"],
                    "description": "Compressed audio format, widely supported",
                    "max_sample_rate": 48000,
                    "max_bit_depth": 16
                },
                {
                    "format": "FLAC",
                    "extensions": [".flac"],
                    "mime_types": ["audio/flac"],
                    "description": "Lossless compressed audio format",
                    "max_sample_rate": 192000,
                    "max_bit_depth": 32
                },
                {
                    "format": "M4A",
                    "extensions": [".m4a", ".aac"],
                    "mime_types": ["audio/m4a", "audio/aac"],
                    "description": "Apple audio format, good compression",
                    "max_sample_rate": 96000,
                    "max_bit_depth": 24
                },
                {
                    "format": "OGG",
                    "extensions": [".ogg"],
                    "mime_types": ["audio/ogg"],
                    "description": "Open source compressed format",
                    "max_sample_rate": 192000,
                    "max_bit_depth": 24
                }
            ],
            "output_formats": [
                {
                    "format": "WAV",
                    "description": "Recommended for highest quality",
                    "use_cases": ["Professional audio", "Further processing"]
                },
                {
                    "format": "MP3",
                    "description": "Good for general use and sharing",
                    "use_cases": ["Podcasts", "Voice recordings", "Web streaming"]
                },
                {
                    "format": "FLAC",
                    "description": "Lossless compression for archival",
                    "use_cases": ["Music archival", "High-quality storage"]
                }
            ]
        },
        message="Supported formats retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "enhancement_pipeline": "operational",
                "noise_reduction": "available" if enhancement_pipeline.noise_reduction_available else "limited",
                "audio_processing": "available",
                "format_conversion": "available"
            },
            "supported_formats": 5,
            "available_presets": 5
        }
        
        return create_api_response(
            data=health_status,
            message="Audio enhancement service is healthy"
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