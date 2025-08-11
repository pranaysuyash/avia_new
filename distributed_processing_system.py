#!/usr/bin/env python3
"""
Distributed Processing System for Horizontal Scaling
Implements worker pools, job queues, and load balancing for scalable processing
"""

import asyncio
import json
import logging
import hashlib
import pickle
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from queue import Queue, PriorityQueue
import socket

import redis
from redis.sentinel import Sentinel
import pika  # RabbitMQ
from celery import Celery, Task
from celery.result import AsyncResult
import ray
import dask
from dask.distributed import Client as DaskClient, as_completed
import psutil
import numpy as np
from kubernetes import client, config as k8s_config
import docker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobPriority(Enum):
    """Job priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BATCH = 5

class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class Job:
    """Distributed job representation"""
    job_id: str
    task_name: str
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes default
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Worker:
    """Worker node representation"""
    worker_id: str
    hostname: str
    ip_address: str
    cpu_count: int
    memory_gb: float
    status: str = "idle"
    current_job: Optional[str] = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    capabilities: List[str] = field(default_factory=list)
    load_average: float = 0.0

class DistributedQueue:
    """Distributed job queue with priority support"""
    
    def __init__(self, redis_client: redis.Redis, queue_name: str = "jobs"):
        self.redis = redis_client
        self.queue_name = queue_name
        self.priority_queues = {
            priority: f"{queue_name}:priority:{priority.value}"
            for priority in JobPriority
        }
    
    async def enqueue(self, job: Job) -> None:
        """Add job to queue"""
        queue_key = self.priority_queues[job.priority]
        job_data = pickle.dumps(job)
        
        # Add to priority queue
        self.redis.lpush(queue_key, job_data)
        
        # Store job details
        self.redis.hset(
            f"job:{job.job_id}",
            mapping={
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "priority": job.priority.value
            }
        )
    
    async def dequeue(self) -> Optional[Job]:
        """Get next job from queue"""
        # Check queues in priority order
        for priority in JobPriority:
            queue_key = self.priority_queues[priority]
            
            # Try to get job from queue
            job_data = self.redis.rpop(queue_key)
            if job_data:
                job = pickle.loads(job_data)
                
                # Update job status
                self.redis.hset(
                    f"job:{job.job_id}",
                    "status", JobStatus.RUNNING.value
                )
                
                return job
        
        return None
    
    async def get_queue_size(self) -> Dict[str, int]:
        """Get size of each priority queue"""
        sizes = {}
        for priority in JobPriority:
            queue_key = self.priority_queues[priority]
            sizes[priority.name] = self.redis.llen(queue_key)
        return sizes

class WorkerPool:
    """Manages pool of worker processes"""
    
    def __init__(
        self,
        num_workers: int = None,
        use_processes: bool = True
    ):
        self.num_workers = num_workers or mp.cpu_count()
        self.use_processes = use_processes
        self.workers: Dict[str, Worker] = {}
        self.executor = None
        self.tasks = {}
        self._shutdown = False
        
        # Initialize executor
        if use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
    
    def register_worker(self, worker: Worker) -> None:
        """Register a worker in the pool"""
        self.workers[worker.worker_id] = worker
        logger.info(f"Registered worker {worker.worker_id}")
    
    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a worker"""
        if worker_id in self.workers:
            del self.workers[worker_id]
            logger.info(f"Unregistered worker {worker_id}")
    
    def get_available_worker(self) -> Optional[Worker]:
        """Get an available worker"""
        for worker in self.workers.values():
            if worker.status == "idle":
                return worker
        return None
    
    async def execute_job(self, job: Job, func: Callable) -> Any:
        """Execute job on available worker"""
        worker = self.get_available_worker()
        if not worker:
            return None
        
        # Update worker status
        worker.status = "busy"
        worker.current_job = job.job_id
        job.worker_id = worker.worker_id
        job.started_at = datetime.now()
        
        try:
            # Execute job
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                func,
                job.payload
            )
            
            # Update job status
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            
            # Update worker stats
            worker.jobs_completed += 1
            
            return result
            
        except Exception as e:
            # Handle failure
            job.status = JobStatus.FAILED
            job.error = str(e)
            worker.jobs_failed += 1
            
            # Retry if applicable
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRYING
                logger.warning(f"Job {job.job_id} failed, retrying ({job.retry_count}/{job.max_retries})")
            
            raise e
            
        finally:
            # Reset worker status
            worker.status = "idle"
            worker.current_job = None
    
    def shutdown(self) -> None:
        """Shutdown worker pool"""
        self._shutdown = True
        if self.executor:
            self.executor.shutdown(wait=True)

class CeleryDistributedSystem:
    """Celery-based distributed processing"""
    
    def __init__(
        self,
        broker_url: str = "redis://localhost:6379/0",
        backend_url: str = "redis://localhost:6379/1"
    ):
        self.app = Celery(
            "distributed_processing",
            broker=broker_url,
            backend=backend_url
        )
        
        # Configure Celery
        self.app.conf.update(
            task_serializer='pickle',
            accept_content=['pickle', 'json'],
            result_serializer='pickle',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=300,
            task_soft_time_limit=250,
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1000,
        )
        
        self._register_tasks()
    
    def _register_tasks(self):
        """Register Celery tasks"""
        
        @self.app.task(bind=True, name='process_transcription')
        def process_transcription(self, audio_data: bytes) -> Dict:
            """Process audio transcription"""
            # Placeholder for actual transcription logic
            return {"status": "completed", "text": "Transcribed text"}
        
        @self.app.task(bind=True, name='process_translation')
        def process_translation(self, text: str, target_lang: str) -> str:
            """Process translation"""
            # Placeholder for actual translation logic
            return f"Translated to {target_lang}"
        
        @self.app.task(bind=True, name='process_analysis')
        def process_analysis(self, data: Dict) -> Dict:
            """Process data analysis"""
            # Placeholder for actual analysis logic
            return {"analysis": "completed"}
    
    def submit_job(self, task_name: str, *args, **kwargs) -> str:
        """Submit job to Celery"""
        task = self.app.send_task(task_name, args=args, kwargs=kwargs)
        return task.id
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get job status"""
        result = AsyncResult(job_id, app=self.app)
        return {
            "id": job_id,
            "state": result.state,
            "result": result.result if result.ready() else None,
            "info": result.info
        }

class RayDistributedSystem:
    """Ray-based distributed processing"""
    
    def __init__(self, address: Optional[str] = None):
        if address:
            ray.init(address=address)
        else:
            ray.init()
        
        self.actors = {}
    
    @ray.remote
    class ProcessingActor:
        """Ray actor for processing"""
        
        def __init__(self, actor_id: str):
            self.actor_id = actor_id
            self.jobs_processed = 0
        
        def process(self, job_data: Dict) -> Dict:
            """Process job"""
            self.jobs_processed += 1
            # Placeholder for actual processing
            return {"actor": self.actor_id, "result": "processed"}
    
    def create_actors(self, num_actors: int) -> None:
        """Create Ray actors"""
        for i in range(num_actors):
            actor_id = f"actor_{i}"
            actor = self.ProcessingActor.remote(actor_id)
            self.actors[actor_id] = actor
    
    async def submit_job(self, job_data: Dict) -> Any:
        """Submit job to Ray"""
        # Round-robin actor selection
        actor_id = f"actor_{len(self.actors) % len(self.actors)}"
        actor = self.actors[actor_id]
        
        # Submit job
        result_ref = actor.process.remote(job_data)
        result = await result_ref
        
        return result
    
    def shutdown(self):
        """Shutdown Ray"""
        ray.shutdown()

class LoadBalancer:
    """Load balancing for distributed system"""
    
    def __init__(self, workers: List[Worker]):
        self.workers = workers
        self.current_index = 0
        self.strategies = {
            "round_robin": self._round_robin,
            "least_loaded": self._least_loaded,
            "random": self._random,
            "weighted": self._weighted
        }
        self.strategy = "least_loaded"
    
    def _round_robin(self) -> Optional[Worker]:
        """Round-robin selection"""
        if not self.workers:
            return None
        
        worker = self.workers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.workers)
        return worker
    
    def _least_loaded(self) -> Optional[Worker]:
        """Select least loaded worker"""
        if not self.workers:
            return None
        
        available_workers = [w for w in self.workers if w.status == "idle"]
        if not available_workers:
            return None
        
        return min(available_workers, key=lambda w: w.load_average)
    
    def _random(self) -> Optional[Worker]:
        """Random selection"""
        import random
        available_workers = [w for w in self.workers if w.status == "idle"]
        if not available_workers:
            return None
        
        return random.choice(available_workers)
    
    def _weighted(self) -> Optional[Worker]:
        """Weighted selection based on capacity"""
        available_workers = [w for w in self.workers if w.status == "idle"]
        if not available_workers:
            return None
        
        # Weight by CPU and memory
        weights = [w.cpu_count * w.memory_gb for w in available_workers]
        total_weight = sum(weights)
        
        import random
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        for worker, weight in zip(available_workers, weights):
            cumulative += weight
            if r <= cumulative:
                return worker
        
        return available_workers[-1]
    
    def select_worker(self) -> Optional[Worker]:
        """Select worker using current strategy"""
        return self.strategies[self.strategy]()
    
    def update_worker_load(self, worker_id: str, load: float) -> None:
        """Update worker load information"""
        for worker in self.workers:
            if worker.worker_id == worker_id:
                worker.load_average = load
                break

class KubernetesScaler:
    """Kubernetes-based auto-scaling"""
    
    def __init__(self):
        # Load Kubernetes config
        try:
            k8s_config.load_incluster_config()
        except:
            k8s_config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
    
    def scale_deployment(
        self,
        namespace: str,
        deployment_name: str,
        replicas: int
    ) -> None:
        """Scale Kubernetes deployment"""
        body = {"spec": {"replicas": replicas}}
        
        self.apps_v1.patch_namespaced_deployment_scale(
            name=deployment_name,
            namespace=namespace,
            body=body
        )
        
        logger.info(f"Scaled {deployment_name} to {replicas} replicas")
    
    def get_pod_metrics(self, namespace: str) -> List[Dict]:
        """Get pod metrics"""
        pods = self.v1.list_namespaced_pod(namespace)
        
        metrics = []
        for pod in pods.items:
            metric = {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "node": pod.spec.node_name,
                "containers": len(pod.spec.containers)
            }
            metrics.append(metric)
        
        return metrics
    
    def auto_scale(
        self,
        namespace: str,
        deployment_name: str,
        min_replicas: int = 1,
        max_replicas: int = 10,
        target_cpu_percent: int = 70
    ) -> None:
        """Auto-scale based on metrics"""
        # Get current metrics
        metrics = self.get_pod_metrics(namespace)
        
        # Calculate average CPU usage (placeholder)
        avg_cpu = 50  # This would come from metrics server
        
        # Determine scaling action
        current_replicas = len(metrics)
        
        if avg_cpu > target_cpu_percent and current_replicas < max_replicas:
            new_replicas = min(current_replicas + 1, max_replicas)
            self.scale_deployment(namespace, deployment_name, new_replicas)
        elif avg_cpu < target_cpu_percent * 0.5 and current_replicas > min_replicas:
            new_replicas = max(current_replicas - 1, min_replicas)
            self.scale_deployment(namespace, deployment_name, new_replicas)

class DistributedProcessingOrchestrator:
    """Main orchestrator for distributed processing"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        use_celery: bool = True,
        use_ray: bool = False,
        enable_k8s_scaling: bool = False
    ):
        # Initialize Redis
        self.redis = redis.from_url(redis_url)
        
        # Initialize queue
        self.queue = DistributedQueue(self.redis)
        
        # Initialize worker pool
        self.worker_pool = WorkerPool()
        
        # Initialize load balancer
        self.load_balancer = None
        
        # Initialize distributed systems
        self.celery_system = None
        if use_celery:
            self.celery_system = CeleryDistributedSystem()
        
        self.ray_system = None
        if use_ray:
            self.ray_system = RayDistributedSystem()
        
        # Initialize Kubernetes scaler
        self.k8s_scaler = None
        if enable_k8s_scaling:
            self.k8s_scaler = KubernetesScaler()
        
        # Monitoring
        self.stats = {
            "jobs_submitted": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "avg_processing_time": 0
        }
    
    async def submit_job(
        self,
        task_name: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL
    ) -> str:
        """Submit job for processing"""
        # Create job
        job = Job(
            job_id=str(uuid.uuid4()),
            task_name=task_name,
            payload=payload,
            priority=priority
        )
        
        # Add to queue
        await self.queue.enqueue(job)
        
        self.stats["jobs_submitted"] += 1
        
        return job.job_id
    
    async def process_jobs(self) -> None:
        """Main job processing loop"""
        while True:
            # Get next job
            job = await self.queue.dequeue()
            if not job:
                await asyncio.sleep(1)
                continue
            
            try:
                # Select processing method
                if self.celery_system and job.task_name.startswith("celery:"):
                    # Process with Celery
                    task_id = self.celery_system.submit_job(
                        job.task_name.replace("celery:", ""),
                        **job.payload
                    )
                    job.metadata["celery_task_id"] = task_id
                
                elif self.ray_system and job.task_name.startswith("ray:"):
                    # Process with Ray
                    result = await self.ray_system.submit_job(job.payload)
                    job.result = result
                
                else:
                    # Process with local worker pool
                    # Placeholder for actual processing function
                    async def process_func(payload):
                        await asyncio.sleep(1)
                        return {"processed": payload}
                    
                    result = await self.worker_pool.execute_job(job, process_func)
                    job.result = result
                
                job.status = JobStatus.COMPLETED
                self.stats["jobs_completed"] += 1
                
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                self.stats["jobs_failed"] += 1
                logger.error(f"Job {job.job_id} failed: {e}")
            
            finally:
                # Update job status in Redis
                self.redis.hset(
                    f"job:{job.job_id}",
                    mapping={
                        "status": job.status.value,
                        "completed_at": datetime.now().isoformat() if job.completed_at else "",
                        "error": job.error or ""
                    }
                )
    
    async def monitor_and_scale(self) -> None:
        """Monitor system and auto-scale"""
        while True:
            # Get queue sizes
            queue_sizes = await self.queue.get_queue_size()
            
            # Get worker stats
            active_workers = len([w for w in self.worker_pool.workers.values() if w.status == "busy"])
            idle_workers = len([w for w in self.worker_pool.workers.values() if w.status == "idle"])
            
            # Calculate metrics
            total_pending = sum(queue_sizes.values())
            
            # Auto-scale logic
            if self.k8s_scaler and total_pending > idle_workers * 10:
                # Scale up if too many pending jobs
                self.k8s_scaler.auto_scale(
                    namespace="default",
                    deployment_name="worker-deployment",
                    min_replicas=2,
                    max_replicas=20
                )
            
            # Log metrics
            logger.info(f"Queue sizes: {queue_sizes}, Active workers: {active_workers}, Idle workers: {idle_workers}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get job status"""
        job_data = self.redis.hgetall(f"job:{job_id}")
        
        if not job_data:
            return {"status": "not_found"}
        
        return {
            key.decode(): value.decode()
            for key, value in job_data.items()
        }
    
    async def shutdown(self) -> None:
        """Shutdown orchestrator"""
        self.worker_pool.shutdown()
        
        if self.ray_system:
            self.ray_system.shutdown()

# Example usage
async def main():
    """Example usage of distributed processing"""
    
    # Initialize orchestrator
    orchestrator = DistributedProcessingOrchestrator(
        use_celery=True,
        use_ray=False
    )
    
    # Submit jobs
    job_ids = []
    for i in range(10):
        job_id = await orchestrator.submit_job(
            task_name="process_data",
            payload={"data": f"item_{i}"},
            priority=JobPriority.NORMAL
        )
        job_ids.append(job_id)
        print(f"Submitted job {job_id}")
    
    # Start processing
    processing_task = asyncio.create_task(orchestrator.process_jobs())
    
    # Wait a bit
    await asyncio.sleep(5)
    
    # Check job statuses
    for job_id in job_ids:
        status = orchestrator.get_job_status(job_id)
        print(f"Job {job_id}: {status}")
    
    # Shutdown
    await orchestrator.shutdown()
    processing_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())