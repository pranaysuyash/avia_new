"""
Distributed Processing API Endpoints
FastAPI endpoints for managing distributed job processing
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import json
import uuid

from ...distributed_processing_system import (
    DistributedProcessingOrchestrator,
    JobPriority,
    JobStatus,
    Job,
    Worker,
    WorkerPool
)
from ...advanced_caching_optimization import AdvancedCachingSystem
from ..auth import get_current_user
from ..models import User
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/distributed", tags=["distributed-processing"])

# Initialize systems
orchestrator = DistributedProcessingOrchestrator()
cache_system = AdvancedCachingSystem()

# Pydantic models
class JobSubmissionRequest(BaseModel):
    task_name: str
    payload: Dict[str, Any]
    priority: Optional[str] = "NORMAL"
    timeout: Optional[int] = Field(default=300, ge=1, le=3600)
    max_retries: Optional[int] = Field(default=3, ge=0, le=10)

class WorkerRegistrationRequest(BaseModel):
    hostname: str
    ip_address: str
    cpu_count: int
    memory_gb: float
    capabilities: List[str] = []

class ScalingRequest(BaseModel):
    min_workers: int = Field(ge=1, le=100)
    max_workers: int = Field(ge=1, le=1000)
    target_utilization: float = Field(ge=0.1, le=1.0)

class CacheConfigRequest(BaseModel):
    tier: str = "L1_MEMORY"
    ttl: Optional[int] = 3600
    compression_enabled: bool = True
    auto_warmup: bool = False

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float]
    result: Optional[Any]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    worker_id: Optional[str]

class QueueStatusResponse(BaseModel):
    queues: Dict[str, int]
    total_pending: int
    total_running: int
    total_completed: int
    total_failed: int

class WorkerStatusResponse(BaseModel):
    worker_id: str
    hostname: str
    status: str
    current_job: Optional[str]
    jobs_completed: int
    jobs_failed: int
    load_average: float
    last_heartbeat: str

class SystemMetricsResponse(BaseModel):
    jobs_submitted: int
    jobs_completed: int
    jobs_failed: int
    avg_processing_time: float
    queue_sizes: Dict[str, int]
    active_workers: int
    idle_workers: int
    cache_hit_rate: float
    memory_usage_mb: float

@router.post("/submit-job", response_model=JobResponse)
async def submit_job(
    request: JobSubmissionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a job for distributed processing"""
    try:
        # Convert priority string to enum
        priority = JobPriority[request.priority]
        
        # Submit job to orchestrator
        job_id = await orchestrator.submit_job(
            task_name=request.task_name,
            payload=request.payload,
            priority=priority
        )
        
        # Start processing in background if not already running
        background_tasks.add_task(process_jobs_background)
        
        return JobResponse(
            job_id=job_id,
            status="submitted",
            created_at=datetime.now().isoformat(),
            message=f"Job submitted successfully with priority {request.priority}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of a specific job"""
    try:
        status = orchestrator.get_job_status(job_id)
        
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(
            job_id=job_id,
            status=status.get("status", "unknown"),
            progress=None,  # Could be calculated based on task
            result=None,  # Would need to fetch from result backend
            error=status.get("error"),
            created_at=status.get("created_at", ""),
            started_at=status.get("started_at"),
            completed_at=status.get("completed_at"),
            worker_id=status.get("worker_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/job/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a pending or running job"""
    try:
        # Update job status to cancelled
        orchestrator.redis.hset(
            f"job:{job_id}",
            "status", JobStatus.CANCELLED.value
        )
        
        return {"message": f"Job {job_id} cancelled"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(
    current_user: User = Depends(get_current_user)
):
    """Get current queue status"""
    try:
        queue_sizes = await orchestrator.queue.get_queue_size()
        
        # Get job counts from Redis
        all_jobs = orchestrator.redis.keys("job:*")
        statuses = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        
        for job_key in all_jobs:
            status = orchestrator.redis.hget(job_key, "status")
            if status:
                status_str = status.decode()
                if status_str in statuses:
                    statuses[status_str] += 1
        
        return QueueStatusResponse(
            queues=queue_sizes,
            total_pending=statuses["pending"],
            total_running=statuses["running"],
            total_completed=statuses["completed"],
            total_failed=statuses["failed"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/worker/register", response_model=Dict[str, str])
async def register_worker(
    request: WorkerRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """Register a new worker node"""
    try:
        worker_id = str(uuid.uuid4())
        
        worker = Worker(
            worker_id=worker_id,
            hostname=request.hostname,
            ip_address=request.ip_address,
            cpu_count=request.cpu_count,
            memory_gb=request.memory_gb,
            capabilities=request.capabilities
        )
        
        orchestrator.worker_pool.register_worker(worker)
        
        return {
            "worker_id": worker_id,
            "status": "registered",
            "message": f"Worker registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/worker/{worker_id}/unregister")
async def unregister_worker(
    worker_id: str,
    current_user: User = Depends(get_current_user)
):
    """Unregister a worker node"""
    try:
        orchestrator.worker_pool.unregister_worker(worker_id)
        
        return {"message": f"Worker {worker_id} unregistered"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workers/status", response_model=List[WorkerStatusResponse])
async def get_workers_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all workers"""
    try:
        workers = []
        
        for worker in orchestrator.worker_pool.workers.values():
            workers.append(WorkerStatusResponse(
                worker_id=worker.worker_id,
                hostname=worker.hostname,
                status=worker.status,
                current_job=worker.current_job,
                jobs_completed=worker.jobs_completed,
                jobs_failed=worker.jobs_failed,
                load_average=worker.load_average,
                last_heartbeat=worker.last_heartbeat.isoformat()
            ))
        
        return workers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scaling/configure")
async def configure_scaling(
    request: ScalingRequest,
    current_user: User = Depends(get_current_user)
):
    """Configure auto-scaling parameters"""
    try:
        # This would configure Kubernetes HPA or other scaling mechanisms
        if orchestrator.k8s_scaler:
            orchestrator.k8s_scaler.auto_scale(
                namespace="default",
                deployment_name="worker-deployment",
                min_replicas=request.min_workers,
                max_replicas=request.max_workers,
                target_cpu_percent=int(request.target_utilization * 100)
            )
        
        return {
            "message": "Scaling configuration updated",
            "min_workers": request.min_workers,
            "max_workers": request.max_workers,
            "target_utilization": request.target_utilization
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get system-wide metrics"""
    try:
        # Get orchestrator stats
        orchestrator_stats = orchestrator.stats
        
        # Get queue sizes
        queue_sizes = await orchestrator.queue.get_queue_size()
        
        # Get worker stats
        active_workers = len([w for w in orchestrator.worker_pool.workers.values() if w.status == "busy"])
        idle_workers = len([w for w in orchestrator.worker_pool.workers.values() if w.status == "idle"])
        
        # Get cache stats
        cache_stats = cache_system.get_stats()
        
        return SystemMetricsResponse(
            jobs_submitted=orchestrator_stats["jobs_submitted"],
            jobs_completed=orchestrator_stats["jobs_completed"],
            jobs_failed=orchestrator_stats["jobs_failed"],
            avg_processing_time=orchestrator_stats.get("avg_processing_time", 0),
            queue_sizes=queue_sizes,
            active_workers=active_workers,
            idle_workers=idle_workers,
            cache_hit_rate=cache_stats["hit_rate"],
            memory_usage_mb=cache_stats["memory_usage_mb"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/configure")
async def configure_cache(
    request: CacheConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Configure caching parameters"""
    try:
        # Configure cache settings
        if request.compression_enabled:
            cache_system.compression_threshold = 1024
        else:
            cache_system.compression_threshold = float('inf')
        
        cache_system.optimization_enabled = request.auto_warmup
        
        return {
            "message": "Cache configuration updated",
            "tier": request.tier,
            "ttl": request.ttl,
            "compression_enabled": request.compression_enabled,
            "auto_warmup": request.auto_warmup
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Clear cache entries"""
    try:
        if pattern:
            await cache_system.invalidate_pattern(pattern)
            message = f"Cleared cache entries matching pattern: {pattern}"
        else:
            cache_system.l1_cache.clear()
            message = "Cleared all cache entries"
        
        return {"message": message}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """Get cache statistics"""
    try:
        stats = cache_system.get_stats()
        
        return {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "hit_rate": stats["hit_rate"],
            "evictions": stats["evictions"],
            "total_requests": stats["total_requests"],
            "avg_response_time_ms": stats["avg_response_time_ms"],
            "memory_usage_mb": stats["memory_usage_mb"],
            "l1_cache_size": stats["l1_cache_size"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/monitor")
async def monitor_system(websocket: WebSocket):
    """WebSocket endpoint for real-time system monitoring"""
    await websocket.accept()
    
    try:
        while True:
            # Gather metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "queue_sizes": await orchestrator.queue.get_queue_size(),
                "active_workers": len([w for w in orchestrator.worker_pool.workers.values() if w.status == "busy"]),
                "idle_workers": len([w for w in orchestrator.worker_pool.workers.values() if w.status == "idle"]),
                "cache_stats": cache_system.get_stats()
            }
            
            # Send metrics
            await websocket.send_json(metrics)
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()

# Background task to process jobs
async def process_jobs_background():
    """Background task to process jobs"""
    try:
        # This would typically be handled by Celery workers or similar
        await orchestrator.process_jobs()
    except Exception as e:
        logger.error(f"Error processing jobs: {e}")

# Startup event to initialize monitoring
@router.on_event("startup")
async def startup_monitoring():
    """Start monitoring tasks on startup"""
    asyncio.create_task(orchestrator.monitor_and_scale())

# Cleanup on shutdown
@router.on_event("shutdown")
async def shutdown_cleanup():
    """Cleanup on shutdown"""
    await orchestrator.shutdown()