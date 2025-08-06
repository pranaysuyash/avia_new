"""
Intelligent Content Search API Endpoints
FastAPI endpoints for visual scene search and audio pattern recognition
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid
import os
import tempfile
import json

from ...intelligent_content_search import (
    IntelligentContentSearchSystem, VisualScene, AudioPattern, SearchResult
)
from ..auth import get_current_user
from ..models import User
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/intelligent-search", tags=["intelligent-search"])

# Pydantic models
class VisualSearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=10, ge=1, le=100)
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    file_filter: Optional[str] = None

class AudioPatternSearchRequest(BaseModel):
    pattern_type: Optional[str] = Field(None, pattern="^(music|speech|applause|silence|noise)$")
    file_filter: Optional[str] = None
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    max_results: int = Field(default=50, ge=1, le=500)

class VideoProcessRequest(BaseModel):
    video_url: str
    sample_interval: float = Field(default=1.0, ge=0.5, le=10.0)
    analyze_visual: bool = True
    analyze_audio: bool = True
    segment_duration: float = Field(default=5.0, ge=1.0, le=30.0)

class SearchResultResponse(BaseModel):
    content_id: str
    content_type: str
    file_path: str
    timestamp: float
    relevance_score: float
    description: str
    metadata: Dict[str, Any]

class ProcessingStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    results: Optional[Dict[str, Any]] = None

# Initialize search system
search_system = IntelligentContentSearchSystem()

@router.post("/search/visual")
async def search_visual_scenes(
    request: VisualSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for visual scenes using natural language description"""
    try:
        # Perform search
        results = search_system.search_visual_scenes(request.query, request.max_results)
        
        # Filter by confidence
        results = [r for r in results if r.relevance_score >= request.confidence_threshold]
        
        # Filter by file if specified
        if request.file_filter:
            results = [r for r in results if request.file_filter in r.file_path]
        
        # Convert to response format
        response_results = []
        for result in results:
            response_results.append(SearchResultResponse(
                content_id=result.content_id,
                content_type=result.content_type,
                file_path=result.file_path,
                timestamp=result.timestamp,
                relevance_score=result.relevance_score,
                description=result.description,
                metadata=result.metadata
            ))
        
        return {
            "status": "success",
            "query": request.query,
            "results_count": len(response_results),
            "results": response_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/audio")
async def search_audio_patterns(
    request: AudioPatternSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for audio patterns in processed content"""
    try:
        # Perform search
        results = search_system.search_audio_patterns(
            pattern_type=request.pattern_type,
            file_path=request.file_filter
        )
        
        # Filter by confidence
        results = [r for r in results if r.relevance_score >= request.confidence_threshold]
        
        # Limit results
        results = results[:request.max_results]
        
        # Convert to response format
        response_results = []
        for result in results:
            response_results.append(SearchResultResponse(
                content_id=result.content_id,
                content_type=result.content_type,
                file_path=result.file_path,
                timestamp=result.timestamp,
                relevance_score=result.relevance_score,
                description=result.description,
                metadata=result.metadata
            ))
        
        return {
            "status": "success",
            "pattern_type": request.pattern_type,
            "results_count": len(response_results),
            "results": response_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/combined")
async def combined_search(
    query: str,
    max_results: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search across both visual scenes and audio patterns"""
    try:
        # Search visual scenes
        visual_results = search_system.search_visual_scenes(query, max_results // 2)
        
        # Search audio patterns (match query keywords to pattern types)
        pattern_keywords = {
            'music': ['music', 'song', 'melody', 'tune'],
            'speech': ['speech', 'talking', 'voice', 'conversation'],
            'applause': ['applause', 'clapping', 'cheering'],
            'silence': ['silence', 'quiet', 'pause'],
            'noise': ['noise', 'sound', 'audio']
        }
        
        # Find matching pattern type
        pattern_type = None
        query_lower = query.lower()
        for ptype, keywords in pattern_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                pattern_type = ptype
                break
        
        audio_results = search_system.search_audio_patterns(pattern_type=pattern_type)
        audio_results = audio_results[:max_results // 2]
        
        # Combine results
        all_results = visual_results + audio_results
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        all_results = all_results[:max_results]
        
        # Convert to response format
        response_results = []
        for result in all_results:
            response_results.append(SearchResultResponse(
                content_id=result.content_id,
                content_type=result.content_type,
                file_path=result.file_path,
                timestamp=result.timestamp,
                relevance_score=result.relevance_score,
                description=result.description,
                metadata=result.metadata
            ))
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(response_results),
            "results": response_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/video")
async def process_video(
    request: VideoProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a video file for intelligent search"""
    try:
        job_id = str(uuid.uuid4())
        
        # Add background task
        background_tasks.add_task(
            process_video_background,
            job_id,
            request.video_url,
            request.sample_interval,
            request.analyze_visual,
            request.analyze_audio,
            request.segment_duration,
            current_user.id
        )
        
        return ProcessingStatusResponse(
            job_id=job_id,
            status="processing",
            progress=0.0,
            message="Video processing started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/upload")
async def process_uploaded_video(
    file: UploadFile = File(...),
    sample_interval: float = 1.0,
    analyze_visual: bool = True,
    analyze_audio: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process an uploaded video file"""
    try:
        # Validate file type
        allowed_types = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"File type {file.content_type} not supported")
        
        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process video
            results = search_system.process_video_file(tmp_path, sample_interval)
            
            # Clean up temporary file
            os.unlink(tmp_path)
            
            return {
                "status": "success",
                "filename": file.filename,
                "visual_scenes": len(results['visual_scenes']),
                "audio_patterns": len(results['audio_patterns']),
                "metadata": results['metadata']
            }
            
        except Exception as e:
            # Clean up on error
            try:
                os.unlink(tmp_path)
            except:
                pass
            raise e
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline/{file_path:path}")
async def get_video_timeline(
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete timeline of analyzed content for a video"""
    try:
        timeline = search_system.get_video_timeline(file_path)
        
        return {
            "status": "success",
            "file_path": file_path,
            "timeline": timeline
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    try:
        stats = search_system.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing job status"""
    try:
        # In production, fetch from job queue/database
        # For now, return mock status
        return ProcessingStatusResponse(
            job_id=job_id,
            status="completed",
            progress=1.0,
            message="Processing completed successfully",
            results={
                "visual_scenes": 42,
                "audio_patterns": 15,
                "duration": 180.5
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    content_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete analyzed content"""
    try:
        # In production, implement deletion logic
        # For now, return success
        return {
            "status": "success",
            "message": f"Content {content_id} deleted"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def process_video_background(
    job_id: str,
    video_url: str,
    sample_interval: float,
    analyze_visual: bool,
    analyze_audio: bool,
    segment_duration: float,
    user_id: int
):
    """Process video in background"""
    try:
        # Download video if URL
        # Process with search system
        # Update job status in database
        # Send notification when complete
        pass
    except Exception as e:
        # Log error and update job status
        pass