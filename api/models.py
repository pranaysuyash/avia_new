"""
API Data Models
Pydantic models for API request and response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class BaseResponse(BaseModel):
    """Base API response model"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    status_code: int = 400


# Authentication Models
class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class LoginResponse(BaseResponse):
    """Login response model"""
    token: str
    user_id: str
    expires_at: datetime


class APIKeyRequest(BaseModel):
    """API key generation request"""
    description: Optional[str] = Field(None, max_length=200)


class APIKeyResponse(BaseResponse):
    """API key generation response"""
    api_key: str
    description: Optional[str]
    created_at: datetime


# Transcription Models
class TranscriptionRequest(BaseModel):
    """Transcription request model"""
    use_api: bool = Field(default=False, description="Use OpenAI API or local model")
    language: Optional[str] = Field(default="auto", description="Audio language")
    model: Optional[str] = Field(default="base", description="Whisper model size")
    enable_diarization: bool = Field(default=False, description="Enable speaker diarization")
    extract_entities: bool = Field(default=True, description="Extract named entities")
    
    @validator('language')
    def validate_language(cls, v):
        valid_languages = ['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
        if v not in valid_languages:
            raise ValueError(f'Language must be one of {valid_languages}')
        return v
    
    @validator('model')
    def validate_model(cls, v):
        valid_models = ['tiny', 'base', 'small', 'medium', 'large']
        if v not in valid_models:
            raise ValueError(f'Model must be one of {valid_models}')
        return v


class Entity(BaseModel):
    """Named entity model"""
    text: str
    label: str
    start: int
    end: int
    confidence: Optional[float] = None


class SpeakerSegment(BaseModel):
    """Speaker diarization segment"""
    speaker_id: str
    start_time: float
    end_time: float
    text: Optional[str] = None
    confidence: float


class TranscriptionResult(BaseModel):
    """Transcription result model"""
    transcript_id: str
    text: str
    language: str
    duration: float
    word_count: int
    entities: List[Entity] = []
    speakers: Optional[List[SpeakerSegment]] = None
    confidence: Optional[float] = None
    processing_time: float
    created_at: datetime


class TranscriptionResponse(BaseResponse):
    """Transcription response model"""
    data: TranscriptionResult


# Search Models
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = Field(default="relevance")
    include_snippets: bool = Field(default=True)
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        valid_sorts = ['relevance', 'date', 'duration', 'word_count']
        if v not in valid_sorts:
            raise ValueError(f'sort_by must be one of {valid_sorts}')
        return v


class SearchResult(BaseModel):
    """Search result item"""
    transcript_id: str
    title: Optional[str]
    snippet: str
    score: float
    created_at: datetime
    duration: Optional[float]
    word_count: Optional[int]


class SearchResponse(BaseResponse):
    """Search response model"""
    data: Dict[str, Any] = Field(..., description="Search results and metadata")
    total_count: int
    page: int
    per_page: int


# Export Models
class ExportFormat(str, Enum):
    """Export format options"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    HTML = "html"
    XML = "xml"
    XLSX = "xlsx"


class ExportRequest(BaseModel):
    """Export request model"""
    transcript_id: str
    format: ExportFormat
    include_metadata: bool = Field(default=True)
    include_entities: bool = Field(default=True)
    include_speakers: bool = Field(default=True)
    custom_template: Optional[str] = None


class ExportResponse(BaseResponse):
    """Export response model"""
    download_url: str
    file_name: str
    file_size: int
    expires_at: datetime


# Content Insights Models
class InsightRequest(BaseModel):
    """Content insight request model"""
    transcript_id: str
    analysis_types: List[str] = Field(default=["summary", "sentiment", "topics"])
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = ["summary", "sentiment", "topics", "speakers", "key_moments", "action_items"]
        for analysis_type in v:
            if analysis_type not in valid_types:
                raise ValueError(f'Analysis type must be one of {valid_types}')
        return v


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    overall_sentiment: str
    confidence: float
    positive_score: float
    negative_score: float
    neutral_score: float


class TopicAnalysis(BaseModel):
    """Topic analysis result"""
    topics: List[Dict[str, Any]]
    main_topic: str
    topic_distribution: Dict[str, float]


class ContentSummary(BaseModel):
    """Content summary result"""
    brief: str
    detailed: str
    key_points: List[str]
    word_count: int


class InsightResult(BaseModel):
    """Content insight result"""
    transcript_id: str
    sentiment: Optional[SentimentAnalysis] = None
    topics: Optional[TopicAnalysis] = None
    summary: Optional[ContentSummary] = None
    processing_time: float
    generated_at: datetime


class InsightResponse(BaseResponse):
    """Content insight response model"""
    data: InsightResult


# Video Processing Models
class VideoProcessingRequest(BaseModel):
    """Video processing request model"""
    extract_frames: bool = Field(default=True)
    detect_scenes: bool = Field(default=True)
    generate_thumbnails: bool = Field(default=True)
    keyframe_interval: float = Field(default=10.0, ge=1.0, le=60.0)
    thumbnail_count: int = Field(default=5, ge=1, le=20)


class VideoFrame(BaseModel):
    """Video frame information"""
    timestamp: float
    frame_path: str
    width: int
    height: int


class VideoScene(BaseModel):
    """Video scene information"""
    start_time: float
    end_time: float
    duration: float
    frame_count: int
    thumbnail_path: Optional[str] = None


class VideoAnalysisResult(BaseModel):
    """Video analysis result"""
    duration: float
    fps: float
    frame_count: int
    resolution: Dict[str, int]
    keyframes: List[VideoFrame] = []
    scenes: List[VideoScene] = []
    thumbnails: List[str] = []
    metadata: Dict[str, Any] = {}


class VideoProcessingResponse(BaseResponse):
    """Video processing response model"""
    data: VideoAnalysisResult


# Security Models
class UserCreateRequest(BaseModel):
    """User creation request"""
    user_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="user")
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['admin', 'user', 'viewer']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of {valid_roles}')
        return v


class UserResponse(BaseModel):
    """User information response"""
    user_id: str
    role: str
    created_at: datetime
    last_login: Optional[datetime]
    active: bool


class SecurityStatusResponse(BaseResponse):
    """Security status response"""
    data: Dict[str, Any]


# Batch Processing Models
class BatchProcessingRequest(BaseModel):
    """Batch processing request"""
    file_urls: List[str] = Field(..., min_items=1, max_items=100)
    processing_options: TranscriptionRequest
    notification_webhook: Optional[str] = None


class BatchJob(BaseModel):
    """Batch job information"""
    job_id: str
    status: str
    total_files: int
    completed_files: int
    failed_files: int
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None


class BatchProcessingResponse(BaseResponse):
    """Batch processing response"""
    data: BatchJob


# Webhook Models
class WebhookEvent(BaseModel):
    """Webhook event model"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: str


# File Upload Models
class FileUploadResponse(BaseResponse):
    """File upload response"""
    file_id: str
    file_name: str
    file_size: int
    content_type: str
    upload_url: Optional[str] = None


# List Response Models
class PaginatedResponse(BaseResponse):
    """Paginated list response"""
    data: List[Any]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
    uptime_seconds: Optional[float] = None


class MetricsResponse(BaseModel):
    """API metrics response"""
    requests_total: int
    requests_per_second: float
    active_sessions: int
    api_keys_active: int
    uptime_seconds: float
    memory_usage_mb: float
    timestamp: datetime