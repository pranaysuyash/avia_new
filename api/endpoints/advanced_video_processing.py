"""
Advanced Video Processing API Endpoints
Task 3: Advanced Media Processing Pipeline

FastAPI endpoints for advanced video processing with scene detection,
keyframe extraction, object recognition, and intelligent B-roll suggestions.
"""

import os
import tempfile
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio

# Import the advanced video processing engine
try:
    from advanced_video_processing_engine import (
        AdvancedVideoProcessingEngine, VideoMetadata, SceneInfo, 
        KeyFrame, ObjectDetection, BRollSuggestion, VideoEnhancement
    )
except ImportError as e:
    logging.error(f"Failed to import AdvancedVideoProcessingEngine: {e}")
    AdvancedVideoProcessingEngine = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/video", tags=["Advanced Video Processing"])

# Global engine instance
video_engine = None

def get_video_engine():
    """Get or create video processing engine instance"""
    global video_engine
    if video_engine is None and AdvancedVideoProcessingEngine:
        video_engine = AdvancedVideoProcessingEngine()
    return video_engine

# Request/Response Models
class VideoProcessingRequest(BaseModel):
    """Video processing request configuration"""
    extract_keyframes: bool = Field(True, description="Extract keyframes from video")
    detect_scenes: bool = Field(True, description="Detect scene changes")
    detect_objects: bool = Field(True, description="Detect objects in video")
    suggest_broll: bool = Field(True, description="Generate B-roll suggestions")
    enhance_quality: bool = Field(False, description="Apply quality enhancements")
    processing_strategy: Optional[str] = Field(None, description="Override processing strategy")

class VideoMetadataResponse(BaseModel):
    """Video metadata response"""
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    codec: str
    bitrate: Optional[int] = None
    file_size: int
    aspect_ratio: str
    has_audio: bool
    quality_score: float
    complexity_score: float

class SceneInfoResponse(BaseModel):
    """Scene information response"""
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int
    confidence: float
    scene_type: str
    description: str
    motion_intensity: float
    visual_complexity: float

class KeyFrameResponse(BaseModel):
    """Keyframe response"""
    frame_number: int
    timestamp: float
    confidence: float
    frame_path: Optional[str] = None
    visual_hash: str
    objects_detected: List[str]

class ObjectDetectionResponse(BaseModel):
    """Object detection response"""
    class_name: str
    category: str
    confidence: float
    bbox: List[int]  # [x, y, width, height]
    timestamp: float
    frame_number: int
    tracking_id: Optional[str] = None

class BRollSuggestionResponse(BaseModel):
    """B-roll suggestion response"""
    timestamp: float
    duration: float
    suggestion_type: str
    description: str
    confidence: float
    keywords: List[str]
    priority: int

class VideoProcessingResponse(BaseModel):
    """Comprehensive video processing response"""
    job_id: str
    success: bool
    processing_time: float
    processing_strategy: str
    metadata: VideoMetadataResponse
    keyframes: List[KeyFrameResponse]
    scenes: List[SceneInfoResponse]
    objects: List[ObjectDetectionResponse]
    broll_suggestions: List[BRollSuggestionResponse]
    errors: List[str] = []

class ProcessingJobStatus(BaseModel):
    """Processing job status"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 1.0
    message: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[VideoProcessingResponse] = None

# In-memory job storage (in production, use Redis or database)
processing_jobs: Dict[str, ProcessingJobStatus] = {}

@router.post("/process", response_model=VideoProcessingResponse)
async def process_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    extract_keyframes: bool = True,
    detect_scenes: bool = True,
    detect_objects: bool = True,
    suggest_broll: bool = True,
    enhance_quality: bool = False,
    processing_strategy: Optional[str] = None
):
    """
    Process video with advanced analysis including scene detection,
    keyframe extraction, object recognition, and B-roll suggestions.
    """
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    job_id = str(uuid.uuid4())
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"video_{job_id}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Create job status
        job_status = ProcessingJobStatus(
            job_id=job_id,
            status="processing",
            progress=0.0,
            message="Starting video processing...",
            started_at=datetime.now()
        )
        processing_jobs[job_id] = job_status
        
        # Process video
        processing_options = {
            'extract_keyframes': extract_keyframes,
            'detect_scenes': detect_scenes,
            'detect_objects': detect_objects,
            'suggest_broll': suggest_broll,
            'enhance_quality': enhance_quality
        }
        
        if processing_strategy:
            processing_options['processing_strategy'] = processing_strategy
        
        # Start background processing
        background_tasks.add_task(
            process_video_background,
            engine,
            temp_file_path,
            processing_options,
            job_id
        )
        
        # Return immediate response with job ID
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "processing",
                "message": "Video processing started. Use /status/{job_id} to check progress."
            }
        )
        
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")

async def process_video_background(
    engine: AdvancedVideoProcessingEngine,
    video_path: str,
    processing_options: Dict[str, Any],
    job_id: str
):
    """Background task for video processing"""
    try:
        # Update job status
        processing_jobs[job_id].status = "processing"
        processing_jobs[job_id].progress = 0.1
        processing_jobs[job_id].message = "Analyzing video content..."
        
        # Process video
        results = await engine.process_video_comprehensive(video_path, processing_options)
        
        if results['success']:
            # Convert results to response format
            response = VideoProcessingResponse(
                job_id=job_id,
                success=True,
                processing_time=results['processing_time'],
                processing_strategy=results['processing_strategy'],
                metadata=VideoMetadataResponse(**results['metadata'].__dict__),
                keyframes=[
                    KeyFrameResponse(
                        frame_number=kf.frame_number,
                        timestamp=kf.timestamp,
                        confidence=kf.confidence,
                        frame_path=kf.frame_path,
                        visual_hash=kf.visual_hash,
                        objects_detected=kf.objects_detected
                    ) for kf in results.get('keyframes', [])
                ],
                scenes=[
                    SceneInfoResponse(
                        start_time=scene.start_time,
                        end_time=scene.end_time,
                        start_frame=scene.start_frame,
                        end_frame=scene.end_frame,
                        confidence=scene.confidence,
                        scene_type=scene.scene_type.value,
                        description=scene.description,
                        motion_intensity=scene.motion_intensity,
                        visual_complexity=scene.visual_complexity
                    ) for scene in results.get('scenes', [])
                ],
                objects=[
                    ObjectDetectionResponse(
                        class_name=obj.class_name,
                        category=obj.category.value,
                        confidence=obj.confidence,
                        bbox=list(obj.bbox),
                        timestamp=obj.timestamp,
                        frame_number=obj.frame_number,
                        tracking_id=obj.tracking_id
                    ) for obj in results.get('objects', [])
                ],
                broll_suggestions=[
                    BRollSuggestionResponse(
                        timestamp=suggestion.timestamp,
                        duration=suggestion.duration,
                        suggestion_type=suggestion.suggestion_type,
                        description=suggestion.description,
                        confidence=suggestion.confidence,
                        keywords=suggestion.keywords,
                        priority=suggestion.priority
                    ) for suggestion in results.get('broll_suggestions', [])
                ],
                errors=results.get('errors', [])
            )
            
            # Update job status
            processing_jobs[job_id].status = "completed"
            processing_jobs[job_id].progress = 1.0
            processing_jobs[job_id].message = "Video processing completed successfully"
            processing_jobs[job_id].completed_at = datetime.now()
            processing_jobs[job_id].result = response
            
        else:
            # Processing failed
            processing_jobs[job_id].status = "failed"
            processing_jobs[job_id].progress = 0.0
            processing_jobs[job_id].message = f"Processing failed: {results.get('error', 'Unknown error')}"
            processing_jobs[job_id].completed_at = datetime.now()
        
    except Exception as e:
        logger.error(f"Background video processing failed: {e}")
        processing_jobs[job_id].status = "failed"
        processing_jobs[job_id].progress = 0.0
        processing_jobs[job_id].message = f"Processing failed: {str(e)}"
        processing_jobs[job_id].completed_at = datetime.now()
    
    finally:
        # Cleanup temporary file
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                # Remove temp directory if empty
                temp_dir = os.path.dirname(video_path)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

@router.get("/status/{job_id}", response_model=ProcessingJobStatus)
async def get_processing_status(job_id: str):
    """Get the status of a video processing job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

@router.get("/result/{job_id}", response_model=VideoProcessingResponse)
async def get_processing_result(job_id: str):
    """Get the result of a completed video processing job"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    if job.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    if not job.result:
        raise HTTPException(status_code=500, detail="Job completed but no result available")
    
    return job.result

@router.post("/metadata", response_model=VideoMetadataResponse)
async def extract_video_metadata(video: UploadFile = File(...)):
    """Extract metadata from video file"""
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"metadata_{uuid.uuid4()}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Extract metadata
        metadata = await engine.get_video_metadata(temp_file_path)
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return VideoMetadataResponse(**metadata.__dict__)
        
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Metadata extraction failed: {str(e)}")

@router.post("/keyframes", response_model=List[KeyFrameResponse])
async def extract_keyframes(
    video: UploadFile = File(...),
    processing_strategy: Optional[str] = None
):
    """Extract keyframes from video"""
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"keyframes_{uuid.uuid4()}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Extract metadata and keyframes
        metadata = await engine.get_video_metadata(temp_file_path)
        keyframes = engine._extract_keyframes_advanced(temp_file_path, metadata)
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return [
            KeyFrameResponse(
                frame_number=kf.frame_number,
                timestamp=kf.timestamp,
                confidence=kf.confidence,
                frame_path=kf.frame_path,
                visual_hash=kf.visual_hash,
                objects_detected=kf.objects_detected
            ) for kf in keyframes
        ]
        
    except Exception as e:
        logger.error(f"Keyframe extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Keyframe extraction failed: {str(e)}")

@router.post("/scenes", response_model=List[SceneInfoResponse])
async def detect_scenes(
    video: UploadFile = File(...),
    processing_strategy: Optional[str] = "enhanced"
):
    """Detect scenes in video"""
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"scenes_{uuid.uuid4()}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Extract metadata and detect scenes
        metadata = await engine.get_video_metadata(temp_file_path)
        
        if processing_strategy == "basic":
            scenes = engine._detect_scenes_basic(temp_file_path, metadata)
        else:
            scenes = engine._detect_scenes_advanced(temp_file_path, metadata)
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return [
            SceneInfoResponse(
                start_time=scene.start_time,
                end_time=scene.end_time,
                start_frame=scene.start_frame,
                end_frame=scene.end_frame,
                confidence=scene.confidence,
                scene_type=scene.scene_type.value,
                description=scene.description,
                motion_intensity=scene.motion_intensity,
                visual_complexity=scene.visual_complexity
            ) for scene in scenes
        ]
        
    except Exception as e:
        logger.error(f"Scene detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scene detection failed: {str(e)}")

@router.post("/objects", response_model=List[ObjectDetectionResponse])
async def detect_objects(
    video: UploadFile = File(...),
    processing_strategy: Optional[str] = "enhanced"
):
    """Detect objects in video"""
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"objects_{uuid.uuid4()}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Extract metadata and detect objects
        metadata = await engine.get_video_metadata(temp_file_path)
        
        if processing_strategy == "basic":
            objects = engine._detect_objects_basic(temp_file_path, metadata)
        else:
            objects = engine._detect_objects_advanced(temp_file_path, metadata)
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        return [
            ObjectDetectionResponse(
                class_name=obj.class_name,
                category=obj.category.value,
                confidence=obj.confidence,
                bbox=list(obj.bbox),
                timestamp=obj.timestamp,
                frame_number=obj.frame_number,
                tracking_id=obj.tracking_id
            ) for obj in objects
        ]
        
    except Exception as e:
        logger.error(f"Object detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

@router.post("/broll-suggestions", response_model=List[BRollSuggestionResponse])
async def generate_broll_suggestions(
    video: UploadFile = File(...),
    processing_strategy: Optional[str] = "enhanced"
):
    """Generate intelligent B-roll suggestions for video"""
    engine = get_video_engine()
    if not engine:
        raise HTTPException(status_code=503, detail="Video processing engine not available")
    
    # Validate file type
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"broll_{uuid.uuid4()}.{video.filename.split('.')[-1]}")
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        # Process video for B-roll analysis
        processing_options = {
            'extract_keyframes': True,
            'detect_scenes': True,
            'detect_objects': True,
            'suggest_broll': True
        }
        
        results = await engine.process_video_comprehensive(temp_file_path, processing_options)
        
        # Cleanup
        os.remove(temp_file_path)
        os.rmdir(temp_dir)
        
        if results['success']:
            return [
                BRollSuggestionResponse(
                    timestamp=suggestion.timestamp,
                    duration=suggestion.duration,
                    suggestion_type=suggestion.suggestion_type,
                    description=suggestion.description,
                    confidence=suggestion.confidence,
                    keywords=suggestion.keywords,
                    priority=suggestion.priority
                ) for suggestion in results.get('broll_suggestions', [])
            ]
        else:
            raise HTTPException(status_code=500, detail=f"B-roll analysis failed: {results.get('error')}")
        
    except Exception as e:
        logger.error(f"B-roll suggestion generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"B-roll suggestion generation failed: {str(e)}")

@router.delete("/jobs/{job_id}")
async def delete_processing_job(job_id: str):
    """Delete a processing job and its results"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del processing_jobs[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}

@router.get("/jobs", response_model=List[ProcessingJobStatus])
async def list_processing_jobs():
    """List all processing jobs"""
    return list(processing_jobs.values())

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    engine = get_video_engine()
    
    return {
        "status": "healthy" if engine else "degraded",
        "engine_available": engine is not None,
        "active_jobs": len([job for job in processing_jobs.values() if job.status == "processing"]),
        "total_jobs": len(processing_jobs)
    }