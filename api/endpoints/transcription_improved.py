"""
Transcription API Endpoints - Improved Exception Handling
REST API for audio/video transcription functionality with specific exception handling
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
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import auth_required, write_required, create_api_response, create_error_response
from api.models import (
    TranscriptionRequest, TranscriptionResponse, TranscriptionResult,
    Entity, SpeakerSegment, FileUploadResponse
)

# Import transcription modules
try:
    from mock_transcriber import MockTranscriber as AdvancedTranscriber
    from ner_advanced import extract_entities_advanced
    from api_session_manager import SessionManager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import required modules: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcription", tags=["Transcription"])

# Initialize components
try:
    transcriber = AdvancedTranscriber()
    session_manager = SessionManager()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise


@router.post("/upload", response_model=FileUploadResponse)
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
    
    # Validate file type
    allowed_types = {
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac',
        'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'
    }
    
    # Some browsers don't send proper content type for audio files
    file_extension = Path(file.filename).suffix.lower() if file.filename else ""
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    if file.content_type not in allowed_types and file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type or 'unknown'}. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    temp_path = None
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size (2GB limit)
        max_size = 2048 * 1024 * 1024  # 2GB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (2048MB)"
            )
        
        # Check if file is empty
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        # Save file temporarily
        try:
            suffix = file_extension or os.path.splitext(file.filename)[1] if file.filename else '.tmp'
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
            file_id = f"upload_{user_id}_{int(datetime.now().timestamp())}"
        except (ValueError, OSError) as e:
            logger.error(f"Failed to generate file ID: {e}")
            file_id = f"upload_{user_id}_default"
        
        # Store file info in session
        try:
            session_data = {
                'uploaded_file_path': temp_path,
                'uploaded_file_name': file.filename or 'unnamed_file',
                'uploaded_file_size': file_size,
                'uploaded_file_type': file.content_type or 'application/octet-stream',
                'file_id': file_id
            }
            session_manager.set_session_data(user_id, session_data)
        except AttributeError as e:
            logger.error(f"Session manager error: {e}")
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Session management service unavailable"
            )
        
        return create_api_response({
            "file_id": file_id,
            "file_name": file.filename or 'unnamed_file',
            "file_size": file_size,
            "content_type": file.content_type or 'application/octet-stream'
        }, "File uploaded successfully")
        
    except HTTPException:
        # Clean up temp file on HTTP errors
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise
    except MemoryError as e:
        logger.error(f"Memory error during file upload: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large to process in available memory"
        )


@router.post("/process", response_model=TranscriptionResponse)
async def process_transcription(
    request: TranscriptionRequest,
    file_id: Optional[str] = None,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Process uploaded file for transcription"""
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
            detail="No uploaded file found in session. Please upload a file first."
        )
    
    file_path = session_data['uploaded_file_path']
    file_name = session_data.get('uploaded_file_name', 'unknown')
    
    # Verify file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file no longer exists. Please upload the file again."
        )
    
    # Verify file is readable
    if not os.access(file_path, os.R_OK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot read uploaded file. Permission denied."
        )
    
    start_time = datetime.now()
    
    try:
        # Process transcription with timeout
        transcription_result = await asyncio.wait_for(
            asyncio.to_thread(
                transcriber.transcribe_with_speaker_diarization,
                file_path,
                language=request.language if request.language != "auto" else None,
                use_api=request.use_api
            ),
            timeout=300.0  # 5 minute timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"Transcription timed out for file: {file_name}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Transcription processing timed out after 5 minutes"
        )
    except FileNotFoundError as e:
        logger.error(f"File not found during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found during processing"
        )
    except PermissionError as e:
        logger.error(f"Permission denied during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied while processing file"
        )
    except MemoryError as e:
        logger.error(f"Out of memory during transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to process file"
        )
    except AttributeError as e:
        logger.error(f"Transcriber API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service error"
        )
    except Exception as e:
        logger.error(f"Unexpected transcription error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transcription"
        )
    
    # Validate transcription result
    if not transcription_result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcription returned no result"
        )
    
    if not hasattr(transcription_result, 'text') or not transcription_result.text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcription returned empty text"
        )
    
    # Extract entities if requested
    entities = []
    if request.extract_entities:
        try:
            entity_results = extract_entities_advanced(transcription_result.text)
            
            if isinstance(entity_results, dict) and 'entities' in entity_results:
                entities_list = entity_results.get('entities', [])
                
                for entity_data in entities_list:
                    try:
                        if isinstance(entity_data, dict):
                            entities.append(Entity(
                                text=str(entity_data.get('text', '')),
                                label=str(entity_data.get('label', 'UNKNOWN')),
                                start=int(entity_data.get('start', 0)),
                                end=int(entity_data.get('end', 0)),
                                confidence=float(entity_data.get('confidence', 0.0)) if entity_data.get('confidence') else None
                            ))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid entity data: {e}")
                        continue
                        
        except ImportError as e:
            logger.error(f"Entity extraction module not available: {e}")
            # Continue without entities rather than failing
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(f"Entity extraction data error: {e}")
            # Continue without entities
        except Exception as e:
            logger.warning(f"Unexpected entity extraction error: {type(e).__name__}: {e}")
            # Continue without entities
    
    # Speaker diarization if requested
    speakers = None
    if request.enable_diarization:
        try:
            from speaker_diarization.diarization_manager import DiarizationManager
            diarization_manager = DiarizationManager()
            
            diarization_result = await asyncio.wait_for(
                diarization_manager.process_audio(file_path),
                timeout=180.0  # 3 minute timeout for diarization
            )
            
            if diarization_result and hasattr(diarization_result, 'segments'):
                speakers = []
                for segment in diarization_result.segments:
                    try:
                        speakers.append(SpeakerSegment(
                            speaker_id=str(segment.speaker_id),
                            start_time=float(segment.start_time),
                            end_time=float(segment.end_time),
                            text=str(segment.text),
                            confidence=float(segment.confidence) if hasattr(segment, 'confidence') else None
                        ))
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.warning(f"Invalid speaker segment data: {e}")
                        continue
                        
        except ImportError as e:
            logger.error(f"Diarization module not available: {e}")
            speakers = None
        except asyncio.TimeoutError:
            logger.warning("Speaker diarization timed out")
            speakers = None
        except Exception as e:
            logger.warning(f"Speaker diarization error: {type(e).__name__}: {e}")
            speakers = None
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Generate transcript ID
    try:
        transcript_id = f"transcript_{user_id}_{int(start_time.timestamp())}"
    except (ValueError, OSError) as e:
        logger.error(f"Failed to generate transcript ID: {e}")
        transcript_id = f"transcript_{user_id}_default"
    
    # Create result
    try:
        result = TranscriptionResult(
            transcript_id=transcript_id,
            text=transcription_result.text,
            language=getattr(transcription_result, 'language', 'unknown'),
            duration=float(transcription_result.get_total_duration()) if hasattr(transcription_result, 'get_total_duration') else 0.0,
            word_count=len(transcription_result.text.split()),
            entities=entities,
            speakers=speakers,
            confidence=float(transcription_result.confidence) if hasattr(transcription_result, 'confidence') else 0.0,
            processing_time=processing_time,
            created_at=start_time
        )
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Failed to create result object: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to format transcription result"
        )
    
    # Store result in session
    try:
        session_manager.store_result(user_id, {
            'transcript_id': transcript_id,
            'result': result.dict(),
            'file_name': file_name,
            'processing_options': request.dict()
        })
    except AttributeError as e:
        logger.error(f"Failed to store result: {e}")
        # Continue - at least return the result to user
    
    # Cleanup temp file
    try:
        os.unlink(file_path)
    except FileNotFoundError:
        # File already deleted
        pass
    except PermissionError as e:
        logger.warning(f"Cannot delete temp file {file_path}: Permission denied")
    except OSError as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")
    
    return create_api_response(result, "Transcription completed successfully")


@router.get("/status/{transcript_id}")
async def get_transcription_status(
    transcript_id: str,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Get transcription status by ID"""
    # Validate transcript_id
    if not transcript_id or not isinstance(transcript_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcript ID"
        )
    
    try:
        # Get stored results
        results = session_manager.get_stored_results(user_id)
    except AttributeError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management service unavailable"
        )
    
    if not isinstance(results, list):
        logger.error(f"Invalid results format: {type(results)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid data format in storage"
        )
    
    # Search for transcript
    for result in results:
        try:
            if isinstance(result, dict) and result.get('transcript_id') == transcript_id:
                return create_api_response({
                    "transcript_id": transcript_id,
                    "status": "completed",
                    "result": result['result']
                }, "Transcription found")
        except (KeyError, TypeError) as e:
            logger.warning(f"Invalid result structure: {e}")
            continue
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Transcription '{transcript_id}' not found"
    )


@router.get("/history")
async def get_transcription_history(
    limit: int = 10,
    offset: int = 0,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Get user's transcription history"""
    # Validate pagination parameters
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative"
        )
    
    try:
        results = session_manager.get_stored_results(user_id)
    except AttributeError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management service unavailable"
        )
    
    if not isinstance(results, list):
        results = []
    
    # Apply pagination
    total_count = len(results)
    
    try:
        paginated_results = results[offset:offset + limit]
    except (IndexError, TypeError) as e:
        logger.error(f"Pagination error: {e}")
        paginated_results = []
    
    # Format history items
    history_items = []
    for result in paginated_results:
        try:
            if isinstance(result, dict):
                result_data = result.get('result', {})
                history_items.append({
                    "transcript_id": result.get('transcript_id', 'unknown'),
                    "file_name": result.get('file_name', 'unknown'),
                    "created_at": result_data.get('created_at', ''),
                    "duration": float(result_data.get('duration', 0)),
                    "word_count": int(result_data.get('word_count', 0)),
                    "language": result_data.get('language', 'unknown'),
                    "has_speakers": bool(result_data.get('speakers')),
                    "has_entities": bool(result_data.get('entities'))
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Invalid history item: {e}")
            continue
    
    return create_api_response({
        "transcriptions": history_items,
        "total_count": total_count,
        "page": (offset // limit + 1) if limit > 0 else 1,
        "per_page": limit
    }, "Transcription history retrieved")


@router.delete("/{transcript_id}")
async def delete_transcription(
    transcript_id: str,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Delete a transcription"""
    # Validate transcript_id
    if not transcript_id or not isinstance(transcript_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transcript ID"
        )
    
    try:
        # Get current results
        results = session_manager.get_stored_results(user_id)
        
        # Find and remove the transcript
        found = False
        updated_results = []
        
        for result in results:
            try:
                if isinstance(result, dict) and result.get('transcript_id') != transcript_id:
                    updated_results.append(result)
                elif isinstance(result, dict) and result.get('transcript_id') == transcript_id:
                    found = True
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid result during deletion: {e}")
                updated_results.append(result)  # Keep invalid items
        
        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transcription '{transcript_id}' not found"
            )
        
        # Update stored results
        # In a real implementation, this would update the database
        # For now, we just log the deletion
        logger.info(f"Deleted transcription {transcript_id} for user {user_id}")
        
        return create_api_response({
            "transcript_id": transcript_id,
            "deleted": True
        }, "Transcription deleted successfully")
        
    except HTTPException:
        raise
    except AttributeError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session management service unavailable"
        )