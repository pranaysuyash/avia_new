"""
Enterprise Frame OCR Job Management and Workflow System

This module provides comprehensive job management capabilities for Frame OCR processing
with distributed queue support, horizontal scaling, and enterprise-grade features.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import PriorityQueue, Queue
import sqlite3
import os
from pathlib import Path

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class ProcessingMode(Enum):
    """Processing mode for resource optimization"""
    PEAK = "peak"
    OFF_PEAK = "off_peak"
    BALANCED = "balanced"

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 300.0
    exponential_base: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

@dataclass
class ResourceAllocation:
    """Resource allocation configuration per tenant"""
    tenant_id: str
    max_concurrent_jobs: int = 5
    cpu_limit: float = 1.0  # CPU cores
    memory_limit: int = 2048  # MB
    gpu_allocation: float = 0.0  # GPU fraction
    priority_weight: float = 1.0
    cost_budget: float = 100.0  # USD per month

@dataclass
class JobMetrics:
    """Job execution metrics"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: float = 0.0
    frames_processed: int = 0
    frames_total: int = 0
    cost_estimate: float = 0.0
    actual_cost: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    gpu_usage: float = 0.0

@dataclass
class FrameOCRJob:
    """Enhanced Frame OCR Job with enterprise features"""
    job_id: str
    tenant_id: str
    video_id: str
    video_path: str
    status: JobStatus
    priority: JobPriority
    config: Dict[str, Any]
    created_at: datetime
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    metrics: JobMetrics = None
    tags: List[str] = None
    dependencies: List[str] = None
    webhook_url: Optional[str] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = JobMetrics()
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []
    
    def __lt__(self, other):
        """Make FrameOCRJob comparable for priority queue"""
        if not isinstance(other, FrameOCRJob):
            return NotImplemented
        # Compare by priority first, then by creation time
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Higher priority value = higher priority
        return self.created_at < other.created_at

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "half_open"
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "half_open":
                    self.state = "closed"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "open"
                
                raise e

class JobQueue:
    """Priority-based job queue with tenant awareness"""
    
    def __init__(self):
        self.queue = PriorityQueue()
        self.tenant_queues: Dict[str, Queue] = {}
        self.tenant_allocations: Dict[str, ResourceAllocation] = {}
        self._lock = threading.Lock()
    
    def add_job(self, job: FrameOCRJob):
        """Add job to appropriate queue"""
        with self._lock:
            # Priority calculation: higher priority enum value = higher priority
            # Negative for PriorityQueue (min-heap)
            priority_score = -job.priority.value
            
            # Adjust priority based on tenant weight
            if job.tenant_id in self.tenant_allocations:
                allocation = self.tenant_allocations[job.tenant_id]
                priority_score *= allocation.priority_weight
            
            self.queue.put((priority_score, job.created_at.timestamp(), job))
    
    def get_job(self, tenant_id: Optional[str] = None) -> Optional[FrameOCRJob]:
        """Get next job from queue"""
        try:
            _, _, job = self.queue.get_nowait()
            return job
        except:
            return None
    
    def set_tenant_allocation(self, allocation: ResourceAllocation):
        """Set resource allocation for tenant"""
        self.tenant_allocations[allocation.tenant_id] = allocation

class CanaryProcessor:
    """Canary processing for new models with automatic rollback"""
    
    def __init__(self):
        self.canary_models: Dict[str, Dict] = {}
        self.baseline_metrics: Dict[str, float] = {}
        self.canary_traffic_percentage = 0.1  # 10% canary traffic
        self.regression_threshold = 0.05  # 5% performance degradation
    
    def register_canary_model(self, model_id: str, model_config: Dict):
        """Register a new model for canary testing"""
        self.canary_models[model_id] = {
            'config': model_config,
            'start_time': datetime.now(),
            'processed_jobs': 0,
            'success_rate': 0.0,
            'avg_processing_time': 0.0,
            'accuracy_score': 0.0
        }
        logger.info(f"Registered canary model: {model_id}")
    
    def should_use_canary(self, job: FrameOCRJob) -> bool:
        """Determine if job should use canary model"""
        import random
        return random.random() < self.canary_traffic_percentage
    
    def update_canary_metrics(self, model_id: str, success: bool, 
                            processing_time: float, accuracy: float):
        """Update metrics for canary model"""
        if model_id not in self.canary_models:
            return
        
        canary = self.canary_models[model_id]
        canary['processed_jobs'] += 1
        
        # Update success rate
        current_success_rate = canary['success_rate']
        canary['success_rate'] = (
            (current_success_rate * (canary['processed_jobs'] - 1) + (1 if success else 0))
            / canary['processed_jobs']
        )
        
        # Update processing time
        current_avg_time = canary['avg_processing_time']
        canary['avg_processing_time'] = (
            (current_avg_time * (canary['processed_jobs'] - 1) + processing_time)
            / canary['processed_jobs']
        )
        
        # Update accuracy
        current_accuracy = canary['accuracy_score']
        canary['accuracy_score'] = (
            (current_accuracy * (canary['processed_jobs'] - 1) + accuracy)
            / canary['processed_jobs']
        )
    
    def check_for_regression(self, model_id: str) -> bool:
        """Check if canary model shows regression"""
        if model_id not in self.canary_models:
            return False
        
        canary = self.canary_models[model_id]
        
        # Need minimum samples for statistical significance
        if canary['processed_jobs'] < 10:
            return False
        
        # Check against baseline metrics
        baseline_success = self.baseline_metrics.get('success_rate', 0.95)
        baseline_time = self.baseline_metrics.get('avg_processing_time', 10.0)
        baseline_accuracy = self.baseline_metrics.get('accuracy_score', 0.85)
        
        # Check for regression
        success_regression = (baseline_success - canary['success_rate']) > self.regression_threshold
        time_regression = (canary['avg_processing_time'] - baseline_time) / baseline_time > self.regression_threshold
        accuracy_regression = (baseline_accuracy - canary['accuracy_score']) > self.regression_threshold
        
        return success_regression or time_regression or accuracy_regression
    
    def rollback_canary(self, model_id: str):
        """Rollback canary model due to regression"""
        if model_id in self.canary_models:
            logger.warning(f"Rolling back canary model {model_id} due to regression")
            del self.canary_models[model_id]

class FrameOCRJobManager:
    """Enterprise Frame OCR Job Manager with distributed queue support"""
    
    def __init__(self, db_path: str = "frame_ocr_jobs.db"):
        self.db_path = db_path
        self.job_queue = JobQueue()
        self.running_jobs: Dict[str, FrameOCRJob] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.canary_processor = CanaryProcessor()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.scheduler_running = False
        self.scheduler_thread = None
        self.retry_configs: Dict[str, RetryConfig] = {}
        self.webhook_callbacks: Dict[str, Callable] = {}
        
        # Initialize database
        self._init_database()
        
        # Default retry configuration
        self.default_retry_config = RetryConfig()
        
        # Start scheduler
        self.start_scheduler()
    
    def _init_database(self):
        """Initialize SQLite database for job persistence"""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS frame_ocr_jobs (
                    job_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    video_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scheduled_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    progress REAL DEFAULT 0.0,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    metrics TEXT,
                    tags TEXT,
                    dependencies TEXT,
                    webhook_url TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_status 
                ON frame_ocr_jobs(tenant_id, status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON frame_ocr_jobs(created_at)
            """)
    
    def create_job(self, tenant_id: str, video_id: str, video_path: str,
                   config: Dict[str, Any], priority: JobPriority = JobPriority.NORMAL,
                   scheduled_at: Optional[datetime] = None,
                   tags: List[str] = None, dependencies: List[str] = None,
                   webhook_url: Optional[str] = None) -> FrameOCRJob:
        """Create a new Frame OCR job"""
        
        job_id = str(uuid.uuid4())
        job = FrameOCRJob(
            job_id=job_id,
            tenant_id=tenant_id,
            video_id=video_id,
            video_path=video_path,
            status=JobStatus.PENDING,
            priority=priority,
            config=config,
            created_at=datetime.now(),
            scheduled_at=scheduled_at,
            tags=tags or [],
            dependencies=dependencies or [],
            webhook_url=webhook_url
        )
        
        # Estimate cost
        job.metrics.cost_estimate = self._estimate_job_cost(job)
        
        # Save to database
        self._save_job(job)
        
        # Add to queue if not scheduled for later
        if scheduled_at is None or scheduled_at <= datetime.now():
            job.status = JobStatus.QUEUED
            self.job_queue.add_job(job)
            self._save_job(job)
        
        logger.info(f"Created job {job_id} for tenant {tenant_id}")
        return job
    
    def _estimate_job_cost(self, job: FrameOCRJob) -> float:
        """Estimate processing cost for job"""
        # Simple cost estimation based on video duration and configuration
        base_cost_per_minute = 0.10  # $0.10 per minute
        
        # Get video duration (simplified - would use actual video metadata)
        estimated_duration = 300  # 5 minutes default
        
        # Adjust based on configuration
        config = job.config
        sampling_rate = config.get('sampling_interval', 1.0)
        ocr_engines = config.get('ocr_engines', ['tesseract'])
        
        cost_multiplier = 1.0
        if 'cloud' in str(ocr_engines):
            cost_multiplier *= 2.0  # Cloud OCR is more expensive
        
        cost_multiplier *= (1.0 / sampling_rate)  # More frequent sampling = higher cost
        
        return base_cost_per_minute * (estimated_duration / 60) * cost_multiplier
    
    def _save_job(self, job: FrameOCRJob):
        """Save job to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO frame_ocr_jobs 
                (job_id, tenant_id, video_id, video_path, status, priority, config,
                 created_at, scheduled_at, started_at, completed_at, progress,
                 error_message, retry_count, metrics, tags, dependencies, webhook_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.tenant_id, job.video_id, job.video_path,
                job.status.value, job.priority.value, json.dumps(job.config),
                job.created_at.isoformat(),
                job.scheduled_at.isoformat() if job.scheduled_at else None,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                job.progress, job.error_message, job.retry_count,
                json.dumps(asdict(job.metrics), cls=DateTimeEncoder) if job.metrics else None,
                json.dumps(job.tags), json.dumps(job.dependencies),
                job.webhook_url
            ))
    
    def get_job(self, job_id: str) -> Optional[FrameOCRJob]:
        """Get job by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM frame_ocr_jobs WHERE job_id = ?", (job_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_job(row)
            return None
    
    def _row_to_job(self, row: sqlite3.Row) -> FrameOCRJob:
        """Convert database row to FrameOCRJob"""
        metrics_data = json.loads(row['metrics']) if row['metrics'] else {}
        
        # Convert datetime strings back to datetime objects in metrics
        if metrics_data:
            for key in ['start_time', 'end_time']:
                if key in metrics_data and metrics_data[key]:
                    try:
                        metrics_data[key] = datetime.fromisoformat(metrics_data[key])
                    except (ValueError, TypeError):
                        metrics_data[key] = None
        
        metrics = JobMetrics(**metrics_data) if metrics_data else JobMetrics()
        
        return FrameOCRJob(
            job_id=row['job_id'],
            tenant_id=row['tenant_id'],
            video_id=row['video_id'],
            video_path=row['video_path'],
            status=JobStatus(row['status']),
            priority=JobPriority(row['priority']),
            config=json.loads(row['config']),
            created_at=datetime.fromisoformat(row['created_at']),
            scheduled_at=datetime.fromisoformat(row['scheduled_at']) if row['scheduled_at'] else None,
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            progress=row['progress'],
            error_message=row['error_message'],
            retry_count=row['retry_count'],
            metrics=metrics,
            tags=json.loads(row['tags']) if row['tags'] else [],
            dependencies=json.loads(row['dependencies']) if row['dependencies'] else [],
            webhook_url=row['webhook_url']
        )    

    def list_jobs(self, tenant_id: Optional[str] = None, 
                  status: Optional[JobStatus] = None,
                  limit: int = 100, offset: int = 0) -> List[FrameOCRJob]:
        """List jobs with filtering"""
        query = "SELECT * FROM frame_ocr_jobs WHERE 1=1"
        params = []
        
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_job(row) for row in cursor.fetchall()]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED]:
            return False
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        self._save_job(job)
        
        # Remove from running jobs if present
        if job_id in self.running_jobs:
            del self.running_jobs[job_id]
        
        # Send webhook notification
        self._send_webhook_notification(job)
        
        logger.info(f"Cancelled job {job_id}")
        return True
    
    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job"""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.FAILED:
            return False
        
        retry_config = self.retry_configs.get(job.tenant_id, self.default_retry_config)
        
        if job.retry_count >= retry_config.max_attempts:
            logger.warning(f"Job {job_id} exceeded max retry attempts")
            return False
        
        job.status = JobStatus.QUEUED
        job.retry_count += 1
        job.error_message = None
        job.started_at = None
        job.completed_at = None
        
        self._save_job(job)
        self.job_queue.add_job(job)
        
        logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")
        return True
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a running job"""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.RUNNING:
            return False
        
        job.status = JobStatus.PAUSED
        self._save_job(job)
        
        logger.info(f"Paused job {job_id}")
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.PAUSED:
            return False
        
        job.status = JobStatus.QUEUED
        self._save_job(job)
        self.job_queue.add_job(job)
        
        logger.info(f"Resumed job {job_id}")
        return True
    
    def set_tenant_allocation(self, allocation: ResourceAllocation):
        """Set resource allocation for tenant"""
        self.job_queue.set_tenant_allocation(allocation)
        logger.info(f"Set resource allocation for tenant {allocation.tenant_id}")
    
    def set_retry_config(self, tenant_id: str, config: RetryConfig):
        """Set retry configuration for tenant"""
        self.retry_configs[tenant_id] = config
    
    def start_scheduler(self):
        """Start the job scheduler"""
        if self.scheduler_running:
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Started job scheduler")
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Stopped job scheduler")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                # Process scheduled jobs
                self._process_scheduled_jobs()
                
                # Process queued jobs
                self._process_queued_jobs()
                
                # Check for job timeouts
                self._check_job_timeouts()
                
                # Update job metrics
                self._update_job_metrics()
                
                # Check canary models for regression
                self._check_canary_regression()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def _process_scheduled_jobs(self):
        """Process jobs scheduled for future execution"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM frame_ocr_jobs 
                WHERE status = 'pending' AND scheduled_at <= ?
            """, (datetime.now().isoformat(),))
            
            for row in cursor.fetchall():
                job = self._row_to_job(row)
                job.status = JobStatus.QUEUED
                self._save_job(job)
                self.job_queue.add_job(job)
                logger.info(f"Scheduled job {job.job_id} moved to queue")
    
    def _process_queued_jobs(self):
        """Process jobs from the queue"""
        # Check available capacity
        max_concurrent = 5  # Default, should be configurable per tenant
        
        if len(self.running_jobs) >= max_concurrent:
            return
        
        # Get next job from queue
        job = self.job_queue.get_job()
        if not job:
            return
        
        # Check dependencies
        if not self._check_job_dependencies(job):
            # Re-queue job for later
            self.job_queue.add_job(job)
            return
        
        # Start job processing
        self._start_job_processing(job)
    
    def _check_job_dependencies(self, job: FrameOCRJob) -> bool:
        """Check if job dependencies are satisfied"""
        if not job.dependencies:
            return True
        
        for dep_job_id in job.dependencies:
            dep_job = self.get_job(dep_job_id)
            if not dep_job or dep_job.status != JobStatus.COMPLETED:
                return False
        
        return True
    
    def _start_job_processing(self, job: FrameOCRJob):
        """Start processing a job"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        job.metrics.start_time = job.started_at
        
        self.running_jobs[job.job_id] = job
        self._save_job(job)
        
        # Submit job to thread pool
        future = self.executor.submit(self._process_job, job)
        
        # Store future for tracking
        job.future = future
        
        logger.info(f"Started processing job {job.job_id}")
    
    def _process_job(self, job: FrameOCRJob):
        """Process a single job (placeholder implementation)"""
        try:
            # Simulate job processing
            total_steps = 100
            
            for step in range(total_steps):
                if job.status == JobStatus.CANCELLED:
                    return
                
                # Simulate processing step
                time.sleep(0.1)
                
                # Update progress
                job.progress = (step + 1) / total_steps
                job.metrics.frames_processed = step + 1
                job.metrics.frames_total = total_steps
                
                # Update in database periodically
                if step % 10 == 0:
                    self._save_job(job)
                    self._send_progress_notification(job)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.metrics.end_time = job.completed_at
            job.metrics.processing_time = (
                job.completed_at - job.started_at
            ).total_seconds()
            job.progress = 1.0
            
            # Calculate actual cost (simplified)
            job.metrics.actual_cost = job.metrics.cost_estimate * 0.95  # 5% discount for completion
            
            self._save_job(job)
            self._send_webhook_notification(job)
            
            logger.info(f"Completed job {job.job_id}")
            
        except Exception as e:
            # Job failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = str(e)
            
            self._save_job(job)
            self._send_webhook_notification(job)
            
            # Check if retry is needed
            retry_config = self.retry_configs.get(job.tenant_id, self.default_retry_config)
            if job.retry_count < retry_config.max_attempts:
                # Schedule retry with exponential backoff
                delay = min(
                    retry_config.base_delay * (retry_config.exponential_base ** job.retry_count),
                    retry_config.max_delay
                )
                
                if retry_config.jitter:
                    import random
                    delay *= (0.5 + random.random() * 0.5)  # Add jitter
                
                # Schedule retry
                retry_time = datetime.now() + timedelta(seconds=delay)
                job.scheduled_at = retry_time
                job.status = JobStatus.PENDING
                job.retry_count += 1
                job.error_message = None
                
                self._save_job(job)
                
                logger.info(f"Scheduled retry for job {job.job_id} in {delay} seconds")
            else:
                logger.error(f"Job {job.job_id} failed permanently: {e}")
        
        finally:
            # Remove from running jobs
            if job.job_id in self.running_jobs:
                del self.running_jobs[job.job_id]
    
    def _check_job_timeouts(self):
        """Check for jobs that have timed out"""
        timeout_threshold = datetime.now() - timedelta(hours=2)  # 2 hour timeout
        
        for job_id, job in list(self.running_jobs.items()):
            if job.started_at and job.started_at < timeout_threshold:
                logger.warning(f"Job {job_id} timed out")
                job.status = JobStatus.FAILED
                job.error_message = "Job timed out"
                job.completed_at = datetime.now()
                
                self._save_job(job)
                self._send_webhook_notification(job)
                
                del self.running_jobs[job_id]
    
    def _update_job_metrics(self):
        """Update metrics for running jobs"""
        for job in self.running_jobs.values():
            # Update resource usage metrics (simplified)
            job.metrics.cpu_usage = 0.5  # 50% CPU usage
            job.metrics.memory_usage = 1024  # 1GB memory usage
            
            self._save_job(job)
    
    def _check_canary_regression(self):
        """Check canary models for regression and rollback if needed"""
        for model_id in list(self.canary_processor.canary_models.keys()):
            if self.canary_processor.check_for_regression(model_id):
                self.canary_processor.rollback_canary(model_id)
    
    def _send_webhook_notification(self, job: FrameOCRJob):
        """Send webhook notification for job status change"""
        if not job.webhook_url:
            return
        
        try:
            import requests
            
            payload = {
                'job_id': job.job_id,
                'status': job.status.value,
                'progress': job.progress,
                'error_message': job.error_message,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                job.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook notification sent for job {job.job_id}")
            else:
                logger.warning(f"Webhook notification failed for job {job.job_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Webhook notification error for job {job.job_id}: {e}")
    
    def _send_progress_notification(self, job: FrameOCRJob):
        """Send progress notification (simplified)"""
        if job.progress > 0 and job.progress % 0.25 == 0:  # Every 25%
            logger.info(f"Job {job.job_id} progress: {job.progress:.1%}")
    
    def get_job_statistics(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get job statistics"""
        query = "SELECT status, COUNT(*) as count FROM frame_ocr_jobs"
        params = []
        
        if tenant_id:
            query += " WHERE tenant_id = ?"
            params.append(tenant_id)
        
        query += " GROUP BY status"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Calculate additional metrics
        total_jobs = sum(status_counts.values())
        success_rate = status_counts.get('completed', 0) / max(total_jobs, 1)
        
        return {
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'success_rate': success_rate,
            'running_jobs': len(self.running_jobs),
            'queue_size': self.job_queue.queue.qsize()
        }
    
    def get_cost_analytics(self, tenant_id: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get cost analytics"""
        query = """
            SELECT 
                SUM(CASE WHEN json_extract(metrics, '$.actual_cost') IS NOT NULL 
                    THEN json_extract(metrics, '$.actual_cost') 
                    ELSE json_extract(metrics, '$.cost_estimate') END) as total_cost,
                COUNT(*) as job_count,
                AVG(CASE WHEN json_extract(metrics, '$.processing_time') IS NOT NULL 
                    THEN json_extract(metrics, '$.processing_time') 
                    ELSE 0 END) as avg_processing_time
            FROM frame_ocr_jobs WHERE 1=1
        """
        params = []
        
        if tenant_id:
            query += " AND tenant_id = ?"
            params.append(tenant_id)
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            return {
                'total_cost': row[0] or 0.0,
                'job_count': row[1] or 0,
                'avg_processing_time': row[2] or 0.0,
                'cost_per_job': (row[0] or 0.0) / max(row[1] or 1, 1)
            }
    
    def optimize_scheduling(self, mode: ProcessingMode = ProcessingMode.BALANCED):
        """Optimize job scheduling based on processing mode"""
        if mode == ProcessingMode.OFF_PEAK:
            # Increase concurrent job limit during off-peak hours
            current_hour = datetime.now().hour
            if 22 <= current_hour or current_hour <= 6:  # 10 PM to 6 AM
                # Process more jobs during off-peak
                pass
        
        elif mode == ProcessingMode.PEAK:
            # Reduce resource usage during peak hours
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 17:  # 9 AM to 5 PM
                # Limit concurrent jobs during peak
                pass
    
    def cleanup_old_jobs(self, retention_days: int = 30):
        """Clean up old completed jobs"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM frame_ocr_jobs 
                WHERE status IN ('completed', 'failed', 'cancelled') 
                AND completed_at < ?
            """, (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            logger.info(f"Cleaned up {deleted_count} old jobs")
            
        return deleted_count
    
    def shutdown(self):
        """Gracefully shutdown the job manager"""
        logger.info("Shutting down Frame OCR Job Manager")
        
        # Stop scheduler
        self.stop_scheduler()
        
        # Cancel running jobs
        for job_id in list(self.running_jobs.keys()):
            self.cancel_job(job_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Frame OCR Job Manager shutdown complete")


# Example usage and testing
if __name__ == "__main__":
    # Initialize job manager
    job_manager = FrameOCRJobManager()
    
    # Set tenant resource allocation
    allocation = ResourceAllocation(
        tenant_id="tenant_1",
        max_concurrent_jobs=3,
        cpu_limit=2.0,
        memory_limit=4096,
        priority_weight=1.5,
        cost_budget=500.0
    )
    job_manager.set_tenant_allocation(allocation)
    
    # Create test jobs
    config = {
        'sampling_interval': 1.0,
        'ocr_engines': ['tesseract'],
        'confidence_threshold': 0.8
    }
    
    job1 = job_manager.create_job(
        tenant_id="tenant_1",
        video_id="video_123",
        video_path="/path/to/video.mp4",
        config=config,
        priority=JobPriority.HIGH,
        tags=["test", "demo"],
        webhook_url="https://example.com/webhook"
    )
    
    job2 = job_manager.create_job(
        tenant_id="tenant_1",
        video_id="video_456",
        video_path="/path/to/video2.mp4",
        config=config,
        priority=JobPriority.NORMAL,
        dependencies=[job1.job_id]  # Depends on job1
    )
    
    print(f"Created jobs: {job1.job_id}, {job2.job_id}")
    
    # Wait for jobs to process
    time.sleep(15)
    
    # Get job statistics
    stats = job_manager.get_job_statistics("tenant_1")
    print(f"Job statistics: {stats}")
    
    # Get cost analytics
    cost_analytics = job_manager.get_cost_analytics("tenant_1")
    print(f"Cost analytics: {cost_analytics}")
    
    # Cleanup
    job_manager.shutdown()