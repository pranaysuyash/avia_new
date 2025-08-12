"""
Advanced Features API Endpoints
Unified endpoints for all newly implemented systems
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import io
import json

# Import all new systems
from batch_transcription_system import (
    BatchTranscriptionSystem, Priority as BatchPriority, 
    ProcessingStatus, ExportFormat
)
from punctuation_restoration import (
    PunctuationRestorer, ModelType as PunctuationModel,
    RestorationMode
)
from advanced_timestamping_system import (
    AdvancedTimestampingSystem, TimestampGranularity,
    TimestampFormat
)
from keyword_extraction_system import (
    AdvancedKeywordExtractor, ExtractionMethod,
    KeywordVisualization
)
from event_extraction_system import (
    EventExtractor, EventType, Priority as EventPriority
)
from visual_content_analysis import (
    VisualContentAnalyzer, AnalysisType,
    PrivacyMode, DetectionModel
)
from text_classification_system import (
    TextClassificationSystem, ClassificationType,
    ModelType as ClassificationModel
)

# Create router
router = APIRouter(prefix="/api/advanced", tags=["advanced_features"])

# Initialize systems (would be dependency injected in production)
batch_system = None
punctuation_system = None
timestamp_system = None
keyword_system = None
event_system = None
visual_system = None
classification_system = None


# Request/Response Models
class BatchCreateRequest(BaseModel):
    name: str
    file_urls: List[str]
    priority: str = "medium"
    webhook_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    progress: float
    completed_jobs: int
    total_jobs: int
    estimated_time_remaining: Optional[int] = None


class PunctuationRequest(BaseModel):
    text: str
    model: str = "t5"
    mode: str = "comprehensive"
    preserve_formatting: bool = True
    confidence_threshold: float = 0.7


class TimestampRequest(BaseModel):
    audio_url: str
    granularity: str = "word"
    format: str = "json"
    include_confidence: bool = True
    enable_search: bool = True


class KeywordRequest(BaseModel):
    text: str
    methods: List[str] = ["rake", "tfidf", "textrank"]
    max_keywords: int = 20
    include_scores: bool = True
    visualize: bool = False


class EventRequest(BaseModel):
    text: str
    extract_actions: bool = True
    build_timeline: bool = True
    reference_date: Optional[str] = None
    export_format: Optional[str] = None


class VisualAnalysisRequest(BaseModel):
    image_url: str
    analysis_types: List[str] = ["objects", "scene", "text"]
    privacy_mode: Optional[str] = None
    detect_faces: bool = True
    extract_text: bool = True


class ClassificationRequest(BaseModel):
    text: str
    classification_type: str = "multiclass"
    model_key: Optional[str] = None
    candidate_labels: Optional[List[str]] = None
    threshold: float = 0.5


class TrainClassifierRequest(BaseModel):
    texts: List[str]
    labels: Union[List[str], List[List[str]]]
    classification_type: str
    model_type: str = "logistic_regression"
    test_size: float = 0.2


# Batch Processing Endpoints
@router.post("/batch/create", response_model=BatchStatusResponse)
async def create_batch(request: BatchCreateRequest, background_tasks: BackgroundTasks):
    """Create a new batch transcription job"""
    global batch_system
    
    if not batch_system:
        batch_system = BatchTranscriptionSystem()
        await batch_system.initialize()
    
    try:
        # Convert string priority to enum
        priority = BatchPriority[request.priority.upper()]
        
        # Create batch
        batch = await batch_system.create_batch(
            name=request.name,
            file_paths=request.file_urls,
            priority=priority,
            webhook_url=request.webhook_url,
            config=request.config
        )
        
        # Start processing in background
        background_tasks.add_task(batch_system.start_batch, batch.batch_id)
        
        return BatchStatusResponse(
            batch_id=batch.batch_id,
            status=batch.status.value,
            progress=0.0,
            completed_jobs=0,
            total_jobs=len(batch.jobs)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Get status of a batch transcription job"""
    if not batch_system:
        raise HTTPException(status_code=503, detail="Batch system not initialized")
    
    status = await batch_system.get_batch_status(batch_id)
    if not status:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return BatchStatusResponse(
        batch_id=status.batch_id,
        status=status.status.value,
        progress=status.progress,
        completed_jobs=len([j for j in status.jobs if j.status == ProcessingStatus.COMPLETED]),
        total_jobs=len(status.jobs),
        estimated_time_remaining=status.estimated_completion_time
    )


@router.post("/batch/{batch_id}/pause")
async def pause_batch(batch_id: str):
    """Pause a batch transcription job"""
    if not batch_system:
        raise HTTPException(status_code=503, detail="Batch system not initialized")
    
    success = await batch_system.pause_batch(batch_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to pause batch")
    
    return {"message": "Batch paused successfully"}


@router.post("/batch/{batch_id}/resume")
async def resume_batch(batch_id: str):
    """Resume a paused batch"""
    if not batch_system:
        raise HTTPException(status_code=503, detail="Batch system not initialized")
    
    success = await batch_system.resume_batch(batch_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to resume batch")
    
    return {"message": "Batch resumed successfully"}


@router.delete("/batch/{batch_id}")
async def cancel_batch(batch_id: str):
    """Cancel a batch transcription job"""
    if not batch_system:
        raise HTTPException(status_code=503, detail="Batch system not initialized")
    
    success = await batch_system.cancel_batch(batch_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel batch")
    
    return {"message": "Batch cancelled successfully"}


# Punctuation Restoration Endpoints
@router.post("/punctuation/restore")
async def restore_punctuation(request: PunctuationRequest):
    """Restore punctuation in text"""
    global punctuation_system
    
    if not punctuation_system:
        punctuation_system = PunctuationRestorer()
    
    try:
        # Convert string enums
        model = PunctuationModel[request.model.upper()]
        mode = RestorationMode[request.mode.upper()]
        
        # Restore punctuation
        result = await punctuation_system.restore_punctuation(
            text=request.text,
            model_type=model,
            mode=mode,
            preserve_formatting=request.preserve_formatting
        )
        
        return {
            "original_text": request.text,
            "restored_text": result.restored_text,
            "corrections": result.corrections,
            "confidence": result.overall_confidence,
            "processing_time": result.processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/punctuation/batch")
async def batch_restore_punctuation(texts: List[str]):
    """Restore punctuation for multiple texts"""
    global punctuation_system
    
    if not punctuation_system:
        punctuation_system = PunctuationRestorer()
    
    try:
        results = await punctuation_system.batch_restore(texts)
        
        return {
            "results": [
                {
                    "original": texts[i],
                    "restored": r.restored_text,
                    "confidence": r.overall_confidence
                }
                for i, r in enumerate(results)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Timestamping Endpoints
@router.post("/timestamps/generate")
async def generate_timestamps(request: TimestampRequest):
    """Generate advanced timestamps for audio/video"""
    global timestamp_system
    
    if not timestamp_system:
        timestamp_system = AdvancedTimestampingSystem()
    
    try:
        # Convert string enums
        granularity = TimestampGranularity[request.granularity.upper()]
        
        # Generate timestamps
        result = await timestamp_system.generate_timestamps(
            audio_file=request.audio_url,
            granularity=granularity,
            include_confidence=request.include_confidence
        )
        
        # Format output based on request
        if request.format == "srt":
            output = timestamp_system.export_subtitles(
                result,
                format=TimestampFormat.SRT
            )
            return StreamingResponse(
                io.StringIO(output),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=subtitles.srt"}
            )
        elif request.format == "vtt":
            output = timestamp_system.export_subtitles(
                result,
                format=TimestampFormat.VTT
            )
            return StreamingResponse(
                io.StringIO(output),
                media_type="text/vtt",
                headers={"Content-Disposition": "attachment; filename=subtitles.vtt"}
            )
        else:
            return {
                "timestamps": result.timestamps,
                "searchable": result.searchable_index if request.enable_search else None,
                "chapters": result.chapters,
                "statistics": result.statistics
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Keyword Extraction Endpoints
@router.post("/keywords/extract")
async def extract_keywords(request: KeywordRequest):
    """Extract keywords from text"""
    global keyword_system
    
    if not keyword_system:
        keyword_system = AdvancedKeywordExtractor()
    
    try:
        # Convert string methods to enums
        methods = [ExtractionMethod[m.upper()] for m in request.methods]
        
        # Extract keywords
        result = await keyword_system.extract_keywords(
            text=request.text,
            methods=methods,
            max_keywords=request.max_keywords,
            include_scores=request.include_scores
        )
        
        response = {
            "keywords": result.keywords,
            "key_phrases": result.key_phrases,
            "topics": result.topics,
            "statistics": result.statistics
        }
        
        # Add visualization if requested
        if request.visualize:
            viz = keyword_system.visualize_keywords(
                result,
                visualization_type=KeywordVisualization.WORDCLOUD
            )
            # Convert visualization to base64 for API response
            import base64
            buffer = io.BytesIO()
            viz.savefig(buffer, format='png')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            response["visualization"] = image_base64
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Event Extraction Endpoints
@router.post("/events/extract")
async def extract_events(request: EventRequest):
    """Extract events and temporal information from text"""
    global event_system
    
    if not event_system:
        event_system = EventExtractor()
    
    try:
        # Parse reference date if provided
        reference_date = None
        if request.reference_date:
            reference_date = datetime.fromisoformat(request.reference_date)
        
        # Extract events
        result = await event_system.extract_events(
            text=request.text,
            extract_actions=request.extract_actions,
            build_timeline=request.build_timeline,
            reference_date=reference_date
        )
        
        response = {
            "events": [
                {
                    "id": e.event_id,
                    "text": e.text,
                    "type": e.event_type.value,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "participants": e.participants,
                    "location": e.location
                }
                for e in result.events
            ],
            "action_items": [
                {
                    "id": a.action_id,
                    "text": a.text,
                    "assignee": a.assignee,
                    "deadline": a.deadline.isoformat() if a.deadline else None,
                    "priority": a.priority.value
                }
                for a in result.action_items
            ],
            "temporal_expressions": [
                {
                    "text": t.text,
                    "parsed_time": t.parsed_time.isoformat() if t.parsed_time else None,
                    "type": t.time_type
                }
                for t in result.temporal_expressions
            ],
            "statistics": result.statistics
        }
        
        # Export to calendar format if requested
        if request.export_format == "ics":
            calendar_data = event_system.export_calendar(
                result.events,
                result.action_items,
                format="ics"
            )
            return StreamingResponse(
                io.StringIO(calendar_data),
                media_type="text/calendar",
                headers={"Content-Disposition": "attachment; filename=events.ics"}
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Visual Analysis Endpoints
@router.post("/visual/analyze")
async def analyze_visual_content(request: VisualAnalysisRequest):
    """Analyze visual content in images or videos"""
    global visual_system
    
    if not visual_system:
        visual_system = VisualContentAnalyzer()
    
    try:
        # Parse analysis types
        detect_objects = "objects" in request.analysis_types
        detect_scene = "scene" in request.analysis_types
        extract_text = "text" in request.analysis_types and request.extract_text
        
        # Parse privacy mode
        privacy_mode = None
        if request.privacy_mode:
            privacy_mode = PrivacyMode[request.privacy_mode.upper()]
        
        # Analyze image
        result = await visual_system.analyze_image(
            image_path=request.image_url,
            detect_objects=detect_objects,
            detect_faces=request.detect_faces,
            extract_text=extract_text,
            privacy_mode=privacy_mode
        )
        
        return {
            "objects": result.objects if detect_objects else None,
            "faces": result.faces if request.detect_faces else None,
            "scene_description": result.scene_description if detect_scene else None,
            "extracted_text": result.extracted_text if extract_text else None,
            "safety_scores": result.safety_scores,
            "metadata": result.metadata,
            "processing_time": result.processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visual/search")
async def visual_search(query: Union[str, UploadFile]):
    """Search for visually similar content"""
    global visual_system
    
    if not visual_system:
        visual_system = VisualContentAnalyzer()
    
    try:
        if isinstance(query, str):
            # Text-based visual search
            results = await visual_system.visual_search(query)
        else:
            # Image-based visual search
            image_data = await query.read()
            results = await visual_system.visual_search(image_data)
        
        return {
            "results": [
                {
                    "image_id": r.image_id,
                    "similarity_score": r.similarity_score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Text Classification Endpoints
@router.post("/classify/text")
async def classify_text(request: ClassificationRequest):
    """Classify text into categories"""
    global classification_system
    
    if not classification_system:
        classification_system = TextClassificationSystem()
    
    try:
        # Handle zero-shot classification
        if request.classification_type == "zero_shot" and request.candidate_labels:
            result = await classification_system.zero_shot_classify(
                text=request.text,
                candidate_labels=request.candidate_labels
            )
        elif request.model_key:
            # Use existing trained model
            result = await classification_system.predict(
                text=request.text,
                model_key=request.model_key,
                threshold=request.threshold
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either model_key or candidate_labels (for zero-shot) must be provided"
            )
        
        return {
            "text": result.text,
            "predicted_labels": result.predicted_labels,
            "confidence_scores": result.confidence_scores,
            "classification_type": result.classification_type.value,
            "processing_time": result.processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classify/train")
async def train_classifier(request: TrainClassifierRequest):
    """Train a new text classifier"""
    global classification_system
    
    if not classification_system:
        classification_system = TextClassificationSystem()
    
    try:
        # Convert string enums
        classification_type = ClassificationType[request.classification_type.upper()]
        model_type = ClassificationModel[request.model_type.upper()]
        
        # Train classifier
        performance = await classification_system.train_classifier(
            texts=request.texts,
            labels=request.labels,
            classification_type=classification_type,
            model_type=model_type,
            test_size=request.test_size
        )
        
        return {
            "model_key": performance.metadata.get("model_key"),
            "accuracy": performance.accuracy,
            "precision": performance.precision,
            "recall": performance.recall,
            "f1_score": performance.f1_score,
            "classification_report": performance.classification_report
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classify/active-learning/setup")
async def setup_active_learning(
    initial_texts: List[str],
    initial_labels: List[str],
    model_type: str = "logistic_regression"
):
    """Setup active learning for classification"""
    global classification_system
    
    if not classification_system:
        classification_system = TextClassificationSystem()
    
    try:
        model = ClassificationModel[model_type.upper()]
        learner_key = classification_system.setup_active_learning(
            initial_texts=initial_texts,
            initial_labels=initial_labels,
            model_type=model
        )
        
        return {"learner_key": learner_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/classify/active-learning/{learner_key}/query")
async def query_active_learning(
    learner_key: str,
    pool_texts: List[str],
    n_instances: int = 10
):
    """Query most informative samples for labeling"""
    global classification_system
    
    if not classification_system:
        raise HTTPException(status_code=503, detail="Classification system not initialized")
    
    try:
        queries = classification_system.query_active_learning(
            learner_key=learner_key,
            pool_texts=pool_texts,
            n_instances=n_instances
        )
        
        return {
            "queries": [
                {
                    "text_id": q.text_id,
                    "text": q.text,
                    "uncertainty_score": q.uncertainty_score,
                    "predicted_labels": q.predicted_labels
                }
                for q in queries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Check health status of advanced features"""
    return {
        "status": "healthy",
        "systems": {
            "batch_processing": batch_system is not None,
            "punctuation": punctuation_system is not None,
            "timestamping": timestamp_system is not None,
            "keywords": keyword_system is not None,
            "events": event_system is not None,
            "visual": visual_system is not None,
            "classification": classification_system is not None
        }
    }


# System statistics endpoint
@router.get("/stats")
async def get_system_statistics():
    """Get statistics for all advanced features"""
    stats = {}
    
    if batch_system:
        queue_status = await batch_system.get_queue_status()
        stats["batch_processing"] = {
            "active_batches": queue_status.get("active_batches", 0),
            "pending_jobs": queue_status.get("pending_jobs", 0),
            "workers": queue_status.get("total_workers", 0)
        }
    
    if visual_system:
        stats["visual_analysis"] = {
            "models_loaded": len(visual_system.models),
            "cache_size": visual_system.get_cache_size()
        }
    
    if classification_system:
        stats["classification"] = {
            "trained_models": len(classification_system.models),
            "active_learners": len(classification_system.active_learners)
        }
    
    return stats