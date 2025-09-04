"""
FastAPI endpoints for Frame OCR Job Management System

This module provides RESTful API endpoints for enterprise job management
with comprehensive features including job lifecycle, monitoring, and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

from frame_ocr_job_manager import (
    FrameOCRJobManager, JobStatus, JobPriority, ProcessingMode,
    ResourceAllocation, RetryConfig, FrameOCRJob, JobMetrics
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/frame-ocr", tags=["Frame OCR Job Management"])

# Security
security = HTTPBearer()

# Global job manager instance
job_manager = FrameOCRJobManager()

# Pydantic models for API
class JobStatusEnum(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

class JobPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ProcessingModeEnum(str, Enum):
    PEAK = "peak"
    OFF_PEAK = "off_peak"
    BALANCED = "balanced"

class JobConfigModel(BaseModel):
    sampling_interval: float = Field(default=1.0, ge=0.1, le=10.0)
    max_frames: int = Field(default=1000, ge=1, le=10000)
    ocr_engines: List[str] = Field(default=["tesseract"])
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    languages: List[str] = Field(default=["en"])
    preprocessing_enabled: bool = Field(default=True)

class CreateJobRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=100)
    video_id: str = Field(..., min_length=1, max_length=255)
    video_path: str = Field(..., min_length=1)
    config: JobConfigModel
    priority: JobPriorityEnum = JobPriorityEnum.NORMAL
    scheduled_at: Optional[datetime] = None
    tags: List[str] = Field(default=[])
    dependencies: List[str] = Field(default=[])
    webhook_url: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    tenant_id: str
    video_id: str
    video_path: str
    status: JobStatusEnum
    priority: JobPriorityEnum
    config: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    error_message: Optional[str]
    retry_count: int
    tags: List[str]
    dependencies: List[str]
    webhook_url: Optional[str]
    metrics: Optional[Dict[str, Any]]

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

class JobStatisticsResponse(BaseModel):
    total_jobs: int
    status_counts: Dict[str, int]
    success_rate: float
    running_jobs: int
    queue_size: int

class CostAnalyticsResponse(BaseModel):
    total_cost: float
    job_count: int
    avg_processing_time: float
    cost_per_job: float

class ResourceAllocationModel(BaseModel):
    tenant_id: str
    max_concurrent_jobs: int = Field(default=5, ge=1, le=100)
    cpu_limit: float = Field(default=1.0, ge=0.1, le=32.0)
    memory_limit: int = Field(default=2048, ge=512, le=32768)
    gpu_allocation: float = Field(default=0.0, ge=0.0, le=1.0)
    priority_weight: float = Field(default=1.0, ge=0.1, le=10.0)
    cost_budget: float = Field(default=100.0, ge=0.0)

class RetryConfigModel(BaseModel):
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay: float = Field(default=300.0, ge=1.0, le=3600.0)
    exponential_base: float = Field(default=2.0, ge=1.1, le=5.0)
    jitter: bool = Field(default=True)
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=20)
    circuit_breaker_timeout: float = Field(default=60.0, ge=1.0, le=600.0)

class WebhookPayload(BaseModel):
    job_id: str
    status: JobStatusEnum
    progress: float
    error_message: Optional[str]
    timestamp: datetime

# Dependency for authentication (simplified)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate authentication token"""
    # In a real implementation, validate the JWT token
    # For now, just return a mock user
    return {"user_id": "user_123", "tenant_id": "tenant_1"}

# Helper functions
def convert_job_to_response(job: FrameOCRJob) -> JobResponse:
    """Convert internal job object to API response"""
    return JobResponse(
        job_id=job.job_id,
        tenant_id=job.tenant_id,
        video_id=job.video_id,
        video_path=job.video_path,
        status=JobStatusEnum(job.status.value),
        priority=JobPriorityEnum(job.priority.value),
        config=job.config,
        created_at=job.created_at,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        progress=job.progress,
        error_message=job.error_message,
        retry_count=job.retry_count,
        tags=job.tags,
        dependencies=job.dependencies,
        webhook_url=job.webhook_url,
        metrics=job.metrics.__dict__ if job.metrics else None
    )

# Job Management Endpoints

@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Create a new Frame OCR job"""
    try:
        # Convert priority enum
        priority = JobPriority(request.priority.value.upper())
        
        # Create job
        job = job_manager.create_job(
            tenant_id=request.tenant_id,
            video_id=request.video_id,
            video_path=request.video_path,
            config=request.config.dict(),
            priority=priority,
            scheduled_at=request.scheduled_at,
            tags=request.tags,
            dependencies=request.dependencies,
            webhook_url=request.webhook_url
        )
        
        logger.info(f"Created job {job.job_id} for tenant {request.tenant_id}")
        
        return convert_job_to_response(job)
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get job by ID"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check tenant access
    if job.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return convert_job_to_response(job)

@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    tenant_id: Optional[str] = Query(None),
    status: Optional[JobStatusEnum] = Query(None),
    priority: Optional[JobPriorityEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """List jobs with filtering and pagination"""
    try:
        # Use current user's tenant if not specified
        if not tenant_id:
            tenant_id = current_user.get("tenant_id")
        
        # Check tenant access
        if tenant_id != current_user.get("tenant_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert status enum
        status_filter = None
        if status:
            status_filter = JobStatus(status.value.upper())
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get jobs
        jobs = job_manager.list_jobs(
            tenant_id=tenant_id,
            status=status_filter,
            limit=page_size + 1,  # Get one extra to check if there's a next page
            offset=offset
        )
        
        # Filter by priority if specified
        if priority:
            jobs = [job for job in jobs if job.priority.value == priority.value.upper()]
        
        # Check if there's a next page
        has_next = len(jobs) > page_size
        if has_next:
            jobs = jobs[:-1]  # Remove the extra job
        
        # Convert to response format
        job_responses = [convert_job_to_response(job) for job in jobs]
        
        return JobListResponse(
            jobs=job_responses,
            total=len(job_responses),  # This would be the actual total in a real implementation
            page=page,
            page_size=page_size,
            has_next=has_next
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check tenant access
    if job.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = job_manager.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    return {"message": "Job cancelled successfully"}

@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retry a failed job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check tenant access
    if job.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = job_manager.retry_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be retried")
    
    return {"message": "Job retry initiated"}

@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a running job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check tenant access
    if job.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = job_manager.pause_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be paused")
    
    return {"message": "Job paused successfully"}

@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Resume a paused job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check tenant access
    if job.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = job_manager.resume_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be resumed")
    
    return {"message": "Job resumed successfully"}

# Analytics and Monitoring Endpoints

@router.get("/statistics", response_model=JobStatisticsResponse)
async def get_job_statistics(
    tenant_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get job statistics"""
    # Use current user's tenant if not specified
    if not tenant_id:
        tenant_id = current_user.get("tenant_id")
    
    # Check tenant access
    if tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    stats = job_manager.get_job_statistics(tenant_id)
    
    return JobStatisticsResponse(**stats)

@router.get("/analytics/cost", response_model=CostAnalyticsResponse)
async def get_cost_analytics(
    tenant_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get cost analytics"""
    # Use current user's tenant if not specified
    if not tenant_id:
        tenant_id = current_user.get("tenant_id")
    
    # Check tenant access
    if tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    analytics = job_manager.get_cost_analytics(tenant_id, start_date, end_date)
    
    return CostAnalyticsResponse(**analytics)

# Resource Management Endpoints

@router.post("/resource-allocation")
async def set_resource_allocation(
    allocation: ResourceAllocationModel,
    current_user: dict = Depends(get_current_user)
):
    """Set resource allocation for tenant"""
    # Check tenant access
    if allocation.tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        resource_allocation = ResourceAllocation(
            tenant_id=allocation.tenant_id,
            max_concurrent_jobs=allocation.max_concurrent_jobs,
            cpu_limit=allocation.cpu_limit,
            memory_limit=allocation.memory_limit,
            gpu_allocation=allocation.gpu_allocation,
            priority_weight=allocation.priority_weight,
            cost_budget=allocation.cost_budget
        )
        
        job_manager.set_tenant_allocation(resource_allocation)
        
        return {"message": "Resource allocation updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to set resource allocation: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/retry-config")
async def set_retry_config(
    tenant_id: str,
    config: RetryConfigModel,
    current_user: dict = Depends(get_current_user)
):
    """Set retry configuration for tenant"""
    # Check tenant access
    if tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        retry_config = RetryConfig(
            max_attempts=config.max_attempts,
            base_delay=config.base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter,
            circuit_breaker_threshold=config.circuit_breaker_threshold,
            circuit_breaker_timeout=config.circuit_breaker_timeout
        )
        
        job_manager.set_retry_config(tenant_id, retry_config)
        
        return {"message": "Retry configuration updated successfully"}
        
    except Exception as e:
        logger.error(f"Failed to set retry config: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# System Management Endpoints

@router.post("/optimize-scheduling")
async def optimize_scheduling(
    mode: ProcessingModeEnum,
    current_user: dict = Depends(get_current_user)
):
    """Optimize job scheduling based on processing mode"""
    try:
        processing_mode = ProcessingMode(mode.value.upper())
        job_manager.optimize_scheduling(processing_mode)
        
        return {"message": f"Scheduling optimized for {mode.value} mode"}
        
    except Exception as e:
        logger.error(f"Failed to optimize scheduling: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cleanup")
async def cleanup_old_jobs(
    retention_days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Clean up old completed jobs"""
    try:
        deleted_count = job_manager.cleanup_old_jobs(retention_days)
        
        return {
            "message": f"Cleaned up {deleted_count} old jobs",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Webhook Endpoints

@router.post("/webhooks/test")
async def test_webhook(
    webhook_url: str,
    current_user: dict = Depends(get_current_user)
):
    """Test webhook endpoint"""
    try:
        import requests
        
        test_payload = WebhookPayload(
            job_id="test_job_123",
            status=JobStatusEnum.COMPLETED,
            progress=1.0,
            error_message=None,
            timestamp=datetime.now()
        )
        
        response = requests.post(
            webhook_url,
            json=test_payload.dict(),
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        return {
            "message": "Webhook test completed",
            "status_code": response.status_code,
            "response": response.text[:500]  # Limit response size
        }
        
    except Exception as e:
        logger.error(f"Webhook test failed: {e}")
        raise HTTPException(status_code=400, detail=f"Webhook test failed: {e}")

# Health Check Endpoint

@router.get("/health")
async def health_check():
    """System health check"""
    try:
        stats = job_manager.get_job_statistics()
        
        # Determine system health
        health_status = "healthy"
        if stats['queue_size'] > 100:
            health_status = "degraded"
        if stats['running_jobs'] > 50:
            health_status = "overloaded"
        
        return {
            "status": health_status,
            "timestamp": datetime.now(),
            "queue_size": stats['queue_size'],
            "running_jobs": stats['running_jobs'],
            "success_rate": stats['success_rate']
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }

# Bulk Operations

@router.post("/jobs/bulk/cancel")
async def bulk_cancel_jobs(
    job_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Cancel multiple jobs"""
    results = []
    
    for job_id in job_ids:
        try:
            job = job_manager.get_job(job_id)
            
            if not job:
                results.append({"job_id": job_id, "success": False, "error": "Job not found"})
                continue
            
            # Check tenant access
            if job.tenant_id != current_user.get("tenant_id"):
                results.append({"job_id": job_id, "success": False, "error": "Access denied"})
                continue
            
            success = job_manager.cancel_job(job_id)
            results.append({"job_id": job_id, "success": success})
            
        except Exception as e:
            results.append({"job_id": job_id, "success": False, "error": str(e)})
    
    successful_count = sum(1 for r in results if r["success"])
    
    return {
        "message": f"Cancelled {successful_count}/{len(job_ids)} jobs",
        "results": results
    }

@router.post("/jobs/bulk/retry")
async def bulk_retry_jobs(
    job_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """Retry multiple failed jobs"""
    results = []
    
    for job_id in job_ids:
        try:
            job = job_manager.get_job(job_id)
            
            if not job:
                results.append({"job_id": job_id, "success": False, "error": "Job not found"})
                continue
            
            # Check tenant access
            if job.tenant_id != current_user.get("tenant_id"):
                results.append({"job_id": job_id, "success": False, "error": "Access denied"})
                continue
            
            success = job_manager.retry_job(job_id)
            results.append({"job_id": job_id, "success": success})
            
        except Exception as e:
            results.append({"job_id": job_id, "success": False, "error": str(e)})
    
    successful_count = sum(1 for r in results if r["success"])
    
    return {
        "message": f"Retried {successful_count}/{len(job_ids)} jobs",
        "results": results
    }

# Export job data
@router.get("/jobs/export")
async def export_jobs(
    tenant_id: Optional[str] = Query(None),
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Export job data"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Use current user's tenant if not specified
    if not tenant_id:
        tenant_id = current_user.get("tenant_id")
    
    # Check tenant access
    if tenant_id != current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get jobs (simplified - would need proper date filtering)
        jobs = job_manager.list_jobs(tenant_id, limit=10000)
        
        if format == "json":
            import json
            
            job_data = [convert_job_to_response(job).dict() for job in jobs]
            json_str = json.dumps(job_data, indent=2, default=str)
            
            return StreamingResponse(
                io.StringIO(json_str),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=jobs_{tenant_id}.json"}
            )
        
        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "job_id", "tenant_id", "video_id", "status", "priority",
                "progress", "created_at", "started_at", "completed_at",
                "error_message", "retry_count"
            ])
            
            # Write data
            for job in jobs:
                writer.writerow([
                    job.job_id, job.tenant_id, job.video_id, job.status.value,
                    job.priority.value, job.progress, job.created_at,
                    job.started_at, job.completed_at, job.error_message,
                    job.retry_count
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=jobs_{tenant_id}.csv"}
            )
    
    except Exception as e:
        logger.error(f"Failed to export jobs: {e}")
        raise HTTPException(status_code=400, detail=str(e))