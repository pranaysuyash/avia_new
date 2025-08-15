"""
Real-time Translation API Endpoints
FastAPI endpoints for transcript translation services
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import asyncio
import json
import uuid

from ...realtime_translation_system import (
    RealtimeTranslationSystem, 
    TranslationRequest as SystemTranslationRequest,
    TranslationProvider,
    TranscriptSegment
)
from ..auth import get_current_user
from ..models import User
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/translation", tags=["translation"])

# Initialize translation system
translation_system = RealtimeTranslationSystem()

# Pydantic models
class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = "auto"
    provider: Optional[str] = "google"
    context: Optional[str] = None
    preserve_formatting: bool = True

class TranscriptTranslationRequest(BaseModel):
    segments: List[Dict[str, Any]]
    target_language: str
    source_language: Optional[str] = None
    provider: Optional[str] = "google"

class BatchTranslationRequest(BaseModel):
    texts: List[str]
    target_languages: List[str]
    source_language: Optional[str] = None
    provider: Optional[str] = "google"

class SubtitleTranslationRequest(BaseModel):
    srt_content: str
    target_language: str
    source_language: Optional[str] = None

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    provider: str
    confidence: float
    processing_time: float
    cached: bool

class LanguageDetectionRequest(BaseModel):
    text: str

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Translate text to target language"""
    try:
        # Convert provider string to enum
        provider = TranslationProvider[request.provider.upper()]
        
        # Create system request
        system_request = SystemTranslationRequest(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
            provider=provider,
            context=request.context,
            preserve_formatting=request.preserve_formatting
        )
        
        # Perform translation
        result = await translation_system.translate_text(system_request)
        
        # Log translation for analytics
        # Add database logging
        try:
            from database.connection import get_db_context
            from database.models import TranslationRecord
            
            with get_db_context() as db:
                translation_record = TranslationRecord(
                    source_text=result.original_text[:500],  # Limit to 500 chars
                    target_text=result.translated_text[:500],  # Limit to 500 chars
                    source_language=result.source_language,
                    target_language=result.target_language,
                    provider=result.provider,
                    confidence=result.confidence,
                    processing_time=result.processing_time,
                    cached=result.cached,
                    user_id=getattr(current_user, 'id', None),
                    created_at=datetime.now()
                )
                
                db.add(translation_record)
                db.commit()
                
                logger.info(f"Translation logged to database: {translation_record.id}")
                
        except Exception as db_error:
            logger.error(f"Failed to log translation to database: {db_error}")
            # Continue with translation even if logging fails
        
        return TranslationResponse(
            original_text=result.original_text,
            translated_text=result.translated_text,
            source_language=result.source_language,
            target_language=result.target_language,
            provider=result.provider,
            confidence=result.confidence,
            processing_time=result.processing_time,
            cached=result.cached
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate-transcript")
async def translate_transcript(
    request: TranscriptTranslationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Translate entire transcript"""
    try:
        # Convert segments to TranscriptSegment objects
        segments = []
        for seg in request.segments:
            segment = TranscriptSegment(
                text=seg['text'],
                start_time=seg.get('start_time', 0),
                end_time=seg.get('end_time', 0),
                speaker=seg.get('speaker'),
                confidence=seg.get('confidence', 1.0)
            )
            segments.append(segment)
        
        # Convert provider
        provider = TranslationProvider[request.provider.upper()]
        
        # Translate transcript
        translated_segments = await translation_system.translate_transcript(
            segments=segments,
            target_language=request.target_language,
            source_language=request.source_language,
            provider=provider
        )
        
        # Convert back to dict format
        result = []
        for segment in translated_segments:
            result.append({
                'text': segment.text,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'speaker': segment.speaker,
                'confidence': segment.confidence
            })
        
        return {
            'translated_segments': result,
            'target_language': request.target_language,
            'source_language': request.source_language or 'auto',
            'total_segments': len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-translate")
async def batch_translate(
    request: BatchTranslationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Batch translate texts to multiple languages"""
    try:
        # Convert provider
        provider = TranslationProvider[request.provider.upper()]
        
        # Perform batch translation
        results = await translation_system.batch_translate(
            texts=request.texts,
            target_languages=request.target_languages,
            source_language=request.source_language,
            provider=provider
        )
        
        return {
            'translations': results,
            'source_language': request.source_language or 'auto',
            'text_count': len(request.texts),
            'language_count': len(request.target_languages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/translate-subtitles")
async def translate_subtitles(
    request: SubtitleTranslationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Translate SRT subtitle content"""
    try:
        # Translate subtitles
        translated_srt = await translation_system.translate_subtitles(
            srt_content=request.srt_content,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        return {
            'translated_srt': translated_srt,
            'target_language': request.target_language,
            'source_language': request.source_language or 'auto'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-language")
async def detect_language(
    request: LanguageDetectionRequest,
    current_user: User = Depends(get_current_user)
):
    """Detect language of text"""
    try:
        detected = await translation_system.detect_language(request.text)
        
        languages = translation_system.get_supported_languages()
        language_name = languages.get(detected, "Unknown")
        
        return {
            'detected_language': detected,
            'language_name': language_name,
            'confidence': 0.95  # Placeholder confidence
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        languages = translation_system.get_supported_languages()
        
        return {
            'languages': [
                {'code': code, 'name': name}
                for code, name in languages.items()
            ],
            'total': len(languages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/stream")
async def stream_translation(
    websocket: WebSocket,
    target_language: str,
    source_language: Optional[str] = None
):
    """WebSocket endpoint for streaming translation"""
    await websocket.accept()
    
    try:
        # Create async generator from websocket messages
        async def text_generator():
            while True:
                data = await websocket.receive_text()
                if data == "END":
                    break
                yield data
        
        # Stream translation
        async for translated in translation_system.stream_translation(
            text_generator(),
            target_language=target_language,
            source_language=source_language
        ):
            await websocket.send_text(translated)
        
        await websocket.send_text("TRANSLATION_COMPLETE")
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(f"ERROR: {str(e)}")
    finally:
        await websocket.close()

@router.post("/translate-with-context")
async def translate_with_context(
    text: str,
    context: str,
    target_language: str,
    source_language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Translate with additional context for better accuracy"""
    try:
        result = await translation_system.translate_with_context(
            text=text,
            context=context,
            target_language=target_language,
            source_language=source_language
        )
        
        return TranslationResponse(
            original_text=result.original_text,
            translated_text=result.translated_text,
            source_language=result.source_language,
            target_language=result.target_language,
            provider=result.provider,
            confidence=result.confidence,
            processing_time=result.processing_time,
            cached=result.cached
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task for caching popular translations
async def cache_popular_translations(db: Session):
    """Background task to pre-cache popular translations"""
    common_phrases = [
        "Hello", "Thank you", "Good morning", "Good evening",
        "How are you?", "Nice to meet you", "Goodbye"
    ]
    
    popular_languages = ["es", "fr", "de", "zh", "ja", "ko"]
    
    for phrase in common_phrases:
        for lang in popular_languages:
            request = SystemTranslationRequest(
                text=phrase,
                source_language="en",
                target_language=lang,
                provider=TranslationProvider.GOOGLE
            )
            await translation_system.translate_text(request)

@router.post("/cache-warmup")
async def warmup_cache(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Warm up translation cache with common phrases"""
    background_tasks.add_task(cache_popular_translations, db)
    return {"message": "Cache warmup initiated"}