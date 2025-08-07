"""
Transcription Models
Pydantic models for transcription requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TranscriptionStatus(str, Enum):
    """Transcription status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Entity(BaseModel):
    """Named entity model"""
    text: str = Field(..., description="Entity text")
    label: str = Field(..., description="Entity label/type")
    start: int = Field(..., description="Start position")
    end: int = Field(..., description="End position")
    confidence: Optional[float] = Field(None, description="Confidence score")


class SpeakerSegment(BaseModel):
    """Speaker diarization segment"""
    speaker: str = Field(..., description="Speaker identifier")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Segment text")


class TranscriptionRequest(BaseModel):
    """Transcription request model"""
    file_url: Optional[str] = Field(None, description="File URL")
    language: Optional[str] = Field("auto", description="Language code")
    model: Optional[str] = Field("whisper-1", description="Transcription model")
    enable_diarization: bool = Field(False, description="Enable speaker diarization")
    enable_ner: bool = Field(False, description="Enable named entity recognition")
    custom_vocabulary: Optional[List[str]] = Field(None, description="Custom vocabulary")
    

class TranscriptionResponse(BaseModel):
    """Transcription response model"""
    task_id: str = Field(..., description="Task ID")
    status: TranscriptionStatus = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: Optional[str] = Field(None, description="Status message")


class TranscriptionResult(BaseModel):
    """Transcription result model"""
    task_id: str = Field(..., description="Task ID")
    status: TranscriptionStatus = Field(..., description="Task status")
    text: Optional[str] = Field(None, description="Transcribed text")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Transcription segments")
    speakers: Optional[List[SpeakerSegment]] = Field(None, description="Speaker segments")
    entities: Optional[List[Entity]] = Field(None, description="Named entities")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration")
    processing_time: Optional[float] = Field(None, description="Processing time")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class FileUploadResponse(BaseModel):
    """File upload response model"""
    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    upload_url: Optional[str] = Field(None, description="Upload URL")
    status: str = Field(..., description="Upload status")