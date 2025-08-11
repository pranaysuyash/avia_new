"""
Whisper Advanced Integration API Endpoints
REST API for advanced Whisper transcription with custom configurations
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

# Import Whisper advanced system
from whisper_advanced_processor import (
    WhisperAdvancedProcessor, WhisperConfig, WhisperModel, 
    TranscriptionResult, LanguageDetectionResult, SpeakerDiarizationResult,
    create_high_accuracy_config, create_fast_processing_config, create_balanced_config
)
from whisper_audio_preprocessor import AudioPreprocessor, AudioConfig, ProcessingMode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whisper-advanced", tags=["Whisper Advanced"])

# Initialize components
whisper_processor = WhisperAdvancedProcessor()
audio_preprocessor = AudioPreprocessor()

# Pydantic models for API
class WhisperConfigAPI(BaseModel):
    """API request model for Whisper configuration"""
    model: str = Field(default="whisper-1", description="Whisper model to use")
    language: Optional[str] = Field(None, description="Language code (auto-detect if None)")
    prompt: Optional[str] = Field(None, description="Custom prompt for context")
    response_format: str = Field(default="json", description="Response format")
    temperature: float = Field(default=0.0, description="Sampling temperature", ge=0.0, le=1.0)
    enable_language_detection: bool = Field(default=True, description="Enable language detection")
    enable_confidence_analysis: bool = Field(default=True, description="Enable confidence analysis")
    enable_custom_vocabulary: bool = Field(default=False, description="Enable custom vocabulary")
    confidence_threshold: float = Field(default=0.8, description="Confidence threshold", ge=0.0, le=1.0)
    chunk_length_s: int = Field(default=30, description="Chunk length in seconds", ge=10, le=60)
    enable_word_timestamps: bool = Field(default=True, description="Enable word-level timestamps")
    enable_speaker_detection: bool = Field(default=False, description="Enable speaker detection")

class CustomVocabularyConfigAPI(BaseModel):
    """API request model for custom vocabulary configuration"""
    vocabulary_terms: List[str] = Field(default=[], description="Custom vocabulary terms")
    domain_specific_terms: List[str] = Field(default=[], description="Domain-specific terminology")
    proper_nouns: List[str] = Field(default=[], description="Proper nouns and names")
    technical_terms: List[str] = Field(default=[], description="Technical terminology")
    boost_factor: float = Field(default=1.5, description="Vocabulary boost factor", ge=1.0, le=3.0)

class PromptConfigAPI(BaseModel):
    """API request model for prompt configuration"""
    context_prompt: Optional[str] = Field(None, description="Context prompt for transcription")
    style_prompt: Optional[str] = Field(None, description="Style guidance prompt")
    domain_prompt: Optional[str] = Field(None, description="Domain-specific prompt")
    format_prompt: Optional[str] = Field(None, description="Format guidance prompt")

class TranscriptionResultAPI(BaseModel):
    """API response model for transcription results"""
    text: str
    language: Optional[str]
    language_confidence: Optional[float]
    segments: List[Dict[str, Any]]
    words: Optional[List[Dict[str, Any]]]
    confidence_analysis: Optional[Dict[str, Any]]
    processing_time: float
    model_used: str
    config_used: WhisperConfigAPI

class LanguageDetectionResultAPI(BaseModel):
    """API response model for language detection"""
    detected_language: str
    confidence: float
    alternative_languages: List[Dict[str, float]]
    language_segments: Optional[List[Dict[str, Any]]]

class BatchTranscriptionAPI(BaseModel):
    """API response model for batch transcription"""
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    total_processing_time: float

@router.post("/transcribe", response_model=TranscriptionResultAPI)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    config: str = Form(...),
    custom_vocabulary: Optional[str] = Form(None),
    prompt_config: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_active_user)
):
    """Transcribe audio with advanced Whisper configuration"""
    try:
        # Parse config from JSON string
        import json
        config_dict = json.loads(config)
        request_config = WhisperConfigAPI(**config_dict)
        
        # Parse optional configurations
        vocab_config = None
        if custom_vocabulary:
            vocab_dict = json.loads(custom_vocabulary)
            vocab_config = CustomVocabularyConfigAPI(**vocab_dict)
        
        prompt_cfg = None
        if prompt_config:
            prompt_dict = json.loads(prompt_config)
            prompt_cfg = PromptConfigAPI(**prompt_dict)
        
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac', 'audio/mp4'
        }
        
        if audio_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {audio_file.content_type}"
            )
        
        # Check file size (Whisper has 25MB limit)
        if audio_file.size and audio_file.size > 25 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 25MB limit for Whisper API"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # First preprocess the audio for optimal Whisper performance
            audio_config = AudioConfig(
                processing_mode=ProcessingMode.BALANCED,
                enable_noise_reduction=True,
                enable_enhancement=True,
                enable_normalization=True
            )
            
            preprocessing_result = audio_preprocessor.preprocess_audio(
                temp_file_path, 
                config=audio_config
            )
            
            # Configure Whisper processor
            whisper_config = WhisperConfig(
                model_size=WhisperModel.BASE if request_config.model == "whisper-1" else WhisperModel.BASE,
                language=request_config.language,
                task="transcribe",
                temperature=request_config.temperature,
                word_timestamps=request_config.enable_word_timestamps,
                enable_diarization=request_config.enable_speaker_detection,
                initial_prompt=request_config.prompt,
                custom_vocabulary=vocab_config.vocabulary_terms if vocab_config else []
            )
            
            # Perform transcription using preprocessed audio
            transcription_result = await whisper_processor.transcribe(
                preprocessing_result.processed_audio_path,
                config=whisper_config
            )
            
            # Convert segments to API format
            segments_api = []
            for segment in transcription_result.segments:
                segments_api.append({
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "confidence": segment.confidence,
                    "speaker_id": segment.speaker_id
                })
            
            # Convert words to API format if available
            words_api = []
            for segment in transcription_result.segments:
                for word in segment.words:
                    words_api.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.confidence
                    })
            
            # Convert to API response
            api_result = TranscriptionResultAPI(
                text=transcription_result.text,
                language=transcription_result.language,
                language_confidence=float(transcription_result.language_detection.language_probability) if transcription_result.language_detection else None,
                segments=segments_api,
                words=words_api if request_config.enable_word_timestamps else None,
                confidence_analysis={
                    "overall_confidence": transcription_result.confidence_score,
                    "preprocessing_quality": preprocessing_result.processed_metrics.quality_score,
                    "quality_improvement": preprocessing_result.quality_improvement
                },
                processing_time=float(transcription_result.processing_time + preprocessing_result.processing_time),
                model_used=transcription_result.model_used,
                config_used=request_config
            )
            
            logger.info(f"Whisper transcription completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{len(transcription_result.text)} characters, "
                       f"{transcription_result.processing_time:.2f}s processing time")
            
            return create_api_response(
                data=api_result,
                message="Transcription completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except ValueError as e:
        logger.error(f"Validation error in Whisper transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in Whisper transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )

@router.post("/detect-language", response_model=LanguageDetectionResultAPI)
async def detect_language(
    audio_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Detect language from audio file"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm', 'audio/aac', 'audio/mp4'
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
            # Perform language detection
            detection_result = await whisper_processor.detect_language(
                audio_file_path=temp_file_path
            )
            
            # Convert to API response
            api_result = LanguageDetectionResultAPI(
                detected_language=detection_result.detected_language,
                confidence=float(detection_result.language_probability),
                alternative_languages=[
                    {lang: float(prob)} for lang, prob in detection_result.all_language_probs.items()
                ],
                language_segments=None  # Not implemented in current version
            )
            
            logger.info(f"Language detection completed for user {current_user.get('user_id', 'unknown')}: "
                       f"{detection_result.detected_language} ({detection_result.confidence:.2f})")
            
            return create_api_response(
                data=api_result,
                message="Language detection completed successfully"
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to detect language"
        )

@router.post("/batch-transcribe")
async def batch_transcribe(
    files: List[UploadFile] = File(...),
    config: WhisperConfigAPI = Depends(),
    current_user: dict = Depends(get_current_active_user)
):
    """Batch transcribe multiple audio files"""
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
                    'audio/ogg', 'audio/webm', 'audio/aac', 'audio/mp4'
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
                
                # Check file size
                if file.size and file.size > 25 * 1024 * 1024:
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "error",
                        "error": "File size exceeds 25MB limit"
                    })
                    failed += 1
                    continue
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # Preprocess audio for optimal performance
                    audio_config = AudioConfig(processing_mode=ProcessingMode.FAST)
                    preprocessing_result = audio_preprocessor.preprocess_audio(
                        temp_file_path, 
                        config=audio_config
                    )
                    
                    # Configure Whisper processor
                    whisper_config = WhisperConfig(
                        model_size=WhisperModel.BASE,
                        language=config.language,
                        temperature=config.temperature,
                        word_timestamps=config.enable_word_timestamps,
                        enable_diarization=config.enable_speaker_detection,
                        initial_prompt=config.prompt
                    )
                    
                    # Perform transcription
                    transcription_result = await whisper_processor.transcribe(
                        preprocessing_result.processed_audio_path,
                        config=whisper_config
                    )
                    
                    results.append({
                        "index": i,
                        "filename": file.filename,
                        "status": "success",
                        "result": {
                            "text": transcription_result.text,
                            "language": transcription_result.language,
                            "language_confidence": transcription_result.language_detection.language_probability if transcription_result.language_detection else None,
                            "processing_time": transcription_result.processing_time + preprocessing_result.processing_time,
                            "word_count": transcription_result.word_count,
                            "segments_count": len(transcription_result.segments),
                            "confidence_score": transcription_result.confidence_score,
                            "quality_improvement": preprocessing_result.quality_improvement
                        }
                    })
                    
                    total_processing_time += transcription_result.processing_time
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
        total_words = sum(r["result"]["word_count"] for r in successful_results)
        avg_processing_time = total_processing_time / successful if successful > 0 else 0
        
        summary = {
            "total_files": len(files),
            "successful": successful,
            "failed": failed,
            "total_words": total_words,
            "average_processing_time": avg_processing_time,
            "total_processing_time": total_processing_time
        }
        
        api_result = BatchTranscriptionAPI(
            results=results,
            summary=summary,
            total_processing_time=total_processing_time
        )
        
        logger.info(f"Batch Whisper transcription completed for user {current_user.get('user_id', 'unknown')}: "
                   f"{successful} successful, {failed} failed")
        
        return create_api_response(
            data=api_result,
            message=f"Batch transcription completed: {successful} successful, {failed} failed"
        )
        
    except ValueError as e:
        logger.error(f"Validation error in batch transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in batch transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch transcription"
        )

@router.get("/models")
async def get_available_models():
    """Get available Whisper models and their capabilities"""
    return create_api_response(
        data={
            "models": [
                {
                    "id": "whisper-1",
                    "name": "Whisper v1",
                    "description": "OpenAI's Whisper model for speech recognition",
                    "max_file_size_mb": 25,
                    "supported_formats": ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"],
                    "features": [
                        "Multi-language support",
                        "Word-level timestamps",
                        "Language detection",
                        "Custom prompts",
                        "Temperature control"
                    ]
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
                {"code": "zh", "name": "Chinese"},
                {"code": "ar", "name": "Arabic"},
                {"code": "hi", "name": "Hindi"},
                {"code": "tr", "name": "Turkish"},
                {"code": "pl", "name": "Polish"},
                {"code": "nl", "name": "Dutch"}
            ],
            "response_formats": [
                {
                    "format": "json",
                    "description": "Detailed JSON response with segments and metadata"
                },
                {
                    "format": "text",
                    "description": "Plain text transcription only"
                }
            ]
        },
        message="Available models retrieved successfully"
    )

@router.get("/presets")
async def get_transcription_presets():
    """Get predefined transcription presets"""
    return create_api_response(
        data={
            "presets": [
                {
                    "name": "High Accuracy",
                    "description": "Maximum accuracy with detailed analysis",
                    "config": {
                        "model": "whisper-1",
                        "temperature": 0.0,
                        "enable_language_detection": True,
                        "enable_confidence_analysis": True,
                        "enable_word_timestamps": True,
                        "confidence_threshold": 0.9,
                        "chunk_length_s": 30
                    }
                },
                {
                    "name": "Fast Processing",
                    "description": "Optimized for speed with good accuracy",
                    "config": {
                        "model": "whisper-1",
                        "temperature": 0.2,
                        "enable_language_detection": False,
                        "enable_confidence_analysis": False,
                        "enable_word_timestamps": False,
                        "confidence_threshold": 0.7,
                        "chunk_length_s": 60
                    }
                },
                {
                    "name": "Multi-language",
                    "description": "Optimized for multi-language content",
                    "config": {
                        "model": "whisper-1",
                        "temperature": 0.1,
                        "enable_language_detection": True,
                        "enable_confidence_analysis": True,
                        "enable_word_timestamps": True,
                        "confidence_threshold": 0.8,
                        "chunk_length_s": 20
                    }
                },
                {
                    "name": "Technical Content",
                    "description": "Optimized for technical and specialized content",
                    "config": {
                        "model": "whisper-1",
                        "temperature": 0.0,
                        "enable_language_detection": True,
                        "enable_confidence_analysis": True,
                        "enable_custom_vocabulary": True,
                        "enable_word_timestamps": True,
                        "confidence_threshold": 0.85,
                        "chunk_length_s": 25
                    }
                },
                {
                    "name": "Podcast/Interview",
                    "description": "Optimized for conversational content",
                    "config": {
                        "model": "whisper-1",
                        "temperature": 0.3,
                        "enable_language_detection": True,
                        "enable_confidence_analysis": True,
                        "enable_speaker_detection": True,
                        "enable_word_timestamps": True,
                        "confidence_threshold": 0.75,
                        "chunk_length_s": 30
                    }
                }
            ]
        },
        message="Transcription presets retrieved successfully"
    )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "components": {
                "whisper_transcriber": "operational",
                "openai_api": "available",
                "language_detection": "available",
                "custom_vocabulary": "available"
            },
            "supported_models": 1,
            "supported_languages": 15,
            "max_file_size_mb": 25
        }
        
        return create_api_response(
            data=health_status,
            message="Whisper advanced service is healthy"
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