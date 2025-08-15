"""
Voice Profiling and Analysis API Endpoints
Connects React frontend to the existing VoiceProfilingAnalysisSystem
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import asyncio
import logging
import tempfile
import os
from datetime import datetime

# Import existing voice profiling system
try:
    from voice_profiling_analysis import (
        VoiceProfilingAnalysisSystem,
        AnalysisType,
        EmotionType,
        VoiceProfile,
        AnalysisResult
    )
except ImportError:
    # Fallback if module not available
    VoiceProfilingAnalysisSystem = None
    AnalysisType = None
    EmotionType = None
    VoiceProfile = None
    AnalysisResult = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice-profiling", tags=["voice-profiling"])

# Global voice profiling system instance
_voice_system: Optional[VoiceProfilingAnalysisSystem] = None

def get_voice_system() -> VoiceProfilingAnalysisSystem:
    """Get or create voice profiling system instance"""
    global _voice_system
    if _voice_system is None and VoiceProfilingAnalysisSystem:
        _voice_system = VoiceProfilingAnalysisSystem()
    return _voice_system

# Request/Response Models
class VoiceAnalysisRequest(BaseModel):
    analysis_types: List[str] = Field(
        default=["emotion", "identification", "stress"],
        description="Types of analysis to perform"
    )
    speaker_id: Optional[str] = Field(None, description="Known speaker ID for comparison")
    real_time: bool = Field(False, description="Enable real-time analysis")

class VoiceProfileResponse(BaseModel):
    profile_id: str
    name: str
    voice_characteristics: Dict[str, Any]
    enrollment_date: str
    last_seen: Optional[str]
    recognition_count: int

class EmotionAnalysisResponse(BaseModel):
    primary_emotion: str
    emotion_scores: Dict[str, float]
    valence: float
    arousal: float
    confidence: float
    timestamp: str

class SpeakerIdentificationResponse(BaseModel):
    identified_speaker: Optional[str]
    confidence: float
    similarity_scores: Dict[str, float]
    is_known_speaker: bool

class VoiceAnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: str
    audio_duration: float
    results: Dict[str, Any]
    processing_time_ms: int

class SpeakerEnrollmentRequest(BaseModel):
    name: str
    profile_id: Optional[str] = None
    description: Optional[str] = None

@router.post("/analyze", response_model=VoiceAnalysisResponse)
async def analyze_voice(
    audio_file: UploadFile = File(...),
    request: VoiceAnalysisRequest = Depends(),
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Perform comprehensive voice analysis on uploaded audio
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        start_time = datetime.now()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Convert analysis types
            analysis_types = []
            for analysis_type in request.analysis_types:
                if hasattr(AnalysisType, analysis_type.upper()):
                    analysis_types.append(getattr(AnalysisType, analysis_type.upper()))
            
            # Perform analysis
            results = await voice_system.analyze_voice(
                audio_file=temp_file_path,
                analysis_types=analysis_types,
                speaker_id=request.speaker_id
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Format results
            formatted_results = {}
            for result in results:
                if result.analysis_type == AnalysisType.EMOTION:
                    formatted_results["emotion"] = {
                        "primary_emotion": result.emotion.value if result.emotion else "neutral",
                        "emotion_scores": result.emotion_scores,
                        "valence": result.valence or 0.0,
                        "arousal": result.arousal or 0.0,
                        "confidence": result.confidence
                    }
                elif result.analysis_type == AnalysisType.IDENTIFICATION:
                    formatted_results["identification"] = {
                        "identified_speaker": result.speaker_id,
                        "confidence": result.confidence,
                        "similarity_score": result.similarity_score or 0.0,
                        "is_known_speaker": result.speaker_id is not None
                    }
                elif result.analysis_type == AnalysisType.STRESS:
                    formatted_results["stress"] = {
                        "stress_level": result.stress_level or 0.0,
                        "fatigue_level": result.fatigue_level or 0.0,
                        "voice_quality": result.voice_quality or 0.0,
                        "confidence": result.confidence
                    }
            
            return VoiceAnalysisResponse(
                analysis_id=f"analysis_{int(start_time.timestamp())}",
                timestamp=start_time.isoformat(),
                audio_duration=len(content) / 16000.0,  # Approximate duration
                results=formatted_results,
                processing_time_ms=int(processing_time)
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Voice analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice analysis failed: {str(e)}")

@router.post("/enroll", response_model=VoiceProfileResponse)
async def enroll_speaker(
    audio_files: List[UploadFile] = File(...),
    request: SpeakerEnrollmentRequest = Depends(),
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Enroll a new speaker with voice samples
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        # Save uploaded files temporarily
        temp_files = []
        for audio_file in audio_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                content = await audio_file.read()
                temp_file.write(content)
                temp_files.append(temp_file.name)
        
        try:
            # Enroll speaker
            profile = await voice_system.speaker_identification.enroll_speaker(
                name=request.name,
                audio_files=temp_files,
                profile_id=request.profile_id
            )
            
            return VoiceProfileResponse(
                profile_id=profile.profile_id,
                name=profile.name,
                voice_characteristics=profile.voice_characteristics,
                enrollment_date=profile.enrollment_date.isoformat(),
                last_seen=profile.last_seen.isoformat() if profile.last_seen else None,
                recognition_count=profile.recognition_count
            )
            
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
    except Exception as e:
        logger.error(f"Speaker enrollment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speaker enrollment failed: {str(e)}")

@router.get("/profiles", response_model=List[VoiceProfileResponse])
async def get_voice_profiles(
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Get all enrolled voice profiles
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        profiles = []
        for profile_id, profile in voice_system.speaker_identification.profiles.items():
            profiles.append(VoiceProfileResponse(
                profile_id=profile.profile_id,
                name=profile.name,
                voice_characteristics=profile.voice_characteristics,
                enrollment_date=profile.enrollment_date.isoformat(),
                last_seen=profile.last_seen.isoformat() if profile.last_seen else None,
                recognition_count=profile.recognition_count
            ))
        
        return profiles
        
    except Exception as e:
        logger.error(f"Failed to get voice profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice profiles: {str(e)}")

@router.get("/profiles/{profile_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(
    profile_id: str,
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Get specific voice profile by ID
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        profile = voice_system.speaker_identification.profiles.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        
        return VoiceProfileResponse(
            profile_id=profile.profile_id,
            name=profile.name,
            voice_characteristics=profile.voice_characteristics,
            enrollment_date=profile.enrollment_date.isoformat(),
            last_seen=profile.last_seen.isoformat() if profile.last_seen else None,
            recognition_count=profile.recognition_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get voice profile: {str(e)}")

@router.delete("/profiles/{profile_id}")
async def delete_voice_profile(
    profile_id: str,
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Delete a voice profile
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        if profile_id not in voice_system.speaker_identification.profiles:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        
        del voice_system.speaker_identification.profiles[profile_id]
        if profile_id in voice_system.speaker_identification.gmm_models:
            del voice_system.speaker_identification.gmm_models[profile_id]
        
        return {"status": "success", "message": f"Voice profile {profile_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete voice profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete voice profile: {str(e)}")

@router.get("/emotions/timeline")
async def get_emotion_timeline(
    audio_file: UploadFile = File(...),
    window_size: float = 5.0,
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Get emotion timeline for audio file
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Analyze emotion timeline
            timeline = await voice_system._analyze_emotion_timeline(
                temp_file_path, 
                window_size=window_size
            )
            
            return {
                "timeline": timeline,
                "window_size": window_size,
                "total_duration": len(timeline) * window_size
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Emotion timeline analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Emotion timeline analysis failed: {str(e)}")

@router.get("/stats")
async def get_voice_profiling_stats(
    voice_system: VoiceProfilingAnalysisSystem = Depends(get_voice_system)
):
    """
    Get voice profiling system statistics
    """
    if not voice_system:
        raise HTTPException(status_code=503, detail="Voice profiling system not available")
    
    try:
        stats = {
            "enrolled_speakers": len(voice_system.speaker_identification.profiles),
            "total_analyses": 0,  # Would need to track this
            "supported_emotions": [emotion.value for emotion in EmotionType] if EmotionType else [],
            "analysis_types": [analysis.value for analysis in AnalysisType] if AnalysisType else [],
            "system_status": "operational"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        voice_system = get_voice_system()
        return {
            "status": "healthy" if voice_system else "degraded",
            "voice_profiling_system": "operational" if voice_system else "unavailable",
            "components": {
                "emotion_detector": voice_system.emotion_detector is not None if voice_system else False,
                "speaker_identification": voice_system.speaker_identification is not None if voice_system else False,
                "stress_analyzer": voice_system.stress_analyzer is not None if voice_system else False
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }