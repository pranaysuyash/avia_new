"""
Enterprise-Grade API Endpoints for Audio Intelligence Platform
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Optional, Dict, Any
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np
from sqlalchemy.orm import Session

# Import your existing modules
from media import MediaProcessor
from stt import TranscriptionService
from ner_advanced import AdvancedNER
from audio_enhancement_pipeline import AudioEnhancementPipeline
from speaker_diarization_system import SpeakerDiarization
from database.models import Transcription, User, Team, ProcessingJob
from auth.jwt_handler import get_current_user
from services.websocket_manager import WebSocketManager

router = APIRouter(prefix="/api/v1/enterprise", tags=["enterprise"])
ws_manager = WebSocketManager()

# Pydantic Models
class ProcessingOptions(BaseModel):
    enhance: bool = True
    transcribe: bool = True
    extract_entities: bool = True
    generate_summary: bool = True
    detect_speakers: bool = True
    language: Optional[str] = "auto"
    model: str = "whisper-large-v3"
    
class ProcessingStatus(BaseModel):
    job_id: str
    status: str
    stage: str
    progress: float
    message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    
class AudioQualityMetrics(BaseModel):
    overall_quality: float
    clarity_score: float
    noise_level: float
    signal_to_noise_ratio: float
    peak_amplitude: float
    dynamic_range: float
    
class TranscriptionResult(BaseModel):
    text: str
    segments: List[Dict[str, Any]]
    language: str
    confidence: float
    duration: float
    word_count: int
    speakers: Optional[List[Dict[str, Any]]] = None
    
class EntityExtractionResult(BaseModel):
    entities: Dict[str, List[Dict[str, Any]]]
    keywords: List[str]
    summary: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    
class AnalyticsMetrics(BaseModel):
    total_processed: int
    total_duration: float
    average_processing_time: float
    accuracy_rate: float
    cost_saved: float
    processing_volume: List[Dict[str, Any]]
    entity_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    user_activity: List[Dict[str, Any]]

# Initialize services
media_processor = MediaProcessor()
transcription_service = TranscriptionService()
ner_service = AdvancedNER()
enhancement_pipeline = AudioEnhancementPipeline()
diarization_service = SpeakerDiarization()

# WebSocket endpoint for real-time processing updates
@router.websocket("/ws/processing/{client_id}")
async def websocket_processing(websocket: WebSocket, client_id: str):
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and send updates
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)

# WebSocket endpoint for real-time collaboration
@router.websocket("/ws/collaboration/{transcript_id}")
async def websocket_collaboration(websocket: WebSocket, transcript_id: str):
    await ws_manager.connect(websocket, f"collab_{transcript_id}")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Broadcast collaboration events to all connected clients
            await ws_manager.broadcast(f"collab_{transcript_id}", message)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(f"collab_{transcript_id}")

# Main audio processing endpoint
@router.post("/audio/process", response_model=ProcessingStatus)
async def process_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: ProcessingOptions = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Enterprise-grade audio processing pipeline with real-time updates
    """
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Validate file
    if not file.content_type.startswith(('audio/', 'video/')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Check file size (max 5GB)
    if file.size > 5 * 1024 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5GB)")
    
    # Create processing job
    job = ProcessingJob(
        id=job_id,
        user_id=current_user.id,
        filename=file.filename,
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    
    # Start background processing
    background_tasks.add_task(
        process_audio_task,
        job_id,
        file,
        options,
        current_user.id,
        db
    )
    
    return ProcessingStatus(
        job_id=job_id,
        status="pending",
        stage="initialization",
        progress=0,
        message="Processing started"
    )

async def process_audio_task(
    job_id: str,
    file: UploadFile,
    options: ProcessingOptions,
    user_id: str,
    db: Session
):
    """
    Background task for audio processing
    """
    try:
        # Send initial status
        await ws_manager.send_to_client(
            user_id,
            {
                "type": "processing_status",
                "job_id": job_id,
                "stage": "uploading",
                "progress": 10,
                "message": "Uploading file..."
            }
        )
        
        # Save uploaded file
        file_path = f"/tmp/{job_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Audio quality assessment
        await ws_manager.send_to_client(
            user_id,
            {
                "type": "processing_status",
                "job_id": job_id,
                "stage": "quality_check",
                "progress": 20,
                "message": "Analyzing audio quality..."
            }
        )
        
        quality_metrics = await analyze_audio_quality(file_path)
        
        # Audio enhancement
        if options.enhance:
            await ws_manager.send_to_client(
                user_id,
                {
                    "type": "processing_status",
                    "job_id": job_id,
                    "stage": "enhancing",
                    "progress": 30,
                    "message": "Enhancing audio quality..."
                }
            )
            
            enhanced_path = await enhancement_pipeline.process(file_path)
        else:
            enhanced_path = file_path
        
        # Transcription
        transcription_result = None
        if options.transcribe:
            await ws_manager.send_to_client(
                user_id,
                {
                    "type": "processing_status",
                    "job_id": job_id,
                    "stage": "transcribing",
                    "progress": 50,
                    "message": "Transcribing audio..."
                }
            )
            
            transcription_result = await transcription_service.transcribe(
                enhanced_path,
                language=options.language,
                model=options.model
            )
        
        # Speaker diarization
        speakers = None
        if options.detect_speakers and transcription_result:
            await ws_manager.send_to_client(
                user_id,
                {
                    "type": "processing_status",
                    "job_id": job_id,
                    "stage": "diarization",
                    "progress": 60,
                    "message": "Detecting speakers..."
                }
            )
            
            speakers = await diarization_service.process(enhanced_path)
        
        # Entity extraction and analysis
        entities = None
        summary = None
        if options.extract_entities and transcription_result:
            await ws_manager.send_to_client(
                user_id,
                {
                    "type": "processing_status",
                    "job_id": job_id,
                    "stage": "analyzing",
                    "progress": 80,
                    "message": "Extracting entities and insights..."
                }
            )
            
            analysis = await ner_service.analyze(transcription_result['text'])
            entities = analysis.get('entities')
            
            if options.generate_summary:
                summary = analysis.get('summary')
        
        # Save results to database
        transcription = Transcription(
            id=job_id,
            user_id=user_id,
            filename=file.filename,
            text=transcription_result['text'] if transcription_result else None,
            entities=json.dumps(entities) if entities else None,
            summary=summary,
            speakers=json.dumps(speakers) if speakers else None,
            confidence=transcription_result.get('confidence', 0) if transcription_result else 0,
            duration=transcription_result.get('duration', 0) if transcription_result else 0,
            language=transcription_result.get('language', 'unknown') if transcription_result else 'unknown',
            created_at=datetime.utcnow()
        )
        db.add(transcription)
        db.commit()
        
        # Send completion status
        await ws_manager.send_to_client(
            user_id,
            {
                "type": "processing_complete",
                "job_id": job_id,
                "stage": "completed",
                "progress": 100,
                "message": "Processing completed successfully",
                "result": {
                    "transcription_id": job_id,
                    "quality_metrics": quality_metrics.dict() if quality_metrics else None,
                    "transcription": transcription_result,
                    "entities": entities,
                    "summary": summary,
                    "speakers": speakers
                }
            }
        )
        
        # Update job status
        job = db.query(ProcessingJob).filter_by(id=job_id).first()
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        # Send error status
        await ws_manager.send_to_client(
            user_id,
            {
                "type": "processing_error",
                "job_id": job_id,
                "stage": "error",
                "progress": 0,
                "message": f"Processing failed: {str(e)}"
            }
        )
        
        # Update job status
        job = db.query(ProcessingJob).filter_by(id=job_id).first()
        job.status = "failed"
        job.error = str(e)
        db.commit()

# Analytics endpoint
@router.get("/analytics/metrics", response_model=AnalyticsMetrics)
async def get_analytics_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    time_range: str = "7d"
):
    """
    Get comprehensive analytics metrics for the dashboard
    """
    # Calculate time range
    if time_range == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
    elif time_range == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
    else:
        start_date = datetime.utcnow() - timedelta(days=90)
    
    # Query metrics
    transcriptions = db.query(Transcription).filter(
        Transcription.created_at >= start_date,
        Transcription.user_id == current_user.id
    ).all()
    
    # Calculate metrics
    total_processed = len(transcriptions)
    total_duration = sum(t.duration for t in transcriptions)
    avg_processing_time = np.mean([
        (t.completed_at - t.created_at).total_seconds() 
        for t in transcriptions 
        if t.completed_at
    ]) if transcriptions else 0
    
    # Calculate accuracy (mock data for demo)
    accuracy_rate = 97.8
    
    # Calculate cost saved (mock calculation)
    cost_saved = total_duration * 0.15  # $0.15 per minute saved
    
    # Processing volume by day
    processing_volume = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        day_transcriptions = [
            t for t in transcriptions 
            if t.created_at.date() == date.date()
        ]
        processing_volume.append({
            "date": date.strftime("%b %d"),
            "processed": len(day_transcriptions),
            "duration": sum(t.duration for t in day_transcriptions)
        })
    
    # Entity distribution
    entity_distribution = {}
    for t in transcriptions:
        if t.entities:
            entities = json.loads(t.entities)
            for entity_type, items in entities.items():
                entity_distribution[entity_type] = entity_distribution.get(entity_type, 0) + len(items)
    
    # Language distribution
    language_distribution = {}
    for t in transcriptions:
        lang = t.language or "unknown"
        language_distribution[lang] = language_distribution.get(lang, 0) + 1
    
    # User activity (recent)
    user_activity = []
    recent_transcriptions = sorted(transcriptions, key=lambda x: x.created_at, reverse=True)[:10]
    for t in recent_transcriptions:
        user_activity.append({
            "timestamp": t.created_at.isoformat(),
            "action": f"Processed {t.filename}",
            "status": "completed" if t.completed_at else "processing"
        })
    
    return AnalyticsMetrics(
        total_processed=total_processed,
        total_duration=total_duration,
        average_processing_time=avg_processing_time,
        accuracy_rate=accuracy_rate,
        cost_saved=cost_saved,
        processing_volume=processing_volume,
        entity_distribution=entity_distribution,
        language_distribution=language_distribution,
        user_activity=user_activity
    )

# Transcription management endpoints
@router.get("/transcriptions", response_model=List[TranscriptionResult])
async def get_transcriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database),
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None
):
    """
    Get user's transcriptions with pagination and search
    """
    query = db.query(Transcription).filter(Transcription.user_id == current_user.id)
    
    if search:
        query = query.filter(Transcription.text.contains(search))
    
    transcriptions = query.offset(skip).limit(limit).all()
    
    return [
        TranscriptionResult(
            text=t.text,
            segments=json.loads(t.segments) if t.segments else [],
            language=t.language,
            confidence=t.confidence,
            duration=t.duration,
            word_count=len(t.text.split()) if t.text else 0,
            speakers=json.loads(t.speakers) if t.speakers else None
        )
        for t in transcriptions
    ]

@router.get("/transcriptions/{transcription_id}")
async def get_transcription(
    transcription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get specific transcription with all details
    """
    transcription = db.query(Transcription).filter(
        Transcription.id == transcription_id,
        Transcription.user_id == current_user.id
    ).first()
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    return {
        "id": transcription.id,
        "filename": transcription.filename,
        "text": transcription.text,
        "segments": json.loads(transcription.segments) if transcription.segments else [],
        "entities": json.loads(transcription.entities) if transcription.entities else {},
        "summary": transcription.summary,
        "speakers": json.loads(transcription.speakers) if transcription.speakers else [],
        "confidence": transcription.confidence,
        "duration": transcription.duration,
        "language": transcription.language,
        "created_at": transcription.created_at.isoformat()
    }

# Export endpoints
@router.post("/transcriptions/{transcription_id}/export")
async def export_transcription(
    transcription_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Export transcription in various formats
    """
    transcription = db.query(Transcription).filter(
        Transcription.id == transcription_id,
        Transcription.user_id == current_user.id
    ).first()
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    if format == "json":
        return JSONResponse(content={
            "transcription": transcription.text,
            "entities": json.loads(transcription.entities) if transcription.entities else {},
            "summary": transcription.summary,
            "metadata": {
                "filename": transcription.filename,
                "duration": transcription.duration,
                "language": transcription.language,
                "confidence": transcription.confidence
            }
        })
    
    elif format == "csv":
        # Generate CSV export
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Timestamp", "Speaker", "Text", "Confidence"])
        
        # Write segments
        segments = json.loads(transcription.segments) if transcription.segments else []
        for segment in segments:
            writer.writerow([
                segment.get("start", ""),
                segment.get("speaker", ""),
                segment.get("text", ""),
                segment.get("confidence", "")
            ])
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={transcription_id}.csv"}
        )
    
    elif format == "pdf":
        # Generate PDF export (requires additional library)
        # Implementation would go here
        pass
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

# Audio quality analysis
async def analyze_audio_quality(file_path: str) -> AudioQualityMetrics:
    """
    Analyze audio quality metrics
    """
    import librosa
    
    # Load audio
    audio, sr = librosa.load(file_path, sr=None)
    
    # Calculate metrics
    rms = np.sqrt(np.mean(audio**2))
    peak = np.max(np.abs(audio))
    
    # Calculate SNR (simplified)
    signal_power = np.mean(audio**2)
    noise_power = np.mean(audio[:sr//10]**2)  # Assume first 0.1s is noise
    snr = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 0
    
    # Dynamic range
    dynamic_range = 20 * np.log10(peak / rms) if rms > 0 else 0
    
    # Overall quality score (0-100)
    quality_score = min(100, max(0, snr * 2 + 50))
    
    # Clarity score (0-100)
    clarity_score = min(100, max(0, dynamic_range * 5))
    
    return AudioQualityMetrics(
        overall_quality=quality_score,
        clarity_score=clarity_score,
        noise_level=20 * np.log10(noise_power) if noise_power > 0 else -60,
        signal_to_noise_ratio=snr,
        peak_amplitude=peak,
        dynamic_range=dynamic_range
    )

# Team collaboration endpoints
@router.get("/teams/{team_id}/members")
async def get_team_members(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Get team members for collaboration
    """
    team = db.query(Team).filter(
        Team.id == team_id,
        Team.members.contains(current_user.id)
    ).first()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    members = db.query(User).filter(User.id.in_(team.members)).all()
    
    return [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "avatar": m.avatar,
            "role": m.role,
            "is_active": m.is_active
        }
        for m in members
    ]

# Annotation endpoints for collaboration
@router.post("/transcriptions/{transcription_id}/annotations")
async def add_annotation(
    transcription_id: str,
    annotation: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Add annotation to transcription
    """
    # Verify access
    transcription = db.query(Transcription).filter(
        Transcription.id == transcription_id,
        Transcription.user_id == current_user.id
    ).first()
    
    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")
    
    # Add annotation
    annotation_id = str(uuid.uuid4())
    annotation_data = {
        "id": annotation_id,
        "user_id": current_user.id,
        "user_name": current_user.name,
        "timestamp": datetime.utcnow().isoformat(),
        **annotation
    }
    
    # Store annotation (simplified - should use proper annotation table)
    annotations = json.loads(transcription.annotations) if transcription.annotations else []
    annotations.append(annotation_data)
    transcription.annotations = json.dumps(annotations)
    db.commit()
    
    # Broadcast to collaborators
    await ws_manager.broadcast(
        f"collab_{transcription_id}",
        {
            "type": "annotation",
            "annotation": annotation_data
        }
    )
    
    return annotation_data
