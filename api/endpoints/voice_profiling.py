#!/usr/bin/env python3
"""
API endpoints for Voice Profiling and Analysis System
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List, Optional
import json
import logging
import asyncio
from datetime import datetime
import hashlib
import tempfile
import os
from pathlib import Path

from voice_profiling_analysis import (
    VoiceProfilingAnalysisSystem,
    AnalysisType,
    VoiceProfile,
    AnalysisConfig
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/voice-profiling", tags=["voice-profiling"])

# Global voice profiling system instance
voice_system = VoiceProfilingAnalysisSystem()


@router.post("/profile/create")
async def create_voice_profile(
    name: str = Form(...),
    audio_files: List[UploadFile] = File(...),
    metadata: Optional[str] = Form(None)
) -> JSONResponse:
    """Create a new voice profile from audio samples"""
    
    try:
        # Save uploaded files temporarily
        temp_files = []
        for audio_file in audio_files:
            temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
            with open(temp_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            temp_files.append(temp_path)
        
        # Parse metadata if provided
        profile_metadata = json.loads(metadata) if metadata else {}
        
        # Create voice profile
        profile = voice_system.enroll_speaker(
            name=name,
            audio_files=temp_files
        )
        
        # Clean up temp files
        for temp_file in temp_files:
            os.unlink(temp_file)
        
        return JSONResponse({
            "profile_id": profile.profile_id,
            "name": profile.name,
            "created_at": profile.created_at.isoformat(),
            "characteristics": profile.characteristics,
            "embedding_size": len(profile.embeddings) if profile.embeddings is not None else 0,
            "metadata": profile.metadata
        })
        
    except Exception as e:
        logger.error(f"Failed to create voice profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze")
async def analyze_voice(
    audio_file: UploadFile = File(...),
    analysis_types: str = Form(...),
    config: Optional[str] = Form(None)
) -> JSONResponse:
    """Analyze voice from audio file"""
    
    try:
        # Parse analysis types
        types_list = [AnalysisType[t.strip().upper()] for t in analysis_types.split(",")]
        
        # Parse config if provided
        analysis_config = None
        if config:
            config_data = json.loads(config)
            analysis_config = AnalysisConfig(**config_data)
        
        # Save uploaded file temporarily
        temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Perform analysis
        result = await voice_system.analyze_voice(
            audio_file=temp_path,
            analysis_types=types_list,
            config=analysis_config
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Format response
        response = {
            "timestamp": result.timestamp.isoformat(),
            "duration": result.duration,
            "analyses": {}
        }
        
        # Add analysis results
        if result.emotion_result:
            response["analyses"]["emotion"] = {
                "primary": result.emotion_result.primary_emotion,
                "scores": result.emotion_result.emotion_scores,
                "confidence": result.emotion_result.confidence,
                "valence": result.emotion_result.valence,
                "arousal": result.emotion_result.arousal
            }
        
        if result.stress_result:
            response["analyses"]["stress"] = {
                "level": result.stress_result.stress_level,
                "score": result.stress_result.stress_score,
                "indicators": result.stress_result.indicators,
                "confidence": result.stress_result.confidence
            }
        
        if result.health_result:
            response["analyses"]["health"] = {
                "indicators": result.health_result.indicators,
                "risk_factors": result.health_result.risk_factors,
                "recommendations": result.health_result.recommendations,
                "confidence": result.health_result.confidence
            }
        
        if result.speaker_result:
            response["analyses"]["speaker"] = {
                "identity": result.speaker_result.speaker_id,
                "confidence": result.speaker_result.confidence,
                "verified": result.speaker_result.verified,
                "similarity": result.speaker_result.similarity_score
            }
        
        if result.quality_result:
            response["analyses"]["quality"] = {
                "scores": result.quality_result.quality_scores,
                "issues": result.quality_result.issues,
                "overall": result.quality_result.overall_score
            }
        
        if result.acoustic_features:
            response["acoustic_features"] = result.acoustic_features
        
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Voice analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify")
async def verify_speaker(
    profile_id: str = Form(...),
    audio_file: UploadFile = File(...),
    threshold: Optional[float] = Form(0.85)
) -> JSONResponse:
    """Verify speaker identity against a profile"""
    
    try:
        # Save uploaded file temporarily
        temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Verify speaker
        verification_result = voice_system.verify_speaker(
            profile_id=profile_id,
            audio_file=temp_path,
            threshold=threshold
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        return JSONResponse({
            "verified": verification_result["verified"],
            "confidence": verification_result["confidence"],
            "similarity_score": verification_result["similarity"],
            "profile_id": profile_id,
            "threshold": threshold
        })
        
    except Exception as e:
        logger.error(f"Speaker verification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/identify")
async def identify_speaker(
    audio_file: UploadFile = File(...),
    candidate_profiles: Optional[str] = Form(None)
) -> JSONResponse:
    """Identify speaker from enrolled profiles"""
    
    try:
        # Save uploaded file temporarily
        temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Parse candidate profiles if provided
        candidates = None
        if candidate_profiles:
            candidates = json.loads(candidate_profiles)
        
        # Identify speaker
        identification_result = voice_system.identify_speaker(
            audio_file=temp_path,
            candidate_profiles=candidates
        )
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if identification_result:
            return JSONResponse({
                "identified": True,
                "profile_id": identification_result["profile_id"],
                "name": identification_result["name"],
                "confidence": identification_result["confidence"],
                "similarity": identification_result["similarity"]
            })
        else:
            return JSONResponse({
                "identified": False,
                "message": "No matching speaker found"
            })
        
    except Exception as e:
        logger.error(f"Speaker identification failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles")
async def list_profiles() -> JSONResponse:
    """List all voice profiles"""
    
    profiles = voice_system.get_all_profiles()
    
    formatted_profiles = [
        {
            "profile_id": profile["profile_id"],
            "name": profile["name"],
            "created_at": profile["created_at"],
            "characteristics": profile["characteristics"],
            "audio_count": profile["audio_count"]
        }
        for profile in profiles
    ]
    
    return JSONResponse({
        "profiles": formatted_profiles,
        "total": len(formatted_profiles)
    })


@router.get("/profile/{profile_id}")
async def get_profile(profile_id: str) -> JSONResponse:
    """Get details of a specific profile"""
    
    profile = voice_system.get_profile(profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return JSONResponse({
        "profile_id": profile["profile_id"],
        "name": profile["name"],
        "created_at": profile["created_at"],
        "characteristics": profile["characteristics"],
        "audio_count": profile["audio_count"],
        "metadata": profile.get("metadata", {})
    })


@router.delete("/profile/{profile_id}")
async def delete_profile(profile_id: str) -> JSONResponse:
    """Delete a voice profile"""
    
    success = voice_system.delete_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return JSONResponse({
        "message": "Profile deleted successfully",
        "profile_id": profile_id
    })


@router.post("/profile/{profile_id}/update")
async def update_profile(
    profile_id: str,
    audio_files: Optional[List[UploadFile]] = File(None),
    name: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
) -> JSONResponse:
    """Update a voice profile with new audio samples"""
    
    try:
        profile = voice_system.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Add new audio samples if provided
        if audio_files:
            temp_files = []
            for audio_file in audio_files:
                temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
                with open(temp_path, "wb") as f:
                    content = await audio_file.read()
                    f.write(content)
                temp_files.append(temp_path)
            
            # Update profile with new samples
            voice_system.update_profile(profile_id, audio_files=temp_files)
            
            # Clean up temp files
            for temp_file in temp_files:
                os.unlink(temp_file)
        
        # Update metadata if provided
        if metadata:
            profile_metadata = json.loads(metadata)
            voice_system.update_profile(profile_id, metadata=profile_metadata)
        
        # Update name if provided
        if name:
            voice_system.update_profile(profile_id, name=name)
        
        return JSONResponse({
            "message": "Profile updated successfully",
            "profile_id": profile_id
        })
        
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare")
async def compare_voices(
    audio_file1: UploadFile = File(...),
    audio_file2: UploadFile = File(...)
) -> JSONResponse:
    """Compare two voice samples"""
    
    try:
        # Save uploaded files temporarily
        temp_path1 = tempfile.mktemp(suffix=Path(audio_file1.filename).suffix)
        temp_path2 = tempfile.mktemp(suffix=Path(audio_file2.filename).suffix)
        
        with open(temp_path1, "wb") as f:
            content = await audio_file1.read()
            f.write(content)
        
        with open(temp_path2, "wb") as f:
            content = await audio_file2.read()
            f.write(content)
        
        # Compare voices
        comparison_result = voice_system.compare_voices(temp_path1, temp_path2)
        
        # Clean up temp files
        os.unlink(temp_path1)
        os.unlink(temp_path2)
        
        return JSONResponse({
            "similarity": comparison_result["similarity"],
            "same_speaker": comparison_result["same_speaker"],
            "confidence": comparison_result["confidence"],
            "feature_comparison": comparison_result.get("features", {})
        })
        
    except Exception as e:
        logger.error(f"Voice comparison failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch/analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    analysis_types: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> JSONResponse:
    """Batch analyze multiple audio files"""
    
    try:
        # Parse analysis types
        types_list = [AnalysisType[t.strip().upper()] for t in analysis_types.split(",")]
        
        # Create batch job ID
        batch_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()
        
        # Save files and prepare batch
        batch_files = []
        for audio_file in files:
            temp_path = tempfile.mktemp(suffix=Path(audio_file.filename).suffix)
            with open(temp_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            batch_files.append({
                "path": temp_path,
                "name": audio_file.filename
            })
        
        # Start batch processing in background
        background_tasks.add_task(
            process_batch_analysis,
            batch_id,
            batch_files,
            types_list,
            voice_system
        )
        
        return JSONResponse({
            "batch_id": batch_id,
            "status": "processing",
            "file_count": len(files),
            "analysis_types": [t.value for t in types_list]
        })
        
    except Exception as e:
        logger.error(f"Batch analysis failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def process_batch_analysis(
    batch_id: str,
    batch_files: List[Dict[str, str]],
    analysis_types: List[AnalysisType],
    system: VoiceProfilingAnalysisSystem
):
    """Process batch analysis in background"""
    
    results = []
    for file_info in batch_files:
        try:
            result = await system.analyze_voice(
                audio_file=file_info["path"],
                analysis_types=analysis_types
            )
            results.append({
                "file": file_info["name"],
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "file": file_info["name"],
                "success": False,
                "error": str(e)
            })
        finally:
            # Clean up temp file
            os.unlink(file_info["path"])
    
    # Store results (in production, use a database or cache)
    # For now, just log completion
    logger.info(f"Batch {batch_id} completed with {len(results)} results")


@router.get("/analysis-types")
async def list_analysis_types() -> JSONResponse:
    """List available analysis types"""
    
    types = [
        {
            "name": analysis_type.value,
            "description": f"Analyze {analysis_type.value} aspects of voice"
        }
        for analysis_type in AnalysisType
    ]
    
    return JSONResponse({"analysis_types": types})


@router.post("/export/{profile_id}")
async def export_profile(profile_id: str, format: str = "json") -> FileResponse:
    """Export voice profile data"""
    
    profile = voice_system.get_profile(profile_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Create export file
    export_path = f"/tmp/voice_profile_{profile_id}.{format}"
    
    if format == "json":
        with open(export_path, "w") as f:
            json.dump(profile, f, indent=2, default=str)
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    return FileResponse(
        export_path,
        media_type="application/json",
        filename=f"voice_profile_{profile_id}.{format}"
    )