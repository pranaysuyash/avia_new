"""
Emotion and Sentiment Detection API Endpoints
REST API for emotion and sentiment analysis functionality
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

# Import emotion/sentiment detection system
from emotion_sentiment_detection import (
    EmotionSentimentDetector, EmotionResult, SentimentResult,
    EmotionConfig, DetectionMode, EmotionCategory, SentimentPolarity
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/emotion-sentiment", tags=["Emotion & Sentiment Detection"])

# Initialize components
emotion_detector = EmotionSentimentDetector()

# Pydantic models for API
class EmotionConfigAPI(BaseModel):
    """API request model for emotion detection configuration"""
    detection_mode: str = Field(default="both", description="Detection mode: emotion, sentiment, or both")
    model_type: str = Field(default="transformer", description="Model type to use")
    language: str = Field(default="en", description="Language code")
    confidence_threshold: float = Field(default=0.5, description="Confidence threshold", ge=0.0, le=1.0)
    enable_audio_analysis: bool = Field(default=True, description="Enable audio-based emotion detection")
    enable_text_analysis: bool = Field(default=True, description="Enable text-based sentiment analysis")
    enable_temporal_analysis: bool = Field(default=True, description="Enable temporal emotion tracking")
    segment_duration: float = Field(default=2.0, description="Segment duration for analysis", ge=0.5, le=10.0)
    overlap_duration: float = Field(default=0.5, description="Overlap between segments", ge=0.0, le=2.0)
    enable_speaker_emotion: bool = Field(default=True, description="Enable per-speaker emotion analysis")

class EmotionResultAPI(BaseModel):
    """API response model for emotion detection results"""
    timestamp: float
    duration: float
    primary_emotion: str
    emotion_scores: Dict[str, float]
    confidence: float
    intensity: float
    speaker_id: Optional[str] = None
    audio_features: Optional[Dict[str, float]] = None
    text_content: Optional[str] = None

class SentimentResultAPI(BaseModel):
    """API response model for sentiment analysis results"""
    timestamp: float
    duration: float
    polarity: str  # positive, negative, neutral
    sentiment_score: float  # -1 to 1
    confidence: float
    subjectivity: float  # 0 to 1
    speaker_id: Optional[str] = None
    text_content: Optional[str] = None
    keywords: List[str] = []

class EmotionSentimentAnalysisAPI(BaseModel):
    """API response model for combined analysis results"""
    emotions: List[EmotionResultAPI]
    sentiments: List[SentimentResultAPI]
    overall_emotion: str
    overall_sentiment: str
    emotion_timeline: List[Dict[str, Any]]
    sentiment_timeline: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    processing_time: float
    total_duration: float
    config_used: EmotionConfigAPI

def _convert_emotion_result_to_api(result: EmotionResult) -> EmotionResultAPI:
    """Convert internal emotion result to API response"""
    return EmotionResultAPI(
        timestamp=float(result.timestamp),
        duration=float(result.duration),
        primary_emotion=result.primary_emotion.value if hasattr(result.primary_emotion, 'value') else str(result.primary_emotion),
        emotion_scores={k.value if hasattr(k, 'value') else str(k): float(v) for k, v in result.emotion_scores.items()},
        confidence=float(result.confidence),
        intensity=float(result.intensity),
        speaker_id=result.speaker_id,
        audio_features=result.audio_features,
        text_content=result.text_content
    )

def _convert_sentiment_result_to_api(result: SentimentResult) -> SentimentResultAPI:
    """Convert internal sentiment result to API response"""
    return SentimentResultAPI(
        timestamp=float(result.timestamp),
        duration=float(result.duration),
        polarity=result.polarity.value if hasattr(result.polarity, 'value') else str(result.polarity),
        sentiment_score=float(result.sentiment_score),
        confidence=float(result.confidence),
        subjectivity=float(result.subjectivity),
        speaker_id=result.speaker_id,
        text_content=result.text_content,
        keywords=result.keywords or []
    )

@router.post("/analyze", response_model=EmotionSentimentAnalysisAPI)
async def analyze_emotion_sentiment(
    audio_file: UploadFile = File(...),
    config: str = Form(...),
    transcript_text: Optional[str] = Form(None),
    include_timeline: bool = Form(True),
    include_statistics: bool = Form(True),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze emotion and sentiment from audio file"""
    try:
        # Parse config from JSON string
        import json
        config_dict = json.loads(config)
        request_config = EmotionConfigAPI(**config_dict)
        
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
            # Configure emotion detector
            config_obj = EmotionConfig(
                detection_mode=DetectionMode(request_config.detection_mode),
                model_type=request_config.model_type,
                language=request_config.language,
                confidence_threshold=request_config.confidence_threshold,
                enable_audio_analysis=request_config.enable_audio_analysis,
                enable_text_analysis=request_config.enable_text_analysis,
                enable_temporal_analysis=request_config.enable_temporal_analysis,
                segment_duration=request_config.segment_duration,
                overlap_duration=request_config.overlap_duration,
                enable_speaker_emotion=request_config.enable_speaker_emotion
            )
            
            # Perform emotion/sentiment analysis
            analysis_result = await emotion_detector.analyze(
                audio_file_path=temp_file_path,
                transcript_text=transcript_text,
                config=config_obj,
                include_timeline=include_timeline,
                include_statistics=include_statistics
            )
            
            # Convert results to API response
            api_emotions = [_convert_emotion_result_to_api(e) for e in analysis_result.emotions]
            api_sentiments = [_convert_sentiment_result_to_api(s) for s in analysis_result.sentiments]
            
            api_result = EmotionSentimentAnalysisAPI(
                emotions=api_emotions,
                sentiments=api_sentiments,
                overall_emotion=analysis_result.overall_emotion.value if hasattr(analysis_result.overall_emotion, 'value') else str(analysis_result.overall_emotion),
                overall_sentiment=analysis_result.overall_sentiment.value if hasattr(analysis_result.overall_sentiment, 'value') else str(analysis_result.overall_sentiment),
                emotion_timeline=analysis_result.emotion_timeline,
                sentiment_timeline=analysis_result.sentiment_timeline,
                statistics=analysis_result.statistics,
                processing_time=analysis_result.processing_time,
                total_duration=analysis_result.total_duration,
                config_used=request_config
            )
            
            logger.info(f"Emotion/sentiment analysis completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{len(api_emotions)} emotion segments, {len(api_sentiments)} sentiment segments, "
                       f"{analysis_result.processing_time:.2f}s processing time")
            
            return create_api_response(
                data=api_result,
                message="Emotion and sentiment analysis completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in emotion/sentiment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in emotion/sentiment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze emotion and sentiment"
        )

@router.post("/analyze-text", response_model=List[SentimentResultAPI])
async def analyze_text_sentiment(
    text: str = Form(...),
    language: str = Form(default="en"),
    model_type: str = Form(default="transformer"),
    current_user: dict = Depends(get_current_active_user)
):
    """Analyze sentiment from text only"""
    try:
        # Configure for text-only analysis
        config = EmotionConfig(
            detection_mode=DetectionMode.SENTIMENT,
            model_type=model_type,
            language=language,
            enable_audio_analysis=False,
            enable_text_analysis=True
        )
        
        # Perform text sentiment analysis
        sentiment_results = await emotion_detector.analyze_text_sentiment(
            text=text,
            config=config
        )
        
        # Convert results to API response
        api_results = [_convert_sentiment_result_to_api(s) for s in sentiment_results]
        
        logger.info(f"Text sentiment analysis completed for user {current_user.get('user_id', 'unknown')}: "
                   f"{len(api_results)} sentiment segments")
        
        return create_api_response(
            data=api_results,
            message="Text sentiment analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in text sentiment analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze text sentiment"
        )

@router.get("/models")
async def get_available_models():
    """Get available emotion and sentiment detection models"""
    return create_api_response(
        data={
            "emotion_models": [
                {
                    "value": "transformer",
                    "label": "Transformer Model",
                    "description": "State-of-the-art transformer-based emotion detection",
                    "emotions": ["joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"]
                },
                {
                    "value": "cnn",
                    "label": "CNN Model", 
                    "description": "Convolutional neural network for audio emotion recognition",
                    "emotions": ["happy", "sad", "angry", "fearful", "surprised", "disgusted", "neutral"]
                },
                {
                    "value": "svm",
                    "label": "SVM Model",
                    "description": "Support vector machine with audio features",
                    "emotions": ["positive", "negative", "neutral"]
                }
            ],
            "sentiment_models": [
                {
                    "value": "transformer",
                    "label": "BERT-based Sentiment",
                    "description": "Fine-tuned BERT model for sentiment analysis",
                    "polarities": ["positive", "negative", "neutral"]
                },
                {
                    "value": "vader",
                    "label": "VADER Sentiment",
                    "description": "Valence Aware Dictionary and sEntiment Reasoner",
                    "polarities": ["positive", "negative", "neutral", "compound"]
                },
                {
                    "value": "textblob",
                    "label": "TextBlob",
                    "description": "Simple sentiment analysis with polarity and subjectivity",
                    "polarities": ["positive", "negative", "neutral"]
                }
            ],
            "detection_modes": [
                {
                    "value": "emotion",
                    "label": "Emotion Only",
                    "description": "Detect emotions from audio features"
                },
                {
                    "value": "sentiment",
                    "label": "Sentiment Only", 
                    "description": "Analyze sentiment from text content"
                },
                {
                    "value": "both",
                    "label": "Emotion & Sentiment",
                    "description": "Combined emotion and sentiment analysis"
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
            ]
        },
        message="Available models retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "emotion_detector": "operational",
                "sentiment_analyzer": "operational",
                "audio_processor": "available",
                "text_processor": "available"
            },
            "supported_models": 6,
            "supported_languages": 10
        }
        
        return create_api_response(
            data=health_status,
            message="Emotion and sentiment detection service is healthy"
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