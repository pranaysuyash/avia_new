"""
Professional Audio Format Handler API Endpoints
FastAPI endpoints for comprehensive audio format handling and conversion

Requirements: 1.3
Dependencies: professional_audio_format_handler.py
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
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
import zipfile

try:
    from professional_audio_format_handler import (
        ProfessionalAudioFormatHandler, AudioFormat, AudioCodec,
        QualityLevel, ConversionMode, ConversionSettings,
        BatchProcessingJob, AudioMetadata, ConversionResult
    )
    FORMAT_HANDLER_AVAILABLE = True
except ImportError:
    FORMAT_HANDLER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/audio-format", tags=["Audio Format Handling"])

# Global handler instance
if FORMAT_HANDLER_AVAILABLE:
    format_handler = ProfessionalAudioFormatHandler()
else:
    format_handler = None


# Pydantic models for API
class AudioMetadataResponse(BaseModel):
    """Response model for audio metadata"""
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    peak_level: Optional[float] = None
    rms_level: Optional[float] = None
    dynamic_range: Optional[float] = None
    lufs: Optional[float] = None


class FormatDetectionResponse(BaseModel):
    """Response model for format detection"""
    detected_format: str
    metadata: AudioMetadataResponse
    processing_time: float


class ConversionSettingsRequest(BaseModel):
    """Request model for conversion settings"""
    target_format: str
    target_codec: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    quality_level: str = "standard"
    conversion_mode: str = "balanced"
    preserve_metadata: bool = True
    normalize_audio: bool = False
    apply_dithering: bool = True


class ConversionResultResponse(BaseModel):
    """Response model for conversion results"""
    success: bool
    original_format: Optional[str] = None
    target_format: Optional[str] = None
    original_size: Optional[int] = None
    converted_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    processing_time: Optional[float] = None
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing"""
    conversion_settings: ConversionSettingsRequest
    parallel_workers: int = Field(default=4, ge=1, le=8)
    output_directory_name: str = "converted_audio"


class BatchProcessingResponse(BaseModel):
    """Response model for batch processing"""
    job_id: str
    status: str
    total_files: int
    successful_conversions: int
    failed_conversions: int
    processing_time: float
    results: List[ConversionResultResponse]


class ValidationResponse(BaseModel):
    """Response model for audio validation"""
    is_valid: bool
    file_exists: bool
    format_detected: Optional[str] = None
    metadata: Optional[AudioMetadataResponse] = None
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = None


class FormatInfoResponse(BaseModel):
    """Response model for format information"""
    format: str
    codec: str
    supports_metadata: bool
    supports_multichannel: bool
    max_channels: int
    max_sample_rate: int
    max_bit_depth: int
    is_lossless: bool
    typical_bitrates: List[int]
    file_extensions: List[str]
    use_cases: List[str]


class ProcessingStatsResponse(BaseModel):
    """Response model for processing statistics"""
    total_conversions: int
    successful_conversions: int
    failed_conversions: int
    success_rate: float
    average_processing_time: float
    average_compression_ratio: float
    total_processing_time: float
    formats_processed: Dict[str, int]


# Helper functions
def validate_handler():
    """Validate that the format handler is available"""
    if not FORMAT_HANDLER_AVAILABLE or format_handler is None:
        raise HTTPException(
            status_code=503,
            detail="Professional Audio Format Handler not available"
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


def convert_metadata_to_response(metadata: AudioMetadata) -> AudioMetadataResponse:
    """Convert AudioMetadata to response model"""
    return AudioMetadataResponse(
        title=metadata.title,
        artist=metadata.artist,
        album=metadata.album,
        year=metadata.year,
        genre=metadata.genre,
        duration=metadata.duration,
        sample_rate=metadata.sample_rate,
        channels=metadata.channels,
        bit_depth=metadata.bit_depth,
        bitrate=metadata.bitrate,
        codec=metadata.codec,
        peak_level=metadata.peak_level,
        rms_level=metadata.rms_level,
        dynamic_range=metadata.dynamic_range,
        lufs=metadata.lufs
    )


def create_conversion_settings(request: ConversionSettingsRequest) -> ConversionSettings:
    """Create ConversionSettings from request"""
    return ConversionSettings(
        target_format=AudioFormat(request.target_format),
        target_codec=AudioCodec(request.target_codec) if request.target_codec else None,
        sample_rate=request.sample_rate,
        channels=request.channels,
        bit_depth=request.bit_depth,
        bitrate=request.bitrate,
        quality_level=QualityLevel(request.quality_level),
        conversion_mode=ConversionMode(request.conversion_mode),
        preserve_metadata=request.preserve_metadata,
        normalize_audio=request.normalize_audio,
        apply_dithering=request.apply_dithering
    )


# API Endpoints
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if FORMAT_HANDLER_AVAILABLE else "unavailable",
        "handler_available": FORMAT_HANDLER_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/detect-format", response_model=FormatDetectionResponse)
async def detect_audio_format(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to analyze")
):
    """Detect audio format and extract metadata"""
    validate_handler()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        start_time = datetime.now()
        
        # Detect format and extract metadata
        format_detected, metadata = await format_handler.detect_format(temp_file)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return FormatDetectionResponse(
            detected_format=format_detected.value,
            metadata=convert_metadata_to_response(metadata),
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Format detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Format detection failed: {str(e)}")


@router.post("/convert", response_model=ConversionResultResponse)
async def convert_audio_format(
    background_tasks: BackgroundTasks,
    conversion_settings: ConversionSettingsRequest,
    file: UploadFile = File(..., description="Audio file to convert"),
    return_file: bool = Query(False, description="Return converted file instead of metadata")
):
    """Convert audio file to different format"""
    validate_handler()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Create conversion settings
        settings = create_conversion_settings(conversion_settings)
        
        # Create output file
        output_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f'.{settings.target_format.value}'
        ).name
        
        # Perform conversion
        result = await format_handler.convert_format(temp_file, output_file, settings)
        
        if result.success and return_file:
            # Return the converted file
            background_tasks.add_task(cleanup_file, output_file)
            return FileResponse(
                output_file,
                media_type=f"audio/{settings.target_format.value}",
                filename=f"converted.{settings.target_format.value}"
            )
        else:
            # Return conversion metadata
            background_tasks.add_task(cleanup_file, output_file)
            
            return ConversionResultResponse(
                success=result.success,
                original_format=result.original_format.value if result.original_format else None,
                target_format=result.target_format.value if result.target_format else None,
                original_size=result.original_size,
                converted_size=result.converted_size,
                compression_ratio=result.compression_ratio,
                processing_time=result.processing_time,
                quality_metrics=result.quality_metrics,
                error_message=result.error_message,
                warnings=result.warnings
            )
        
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio conversion failed: {str(e)}")


@router.post("/batch-convert", response_model=BatchProcessingResponse)
async def batch_convert_audio(
    background_tasks: BackgroundTasks,
    batch_request: BatchProcessingRequest,
    files: List[UploadFile] = File(..., description="Audio files to convert")
):
    """Convert multiple audio files in batch"""
    validate_handler()
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 20:  # Limit batch size
        raise HTTPException(status_code=400, detail="Too many files (max 20)")
    
    # Save all uploaded files
    temp_files = []
    for file in files:
        if not file.filename:
            continue
        temp_file = save_uploaded_file(file)
        temp_files.append(temp_file)
        background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Create output directory
        output_dir = tempfile.mkdtemp(prefix=batch_request.output_directory_name + "_")
        background_tasks.add_task(cleanup_file, output_dir)
        
        # Create conversion settings
        settings = create_conversion_settings(batch_request.conversion_settings)
        
        # Create batch job
        job = BatchProcessingJob(
            job_id=f"batch_{len(temp_files)}_{settings.target_format.value}",
            input_files=temp_files,
            output_directory=output_dir,
            conversion_settings=settings,
            parallel_workers=batch_request.parallel_workers
        )
        
        # Process batch
        start_time = datetime.now()
        completed_job = await format_handler.batch_convert(job)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Convert results
        result_responses = []
        for result in completed_job.results:
            result_responses.append(ConversionResultResponse(
                success=result.success,
                original_format=result.original_format.value if result.original_format else None,
                target_format=result.target_format.value if result.target_format else None,
                original_size=result.original_size,
                converted_size=result.converted_size,
                compression_ratio=result.compression_ratio,
                processing_time=result.processing_time,
                quality_metrics=result.quality_metrics,
                error_message=result.error_message,
                warnings=result.warnings
            ))
        
        successful_conversions = sum(1 for r in completed_job.results if r.success)
        failed_conversions = len(completed_job.results) - successful_conversions
        
        return BatchProcessingResponse(
            job_id=completed_job.job_id,
            status=completed_job.status,
            total_files=len(completed_job.results),
            successful_conversions=successful_conversions,
            failed_conversions=failed_conversions,
            processing_time=processing_time,
            results=result_responses
        )
        
    except Exception as e:
        logger.error(f"Batch conversion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch conversion failed: {str(e)}")


@router.post("/validate", response_model=ValidationResponse)
async def validate_audio_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to validate")
):
    """Validate audio file and assess quality"""
    validate_handler()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        # Validate audio file
        validation_result = await format_handler.validate_audio_file(temp_file)
        
        # Calculate quality score if metadata is available
        quality_score = None
        metadata_response = None
        
        if validation_result.get('metadata'):
            metadata = validation_result['metadata']
            metadata_response = convert_metadata_to_response(metadata)
            quality_score = calculate_quality_score(metadata)
        
        return ValidationResponse(
            is_valid=validation_result['is_valid'],
            file_exists=validation_result['file_exists'],
            format_detected=validation_result.get('format_detected'),
            metadata=metadata_response,
            issues=validation_result['issues'],
            recommendations=validation_result['recommendations'],
            quality_score=quality_score
        )
        
    except Exception as e:
        logger.error(f"Audio validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio validation failed: {str(e)}")


@router.get("/formats", response_model=List[FormatInfoResponse])
async def get_supported_formats():
    """Get information about all supported audio formats"""
    validate_handler()
    
    try:
        supported_formats = await format_handler.get_supported_formats()
        format_responses = []
        
        for format_enum in supported_formats:
            format_info = await format_handler.get_format_info(format_enum)
            if format_info:
                use_cases = get_format_use_cases(format_enum)
                
                format_responses.append(FormatInfoResponse(
                    format=format_info.format.value,
                    codec=format_info.codec.value,
                    supports_metadata=format_info.supports_metadata,
                    supports_multichannel=format_info.supports_multichannel,
                    max_channels=format_info.max_channels,
                    max_sample_rate=format_info.max_sample_rate,
                    max_bit_depth=format_info.max_bit_depth,
                    is_lossless=format_info.is_lossless,
                    typical_bitrates=format_info.typical_bitrates,
                    file_extensions=format_info.file_extensions,
                    use_cases=use_cases
                ))
        
        return format_responses
        
    except Exception as e:
        logger.error(f"Failed to get format information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get format information: {str(e)}")


@router.get("/formats/{format_name}", response_model=FormatInfoResponse)
async def get_format_info(format_name: str):
    """Get detailed information about a specific audio format"""
    validate_handler()
    
    try:
        format_enum = AudioFormat(format_name.lower())
        format_info = await format_handler.get_format_info(format_enum)
        
        if not format_info:
            raise HTTPException(status_code=404, detail=f"Format {format_name} not found")
        
        use_cases = get_format_use_cases(format_enum)
        
        return FormatInfoResponse(
            format=format_info.format.value,
            codec=format_info.codec.value,
            supports_metadata=format_info.supports_metadata,
            supports_multichannel=format_info.supports_multichannel,
            max_channels=format_info.max_channels,
            max_sample_rate=format_info.max_sample_rate,
            max_bit_depth=format_info.max_bit_depth,
            is_lossless=format_info.is_lossless,
            typical_bitrates=format_info.typical_bitrates,
            file_extensions=format_info.file_extensions,
            use_cases=use_cases
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid format: {format_name}")
    except Exception as e:
        logger.error(f"Failed to get format info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get format info: {str(e)}")


@router.get("/recommendations/{use_case}")
async def get_conversion_recommendations(
    use_case: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Sample audio file for analysis")
):
    """Get conversion recommendations for specific use case"""
    validate_handler()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Save uploaded file
    temp_file = save_uploaded_file(file)
    background_tasks.add_task(cleanup_file, temp_file)
    
    try:
        recommendations = await format_handler.get_conversion_recommendations(temp_file, use_case)
        
        return {
            "use_case": use_case,
            "target_format": recommendations.target_format.value,
            "target_codec": recommendations.target_codec.value if recommendations.target_codec else None,
            "sample_rate": recommendations.sample_rate,
            "channels": recommendations.channels,
            "bit_depth": recommendations.bit_depth,
            "bitrate": recommendations.bitrate,
            "quality_level": recommendations.quality_level.value,
            "conversion_mode": recommendations.conversion_mode.value,
            "preserve_metadata": recommendations.preserve_metadata,
            "normalize_audio": recommendations.normalize_audio,
            "apply_dithering": recommendations.apply_dithering
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/statistics", response_model=ProcessingStatsResponse)
async def get_processing_statistics():
    """Get processing statistics"""
    validate_handler()
    
    try:
        stats = await format_handler.get_processing_statistics()
        
        return ProcessingStatsResponse(
            total_conversions=stats['total_conversions'],
            successful_conversions=stats['successful_conversions'],
            failed_conversions=stats['failed_conversions'],
            success_rate=stats['success_rate'],
            average_processing_time=stats['average_processing_time'],
            average_compression_ratio=stats['average_compression_ratio'],
            total_processing_time=stats['total_processing_time'],
            formats_processed=stats['formats_processed']
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# Helper functions
def get_format_use_cases(format: AudioFormat) -> List[str]:
    """Get recommended use cases for a format"""
    use_cases = {
        AudioFormat.WAV: ["Professional recording", "Audio editing", "Mastering", "Broadcast"],
        AudioFormat.FLAC: ["Archival storage", "High-quality music", "Lossless distribution"],
        AudioFormat.MP3: ["Music streaming", "Podcasts", "Web audio", "Mobile devices"],
        AudioFormat.AAC: ["Streaming services", "Mobile apps", "Video soundtracks"],
        AudioFormat.OGG: ["Open-source projects", "Gaming", "Web streaming"],
        AudioFormat.OPUS: ["Voice calls", "Low-latency streaming", "Internet radio"],
        AudioFormat.AIFF: ["Mac-based workflows", "Professional audio", "Legacy systems"]
    }
    
    return use_cases.get(format, ["General audio use"])


def calculate_quality_score(metadata: AudioMetadata) -> float:
    """Calculate overall quality score from metadata"""
    score = 50  # Base score
    
    # Sample rate scoring
    if metadata.sample_rate:
        if metadata.sample_rate >= 96000:
            score += 20
        elif metadata.sample_rate >= 48000:
            score += 15
        elif metadata.sample_rate >= 44100:
            score += 10
        else:
            score += 5
    
    # Bit depth scoring
    if metadata.bit_depth:
        if metadata.bit_depth >= 24:
            score += 15
        elif metadata.bit_depth >= 16:
            score += 10
        else:
            score += 5
    
    # Dynamic range scoring
    if metadata.dynamic_range:
        if metadata.dynamic_range >= 20:
            score += 10
        elif metadata.dynamic_range >= 12:
            score += 5
        else:
            score -= 5
    
    # Peak level scoring (avoid clipping)
    if metadata.peak_level:
        if metadata.peak_level < 0.95:
            score += 5
        elif metadata.peak_level >= 1.0:
            score -= 10
    
    return min(100, max(0, score))


# Startup and shutdown events
@router.on_event("startup")
async def startup_event():
    """Initialize handler on startup"""
    if FORMAT_HANDLER_AVAILABLE:
        logger.info("Professional Audio Format Handler API initialized successfully")
    else:
        logger.warning("Professional Audio Format Handler not available")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if format_handler:
        await format_handler.cleanup()
        logger.info("Professional Audio Format Handler cleanup completed")