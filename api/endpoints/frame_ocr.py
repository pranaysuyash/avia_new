#!/usr/bin/env python3
"""
Frame OCR API Endpoints
FastAPI endpoints for Frame OCR processing and search
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query, BackgroundTasks, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid
from pathlib import Path

from api.auth_middleware import get_current_user
from database.connection import get_db
from database.models import User  # Import User from models.py instead of connection.py

# Import Frame OCR components
from frame_ocr_pipeline import FrameOCRPipeline
from frame_ocr_models import (
    FrameOCRJob, FrameOCRResult, TextSegment, BoundingBox, OCRJobConfig,
    JobStatus, OCREngine, RegionType, SamplingStrategy
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/frame-ocr", tags=["frame-ocr"])

# Initialize pipeline (singleton)
frame_ocr_pipeline = FrameOCRPipeline()


class ProcessVideoRequest(BaseModel):
    """Request model for video processing"""
    sampling_strategy: SamplingStrategy = Field(
        default=SamplingStrategy.ADAPTIVE,
        description="Frame sampling strategy"
    )
    sampling_interval: float = Field(
        default=2.0,
        ge=0.1,
        le=60.0,
        description="Sampling interval in seconds (for time-based sampling)"
    )
    max_frames: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of frames to process"
    )
    quality_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum frame quality threshold"
    )
    ocr_engine: OCREngine = Field(
        default=OCREngine.TESSERACT,
        description="OCR engine to use"
    )
    languages: List[str] = Field(
        default=["en"],
        description="Languages to detect (ISO 639-1 codes)"
    )
    preprocess: bool = Field(
        default=True,
        description="Enable image preprocessing"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for text recognition"
    )
    enable_spell_check: bool = Field(
        default=True,
        description="Enable spell checking and correction"
    )
    enable_gpu_acceleration: bool = Field(
        default=False,
        description="Enable GPU acceleration (if available)"
    )


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: JobStatus
    progress: int
    message: Optional[str]
    created_at: datetime
    updated_at: datetime
    video_path: str
    frames_processed: Optional[int]
    results_indexed: Optional[int]


class SearchResult(BaseModel):
    """Response model for search results"""
    text: str
    timestamp: float
    frame_number: int
    confidence: float
    language: str
    job_id: str
    bounding_boxes: List[BoundingBox]


class SearchRequest(BaseModel):
    """Request model for searching in OCR results"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query text"
    )
    job_id: Optional[str] = Field(
        None,
        description="Filter results by specific job ID"
    )
    min_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    language: Optional[str] = Field(
        None,
        description="Filter results by language"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )


@router.post("/process", response_model=JobStatusResponse)
async def process_video(
    video_file: UploadFile = File(...),
    request: ProcessVideoRequest = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    """
    Process a video file and extract text from frames using OCR.
    
    This endpoint accepts a video file and configuration parameters,
    then starts background processing to extract text from video frames.
    The processing includes frame extraction, OCR processing, and indexing
    the results for search.
    """
    try:
        # Validate file type
        allowed_types = {
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv',
            'video/webm', 'video/mkv'
        }
        
        if video_file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {video_file.content_type}"
            )
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await video_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Create job configuration from request
        job_config = OCRJobConfig(
            sampling_strategy=request.sampling_strategy,
            sampling_interval=request.sampling_interval,
            max_frames=request.max_frames,
            quality_threshold=request.quality_threshold,
            ocr_engine=request.ocr_engine,
            languages=request.languages,
            preprocess=request.preprocess,
            confidence_threshold=request.confidence_threshold,
            enable_spell_check=request.enable_spell_check,
            enable_gpu_acceleration=request.enable_gpu_acceleration
        )
        
        # Process video in background
        job_id = await frame_ocr_pipeline.process_video(temp_file_path, job_config)
        
        # Get initial job status
        job_record = frame_ocr_pipeline.database.get_job(job_id)
        
        return JobStatusResponse(
            job_id=job_id,
            status=job_record.status,
            progress=job_record.progress,
            message=job_record.message,
            created_at=job_record.created_at,
            updated_at=job_record.updated_at,
            video_path=job_record.video_path,
            frames_processed=None,
            results_indexed=None
        )
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a Frame OCR processing job.
    
    Returns detailed information about the job including current status,
    progress percentage, and any messages or errors.
    """
    try:
        # Get job record from database
        job_record = frame_ocr_pipeline.database.get_job(job_id)
        
        if not job_record:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Get additional metrics
        frames_processed = None
        results_indexed = None
        
        if job_record.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            # Get count of processed frames
            frames_processed = frame_ocr_pipeline.database.get_frame_count(job_id)
            results_indexed = frame_ocr_pipeline.database.get_indexed_count(job_id)
        
        return JobStatusResponse(
            job_id=job_record.job_id,
            status=job_record.status,
            progress=job_record.progress,
            message=job_record.message,
            created_at=job_record.created_at,
            updated_at=job_record.updated_at,
            video_path=job_record.video_path,
            frames_processed=frames_processed,
            results_indexed=results_indexed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/results/{job_id}", response_model=List[SearchResult])
async def get_ocr_results(
    job_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user)
):
    """
    Get OCR results for a specific job.
    
    Returns the extracted text segments with their timestamps and metadata.
    Results can be filtered by confidence threshold and paginated.
    """
    try:
        # Validate job exists
        job_record = frame_ocr_pipeline.database.get_job(job_id)
        
        if not job_record:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Get OCR results from database
        results = frame_ocr_pipeline.database.get_results(
            job_id=job_id,
            limit=limit,
            offset=offset,
            min_confidence=min_confidence
        )
        
        # Convert to response format
        response_results = []
        for result in results:
            response_results.append(SearchResult(
                text=result.text,
                timestamp=result.timestamp,
                frame_number=result.frame_number,
                confidence=result.confidence,
                language=result.language,
                job_id=result.job_id,
                bounding_boxes=result.bounding_boxes or []
            ))
        
        return response_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting OCR results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get OCR results: {str(e)}"
        )


@router.post("/query", response_model=List[SearchResult])
async def search_ocr_results(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for text in OCR results across all processed videos.
    
    Performs a full-text search in the indexed OCR results and returns
    matching text segments with their timestamps for video navigation.
    """
    try:
        # Search in OCR results using the search integration
        search_results = await frame_ocr_pipeline.search_integration.search_documents(
            query=request.query,
            filters={
                'job_id': request.job_id,
                'min_confidence': request.min_confidence,
                'language': request.language
            },
            limit=request.limit
        )
        
        # Convert search results to response format
        response_results = []
        for result in search_results:
            # Extract relevant fields from search result
            response_results.append(SearchResult(
                text=result.get('content', ''),
                timestamp=result.get('timestamp', 0.0),
                frame_number=result.get('frame_number', 0),
                confidence=result.get('confidence', 0.0),
                language=result.get('language', 'en'),
                job_id=result.get('job_id', ''),
                bounding_boxes=[]  # Bounding boxes would need to be stored separately
            ))
        
        return response_results
        
    except Exception as e:
        logger.error(f"Error searching OCR results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search OCR results: {str(e)}"
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a Frame OCR processing job.
    
    Attempts to cancel an active processing job. Note that cancellation
    may not be immediate for jobs that are already in progress.
    """
    try:
        # Check if job exists
        job_record = frame_ocr_pipeline.database.get_job(job_id)
        
        if not job_record:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        # Check if job can be cancelled
        if job_record.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING]:
            raise HTTPException(
                status_code=400,
                detail=f"Job {job_id} cannot be cancelled (status: {job_record.status.value})"
            )
        
        # Update job status to cancelled
        frame_ocr_pipeline.database.update_job_status(job_id, JobStatus.CANCELLED)
        
        return {
            "message": f"Job {job_id} cancelled successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    List Frame OCR processing jobs.
    
    Returns a list of jobs with their current status, optionally filtered
    by status and paginated.
    """
    try:
        # Get jobs from database
        jobs = frame_ocr_pipeline.database.list_jobs(
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        response_jobs = []
        for job in jobs:
            response_jobs.append(JobStatusResponse(
                job_id=job.job_id,
                status=job.status,
                progress=job.progress,
                message=job.message,
                created_at=job.created_at,
                updated_at=job.updated_at,
                video_path=job.video_path,
                frames_processed=None,
                results_indexed=None
            ))
        
        return response_jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )