"""
Text-to-Speech API Endpoints
FastAPI endpoints for TTS synthesis functionality
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import base64
import io
import logging
from datetime import datetime

from api.dependencies import get_current_user, require_roles
from api.middleware.quota_enforcement import require_quota, track_tts_usage
from database.connection import get_db
from sqlalchemy.orm import Session

# Import TTS functionality
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import tts
from elevenlabs import VoiceSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tts")

# Pydantic models
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice: Optional[str] = Field(default="default", description="Voice to use for synthesis")
    language: Optional[str] = Field(default="en", description="Language code")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Voice pitch")
    format: Optional[str] = Field(default="mp3", description="Output audio format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, this is a test of the text-to-speech system.",
                "voice": "emily",
                "language": "en",
                "speed": 1.0,
                "pitch": 1.0,
                "format": "mp3"
            }
        }

class VoiceInfo(BaseModel):
    id: str
    name: str
    language: str
    gender: Optional[str]
    description: Optional[str]
    sample_url: Optional[str]

class TTSResponse(BaseModel):
    audio_data: str  # Base64 encoded audio
    format: str
    duration: float
    size_bytes: int
    synthesis_time: float

@router.post("/synthesize", response_model=TTSResponse)
@require_quota('api_calls', 1)  # Enforce API call quota
async def synthesize_speech(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synthesize speech from text
    
    Returns base64 encoded audio data
    """
    try:
        start_time = datetime.now()
        
        # Log the request
        logger.info(f"TTS request from user {current_user['id']}: {len(request.text)} chars")
        
        # Create voice settings
        voice_settings = VoiceSettings(
            stability=0.75,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
        
        # Synthesize speech using the TTS module
        audio_file_path = tts.synthesize_speech(
            text=request.text,
            voice_id=request.voice,
            voice_settings=voice_settings,
            output_format=request.format
        )
        
        # Read audio file and convert to base64
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Clean up temporary file
        os.unlink(audio_file_path)
        
        # Calculate synthesis time
        synthesis_time = (datetime.now() - start_time).total_seconds()
        
        return TTSResponse(
            audio_data=audio_base64,
            format=request.format,
            duration=0,  # Would need audio analysis to get actual duration
            size_bytes=len(audio_data),
            synthesis_time=synthesis_time
        )
        
    except Exception as e:
        logger.error(f"TTS synthesis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to synthesize speech: {str(e)}"
        )

@router.get("/voices", response_model=List[VoiceInfo])
async def list_available_voices(
    language: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of available TTS voices
    
    Optionally filter by language
    """
    try:
        voices_data = tts.list_available_voices()
        
        # Filter by language if specified
        if language:
            voices_data = [v for v in voices_data if v.get('labels', {}).get('language', '').startswith(language)]
        
        return [
            VoiceInfo(
                id=v['voice_id'],
                name=v['name'],
                language=v.get('labels', {}).get('language', 'en'),
                gender=v.get('labels', {}).get('gender'),
                description=v.get('description', ''),
                sample_url=v.get('preview_url')
            )
            for v in voices_data
        ]
        
    except Exception as e:
        logger.error(f"Error listing voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list voices: {str(e)}"
        )

@router.get("/languages")
async def list_supported_languages(
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported languages for TTS"""
    try:
        # Get languages from available voices
        voices_data = tts.list_available_voices()
        languages = set()
        
        for voice in voices_data:
            lang = voice.get('labels', {}).get('language')
            if lang:
                languages.add(lang)
        
        return [{"code": lang, "name": lang} for lang in sorted(languages)]
        
    except Exception as e:
        logger.error(f"Error listing languages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list languages: {str(e)}"
        )

@router.post("/preview")
async def preview_voice(
    voice_id: str,
    text: Optional[str] = "Hello, this is a preview of the selected voice.",
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a preview of a specific voice
    
    Returns audio file directly
    """
    try:
        # Synthesize preview
        audio_data, metadata = await tts_engine.synthesize(
            text=text[:100],  # Limit preview text length
            voice=voice_id,
            output_format="mp3"
        )
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=preview_{voice_id}.mp3"
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.post("/batch")
async def batch_synthesize(
    texts: List[TTSRequest],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synthesize multiple texts in batch
    
    Admin only endpoint for bulk processing
    """
    # Require admin role for batch processing
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if len(texts) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 texts per batch request"
        )
    
    try:
        results = []
        
        for i, request in enumerate(texts):
            try:
                # Synthesize each text
                audio_data, metadata = await tts_engine.synthesize(
                    text=request.text,
                    voice=request.voice,
                    language=request.language,
                    speed=request.speed,
                    pitch=request.pitch,
                    output_format=request.format
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                    "format": request.format,
                    "duration": metadata.get('duration', 0),
                    "size_bytes": len(audio_data)
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total": len(texts),
            "successful": sum(1 for r in results if r['success']),
            "failed": sum(1 for r in results if not r['success']),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch TTS error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch synthesis failed: {str(e)}"
        )

@router.get("/usage/stats")
async def get_tts_usage_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get TTS usage statistics
    
    Admin endpoint for monitoring usage
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # TODO: Implement actual usage tracking
        # For now, return mock data
        return {
            "total_requests": 1234,
            "total_characters": 567890,
            "total_duration_seconds": 4567.8,
            "average_request_size": 460,
            "popular_voices": [
                {"voice": "emily", "count": 456},
                {"voice": "john", "count": 345},
                {"voice": "sarah", "count": 234}
            ],
            "languages": [
                {"language": "en", "count": 890},
                {"language": "es", "count": 234},
                {"language": "fr", "count": 110}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting TTS stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage stats: {str(e)}"
        )

# Additional advanced TTS endpoints

class TTSVoiceSettingsRequest(BaseModel):
    stability: float = Field(0.75, ge=0.0, le=1.0, description="Voice stability")
    similarity_boost: float = Field(0.75, ge=0.0, le=1.0, description="Similarity boost")
    style: float = Field(0.0, ge=0.0, le=1.0, description="Style exaggeration")
    use_speaker_boost: bool = Field(True, description="Use speaker boost")

class TTSAdvancedRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    voice_settings: Optional[TTSVoiceSettingsRequest] = None
    output_format: str = Field("mp3", description="Output format (mp3, wav)")

@router.post("/synthesize/advanced", response_model=TTSResponse)
@require_quota('api_calls', 1, 'advanced_analytics')  # Require advanced feature access
async def synthesize_speech_advanced(
    request: TTSAdvancedRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Advanced TTS synthesis with full voice control
    
    Provides access to ElevenLabs voice settings for fine-tuned control
    """
    try:
        start_time = datetime.now()
        
        # Create voice settings
        if request.voice_settings:
            voice_settings = VoiceSettings(
                stability=request.voice_settings.stability,
                similarity_boost=request.voice_settings.similarity_boost,
                style=request.voice_settings.style,
                use_speaker_boost=request.voice_settings.use_speaker_boost
            )
        else:
            voice_settings = None
        
        # Synthesize speech
        audio_file_path = tts.synthesize_speech(
            text=request.text,
            voice_id=request.voice_id,
            voice_settings=voice_settings,
            output_format=request.output_format
        )
        
        # Read and encode audio
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Clean up
        os.unlink(audio_file_path)
        
        synthesis_time = (datetime.now() - start_time).total_seconds()
        
        return TTSResponse(
            audio_data=audio_base64,
            format=request.output_format,
            duration=0,
            size_bytes=len(audio_data),
            synthesis_time=synthesis_time
        )
        
    except Exception as e:
        logger.error(f"Advanced TTS error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Advanced synthesis failed: {str(e)}"
        )

@router.get("/voices/search")
async def search_voices(
    query: str,
    language: Optional[str] = None,
    gender: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Search for voices by name, description, or characteristics
    """
    try:
        voices_data = tts.list_available_voices()
        
        # Filter by search criteria
        filtered_voices = []
        
        for voice in voices_data:
            # Check query match
            if query.lower() not in voice['name'].lower() and \
               query.lower() not in voice.get('description', '').lower():
                continue
            
            # Check language filter
            if language and voice.get('labels', {}).get('language') != language:
                continue
            
            # Check gender filter
            if gender and voice.get('labels', {}).get('gender') != gender:
                continue
            
            filtered_voices.append(VoiceInfo(
                id=voice['voice_id'],
                name=voice['name'],
                language=voice.get('labels', {}).get('language', 'en'),
                gender=voice.get('labels', {}).get('gender'),
                description=voice.get('description', ''),
                sample_url=voice.get('preview_url')
            ))
        
        return filtered_voices
        
    except Exception as e:
        logger.error(f"Voice search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice search failed: {str(e)}"
        )

@router.get("/voice/{voice_id}")
async def get_voice_details(
    voice_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific voice
    """
    try:
        voice = tts.get_voice_by_name(voice_id)
        
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        return VoiceInfo(
            id=voice['voice_id'],
            name=voice['name'],
            language=voice.get('labels', {}).get('language', 'en'),
            gender=voice.get('labels', {}).get('gender'),
            description=voice.get('description', ''),
            sample_url=voice.get('preview_url')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get voice details error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get voice details: {str(e)}"
        )

@router.post("/estimate-cost")
async def estimate_synthesis_cost(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Estimate the cost of synthesizing given text
    """
    try:
        cost = tts.estimate_synthesis_cost(text)
        
        return {
            "text_length": len(text),
            "character_count": len(text),
            "estimated_cost_usd": cost,
            "cost_per_character": cost / len(text) if len(text) > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Cost estimation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cost estimation failed: {str(e)}"
        )

@router.get("/synthesis-history")
async def get_synthesis_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's TTS synthesis history
    """
    try:
        history = tts.get_synthesis_history()
        
        # Limit results
        limited_history = history[:limit] if len(history) > limit else history
        
        return {
            "total_syntheses": len(history),
            "returned_count": len(limited_history),
            "history": limited_history
        }
        
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get synthesis history: {str(e)}"
        )