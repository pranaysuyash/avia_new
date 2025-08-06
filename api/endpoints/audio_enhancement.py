"""
Audio Enhancement API Endpoints
FastAPI endpoints for audio processing and enhancement
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import base64
import io
import logging
from datetime import datetime
import tempfile
import os

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from database.connection import get_db
from sqlalchemy.orm import Session

# Import audio processing functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from audio_processor import AudioProcessor
from advanced_audio_processor import AdvancedAudioProcessor, AudioQualityMetrics, AudioBookmark

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audio")

# Initialize processors
audio_processor = AudioProcessor()
advanced_processor = AdvancedAudioProcessor()

# Pydantic models
class AudioEnhancementRequest(BaseModel):
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    enhancement_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Enhancement options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_data": "base64_encoded_audio_here",
                "enhancement_options": {
                    "noise_reduction": True,
                    "normalize": True,
                    "remove_silence": True,
                    "enhance_voice": True,
                    "target_loudness": -16.0
                }
            }
        }

class AudioMetadata(BaseModel):
    duration: float
    sample_rate: int
    channels: int
    format: str
    size_bytes: int

class AudioEnhancementResponse(BaseModel):
    enhanced_audio: str  # Base64 encoded
    original_metadata: AudioMetadata
    enhanced_metadata: AudioMetadata
    processing_time: float
    enhancements_applied: List[str]

@router.post("/enhance", response_model=AudioEnhancementResponse)
@require_quota('api_calls', 1)  # Enforce API call quota
async def enhance_audio(
    request: AudioEnhancementRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhance audio with various processing options
    
    Options include:
    - Noise reduction
    - Normalization
    - Silence removal
    - Voice enhancement
    - Dynamic range compression
    """
    try:
        start_time = datetime.now()
        
        # Decode audio data
        if not request.audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
            
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Get original metadata
            original_metadata = audio_processor.get_audio_metadata(tmp_path)
            
            # Apply enhancements
            enhancements_applied = []
            enhanced_path = tmp_path
            
            options = request.enhancement_options
            
            if options.get('noise_reduction', False):
                enhanced_path = await advanced_processor.reduce_noise(
                    enhanced_path,
                    reduction_strength=options.get('noise_reduction_strength', 0.7)
                )
                enhancements_applied.append('noise_reduction')
            
            if options.get('normalize', False):
                enhanced_path = await advanced_processor.normalize_audio(
                    enhanced_path,
                    target_loudness=options.get('target_loudness', -16.0)
                )
                enhancements_applied.append('normalization')
            
            if options.get('remove_silence', False):
                enhanced_path = await advanced_processor.remove_silence(
                    enhanced_path,
                    silence_threshold=options.get('silence_threshold', -40)
                )
                enhancements_applied.append('silence_removal')
            
            if options.get('enhance_voice', False):
                enhanced_path = await advanced_processor.enhance_voice(enhanced_path)
                enhancements_applied.append('voice_enhancement')
            
            if options.get('compress_dynamics', False):
                enhanced_path = await advanced_processor.compress_dynamics(
                    enhanced_path,
                    threshold=options.get('compression_threshold', -20),
                    ratio=options.get('compression_ratio', 4)
                )
                enhancements_applied.append('dynamic_compression')
            
            # Read enhanced audio
            with open(enhanced_path, 'rb') as f:
                enhanced_audio_bytes = f.read()
            
            # Get enhanced metadata
            enhanced_metadata = audio_processor.get_audio_metadata(enhanced_path)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Clean up temporary files
            if enhanced_path != tmp_path:
                os.unlink(enhanced_path)
            
            return AudioEnhancementResponse(
                enhanced_audio=base64.b64encode(enhanced_audio_bytes).decode('utf-8'),
                original_metadata=AudioMetadata(
                    duration=original_metadata['duration'],
                    sample_rate=original_metadata['sample_rate'],
                    channels=original_metadata['channels'],
                    format=original_metadata['format'],
                    size_bytes=len(audio_bytes)
                ),
                enhanced_metadata=AudioMetadata(
                    duration=enhanced_metadata['duration'],
                    sample_rate=enhanced_metadata['sample_rate'],
                    channels=enhanced_metadata['channels'],
                    format=enhanced_metadata['format'],
                    size_bytes=len(enhanced_audio_bytes)
                ),
                processing_time=processing_time,
                enhancements_applied=enhancements_applied
            )
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Audio enhancement error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance audio: {str(e)}"
        )

@router.post("/enhance/file")
async def enhance_audio_file(
    file: UploadFile = File(...),
    noise_reduction: bool = Form(False),
    normalize: bool = Form(False),
    remove_silence: bool = Form(False),
    enhance_voice: bool = Form(False),
    compress_dynamics: bool = Form(False),
    target_loudness: float = Form(-16.0),
    current_user: dict = Depends(get_current_user)
):
    """
    Enhance uploaded audio file
    
    Direct file upload endpoint
    """
    try:
        # Read file content
        content = await file.read()
        
        # Create enhancement request
        request = AudioEnhancementRequest(
            audio_data=base64.b64encode(content).decode('utf-8'),
            enhancement_options={
                'noise_reduction': noise_reduction,
                'normalize': normalize,
                'remove_silence': remove_silence,
                'enhance_voice': enhance_voice,
                'compress_dynamics': compress_dynamics,
                'target_loudness': target_loudness
            }
        )
        
        # Process enhancement
        response = await enhance_audio(request, current_user, None)
        
        return response
        
    except Exception as e:
        logger.error(f"File enhancement error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enhance audio file: {str(e)}"
        )

@router.post("/analyze")
async def analyze_audio(
    audio_data: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze audio and return detailed metrics
    
    Returns audio characteristics and quality metrics
    """
    try:
        # Decode audio
        audio_bytes = base64.b64decode(audio_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Analyze audio
            analysis = await advanced_processor.analyze_audio(tmp_path)
            
            return {
                "metadata": analysis['metadata'],
                "quality_metrics": {
                    "snr": analysis.get('snr', 0),
                    "peak_level": analysis.get('peak_level', 0),
                    "rms_level": analysis.get('rms_level', 0),
                    "dynamic_range": analysis.get('dynamic_range', 0),
                    "clipping_detected": analysis.get('clipping_detected', False),
                    "silence_percentage": analysis.get('silence_percentage', 0)
                },
                "frequency_analysis": {
                    "dominant_frequency": analysis.get('dominant_frequency', 0),
                    "frequency_range": analysis.get('frequency_range', [0, 0]),
                    "spectral_centroid": analysis.get('spectral_centroid', 0)
                },
                "recommendations": analysis.get('recommendations', [])
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze audio: {str(e)}"
        )

@router.get("/presets")
async def get_enhancement_presets(
    current_user: dict = Depends(get_current_user)
):
    """Get available audio enhancement presets"""
    return {
        "presets": [
            {
                "id": "voice_podcast",
                "name": "Podcast Voice",
                "description": "Optimized for voice podcasts",
                "options": {
                    "noise_reduction": True,
                    "normalize": True,
                    "remove_silence": True,
                    "enhance_voice": True,
                    "target_loudness": -16.0
                }
            },
            {
                "id": "meeting_recording",
                "name": "Meeting Recording",
                "description": "Clean up meeting recordings",
                "options": {
                    "noise_reduction": True,
                    "normalize": True,
                    "remove_silence": False,
                    "enhance_voice": True,
                    "compress_dynamics": True
                }
            },
            {
                "id": "music_master",
                "name": "Music Mastering",
                "description": "Basic music mastering",
                "options": {
                    "normalize": True,
                    "compress_dynamics": True,
                    "target_loudness": -14.0
                }
            },
            {
                "id": "clean_only",
                "name": "Clean Only",
                "description": "Just noise reduction",
                "options": {
                    "noise_reduction": True,
                    "noise_reduction_strength": 0.8
                }
            }
        ]
    }

@router.post("/batch/enhance")
async def batch_enhance_audio(
    files: List[UploadFile] = File(...),
    preset: str = Form("voice_podcast"),
    current_user: dict = Depends(get_current_user)
):
    """
    Batch enhance multiple audio files
    
    Admin only endpoint
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files per batch"
        )
    
    # Get preset
    presets = await get_enhancement_presets(current_user)
    preset_options = next(
        (p['options'] for p in presets['presets'] if p['id'] == preset),
        None
    )
    
    if not preset_options:
        raise HTTPException(status_code=400, detail="Invalid preset")
    
    results = []
    
    for i, file in enumerate(files):
        try:
            content = await file.read()
            
            request = AudioEnhancementRequest(
                audio_data=base64.b64encode(content).decode('utf-8'),
                enhancement_options=preset_options
            )
            
            response = await enhance_audio(request, current_user, None)
            
            results.append({
                "index": i,
                "filename": file.filename,
                "success": True,
                "enhanced_audio": response.enhanced_audio,
                "enhancements_applied": response.enhancements_applied
            })
            
        except Exception as e:
            results.append({
                "index": i,
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "successful": sum(1 for r in results if r['success']),
        "failed": sum(1 for r in results if not r['success']),
        "results": results
    }

# Advanced Audio Processing Endpoints

class AudioQualityRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")

class AudioQualityResponse(BaseModel):
    snr_db: float
    dynamic_range_db: float
    spectral_centroid: float
    zero_crossing_rate: float
    rms_energy: float
    quality_score: float
    recommendations: List[str]
    processing_time: float

@router.post("/analyze/quality", response_model=AudioQualityResponse)
@require_quota('api_calls', 1, 'advanced_analytics')  # Require advanced feature
async def analyze_audio_quality(
    request: AudioQualityRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze audio quality and provide recommendations
    
    Returns detailed metrics about audio quality including:
    - Signal-to-noise ratio
    - Dynamic range
    - Spectral characteristics
    - Quality score (0-100)
    - Improvement recommendations
    """
    try:
        start_time = datetime.now()
        
        # Decode audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Analyze quality
            quality_metrics = advanced_processor.quality_analyzer.analyze_quality(tmp_path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AudioQualityResponse(
                snr_db=quality_metrics.snr_db,
                dynamic_range_db=quality_metrics.dynamic_range_db,
                spectral_centroid=quality_metrics.spectral_centroid,
                zero_crossing_rate=quality_metrics.zero_crossing_rate,
                rms_energy=quality_metrics.rms_energy,
                quality_score=quality_metrics.quality_score,
                recommendations=quality_metrics.recommendations,
                processing_time=processing_time
            )
            
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Audio quality analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze audio quality: {str(e)}"
        )

class AudioSegmentRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")

class AudioSegmentResponse(BaseModel):
    segmented_audio: str = Field(..., description="Base64 encoded segmented audio")
    original_duration: float
    segment_duration: float
    processing_time: float

@router.post("/segment/extract", response_model=AudioSegmentResponse)
async def extract_audio_segment(
    request: AudioSegmentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract a specific segment from audio file
    
    Useful for creating clips, removing sections, or isolating specific parts
    """
    try:
        start_time = datetime.now()
        
        # Decode audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Extract segment
            segment_path = advanced_processor.trimmer.extract_segment(
                tmp_path, 
                request.start_time, 
                request.end_time
            )
            
            # Read segmented audio
            with open(segment_path, 'rb') as f:
                segment_bytes = f.read()
            
            # Calculate durations
            original_metadata = audio_processor.get_audio_metadata(tmp_path)
            segment_metadata = audio_processor.get_audio_metadata(segment_path)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Clean up
            os.unlink(segment_path)
            
            return AudioSegmentResponse(
                segmented_audio=base64.b64encode(segment_bytes).decode('utf-8'),
                original_duration=original_metadata['duration'],
                segment_duration=segment_metadata['duration'],
                processing_time=processing_time
            )
            
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Audio segmentation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract audio segment: {str(e)}"
        )

class AudioSilenceDetectionRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    silence_threshold: int = Field(-40, description="Silence threshold in dB")
    min_silence_duration: int = Field(500, description="Minimum silence duration in ms")

class SilenceSegment(BaseModel):
    start_time: float
    end_time: float
    duration: float

class AudioSilenceDetectionResponse(BaseModel):
    silence_segments: List[SilenceSegment]
    total_silence_duration: float
    speech_duration: float
    silence_percentage: float
    processing_time: float

@router.post("/analyze/silence", response_model=AudioSilenceDetectionResponse)
async def detect_silence_segments(
    request: AudioSilenceDetectionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Detect silence segments in audio
    
    Useful for:
    - Automatic chapter detection
    - Speech activity detection
    - Audio trimming guidance
    """
    try:
        start_time = datetime.now()
        
        # Decode audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        try:
            # Detect silence segments
            segments = advanced_processor.trimmer.segment_by_silence(
                tmp_path,
                silence_thresh=request.silence_threshold,
                min_silence_len=request.min_silence_duration
            )
            
            # Get total duration
            metadata = audio_processor.get_audio_metadata(tmp_path)
            total_duration = metadata['duration']
            
            # Process segments
            silence_segments = []
            total_silence = 0
            
            for segment_path in segments:
                seg_metadata = audio_processor.get_audio_metadata(segment_path)
                duration = seg_metadata['duration']
                total_silence += duration
                
                # Note: This is simplified - in reality you'd need to track timestamps
                silence_segments.append(SilenceSegment(
                    start_time=0,  # Would need proper calculation
                    end_time=duration,
                    duration=duration
                ))
                
                # Clean up segment file
                os.unlink(segment_path)
            
            speech_duration = total_duration - total_silence
            silence_percentage = (total_silence / total_duration) * 100 if total_duration > 0 else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AudioSilenceDetectionResponse(
                silence_segments=silence_segments,
                total_silence_duration=total_silence,
                speech_duration=speech_duration,
                silence_percentage=silence_percentage,
                processing_time=processing_time
            )
            
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        logger.error(f"Silence detection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect silence: {str(e)}"
        )

class AudioBookmarkRequest(BaseModel):
    audio_id: str = Field(..., description="Audio file identifier")
    timestamp: float = Field(..., description="Bookmark timestamp in seconds")
    title: str = Field(..., description="Bookmark title")
    description: str = Field("", description="Optional description")
    bookmark_type: str = Field("manual", description="Bookmark type: manual, auto, chapter")

class AudioBookmarkResponse(BaseModel):
    bookmark_id: str
    timestamp: float
    title: str
    description: str
    bookmark_type: str
    created_at: str

@router.post("/bookmarks/create", response_model=AudioBookmarkResponse)
async def create_audio_bookmark(
    request: AudioBookmarkRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a bookmark for an audio file
    
    Bookmarks help users navigate long audio files and mark important sections
    """
    try:
        bookmark = AudioBookmark(
            timestamp=request.timestamp,
            title=request.title,
            description=request.description,
            bookmark_type=request.bookmark_type
        )
        
        # Add to bookmark manager
        bookmark_id = advanced_processor.bookmark_manager.add_bookmark(
            request.audio_id,
            bookmark
        )
        
        return AudioBookmarkResponse(
            bookmark_id=bookmark_id,
            timestamp=bookmark.timestamp,
            title=bookmark.title,
            description=bookmark.description,
            bookmark_type=bookmark.bookmark_type,
            created_at=bookmark.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Bookmark creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create bookmark: {str(e)}"
        )

@router.get("/bookmarks/{audio_id}")
async def get_audio_bookmarks(
    audio_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all bookmarks for an audio file"""
    try:
        bookmarks = advanced_processor.bookmark_manager.get_bookmarks(audio_id)
        
        return {
            "audio_id": audio_id,
            "bookmarks": [
                {
                    "timestamp": b.timestamp,
                    "title": b.title,
                    "description": b.description,
                    "bookmark_type": b.bookmark_type,
                    "created_at": b.created_at.isoformat()
                }
                for b in bookmarks
            ]
        }
        
    except Exception as e:
        logger.error(f"Get bookmarks error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get bookmarks: {str(e)}"
        )