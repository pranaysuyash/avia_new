"""
Processing Router and Workflow Engine
Task 2: Advanced Media Processing Pipeline

Intelligent processing workflow selection based on content analysis with routing logic
for different media types, workflow orchestration with parallel processing coordination,
and fallback strategies for processing failures.

This module integrates with the MediaIngestionController and leverages existing
workflow orchestration patterns to provide intelligent media processing routing.

Requirements: 1.2, 1.6, 5.1
Dependencies: MediaIngestionController, WorkflowEngine patterns
"""

import os
import logging
import asyncio
import json
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

# Import existing components
try:
    from media_ingestion_controller import MediaIngestionController, MediaType, IngestionResult
    from workflow_orchestration_system import WorkflowEngine, WorkflowNode, NodeType, NodeStatus, WorkflowStatus
    from enterprise_workflow_management import WorkflowPriority, WorkflowCategory, ExecutionMode
except ImportError as e:
    logging.warning(f"Import warning: {e}, using fallback implementations")
    
    # Fallback enums and classes
    class MediaType(Enum):
        AUDIO = "audio"
        VIDEO = "video"
        IMAGE = "image"
        DOCUMENT = "document"
        UNKNOWN = "unknown"
    
    class WorkflowStatus(Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    
    class WorkflowPriority(Enum):
        LOW = "low"
        NORMAL = "normal"
        HIGH = "high"
        CRITICAL = "critical"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingStrategy(Enum):
    """Processing strategy types"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class ContentComplexity(Enum):
    """Content complexity levels for processing decisions"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class ProcessingMode(Enum):
    """Processing execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


@dataclass
class ContentAnalysis:
    """Content analysis results for routing decisions"""
    media_type: MediaType
    file_size_mb: float
    duration_seconds: float
    complexity: ContentComplexity
    quality_score: float
    content_features: Dict[str, Any] = field(default_factory=dict)
    processing_requirements: List[str] = field(default_factory=list)
    estimated_processing_time: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingRoute:
    """Processing route definition"""
    route_id: str
    name: str
    description: str
    media_types: List[MediaType]
    complexity_levels: List[ContentComplexity]
    processing_steps: List[str]
    strategy: ProcessingStrategy
    mode: ProcessingMode
    priority: WorkflowPriority
    estimated_duration: float
    resource_cost: float
    fallback_routes: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingJob:
    """Processing job definition"""
    job_id: str
    input_file: str
    content_analysis: ContentAnalysis
    selected_route: ProcessingRoute
    workflow_id: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Processing result with comprehensive details"""
    job_id: str
    success: bool
    output_files: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    route_used: Optional[str] = None
    fallbacks_used: List[str] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessingRouterWorkflowEngine:
    """
    Intelligent processing router and workflow engine that provides:
    - Content-based routing decisions
    - Workflow orchestration with parallel processing
    - Fallback strategies for processing failures
    - Resource optimization and load balancing
    """
    
    def __init__(self, 
                 media_ingestion_controller: Optional[Any] = None,
                 max_concurrent_jobs: int = 4,
                 temp_dir: Optional[str] = None):
        """
        Initialize the processing router and workflow engine
        
        Args:
            media_ingestion_controller: MediaIngestionController instance
            max_concurrent_jobs: Maximum concurrent processing jobs
            temp_dir: Temporary directory for processing
        """
        self.media_controller = media_ingestion_controller
        self.max_concurrent_jobs = max_concurrent_jobs
        self.temp_dir = temp_dir or "/tmp/processing"
        
        # Core components
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: Dict[str, ProcessingJob] = {}
        self.processing_routes: Dict[str, ProcessingRoute] = {}
        self.job_queue: List[ProcessingJob] = []
        self.job_lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'average_processing_time': 0.0,
            'resource_utilization': 0.0
        }
        
        # Initialize default routes
        self._initialize_default_routes()
        
        # Start background processing
        self._start_background_processor()
        
        logger.info(f"ProcessingRouterWorkflowEngine initialized with {max_concurrent_jobs} workers")
    
    def _initialize_default_routes(self):
        """Initialize default processing routes for different content types"""
        
        # Audio processing routes
        self.processing_routes["audio_basic"] = ProcessingRoute(
            route_id="audio_basic",
            name="Basic Audio Processing",
            description="Basic audio enhancement and transcription",
            media_types=[MediaType.AUDIO],
            complexity_levels=[ContentComplexity.SIMPLE, ContentComplexity.MODERATE],
            processing_steps=["audio_enhancement", "transcription", "quality_check"],
            strategy=ProcessingStrategy.BASIC,
            mode=ProcessingMode.SEQUENTIAL,
            priority=WorkflowPriority.NORMAL,
            estimated_duration=60.0,
            resource_cost=1.0,
            fallback_routes=["audio_minimal"]
        )
        
        self.processing_routes["audio_professional"] = ProcessingRoute(
            route_id="audio_professional",
            name="Professional Audio Processing",
            description="Advanced audio processing with speaker diarization and NLP",
            media_types=[MediaType.AUDIO],
            complexity_levels=[ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX],
            processing_steps=[
                "advanced_audio_enhancement", "noise_reduction", "speaker_diarization",
                "advanced_transcription", "nlp_analysis", "quality_validation"
            ],
            strategy=ProcessingStrategy.PROFESSIONAL,
            mode=ProcessingMode.PARALLEL,
            priority=WorkflowPriority.HIGH,
            estimated_duration=180.0,
            resource_cost=3.0,
            fallback_routes=["audio_basic", "audio_minimal"]
        )
        
        # Video processing routes
        self.processing_routes["video_basic"] = ProcessingRoute(
            route_id="video_basic",
            name="Basic Video Processing",
            description="Basic video analysis and transcription",
            media_types=[MediaType.VIDEO],
            complexity_levels=[ContentComplexity.SIMPLE, ContentComplexity.MODERATE],
            processing_steps=["video_analysis", "audio_extraction", "transcription", "quality_check"],
            strategy=ProcessingStrategy.BASIC,
            mode=ProcessingMode.SEQUENTIAL,
            priority=WorkflowPriority.NORMAL,
            estimated_duration=120.0,
            resource_cost=2.0,
            fallback_routes=["video_minimal"]
        )
        
        self.processing_routes["video_professional"] = ProcessingRoute(
            route_id="video_professional",
            name="Professional Video Processing",
            description="Advanced video processing with scene detection and object recognition",
            media_types=[MediaType.VIDEO],
            complexity_levels=[ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX],
            processing_steps=[
                "scene_detection", "keyframe_extraction", "object_recognition",
                "advanced_audio_processing", "advanced_transcription", "content_analysis",
                "quality_validation"
            ],
            strategy=ProcessingStrategy.PROFESSIONAL,
            mode=ProcessingMode.HYBRID,
            priority=WorkflowPriority.HIGH,
            estimated_duration=300.0,
            resource_cost=5.0,
            fallback_routes=["video_basic", "video_minimal"]
        )
        
        # Document processing routes
        self.processing_routes["document_basic"] = ProcessingRoute(
            route_id="document_basic",
            name="Basic Document Processing",
            description="OCR and basic text extraction",
            media_types=[MediaType.DOCUMENT],
            complexity_levels=[ContentComplexity.SIMPLE, ContentComplexity.MODERATE],
            processing_steps=["ocr", "text_extraction", "basic_nlp", "quality_check"],
            strategy=ProcessingStrategy.BASIC,
            mode=ProcessingMode.SEQUENTIAL,
            priority=WorkflowPriority.NORMAL,
            estimated_duration=30.0,
            resource_cost=1.0,
            fallback_routes=["document_minimal"]
        )
        
        # Fallback minimal routes
        self.processing_routes["audio_minimal"] = ProcessingRoute(
            route_id="audio_minimal",
            name="Minimal Audio Processing",
            description="Basic audio validation and format conversion",
            media_types=[MediaType.AUDIO],
            complexity_levels=[ContentComplexity.SIMPLE],
            processing_steps=["format_validation", "basic_conversion"],
            strategy=ProcessingStrategy.BASIC,
            mode=ProcessingMode.SEQUENTIAL,
            priority=WorkflowPriority.LOW,
            estimated_duration=15.0,
            resource_cost=0.5
        )
        
        logger.info(f"Initialized {len(self.processing_routes)} default processing routes")
    
    async def analyze_content(self, file_path: str) -> ContentAnalysis:
        """
        Analyze content to determine processing requirements
        
        Args:
            file_path: Path to the media file
            
        Returns:
            ContentAnalysis with routing information
        """
        try:
            # Get basic file information
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            file_ext = Path(file_path).suffix.lower()
            
            # Determine media type
            media_type = self._determine_media_type(file_ext)
            
            # Analyze content complexity
            complexity = await self._analyze_complexity(file_path, media_type, file_size)
            
            # Get duration for media files
            duration = await self._get_media_duration(file_path, media_type)
            
            # Calculate quality score
            quality_score = await self._assess_quality(file_path, media_type)
            
            # Determine processing requirements
            processing_requirements = self._determine_processing_requirements(
                media_type, complexity, file_size, duration
            )
            
            # Estimate processing time
            estimated_time = self._estimate_processing_time(
                media_type, complexity, file_size, duration
            )
            
            # Calculate resource requirements
            resource_requirements = self._calculate_resource_requirements(
                media_type, complexity, file_size
            )
            
            analysis = ContentAnalysis(
                media_type=media_type,
                file_size_mb=file_size,
                duration_seconds=duration,
                complexity=complexity,
                quality_score=quality_score,
                processing_requirements=processing_requirements,
                estimated_processing_time=estimated_time,
                resource_requirements=resource_requirements,
                content_features={
                    'file_extension': file_ext,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Content analysis completed: {media_type.value}, complexity: {complexity.value}")
            return analysis
            
        except Exception as e:
            logger.error(f"Content analysis failed for {file_path}: {e}")
            # Return minimal analysis as fallback
            return ContentAnalysis(
                media_type=MediaType.UNKNOWN,
                file_size_mb=file_size if 'file_size' in locals() else 0.0,
                duration_seconds=0.0,
                complexity=ContentComplexity.SIMPLE,
                quality_score=0.5,
                processing_requirements=["basic_validation"],
                estimated_processing_time=30.0,
                resource_requirements={'cpu': 1, 'memory': 512}
            )
    
    def select_processing_route(self, content_analysis: ContentAnalysis) -> ProcessingRoute:
        """
        Select optimal processing route based on content analysis
        
        Args:
            content_analysis: Content analysis results
            
        Returns:
            Selected ProcessingRoute
        """
        try:
            # Find matching routes
            candidate_routes = []
            
            for route in self.processing_routes.values():
                if (content_analysis.media_type in route.media_types and
                    content_analysis.complexity in route.complexity_levels):
                    candidate_routes.append(route)
            
            if not candidate_routes:
                # Fallback to minimal processing
                fallback_route_id = f"{content_analysis.media_type.value}_minimal"
                if fallback_route_id in self.processing_routes:
                    selected_route = self.processing_routes[fallback_route_id]
                    logger.warning(f"Using fallback route: {fallback_route_id}")
                    return selected_route
                else:
                    # Create emergency fallback
                    return self._create_emergency_fallback_route(content_analysis.media_type)
            
            # Select best route based on complexity and quality requirements
            if content_analysis.complexity in [ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX]:
                # Prefer professional routes for complex content
                professional_routes = [r for r in candidate_routes if r.strategy == ProcessingStrategy.PROFESSIONAL]
                if professional_routes:
                    selected_route = professional_routes[0]
                else:
                    selected_route = candidate_routes[0]
            else:
                # Prefer basic routes for simple content
                basic_routes = [r for r in candidate_routes if r.strategy == ProcessingStrategy.BASIC]
                if basic_routes:
                    selected_route = basic_routes[0]
                else:
                    selected_route = candidate_routes[0]
            
            logger.info(f"Selected processing route: {selected_route.name}")
            return selected_route
            
        except Exception as e:
            logger.error(f"Route selection failed: {e}")
            return self._create_emergency_fallback_route(content_analysis.media_type)
    
    async def process_media(self, file_path: str, 
                          custom_route: Optional[str] = None,
                          priority: WorkflowPriority = WorkflowPriority.NORMAL) -> str:
        """
        Process media file through intelligent routing
        
        Args:
            file_path: Path to media file
            custom_route: Optional custom route ID
            priority: Processing priority
            
        Returns:
            Job ID for tracking
        """
        try:
            # Analyze content
            content_analysis = await self.analyze_content(file_path)
            
            # Select processing route
            if custom_route and custom_route in self.processing_routes:
                selected_route = self.processing_routes[custom_route]
                logger.info(f"Using custom route: {custom_route}")
            else:
                selected_route = self.select_processing_route(content_analysis)
            
            # Create processing job
            job_id = str(uuid.uuid4())
            job = ProcessingJob(
                job_id=job_id,
                input_file=file_path,
                content_analysis=content_analysis,
                selected_route=selected_route,
                metadata={
                    'priority': priority.value,
                    'created_by': 'processing_router',
                    'route_selection_reason': 'content_analysis'
                }
            )
            
            # Add to queue
            with self.job_lock:
                self.job_queue.append(job)
                self.active_jobs[job_id] = job
            
            logger.info(f"Created processing job {job_id} with route {selected_route.name}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create processing job for {file_path}: {e}")
            raise
    
    def _start_background_processor(self):
        """Start background job processor"""
        def process_jobs():
            while True:
                try:
                    with self.job_lock:
                        if self.job_queue and len([j for j in self.active_jobs.values() 
                                                 if j.status == WorkflowStatus.RUNNING]) < self.max_concurrent_jobs:
                            job = self.job_queue.pop(0)
                            if job.status == WorkflowStatus.PENDING:
                                job.status = WorkflowStatus.RUNNING
                                job.started_at = datetime.now()
                                
                                # Submit job for processing
                                future = self.executor.submit(self._execute_job, job)
                                job.metadata['future'] = future
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    logger.error(f"Background processor error: {e}")
                    time.sleep(5)  # Wait longer on error
        
        # Start background thread
        processor_thread = threading.Thread(target=process_jobs, daemon=True)
        processor_thread.start()
        logger.info("Background job processor started")
    
    def _execute_job(self, job: ProcessingJob) -> ProcessingResult:
        """
        Execute a processing job
        
        Args:
            job: ProcessingJob to execute
            
        Returns:
            ProcessingResult
        """
        start_time = time.time()
        result = ProcessingResult(job_id=job.job_id, success=False)
        
        try:
            logger.info(f"Executing job {job.job_id} with route {job.selected_route.name}")
            
            # Execute processing steps
            for i, step in enumerate(job.selected_route.processing_steps):
                try:
                    step_result = self._execute_processing_step(step, job)
                    job.progress = (i + 1) / len(job.selected_route.processing_steps)
                    
                    if not step_result.get('success', False):
                        raise Exception(f"Step {step} failed: {step_result.get('error', 'Unknown error')}")
                    
                    # Store step results
                    job.results[step] = step_result
                    
                except Exception as step_error:
                    logger.warning(f"Step {step} failed for job {job.job_id}: {step_error}")
                    
                    # Try fallback routes
                    if job.selected_route.fallback_routes:
                        fallback_success = self._try_fallback_routes(job, step_error)
                        if fallback_success:
                            break
                    
                    # If no fallback worked, fail the job
                    raise step_error
            
            # Job completed successfully
            job.status = WorkflowStatus.COMPLETED
            job.completed_at = datetime.now()
            result.success = True
            result.processing_time = time.time() - start_time
            result.route_used = job.selected_route.route_id
            result.output_files = job.results.get('output_files', [])
            
            logger.info(f"Job {job.job_id} completed successfully in {result.processing_time:.2f}s")
            
        except Exception as e:
            job.status = WorkflowStatus.FAILED
            job.completed_at = datetime.now()
            job.errors.append(str(e))
            result.errors.append(str(e))
            result.processing_time = time.time() - start_time
            
            logger.error(f"Job {job.job_id} failed: {e}")
        
        finally:
            # Move job to completed
            with self.job_lock:
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                self.completed_jobs[job.job_id] = job
            
            # Update performance metrics
            self._update_performance_metrics(result)
        
        return result
    
    def _execute_processing_step(self, step: str, job: ProcessingJob) -> Dict[str, Any]:
        """
        Execute a single processing step
        
        Args:
            step: Processing step name
            job: ProcessingJob context
            
        Returns:
            Step execution result
        """
        try:
            logger.debug(f"Executing step {step} for job {job.job_id}")
            
            # Simulate processing steps (replace with actual implementations)
            if step == "audio_enhancement":
                return self._simulate_audio_enhancement(job)
            elif step == "transcription":
                return self._simulate_transcription(job)
            elif step == "video_analysis":
                return self._simulate_video_analysis(job)
            elif step == "quality_check":
                return self._simulate_quality_check(job)
            elif step == "format_validation":
                return self._simulate_format_validation(job)
            else:
                # Generic step simulation
                time.sleep(1)  # Simulate processing time
                return {
                    'success': True,
                    'step': step,
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Step {step} completed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'step': step,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _simulate_audio_enhancement(self, job: ProcessingJob) -> Dict[str, Any]:
        """Simulate audio enhancement step"""
        time.sleep(2)  # Simulate processing
        return {
            'success': True,
            'step': 'audio_enhancement',
            'enhancements_applied': ['noise_reduction', 'normalization'],
            'quality_improvement': 0.15,
            'timestamp': datetime.now().isoformat()
        }
    
    def _simulate_transcription(self, job: ProcessingJob) -> Dict[str, Any]:
        """Simulate transcription step"""
        time.sleep(3)  # Simulate processing
        return {
            'success': True,
            'step': 'transcription',
            'transcript': 'Sample transcription text...',
            'confidence': 0.92,
            'word_count': 150,
            'timestamp': datetime.now().isoformat()
        }
    
    def _simulate_video_analysis(self, job: ProcessingJob) -> Dict[str, Any]:
        """Simulate video analysis step"""
        time.sleep(4)  # Simulate processing
        return {
            'success': True,
            'step': 'video_analysis',
            'scenes_detected': 5,
            'keyframes_extracted': 15,
            'resolution': '1920x1080',
            'timestamp': datetime.now().isoformat()
        }
    
    def _simulate_quality_check(self, job: ProcessingJob) -> Dict[str, Any]:
        """Simulate quality check step"""
        time.sleep(1)  # Simulate processing
        return {
            'success': True,
            'step': 'quality_check',
            'quality_score': 0.87,
            'issues_found': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _simulate_format_validation(self, job: ProcessingJob) -> Dict[str, Any]:
        """Simulate format validation step"""
        time.sleep(0.5)  # Simulate processing
        return {
            'success': True,
            'step': 'format_validation',
            'format_valid': True,
            'format_detected': job.content_analysis.content_features.get('file_extension', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
    
    def _try_fallback_routes(self, job: ProcessingJob, error: Exception) -> bool:
        """
        Try fallback routes when primary route fails
        
        Args:
            job: Failed ProcessingJob
            error: Error that caused failure
            
        Returns:
            True if fallback succeeded
        """
        for fallback_route_id in job.selected_route.fallback_routes:
            if fallback_route_id in self.processing_routes:
                try:
                    logger.info(f"Trying fallback route {fallback_route_id} for job {job.job_id}")
                    
                    # Switch to fallback route
                    fallback_route = self.processing_routes[fallback_route_id]
                    job.selected_route = fallback_route
                    job.metadata['fallback_used'] = fallback_route_id
                    job.metadata['original_error'] = str(error)
                    
                    # Reset progress and continue
                    job.progress = 0.0
                    return True
                    
                except Exception as fallback_error:
                    logger.warning(f"Fallback route {fallback_route_id} also failed: {fallback_error}")
                    continue
        
        return False
    
    def _determine_media_type(self, file_ext: str) -> MediaType:
        """Determine media type from file extension"""
        audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        doc_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf'}
        
        if file_ext in audio_exts:
            return MediaType.AUDIO
        elif file_ext in video_exts:
            return MediaType.VIDEO
        elif file_ext in image_exts:
            return MediaType.IMAGE
        elif file_ext in doc_exts:
            return MediaType.DOCUMENT
        else:
            return MediaType.UNKNOWN
    
    async def _analyze_complexity(self, file_path: str, media_type: MediaType, file_size: float) -> ContentComplexity:
        """Analyze content complexity"""
        try:
            # Simple heuristic based on file size and type
            if media_type == MediaType.AUDIO:
                if file_size < 10:
                    return ContentComplexity.SIMPLE
                elif file_size < 50:
                    return ContentComplexity.MODERATE
                elif file_size < 200:
                    return ContentComplexity.COMPLEX
                else:
                    return ContentComplexity.VERY_COMPLEX
            
            elif media_type == MediaType.VIDEO:
                if file_size < 50:
                    return ContentComplexity.SIMPLE
                elif file_size < 200:
                    return ContentComplexity.MODERATE
                elif file_size < 1000:
                    return ContentComplexity.COMPLEX
                else:
                    return ContentComplexity.VERY_COMPLEX
            
            else:
                # Default for other types
                if file_size < 5:
                    return ContentComplexity.SIMPLE
                elif file_size < 20:
                    return ContentComplexity.MODERATE
                else:
                    return ContentComplexity.COMPLEX
                    
        except Exception:
            return ContentComplexity.SIMPLE
    
    async def _get_media_duration(self, file_path: str, media_type: MediaType) -> float:
        """Get media duration in seconds"""
        try:
            if media_type in [MediaType.AUDIO, MediaType.VIDEO]:
                # Try to get duration using ffmpeg if available
                try:
                    import ffmpeg
                    probe = ffmpeg.probe(file_path)
                    duration = float(probe['format']['duration'])
                    return duration
                except:
                    pass
            
            # Fallback estimation based on file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if media_type == MediaType.AUDIO:
                return file_size_mb * 8  # Rough estimate: 8 seconds per MB
            elif media_type == MediaType.VIDEO:
                return file_size_mb * 2  # Rough estimate: 2 seconds per MB
            
            return 0.0
            
        except Exception:
            return 0.0
    
    async def _assess_quality(self, file_path: str, media_type: MediaType) -> float:
        """Assess content quality (0.0 to 1.0)"""
        try:
            # Simple quality assessment based on file size and type
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            if media_type == MediaType.AUDIO:
                # Higher bitrate generally means better quality
                if file_size_mb > 50:
                    return 0.9
                elif file_size_mb > 20:
                    return 0.8
                elif file_size_mb > 5:
                    return 0.7
                else:
                    return 0.6
            
            elif media_type == MediaType.VIDEO:
                # Video quality assessment
                if file_size_mb > 500:
                    return 0.9
                elif file_size_mb > 100:
                    return 0.8
                elif file_size_mb > 50:
                    return 0.7
                else:
                    return 0.6
            
            return 0.7  # Default quality score
            
        except Exception:
            return 0.5
    
    def _determine_processing_requirements(self, media_type: MediaType, 
                                         complexity: ContentComplexity,
                                         file_size: float, duration: float) -> List[str]:
        """Determine processing requirements based on content analysis"""
        requirements = ["format_validation"]
        
        if media_type == MediaType.AUDIO:
            requirements.extend(["audio_enhancement", "transcription"])
            if complexity in [ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX]:
                requirements.extend(["speaker_diarization", "advanced_nlp"])
        
        elif media_type == MediaType.VIDEO:
            requirements.extend(["video_analysis", "audio_extraction", "transcription"])
            if complexity in [ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX]:
                requirements.extend(["scene_detection", "object_recognition"])
        
        elif media_type == MediaType.DOCUMENT:
            requirements.extend(["ocr", "text_extraction"])
            if complexity != ContentComplexity.SIMPLE:
                requirements.append("advanced_nlp")
        
        requirements.append("quality_check")
        return requirements
    
    def _estimate_processing_time(self, media_type: MediaType, 
                                complexity: ContentComplexity,
                                file_size: float, duration: float) -> float:
        """Estimate processing time in seconds"""
        base_time = 30.0  # Base processing time
        
        # Adjust for media type
        if media_type == MediaType.VIDEO:
            base_time *= 2
        elif media_type == MediaType.AUDIO:
            base_time *= 1.5
        
        # Adjust for complexity
        complexity_multipliers = {
            ContentComplexity.SIMPLE: 1.0,
            ContentComplexity.MODERATE: 1.5,
            ContentComplexity.COMPLEX: 2.5,
            ContentComplexity.VERY_COMPLEX: 4.0
        }
        base_time *= complexity_multipliers.get(complexity, 1.0)
        
        # Adjust for file size
        base_time += file_size * 0.5  # 0.5 seconds per MB
        
        # Adjust for duration
        if duration > 0:
            base_time += duration * 0.1  # 0.1 seconds per second of media
        
        return base_time
    
    def _calculate_resource_requirements(self, media_type: MediaType,
                                       complexity: ContentComplexity,
                                       file_size: float) -> Dict[str, Any]:
        """Calculate resource requirements"""
        base_cpu = 1
        base_memory = 512  # MB
        
        # Adjust for media type
        if media_type == MediaType.VIDEO:
            base_cpu = 2
            base_memory = 1024
        elif media_type == MediaType.AUDIO:
            base_cpu = 1
            base_memory = 512
        
        # Adjust for complexity
        complexity_multipliers = {
            ContentComplexity.SIMPLE: 1.0,
            ContentComplexity.MODERATE: 1.5,
            ContentComplexity.COMPLEX: 2.0,
            ContentComplexity.VERY_COMPLEX: 3.0
        }
        multiplier = complexity_multipliers.get(complexity, 1.0)
        
        return {
            'cpu': int(base_cpu * multiplier),
            'memory': int(base_memory * multiplier),
            'disk': int(file_size * 2),  # 2x file size for temporary files
            'gpu': 1 if complexity in [ContentComplexity.COMPLEX, ContentComplexity.VERY_COMPLEX] else 0
        }
    
    def _create_emergency_fallback_route(self, media_type: MediaType) -> ProcessingRoute:
        """Create emergency fallback route"""
        return ProcessingRoute(
            route_id=f"emergency_{media_type.value}",
            name=f"Emergency {media_type.value.title()} Processing",
            description="Emergency fallback processing route",
            media_types=[media_type],
            complexity_levels=[ContentComplexity.SIMPLE],
            processing_steps=["format_validation"],
            strategy=ProcessingStrategy.BASIC,
            mode=ProcessingMode.SEQUENTIAL,
            priority=WorkflowPriority.LOW,
            estimated_duration=10.0,
            resource_cost=0.1
        )
    
    def _update_performance_metrics(self, result: ProcessingResult):
        """Update performance metrics"""
        self.performance_metrics['total_jobs'] += 1
        
        if result.success:
            self.performance_metrics['successful_jobs'] += 1
        else:
            self.performance_metrics['failed_jobs'] += 1
        
        # Update average processing time
        total_jobs = self.performance_metrics['total_jobs']
        current_avg = self.performance_metrics['average_processing_time']
        new_avg = ((current_avg * (total_jobs - 1)) + result.processing_time) / total_jobs
        self.performance_metrics['average_processing_time'] = new_avg
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and progress"""
        job = self.active_jobs.get(job_id) or self.completed_jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'status': job.status.value,
            'progress': job.progress,
            'route': job.selected_route.name,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'errors': job.errors,
            'results': job.results
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.performance_metrics,
            'active_jobs': len(self.active_jobs),
            'queued_jobs': len(self.job_queue),
            'available_routes': len(self.processing_routes)
        }
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up ProcessingRouterWorkflowEngine...")
        
        # Cancel active jobs
        with self.job_lock:
            for job in self.active_jobs.values():
                if job.status == WorkflowStatus.RUNNING:
                    job.status = WorkflowStatus.CANCELLED
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("ProcessingRouterWorkflowEngine cleanup completed")


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_processing_router():
        """Test the processing router and workflow engine"""
        
        # Initialize the router
        router = ProcessingRouterWorkflowEngine(max_concurrent_jobs=2)
        
        print("🚀 ProcessingRouterWorkflowEngine Test Started")
        print(f"📊 Available routes: {len(router.processing_routes)}")
        
        # Test content analysis
        test_file = "test_audio.mp3"  # This would be a real file in practice
        
        try:
            # Simulate file for testing
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp.write(b"fake audio data")
                test_file = tmp.name
            
            print(f"📁 Analyzing test file: {test_file}")
            
            # Analyze content
            analysis = await router.analyze_content(test_file)
            print(f"📋 Content Analysis:")
            print(f"   Media Type: {analysis.media_type.value}")
            print(f"   Complexity: {analysis.complexity.value}")
            print(f"   File Size: {analysis.file_size_mb:.2f} MB")
            print(f"   Estimated Processing Time: {analysis.estimated_processing_time:.1f}s")
            
            # Select route
            route = router.select_processing_route(analysis)
            print(f"🛤️  Selected Route: {route.name}")
            print(f"   Strategy: {route.strategy.value}")
            print(f"   Steps: {route.processing_steps}")
            
            # Process media
            job_id = await router.process_media(test_file)
            print(f"⚙️  Created processing job: {job_id}")
            
            # Monitor progress
            print("📈 Monitoring progress...")
            while True:
                status = router.get_job_status(job_id)
                if status:
                    print(f"   Status: {status['status']}, Progress: {status['progress']:.1%}")
                    if status['status'] in ['completed', 'failed', 'cancelled']:
                        break
                await asyncio.sleep(1)
            
            # Show final results
            final_status = router.get_job_status(job_id)
            if final_status:
                print(f"✅ Job completed with status: {final_status['status']}")
                if final_status['errors']:
                    print(f"❌ Errors: {final_status['errors']}")
            
            # Show performance metrics
            metrics = router.get_performance_metrics()
            print(f"📊 Performance Metrics:")
            print(f"   Total Jobs: {metrics['total_jobs']}")
            print(f"   Success Rate: {metrics['successful_jobs']}/{metrics['total_jobs']}")
            print(f"   Average Processing Time: {metrics['average_processing_time']:.2f}s")
            
            # Cleanup
            os.unlink(test_file)
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            await router.cleanup()
            print("🧹 Cleanup completed")
    
    # Run the test
    asyncio.run(test_processing_router())