#!/usr/bin/env python3
"""
Batch Transcription Processing System
Handles high-volume transcription with queue management, parallel processing,
and comprehensive progress tracking
"""

import asyncio
import json
import logging
import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from queue import PriorityQueue
import redis
from celery import Celery, Task
from celery.result import AsyncResult
import whisper
from faster_whisper import WhisperModel
import pandas as pd
import numpy as np
from tqdm import tqdm
import pickle
import yaml
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Priority(Enum):
    """Job priority levels"""
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class JobStatus(Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"


class ExportFormat(Enum):
    """Export format types"""
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    XML = "xml"
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class TranscriptionJob:
    """Individual transcription job"""
    job_id: str
    file_path: str
    priority: Priority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    callback_url: Optional[str] = None
    notification_email: Optional[str] = None


@dataclass
class BatchJob:
    """Batch of transcription jobs"""
    batch_id: str
    name: str
    jobs: List[TranscriptionJob]
    priority: Priority
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    export_formats: List[ExportFormat] = field(default_factory=list)
    output_path: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None
    notification_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkerStats:
    """Worker performance statistics"""
    worker_id: str
    jobs_processed: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    current_job: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    success_rate: float = 100.0


class BatchTranscriptionSystem:
    """Main batch transcription processing system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.jobs_queue = PriorityQueue()
        self.active_jobs: Dict[str, TranscriptionJob] = {}
        self.completed_jobs: Dict[str, TranscriptionJob] = {}
        self.batches: Dict[str, BatchJob] = {}
        self.workers: Dict[str, WorkerStats] = {}
        
        # Initialize worker pool
        self.max_workers = self.config.get('max_workers', mp.cpu_count())
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        self.thread_executor = ThreadPoolExecutor(max_workers=self.max_workers * 2)
        
        # Initialize models
        self.models: Dict[str, Any] = {}
        self._initialize_models()
        
        # Initialize Redis for distributed queue (optional)
        self.redis_client = None
        if self.config.get('use_redis', False):
            self._initialize_redis()
        
        # Initialize Celery for distributed processing (optional)
        self.celery_app = None
        if self.config.get('use_celery', False):
            self._initialize_celery()
        
        # Scheduling
        self.scheduler = schedule.Scheduler()
        self.is_running = False
        
    def _initialize_models(self):
        """Initialize transcription models"""
        try:
            # Initialize Faster Whisper for batch processing
            self.models['faster_whisper'] = WhisperModel(
                "base",
                device="cpu",
                compute_type="int8",
                num_workers=self.max_workers
            )
            
            # Initialize standard Whisper as fallback
            self.models['whisper'] = whisper.load_model("base")
            
            logger.info("Transcription models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.get('redis_host', 'localhost'),
                port=self.config.get('redis_port', 6379),
                db=self.config.get('redis_db', 0),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory queue.")
            self.redis_client = None
    
    def _initialize_celery(self):
        """Initialize Celery for distributed processing"""
        try:
            self.celery_app = Celery(
                'batch_transcription',
                broker=self.config.get('celery_broker', 'redis://localhost:6379'),
                backend=self.config.get('celery_backend', 'redis://localhost:6379')
            )
            logger.info("Celery initialized for distributed processing")
        except Exception as e:
            logger.warning(f"Celery initialization failed: {e}")
            self.celery_app = None
    
    async def create_batch(
        self,
        name: str,
        file_paths: List[str],
        priority: Priority = Priority.NORMAL,
        config: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[ExportFormat]] = None,
        schedule_time: Optional[datetime] = None,
        notification_email: Optional[str] = None
    ) -> BatchJob:
        """Create a new batch job"""
        
        batch_id = str(uuid.uuid4())
        batch_config = config or {}
        
        # Create individual jobs
        jobs = []
        for file_path in file_paths:
            job = TranscriptionJob(
                job_id=str(uuid.uuid4()),
                file_path=file_path,
                priority=priority,
                status=JobStatus.QUEUED,
                created_at=datetime.now(),
                config=batch_config,
                notification_email=notification_email
            )
            jobs.append(job)
            
            # Add to queue
            self.jobs_queue.put((priority.value, job.created_at, job))
            
            # Store in Redis if available
            if self.redis_client:
                self._store_job_redis(job)
        
        # Create batch
        batch = BatchJob(
            batch_id=batch_id,
            name=name,
            jobs=jobs,
            priority=priority,
            status=JobStatus.QUEUED,
            created_at=datetime.now(),
            total_files=len(file_paths),
            export_formats=export_formats or [ExportFormat.JSON],
            notification_config={'email': notification_email} if notification_email else {}
        )
        
        self.batches[batch_id] = batch
        
        # Schedule if needed
        if schedule_time:
            self._schedule_batch(batch, schedule_time)
        else:
            # Start processing immediately
            asyncio.create_task(self._process_batch(batch))
        
        logger.info(f"Created batch {batch_id} with {len(jobs)} jobs")
        
        return batch
    
    def _store_job_redis(self, job: TranscriptionJob):
        """Store job in Redis"""
        if self.redis_client:
            job_data = {
                'job_id': job.job_id,
                'file_path': job.file_path,
                'priority': job.priority.value,
                'status': job.status.value,
                'created_at': job.created_at.isoformat(),
                'config': json.dumps(job.config)
            }
            self.redis_client.hset(f"job:{job.job_id}", mapping=job_data)
            self.redis_client.zadd(
                "job_queue",
                {job.job_id: job.priority.value}
            )
    
    def _schedule_batch(self, batch: BatchJob, schedule_time: datetime):
        """Schedule batch for later processing"""
        
        def run_batch():
            asyncio.run(self._process_batch(batch))
        
        # Calculate delay
        delay = (schedule_time - datetime.now()).total_seconds()
        
        if delay > 0:
            # Schedule for later
            timer = threading.Timer(delay, run_batch)
            timer.start()
            logger.info(f"Batch {batch.batch_id} scheduled for {schedule_time}")
        else:
            # Run immediately if time has passed
            asyncio.create_task(self._process_batch(batch))
    
    async def _process_batch(self, batch: BatchJob):
        """Process all jobs in a batch"""
        
        batch.status = JobStatus.PROCESSING
        logger.info(f"Starting batch {batch.batch_id} processing")
        
        # Create worker tasks
        worker_tasks = []
        for i in range(min(self.max_workers, len(batch.jobs))):
            worker_id = f"worker_{i}"
            self.workers[worker_id] = WorkerStats(worker_id=worker_id)
            task = asyncio.create_task(self._worker(worker_id))
            worker_tasks.append(task)
        
        # Monitor progress
        monitor_task = asyncio.create_task(self._monitor_batch_progress(batch))
        
        # Wait for all jobs to complete
        while batch.completed_files + batch.failed_files < batch.total_files:
            await asyncio.sleep(1)
        
        # Cancel workers
        for task in worker_tasks:
            task.cancel()
        
        monitor_task.cancel()
        
        # Export results
        if batch.export_formats:
            await self._export_batch_results(batch)
        
        # Send notifications
        await self._send_batch_notification(batch)
        
        batch.status = JobStatus.COMPLETED
        batch.completed_at = datetime.now()
        
        logger.info(f"Batch {batch.batch_id} completed: {batch.completed_files} success, {batch.failed_files} failed")
    
    async def _worker(self, worker_id: str):
        """Worker process for handling jobs"""
        
        worker_stats = self.workers[worker_id]
        
        while True:
            try:
                # Get job from queue
                if not self.jobs_queue.empty():
                    priority, created_at, job = self.jobs_queue.get(timeout=1)
                    
                    worker_stats.current_job = job.job_id
                    worker_stats.last_activity = datetime.now()
                    
                    # Process job
                    start_time = time.time()
                    job.status = JobStatus.PROCESSING
                    job.started_at = datetime.now()
                    self.active_jobs[job.job_id] = job
                    
                    try:
                        # Perform transcription
                        result = await self._transcribe_file(job)
                        
                        job.result = result
                        job.status = JobStatus.COMPLETED
                        job.completed_at = datetime.now()
                        job.progress = 100.0
                        
                        # Update statistics
                        processing_time = time.time() - start_time
                        worker_stats.jobs_processed += 1
                        worker_stats.total_processing_time += processing_time
                        worker_stats.average_processing_time = (
                            worker_stats.total_processing_time / worker_stats.jobs_processed
                        )
                        
                        # Move to completed
                        self.completed_jobs[job.job_id] = job
                        del self.active_jobs[job.job_id]
                        
                        # Update batch
                        self._update_batch_progress(job, success=True)
                        
                        logger.info(f"Worker {worker_id} completed job {job.job_id}")
                        
                    except Exception as e:
                        logger.error(f"Worker {worker_id} failed job {job.job_id}: {e}")
                        
                        job.error_message = str(e)
                        job.retry_count += 1
                        
                        if job.retry_count < job.max_retries:
                            # Retry job
                            job.status = JobStatus.RETRYING
                            await asyncio.sleep(2 ** job.retry_count)  # Exponential backoff
                            self.jobs_queue.put((job.priority.value, job.created_at, job))
                        else:
                            # Mark as failed
                            job.status = JobStatus.FAILED
                            job.completed_at = datetime.now()
                            self.completed_jobs[job.job_id] = job
                            del self.active_jobs[job.job_id]
                            
                            # Update batch
                            self._update_batch_progress(job, success=False)
                            
                            worker_stats.error_count += 1
                    
                    worker_stats.current_job = None
                    worker_stats.success_rate = (
                        (worker_stats.jobs_processed - worker_stats.error_count) 
                        / worker_stats.jobs_processed * 100
                        if worker_stats.jobs_processed > 0 else 100
                    )
                    
                else:
                    await asyncio.sleep(0.5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)
    
    async def _transcribe_file(self, job: TranscriptionJob) -> Dict[str, Any]:
        """Transcribe a single file"""
        
        file_path = job.file_path
        config = job.config
        
        # Update progress
        job.progress = 10.0
        
        # Select model based on config
        model_type = config.get('model', 'faster_whisper')
        
        if model_type == 'faster_whisper' and 'faster_whisper' in self.models:
            result = await self._transcribe_with_faster_whisper(file_path, config, job)
        else:
            result = await self._transcribe_with_whisper(file_path, config, job)
        
        # Post-process result
        result['file_path'] = file_path
        result['job_id'] = job.job_id
        result['processing_time'] = (datetime.now() - job.started_at).total_seconds()
        
        job.progress = 100.0
        
        return result
    
    async def _transcribe_with_faster_whisper(
        self,
        file_path: str,
        config: Dict[str, Any],
        job: TranscriptionJob
    ) -> Dict[str, Any]:
        """Transcribe using Faster Whisper"""
        
        model = self.models['faster_whisper']
        
        # Update progress
        job.progress = 30.0
        
        # Transcribe
        segments, info = model.transcribe(
            file_path,
            language=config.get('language'),
            initial_prompt=config.get('prompt'),
            beam_size=config.get('beam_size', 5),
            word_timestamps=config.get('word_timestamps', True),
            vad_filter=config.get('vad_filter', True),
            vad_parameters=config.get('vad_parameters')
        )
        
        job.progress = 70.0
        
        # Collect results
        transcript_segments = []
        full_text = ""
        
        for segment in segments:
            seg_data = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text,
                'words': []
            }
            
            if segment.words:
                for word in segment.words:
                    seg_data['words'].append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'probability': word.probability
                    })
            
            transcript_segments.append(seg_data)
            full_text += segment.text + " "
        
        job.progress = 90.0
        
        return {
            'text': full_text.strip(),
            'segments': transcript_segments,
            'language': info.language,
            'language_probability': info.language_probability,
            'duration': info.duration
        }
    
    async def _transcribe_with_whisper(
        self,
        file_path: str,
        config: Dict[str, Any],
        job: TranscriptionJob
    ) -> Dict[str, Any]:
        """Transcribe using standard Whisper"""
        
        model = self.models['whisper']
        
        job.progress = 30.0
        
        # Transcribe
        result = model.transcribe(
            file_path,
            language=config.get('language'),
            initial_prompt=config.get('prompt'),
            word_timestamps=config.get('word_timestamps', False),
            verbose=False
        )
        
        job.progress = 90.0
        
        return {
            'text': result['text'],
            'segments': result.get('segments', []),
            'language': result.get('language', 'unknown')
        }
    
    def _update_batch_progress(self, job: TranscriptionJob, success: bool):
        """Update batch progress when job completes"""
        
        # Find batch containing this job
        for batch in self.batches.values():
            if any(j.job_id == job.job_id for j in batch.jobs):
                if success:
                    batch.completed_files += 1
                else:
                    batch.failed_files += 1
                break
    
    async def _monitor_batch_progress(self, batch: BatchJob):
        """Monitor and report batch progress"""
        
        while batch.status == JobStatus.PROCESSING:
            # Calculate overall progress
            total_progress = sum(job.progress for job in batch.jobs)
            average_progress = total_progress / len(batch.jobs) if batch.jobs else 0
            
            # Log progress
            logger.info(
                f"Batch {batch.batch_id}: {average_progress:.1f}% complete "
                f"({batch.completed_files}/{batch.total_files} files)"
            )
            
            # Update Redis if available
            if self.redis_client:
                self.redis_client.hset(
                    f"batch:{batch.batch_id}",
                    mapping={
                        'progress': average_progress,
                        'completed_files': batch.completed_files,
                        'failed_files': batch.failed_files
                    }
                )
            
            await asyncio.sleep(5)
    
    async def _export_batch_results(self, batch: BatchJob):
        """Export batch results in requested formats"""
        
        output_dir = batch.output_path or f"batch_output/{batch.batch_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect all results
        results = []
        for job in batch.jobs:
            if job.status == JobStatus.COMPLETED and job.result:
                results.append({
                    'file': job.file_path,
                    'job_id': job.job_id,
                    'transcript': job.result.get('text', ''),
                    'segments': job.result.get('segments', []),
                    'language': job.result.get('language', 'unknown'),
                    'duration': job.result.get('duration', 0),
                    'processing_time': job.result.get('processing_time', 0)
                })
        
        # Export in different formats
        for format_type in batch.export_formats:
            if format_type == ExportFormat.JSON:
                output_file = os.path.join(output_dir, f"batch_{batch.batch_id}.json")
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                    
            elif format_type == ExportFormat.CSV:
                output_file = os.path.join(output_dir, f"batch_{batch.batch_id}.csv")
                df = pd.DataFrame(results)
                df.to_csv(output_file, index=False)
                
            elif format_type == ExportFormat.TXT:
                output_file = os.path.join(output_dir, f"batch_{batch.batch_id}.txt")
                with open(output_file, 'w') as f:
                    for result in results:
                        f.write(f"File: {result['file']}\n")
                        f.write(f"Transcript: {result['transcript']}\n")
                        f.write("-" * 80 + "\n")
                        
            elif format_type == ExportFormat.SRT:
                for result in results:
                    base_name = Path(result['file']).stem
                    output_file = os.path.join(output_dir, f"{base_name}.srt")
                    self._export_srt(result['segments'], output_file)
                    
            elif format_type == ExportFormat.VTT:
                for result in results:
                    base_name = Path(result['file']).stem
                    output_file = os.path.join(output_dir, f"{base_name}.vtt")
                    self._export_vtt(result['segments'], output_file)
        
        logger.info(f"Exported batch {batch.batch_id} results to {output_dir}")
    
    def _export_srt(self, segments: List[Dict], output_file: str):
        """Export segments as SRT file"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start_time = self._format_timestamp(segment['start'], 'srt')
                end_time = self._format_timestamp(segment['end'], 'srt')
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")
    
    def _export_vtt(self, segments: List[Dict], output_file: str):
        """Export segments as WebVTT file"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for segment in segments:
                start_time = self._format_timestamp(segment['start'], 'vtt')
                end_time = self._format_timestamp(segment['end'], 'vtt')
                
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{segment['text'].strip()}\n\n")
    
    def _format_timestamp(self, seconds: float, format_type: str) -> str:
        """Format timestamp for subtitle formats"""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if format_type == 'srt':
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
        else:  # vtt
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    async def _send_batch_notification(self, batch: BatchJob):
        """Send notification when batch completes"""
        
        if batch.notification_config.get('email'):
            try:
                email = batch.notification_config['email']
                subject = f"Batch Transcription Complete: {batch.name}"
                
                body = f"""
                Batch transcription has completed.
                
                Batch ID: {batch.batch_id}
                Name: {batch.name}
                Total Files: {batch.total_files}
                Completed: {batch.completed_files}
                Failed: {batch.failed_files}
                Success Rate: {(batch.completed_files/batch.total_files*100):.1f}%
                Processing Time: {(batch.completed_at - batch.created_at).total_seconds():.1f} seconds
                """
                
                # Send email (simplified - in production use proper email service)
                logger.info(f"Notification sent to {email}: {subject}")
                
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get current batch status"""
        
        if batch_id not in self.batches:
            return None
        
        batch = self.batches[batch_id]
        
        # Calculate progress
        total_progress = sum(job.progress for job in batch.jobs)
        average_progress = total_progress / len(batch.jobs) if batch.jobs else 0
        
        return {
            'batch_id': batch_id,
            'name': batch.name,
            'status': batch.status.value,
            'progress': average_progress,
            'total_files': batch.total_files,
            'completed_files': batch.completed_files,
            'failed_files': batch.failed_files,
            'created_at': batch.created_at.isoformat(),
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
            'jobs': [
                {
                    'job_id': job.job_id,
                    'file': job.file_path,
                    'status': job.status.value,
                    'progress': job.progress
                }
                for job in batch.jobs
            ]
        }
    
    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch job"""
        
        if batch_id not in self.batches:
            return False
        
        batch = self.batches[batch_id]
        batch.status = JobStatus.CANCELLED
        
        # Cancel all pending jobs
        for job in batch.jobs:
            if job.status in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                job.status = JobStatus.CANCELLED
        
        logger.info(f"Batch {batch_id} cancelled")
        return True
    
    def get_worker_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all workers"""
        
        return [
            {
                'worker_id': worker.worker_id,
                'jobs_processed': worker.jobs_processed,
                'average_time': worker.average_processing_time,
                'current_job': worker.current_job,
                'last_activity': worker.last_activity.isoformat(),
                'success_rate': worker.success_rate,
                'error_count': worker.error_count
            }
            for worker in self.workers.values()
        ]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        
        return {
            'queued_jobs': self.jobs_queue.qsize(),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'total_batches': len(self.batches),
            'active_workers': len([w for w in self.workers.values() if w.current_job]),
            'total_workers': len(self.workers)
        }


# Example usage
async def main():
    """Example usage of batch transcription system"""
    
    # Initialize system
    batch_system = BatchTranscriptionSystem({
        'max_workers': 4,
        'use_redis': False,
        'use_celery': False
    })
    
    # Create a batch job
    batch = await batch_system.create_batch(
        name="Meeting Recordings Batch",
        file_paths=[
            "meeting1.mp3",
            "meeting2.mp3",
            "meeting3.mp3"
        ],
        priority=Priority.HIGH,
        config={
            'language': 'en',
            'word_timestamps': True,
            'vad_filter': True
        },
        export_formats=[ExportFormat.JSON, ExportFormat.SRT, ExportFormat.CSV],
        notification_email="user@example.com"
    )
    
    print(f"Created batch: {batch.batch_id}")
    
    # Monitor progress
    while batch.status != JobStatus.COMPLETED:
        status = batch_system.get_batch_status(batch.batch_id)
        print(f"Progress: {status['progress']:.1f}%")
        await asyncio.sleep(5)
    
    print("Batch processing complete!")
    
    # Get worker statistics
    worker_stats = batch_system.get_worker_stats()
    for stats in worker_stats:
        print(f"Worker {stats['worker_id']}: {stats['jobs_processed']} jobs, "
              f"{stats['success_rate']:.1f}% success rate")


if __name__ == "__main__":
    import threading
    asyncio.run(main())