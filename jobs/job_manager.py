"""
Job management system for background tasks
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
import traceback

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(Enum):
    """Job type enumeration"""
    EXPORT = "export"
    MEDIA_PROCESSING = "media_processing"
    NOTIFICATION = "notification"
    CLEANUP = "cleanup"
    EMAIL = "email"
    ANALYSIS = "analysis"
    BACKUP = "backup"


@dataclass
class Job:
    """Represents a background job"""
    id: str
    type: JobType
    status: JobStatus
    data: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    max_retries: int = 3
    retry_count: int = 0
    priority: int = 0  # Higher number = higher priority
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'status': self.status.value,
            'data': self.data,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'max_retries': self.max_retries,
            'retry_count': self.retry_count,
            'priority': self.priority,
            'user_id': self.user_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        job = cls(
            id=data['id'],
            type=JobType(data['type']),
            status=JobStatus(data['status']),
            data=data['data'],
            result=data.get('result'),
            error=data.get('error'),
            created_at=datetime.fromisoformat(data['created_at']),
            progress=data.get('progress', 0),
            max_retries=data.get('max_retries', 3),
            retry_count=data.get('retry_count', 0),
            priority=data.get('priority', 0),
            user_id=data.get('user_id'),
            metadata=data.get('metadata', {})
        )
        
        if data.get('started_at'):
            job.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            job.completed_at = datetime.fromisoformat(data['completed_at'])
            
        return job
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get job duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.utcnow() - self.started_at
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == JobStatus.FAILED and self.retry_count < self.max_retries


class JobManager:
    """Manages background jobs"""
    
    def __init__(self):
        # In-memory job storage (in production, use Redis or database)
        self.jobs: Dict[str, Job] = {}
        self.task_handlers: Dict[JobType, Callable] = {}
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.max_workers = 5
        self.job_queue = asyncio.Queue()
        self.progress_callbacks: Dict[str, Callable] = {}
        
    def register_handler(self, job_type: JobType, handler: Callable):
        """Register a handler for a job type"""
        self.task_handlers[job_type] = handler
        logger.info(f"Registered handler for {job_type.value}")
    
    def create_job(
        self,
        job_type: JobType,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        priority: int = 0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """Create a new job"""
        job = Job(
            id=str(uuid.uuid4()),
            type=job_type,
            status=JobStatus.PENDING,
            data=data,
            user_id=user_id,
            priority=priority,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        self.jobs[job.id] = job
        logger.info(f"Created job {job.id} of type {job_type.value}")
        
        return job
    
    async def enqueue_job(self, job: Job):
        """Add job to queue"""
        await self.job_queue.put(job)
        logger.info(f"Enqueued job {job.id}")
    
    async def submit_job(
        self,
        job_type: JobType,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        priority: int = 0,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and submit a job"""
        job = self.create_job(job_type, data, user_id, priority, max_retries, metadata)
        await self.enqueue_job(job)
        return job.id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(
        self,
        user_id: Optional[int] = None,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 100
    ) -> List[Job]:
        """List jobs with filters"""
        jobs = list(self.jobs.values())
        
        # Apply filters
        if user_id is not None:
            jobs = [job for job in jobs if job.user_id == user_id]
        
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        
        if job_type is not None:
            jobs = [job for job in jobs if job.type == job_type]
        
        # Sort by created_at desc
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            logger.info(f"Cancelled job {job_id}")
            return True
        
        return False
    
    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job"""
        job = self.get_job(job_id)
        if not job or not job.can_retry():
            return False
        
        job.status = JobStatus.PENDING
        job.error = None
        job.retry_count += 1
        job.progress = 0
        
        await self.enqueue_job(job)
        logger.info(f"Retrying job {job_id} (attempt {job.retry_count + 1})")
        return True
    
    def register_progress_callback(self, job_id: str, callback: Callable):
        """Register progress callback for a job"""
        self.progress_callbacks[job_id] = callback
    
    async def update_progress(self, job_id: str, progress: int, message: str = ""):
        """Update job progress"""
        job = self.get_job(job_id)
        if job:
            job.progress = progress
            if message:
                job.metadata['last_message'] = message
            
            # Call progress callback if registered
            callback = self.progress_callbacks.get(job_id)
            if callback:
                try:
                    await callback(job, progress, message)
                except Exception as e:
                    logger.error(f"Progress callback error for job {job_id}: {e}")
    
    async def start_workers(self):
        """Start background workers"""
        if self.running:
            return
        
        self.running = True
        logger.info(f"Starting {self.max_workers} job workers")
        
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker_task)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_completed_jobs())
        self.workers.append(cleanup_task)
    
    async def stop_workers(self):
        """Stop background workers"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping job workers")
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
    
    async def _worker(self, worker_name: str):
        """Background worker to process jobs"""
        logger.info(f"Worker {worker_name} started")
        
        while self.running:
            try:
                # Get job from queue (wait up to 1 second)
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Process job
                await self._process_job(job, worker_name)
                
            except asyncio.TimeoutError:
                # No job available, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_job(self, job: Job, worker_name: str):
        """Process a single job"""
        logger.info(f"Worker {worker_name} processing job {job.id} ({job.type.value})")
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.progress = 0
        
        try:
            # Get handler
            handler = self.task_handlers.get(job.type)
            if not handler:
                raise Exception(f"No handler registered for job type {job.type.value}")
            
            # Execute handler
            result = await handler(job, self)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.utcnow()
            job.progress = 100
            
            logger.info(f"Job {job.id} completed successfully")
            
        except Exception as e:
            # Job failed
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            
            logger.error(f"Job {job.id} failed: {e}")
            logger.debug(traceback.format_exc())
            
            # Auto-retry if possible
            if job.can_retry():
                logger.info(f"Auto-retrying job {job.id} (attempt {job.retry_count + 1})")
                await asyncio.sleep(2 ** job.retry_count)  # Exponential backoff
                await self.retry_job(job.id)
    
    async def _cleanup_completed_jobs(self):
        """Cleanup old completed jobs"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                jobs_to_remove = []
                
                for job_id, job in self.jobs.items():
                    if (job.is_finished and 
                        job.completed_at and 
                        job.completed_at < cutoff_time):
                        jobs_to_remove.append(job_id)
                
                for job_id in jobs_to_remove:
                    del self.jobs[job_id]
                    self.progress_callbacks.pop(job_id, None)
                
                if jobs_to_remove:
                    logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
                    
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get job queue statistics"""
        status_counts = {}
        type_counts = {}
        
        for job in self.jobs.values():
            # Count by status
            status = job.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by type
            job_type = job.type.value
            type_counts[job_type] = type_counts.get(job_type, 0) + 1
        
        return {
            'total_jobs': len(self.jobs),
            'queue_size': self.job_queue.qsize(),
            'workers_running': len(self.workers),
            'status_counts': status_counts,
            'type_counts': type_counts,
            'running': self.running
        }


# Global job manager instance
job_manager = JobManager()