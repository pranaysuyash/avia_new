#!/usr/bin/env python3
"""
Batch Transcription Processing System
Task 228: Support for processing multiple files simultaneously with queue management,
progress tracking, and automated scheduling.
"""

import asyncio
import json
import os
import sqlite3
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
import hashlib
import logging
import threading
from queue import Queue, PriorityQueue
import heapq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job processing status."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class JobPriority(Enum):
    """Job priority levels."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

class FileFormat(Enum):
    """Supported file formats."""
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"

class ExportFormat(Enum):
    """Export format options."""
    TXT = "txt"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    SRT = "srt"
    VTT = "vtt"
    DOCX = "docx"
    PDF = "pdf"

@dataclass
class FileItem:
    """Individual file in batch processing."""
    file_id: str
    file_path: str
    file_name: str
    file_size: int
    file_format: FileFormat
    estimated_duration: Optional[float] = None
    language: Optional[str] = None
    custom_vocabulary: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchJob:
    """Batch processing job definition."""
    job_id: str
    job_name: str
    files: List[FileItem]
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_file: Optional[str] = None
    processed_files: int = 0
    failed_files: int = 0
    total_files: int = 0
    estimated_completion: Optional[datetime] = None
    processing_options: Dict[str, Any] = field(default_factory=dict)
    export_formats: List[ExportFormat] = field(default_factory=list)
    output_directory: Optional[str] = None
    error_messages: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingResult:
    """Result of processing a single file."""
    file_id: str
    success: bool
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: float = 0.0
    file_size: int = 0
    duration: Optional[float] = None
    language_detected: Optional[str] = None
    word_count: int = 0
    error_message: Optional[str] = None
    export_files: Dict[ExportFormat, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueueStatistics:
    """Queue statistics and metrics."""
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    average_processing_time: float
    queue_size: int
    estimated_wait_time: float
    throughput: float  # files per hour
    system_load: float

@dataclass
class ScheduledJob:
    """Scheduled batch job."""
    schedule_id: str
    job_template: BatchJob
    cron_expression: str
    next_run: datetime
    enabled: bool
    run_count: int = 0
    last_run: Optional[datetime] = None
    last_status: Optional[JobStatus] = None

class FileValidator:
    """Validates and analyzes files for batch processing."""
    
    def __init__(self):
        self.supported_formats = {fmt.value for fmt in FileFormat}
        self.max_file_size = 10 * 1024 * 1024 * 1024  # 10GB
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[FileItem]]:
        """Validate a file for processing."""
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False, f"File not found: {file_path}", None
            
            # Check if it's a file
            if not path.is_file():
                return False, f"Path is not a file: {file_path}", None
            
            # Get file info
            file_size = path.stat().st_size
            file_format = path.suffix.lower().lstrip('.')
            
            # Check file size
            if file_size > self.max_file_size:
                return False, f"File too large: {file_size/1024/1024/1024:.2f}GB (max: {self.max_file_size/1024/1024/1024:.0f}GB)", None
            
            # Check format support
            if file_format not in self.supported_formats:
                return False, f"Unsupported format: {file_format}", None
            
            # Create file item
            file_item = FileItem(
                file_id=str(uuid.uuid4()),
                file_path=str(path.absolute()),
                file_name=path.name,
                file_size=file_size,
                file_format=FileFormat(file_format),
                estimated_duration=self._estimate_duration(file_path, file_size),
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'validated_at': datetime.now().isoformat()
                }
            )
            
            return True, None, file_item
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", None
    
    def _estimate_duration(self, file_path: str, file_size: int) -> float:
        """Estimate audio/video duration based on file size."""
        # Rough estimation: assume ~1MB per minute for compressed audio
        # This is a simplification - real implementation would use audio libraries
        estimated_minutes = file_size / (1024 * 1024)  # MB
        return max(1.0, estimated_minutes * 60)  # Convert to seconds, minimum 1 second

    def validate_batch(self, file_paths: List[str]) -> Tuple[List[FileItem], List[str]]:
        """Validate multiple files for batch processing."""
        valid_files = []
        errors = []
        
        for file_path in file_paths:
            is_valid, error, file_item = self.validate_file(file_path)
            if is_valid and file_item:
                valid_files.append(file_item)
            else:
                errors.append(f"{file_path}: {error}")
        
        return valid_files, errors

class JobQueue:
    """Priority queue for managing batch jobs."""
    
    def __init__(self, max_concurrent_jobs: int = 4):
        self.max_concurrent_jobs = max_concurrent_jobs
        self._queue = PriorityQueue()
        self._processing = {}  # job_id -> job
        self._completed = {}   # job_id -> job
        self._failed = {}      # job_id -> job
        self._lock = threading.Lock()
        self._job_counter = 0
    
    def add_job(self, job: BatchJob) -> str:
        """Add a job to the queue."""
        with self._lock:
            # Set total files
            job.total_files = len(job.files)
            job.status = JobStatus.QUEUED
            
            # Add to priority queue (lower priority value = higher priority)
            self._queue.put((job.priority.value, self._job_counter, job))
            self._job_counter += 1
            
            logger.info(f"Job {job.job_id} added to queue with priority {job.priority.value}")
            return job.job_id
    
    def get_next_job(self) -> Optional[BatchJob]:
        """Get the next job to process."""
        with self._lock:
            if len(self._processing) >= self.max_concurrent_jobs:
                return None
            
            if self._queue.empty():
                return None
            
            _, _, job = self._queue.get()
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            self._processing[job.job_id] = job
            
            return job
    
    def complete_job(self, job_id: str, success: bool = True):
        """Mark a job as completed."""
        with self._lock:
            if job_id in self._processing:
                job = self._processing.pop(job_id)
                job.completed_at = datetime.now()
                
                if success:
                    job.status = JobStatus.COMPLETED
                    job.progress = 1.0
                    self._completed[job_id] = job
                    logger.info(f"Job {job_id} completed successfully")
                else:
                    job.status = JobStatus.FAILED
                    self._failed[job_id] = job
                    logger.error(f"Job {job_id} failed")
    
    def update_job_progress(self, job_id: str, progress: float, current_file: Optional[str] = None):
        """Update job progress."""
        with self._lock:
            if job_id in self._processing:
                job = self._processing[job_id]
                job.progress = min(1.0, max(0.0, progress))
                if current_file:
                    job.current_file = current_file
                
                # Update estimated completion
                if progress > 0:
                    elapsed = (datetime.now() - job.started_at).total_seconds()
                    estimated_total_time = elapsed / progress
                    remaining_time = estimated_total_time - elapsed
                    job.estimated_completion = datetime.now() + timedelta(seconds=remaining_time)
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID."""
        with self._lock:
            # Check all possible locations
            for storage in [self._processing, self._completed, self._failed]:
                if job_id in storage:
                    return storage[job_id]
            
            # Check queue (this is expensive, use sparingly)
            queue_items = []
            while not self._queue.empty():
                item = self._queue.get()
                queue_items.append(item)
                if item[2].job_id == job_id:
                    # Restore queue
                    for qi in queue_items:
                        self._queue.put(qi)
                    return item[2]
            
            # Restore queue
            for item in queue_items:
                self._queue.put(item)
            
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        with self._lock:
            # Can't cancel if already processing or completed
            if job_id in self._processing or job_id in self._completed or job_id in self._failed:
                return False
            
            # Remove from queue
            queue_items = []
            found = False
            
            while not self._queue.empty():
                item = self._queue.get()
                if item[2].job_id == job_id:
                    item[2].status = JobStatus.CANCELLED
                    found = True
                else:
                    queue_items.append(item)
            
            # Restore queue without cancelled job
            for item in queue_items:
                self._queue.put(item)
            
            return found
    
    def get_statistics(self) -> QueueStatistics:
        """Get queue statistics."""
        with self._lock:
            total_jobs = len(self._processing) + len(self._completed) + len(self._failed) + self._queue.qsize()
            
            # Calculate average processing time
            completed_jobs = list(self._completed.values())
            if completed_jobs:
                processing_times = []
                for job in completed_jobs:
                    if job.started_at and job.completed_at:
                        processing_time = (job.completed_at - job.started_at).total_seconds()
                        processing_times.append(processing_time)
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            else:
                avg_processing_time = 0
            
            # Estimate wait time based on queue size and processing capacity
            queue_size = self._queue.qsize()
            available_slots = max(0, self.max_concurrent_jobs - len(self._processing))
            
            if available_slots > 0:
                estimated_wait = 0
            else:
                estimated_wait = (queue_size / self.max_concurrent_jobs) * avg_processing_time
            
            # Calculate throughput (files per hour)
            if completed_jobs:
                total_files = sum(job.total_files for job in completed_jobs)
                total_time_hours = sum(
                    (job.completed_at - job.started_at).total_seconds() / 3600
                    for job in completed_jobs
                    if job.started_at and job.completed_at
                ) or 1
                throughput = total_files / total_time_hours
            else:
                throughput = 0
            
            return QueueStatistics(
                total_jobs=total_jobs,
                pending_jobs=queue_size,
                processing_jobs=len(self._processing),
                completed_jobs=len(self._completed),
                failed_jobs=len(self._failed),
                average_processing_time=avg_processing_time,
                queue_size=queue_size,
                estimated_wait_time=estimated_wait,
                throughput=throughput,
                system_load=len(self._processing) / self.max_concurrent_jobs
            )

class MockTranscriptionEngine:
    """Mock transcription engine for demonstration."""
    
    def __init__(self):
        self.processing_speed = 2.0  # 2x real-time processing
    
    async def transcribe_file(self, file_path: str, options: Dict[str, Any] = None) -> ProcessingResult:
        """Mock transcription of a single file."""
        try:
            # Simulate processing time based on file size
            file_size = os.path.getsize(file_path)
            estimated_duration = file_size / (1024 * 1024) * 60  # Rough estimate
            processing_time = estimated_duration / self.processing_speed
            
            # Simulate processing delay
            await asyncio.sleep(min(processing_time, 5))  # Cap at 5 seconds for demo
            
            # Generate mock transcript
            file_name = os.path.basename(file_path)
            mock_transcript = f"Mock transcription of {file_name}. This is a sample transcript that would contain the actual spoken content from the audio or video file. The transcription includes various words and phrases that demonstrate the capability of the system."
            
            return ProcessingResult(
                file_id=str(uuid.uuid4()),
                success=True,
                transcript=mock_transcript,
                confidence=0.89,
                processing_time=min(processing_time, 5),
                file_size=file_size,
                duration=estimated_duration,
                language_detected="en",
                word_count=len(mock_transcript.split()),
                metadata={
                    'processed_at': datetime.now().isoformat(),
                    'engine': 'mock',
                    'version': '1.0'
                }
            )
            
        except Exception as e:
            return ProcessingResult(
                file_id=str(uuid.uuid4()),
                success=False,
                error_message=str(e),
                processing_time=0,
                file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
            )

class ExportManager:
    """Manages export of transcription results to various formats."""
    
    def __init__(self, output_directory: str = "batch_output"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)
    
    def export_result(self, result: ProcessingResult, formats: List[ExportFormat], 
                     job_id: str, file_item: FileItem) -> Dict[ExportFormat, str]:
        """Export result to specified formats."""
        exported_files = {}
        
        if not result.success or not result.transcript:
            return exported_files
        
        base_name = Path(file_item.file_name).stem
        job_dir = self.output_directory / job_id
        job_dir.mkdir(exist_ok=True)
        
        for format in formats:
            try:
                if format == ExportFormat.TXT:
                    file_path = job_dir / f"{base_name}.txt"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(result.transcript)
                    exported_files[format] = str(file_path)
                
                elif format == ExportFormat.JSON:
                    file_path = job_dir / f"{base_name}.json"
                    data = {
                        'file_name': file_item.file_name,
                        'transcript': result.transcript,
                        'confidence': result.confidence,
                        'duration': result.duration,
                        'language': result.language_detected,
                        'word_count': result.word_count,
                        'processing_time': result.processing_time,
                        'metadata': result.metadata
                    }
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    exported_files[format] = str(file_path)
                
                elif format == ExportFormat.SRT:
                    file_path = job_dir / f"{base_name}.srt"
                    # Simple SRT generation (in real implementation, would need timestamps)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("1\n00:00:00,000 --> 00:01:00,000\n")
                        f.write(result.transcript)
                        f.write("\n\n")
                    exported_files[format] = str(file_path)
                
                elif format == ExportFormat.CSV:
                    file_path = job_dir / f"{base_name}.csv"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("file_name,transcript,confidence,duration,language,word_count\n")
                        f.write(f'"{file_item.file_name}","{result.transcript}",{result.confidence},{result.duration},{result.language_detected},{result.word_count}\n')
                    exported_files[format] = str(file_path)
                
            except Exception as e:
                logger.error(f"Failed to export to {format.value}: {str(e)}")
        
        return exported_files

class BatchDatabase:
    """SQLite database for storing batch processing information."""
    
    def __init__(self, db_path: str = "batch_processing.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    job_id TEXT PRIMARY KEY,
                    job_name TEXT,
                    status TEXT,
                    priority INTEGER,
                    created_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress REAL,
                    total_files INTEGER,
                    processed_files INTEGER,
                    failed_files INTEGER,
                    processing_options TEXT,
                    export_formats TEXT,
                    output_directory TEXT,
                    metadata TEXT
                )
            """)
            
            # Files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batch_files (
                    file_id TEXT PRIMARY KEY,
                    job_id TEXT,
                    file_path TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    file_format TEXT,
                    status TEXT,
                    transcript TEXT,
                    confidence REAL,
                    processing_time REAL,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES batch_jobs (job_id)
                )
            """)
            
            # Scheduled jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    schedule_id TEXT PRIMARY KEY,
                    job_template TEXT,
                    cron_expression TEXT,
                    next_run TIMESTAMP,
                    enabled BOOLEAN,
                    run_count INTEGER,
                    last_run TIMESTAMP,
                    last_status TEXT
                )
            """)
            
            conn.commit()
    
    def store_job(self, job: BatchJob):
        """Store job information."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO batch_jobs 
                (job_id, job_name, status, priority, created_at, started_at, completed_at,
                 progress, total_files, processed_files, failed_files, processing_options,
                 export_formats, output_directory, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.job_id, job.job_name, job.status.value, job.priority.value,
                job.created_at, job.started_at, job.completed_at,
                job.progress, job.total_files, job.processed_files, job.failed_files,
                json.dumps(job.processing_options), json.dumps([f.value for f in job.export_formats]),
                job.output_directory, json.dumps(job.metadata)
            ))
            
            # Store file information
            for file_item in job.files:
                cursor.execute("""
                    INSERT OR REPLACE INTO batch_files
                    (file_id, job_id, file_path, file_name, file_size, file_format, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_item.file_id, job.job_id, file_item.file_path,
                    file_item.file_name, file_item.file_size, file_item.file_format.value,
                    'pending'
                ))
            
            conn.commit()
    
    def get_job_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get job processing history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM batch_jobs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                job_dict = dict(zip(columns, row))
                results.append(job_dict)
            
            return results

class JobScheduler:
    """Scheduler for automated batch processing."""
    
    def __init__(self):
        self.scheduled_jobs = {}
        self.running = False
    
    def add_scheduled_job(self, job_template: BatchJob, cron_expression: str) -> str:
        """Add a scheduled job."""
        schedule_id = str(uuid.uuid4())
        
        scheduled_job = ScheduledJob(
            schedule_id=schedule_id,
            job_template=job_template,
            cron_expression=cron_expression,
            next_run=self._calculate_next_run(cron_expression),
            enabled=True
        )
        
        self.scheduled_jobs[schedule_id] = scheduled_job
        return schedule_id
    
    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression."""
        # Simplified cron parsing - in real implementation, use croniter library
        if cron_expression == "0 2 * * *":  # Daily at 2 AM
            next_run = datetime.now().replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= datetime.now():
                next_run += timedelta(days=1)
            return next_run
        elif cron_expression == "0 0 * * 0":  # Weekly on Sunday
            next_run = datetime.now()
            days_ahead = 6 - next_run.weekday()  # Sunday is 6
            if days_ahead <= 0:
                days_ahead += 7
            return (next_run + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0)
        else:
            # Default to 1 hour from now
            return datetime.now() + timedelta(hours=1)
    
    def get_due_jobs(self) -> List[ScheduledJob]:
        """Get jobs that are due to run."""
        now = datetime.now()
        due_jobs = []
        
        for job in self.scheduled_jobs.values():
            if job.enabled and job.next_run <= now:
                due_jobs.append(job)
        
        return due_jobs

class BatchTranscriptionSystem:
    """Main system for batch transcription processing."""
    
    def __init__(self, max_concurrent_jobs: int = 4, output_directory: str = "batch_output"):
        self.file_validator = FileValidator()
        self.job_queue = JobQueue(max_concurrent_jobs)
        self.transcription_engine = MockTranscriptionEngine()
        self.export_manager = ExportManager(output_directory)
        self.database = BatchDatabase()
        self.scheduler = JobScheduler()
        
        self._processing_active = False
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        
        logger.info("Batch Transcription System initialized")
    
    def create_batch_job(self, 
                        file_paths: List[str],
                        job_name: str,
                        priority: JobPriority = JobPriority.NORMAL,
                        export_formats: List[ExportFormat] = None,
                        processing_options: Dict[str, Any] = None) -> Tuple[bool, str, Optional[str]]:
        """Create a new batch job."""
        try:
            # Validate files
            valid_files, errors = self.file_validator.validate_batch(file_paths)
            
            if not valid_files:
                return False, "No valid files found for processing", None
            
            # Create job
            job = BatchJob(
                job_id=str(uuid.uuid4()),
                job_name=job_name,
                files=valid_files,
                priority=priority,
                status=JobStatus.PENDING,
                created_at=datetime.now(),
                export_formats=export_formats or [ExportFormat.TXT, ExportFormat.JSON],
                processing_options=processing_options or {},
                output_directory=str(self.export_manager.output_directory)
            )
            
            # Add to queue
            job_id = self.job_queue.add_job(job)
            
            # Store in database
            self.database.store_job(job)
            
            error_summary = f" (Errors: {len(errors)} files)" if errors else ""
            return True, f"Batch job created: {len(valid_files)} files queued{error_summary}", job_id
            
        except Exception as e:
            logger.error(f"Failed to create batch job: {str(e)}")
            return False, f"Failed to create batch job: {str(e)}", None
    
    async def start_processing(self):
        """Start the batch processing engine."""
        if self._processing_active:
            return
        
        self._processing_active = True
        logger.info("Starting batch processing engine")
        
        while self._processing_active:
            try:
                # Get next job from queue
                job = self.job_queue.get_next_job()
                
                if job:
                    # Process job in background
                    asyncio.create_task(self._process_job(job))
                
                # Check for scheduled jobs
                due_jobs = self.scheduler.get_due_jobs()
                for scheduled_job in due_jobs:
                    # Create new job from template
                    new_job = scheduled_job.job_template
                    new_job.job_id = str(uuid.uuid4())
                    new_job.created_at = datetime.now()
                    self.job_queue.add_job(new_job)
                    
                    # Update schedule
                    scheduled_job.next_run = self.scheduler._calculate_next_run(scheduled_job.cron_expression)
                    scheduled_job.last_run = datetime.now()
                    scheduled_job.run_count += 1
                
                # Wait before checking for more jobs
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                await asyncio.sleep(10)
    
    def stop_processing(self):
        """Stop the batch processing engine."""
        self._processing_active = False
        logger.info("Stopping batch processing engine")
    
    async def _process_job(self, job: BatchJob):
        """Process a single batch job."""
        try:
            logger.info(f"Processing job {job.job_id}: {job.job_name}")
            
            processed_files = 0
            failed_files = 0
            
            # Process each file
            for i, file_item in enumerate(job.files):
                try:
                    # Update progress
                    progress = i / len(job.files)
                    self.job_queue.update_job_progress(job.job_id, progress, file_item.file_name)
                    
                    logger.info(f"Processing file {i+1}/{len(job.files)}: {file_item.file_name}")
                    
                    # Transcribe file
                    result = await self.transcription_engine.transcribe_file(
                        file_item.file_path, 
                        job.processing_options
                    )
                    
                    if result.success:
                        # Export results
                        exported_files = self.export_manager.export_result(
                            result, job.export_formats, job.job_id, file_item
                        )
                        result.export_files = exported_files
                        
                        processed_files += 1
                        logger.info(f"Successfully processed: {file_item.file_name}")
                        
                        # Store result
                        job.results[file_item.file_id] = {
                            'success': True,
                            'transcript': result.transcript,
                            'confidence': result.confidence,
                            'duration': result.duration,
                            'export_files': exported_files
                        }
                        
                    else:
                        failed_files += 1
                        job.error_messages.append(f"{file_item.file_name}: {result.error_message}")
                        logger.error(f"Failed to process: {file_item.file_name} - {result.error_message}")
                
                except Exception as e:
                    failed_files += 1
                    error_msg = f"{file_item.file_name}: {str(e)}"
                    job.error_messages.append(error_msg)
                    logger.error(f"File processing error: {error_msg}")
            
            # Update job status
            job.processed_files = processed_files
            job.failed_files = failed_files
            
            # Complete job
            success = processed_files > 0  # Consider success if at least one file processed
            self.job_queue.complete_job(job.job_id, success)
            
            # Update database
            self.database.store_job(job)
            
            logger.info(f"Job {job.job_id} completed: {processed_files} successful, {failed_files} failed")
            
        except Exception as e:
            logger.error(f"Job processing failed: {str(e)}")
            job.error_messages.append(f"Job processing failed: {str(e)}")
            self.job_queue.complete_job(job.job_id, False)
            self.database.store_job(job)
    
    def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get the current status of a job."""
        return self.job_queue.get_job(job_id)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        return self.job_queue.cancel_job(job_id)
    
    def get_queue_statistics(self) -> QueueStatistics:
        """Get current queue statistics."""
        return self.job_queue.get_statistics()
    
    def get_job_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get job processing history."""
        return self.database.get_job_history(limit)
    
    def schedule_job(self, job_template: BatchJob, cron_expression: str) -> str:
        """Schedule a job for automated processing."""
        return self.scheduler.add_scheduled_job(job_template, cron_expression)

# Demo and testing functions
async def demo_batch_processing():
    """Demonstrate batch transcription processing capabilities."""
    print("🔄 Batch Transcription Processing System Demo")
    print("=" * 50)
    
    # Initialize system
    system = BatchTranscriptionSystem(max_concurrent_jobs=2)
    
    # Create demo files for testing (in real use, these would be actual audio/video files)
    demo_files = []
    demo_dir = Path("demo_batch_files")
    demo_dir.mkdir(exist_ok=True)
    
    # Create mock audio files for demonstration
    for i in range(5):
        file_path = demo_dir / f"demo_audio_{i+1}.mp3"
        with open(file_path, 'wb') as f:
            # Write some dummy data (in real use, these would be actual audio files)
            f.write(b"Mock audio data " * 1000)
        demo_files.append(str(file_path))
    
    print(f"Created {len(demo_files)} demo files for processing")
    
    # Test 1: Create batch jobs
    print(f"\n📋 Test 1: Creating Batch Jobs")
    print("-" * 30)
    
    # Create high priority job
    success, message, job_id_1 = system.create_batch_job(
        file_paths=demo_files[:3],
        job_name="High Priority Batch",
        priority=JobPriority.HIGH,
        export_formats=[ExportFormat.TXT, ExportFormat.JSON, ExportFormat.SRT]
    )
    
    if success:
        print(f"✅ {message}")
        print(f"   Job ID: {job_id_1}")
    else:
        print(f"❌ {message}")
    
    # Create normal priority job
    success, message, job_id_2 = system.create_batch_job(
        file_paths=demo_files[3:],
        job_name="Normal Priority Batch",
        priority=JobPriority.NORMAL,
        export_formats=[ExportFormat.JSON, ExportFormat.CSV]
    )
    
    if success:
        print(f"✅ {message}")
        print(f"   Job ID: {job_id_2}")
    
    # Test 2: Queue statistics
    print(f"\n📊 Test 2: Queue Statistics")
    print("-" * 30)
    
    stats = system.get_queue_statistics()
    print(f"Total Jobs: {stats.total_jobs}")
    print(f"Queued Jobs: {stats.pending_jobs}")
    print(f"Processing Jobs: {stats.processing_jobs}")
    print(f"System Load: {stats.system_load:.2f}")
    
    # Test 3: Start processing
    print(f"\n🚀 Test 3: Starting Batch Processing")
    print("-" * 30)
    
    # Start processing in background
    processing_task = asyncio.create_task(system.start_processing())
    
    # Monitor progress
    jobs_to_monitor = [job_id_1, job_id_2] if job_id_1 and job_id_2 else []
    
    for _ in range(30):  # Monitor for up to 30 iterations
        await asyncio.sleep(2)
        
        print(f"\n📈 Progress Update:")
        
        all_completed = True
        for job_id in jobs_to_monitor:
            job = system.get_job_status(job_id)
            if job:
                print(f"  Job {job.job_name}: {job.status.value} ({job.progress:.1%})")
                if job.current_file:
                    print(f"    Current: {job.current_file}")
                if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    all_completed = False
            else:
                print(f"  Job {job_id}: Not found")
        
        # Show updated statistics
        stats = system.get_queue_statistics()
        print(f"  Queue: {stats.pending_jobs} pending, {stats.processing_jobs} processing")
        
        if all_completed:
            print(f"\n✅ All jobs completed!")
            break
    
    # Stop processing
    system.stop_processing()
    
    # Test 4: Results summary
    print(f"\n📋 Test 4: Results Summary")
    print("-" * 30)
    
    for job_id in jobs_to_monitor:
        job = system.get_job_status(job_id)
        if job:
            print(f"\nJob: {job.job_name}")
            print(f"  Status: {job.status.value}")
            print(f"  Files: {job.processed_files} processed, {job.failed_files} failed")
            print(f"  Duration: {(job.completed_at - job.started_at).total_seconds():.1f}s" if job.completed_at and job.started_at else "  Duration: N/A")
            
            if job.results:
                print(f"  Results: {len(job.results)} files transcribed")
                for file_id, result in list(job.results.items())[:2]:  # Show first 2
                    if result.get('success'):
                        transcript = result.get('transcript', '')[:100]
                        print(f"    - Transcript preview: {transcript}...")
    
    # Test 5: Job history
    print(f"\n📚 Test 5: Job History")
    print("-" * 30)
    
    history = system.get_job_history(limit=10)
    print(f"Found {len(history)} jobs in history:")
    
    for job in history[:3]:  # Show first 3
        print(f"  - {job['job_name']} ({job['status']}) - {job['total_files']} files")
    
    # Cleanup
    print(f"\n🧹 Cleanup")
    print("-" * 30)
    
    try:
        import shutil
        shutil.rmtree(demo_dir)
        shutil.rmtree("batch_output", ignore_errors=True)
        print("Demo files cleaned up")
    except Exception as e:
        print(f"Cleanup note: {str(e)}")
    
    print(f"\n✅ Batch processing demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_batch_processing())