"""
API Endpoints for Processing Router and Workflow Engine
FastAPI endpoints for intelligent media processing routing and workflow orchestration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os
import tempfile
import uuid
import logging

# Import our processing router
try:
    from processing_router_workflow_engine import (
        ProcessingRouterWorkflowEngine,
        MediaType,
        ContentComplexity,
        ProcessingStrategy,
        WorkflowPriority,
        WorkflowStatus
    )
except ImportError as e:
    logging.warning(f"Import warning: {e}")
    # Fallback for testing
    class ProcessingRouterWorkflowEngine:
        pass

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/processing", tags=["Processing Router"])

# Global processing engine instance
processing_engine: Optional[ProcessingRouterWorkflowEngine] = None

# Pydantic models for API
class ContentAnalysisResponse(BaseModel):
    """Content analysis response model"""
    media_type: str
    file_size_mb: float
    duration_seconds: float
    complexity: str
    quality_score: float
    processing_requirements: List[str]
    estimated_processing_time: float
    resource_requirements: Dict[str, Any]
    content_features: Dict[str, Any]

class ProcessingRouteInfo(BaseModel):
    """Processing route information model"""
    route_id: str
    name: str
    description: str
    media_types: List[str]
    complexity_levels: List[str]
    processing_steps: List[str]
    strategy: str
    mode: str
    priority: str
    estimated_duration: float
    resource_cost: float
    fallback_routes: List[str]

class ProcessingJobRequest(BaseModel):
    """Processing job request model"""
    custom_route: Optional[str] = None
    priority: str = "normal"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProcessingJobResponse(BaseModel):
    """Processing job response model"""
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    """Job status response model"""
    job_id: str
    status: str
    progress: float
    route: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    errors: List[str]
    results: Dict[str, Any]

class PerformanceMetricsResponse(BaseModel):
    """Performance metrics response model"""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    average_processing_time: float
    active_jobs: int
    queued_jobs: int
    available_routes: int
    resource_utilization: float

def get_processing_engine() -> ProcessingRouterWorkflowEngine:
    """Get or create processing engine instance"""
    global processing_engine
    if processing_engine is None:
        processing_engine = ProcessingRouterWorkflowEngine(max_concurrent_jobs=4)
        logger.info("Processing engine initialized")
    return processing_engine

@router.on_event("startup")
async def startup_event():
    """Initialize processing engine on startup"""
    get_processing_engine()
    logger.info("Processing Router API started")

@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup processing engine on shutdown"""
    global processing_engine
    if processing_engine:
        await processing_engine.cleanup()
        logger.info("Processing engine cleaned up")

@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint"""
    try:
        engine = get_processing_engine()
        metrics = engine.get_performance_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_jobs": metrics["active_jobs"],
            "total_processed": metrics["total_jobs"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@router.get("/routes", response_model=List[ProcessingRouteInfo], summary="Get available processing routes")
async def get_processing_routes():
    """Get all available processing routes"""
    try:
        engine = get_processing_engine()
        routes = []
        
        for route_id, route in engine.processing_routes.items():
            routes.append(ProcessingRouteInfo(
                route_id=route.route_id,
                name=route.name,
                description=route.description,
                media_types=[mt.value for mt in route.media_types],
                complexity_levels=[cl.value for cl in route.complexity_levels],
                processing_steps=route.processing_steps,
                strategy=route.strategy.value,
                mode=route.mode.value,
                priority=route.priority.value,
                estimated_duration=route.estimated_duration,
                resource_cost=route.resource_cost,
                fallback_routes=route.fallback_routes
            ))
        
        return routes
        
    except Exception as e:
        logger.error(f"Failed to get processing routes: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve processing routes")

@router.post("/analyze", response_model=ContentAnalysisResponse, summary="Analyze media content")
async def analyze_content(file: UploadFile = File(...)):
    """Analyze uploaded media content for processing route selection"""
    try:
        engine = get_processing_engine()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Analyze content
            analysis = await engine.analyze_content(tmp_file_path)
            
            return ContentAnalysisResponse(
                media_type=analysis.media_type.value,
                file_size_mb=analysis.file_size_mb,
                duration_seconds=analysis.duration_seconds,
                complexity=analysis.complexity.value,
                quality_score=analysis.quality_score,
                processing_requirements=analysis.processing_requirements,
                estimated_processing_time=analysis.estimated_processing_time,
                resource_requirements=analysis.resource_requirements,
                content_features=analysis.content_features
            )
            
        finally:
            # Cleanup temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")

@router.post("/process", response_model=ProcessingJobResponse, summary="Process media file")
async def process_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    custom_route: Optional[str] = Form(None),
    priority: str = Form("normal")
):
    """Process uploaded media file through intelligent routing"""
    try:
        engine = get_processing_engine()
        
        # Validate priority
        try:
            priority_enum = WorkflowPriority(priority.lower())
        except ValueError:
            priority_enum = WorkflowPriority.NORMAL
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Start processing
        job_id = await engine.process_media(
            tmp_file_path,
            custom_route=custom_route,
            priority=priority_enum
        )
        
        # Schedule cleanup of temporary file after processing
        background_tasks.add_task(cleanup_temp_file, tmp_file_path, job_id, engine)
        
        return ProcessingJobResponse(
            job_id=job_id,
            status="submitted",
            message=f"Processing job {job_id} submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Media processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Media processing failed: {str(e)}")

@router.get("/jobs/{job_id}", response_model=JobStatusResponse, summary="Get job status")
async def get_job_status(job_id: str):
    """Get status and progress of a processing job"""
    try:
        engine = get_processing_engine()
        status = engine.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job status")

@router.get("/jobs", summary="List all jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List processing jobs with optional filtering"""
    try:
        engine = get_processing_engine()
        
        # Get all jobs
        all_jobs = {**engine.active_jobs, **engine.completed_jobs}
        
        # Filter by status if provided
        if status:
            filtered_jobs = {
                job_id: job for job_id, job in all_jobs.items()
                if job.status.value == status.lower()
            }
        else:
            filtered_jobs = all_jobs
        
        # Apply pagination
        job_items = list(filtered_jobs.items())[offset:offset + limit]
        
        jobs = []
        for job_id, job in job_items:
            job_status = engine.get_job_status(job_id)
            if job_status:
                jobs.append(job_status)
        
        return {
            "jobs": jobs,
            "total": len(filtered_jobs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")

@router.delete("/jobs/{job_id}", summary="Cancel job")
async def cancel_job(job_id: str):
    """Cancel a processing job"""
    try:
        engine = get_processing_engine()
        
        # Check if job exists
        job_status = engine.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job can be cancelled
        if job_status['status'] in ['completed', 'failed', 'cancelled']:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        # Cancel job (implementation would depend on the actual job execution)
        if job_id in engine.active_jobs:
            engine.active_jobs[job_id].status = WorkflowStatus.CANCELLED
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel job")

@router.get("/metrics", response_model=PerformanceMetricsResponse, summary="Get performance metrics")
async def get_performance_metrics():
    """Get processing engine performance metrics"""
    try:
        engine = get_processing_engine()
        metrics = engine.get_performance_metrics()
        
        return PerformanceMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@router.post("/routes/{route_id}/test", summary="Test processing route")
async def test_processing_route(route_id: str, file: UploadFile = File(...)):
    """Test a specific processing route with uploaded file"""
    try:
        engine = get_processing_engine()
        
        # Check if route exists
        if route_id not in engine.processing_routes:
            raise HTTPException(status_code=404, detail="Processing route not found")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Analyze content first
            analysis = await engine.analyze_content(tmp_file_path)
            
            # Get route info
            route = engine.processing_routes[route_id]
            
            # Check compatibility
            compatible = (
                analysis.media_type in route.media_types and
                analysis.complexity in route.complexity_levels
            )
            
            return {
                "route_id": route_id,
                "route_name": route.name,
                "compatible": compatible,
                "content_analysis": {
                    "media_type": analysis.media_type.value,
                    "complexity": analysis.complexity.value,
                    "file_size_mb": analysis.file_size_mb
                },
                "estimated_processing_time": route.estimated_duration,
                "processing_steps": route.processing_steps
            }
            
        finally:
            os.unlink(tmp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Route testing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Route testing failed: {str(e)}")

@router.get("/stats", summary="Get processing statistics")
async def get_processing_stats():
    """Get detailed processing statistics"""
    try:
        engine = get_processing_engine()
        metrics = engine.get_performance_metrics()
        
        # Calculate additional stats
        success_rate = (
            metrics['successful_jobs'] / metrics['total_jobs'] * 100
            if metrics['total_jobs'] > 0 else 0
        )
        
        # Get route usage stats
        route_usage = {}
        for job in engine.completed_jobs.values():
            route_id = job.selected_route.route_id
            route_usage[route_id] = route_usage.get(route_id, 0) + 1
        
        return {
            "overview": {
                "total_jobs": metrics['total_jobs'],
                "success_rate": round(success_rate, 2),
                "average_processing_time": round(metrics['average_processing_time'], 2),
                "active_jobs": metrics['active_jobs'],
                "queued_jobs": metrics['queued_jobs']
            },
            "route_usage": route_usage,
            "available_routes": metrics['available_routes'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve processing statistics")

async def cleanup_temp_file(file_path: str, job_id: str, engine: ProcessingRouterWorkflowEngine):
    """Background task to cleanup temporary files after processing"""
    try:
        # Wait for job to complete or timeout
        max_wait = 3600  # 1 hour timeout
        wait_time = 0
        
        while wait_time < max_wait:
            job_status = engine.get_job_status(job_id)
            if job_status and job_status['status'] in ['completed', 'failed', 'cancelled']:
                break
            
            await asyncio.sleep(10)  # Check every 10 seconds
            wait_time += 10
        
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
            
    except Exception as e:
        logger.error(f"Failed to cleanup temporary file {file_path}: {e}")

# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
        }
    )

# Include additional imports for background tasks
import asyncio