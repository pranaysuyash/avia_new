"""
Video Processing API Endpoints - Improved Exception Handling
REST API for video analysis and processing functionality with specific exception handling
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional, List, Dict, Any
import os
import sys
import tempfile
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import auth_required, write_required, create_api_response
from api.models import (
    VideoProcessingRequest, VideoProcessingResponse, VideoAnalysisResult,
    VideoFrame, VideoScene, FileUploadResponse
)

# Import video processing modules
try:
    from mock_video_processor import VideoProcessor  # Temporary mock for testing
    from api_session_manager import SessionManager
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import required modules: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["Video Processing"])

# Initialize components
try:
    video_processor = VideoProcessor()
    session_manager = SessionManager()
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise


@router.post("/upload")
async def upload_video_file(
    file: UploadFile = File(...),
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Upload video file for processing"""
    # Validate file presence
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Validate file type
    allowed_types = {
        'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
        'video/quicktime', 'video/x-msvideo'
    }
    
    # Check file extension as backup
    file_extension = Path(file.filename).suffix.lower() if file.filename else ""
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    if file.content_type not in allowed_types and file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported video format: {file.content_type or 'unknown'}. Allowed formats: {', '.join(allowed_extensions)}"
        )
    
    temp_path = None
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size (2GB limit for video)
        max_size = 2048 * 1024 * 1024  # 2GB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Video file size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size (2048MB)"
            )
        
        # Check if file is empty
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is empty"
            )
        
        # Save file temporarily
        try:
            suffix = file_extension or os.path.splitext(file.filename)[1] if file.filename else '.mp4'
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
                logger.error(f"OS error while saving video: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save video to temporary storage"
                )
        except IOError as e:
            logger.error(f"IO error while saving video: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to write video to disk"
            )
        
        # Generate file ID
        try:
            file_id = f"video_{user_id}_{int(datetime.now().timestamp())}"
        except (ValueError, OSError) as e:
            logger.error(f"Failed to generate file ID: {e}")
            file_id = f"video_{user_id}_default"
        
        # Store file info in session
        try:
            session_data = {
                'uploaded_video_path': temp_path,
                'uploaded_video_name': file.filename or 'unnamed_video',
                'uploaded_video_size': file_size,
                'uploaded_video_type': file.content_type or 'video/mp4',
                'video_file_id': file_id
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
            "file_name": file.filename or 'unnamed_video',
            "file_size": file_size,
            "content_type": file.content_type or 'video/mp4'
        }, "Video file uploaded successfully")
        
    except HTTPException:
        # Clean up temp file on HTTP errors
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass
        raise
    except MemoryError as e:
        logger.error(f"Memory error during video upload: {e}")
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Video file too large to process in available memory"
        )


@router.post("/analyze/{file_id}")
async def analyze_video(
    file_id: str,
    request: VideoProcessingRequest,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Analyze uploaded video file"""
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
            detail="No active session found. Please upload a video first."
        )
    
    if 'uploaded_video_path' not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No uploaded video file found. Upload a video first."
        )
    
    if session_data.get('video_file_id') != file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video file ID '{file_id}' not found"
        )
    
    video_path = session_data['uploaded_video_path']
    
    # Verify video file exists
    if not os.path.exists(video_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded video file no longer exists. Please upload the video again."
        )
    
    # Verify video is readable
    if not os.access(video_path, os.R_OK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot read uploaded video file. Permission denied."
        )
    
    try:
        # Process video
        analysis = video_processor.analyze_video(
            video_path,
            extract_frames=request.extract_frames,
            detect_scenes=request.detect_scenes,
            keyframe_interval=request.keyframe_interval
        )
    except FileNotFoundError as e:
        logger.error(f"Video file not found during processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found during processing"
        )
    except PermissionError as e:
        logger.error(f"Permission denied during video processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied while processing video"
        )
    except MemoryError as e:
        logger.error(f"Out of memory during video analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to process video"
        )
    except AttributeError as e:
        logger.error(f"Video processor API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Video processing service error"
        )
    except ValueError as e:
        logger.error(f"Invalid video processing parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid processing parameters: {str(e)}"
        )
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video analysis returned no result"
        )
    
    # Convert keyframes to API format
    keyframes = []
    if hasattr(analysis, 'keyframes') and analysis.keyframes:
        for kf in analysis.keyframes:
            try:
                keyframes.append({
                    "timestamp": float(kf.timestamp),
                    "frame_path": str(kf.frame_path),
                    "download_url": f"/api/v1/video/download/frame/{os.path.basename(kf.frame_path)}"
                })
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Invalid keyframe data: {e}")
                continue
    
    # Convert scenes to API format
    scenes = []
    if hasattr(analysis, 'scenes') and analysis.scenes:
        for scene in analysis.scenes:
            try:
                scenes.append({
                    "start_time": float(scene.start_time),
                    "end_time": float(scene.end_time),
                    "duration": float(scene.duration),
                    "scene_number": int(scene.scene_number)
                })
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Invalid scene data: {e}")
                continue
    
    # Store analysis in session
    try:
        session_data['video_analysis'] = {
            "file_id": file_id,
            "result": {
                "duration": float(analysis.duration) if hasattr(analysis, 'duration') else 0.0,
                "fps": float(analysis.fps) if hasattr(analysis, 'fps') else 0.0,
                "frame_count": int(analysis.frame_count) if hasattr(analysis, 'frame_count') else 0,
                "resolution": analysis.resolution if hasattr(analysis, 'resolution') else {"width": 0, "height": 0},
                "keyframes": keyframes,
                "scenes": scenes,
                "metadata": {
                    "file_size": session_data['uploaded_video_size'],
                    "file_name": session_data['uploaded_video_name'],
                    "analyzed_at": datetime.now().isoformat(),
                    "analysis_options": request.dict()
                }
            }
        }
        session_manager.set_session_data(user_id, session_data)
    except (AttributeError, TypeError) as e:
        logger.error(f"Failed to store analysis result: {e}")
        # Continue - still return the result to user
    
    return create_api_response({
        "file_id": file_id,
        "duration": session_data['video_analysis']['result']['duration'],
        "fps": session_data['video_analysis']['result']['fps'],
        "frame_count": session_data['video_analysis']['result']['frame_count'],
        "resolution": session_data['video_analysis']['result']['resolution'],
        "keyframe_count": len(keyframes),
        "scene_count": len(scenes)
    }, "Video analysis completed")


@router.delete("/analysis/{file_id}")
async def delete_video_analysis(
    file_id: str,
    user_id: str = "test_user"  # Temporarily disabled auth for testing
):
    """Delete video analysis and cleanup files"""
    # Validate file_id
    if not file_id or not isinstance(file_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID"
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
    
    if not session_data or session_data.get('video_file_id') != file_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video analysis for file ID '{file_id}' not found"
        )
    
    cleanup_errors = []
    
    # Cleanup video file
    video_path = session_data.get('uploaded_video_path')
    if video_path and os.path.exists(video_path):
        try:
            os.unlink(video_path)
            logger.info(f"Deleted video file: {video_path}")
        except FileNotFoundError:
            # File already deleted
            pass
        except PermissionError as e:
            logger.warning(f"Cannot delete video file {video_path}: Permission denied")
            cleanup_errors.append(f"Video file: {e}")
        except OSError as e:
            logger.warning(f"Failed to delete video file {video_path}: {e}")
            cleanup_errors.append(f"Video file: {e}")
    
    # Cleanup analysis files (frames, thumbnails)
    analysis_data = session_data.get('video_analysis', {})
    if analysis_data:
        result = analysis_data.get('result', {})
        
        # Cleanup keyframes
        keyframes = result.get('keyframes', [])
        for frame in keyframes:
            if isinstance(frame, dict) and 'frame_path' in frame:
                frame_path = frame['frame_path']
                if frame_path and os.path.exists(frame_path):
                    try:
                        os.unlink(frame_path)
                        logger.debug(f"Deleted keyframe: {frame_path}")
                    except FileNotFoundError:
                        # File already deleted
                        pass
                    except PermissionError as e:
                        logger.warning(f"Cannot delete keyframe {frame_path}: Permission denied")
                        cleanup_errors.append(f"Keyframe: {e}")
                    except OSError as e:
                        logger.warning(f"Failed to delete keyframe {frame_path}: {e}")
                        cleanup_errors.append(f"Keyframe: {e}")
        
        # Cleanup thumbnails
        thumbnails = result.get('thumbnails', [])
        for thumbnail_path in thumbnails:
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    os.unlink(thumbnail_path)
                    logger.debug(f"Deleted thumbnail: {thumbnail_path}")
                except FileNotFoundError:
                    # File already deleted
                    pass
                except PermissionError as e:
                    logger.warning(f"Cannot delete thumbnail {thumbnail_path}: Permission denied")
                    cleanup_errors.append(f"Thumbnail: {e}")
                except OSError as e:
                    logger.warning(f"Failed to delete thumbnail {thumbnail_path}: {e}")
                    cleanup_errors.append(f"Thumbnail: {e}")
    
    # Remove from session
    keys_to_remove = [
        'uploaded_video_path', 'uploaded_video_name', 'uploaded_video_size',
        'uploaded_video_type', 'video_file_id', 'video_analysis'
    ]
    
    for key in keys_to_remove:
        try:
            session_data.pop(key, None)
        except (KeyError, AttributeError):
            pass
    
    try:
        session_manager.set_session_data(user_id, session_data)
    except AttributeError as e:
        logger.error(f"Failed to update session after deletion: {e}")
        # Continue - deletion is still successful
    
    response_data = {"file_id": file_id, "deleted": True}
    
    # Include cleanup warnings if any
    if cleanup_errors:
        response_data["cleanup_warnings"] = cleanup_errors
        logger.warning(f"Video deletion completed with warnings: {cleanup_errors}")
        return create_api_response(
            response_data,
            "Video analysis deleted with some cleanup warnings"
        )
    else:
        return create_api_response(
            response_data,
            "Video analysis deleted successfully"
        )