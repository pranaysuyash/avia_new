#!/usr/bin/env python3
"""
Batch Processing Module for Audio/Video Transcription App
Handles multiple file processing with queue management and progress tracking
"""

import os
import logging
import time
import threading
import queue
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

# Import existing modules
import media
import stt
import ner_basic
import ner_advanced
import utils
from errors import AppError, FileProcessingError, TranscriptionError

logger = logging.getLogger(__name__)

class BatchJobStatus(Enum):
    """Status of batch processing jobs"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchFile:
    """Information about a file in batch processing"""
    id: str
    name: str
    size_bytes: int
    format: str
    temp_path: str
    status: BatchJobStatus = BatchJobStatus.PENDING
    progress: int = 0
    error_message: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

@dataclass
class BatchResults:
    """Results from batch processing a single file"""
    file_id: str
    transcript: str = ""
    entities: Dict[str, Any] = None
    summary: str = ""
    confidence: float = 0.0
    processing_time: float = 0.0
    model_used: str = ""
    language: str = "en"
    word_count: int = 0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}

@dataclass
class BatchJob:
    """A batch processing job containing multiple files"""
    id: str
    name: str
    files: List[BatchFile]
    analysis_mode: str
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_time: datetime = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    results: Dict[str, BatchResults] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.created_time is None:
            self.created_time = datetime.now()
        if self.results is None:
            self.results = {}
        self.total_files = len(self.files)
    
    @property
    def progress_percentage(self) -> int:
        """Calculate overall progress percentage"""
        if self.total_files == 0:
            return 0
        return int((self.completed_files / self.total_files) * 100)
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete"""
        return self.status in [BatchJobStatus.COMPLETED, BatchJobStatus.FAILED, BatchJobStatus.CANCELLED]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get job summary statistics"""
        total_words = sum(result.word_count for result in self.results.values())
        avg_confidence = sum(result.confidence for result in self.results.values()) / len(self.results) if self.results else 0
        
        return {
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'total_words': total_words,
            'average_confidence': avg_confidence,
            'processing_time': (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        }

class BatchProcessor:
    """Manages batch processing of multiple audio/video files"""
    
    def __init__(self, max_concurrent_jobs: int = 2):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.job_queue = queue.Queue()
        self.active_jobs: Dict[str, BatchJob] = {}
        self.completed_jobs: Dict[str, BatchJob] = {}
        self.processing_threads: List[threading.Thread] = []
        self.is_running = False
        self._lock = threading.Lock()
        
        # Progress callbacks
        self.progress_callbacks: List[Callable] = []
        
        logger.info(f"BatchProcessor initialized with max_concurrent_jobs={max_concurrent_jobs}")
    
    def add_progress_callback(self, callback: Callable):
        """Add a callback function for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, job_id: str, file_id: str, progress: int, message: str = ""):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(job_id, file_id, progress, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def create_batch_job(self, files: List[Dict[str, Any]], analysis_mode: str, job_name: str = None) -> str:
        """Create a new batch processing job"""
        
        if not job_name:
            job_name = f"Batch Job {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create BatchFile objects
        batch_files = []
        for file_info in files:
            batch_file = BatchFile(
                id=str(uuid.uuid4())[:8],
                name=file_info['name'],
                size_bytes=file_info['size_bytes'],
                format=file_info['format'],
                temp_path=file_info['temp_path']
            )
            batch_files.append(batch_file)
        
        # Create batch job
        job = BatchJob(
            id=str(uuid.uuid4())[:8],
            name=job_name,
            files=batch_files,
            analysis_mode=analysis_mode
        )
        
        # Add to queue
        self.job_queue.put(job)
        
        logger.info(f"Created batch job {job.id} with {len(batch_files)} files")
        return job.id
    
    def start_processing(self):
        """Start the batch processing system"""
        if self.is_running:
            logger.warning("Batch processor is already running")
            return
        
        self.is_running = True
        
        # Start worker threads
        for i in range(self.max_concurrent_jobs):
            thread = threading.Thread(target=self._worker_thread, name=f"BatchWorker-{i}")
            thread.daemon = True
            thread.start()
            self.processing_threads.append(thread)
        
        logger.info(f"Started batch processor with {self.max_concurrent_jobs} worker threads")
    
    def stop_processing(self):
        """Stop the batch processing system"""
        self.is_running = False
        
        # Cancel all active jobs
        with self._lock:
            for job in self.active_jobs.values():
                if job.status == BatchJobStatus.PROCESSING:
                    job.status = BatchJobStatus.CANCELLED
        
        logger.info("Batch processor stopped")
    
    def _worker_thread(self):
        """Worker thread for processing batch jobs"""
        while self.is_running:
            try:
                # Get job from queue (with timeout to allow checking is_running)
                job = self.job_queue.get(timeout=1.0)
                
                if not self.is_running:
                    # Put job back if we're shutting down
                    self.job_queue.put(job)
                    break
                
                # Process the job
                self._process_batch_job(job)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {e}")
    
    def _process_batch_job(self, job: BatchJob):
        """Process a single batch job"""
        job_id = job.id
        
        try:
            # Move job to active jobs
            with self._lock:
                self.active_jobs[job_id] = job
            
            # Update job status
            job.status = BatchJobStatus.PROCESSING
            job.start_time = datetime.now()
            
            logger.info(f"Starting batch job {job_id} with {job.total_files} files")
            
            # Check if we can use OpenAI batch processing for efficiency
            if openai_batch_processor.can_use_batch_processing(job):
                logger.info(f"Using OpenAI batch processing for job {job_id}")
                self._process_with_openai_batch(job)
            else:
                logger.info(f"Using standard processing for job {job_id}")
                self._process_with_standard_method(job)
            
        except Exception as e:
            # Handle job-level error
            job.status = BatchJobStatus.FAILED
            job.end_time = datetime.now()
            
            with self._lock:
                self.completed_jobs[job_id] = job
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
            
            logger.error(f"Batch job {job_id} failed: {e}")
    
    def _process_with_openai_batch(self, job: BatchJob):
        """Process job using OpenAI batch processing for efficiency"""
        job_id = job.id
        
        try:
            # Step 1: Prepare audio files
            self._notify_progress(job_id, "", 5, "Preparing audio files...")
            audio_files = {}
            
            for file_obj in job.files:
                if not self.is_running or job.status == BatchJobStatus.CANCELLED:
                    return
                
                # Extract audio if needed
                audio_path = file_obj.temp_path
                if file_obj.format.lower() in ['mp4', 'm4a']:
                    audio_path = media.extract_audio(file_obj.temp_path)
                
                audio_files[file_obj.id] = audio_path
            
            # Step 2: Submit transcription batch to OpenAI
            self._notify_progress(job_id, "", 10, "Submitting transcription batch...")
            transcription_batch_id = openai_batch_processor.prepare_transcription_batch(job, audio_files)
            
            if not transcription_batch_id:
                logger.warning(f"Failed to create transcription batch for job {job_id}, falling back to standard processing")
                self._process_with_standard_method(job)
                return
            
            # Step 3: Wait for transcription batch completion
            self._notify_progress(job_id, "", 15, "Processing transcriptions...")
            transcripts = self._wait_for_batch_completion(job_id, f"transcribe_{job_id}", "transcription")
            
            if not transcripts:
                logger.error(f"Transcription batch failed for job {job_id}")
                job.status = BatchJobStatus.FAILED
                return
            
            # Step 4: Submit analysis batch if using Advanced mode
            entities_results = {}
            summaries = {}
            
            if "Advanced" in job.analysis_mode:
                self._notify_progress(job_id, "", 50, "Submitting analysis batch...")
                analysis_batch_id = openai_batch_processor.prepare_analysis_batch(job, transcripts)
                
                if analysis_batch_id:
                    self._notify_progress(job_id, "", 55, "Processing analysis...")
                    analysis_results = self._wait_for_batch_completion(job_id, f"analyze_{job_id}", "analysis")
                    
                    for file_id, (entities, summary) in analysis_results.items():
                        entities_results[file_id] = entities
                        summaries[file_id] = summary
                else:
                    logger.warning(f"Failed to create analysis batch for job {job_id}, using basic analysis")
                    # Fall back to basic analysis
                    for file_id, transcript in transcripts.items():
                        entities_results[file_id] = ner_basic.extract_entities(transcript)
            else:
                # Use basic analysis for all files
                self._notify_progress(job_id, "", 60, "Processing basic analysis...")
                for file_id, transcript in transcripts.items():
                    entities_results[file_id] = ner_basic.extract_entities(transcript)
            
            # Step 5: Compile results
            self._notify_progress(job_id, "", 90, "Compiling results...")
            
            for file_obj in job.files:
                file_id = file_obj.id
                
                if file_id in transcripts:
                    # Create result
                    result = BatchResults(
                        file_id=file_id,
                        transcript=transcripts[file_id],
                        entities=entities_results.get(file_id, {}),
                        summary=summaries.get(file_id, ""),
                        confidence=0.9,  # OpenAI batch processing typically has high confidence
                        processing_time=0.0,  # Will be calculated later
                        model_used="openai-batch",
                        language="en",
                        word_count=len(transcripts[file_id].split()) if transcripts[file_id] else 0
                    )
                    
                    job.results[file_id] = result
                    job.completed_files += 1
                    file_obj.status = BatchJobStatus.COMPLETED
                    
                else:
                    # File failed
                    file_obj.status = BatchJobStatus.FAILED
                    file_obj.error_message = "Failed in batch processing"
                    job.failed_files += 1
                
                file_obj.end_time = datetime.now()
                file_obj.processing_time = (file_obj.end_time - file_obj.start_time).total_seconds() if file_obj.start_time else 0
            
            # Complete job
            job.status = BatchJobStatus.COMPLETED if job.failed_files == 0 else BatchJobStatus.FAILED
            job.end_time = datetime.now()
            
            # Move to completed jobs
            with self._lock:
                self.completed_jobs[job_id] = job
                del self.active_jobs[job_id]
            
            # Cleanup audio files
            for audio_path in audio_files.values():
                if audio_path != file_obj.temp_path:  # Don't delete original temp files
                    utils.cleanup_file(audio_path)
            
            logger.info(f"Completed OpenAI batch job {job_id}: {job.completed_files} successful, {job.failed_files} failed")
            
        except Exception as e:
            logger.error(f"OpenAI batch processing failed for job {job_id}: {e}")
            # Fall back to standard processing
            self._process_with_standard_method(job)
    
    def _process_with_standard_method(self, job: BatchJob):
        """Process job using standard sequential method"""
        job_id = job.id
        
        # Process each file individually
        for file_obj in job.files:
            if not self.is_running or job.status == BatchJobStatus.CANCELLED:
                break
            
            try:
                # Process single file
                result = self._process_single_file(job, file_obj)
                
                # Store result
                job.results[file_obj.id] = result
                job.completed_files += 1
                
                # Update file status
                file_obj.status = BatchJobStatus.COMPLETED
                file_obj.end_time = datetime.now()
                file_obj.processing_time = (file_obj.end_time - file_obj.start_time).total_seconds()
                
                logger.info(f"Completed file {file_obj.name} in job {job_id}")
                
            except Exception as e:
                # Handle file processing error
                file_obj.status = BatchJobStatus.FAILED
                file_obj.error_message = str(e)
                file_obj.end_time = datetime.now()
                job.failed_files += 1
                
                logger.error(f"Failed to process file {file_obj.name} in job {job_id}: {e}")
            
            # Notify progress
            progress = int((job.completed_files + job.failed_files) / job.total_files * 100)
            self._notify_progress(job_id, file_obj.id, progress, f"Processed {file_obj.name}")
        
        # Complete job
        job.status = BatchJobStatus.COMPLETED if job.failed_files == 0 else BatchJobStatus.FAILED
        job.end_time = datetime.now()
        
        # Move to completed jobs
        with self._lock:
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]
        
        logger.info(f"Completed standard batch job {job_id}: {job.completed_files} successful, {job.failed_files} failed")
    
    def _wait_for_batch_completion(self, job_id: str, batch_id: str, batch_type: str, timeout_minutes: int = 30) -> Dict[str, Any]:
        """Wait for OpenAI batch to complete and return results"""
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            if not self.is_running:
                break
            
            # Check batch status
            batch_job = openai_batch_processor.check_batch_status(batch_id)
            
            if not batch_job:
                logger.error(f"Batch job {batch_id} not found")
                break
            
            if batch_job.status == OpenAIBatchStatus.COMPLETED:
                # Process results based on type
                if batch_type == "transcription":
                    return openai_batch_processor.process_transcription_results(batch_job)
                elif batch_type == "analysis":
                    return openai_batch_processor.process_analysis_results(batch_job)
            
            elif batch_job.status in [OpenAIBatchStatus.FAILED, OpenAIBatchStatus.EXPIRED, OpenAIBatchStatus.CANCELLED]:
                logger.error(f"Batch {batch_id} failed: {batch_job.error_message}")
                break
            
            # Update progress
            if batch_type == "transcription":
                progress_base = 15
                progress_range = 35  # 15-50%
            else:  # analysis
                progress_base = 55
                progress_range = 25  # 55-80%
            
            elapsed_ratio = min((time.time() - start_time) / timeout_seconds, 1.0)
            progress = progress_base + int(elapsed_ratio * progress_range)
            self._notify_progress(job_id, "", progress, f"Processing {batch_type}...")
            
            # Wait before next check
            time.sleep(10)  # Check every 10 seconds
        
        logger.warning(f"Batch {batch_id} did not complete within timeout")
        return {}
    
    def _process_single_file(self, job: BatchJob, file_obj: BatchFile) -> BatchResults:
        """Process a single file within a batch job"""
        
        file_obj.status = BatchJobStatus.PROCESSING
        file_obj.start_time = datetime.now()
        file_obj.progress = 0
        
        try:
            # Notify start
            self._notify_progress(job.id, file_obj.id, 0, f"Starting {file_obj.name}")
            
            # Step 1: Media processing (if needed)
            audio_path = file_obj.temp_path
            if file_obj.format.lower() in ['mp4', 'm4a']:
                self._notify_progress(job.id, file_obj.id, 10, "Extracting audio...")
                audio_path = media.extract_audio(file_obj.temp_path)
            
            file_obj.progress = 20
            
            # Step 2: Transcription
            self._notify_progress(job.id, file_obj.id, 20, "Transcribing audio...")
            
            use_api = "Advanced" in job.analysis_mode
            transcript = stt.transcribe(audio_path, use_api=use_api)
            
            if not transcript:
                raise TranscriptionError("Failed to generate transcript")
            
            file_obj.progress = 60
            
            # Step 3: Entity extraction
            entities = {}
            summary = ""
            confidence = 0.8  # Default confidence
            
            if job.analysis_mode == "Basic (spaCy)":
                self._notify_progress(job.id, file_obj.id, 70, "Extracting entities (Basic)...")
                entities = ner_basic.extract_entities(transcript)
                
            elif "Advanced" in job.analysis_mode:
                self._notify_progress(job.id, file_obj.id, 70, "Extracting entities (Advanced)...")
                entities, summary = ner_advanced.extract_entities_advanced(transcript)
            
            file_obj.progress = 90
            
            # Step 4: Create results
            word_count = len(transcript.split()) if transcript else 0
            
            result = BatchResults(
                file_id=file_obj.id,
                transcript=transcript,
                entities=entities,
                summary=summary,
                confidence=confidence,
                processing_time=0.0,  # Will be calculated later
                model_used="whisper" if use_api else "local",
                language="en",
                word_count=word_count
            )
            
            file_obj.progress = 100
            self._notify_progress(job.id, file_obj.id, 100, f"Completed {file_obj.name}")
            
            # Cleanup temporary audio file if it was extracted
            if audio_path != file_obj.temp_path:
                utils.cleanup_file(audio_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_obj.name}: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        
        # Check active jobs
        with self._lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return self._job_to_dict(job)
            
            # Check completed jobs
            if job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
                return self._job_to_dict(job)
        
        return None
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all jobs"""
        all_jobs = {}
        
        with self._lock:
            # Add active jobs
            for job_id, job in self.active_jobs.items():
                all_jobs[job_id] = self._job_to_dict(job)
            
            # Add completed jobs
            for job_id, job in self.completed_jobs.items():
                all_jobs[job_id] = self._job_to_dict(job)
        
        return all_jobs
    
    def _job_to_dict(self, job: BatchJob) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        return {
            'id': job.id,
            'name': job.name,
            'status': job.status.value,
            'analysis_mode': job.analysis_mode,
            'total_files': job.total_files,
            'completed_files': job.completed_files,
            'failed_files': job.failed_files,
            'progress_percentage': job.progress_percentage,
            'created_time': job.created_time.isoformat() if job.created_time else None,
            'start_time': job.start_time.isoformat() if job.start_time else None,
            'end_time': job.end_time.isoformat() if job.end_time else None,
            'files': [self._file_to_dict(f) for f in job.files],
            'summary': job.get_summary() if job.is_complete else None
        }
    
    def _file_to_dict(self, file_obj: BatchFile) -> Dict[str, Any]:
        """Convert file to dictionary for serialization"""
        return {
            'id': file_obj.id,
            'name': file_obj.name,
            'size_bytes': file_obj.size_bytes,
            'format': file_obj.format,
            'status': file_obj.status.value,
            'progress': file_obj.progress,
            'error_message': file_obj.error_message,
            'start_time': file_obj.start_time.isoformat() if file_obj.start_time else None,
            'end_time': file_obj.end_time.isoformat() if file_obj.end_time else None,
            'processing_time': file_obj.processing_time
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job"""
        with self._lock:
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = BatchJobStatus.CANCELLED
                logger.info(f"Cancelled batch job {job_id}")
                return True
        
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a completed job and its results"""
        with self._lock:
            if job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
                
                # Cleanup temporary files
                for file_obj in job.files:
                    if os.path.exists(file_obj.temp_path):
                        utils.cleanup_file(file_obj.temp_path)
                
                del self.completed_jobs[job_id]
                logger.info(f"Deleted batch job {job_id}")
                return True
        
        return False
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, BatchResults]]:
        """Get results for a specific job"""
        with self._lock:
            if job_id in self.completed_jobs:
                return self.completed_jobs[job_id].results
            elif job_id in self.active_jobs:
                return self.active_jobs[job_id].results
        
        return None
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        jobs_to_delete = []
        with self._lock:
            for job_id, job in self.completed_jobs.items():
                if job.end_time and job.end_time < cutoff_time:
                    jobs_to_delete.append(job_id)
        
        for job_id in jobs_to_delete:
            self.delete_job(job_id)
        
        if jobs_to_delete:
            logger.info(f"Cleaned up {len(jobs_to_delete)} old batch jobs")

# Global batch processor instance
batch_processor = BatchProcessor()