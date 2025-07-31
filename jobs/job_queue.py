"""
Job queue implementations for different backends
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import json
import pickle
from datetime import datetime, timedelta

from .job_manager import Job, JobStatus, JobType

logger = logging.getLogger(__name__)


class JobQueue(ABC):
    """Abstract base class for job queues"""
    
    @abstractmethod
    async def put(self, job: Job, priority: int = 0):
        """Add job to queue"""
        pass
    
    @abstractmethod
    async def get(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get job from queue"""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get queue size"""
        pass
    
    @abstractmethod
    async def clear(self):
        """Clear queue"""
        pass


class InMemoryJobQueue(JobQueue):
    """In-memory job queue implementation"""
    
    def __init__(self):
        self.queue = asyncio.PriorityQueue()
        self._counter = 0
    
    async def put(self, job: Job, priority: int = 0):
        """Add job to queue with priority"""
        # Use negative priority for max-heap behavior
        # Add counter to ensure FIFO for same priority
        await self.queue.put((-priority, self._counter, job))
        self._counter += 1
        logger.debug(f"Added job {job.id} to queue with priority {priority}")
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get highest priority job from queue"""
        try:
            if timeout:
                _, _, job = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            else:
                _, _, job = await self.queue.get()
            
            logger.debug(f"Retrieved job {job.id} from queue")
            return job
        except asyncio.TimeoutError:
            return None
    
    async def size(self) -> int:
        """Get queue size"""
        return self.queue.qsize()
    
    async def clear(self):
        """Clear queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break


class RedisJobQueue(JobQueue):
    """Redis-based job queue (placeholder for production)"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
        self.queue_key = "job_queue"
        self.processing_key = "job_processing"
    
    async def connect(self):
        """Connect to Redis"""
        try:
            import aioredis
            self.redis = await aioredis.from_url(self.redis_url)
            logger.info("Connected to Redis job queue")
        except ImportError:
            logger.error("aioredis not installed. Install with: pip install aioredis")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
    
    async def put(self, job: Job, priority: int = 0):
        """Add job to Redis queue"""
        if not self.redis:
            await self.connect()
        
        # Serialize job
        job_data = json.dumps(job.to_dict())
        
        # Add to sorted set with priority as score
        await self.redis.zadd(self.queue_key, {job_data: priority})
        logger.debug(f"Added job {job.id} to Redis queue with priority {priority}")
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get highest priority job from Redis queue"""
        if not self.redis:
            await self.connect()
        
        # Use BZPOPMAX for blocking pop with timeout
        if timeout:
            result = await self.redis.bzpopmax(self.queue_key, timeout=timeout)
        else:
            result = await self.redis.bzpopmax(self.queue_key, timeout=1)
        
        if not result:
            return None
        
        # Parse result
        _, job_data, _ = result
        job_dict = json.loads(job_data)
        job = Job.from_dict(job_dict)
        
        # Move to processing set
        await self.redis.sadd(self.processing_key, job.id)
        
        logger.debug(f"Retrieved job {job.id} from Redis queue")
        return job
    
    async def complete_job(self, job_id: str):
        """Mark job as completed and remove from processing"""
        if self.redis:
            await self.redis.srem(self.processing_key, job_id)
    
    async def size(self) -> int:
        """Get queue size"""
        if not self.redis:
            await self.connect()
        return await self.redis.zcard(self.queue_key)
    
    async def clear(self):
        """Clear queue"""
        if not self.redis:
            await self.connect()
        await self.redis.delete(self.queue_key)
        await self.redis.delete(self.processing_key)


class DatabaseJobQueue(JobQueue):
    """Database-based job queue"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.poll_interval = 1.0
    
    async def put(self, job: Job, priority: int = 0):
        """Add job to database queue"""
        # In a real implementation, you'd have a jobs table
        # For now, we'll use the existing structure
        
        # This would be something like:
        # db_job = DBJob(
        #     id=job.id,
        #     type=job.type.value,
        #     status=job.status.value,
        #     data=json.dumps(job.data),
        #     priority=priority,
        #     created_at=job.created_at
        # )
        # self.db.add(db_job)
        # self.db.commit()
        
        logger.debug(f"Added job {job.id} to database queue")
    
    async def get(self, timeout: Optional[float] = None) -> Optional[Job]:
        """Get job from database queue"""
        # This would query for pending jobs ordered by priority and created_at
        # For now, return None
        
        start_time = datetime.utcnow()
        
        while True:
            # In real implementation:
            # db_job = self.db.query(DBJob).filter_by(
            #     status='pending'
            # ).order_by(
            #     DBJob.priority.desc(),
            #     DBJob.created_at.asc()
            # ).first()
            # 
            # if db_job:
            #     db_job.status = 'running'
            #     self.db.commit()
            #     return Job.from_dict(json.loads(db_job.data))
            
            if timeout and (datetime.utcnow() - start_time).total_seconds() > timeout:
                return None
            
            await asyncio.sleep(self.poll_interval)
    
    async def size(self) -> int:
        """Get queue size"""
        # return self.db.query(DBJob).filter_by(status='pending').count()
        return 0
    
    async def clear(self):
        """Clear queue"""
        # self.db.query(DBJob).filter_by(status='pending').delete()
        # self.db.commit()
        pass


class DelayedJobQueue:
    """Queue for delayed/scheduled jobs"""
    
    def __init__(self, base_queue: JobQueue):
        self.base_queue = base_queue
        self.delayed_jobs: List[tuple] = []  # (execute_at, job)
        self.running = False
        self.scheduler_task = None
    
    async def put_delayed(self, job: Job, delay_seconds: int, priority: int = 0):
        """Add job to be executed after delay"""
        execute_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        self.delayed_jobs.append((execute_at, job, priority))
        self.delayed_jobs.sort(key=lambda x: x[0])  # Sort by execute_at
        logger.info(f"Scheduled job {job.id} to run in {delay_seconds} seconds")
    
    async def put_scheduled(self, job: Job, execute_at: datetime, priority: int = 0):
        """Add job to be executed at specific time"""
        self.delayed_jobs.append((execute_at, job, priority))
        self.delayed_jobs.sort(key=lambda x: x[0])  # Sort by execute_at
        logger.info(f"Scheduled job {job.id} to run at {execute_at}")
    
    async def start_scheduler(self):
        """Start scheduler for delayed jobs"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Started delayed job scheduler")
    
    async def stop_scheduler(self):
        """Stop scheduler"""
        if not self.running:
            return
        
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped delayed job scheduler")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                now = datetime.utcnow()
                jobs_to_execute = []
                
                # Find jobs ready to execute
                for i, (execute_at, job, priority) in enumerate(self.delayed_jobs):
                    if execute_at <= now:
                        jobs_to_execute.append((i, job, priority))
                    else:
                        break  # List is sorted, so we can break early
                
                # Remove executed jobs and add to main queue
                for i, job, priority in reversed(jobs_to_execute):
                    self.delayed_jobs.pop(i)
                    await self.base_queue.put(job, priority)
                    logger.info(f"Moved scheduled job {job.id} to main queue")
                
                # Sleep for a bit before checking again
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(1)
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of scheduled jobs"""
        return [
            {
                'job_id': job.id,
                'job_type': job.type.value,
                'execute_at': execute_at.isoformat(),
                'priority': priority
            }
            for execute_at, job, priority in self.delayed_jobs
        ]