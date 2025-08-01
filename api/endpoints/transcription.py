"""
Transcription API Endpoints
REST API for audio/video transcription functionality
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import sys
import tempfile
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..auth import auth_required, write_required, create_api_response, create_error_response
from ..models import (
    TranscriptionRequest, TranscriptionResponse, TranscriptionResult,
    Entity, SpeakerSegment, FileUploadResponse
)

# Import transcription modules
from enhanced_transcription import EnhancedTranscription
from ner_processor import NERProcessor
from session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcription", tags=["Transcription"])

# Initialize components
transcription_engine = EnhancedTranscription()
ner_processor = NERProcessor()
session_manager = SessionManager()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    user_id: str = Depends(auth_required)
):
    """Upload audio/video file for transcription"""
    try:
        # Validate file type
        allowed_types = {
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Check file size (2GB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 2048 * 1024 * 1024:  # 2GB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 2GB limit"
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Generate file ID
        file_id = f"upload_{user_id}_{int(datetime.now().timestamp())}"
        
        # Store file info in session
        session_manager.set_session_data(user_id, {
            'uploaded_file_path': temp_path,
            'uploaded_file_name': file.filename,
            'uploaded_file_size': file_size,
            'uploaded_file_type': file.content_type,
            'file_id': file_id
        })
        
        return create_api_response({
            "file_id": file_id,
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type
        }, "File uploaded successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )


@router.post("/process", response_model=TranscriptionResponse)
async def process_transcription(
    request: TranscriptionRequest,
    file_id: Optional[str] = None,
    user_id: str = Depends(write_required)
):
    """Process uploaded file for transcription"""
    try:
        # Get file info from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'uploaded_file_path' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No uploaded file found. Upload a file first."
            )
        
        file_path = session_data['uploaded_file_path']
        file_name = session_data.get('uploaded_file_name', 'unknown')
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded file not found"
            )
        
        start_time = datetime.now()
        
        # Process transcription
        transcription_result = await transcription_engine.transcribe_file(
            file_path,
            use_api=request.use_api,
            language=request.language if request.language != "auto" else None,
            model=request.model
        )
        
        if not transcription_result or not transcription_result.get('text'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Transcription failed or returned empty result"
            )
        
        # Extract entities if requested
        entities = []
        if request.extract_entities:
            try:
                entity_results = await ner_processor.extract_entities(
                    transcription_result['text'],
                    use_advanced=request.use_api
                )
                
                entities = [
                    Entity(
                        text=entity['text'],
                        label=entity['label'],
                        start=entity.get('start', 0),
                        end=entity.get('end', 0),
                        confidence=entity.get('confidence')
                    )
                    for entity in entity_results.get('entities', [])
                ]
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
        
        # Speaker diarization if requested
        speakers = None
        if request.enable_diarization:
            try:
                from speaker_diarization.diarization_manager import DiarizationManager
                diarization_manager = DiarizationManager()
                
                diarization_result = await diarization_manager.process_audio(file_path)
                
                speakers = [
                    SpeakerSegment(
                        speaker_id=segment.speaker_id,
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=segment.text,
                        confidence=segment.confidence
                    )
                    for segment in diarization_result.segments
                ]
            except Exception as e:
                logger.warning(f"Speaker diarization failed: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Generate transcript ID
        transcript_id = f"transcript_{user_id}_{int(start_time.timestamp())}"
        
        # Create result
        result = TranscriptionResult(
            transcript_id=transcript_id,
            text=transcription_result['text'],
            language=transcription_result.get('language', 'unknown'),
            duration=transcription_result.get('duration', 0.0),
            word_count=len(transcription_result['text'].split()),
            entities=entities,
            speakers=speakers,
            confidence=transcription_result.get('confidence'),
            processing_time=processing_time,
            created_at=start_time
        )
        
        # Store result in session
        session_manager.store_result(user_id, {
            'transcript_id': transcript_id,
            'result': result.dict(),
            'file_name': file_name,
            'processing_options': request.dict()
        })
        
        # Cleanup temp file
        try:
            os.unlink(file_path)
        except:
            pass
        
        return create_api_response(result, "Transcription completed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transcription processing failed"
        )


@router.get("/status/{transcript_id}")
async def get_transcription_status(
    transcript_id: str,
    user_id: str = Depends(auth_required)
):
    """Get transcription status by ID"""
    try:
        # Get stored result
        results = session_manager.get_stored_results(user_id)
        
        for result in results:
            if result.get('transcript_id') == transcript_id:
                return create_api_response({
                    "transcript_id": transcript_id,
                    "status": "completed",
                    "result": result['result']
                }, "Transcription found")
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Status check failed"
        )


@router.get("/history")
async def get_transcription_history(
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(auth_required)
):
    """Get user's transcription history"""
    try:
        results = session_manager.get_stored_results(user_id)
        
        # Apply pagination
        total_count = len(results)
        paginated_results = results[offset:offset + limit]
        
        return create_api_response({
            "transcriptions": [
                {
                    "transcript_id": result['transcript_id'],
                    "file_name": result.get('file_name', 'unknown'),
                    "created_at": result['result']['created_at'],
                    "duration": result['result']['duration'],
                    "word_count": result['result']['word_count'],
                    "language": result['result']['language'],
                    "has_speakers": len(result['result'].get('speakers', [])) > 0,
                    "has_entities": len(result['result'].get('entities', [])) > 0
                }
                for result in paginated_results
            ],
            "total_count": total_count,
            "page": offset // limit + 1,
            "per_page": limit
        }, "Transcription history retrieved")
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcription history"
        )


@router.delete("/{transcript_id}")
async def delete_transcription(
    transcript_id: str,
    user_id: str = Depends(write_required)
):
    """Delete a transcription"""
    try:
        # This would typically delete from database
        # For now, we'll remove from session
        results = session_manager.get_stored_results(user_id)
        
        updated_results = [
            result for result in results 
            if result.get('transcript_id') != transcript_id
        ]
        
        if len(updated_results) == len(results):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        # Update session with filtered results
        session_data = session_manager.get_session_data(user_id) or {}
        session_data['stored_results'] = updated_results
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(
            {"transcript_id": transcript_id}, 
            "Transcription deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transcription"
        )


@router.get("/supported-formats")
async def get_supported_formats():
    """Get supported audio/video formats"""
    return create_api_response({
        "audio_formats": [
            {"extension": "mp3", "mime_type": "audio/mpeg"},
            {"extension": "wav", "mime_type": "audio/wav"},
            {"extension": "m4a", "mime_type": "audio/m4a"},
            {"extension": "flac", "mime_type": "audio/flac"}
        ],
        "video_formats": [
            {"extension": "mp4", "mime_type": "video/mp4"},
            {"extension": "avi", "mime_type": "video/avi"},
            {"extension": "mov", "mime_type": "video/mov"},
            {"extension": "mkv", "mime_type": "video/mkv"},
            {"extension": "webm", "mime_type": "video/webm"}
        ],
        "max_file_size_mb": 100,
        "supported_languages": [
            "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"
        ],
        "whisper_models": [
            "tiny", "base", "small", "medium", "large"
        ]
    }, "Supported formats retrieved")


@router.get("/models")
async def get_available_models():
    """Get available transcription models"""
    return create_api_response({
        "whisper_models": [
            {
                "name": "tiny",
                "size": "39 MB",
                "speed": "~32x",
                "accuracy": "Good for simple audio"
            },
            {
                "name": "base", 
                "size": "74 MB",
                "speed": "~16x",
                "accuracy": "Better accuracy"
            },
            {
                "name": "small",
                "size": "244 MB", 
                "speed": "~6x",
                "accuracy": "Good balance"
            },
            {
                "name": "medium",
                "size": "769 MB",
                "speed": "~2x", 
                "accuracy": "High accuracy"
            },
            {
                "name": "large",
                "size": "1550 MB",
                "speed": "1x",
                "accuracy": "Best accuracy"
            }
        ],
        "api_models": [
            {
                "name": "whisper-1",
                "provider": "OpenAI",
                "accuracy": "Highest",
                "cost": "Per minute"
            }
        ]
    }, "Available models retrieved")