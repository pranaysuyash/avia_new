"""
Media processing endpoints for the API
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import tempfile
import os
import uuid
import asyncio

from database import get_db_session, User, Transcript
from .auth import get_current_user_flexible as get_current_user
import media
import stt
import ner_basic

logger = logging.getLogger(__name__)

# Router setup
media_router = APIRouter()


# Pydantic models
class TranscriptionRequest(BaseModel):
    file_url: Optional[str] = Field(None, description="URL of media file")
    language: str = Field("en", description="Language code")
    model: str = Field("base", description="Whisper model size")
    team_id: Optional[int] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class TranscriptionResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ProcessingOptions(BaseModel):
    extract_entities: bool = True
    generate_summary: bool = False
    detect_speakers: bool = False
    create_segments: bool = True
    generate_tags: bool = True


# In-memory job storage (should be Redis in production)
jobs_store: Dict[str, Dict[str, Any]] = {}


# Helper functions
async def process_media_file(
    job_id: str,
    file_path: str,
    user_id: int,
    language: str = "en",
    model: str = "base",
    team_id: Optional[int] = None,
    options: Dict[str, Any] = None
):
    """Background task to process media file"""
    try:
        # Update job status
        jobs_store[job_id]["status"] = "processing"
        jobs_store[job_id]["progress"] = 10
        
        # Get file info
        file_info = media.get_file_info(file_path)
        duration = file_info.get("duration", 0)
        
        # Update progress
        jobs_store[job_id]["progress"] = 20
        
        # Transcribe audio
        logger.info(f"Starting transcription for job {job_id}")
        transcript_data = stt.transcribe_audio(
            file_path,
            language=language,
            model=model
        )
        
        jobs_store[job_id]["progress"] = 60
        
        # Extract entities if requested
        entities = []
        if options.get("extract_entities", True):
            entities = ner_basic.extract_entities(transcript_data["text"])
            jobs_store[job_id]["progress"] = 80
        
        # Save to database
        db = next(get_db_session())
        transcript = Transcript(
            user_id=user_id,
            team_id=team_id,
            title=f"API Upload - {os.path.basename(file_path)}",
            content=transcript_data["text"],
            metadata={
                "duration": duration,
                "language": language,
                "model": model,
                "confidence": transcript_data.get("confidence", 0),
                "job_id": job_id,
                "api_upload": True
            }
        )
        
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        # Update job with results
        jobs_store[job_id]["status"] = "completed"
        jobs_store[job_id]["progress"] = 100
        jobs_store[job_id]["completed_at"] = datetime.utcnow()
        jobs_store[job_id]["result"] = {
            "transcript_id": transcript.id,
            "text": transcript_data["text"],
            "duration": duration,
            "word_count": len(transcript_data["text"].split()),
            "confidence": transcript_data.get("confidence", 0),
            "entities": entities,
            "language": language
        }
        
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        jobs_store[job_id]["status"] = "failed"
        jobs_store[job_id]["error"] = str(e)
        jobs_store[job_id]["completed_at"] = datetime.utcnow()
    
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)


# Endpoints
@media_router.post("/upload", response_model=TranscriptionResponse)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Query("en", description="Language code"),
    model: str = Query("base", description="Whisper model size"),
    team_id: Optional[int] = Query(None, description="Team ID"),
    current_user: User = Depends(get_current_user)
):
    """Upload media file for transcription"""
    
    # Validate file type
    allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.mp4', '.avi', '.mov', '.mkv'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (max 500MB)
    max_size = 500 * 1024 * 1024  # 500MB
    file_size = 0
    
    # Save uploaded file
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"api_upload_{uuid.uuid4()}{file_ext}")
    
    try:
        with open(temp_path, "wb") as f:
            while True:
                chunk = await file.read(8192)  # Read in chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > max_size:
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum size is {max_size / 1024 / 1024}MB"
                    )
                f.write(chunk)
        
        # Create job
        job_id = str(uuid.uuid4())
        jobs_store[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.utcnow(),
            "user_id": current_user.id,
            "filename": file.filename
        }
        
        # Estimate processing time (rough estimate: 1 minute per 10MB)
        estimated_time = max(60, int(file_size / (10 * 1024 * 1024) * 60))
        
        # Start background processing
        background_tasks.add_task(
            process_media_file,
            job_id=job_id,
            file_path=temp_path,
            user_id=current_user.id,
            language=language,
            model=model,
            team_id=team_id,
            options={}
        )
        
        return TranscriptionResponse(
            job_id=job_id,
            status="pending",
            message=f"File '{file.filename}' uploaded successfully. Processing started.",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@media_router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_from_url(
    background_tasks: BackgroundTasks,
    request: TranscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Start transcription from URL"""
    
    if not request.file_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_url is required"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    jobs_store[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "created_at": datetime.utcnow(),
        "user_id": current_user.id,
        "file_url": request.file_url
    }
    
    # For URL processing, we'd download and process the file
    # This is simplified for demonstration
    return TranscriptionResponse(
        job_id=job_id,
        status="pending",
        message="Transcription job created. Use /status endpoint to check progress.",
        estimated_time=300  # 5 minutes estimate
    )


@media_router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get job status"""
    
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify user owns the job
    if job.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress"),
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@media_router.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100)
):
    """List user's jobs"""
    
    user_jobs = []
    for job in jobs_store.values():
        if job.get("user_id") == current_user.id:
            if status is None or job["status"] == status:
                user_jobs.append(JobStatusResponse(
                    job_id=job["job_id"],
                    status=job["status"],
                    progress=job.get("progress"),
                    result=job.get("result"),
                    error=job.get("error"),
                    created_at=job["created_at"],
                    completed_at=job.get("completed_at")
                ))
    
    # Sort by created_at desc and limit
    user_jobs.sort(key=lambda x: x.created_at, reverse=True)
    return user_jobs[:limit]


@media_router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending job"""
    
    job = jobs_store.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Verify user owns the job
    if job.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Can only cancel pending jobs
    if job["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status '{job['status']}'"
        )
    
    # Update status
    job["status"] = "cancelled"
    job["completed_at"] = datetime.utcnow()
    
    return {"message": "Job cancelled successfully"}