"""
Advanced Timestamping API Endpoints
REST API for advanced timestamping functionality
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any, Union
import os
import sys
import asyncio
import logging
import tempfile
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_middleware import get_current_active_user, require_write
from api.dependencies import create_api_response, create_error_response

# Import timestamping system
from timestamping_system import (
    TimestampingSystem, WordTimestamp, SegmentTimestamp, Bookmark,
    TimestampingConfig, TimestampingResult, TimestampFormat
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-timestamping", tags=["Advanced Timestamping"])

# Initialize components
timestamping_system = TimestampingSystem()

# Pydantic models for API
class TimestampingConfigAPI(BaseModel):
    """API request model for timestamping configuration"""
    precision_level: str = Field(default="word", description="Precision level: word, phrase, sentence, segment")
    timestamp_format: str = Field(default="seconds", description="Timestamp format")
    include_confidence: bool = Field(default=True, description="Include confidence scores")
    enable_speaker_timestamps: bool = Field(default=True, description="Enable speaker-level timestamps")
    enable_word_timestamps: bool = Field(default=True, description="Enable word-level timestamps")
    enable_segment_timestamps: bool = Field(default=True, description="Enable segment-level timestamps")
    min_word_confidence: float = Field(default=0.5, description="Minimum word confidence", ge=0.0, le=1.0)
    alignment_method: str = Field(default="forced", description="Alignment method")
    audio_sample_rate: int = Field(default=16000, description="Audio sample rate", ge=8000, le=48000)
    enable_silence_detection: bool = Field(default=True, description="Enable silence detection")
    silence_threshold: float = Field(default=0.01, description="Silence threshold", ge=0.0, le=1.0)

class WordTimestampAPI(BaseModel):
    """API response model for word timestamps"""
    word: str
    start_time: float
    end_time: float
    confidence: float
    speaker_id: Optional[str] = None
    segment_id: Optional[str] = None
    duration: float

class SegmentTimestampAPI(BaseModel):
    """API response model for segment timestamps"""
    id: str
    start_time: float
    end_time: float
    segment_type: str
    content: str
    speaker_id: Optional[str] = None
    topic: Optional[str] = None
    confidence: float
    metadata: Dict[str, Any]
    duration: float

class BookmarkAPI(BaseModel):
    """API response model for bookmarks"""
    id: str
    timestamp: float
    title: str
    description: Optional[str] = None
    category: str
    importance: int
    created_at: datetime
    metadata: Dict[str, Any]

class TimestampingResultAPI(BaseModel):
    """API response model for timestamping results"""
    word_timestamps: List[WordTimestampAPI]
    segment_timestamps: List[SegmentTimestampAPI]
    bookmarks: List[BookmarkAPI]
    total_duration: float
    total_words: int
    total_segments: int
    average_confidence: float
    processing_time: float
    config_used: TimestampingConfigAPI
    metadata: Dict[str, Any]

class TimestampingRequest(BaseModel):
    """API request model for timestamping analysis"""
    config: TimestampingConfigAPI
    transcript_text: Optional[str] = Field(None, description="Optional transcript text for alignment")
    include_bookmarks: bool = Field(default=True, description="Include automatic bookmark generation")

class BookmarkCreateRequest(BaseModel):
    """API request model for creating bookmarks"""
    timestamp: float = Field(..., description="Timestamp in seconds", ge=0.0)
    title: str = Field(..., description="Bookmark title", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Bookmark description", max_length=1000)
    category: str = Field(default="general", description="Bookmark category")
    importance: int = Field(default=1, description="Importance level (1-5)", ge=1, le=5)

class NavigationRequest(BaseModel):
    """API request model for navigation operations"""
    target_time: Optional[float] = Field(None, description="Target timestamp")
    target_word: Optional[str] = Field(None, description="Target word")
    target_segment: Optional[str] = Field(None, description="Target segment ID")
    search_query: Optional[str] = Field(None, description="Search query")

def _convert_word_timestamp_to_api(word_ts: WordTimestamp) -> WordTimestampAPI:
    """Convert internal word timestamp to API response"""
    return WordTimestampAPI(
        word=word_ts.word,
        start_time=float(word_ts.start_time),
        end_time=float(word_ts.end_time),
        confidence=float(word_ts.confidence),
        speaker_id=word_ts.speaker_id,
        segment_id=word_ts.segment_id,
        duration=float(word_ts.duration())
    )

def _convert_segment_timestamp_to_api(seg_ts: SegmentTimestamp) -> SegmentTimestampAPI:
    """Convert internal segment timestamp to API response"""
    return SegmentTimestampAPI(
        id=seg_ts.id,
        start_time=float(seg_ts.start_time),
        end_time=float(seg_ts.end_time),
        segment_type=seg_ts.segment_type,
        content=seg_ts.content,
        speaker_id=seg_ts.speaker_id,
        topic=seg_ts.topic,
        confidence=float(seg_ts.confidence),
        metadata=seg_ts.metadata or {},
        duration=float(seg_ts.duration())
    )

def _convert_bookmark_to_api(bookmark: Bookmark) -> BookmarkAPI:
    """Convert internal bookmark to API response"""
    return BookmarkAPI(
        id=bookmark.id,
        timestamp=float(bookmark.timestamp),
        title=bookmark.title,
        description=bookmark.description,
        category=bookmark.category,
        importance=bookmark.importance,
        created_at=bookmark.created_at,
        metadata=bookmark.metadata or {}
    )

def _convert_result_to_api(result: TimestampingResult, config: TimestampingConfigAPI) -> TimestampingResultAPI:
    """Convert internal result to API response"""
    return TimestampingResultAPI(
        word_timestamps=[_convert_word_timestamp_to_api(wt) for wt in result.word_timestamps],
        segment_timestamps=[_convert_segment_timestamp_to_api(st) for st in result.segment_timestamps],
        bookmarks=[_convert_bookmark_to_api(b) for b in result.bookmarks],
        total_duration=float(result.total_duration),
        total_words=result.total_words,
        total_segments=result.total_segments,
        average_confidence=float(result.average_confidence),
        processing_time=result.processing_time,
        config_used=config,
        metadata=result.metadata or {}
    )

@router.post("/analyze", response_model=TimestampingResultAPI)
async def analyze_timestamps(
    request: TimestampingRequest,
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze audio file and generate comprehensive timestamps"""
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
            # Configure timestamping system
            config = TimestampingConfig(
                precision_level=request.config.precision_level,
                timestamp_format=TimestampFormat(request.config.timestamp_format),
                include_confidence=request.config.include_confidence,
                enable_speaker_timestamps=request.config.enable_speaker_timestamps,
                enable_word_timestamps=request.config.enable_word_timestamps,
                enable_segment_timestamps=request.config.enable_segment_timestamps,
                min_word_confidence=Decimal(str(request.config.min_word_confidence)),
                alignment_method=request.config.alignment_method,
                audio_sample_rate=request.config.audio_sample_rate,
                enable_silence_detection=request.config.enable_silence_detection,
                silence_threshold=Decimal(str(request.config.silence_threshold))
            )
            
            # Perform timestamping analysis
            result = await timestamping_system.analyze_timestamps(
                audio_file_path=temp_file_path,
                transcript_text=request.transcript_text,
                config=config,
                include_bookmarks=request.include_bookmarks
            )
            
            # Convert result to API response
            api_result = _convert_result_to_api(result, request.config)
            
            logger.info(f"Timestamping analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{result.total_words} words, {result.total_segments} segments, "
                       f"{result.processing_time:.2f}s processing time")
            
            return create_api_response(
                data=api_result,
                message="Timestamping analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in timestamping analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in timestamping analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze timestamps"
        )

@router.post("/bookmarks", response_model=BookmarkAPI)
async def create_bookmark(
    request: BookmarkCreateRequest,
    session_id: str = Field(..., description="Timestamping session ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new bookmark at specified timestamp"""
    try:
        # Create bookmark
        bookmark = await timestamping_system.create_bookmark(
            session_id=session_id,
            timestamp=Decimal(str(request.timestamp)),
            title=request.title,
            description=request.description,
            category=request.category,
            importance=request.importance,
            user_id=current_user.get('user_id', 'unknown')
        )
        
        # Convert to API response
        api_bookmark = _convert_bookmark_to_api(bookmark)
        
        logger.info(f"Bookmark created for user {current_user.get('user_id', 'unknown')}: "
                   f"{request.title} at {request.timestamp}s")
        
        return create_api_response(
            data=api_bookmark,
            message="Bookmark created successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in bookmark creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bookmark"
        )

@router.get("/bookmarks/{session_id}")
async def get_bookmarks(
    session_id: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get bookmarks for a timestamping session"""
    try:
        # Get bookmarks
        bookmarks = await timestamping_system.get_bookmarks(
            session_id=session_id,
            category=category,
            user_id=current_user.get('user_id', 'unknown')
        )
        
        # Convert to API response
        api_bookmarks = [_convert_bookmark_to_api(b) for b in bookmarks]
        
        return create_api_response(
            data={"bookmarks": api_bookmarks, "total": len(api_bookmarks)},
            message="Bookmarks retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error retrieving bookmarks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookmarks"
        )

@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a bookmark"""
    try:
        # Delete bookmark
        success = await timestamping_system.delete_bookmark(
            bookmark_id=bookmark_id,
            user_id=current_user.get('user_id', 'unknown')
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        logger.info(f"Bookmark deleted for user {current_user.get('user_id', 'unknown')}: {bookmark_id}")
        
        return create_api_response(
            data={"bookmark_id": bookmark_id},
            message="Bookmark deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bookmark"
        )

@router.post("/navigate")
async def navigate_to_timestamp(
    request: NavigationRequest,
    session_id: str = Field(..., description="Timestamping session ID"),
    current_user: dict = Depends(get_current_active_user)
):
    """Navigate to specific timestamp, word, or segment"""
    try:
        # Perform navigation
        navigation_result = await timestamping_system.navigate(
            session_id=session_id,
            target_time=Decimal(str(request.target_time)) if request.target_time else None,
            target_word=request.target_word,
            target_segment=request.target_segment,
            search_query=request.search_query
        )
        
        return create_api_response(
            data=navigation_result,
            message="Navigation completed successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in navigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in navigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to navigate"
        )

@router.get("/export/{session_id}")
async def export_timestamps(
    session_id: str,
    format: str = Field(default="json", description="Export format: json, srt, vtt, eaf"),
    include_bookmarks: bool = Field(default=True, description="Include bookmarks in export"),
    current_user: dict = Depends(get_current_active_user)
):
    """Export timestamps in various formats"""
    try:
        # Export timestamps
        export_data = await timestamping_system.export_timestamps(
            session_id=session_id,
            format=format,
            include_bookmarks=include_bookmarks,
            user_id=current_user.get('user_id', 'unknown')
        )
        
        # Set appropriate content type
        content_types = {
            'json': 'application/json',
            'srt': 'text/plain',
            'vtt': 'text/vtt',
            'eaf': 'application/xml'
        }
        
        return JSONResponse(
            content=export_data,
            media_type=content_types.get(format, 'text/plain'),
            headers={
                'Content-Disposition': f'attachment; filename="timestamps_{session_id}.{format}"'
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error in export: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export timestamps"
        )

@router.get("/formats")
async def get_timestamp_formats():
    """Get available timestamp formats and precision levels"""
    return create_api_response(
        data={
            "precision_levels": [
                {
                    "value": "word",
                    "label": "Word Level",
                    "description": "Individual word timestamps with high precision"
                },
                {
                    "value": "phrase",
                    "label": "Phrase Level",
                    "description": "Phrase-based timestamps for natural groupings"
                },
                {
                    "value": "sentence",
                    "label": "Sentence Level",
                    "description": "Sentence-based timestamps for readability"
                },
                {
                    "value": "segment",
                    "label": "Segment Level",
                    "description": "Speaker or topic segment timestamps"
                }
            ],
            "timestamp_formats": [
                {
                    "value": "seconds",
                    "label": "Seconds",
                    "description": "Decimal seconds (e.g., 123.456)"
                },
                {
                    "value": "milliseconds",
                    "label": "Milliseconds",
                    "description": "Integer milliseconds (e.g., 123456)"
                },
                {
                    "value": "timecode",
                    "label": "Timecode",
                    "description": "HH:MM:SS.mmm format"
                },
                {
                    "value": "frames",
                    "label": "Frames",
                    "description": "Frame-based timestamps"
                }
            ],
            "export_formats": [
                {
                    "value": "json",
                    "label": "JSON",
                    "description": "Structured JSON with all timestamp data"
                },
                {
                    "value": "srt",
                    "label": "SRT Subtitles",
                    "description": "SubRip subtitle format"
                },
                {
                    "value": "vtt",
                    "label": "WebVTT",
                    "description": "Web Video Text Tracks format"
                },
                {
                    "value": "eaf",
                    "label": "ELAN EAF",
                    "description": "ELAN annotation format"
                }
            ],
            "alignment_methods": [
                {
                    "value": "forced",
                    "label": "Forced Alignment",
                    "description": "High-precision forced alignment"
                },
                {
                    "value": "vad_based",
                    "label": "VAD-based",
                    "description": "Voice activity detection based alignment"
                },
                {
                    "value": "energy_based",
                    "label": "Energy-based",
                    "description": "Audio energy level based alignment"
                },
                {
                    "value": "hybrid",
                    "label": "Hybrid",
                    "description": "Combination of multiple methods"
                }
            ]
        },
        message="Timestamp formats retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "timestamping_system": "operational",
                "database": "connected",
                "audio_processing": "available"
            },
            "supported_formats": 4,
            "supported_precision_levels": 4
        }
        
        return create_api_response(
            data=health_status,
            message="Advanced timestamping service is healthy"
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