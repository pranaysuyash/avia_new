"""
Transcription API Endpoints - With Centralized Validation
REST API for audio/video transcription with improved exception handling and centralized validation
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional, List, Dict, Any
import os
import sys
import tempfile
import logging
from datetime import datetime
from pathlib import Path
import asyncio
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import auth_required, write_required, create_api_response
from api.models import TranscriptionRequest, TranscriptionResponse, TranscriptionResult
from api.models import FileUploadResponse

# Import centralized validation functions
from utils import (
    validate_media_file, validate_file_size, sanitize_filename,
    AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_CONTENT_TYPES, VIDEO_CONTENT_TYPES
)

# Import transcription modules
try:
    from stt_complete import transcribe_audio_complete
    from api_session_manager import SessionManager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import required modules: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcription", tags=["Transcription"])

# Initialize session manager
try:
    session_manager = SessionManager()
except Exception as e:
    logger.error(f"Failed to initialize session manager: {e}")
    raise


@router.post("/upload")
async def upload_audio_file(
    file: UploadFile = File(...),
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Upload audio/video file for transcription"""
    # Validate file presence
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename) if file.filename else "unnamed_file"
    
    # Validate file type using centralized validation
    is_valid, media_type = validate_media_file(safe_filename, file.content_type)
    
    if not is_valid or media_type not in ['audio', 'video']:
        # Get allowed extensions for error message
        allowed_extensions = AUDIO_EXTENSIONS + VIDEO_EXTENSIONS
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    temp_path = None
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check if file is empty
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Use centralized file size validation
        max_size_mb = 2048  # 2GB limit
        if not validate_file_size(file_size, max_size_mb * 1024 * 1024):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
            )
        
        # Save file temporarily
        try:
            suffix = os.path.splitext(safe_filename)[1] or '.tmp'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(content)
                temp_path = tmp_file.name
        except OSError as e:
            if "No space left" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
                    detail="Insufficient storage space on server"
                )
            else:
                logger.error(f"OS error while saving file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save file to temporary storage"
                )
        except IOError as e:
            logger.error(f"IO error while saving file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to write file to disk"
            )
        
        # Generate file ID
        try:
            file_id = f"{media_type}_{user_id}_{int(datetime.now().timestamp())}"
        except (ValueError, OSError) as e:
            logger.error(f"Failed to generate file ID: {e}")
            file_id = f"{media_type}_{user_id}_default"
        
        # Store file info in session
        try:
            session_data = {
                'uploaded_file_path': temp_path,
                'uploaded_file_name': safe_filename,
                'uploaded_file_size': file_size,
                'uploaded_file_type': file.content_type or f'{media_type}/*',
                'media_type': media_type,
                'file_id': file_id
            }
            session_manager.set_session_data(user_id, session_data)
        except AttributeError as e:
            logger.error(f"Session manager error: {e}")
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except (OSError, FileNotFoundError):
                    pass
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session management service unavailable"
            )
        
        return create_api_response({
            "file_id": file_id,
            "file_name": safe_filename,
            "file_size": file_size,
            "media_type": media_type,
            "content_type": file.content_type or f'{media_type}/*'
        }, "File uploaded successfully")
        
    except HTTPException:
        # Clean up temp file on HTTP errors
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass
        raise
    except MemoryError as e:
        logger.error(f"Memory error during file upload: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large to process in available memory"
        )


@router.post("/process/{file_id}")
async def process_transcription(
    file_id: str,
    request: TranscriptionRequest,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Process uploaded file for transcription"""
    # Validate file_id
    if not file_id or not isinstance(file_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID"
        )
    
    # Get file info from session
    try:
        session_data = session_manager.get_session_data(user_id)
    except AttributeError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management service unavailable"
        )
    
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active session found. Please upload a file first."
        )
    
    if 'uploaded_file_path' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No uploaded file found. Upload a file first."
        )
    
    if session_data.get('file_id') != file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File ID '{file_id}' not found"
        )
    
    file_path = session_data['uploaded_file_path']
    
    # Verify file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file no longer exists. Please upload again."
        )
    
    # Verify file is readable
    if not os.access(file_path, os.R_OK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot read uploaded file. Permission denied."
        )
    
    try:
        # Process transcription with timeout
        result = await asyncio.wait_for(
            transcribe_audio_complete(
                file_path,
                use_api=request.use_api,
                language=request.language,
                model=request.model,
                enable_diarization=request.enable_diarization,
                extract_entities=request.extract_entities
            ),
            timeout=300.0  # 5 minute timeout
        )
    except asyncio.TimeoutError:
        logger.error("Transcription processing timed out after 5 minutes")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Transcription processing timed out. Try with a smaller file or simpler model."
        )
    except FileNotFoundError as e:
        logger.error(f"File not found during transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found during processing"
        )
    except PermissionError as e:
        logger.error(f"Permission denied during transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied while processing file"
        )
    except MemoryError as e:
        logger.error(f"Out of memory during transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to process file. Try with a smaller file or model."
        )
    except ImportError as e:
        logger.error(f"Missing transcription dependency: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service unavailable. Missing required components."
        )
    except ValueError as e:
        logger.error(f"Invalid transcription parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transcription parameters: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Transcription API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service error"
        )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcription returned no result"
        )
    
    # Store result in session
    try:
        transcription_id = f"transcription_{user_id}_{int(datetime.now().timestamp())}"
        session_data['transcription_result'] = {
            'transcription_id': transcription_id,
            'result': result,
            'file_name': session_data['uploaded_file_name'],
            'processing_options': request.dict()
        }
        session_manager.set_session_data(user_id, session_data)
    except (AttributeError, TypeError) as e:
        logger.error(f"Failed to store transcription result: {e}")
        # Continue - still return the result to user
    
    # Extract key information for response
    response_data = {
        "transcription_id": transcription_id if 'transcription_id' in locals() else "temp_id",
        "text": result.get('transcription', {}).get('text', ''),
        "duration": result.get('transcription', {}).get('duration', 0),
        "word_count": result.get('transcription', {}).get('word_count', 0),
        "language": result.get('transcription', {}).get('language', request.language),
        "confidence": result.get('transcription', {}).get('confidence'),
        "processing_time": result.get('metadata', {}).get('processing_time', 0)
    }
    
    # Add entities if extracted
    if request.extract_entities and 'entities' in result:
        entity_counts = {}
        for entity_type, entities in result['entities'].items():
            entity_counts[entity_type] = len(entities)
        response_data['entity_counts'] = entity_counts
    
    # Add speaker info if diarization was enabled
    if request.enable_diarization and 'diarization' in result:
        response_data['speaker_count'] = result['diarization'].get('speaker_count', 0)
    
    return create_api_response(response_data, "Transcription completed successfully")


@router.get("/result/{transcription_id}")
async def get_transcription_result(
    transcription_id: str,
    include_entities: bool = True,
    include_diarization: bool = True,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Get full transcription result with all details"""
    # Validate transcription_id
    if not transcription_id or not isinstance(transcription_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcription ID"
        )
    
    # Get session data
    try:
        session_data = session_manager.get_session_data(user_id)
    except AttributeError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management service unavailable"
        )
    
    if not session_data or 'transcription_result' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transcription result found"
        )
    
    stored_result = session_data['transcription_result']
    
    if stored_result.get('transcription_id') != transcription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcription ID '{transcription_id}' not found"
        )
    
    # Build response
    result = stored_result['result']
    
    response = {
        "transcription_id": transcription_id,
        "file_name": stored_result['file_name'],
        "processing_options": stored_result['processing_options'],
        "transcription": result.get('transcription', {}),
        "metadata": result.get('metadata', {})
    }
    
    # Add entities if requested
    if include_entities and 'entities' in result:
        response['entities'] = result['entities']
    
    # Add diarization if requested
    if include_diarization and 'diarization' in result:
        response['diarization'] = result['diarization']
    
    return create_api_response(response, "Transcription result retrieved")


@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages for transcription"""
    languages = [
        {"code": "auto", "name": "Auto-detect", "description": "Automatically detect the language"},
        {"code": "en", "name": "English", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "es", "name": "Spanish", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "fr", "name": "French", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "de", "name": "German", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "it", "name": "Italian", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "pt", "name": "Portuguese", "supported_models": ["tiny", "base", "small", "medium", "large"]},
        {"code": "ru", "name": "Russian", "supported_models": ["base", "small", "medium", "large"]},
        {"code": "ja", "name": "Japanese", "supported_models": ["base", "small", "medium", "large"]},
        {"code": "ko", "name": "Korean", "supported_models": ["base", "small", "medium", "large"]},
        {"code": "zh", "name": "Chinese", "supported_models": ["base", "small", "medium", "large"]},
        {"code": "ar", "name": "Arabic", "supported_models": ["base", "small", "medium", "large"]},
        {"code": "hi", "name": "Hindi", "supported_models": ["base", "small", "medium", "large"]}
    ]
    
    return create_api_response({
        "languages": languages,
        "default": "auto",
        "note": "Language detection accuracy improves with larger models"
    }, "Supported languages retrieved")


@router.get("/supported-models")
async def get_supported_models():
    """Get list of supported Whisper models"""
    models = [
        {
            "name": "tiny",
            "size_mb": 39,
            "description": "Fastest model, lowest accuracy",
            "relative_speed": 10,
            "languages": "All supported"
        },
        {
            "name": "base",
            "size_mb": 74,
            "description": "Good balance of speed and accuracy",
            "relative_speed": 7,
            "languages": "All supported"
        },
        {
            "name": "small",
            "size_mb": 244,
            "description": "Better accuracy, moderate speed",
            "relative_speed": 4,
            "languages": "All supported"
        },
        {
            "name": "medium",
            "size_mb": 769,
            "description": "High accuracy, slower processing",
            "relative_speed": 2,
            "languages": "All supported"
        },
        {
            "name": "large",
            "size_mb": 1550,
            "description": "Best accuracy, slowest processing",
            "relative_speed": 1,
            "languages": "All supported"
        }
    ]
    
    return create_api_response({
        "models": models,
        "default": "base",
        "recommendation": "Use 'base' for general use, 'small' or 'medium' for better accuracy"
    }, "Supported models retrieved")