"""
Spatial Audio Processing API Endpoints
FastAPI endpoints for spatial audio processing and format conversion

Requirements: 1.2, 1.5
Dependencies: spatial_audio_processor.py
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import tempfile
import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    from spatial_audio_processor import (
        SpatialAudioProcessor, SpatialFormat, SpatialProcessingMode,
        SpatialPosition, SpatialAnalysis
    )
    SPATIAL_PROCESSOR_AVAILABLE = True
except ImportError:
    SPATIAL_PROCESSOR_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/spatial-audio", tags=["Spatial Audio Processing"])

# Global processor instance
if SPATIAL_PROCESSOR_AVAILABLE:
    spatial_processor = SpatialAudioProcessor()
else:
    spatial_processor = None


# Pydantic models for API
class SpatialFormatResponse(BaseModel):
    """Response model for format detection"""
    detected_format: str
    channels: int
    sample_rate: int
    duration: float
    confidence: float = Field(default=1.0, description="Detection confidence score")


class SpatialAnalysisResponse(BaseModel):
    """Response model for spatial analysis"""
    format_detected: str
    channel_mapping: Dict[int, str]
    spatial_width: float
    spatial_depth: float
    spatial_height: float
    center_of_mass: Dict[str, float]
    immersion_score: float
    localization_accuracy: float
    spatial_artifacts: List[str]
    processing_time: float


class SpatialEnhancementConfig(BaseModel):
    """Configuration for spatial enhancement"""
    width_enhancement: bool = False
    depth_enhancement: bool = False
    height_enhancement: bool = False
    immersion_boost: bool = False
    localization_improvement: bool = False
    clarity_enhancement: bool = False
    enhancement_strength: float = Field(default=1.0, ge=0.1, le=2.0)
    room_simulation: str = Field(default="none", description="Room simulation type")
    crossfeed_amount: float = Field(default=0.3, ge=0.0, le=1.0)
    bass_management: bool = False
    phase_correction: bool = False
    preserve_original: bool = True
    real_time_mode: bool = False


class FormatConversionRequest(BaseModel):
    """Request model for format conversion"""
    target_format: str
    preserve_dynamics: bool = True
    normalize_levels: bool = False
    quality_mode: str = Field(default="standard", description="Quality mode: standard, high, broadcast")


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing"""
    operation: str = Field(description="Operation: detect, convert, enhance, analyze")
    target_format: Optional[str] = None
    enhancement_config: Optional[SpatialEnhancementConfig] = None
    parallel_processing: bool = True


class SpatialVisualizationResponse(BaseModel):
    """Response model for spatial visualization"""
    format: str
    spatial_dimensions: Dict[str, float]
    center_of_mass: Dict[str, float]
    quality_metrics: Dict[str, float]
    channel_mapping: Dict[int, str]
    artifacts: List[str]
    visualization_data: Dict[str, Any]


# Helper functions
def validate_processor():
    """Validate that the spatial processor is available"""
    if not SPATIAL_PROCESSOR_AVAILABLE or spatial_processor is None:
        raise HTTPException(
            status_code=503,
            detail="Spatial Audio Processor not available"
        )


def save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location"""
    try:
        suffix = Path(upload_file.filename).suffix if upload_file.filename else '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = upload_file.file.read()
            tmp_file.write(content)
            return tmp_file.name
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Failed to save uploaded file")


def cleanup_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


# API Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if SPATIAL_PROCESSOR_AVAILABLE else "unavailable",
        "processor_available": SPATIAL_PROCESSOR_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/detect-format", response_model=SpatialFormatResponse)
async def detect_spatial_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to analyze")
):
    """Detect spatial audio format"""
    validate_processor()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        start_time = datetime.now()
        
        # Detect format
        detected_format = await spatial_processor.detect_spatial_format(temp_file)
        
        # Get file info
        import soundfile as sf
        info = sf.info(temp_file)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SpatialFormatResponse(
            detected_format=detected_format.value,
            channels=info.channels,
            sample_rate=info.samplerate,
            duration=info.duration,
            confidence=1.0  # Simplified confidence score
        )
        
    except Exception as e:
        logger.error(f"Format detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Format detection failed: {str(e)}")


@router.post("/analyze", response_model=SpatialAnalysisResponse)
async def analyze_spatial_properties(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to analyze")
):
    """Analyze spatial audio properties"""
    validate_processor()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        start_time = datetime.now()
        
        # Perform spatial analysis
        analysis = await spatial_processor.analyze_spatial_properties(temp_file)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SpatialAnalysisResponse(
            format_detected=analysis.format_detected.value,
            channel_mapping=analysis.channel_mapping,
            spatial_width=analysis.spatial_width,
            spatial_depth=analysis.spatial_depth,
            spatial_height=analysis.spatial_height,
            center_of_mass={
                'x': analysis.center_of_mass.x,
                'y': analysis.center_of_mass.y,
                'z': analysis.center_of_mass.z
            },
            immersion_score=analysis.immersion_score,
            localization_accuracy=analysis.localization_accuracy,
            spatial_artifacts=analysis.spatial_artifacts,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Spatial analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Spatial analysis failed: {str(e)}")


@router.post("/convert")
async def convert_spatial_format(
    background_tasks: BackgroundTasks,
    conversion_request: FormatConversionRequest,
    file: UploadFile = File(..., description="Audio file to convert")
):
    """Convert spatial audio format"""
    validate_processor()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate target format
    try:
        target_format = SpatialFormat(conversion_request.target_format)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid target format: {conversion_request.target_format}"
        )
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Convert format
        converted_file = await spatial_processor.convert_spatial_format(
            temp_file, target_format
        )
        
        # Schedule cleanup of converted file after response
        background_tasks.add_task(cleanup_file, converted_file)
        
        # Return converted file
        return FileResponse(
            converted_file,
            media_type="audio/wav",
            filename=f"converted_{target_format.value}.wav"
        )
        
    except Exception as e:
        logger.error(f"Format conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Format conversion failed: {str(e)}")


@router.post("/enhance")
async def enhance_spatial_audio(
    background_tasks: BackgroundTasks,
    enhancement_config: SpatialEnhancementConfig,
    file: UploadFile = File(..., description="Audio file to enhance")
):
    """Enhance spatial audio properties"""
    validate_processor()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Convert config to dict
        config_dict = enhancement_config.dict()
        
        # Enhance audio
        enhanced_file = await spatial_processor.enhance_spatial_audio(
            temp_file, config_dict
        )
        
        # Schedule cleanup of enhanced file after response
        background_tasks.add_task(cleanup_file, enhanced_file)
        
        # Return enhanced file
        return FileResponse(
            enhanced_file,
            media_type="audio/wav",
            filename="enhanced_spatial_audio.wav"
        )
        
    except Exception as e:
        logger.error(f"Spatial enhancement failed: {e}")
        raise HTTPException(status_code=500, detail=f"Spatial enhancement failed: {str(e)}")


@router.post("/visualize", response_model=SpatialVisualizationResponse)
async def create_spatial_visualization(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to visualize")
):
    """Create spatial audio visualization"""
    validate_processor()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Create visualization
        viz_file = await spatial_processor.create_spatial_visualization(temp_file)
        
        # Load visualization data
        with open(viz_file, 'r') as f:
            viz_data = json.load(f)
        
        # Cleanup visualization file
        background_tasks.add_task(cleanup_file, viz_file)
        
        return SpatialVisualizationResponse(
            format=viz_data['format'],
            spatial_dimensions=viz_data['spatial_dimensions'],
            center_of_mass=viz_data['center_of_mass'],
            quality_metrics=viz_data['quality_metrics'],
            channel_mapping=viz_data['channel_mapping'],
            artifacts=viz_data['artifacts'],
            visualization_data=viz_data
        )
        
    except Exception as e:
        logger.error(f"Spatial visualization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Spatial visualization failed: {str(e)}")


@router.post("/batch-process")
async def batch_process_spatial_audio(
    background_tasks: BackgroundTasks,
    batch_request: BatchProcessingRequest,
    files: List[UploadFile] = File(..., description="Audio files to process")
):
    """Process multiple spatial audio files"""
    validate_processor()
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Too many files (max 10)")
    
    results = []
    temp_files = []
    
    try:
        # Save all uploaded files
        for file in files:
            if not file.filename:
                continue
            temp_file = save_uploaded_file(file)
            temp_files.append((file.filename, temp_file))
        
        # Schedule cleanup of all temp files
        for _, temp_file in temp_files:
            background_tasks.add_task(cleanup_file, temp_file)
        
        # Process files based on operation
        for filename, temp_file in temp_files:
            try:
                if batch_request.operation == "detect":
                    result = await spatial_processor.detect_spatial_format(temp_file)
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'result': {'format': result.value}
                    })
                
                elif batch_request.operation == "analyze":
                    analysis = await spatial_processor.analyze_spatial_properties(temp_file)
                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'result': {
                            'format': analysis.format_detected.value,
                            'spatial_width': analysis.spatial_width,
                            'spatial_depth': analysis.spatial_depth,
                            'immersion_score': analysis.immersion_score
                        }
                    })
                
                elif batch_request.operation == "enhance":
                    if batch_request.enhancement_config:
                        config_dict = batch_request.enhancement_config.dict()
                        enhanced_file = await spatial_processor.enhance_spatial_audio(
                            temp_file, config_dict
                        )
                        background_tasks.add_task(cleanup_file, enhanced_file)
                        results.append({
                            'filename': filename,
                            'status': 'success',
                            'result': {'enhanced_file': Path(enhanced_file).name}
                        })
                    else:
                        results.append({
                            'filename': filename,
                            'status': 'error',
                            'error': 'Enhancement config required'
                        })
                
                else:
                    results.append({
                        'filename': filename,
                        'status': 'error',
                        'error': f'Unknown operation: {batch_request.operation}'
                    })
            
            except Exception as e:
                results.append({
                    'filename': filename,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'operation': batch_request.operation,
            'total_files': len(files),
            'processed_files': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported spatial audio formats"""
    formats = []
    
    for format_enum in SpatialFormat:
        formats.append({
            'value': format_enum.value,
            'name': format_enum.name,
            'description': get_format_description(format_enum)
        })
    
    return {
        'supported_formats': formats,
        'total_formats': len(formats)
    }


@router.get("/capabilities")
async def get_processor_capabilities():
    """Get spatial audio processor capabilities"""
    validate_processor()
    
    return {
        'format_detection': True,
        'spatial_analysis': True,
        'format_conversion': True,
        'spatial_enhancement': True,
        'visualization': True,
        'batch_processing': True,
        'supported_formats': [f.value for f in SpatialFormat],
        'hrtf_available': hasattr(spatial_processor, 'hrtf_data'),
        'room_simulation': list(spatial_processor.room_responses.keys()) if spatial_processor else [],
        'max_batch_size': 10
    }


def get_format_description(format_enum: SpatialFormat) -> str:
    """Get description for spatial format"""
    descriptions = {
        SpatialFormat.STEREO: "Standard stereo with left and right channels",
        SpatialFormat.SURROUND_5_1: "5.1 surround sound with 6 channels",
        SpatialFormat.SURROUND_7_1: "7.1 surround sound with 8 channels",
        SpatialFormat.AMBISONICS_FOA: "First Order Ambisonics with 4 channels",
        SpatialFormat.AMBISONICS_HOA: "Higher Order Ambisonics with 9+ channels",
        SpatialFormat.BINAURAL: "Binaural audio optimized for headphones",
        SpatialFormat.QUAD: "Quadraphonic audio with 4 channels",
        SpatialFormat.DOLBY_ATMOS: "Object-based spatial audio format",
        SpatialFormat.DTS_X: "Object-based spatial audio format"
    }
    
    return descriptions.get(format_enum, "Unknown spatial format")


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP exception: {exc.detail}")
    return {"error": exc.detail, "status_code": exc.status_code}


# Startup event
@router.on_event("startup")
async def startup_event():
    """Initialize processor on startup"""
    if SPATIAL_PROCESSOR_AVAILABLE:
        logger.info("Spatial Audio Processing API initialized successfully")
    else:
        logger.warning("Spatial Audio Processor not available")


# Shutdown event
@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if spatial_processor:
        await spatial_processor.cleanup()
        logger.info("Spatial Audio Processor cleanup completed")