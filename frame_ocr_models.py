"""
Frame OCR Data Models and Database Schema

This module provides comprehensive data models for the Frame OCR Indexing System
with support for validation, serialization, data lineage tracking, and multi-tenancy.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from uuid import uuid4
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """OCR job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class SamplingStrategy(Enum):
    """Frame sampling strategy enumeration"""
    TIME_BASED = "time_based"
    KEYFRAME = "keyframe"
    SCENE_CHANGE = "scene_change"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class OCREngine(Enum):
    """OCR engine enumeration"""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLE_OCR = "paddle_ocr"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"
    AZURE_COGNITIVE = "azure_cognitive"


class RegionType(Enum):
    """Text region classification"""
    LOWER_THIRD = "lower_third"
    TITLE = "title"
    WATERMARK = "watermark"
    CAPTION = "caption"
    BANNER = "banner"
    LOGO = "logo"
    UNKNOWN = "unknown"


@dataclass
class BoundingBox:
    """Bounding box for detected text regions"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    region_type: RegionType = RegionType.UNKNOWN
    
    def __post_init__(self):
        """Validate bounding box parameters"""
        if self.x < 0 or self.y < 0:
            raise ValueError("Bounding box coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Bounding box dimensions must be positive")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def area(self) -> int:
        """Calculate bounding box area"""
        return self.width * self.height
    
    def center(self) -> tuple[int, int]:
        """Get center coordinates"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'region_type': self.region_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BoundingBox':
        """Create from dictionary"""
        return cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            confidence=data['confidence'],
            region_type=RegionType(data.get('region_type', 'unknown'))
        )


@dataclass
class TextSegment:
    """Individual text segment with temporal tracking"""
    segment_id: str = field(default_factory=lambda: str(uuid4()))
    text: str = ""
    confidence: float = 0.0
    language: str = "en"
    bounding_box: Optional[BoundingBox] = None
    stability_score: float = 0.0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    occurrence_count: int = 1
    region_classification: RegionType = RegionType.UNKNOWN
    
    def __post_init__(self):
        """Validate text segment parameters"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.stability_score <= 1.0:
            raise ValueError("Stability score must be between 0.0 and 1.0")
        if self.occurrence_count < 1:
            raise ValueError("Occurrence count must be positive")
        if not self.first_seen:
            self.first_seen = datetime.now(timezone.utc)
        if not self.last_seen:
            self.last_seen = self.first_seen
    
    def update_occurrence(self, timestamp: datetime, confidence: float):
        """Update segment with new occurrence"""
        self.occurrence_count += 1
        self.last_seen = timestamp
        # Update confidence using weighted average
        self.confidence = (self.confidence + confidence) / 2
        # Update stability score based on temporal consistency
        time_span = (self.last_seen - self.first_seen).total_seconds()
        self.stability_score = min(1.0, self.occurrence_count / max(1, time_span / 60))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'segment_id': self.segment_id,
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'bounding_box': self.bounding_box.to_dict() if self.bounding_box else None,
            'stability_score': self.stability_score,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'occurrence_count': self.occurrence_count,
            'region_classification': self.region_classification.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextSegment':
        """Create from dictionary"""
        segment = cls(
            segment_id=data['segment_id'],
            text=data['text'],
            confidence=data['confidence'],
            language=data['language'],
            stability_score=data['stability_score'],
            occurrence_count=data['occurrence_count'],
            region_classification=RegionType(data.get('region_classification', 'unknown'))
        )
        
        if data.get('bounding_box'):
            segment.bounding_box = BoundingBox.from_dict(data['bounding_box'])
        
        if data.get('first_seen'):
            segment.first_seen = datetime.fromisoformat(data['first_seen'])
        
        if data.get('last_seen'):
            segment.last_seen = datetime.fromisoformat(data['last_seen'])
        
        return segment


@dataclass
class OCRJobConfig:
    """Configuration for OCR processing jobs"""
    sampling_strategy: SamplingStrategy = SamplingStrategy.TIME_BASED
    sampling_interval: float = 1.0  # seconds
    max_frames: int = 1000
    ocr_engines: List[OCREngine] = field(default_factory=lambda: [OCREngine.TESSERACT])
    confidence_threshold: float = 0.5
    languages: List[str] = field(default_factory=lambda: ["en"])
    preprocessing_enabled: bool = True
    region_detection_enabled: bool = True
    temporal_consolidation_enabled: bool = True
    stability_threshold: float = 0.7
    max_processing_time: int = 3600  # seconds
    cost_limit: Optional[float] = None
    priority: int = 5  # 1-10 scale
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.sampling_interval <= 0:
            raise ValueError("Sampling interval must be positive")
        if self.max_frames <= 0:
            raise ValueError("Max frames must be positive")
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.stability_threshold <= 1.0:
            raise ValueError("Stability threshold must be between 0.0 and 1.0")
        if not 1 <= self.priority <= 10:
            raise ValueError("Priority must be between 1 and 10")
        if not self.ocr_engines:
            raise ValueError("At least one OCR engine must be specified")
        if not self.languages:
            raise ValueError("At least one language must be specified")
    
    def estimate_cost(self, video_duration: float) -> float:
        """Estimate processing cost based on configuration"""
        estimated_frames = min(
            self.max_frames,
            int(video_duration / self.sampling_interval)
        )
        
        # Base cost per frame (simplified model)
        base_cost_per_frame = 0.001
        engine_multiplier = len(self.ocr_engines)
        preprocessing_multiplier = 1.2 if self.preprocessing_enabled else 1.0
        
        return estimated_frames * base_cost_per_frame * engine_multiplier * preprocessing_multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'sampling_strategy': self.sampling_strategy.value,
            'sampling_interval': self.sampling_interval,
            'max_frames': self.max_frames,
            'ocr_engines': [engine.value for engine in self.ocr_engines],
            'confidence_threshold': self.confidence_threshold,
            'languages': self.languages,
            'preprocessing_enabled': self.preprocessing_enabled,
            'region_detection_enabled': self.region_detection_enabled,
            'temporal_consolidation_enabled': self.temporal_consolidation_enabled,
            'stability_threshold': self.stability_threshold,
            'max_processing_time': self.max_processing_time,
            'cost_limit': self.cost_limit,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OCRJobConfig':
        """Create from dictionary"""
        return cls(
            sampling_strategy=SamplingStrategy(data['sampling_strategy']),
            sampling_interval=data['sampling_interval'],
            max_frames=data['max_frames'],
            ocr_engines=[OCREngine(engine) for engine in data['ocr_engines']],
            confidence_threshold=data['confidence_threshold'],
            languages=data['languages'],
            preprocessing_enabled=data['preprocessing_enabled'],
            region_detection_enabled=data['region_detection_enabled'],
            temporal_consolidation_enabled=data['temporal_consolidation_enabled'],
            stability_threshold=data['stability_threshold'],
            max_processing_time=data['max_processing_time'],
            cost_limit=data.get('cost_limit'),
            priority=data['priority']
        )


@dataclass
class FrameOCRResult:
    """OCR result for a single frame"""
    result_id: str = field(default_factory=lambda: str(uuid4()))
    job_id: str = ""
    video_id: str = ""
    tenant_id: str = ""
    timestamp: float = 0.0
    frame_number: int = 0
    text: str = ""
    confidence: float = 0.0
    language: str = "en"
    bounding_boxes: List[BoundingBox] = field(default_factory=list)
    text_segments: List[TextSegment] = field(default_factory=list)
    ocr_engine: OCREngine = OCREngine.TESSERACT
    preprocessing_applied: bool = False
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate OCR result parameters"""
        if self.timestamp < 0:
            raise ValueError("Timestamp must be non-negative")
        if self.frame_number < 0:
            raise ValueError("Frame number must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.processing_time < 0:
            raise ValueError("Processing time must be non-negative")
    
    def add_text_segment(self, segment: TextSegment):
        """Add a text segment to the result"""
        self.text_segments.append(segment)
    
    def get_high_confidence_text(self, threshold: float = 0.8) -> str:
        """Get text with confidence above threshold"""
        high_conf_segments = [
            seg.text for seg in self.text_segments 
            if seg.confidence >= threshold
        ]
        return " ".join(high_conf_segments)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'result_id': self.result_id,
            'job_id': self.job_id,
            'video_id': self.video_id,
            'tenant_id': self.tenant_id,
            'timestamp': self.timestamp,
            'frame_number': self.frame_number,
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'bounding_boxes': [bbox.to_dict() for bbox in self.bounding_boxes],
            'text_segments': [seg.to_dict() for seg in self.text_segments],
            'ocr_engine': self.ocr_engine.value,
            'preprocessing_applied': self.preprocessing_applied,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrameOCRResult':
        """Create from dictionary"""
        result = cls(
            result_id=data['result_id'],
            job_id=data['job_id'],
            video_id=data['video_id'],
            tenant_id=data['tenant_id'],
            timestamp=data['timestamp'],
            frame_number=data['frame_number'],
            text=data['text'],
            confidence=data['confidence'],
            language=data['language'],
            ocr_engine=OCREngine(data['ocr_engine']),
            preprocessing_applied=data['preprocessing_applied'],
            processing_time=data['processing_time'],
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data.get('metadata', {})
        )
        
        result.bounding_boxes = [
            BoundingBox.from_dict(bbox_data) 
            for bbox_data in data.get('bounding_boxes', [])
        ]
        
        result.text_segments = [
            TextSegment.from_dict(seg_data) 
            for seg_data in data.get('text_segments', [])
        ]
        
        return result


@dataclass
class FrameOCRJob:
    """OCR processing job with comprehensive tracking"""
    job_id: str = field(default_factory=lambda: str(uuid4()))
    video_id: str = ""
    video_path: str = ""
    tenant_id: str = ""
    user_id: str = ""
    status: JobStatus = JobStatus.PENDING
    config: OCRJobConfig = field(default_factory=OCRJobConfig)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    frames_processed: int = 0
    total_frames: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    processing_node: Optional[str] = None
    data_lineage: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate job parameters"""
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("Progress must be between 0.0 and 1.0")
        if self.frames_processed < 0:
            raise ValueError("Frames processed must be non-negative")
        if self.total_frames < 0:
            raise ValueError("Total frames must be non-negative")
        if self.retry_count < 0:
            raise ValueError("Retry count must be non-negative")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.estimated_cost < 0:
            raise ValueError("Estimated cost must be non-negative")
        if self.actual_cost < 0:
            raise ValueError("Actual cost must be non-negative")
    
    def start_processing(self, processing_node: str = None):
        """Mark job as started"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.now(timezone.utc)
        self.processing_node = processing_node
        logger.info(f"Job {self.job_id} started processing on node {processing_node}")
    
    def update_progress(self, frames_processed: int, total_frames: int = None):
        """Update job progress"""
        self.frames_processed = frames_processed
        if total_frames is not None:
            self.total_frames = total_frames
        
        if self.total_frames > 0:
            self.progress = min(1.0, self.frames_processed / self.total_frames)
    
    def complete_job(self, actual_cost: float = 0.0):
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.progress = 1.0
        self.actual_cost = actual_cost
        logger.info(f"Job {self.job_id} completed successfully")
    
    def fail_job(self, error_message: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        logger.error(f"Job {self.job_id} failed: {error_message}")
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries and self.status == JobStatus.FAILED
    
    def retry_job(self):
        """Retry failed job"""
        if not self.can_retry():
            raise ValueError("Job cannot be retried")
        
        self.retry_count += 1
        self.status = JobStatus.QUEUED
        self.error_message = None
        self.progress = 0.0
        self.frames_processed = 0
        logger.info(f"Job {self.job_id} queued for retry (attempt {self.retry_count})")
    
    def get_processing_duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return None
    
    def add_lineage_entry(self, operation: str, details: Dict[str, Any]):
        """Add data lineage tracking entry"""
        timestamp = datetime.now(timezone.utc).isoformat()
        if 'operations' not in self.data_lineage:
            self.data_lineage['operations'] = []
        
        self.data_lineage['operations'].append({
            'timestamp': timestamp,
            'operation': operation,
            'details': details
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'job_id': self.job_id,
            'video_id': self.video_id,
            'video_path': self.video_path,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'status': self.status.value,
            'config': self.config.to_dict(),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'frames_processed': self.frames_processed,
            'total_frames': self.total_frames,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
            'processing_node': self.processing_node,
            'data_lineage': self.data_lineage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrameOCRJob':
        """Create from dictionary"""
        job = cls(
            job_id=data['job_id'],
            video_id=data['video_id'],
            video_path=data['video_path'],
            tenant_id=data['tenant_id'],
            user_id=data['user_id'],
            status=JobStatus(data['status']),
            config=OCRJobConfig.from_dict(data['config']),
            created_at=datetime.fromisoformat(data['created_at']),
            progress=data['progress'],
            frames_processed=data['frames_processed'],
            total_frames=data['total_frames'],
            error_message=data.get('error_message'),
            retry_count=data['retry_count'],
            max_retries=data['max_retries'],
            estimated_cost=data['estimated_cost'],
            actual_cost=data['actual_cost'],
            processing_node=data.get('processing_node'),
            data_lineage=data.get('data_lineage', {})
        )
        
        if data.get('started_at'):
            job.started_at = datetime.fromisoformat(data['started_at'])
        
        if data.get('completed_at'):
            job.completed_at = datetime.fromisoformat(data['completed_at'])
        
        return job


# Model validation utilities
class ModelValidator:
    """Utility class for model validation"""
    
    @staticmethod
    def validate_job(job: FrameOCRJob) -> List[str]:
        """Validate OCR job and return list of errors"""
        errors = []
        
        if not job.video_id:
            errors.append("Video ID is required")
        
        if not job.video_path or not Path(job.video_path).exists():
            errors.append("Valid video path is required")
        
        if not job.tenant_id:
            errors.append("Tenant ID is required")
        
        if not job.user_id:
            errors.append("User ID is required")
        
        # Validate config
        try:
            job.config.__post_init__()
        except ValueError as e:
            errors.append(f"Invalid configuration: {e}")
        
        return errors
    
    @staticmethod
    def validate_result(result: FrameOCRResult) -> List[str]:
        """Validate OCR result and return list of errors"""
        errors = []
        
        if not result.job_id:
            errors.append("Job ID is required")
        
        if not result.video_id:
            errors.append("Video ID is required")
        
        if not result.tenant_id:
            errors.append("Tenant ID is required")
        
        if result.timestamp < 0:
            errors.append("Timestamp must be non-negative")
        
        if result.frame_number < 0:
            errors.append("Frame number must be non-negative")
        
        return errors


# Serialization utilities
class ModelSerializer:
    """Utility class for model serialization"""
    
    @staticmethod
    def serialize_job(job: FrameOCRJob) -> str:
        """Serialize job to JSON string"""
        return json.dumps(job.to_dict(), indent=2)
    
    @staticmethod
    def deserialize_job(json_str: str) -> FrameOCRJob:
        """Deserialize job from JSON string"""
        data = json.loads(json_str)
        return FrameOCRJob.from_dict(data)
    
    @staticmethod
    def serialize_result(result: FrameOCRResult) -> str:
        """Serialize result to JSON string"""
        return json.dumps(result.to_dict(), indent=2)
    
    @staticmethod
    def deserialize_result(json_str: str) -> FrameOCRResult:
        """Deserialize result from JSON string"""
        data = json.loads(json_str)
        return FrameOCRResult.from_dict(data)


if __name__ == "__main__":
    # Example usage and validation
    print("Frame OCR Models - Example Usage")
    
    # Create sample configuration
    config = OCRJobConfig(
        sampling_strategy=SamplingStrategy.TIME_BASED,
        sampling_interval=2.0,
        max_frames=500,
        ocr_engines=[OCREngine.TESSERACT, OCREngine.EASYOCR],
        confidence_threshold=0.7,
        languages=["en", "es"]
    )
    
    # Create sample job
    job = FrameOCRJob(
        video_id="video_123",
        video_path="/path/to/video.mp4",
        tenant_id="tenant_abc",
        user_id="user_xyz",
        config=config
    )
    
    print(f"Created job: {job.job_id}")
    print(f"Estimated cost: ${job.config.estimate_cost(300):.4f}")
    
    # Validate job
    errors = ModelValidator.validate_job(job)
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("Job validation passed")
    
    # Test serialization
    serialized = ModelSerializer.serialize_job(job)
    deserialized = ModelSerializer.deserialize_job(serialized)
    print(f"Serialization test passed: {job.job_id == deserialized.job_id}")