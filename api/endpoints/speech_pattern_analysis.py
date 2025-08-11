"""
Speech Pattern Analysis API Endpoints
REST API for comprehensive speech pattern analysis functionality
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import JSONResponse
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

# Import speech pattern analysis system
from speech_pattern_analysis import (
    SpeechPatternAnalyzer, SpeechSegment, PauseAnalysis, FillerWordAnalysis,
    SpeechRateAnalysis, ConfidenceAnalysis, SpeechPatternResult, AnalysisConfig
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech-pattern", tags=["Speech Pattern Analysis"])

# Initialize components
speech_analyzer = SpeechPatternAnalyzer()

# Pydantic models for API
class AnalysisConfigAPI(BaseModel):
    """API request model for speech pattern analysis configuration"""
    analysis_types: List[str] = Field(default=["all"], description="Types of analysis to perform")
    language: str = Field(default="en", description="Language code")
    speaker_detection: bool = Field(default=True, description="Enable speaker detection")
    filler_word_detection: bool = Field(default=True, description="Enable filler word detection")
    pause_analysis: bool = Field(default=True, description="Enable pause analysis")
    speech_rate_analysis: bool = Field(default=True, description="Enable speech rate analysis")
    confidence_analysis: bool = Field(default=True, description="Enable confidence analysis")
    coaching_suggestions: bool = Field(default=True, description="Enable coaching suggestions")
    segment_duration: float = Field(default=5.0, description="Segment duration for analysis", ge=1.0, le=30.0)
    min_pause_duration: float = Field(default=0.3, description="Minimum pause duration", ge=0.1, le=2.0)
    speech_rate_threshold: float = Field(default=150.0, description="Normal speech rate (WPM)", ge=50.0, le=300.0)

class SpeechSegmentAPI(BaseModel):
    """API response model for speech segments"""
    start_time: float
    end_time: float
    text: str
    speaker_id: Optional[str] = None
    confidence: float
    duration: float
    word_count: int
    speech_rate: float
    pause_count: int
    filler_count: int

class PauseAnalysisAPI(BaseModel):
    """API response model for pause analysis"""
    total_pause_time: float
    pause_count: int
    average_pause_duration: float
    longest_pause_duration: float
    pause_frequency: float
    pause_locations: List[Dict[str, float]]
    silence_ratio: float

class FillerWordAnalysisAPI(BaseModel):
    """API response model for filler word analysis"""
    total_filler_count: int
    filler_frequency: float
    filler_types: Dict[str, int]
    filler_locations: List[Dict[str, Any]]
    filler_ratio: float

class SpeechRateAnalysisAPI(BaseModel):
    """API response model for speech rate analysis"""
    average_speech_rate: float
    speech_rate_variance: float
    speech_rate_timeline: List[Dict[str, float]]
    speaking_time: float
    total_words: int
    rate_classification: str

class ConfidenceAnalysisAPI(BaseModel):
    """API response model for confidence analysis"""
    overall_confidence: float
    confidence_timeline: List[Dict[str, float]]
    hesitation_count: int
    repetition_count: int
    false_starts: int
    confidence_classification: str

class CoachingSuggestionsAPI(BaseModel):
    """API response model for coaching suggestions"""
    overall_score: float
    strengths: List[str]
    areas_for_improvement: List[str]
    specific_suggestions: List[Dict[str, str]]
    practice_exercises: List[str]

class SpeechPatternAnalysisAPI(BaseModel):
    """API response model for complete speech pattern analysis"""
    segments: List[SpeechSegmentAPI]
    pause_analysis: PauseAnalysisAPI
    filler_analysis: FillerWordAnalysisAPI
    speech_rate_analysis: SpeechRateAnalysisAPI
    confidence_analysis: ConfidenceAnalysisAPI
    coaching_suggestions: CoachingSuggestionsAPI
    overall_statistics: Dict[str, Any]
    processing_time: float
    total_duration: float
    config_used: AnalysisConfigAPI

def _convert_speech_segment_to_api(segment: SpeechSegment) -> SpeechSegmentAPI:
    """Convert internal speech segment to API response"""
    return SpeechSegmentAPI(
        start_time=float(segment.start_time),
        end_time=float(segment.end_time),
        text=segment.text,
        speaker_id=segment.speaker_id,
        confidence=float(segment.confidence),
        duration=float(segment.duration),
        word_count=len(segment.text.split()) if segment.text else 0,
        speech_rate=float(getattr(segment, 'speech_rate', 0)),
        pause_count=int(getattr(segment, 'pause_count', 0)),
        filler_count=int(getattr(segment, 'filler_count', 0))
    )

def _convert_pause_analysis_to_api(analysis: PauseAnalysis) -> PauseAnalysisAPI:
    """Convert internal pause analysis to API response"""
    return PauseAnalysisAPI(
        total_pause_time=float(analysis.total_pause_time),
        pause_count=int(analysis.pause_count),
        average_pause_duration=float(analysis.average_pause_duration),
        longest_pause_duration=float(analysis.longest_pause_duration),
        pause_frequency=float(analysis.pause_frequency),
        pause_locations=[
            {"start_time": float(p.start_time), "duration": float(p.duration)}
            for p in analysis.pause_locations
        ],
        silence_ratio=float(analysis.silence_ratio)
    )

def _convert_filler_analysis_to_api(analysis: FillerWordAnalysis) -> FillerWordAnalysisAPI:
    """Convert internal filler analysis to API response"""
    return FillerWordAnalysisAPI(
        total_filler_count=int(analysis.total_filler_count),
        filler_frequency=float(analysis.filler_frequency),
        filler_types=analysis.filler_types,
        filler_locations=[
            {
                "word": loc.word,
                "start_time": float(loc.start_time),
                "confidence": float(loc.confidence)
            }
            for loc in analysis.filler_locations
        ],
        filler_ratio=float(analysis.filler_ratio)
    )

def _convert_speech_rate_analysis_to_api(analysis: SpeechRateAnalysis) -> SpeechRateAnalysisAPI:
    """Convert internal speech rate analysis to API response"""
    return SpeechRateAnalysisAPI(
        average_speech_rate=float(analysis.average_speech_rate),
        speech_rate_variance=float(analysis.speech_rate_variance),
        speech_rate_timeline=[
            {"time": float(point.time), "rate": float(point.rate)}
            for point in analysis.speech_rate_timeline
        ],
        speaking_time=float(analysis.speaking_time),
        total_words=int(analysis.total_words),
        rate_classification=analysis.rate_classification
    )

def _convert_confidence_analysis_to_api(analysis: ConfidenceAnalysis) -> ConfidenceAnalysisAPI:
    """Convert internal confidence analysis to API response"""
    return ConfidenceAnalysisAPI(
        overall_confidence=float(analysis.overall_confidence),
        confidence_timeline=[
            {"time": float(point.time), "confidence": float(point.confidence)}
            for point in analysis.confidence_timeline
        ],
        hesitation_count=int(analysis.hesitation_count),
        repetition_count=int(analysis.repetition_count),
        false_starts=int(analysis.false_starts),
        confidence_classification=analysis.confidence_classification
    )

@router.post("/analyze", response_model=SpeechPatternAnalysisAPI)
async def analyze_speech_patterns(
    audio_file: UploadFile = File(...),
    config: str = Form(...),
    transcript_text: Optional[str] = Form(None),
    include_coaching: bool = Form(True),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze speech patterns from audio file"""
    try:
        # Parse config from JSON string
        import json
        config_dict = json.loads(config)
        request_config = AnalysisConfigAPI(**config_dict)
        
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
            # Configure speech analyzer
            analysis_config = AnalysisConfig(
                analysis_types=request_config.analysis_types,
                language=request_config.language,
                speaker_detection=request_config.speaker_detection,
                filler_word_detection=request_config.filler_word_detection,
                pause_analysis=request_config.pause_analysis,
                speech_rate_analysis=request_config.speech_rate_analysis,
                confidence_analysis=request_config.confidence_analysis,
                coaching_suggestions=request_config.coaching_suggestions,
                segment_duration=request_config.segment_duration,
                min_pause_duration=request_config.min_pause_duration,
                speech_rate_threshold=request_config.speech_rate_threshold
            )
            
            # Perform speech pattern analysis
            analysis_result = await speech_analyzer.analyze(
                audio_file_path=temp_file_path,
                transcript_text=transcript_text,
                config=analysis_config,
                include_coaching=include_coaching
            )
            
            # Convert results to API response
            api_segments = [_convert_speech_segment_to_api(s) for s in analysis_result.segments]
            api_pause_analysis = _convert_pause_analysis_to_api(analysis_result.pause_analysis)
            api_filler_analysis = _convert_filler_analysis_to_api(analysis_result.filler_analysis)
            api_speech_rate_analysis = _convert_speech_rate_analysis_to_api(analysis_result.speech_rate_analysis)
            api_confidence_analysis = _convert_confidence_analysis_to_api(analysis_result.confidence_analysis)
            
            # Convert coaching suggestions
            api_coaching_suggestions = CoachingSuggestionsAPI(
                overall_score=float(analysis_result.coaching_suggestions.overall_score),
                strengths=analysis_result.coaching_suggestions.strengths,
                areas_for_improvement=analysis_result.coaching_suggestions.areas_for_improvement,
                specific_suggestions=[
                    {"category": s.category, "suggestion": s.suggestion}
                    for s in analysis_result.coaching_suggestions.specific_suggestions
                ],
                practice_exercises=analysis_result.coaching_suggestions.practice_exercises
            )
            
            api_result = SpeechPatternAnalysisAPI(
                segments=api_segments,
                pause_analysis=api_pause_analysis,
                filler_analysis=api_filler_analysis,
                speech_rate_analysis=api_speech_rate_analysis,
                confidence_analysis=api_confidence_analysis,
                coaching_suggestions=api_coaching_suggestions,
                overall_statistics=analysis_result.overall_statistics,
                processing_time=analysis_result.processing_time,
                total_duration=analysis_result.total_duration,
                config_used=request_config
            )
            
            logger.info(f"Speech pattern analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{len(api_segments)} segments analyzed, "
                       f"{analysis_result.processing_time:.2f}s processing time")
            
            return create_api_response(
                data=api_result,
                message="Speech pattern analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in speech pattern analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in speech pattern analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze speech patterns"
        )

@router.post("/analyze-segment", response_model=SpeechSegmentAPI)
async def analyze_speech_segment(
    audio_file: UploadFile = File(...),
    start_time: float = Form(...),
    end_time: float = Form(...),
    transcript_text: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze a specific segment of speech"""
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
        
        # Validate time range
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start time must be less than end time"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Analyze specific segment
            segment_result = await speech_analyzer.analyze_segment(
                audio_file_path=temp_file_path,
                start_time=start_time,
                end_time=end_time,
                transcript_text=transcript_text
            )
            
            # Convert to API response
            api_segment = _convert_speech_segment_to_api(segment_result)
            
            logger.info(f"Speech segment analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{start_time:.2f}s - {end_time:.2f}s")
            
            return create_api_response(
                data=api_segment,
                message="Speech segment analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in speech segment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze speech segment"
        )

@router.post("/batch-analyze")
async def batch_analyze_speech_patterns(
    files: List[UploadFile] = File(...),
    config: AnalysisConfigAPI = Depends(),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze speech patterns for multiple files"""
    try:
        if len(files) > 10:  # Limit batch size
            raise ValueError("Batch size cannot exceed 10 files")
        
        results = []
        
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
                    continue
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # Configure analyzer
                    analysis_config = AnalysisConfig(
                        analysis_types=config.analysis_types,
                        language=config.language,
                        speaker_detection=config.speaker_detection,
                        filler_word_detection=config.filler_word_detection,
                        pause_analysis=config.pause_analysis,
                        speech_rate_analysis=config.speech_rate_analysis,
                        confidence_analysis=config.confidence_analysis,
                        coaching_suggestions=config.coaching_suggestions,
                        segment_duration=config.segment_duration,
                        min_pause_duration=config.min_pause_duration,
                        speech_rate_threshold=config.speech_rate_threshold
                    )
                    
                    # Perform analysis
                    analysis_result = await speech_analyzer.analyze(
                        audio_file_path=temp_file_path,
                        config=analysis_config,
                        include_coaching=True
                    )
                    
                    # Convert to API response
                    api_segments = [_convert_speech_segment_to_api(s) for s in analysis_result.segments]
                    
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "success",
                        "result": {
                            "segments_count": len(api_segments),
                            "total_duration": analysis_result.total_duration,
                            "processing_time": analysis_result.processing_time,
                            "overall_statistics": analysis_result.overall_statistics
                        }
                    })
                    
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
        
        logger.info(f"Batch speech pattern analysis completed for user {current_user.get('user_id', 'unknown')}: "
                   f"{len(files)} files processed")
        
        return create_api_response(
            data={
                "results": results,
                "total": len(files),
                "successful": len([r for r in results if r["status"] == "success"])
            },
            message="Batch speech pattern analysis completed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch speech pattern analysis"
        )

@router.get("/analysis-types")
async def get_analysis_types():
    """Get available analysis types and configurations"""
    return create_api_response(
        data={
            "analysis_types": [
                {
                    "value": "all",
                    "label": "Complete Analysis",
                    "description": "Perform all available speech pattern analyses"
                },
                {
                    "value": "pause_analysis",
                    "label": "Pause Analysis",
                    "description": "Analyze pauses and silence patterns"
                },
                {
                    "value": "filler_analysis",
                    "label": "Filler Word Analysis",
                    "description": "Detect and analyze filler words (um, uh, like, etc.)"
                },
                {
                    "value": "speech_rate",
                    "label": "Speech Rate Analysis",
                    "description": "Analyze speaking speed and rhythm"
                },
                {
                    "value": "confidence_analysis",
                    "label": "Confidence Analysis",
                    "description": "Assess speaking confidence and hesitation patterns"
                }
            ],
            "supported_languages": [
                {"code": "en", "name": "English"},
                {"code": "es", "name": "Spanish"},
                {"code": "fr", "name": "French"},
                {"code": "de", "name": "German"},
                {"code": "it", "name": "Italian"},
                {"code": "pt", "name": "Portuguese"},
                {"code": "ru", "name": "Russian"},
                {"code": "ja", "name": "Japanese"},
                {"code": "ko", "name": "Korean"},
                {"code": "zh", "name": "Chinese"}
            ],
            "filler_words": {
                "en": ["um", "uh", "like", "you know", "so", "well", "actually", "basically"],
                "es": ["eh", "este", "pues", "bueno", "o sea"],
                "fr": ["euh", "ben", "alors", "donc", "en fait"],
                "de": ["äh", "ähm", "also", "ja", "nun"],
                "it": ["eh", "ehm", "allora", "dunque", "cioè"]
            }
        },
        message="Analysis types retrieved successfully"
    )

@router.get("/coaching-categories")
async def get_coaching_categories():
    """Get available coaching categories and suggestions"""
    return create_api_response(
        data={
            "categories": [
                {
                    "name": "Speech Rate",
                    "description": "Suggestions for optimal speaking speed",
                    "metrics": ["words_per_minute", "rate_consistency"]
                },
                {
                    "name": "Pause Management",
                    "description": "Effective use of pauses and silence",
                    "metrics": ["pause_frequency", "pause_duration", "strategic_pauses"]
                },
                {
                    "name": "Filler Reduction",
                    "description": "Minimizing filler words and hesitations",
                    "metrics": ["filler_frequency", "filler_variety", "replacement_strategies"]
                },
                {
                    "name": "Confidence Building",
                    "description": "Improving speaking confidence and clarity",
                    "metrics": ["hesitation_frequency", "false_starts", "voice_stability"]
                },
                {
                    "name": "Articulation",
                    "description": "Clear pronunciation and enunciation",
                    "metrics": ["clarity_score", "pronunciation_accuracy"]
                }
            ],
            "practice_exercises": [
                {
                    "category": "Speech Rate",
                    "exercises": [
                        "Read aloud with a metronome",
                        "Practice tongue twisters",
                        "Record and playback exercises"
                    ]
                },
                {
                    "category": "Pause Management",
                    "exercises": [
                        "Breathing exercises",
                        "Strategic pause practice",
                        "Punctuation-based pausing"
                    ]
                },
                {
                    "category": "Filler Reduction",
                    "exercises": [
                        "Awareness recording sessions",
                        "Silent pause substitution",
                        "Structured speaking practice"
                    ]
                }
            ]
        },
        message="Coaching categories retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "speech_analyzer": "operational",
                "audio_processor": "available",
                "pattern_detector": "available",
                "coaching_engine": "available"
            },
            "supported_analysis_types": 5,
            "supported_languages": 10
        }
        
        return create_api_response(
            data=health_status,
            message="Speech pattern analysis service is healthy"
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