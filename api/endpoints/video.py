"""
Video Processing API Endpoints
REST API for video analysis and processing functionality
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional, List, Dict, Any
import os
import sys
import tempfile
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..auth import auth_required, write_required, create_api_response
from ..models import (
    VideoProcessingRequest, VideoProcessingResponse, VideoAnalysisResult,
    VideoFrame, VideoScene, FileUploadResponse
)

# Import video processing modules
from video_processing import VideoProcessor, VideoAnalysis
from session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["Video Processing"])

# Initialize components
video_processor = VideoProcessor()
session_manager = SessionManager()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_video_file(
    file: UploadFile = File(...),
    user_id: str = Depends(auth_required)
):
    """Upload video file for processing"""
    try:
        # Validate file type
        allowed_types = {
            'video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm',
            'video/quicktime', 'video/x-msvideo'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported video format: {file.content_type}"
            )
        
        # Check file size (2GB limit for video)
        content = await file.read()
        file_size = len(content)
        
        if file_size > 2048 * 1024 * 1024:  # 2GB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Video file size exceeds 2GB limit"
            )
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Generate file ID
        file_id = f"video_{user_id}_{int(datetime.now().timestamp())}"
        
        # Store file info in session
        session_manager.set_session_data(user_id, {
            'uploaded_video_path': temp_path,
            'uploaded_video_name': file.filename,
            'uploaded_video_size': file_size,
            'uploaded_video_type': file.content_type,
            'video_file_id': file_id
        })
        
        return create_api_response({
            "file_id": file_id,
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type
        }, "Video file uploaded successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video upload failed"
        )


@router.post("/analyze/{file_id}", response_model=VideoProcessingResponse)
async def analyze_video(
    file_id: str,
    request: VideoProcessingRequest,
    user_id: str = Depends(write_required)
):
    """Analyze uploaded video file"""
    try:
        # Get file info from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'uploaded_video_path' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No uploaded video file found. Upload a video first."
            )
        
        if session_data.get('video_file_id') != file_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file ID not found"
            )
        
        video_path = session_data['uploaded_video_path']
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uploaded video file not found on disk"
            )
        
        # Process video
        analysis = video_processor.analyze_video(
            video_path,
            extract_frames=request.extract_frames,
            detect_scenes=request.detect_scenes,
            keyframe_interval=request.keyframe_interval
        )
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Video analysis failed"
            )
        
        # Convert keyframes to API format
        keyframes = []
        for kf in analysis.keyframes:
            keyframes.append(VideoFrame(
                timestamp=kf.timestamp,
                frame_path=kf.frame_path,
                width=kf.width,
                height=kf.height
            ))
        
        # Convert scenes to API format
        scenes = []
        for scene in analysis.scenes:
            scenes.append(VideoScene(
                start_time=scene.start_time,
                end_time=scene.end_time,
                duration=scene.duration,
                frame_count=scene.frame_count,
                thumbnail_path=scene.thumbnail_path
            ))
        
        # Generate thumbnails if requested
        thumbnails = []
        if request.generate_thumbnails:
            thumbnails = video_processor.generate_thumbnails(
                video_path, 
                count=request.thumbnail_count
            )
        
        # Create result
        result = VideoAnalysisResult(
            duration=analysis.duration,
            fps=analysis.fps,
            frame_count=analysis.frame_count,
            resolution={"width": analysis.width, "height": analysis.height},
            keyframes=keyframes,
            scenes=scenes,
            thumbnails=thumbnails,
            metadata={
                "codec": analysis.metadata.get('codec', 'unknown'),
                "bitrate": analysis.metadata.get('bitrate', 0),
                "file_size": session_data['uploaded_video_size'],
                "analyzed_at": datetime.now().isoformat(),
                "analysis_options": request.dict()
            }
        )
        
        # Store result in session
        video_analysis_id = f"video_analysis_{user_id}_{int(datetime.now().timestamp())}"
        session_data['video_analysis'] = {
            'analysis_id': video_analysis_id,
            'result': result.dict(),
            'file_name': session_data['uploaded_video_name'],
            'analysis_options': request.dict()
        }
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(result, "Video analysis completed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video analysis failed"
        )


@router.get("/frames/{file_id}")
async def get_video_frames(
    file_id: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    interval: float = 5.0,
    user_id: str = Depends(auth_required)
):
    """Extract frames from video at specified intervals"""
    try:
        # Get video analysis from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'video_analysis' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No video analysis found. Analyze a video first."
            )
        
        video_path = session_data['uploaded_video_path']
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found"
            )
        
        # Extract frames at specified interval
        frames = video_processor.extract_frames_at_interval(
            video_path,
            interval=interval,
            start_time=start_time,
            end_time=end_time
        )
        
        frame_list = []
        for frame in frames:
            frame_list.append({
                "timestamp": frame.timestamp,
                "frame_path": frame.frame_path,
                "width": frame.width,
                "height": frame.height,
                "download_url": f"/api/v1/video/download/frame/{os.path.basename(frame.frame_path)}"
            })
        
        return create_api_response({
            "frames": frame_list,
            "count": len(frame_list),
            "interval_seconds": interval,
            "time_range": {
                "start": start_time,
                "end": end_time
            }
        }, f"Extracted {len(frame_list)} frames")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Frame extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Frame extraction failed"
        )


@router.get("/scenes/{file_id}")
async def get_video_scenes(
    file_id: str,
    min_duration: float = 1.0,
    user_id: str = Depends(auth_required)
):
    """Get detected scenes from video analysis"""
    try:
        # Get video analysis from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'video_analysis' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No video analysis found. Analyze a video first."
            )
        
        analysis_result = session_data['video_analysis']['result']
        scenes = analysis_result.get('scenes', [])
        
        # Filter scenes by minimum duration
        filtered_scenes = [
            scene for scene in scenes 
            if scene['duration'] >= min_duration
        ]
        
        return create_api_response({
            "scenes": filtered_scenes,
            "total_scenes": len(scenes),
            "filtered_scenes": len(filtered_scenes),
            "min_duration": min_duration
        }, f"Retrieved {len(filtered_scenes)} scenes")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scene retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scene retrieval failed"
        )


@router.get("/thumbnails/{file_id}")
async def get_video_thumbnails(
    file_id: str,
    count: int = 5,
    user_id: str = Depends(auth_required)
):
    """Generate video thumbnails"""
    try:
        # Get video info from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'uploaded_video_path' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No video file found"
            )
        
        video_path = session_data['uploaded_video_path']
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found on disk"
            )
        
        # Generate thumbnails
        thumbnails = video_processor.generate_thumbnails(video_path, count=count)
        
        thumbnail_list = []
        for i, thumbnail_path in enumerate(thumbnails):
            thumbnail_list.append({
                "index": i,
                "thumbnail_path": thumbnail_path,
                "download_url": f"/api/v1/video/download/thumbnail/{os.path.basename(thumbnail_path)}"
            })
        
        return create_api_response({
            "thumbnails": thumbnail_list,
            "count": len(thumbnail_list)
        }, f"Generated {len(thumbnail_list)} thumbnails")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thumbnail generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Thumbnail generation failed"
        )


@router.get("/metadata/{file_id}")
async def get_video_metadata(
    file_id: str,
    user_id: str = Depends(auth_required)
):
    """Get detailed video metadata"""
    try:
        # Get video analysis from session
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or 'video_analysis' not in session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No video analysis found. Analyze a video first."
            )
        
        analysis_result = session_data['video_analysis']['result']
        
        # Extract comprehensive metadata
        metadata = {
            "basic_info": {
                "duration": analysis_result['duration'],
                "fps": analysis_result['fps'],
                "frame_count": analysis_result['frame_count'],
                "resolution": analysis_result['resolution'],
                "file_size": analysis_result['metadata']['file_size']
            },
            "technical_details": analysis_result['metadata'],
            "content_analysis": {
                "scene_count": len(analysis_result.get('scenes', [])),
                "keyframe_count": len(analysis_result.get('keyframes', [])),
                "thumbnail_count": len(analysis_result.get('thumbnails', []))
            },
            "processing_info": {
                "analyzed_at": analysis_result['metadata']['analyzed_at'],
                "analysis_options": analysis_result['metadata']['analysis_options']
            }
        }
        
        return create_api_response(metadata, "Video metadata retrieved")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metadata retrieval failed"
        )


@router.get("/supported-formats")
async def get_supported_video_formats():
    """Get supported video formats and processing capabilities"""
    return create_api_response({
        "video_formats": [
            {
                "format": "MP4",
                "mime_type": "video/mp4",
                "extensions": [".mp4"],
                "description": "MPEG-4 video format (recommended)"
            },
            {
                "format": "AVI",
                "mime_type": "video/avi",
                "extensions": [".avi"],
                "description": "Audio Video Interleave format"
            },
            {
                "format": "MOV",
                "mime_type": "video/quicktime",
                "extensions": [".mov"],
                "description": "QuickTime movie format"
            },
            {
                "format": "MKV",
                "mime_type": "video/mkv",
                "extensions": [".mkv"],
                "description": "Matroska video format"
            },
            {
                "format": "WebM",
                "mime_type": "video/webm",
                "extensions": [".webm"],
                "description": "WebM video format"
            }
        ],
        "processing_capabilities": [
            {
                "name": "Frame Extraction",
                "description": "Extract keyframes at specified intervals",
                "supported": True
            },
            {
                "name": "Scene Detection",
                "description": "Automatic scene change detection",
                "supported": True
            },
            {
                "name": "Thumbnail Generation",
                "description": "Generate video preview thumbnails",
                "supported": True
            },
            {
                "name": "Metadata Extraction",
                "description": "Extract technical video metadata",
                "supported": True
            }
        ],
        "limits": {
            "max_file_size_mb": 500,
            "max_duration_minutes": 120,
            "max_thumbnails": 20,
            "supported_codecs": ["H.264", "H.265", "VP8", "VP9"]
        }
    }, "Supported video formats retrieved")


@router.delete("/analysis/{file_id}")
async def delete_video_analysis(
    file_id: str,
    user_id: str = Depends(auth_required)
):
    """Delete video analysis and cleanup files"""
    try:
        # Get session data
        session_data = session_manager.get_session_data(user_id)
        
        if not session_data or session_data.get('video_file_id') != file_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video analysis not found"
            )
        
        # Cleanup video file
        video_path = session_data.get('uploaded_video_path')
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except:
                pass
        
        # Cleanup analysis files (frames, thumbnails)
        analysis_data = session_data.get('video_analysis', {})
        if analysis_data:
            result = analysis_data.get('result', {})
            
            # Cleanup keyframes
            for frame in result.get('keyframes', []):
                try:
                    os.unlink(frame['frame_path'])
                except:
                    pass
            
            # Cleanup thumbnails
            for thumbnail_path in result.get('thumbnails', []):
                try:
                    os.unlink(thumbnail_path)
                except:
                    pass
        
        # Remove from session
        keys_to_remove = [
            'uploaded_video_path', 'uploaded_video_name', 'uploaded_video_size',
            'uploaded_video_type', 'video_file_id', 'video_analysis'
        ]
        
        for key in keys_to_remove:
            session_data.pop(key, None)
        
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(
            {"file_id": file_id},
            "Video analysis deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete video analysis"
        )