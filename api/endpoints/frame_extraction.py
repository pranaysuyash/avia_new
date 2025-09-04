"""
FastAPI endpoints for Advanced Frame Extraction Service

This module provides RESTful API endpoints for frame extraction functionality
with comprehensive job management and result retrieval.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import tempfile
import os
import json
import uuid
from datetime import datetime
import asyncio
from pathlib import Path
import zipfile
import io
import base64

from frame_extraction_service import (
    FrameExtractionService, ExtractionConfig, SamplingStrategy,
    FrameQuality, ExtractedFrame, VideoMetadata
)

# Create router
router = APIRouter(prefix="/api/v1/frame-extraction", tags=["Frame Extraction"])

# In-memory job storage (in production, use a proper database)
job_storage = {}
result_storage = {}


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SamplingStrategyAPI(str, Enum):
    """API sampling strategy enumeration"""
    TIME_BASED = "time_based"
    KEYFRAME = "keyframe"
    SCENE_CHANGE = "scene_change"
    ADAPTIVE = "adaptive"
    HYBRID = "hybrid"


class ExtractionConfigRequest(BaseModel):
    """Request model for extraction configuration"""
    sampling_strategy: SamplingStrategyAPI = SamplingStrategyAPI.ADAPTIVE
    time_interval: float = Field(default=1.0, ge=0.1, le=60.0)
    max_frames: int = Field(default=100, ge=1, le=10000)
    min_quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    enable_quality_assessment: bool = True
    enable_perspective_correction: bool = True
    enable_preprocessing: bool = True
    keyframe_threshold: float = Field(default=0.3, ge=0.1, le=1.0)
    scene_change_threshold: float = Field(default=0.4, ge=0.1, le=1.0)
    adaptive_complexity_threshold: float = Field(default=0.5, ge=0.1, le=1.0)
    target_width: Optional[int] = Field(default=None, ge=100, le=4000)
    target_height: Optional[int] = Field(default=None, ge=100, le=4000)
    save_frames: bool = False


class JobResponse(BaseModel):
    """Response model for job information"""
    job_id: str
    status: JobStatus
    video_filename: str
    config: ExtractionConfigRequest
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    frames_extracted: int = 0
    error_message: Optional[str] = None
    processing_time: Optional[float] = None


class VideoMetadataResponse(BaseModel):
    """Response model for video metadata"""
    duration: float
    fps: float
    width: int
    height: int
    total_frames: int
    format: str
    codec: str
    bitrate: int
    file_size: int
    aspect_ratio: float
    color_space: str
    has_audio: bool


class CostEstimateResponse(BaseModel):
    """Response model for cost estimation"""
    estimated_frames: int
    estimated_processing_time_seconds: float
    estimated_storage_mb: float
    video_duration: float
    video_resolution: str
    sampling_strategy: str
    quality_assessment_enabled: bool
    preprocessing_enabled: bool


class FrameQualityResponse(BaseModel):
    """Response model for frame quality metrics"""
    blur_score: float
    contrast_score: float
    brightness_score: float
    noise_level: float
    sharpness_score: float
    perspective_skew: float
    text_region_density: float
    overall_quality: str
    confidence: float


class ExtractedFrameResponse(BaseModel):
    """Response model for extracted frame"""
    frame_number: int
    timestamp: float
    quality_metrics: FrameQualityResponse
    sampling_reason: str
    processing_metadata: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None  # URL to access frame image


class ExtractionResultsResponse(BaseModel):
    """Response model for extraction results"""
    job_id: str
    frames: List[ExtractedFrameResponse]
    total_frames: int
    processing_time: float
    average_quality: float
    quality_distribution: Dict[str, int]
    sampling_summary: Dict[str, int]


def convert_config_to_internal(config: ExtractionConfigRequest) -> ExtractionConfig:
    """Convert API config to internal config"""
    target_resolution = None
    if config.target_width and config.target_height:
        target_resolution = (config.target_width, config.target_height)
    
    return ExtractionConfig(
        sampling_strategy=SamplingStrategy(config.sampling_strategy.value),
        time_interval=config.time_interval,
        max_frames=config.max_frames,
        min_quality_threshold=config.min_quality_threshold,
        enable_quality_assessment=config.enable_quality_assessment,
        enable_perspective_correction=config.enable_perspective_correction,
        enable_preprocessing=config.enable_preprocessing,
        target_resolution=target_resolution,
        keyframe_threshold=config.keyframe_threshold,
        scene_change_threshold=config.scene_change_threshold,
        adaptive_complexity_threshold=config.adaptive_complexity_threshold,
        save_frames=config.save_frames
    )


def convert_metadata_to_response(metadata: VideoMetadata) -> VideoMetadataResponse:
    """Convert internal metadata to API response"""
    return VideoMetadataResponse(
        duration=metadata.duration,
        fps=metadata.fps,
        width=metadata.width,
        height=metadata.height,
        total_frames=metadata.total_frames,
        format=metadata.format,
        codec=metadata.codec,
        bitrate=metadata.bitrate,
        file_size=metadata.file_size,
        aspect_ratio=metadata.aspect_ratio,
        color_space=metadata.color_space,
        has_audio=metadata.has_audio
    )


def convert_frame_to_response(frame: ExtractedFrame, job_id: str) -> ExtractedFrameResponse:
    """Convert internal frame to API response"""
    quality_response = FrameQualityResponse(
        blur_score=frame.quality_metrics.blur_score,
        contrast_score=frame.quality_metrics.contrast_score,
        brightness_score=frame.quality_metrics.brightness_score,
        noise_level=frame.quality_metrics.noise_level,
        sharpness_score=frame.quality_metrics.sharpness_score,
        perspective_skew=frame.quality_metrics.perspective_skew,
        text_region_density=frame.quality_metrics.text_region_density,
        overall_quality=frame.quality_metrics.overall_quality.value,
        confidence=frame.quality_metrics.confidence
    )
    
    return ExtractedFrameResponse(
        frame_number=frame.frame_number,
        timestamp=frame.timestamp,
        quality_metrics=quality_response,
        sampling_reason=frame.sampling_reason,
        processing_metadata=frame.processing_metadata,
        image_url=f"/api/v1/frame-extraction/jobs/{job_id}/frames/{frame.frame_number}/image"
    )


async def process_extraction_job(job_id: str, video_path: str, config: ExtractionConfig):
    """Background task to process frame extraction"""
    try:
        # Update job status
        job_storage[job_id]["status"] = JobStatus.PROCESSING
        job_storage[job_id]["started_at"] = datetime.now()
        
        # Initialize service
        service = FrameExtractionService(config)
        
        # Extract frames
        start_time = datetime.now()
        frames = service.extract_frames(video_path, config)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Store results
        result_storage[job_id] = {
            "frames": frames,
            "processing_time": processing_time,
            "video_path": video_path
        }
        
        # Update job status
        job_storage[job_id]["status"] = JobStatus.COMPLETED
        job_storage[job_id]["completed_at"] = end_time
        job_storage[job_id]["frames_extracted"] = len(frames)
        job_storage[job_id]["processing_time"] = processing_time
        job_storage[job_id]["progress"] = 1.0
        
    except Exception as e:
        # Handle errors
        job_storage[job_id]["status"] = JobStatus.FAILED
        job_storage[job_id]["error_message"] = str(e)
        job_storage[job_id]["completed_at"] = datetime.now()
        
        # Clean up video file on error
        if os.path.exists(video_path):
            os.unlink(video_path)


@router.post("/jobs", response_model=JobResponse)
async def create_extraction_job(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    config: ExtractionConfigRequest = Depends()
):
    """
    Create a new frame extraction job
    
    Upload a video file and configure extraction parameters to start processing.
    """
    # Validate file type
    if not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')):
        raise HTTPException(status_code=400, detail="Unsupported video format")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, f"{job_id}_{video_file.filename}")
    
    try:
        with open(video_path, "wb") as buffer:
            content = await video_file.read()
            buffer.write(content)
        
        # Create job record
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "video_filename": video_file.filename,
            "video_path": video_path,
            "config": config,
            "created_at": datetime.now(),
            "progress": 0.0,
            "frames_extracted": 0
        }
        
        job_storage[job_id] = job_data
        
        # Convert config and start background processing
        internal_config = convert_config_to_internal(config)
        background_tasks.add_task(process_extraction_job, job_id, video_path, internal_config)
        
        return JobResponse(**job_data)
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(video_path):
            os.unlink(video_path)
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a frame extraction job
    
    Returns current job status, progress, and metadata.
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = job_storage[job_id].copy()
    return JobResponse(**job_data)


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a frame extraction job
    
    Cancels a pending or processing job and cleans up resources.
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    # Update status
    job["status"] = JobStatus.CANCELLED
    job["completed_at"] = datetime.now()
    
    # Clean up files
    if "video_path" in job and os.path.exists(job["video_path"]):
        os.unlink(job["video_path"])
    
    if job_id in result_storage:
        del result_storage[job_id]
    
    return {"message": "Job cancelled successfully"}


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Retry a failed frame extraction job
    
    Restarts processing for a failed job with the same configuration.
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    if job["status"] != JobStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    
    # Reset job status
    job["status"] = JobStatus.PENDING
    job["started_at"] = None
    job["completed_at"] = None
    job["error_message"] = None
    job["progress"] = 0.0
    job["frames_extracted"] = 0
    
    # Restart processing
    internal_config = convert_config_to_internal(job["config"])
    background_tasks.add_task(process_extraction_job, job_id, job["video_path"], internal_config)
    
    return JobResponse(**job)


@router.get("/jobs/{job_id}/results", response_model=ExtractionResultsResponse)
async def get_extraction_results(
    job_id: str,
    include_images: bool = Query(default=False, description="Include base64 encoded images"),
    quality_filter: Optional[str] = Query(default=None, description="Filter by quality level"),
    limit: Optional[int] = Query(default=None, ge=1, le=1000, description="Limit number of frames returned")
):
    """
    Get extraction results for a completed job
    
    Returns extracted frames with metadata and optional image data.
    """
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_storage[job_id]
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if job_id not in result_storage:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = result_storage[job_id]
    frames = results["frames"]
    
    # Apply quality filter
    if quality_filter:
        frames = [f for f in frames if f.quality_metrics.overall_quality.value == quality_filter.lower()]
    
    # Apply limit
    if limit:
        frames = frames[:limit]
    
    # Convert frames to response format
    frame_responses = []
    for frame in frames:
        frame_response = convert_frame_to_response(frame, job_id)
        
        # Include base64 image if requested
        if include_images:
            import cv2
            import base64
            
            # Encode image as base64
            _, buffer = cv2.imencode('.jpg', frame.image_data)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            frame_response.image_data = image_base64
        
        frame_responses.append(frame_response)
    
    # Calculate statistics
    all_frames = results["frames"]
    qualities = [f.quality_metrics.confidence for f in all_frames]
    average_quality = sum(qualities) / len(qualities) if qualities else 0
    
    # Quality distribution
    quality_distribution = {}
    for frame in all_frames:
        quality_level = frame.quality_metrics.overall_quality.value
        quality_distribution[quality_level] = quality_distribution.get(quality_level, 0) + 1
    
    # Sampling summary
    sampling_summary = {}
    for frame in all_frames:
        reason = frame.sampling_reason.split('_')[0]
        sampling_summary[reason] = sampling_summary.get(reason, 0) + 1
    
    return ExtractionResultsResponse(
        job_id=job_id,
        frames=frame_responses,
        total_frames=len(all_frames),
        processing_time=results["processing_time"],
        average_quality=average_quality,
        quality_distribution=quality_distribution,
        sampling_summary=sampling_summary
    )


@router.get("/jobs/{job_id}/frames/{frame_number}/image")
async def get_frame_image(job_id: str, frame_number: int):
    """
    Get the image data for a specific frame
    
    Returns the frame image as a JPEG file.
    """
    if job_id not in result_storage:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = result_storage[job_id]
    frames = results["frames"]
    
    # Find the frame
    target_frame = None
    for frame in frames:
        if frame.frame_number == frame_number:
            target_frame = frame
            break
    
    if not target_frame:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    # Convert image to JPEG and return
    import cv2
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        cv2.imwrite(tmp_file.name, target_frame.image_data)
        return FileResponse(
            tmp_file.name,
            media_type="image/jpeg",
            filename=f"frame_{frame_number}_{target_frame.timestamp:.3f}s.jpg"
        )


@router.get("/jobs/{job_id}/export/zip")
async def export_frames_zip(job_id: str):
    """
    Export all frames as a ZIP file
    
    Downloads all extracted frames as JPEG images in a ZIP archive.
    """
    if job_id not in result_storage:
        raise HTTPException(status_code=404, detail="Results not found")
    
    results = result_storage[job_id]
    frames = results["frames"]
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for frame in frames:
            # Convert frame to JPEG
            import cv2
            _, buffer = cv2.imencode('.jpg', frame.image_data)
            
            # Add to ZIP
            filename = f"frame_{frame.frame_number:06d}_{frame.timestamp:.3f}s.jpg"
            zip_file.writestr(filename, buffer.tobytes())
        
        # Add metadata JSON
        metadata = {
            "job_id": job_id,
            "total_frames": len(frames),
            "processing_time": results["processing_time"],
            "frames": [
                {
                    "frame_number": f.frame_number,
                    "timestamp": f.timestamp,
                    "quality_score": f.quality_metrics.confidence,
                    "sampling_reason": f.sampling_reason
                }
                for f in frames
            ]
        }
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    zip_buffer.seek(0)
    
    # Return ZIP file
    return FileResponse(
        zip_buffer,
        media_type="application/zip",
        filename=f"extracted_frames_{job_id}.zip"
    )


@router.post("/analyze/metadata", response_model=VideoMetadataResponse)
async def analyze_video_metadata(video_file: UploadFile = File(...)):
    """
    Analyze video metadata without extraction
    
    Upload a video file to get metadata information only.
    """
    # Validate file type
    if not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')):
        raise HTTPException(status_code=400, detail="Unsupported video format")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        content = await video_file.read()
        tmp_file.write(content)
        video_path = tmp_file.name
    
    try:
        # Extract metadata
        service = FrameExtractionService()
        metadata = service.get_video_metadata(video_path)
        
        return convert_metadata_to_response(metadata)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze video: {str(e)}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_processing_cost(
    video_file: UploadFile = File(...),
    config: ExtractionConfigRequest = Depends()
):
    """
    Estimate processing cost for extraction job
    
    Upload a video file and configuration to get cost estimates.
    """
    # Validate file type
    if not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v')):
        raise HTTPException(status_code=400, detail="Unsupported video format")
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        content = await video_file.read()
        tmp_file.write(content)
        video_path = tmp_file.name
    
    try:
        # Convert config and estimate cost
        internal_config = convert_config_to_internal(config)
        service = FrameExtractionService()
        cost_estimate = service.estimate_processing_cost(video_path, internal_config)
        
        return CostEstimateResponse(**cost_estimate)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to estimate cost: {str(e)}")
    
    finally:
        # Clean up
        if os.path.exists(video_path):
            os.unlink(video_path)


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(default=None, description="Filter by job status"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of jobs to return")
):
    """
    List frame extraction jobs
    
    Returns a list of jobs with optional status filtering.
    """
    jobs = list(job_storage.values())
    
    # Apply status filter
    if status:
        jobs = [job for job in jobs if job["status"] == status]
    
    # Sort by creation time (newest first)
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Apply limit
    jobs = jobs[:limit]
    
    return [JobResponse(**job) for job in jobs]


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service health status and statistics.
    """
    total_jobs = len(job_storage)
    status_counts = {}
    
    for job in job_storage.values():
        status = job["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_jobs": total_jobs,
            "status_distribution": status_counts,
            "active_results": len(result_storage)
        }
    }