"""
Voice Cloning and Synthesis API Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import tempfile
import os
import io
import json
from datetime import datetime
import asyncio
import soundfile as sf
import numpy as np

from ...voice_cloning_synthesis import (
    VoiceCloningSynthesisSystem,
    SynthesisRequest,
    VoiceProfile
)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize voice system
voice_system = VoiceCloningSynthesisSystem()


class VoiceCloneRequest(BaseModel):
    """Request model for voice cloning"""
    profile_name: str
    fine_tune_steps: int = Field(default=500, ge=0, le=5000)
    auto_enhance: bool = True


class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    text: str = Field(..., min_length=1, max_length=5000)
    voice_profile_id: str
    output_format: str = Field(default="wav", pattern="^(wav|mp3|ogg)$")
    sample_rate: int = Field(default=22050, ge=8000, le=48000)
    emotion: Optional[str] = Field(default=None, pattern="^(happy|sad|angry|calm|excited|neutral)$")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch_shift: float = Field(default=0.0, ge=-12, le=12)


class VoiceConversionRequest(BaseModel):
    """Request model for voice conversion"""
    target_profile_id: str
    preserve_prosody: bool = True
    output_format: str = Field(default="wav", pattern="^(wav|mp3|ogg)$")


class BatchSynthesisRequest(BaseModel):
    """Request model for batch synthesis"""
    texts: List[str] = Field(..., min_items=1, max_items=100)
    voice_profile_id: str
    parallel: bool = True
    output_format: str = Field(default="wav", pattern="^(wav|mp3|ogg)$")


@router.post("/clone")
async def clone_voice(
    background_tasks: BackgroundTasks,
    profile_name: str = Form(...),
    fine_tune_steps: int = Form(500),
    auto_enhance: bool = Form(True),
    audio_files: List[UploadFile] = File(..., description="Audio files for voice cloning")
):
    """
    Clone a voice from uploaded audio samples
    
    - **profile_name**: Name for the voice profile
    - **fine_tune_steps**: Number of fine-tuning steps (0-5000)
    - **auto_enhance**: Automatically enhance audio quality
    - **audio_files**: Audio samples of the target voice (WAV, MP3, or OGG)
    """
    
    if len(audio_files) < 1:
        raise HTTPException(status_code=400, detail="At least one audio file is required")
    
    if len(audio_files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 audio files allowed")
    
    temp_files = []
    
    try:
        # Save uploaded files temporarily
        for audio_file in audio_files:
            # Validate file type
            if not audio_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {audio_file.content_type}")
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                content = await audio_file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
        
        # Clone voice
        result = await voice_system.clone_voice(
            audio_files=temp_files,
            profile_name=profile_name,
            fine_tune_steps=fine_tune_steps
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error_message or "Voice cloning failed")
        
        return {
            "profile_id": result.profile_id,
            "success": result.success,
            "quality_score": result.quality_score,
            "training_time": result.training_time,
            "characteristics": result.characteristics,
            "message": f"Voice profile '{profile_name}' created successfully"
        }
        
    finally:
        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


@router.post("/synthesize")
async def synthesize_speech(request: TextToSpeechRequest):
    """
    Synthesize speech using a cloned voice profile
    
    - **text**: Text to synthesize
    - **voice_profile_id**: ID of the voice profile to use
    - **emotion**: Optional emotion to apply
    - **speed**: Speech speed multiplier (0.5-2.0)
    - **pitch_shift**: Pitch shift in semitones (-12 to 12)
    """
    
    try:
        # Create synthesis request
        synth_request = SynthesisRequest(
            text=request.text,
            voice_profile_id=request.voice_profile_id,
            output_format=request.output_format,
            sample_rate=request.sample_rate,
            emotion=request.emotion,
            speed=request.speed,
            pitch_shift=request.pitch_shift
        )
        
        # Synthesize speech
        audio, sr = await voice_system.synthesize_speech(synth_request)
        
        # Convert to requested format
        output_buffer = io.BytesIO()
        sf.write(output_buffer, audio, sr, format=request.output_format.upper())
        output_buffer.seek(0)
        
        return StreamingResponse(
            output_buffer,
            media_type=f"audio/{request.output_format}",
            headers={
                "Content-Disposition": f"attachment; filename=synthesized_{datetime.now().timestamp()}.{request.output_format}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@router.post("/convert")
async def convert_voice(
    request: VoiceConversionRequest,
    source_audio: UploadFile = File(..., description="Source audio file to convert")
):
    """
    Convert voice from source audio to target voice profile
    
    - **source_audio**: Audio file to convert
    - **target_profile_id**: Target voice profile ID
    - **preserve_prosody**: Whether to preserve original prosody
    """
    
    if not source_audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {source_audio.content_type}")
    
    temp_file = None
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await source_audio.read()
            tmp_file.write(content)
            temp_file = tmp_file.name
        
        # Perform voice conversion
        converted_audio = await voice_system.voice_conversion(
            source_audio=temp_file,
            target_profile_id=request.target_profile_id,
            preserve_prosody=request.preserve_prosody
        )
        
        # Convert to requested format
        output_buffer = io.BytesIO()
        sf.write(output_buffer, converted_audio, 22050, format=request.output_format.upper())
        output_buffer.seek(0)
        
        return StreamingResponse(
            output_buffer,
            media_type=f"audio/{request.output_format}",
            headers={
                "Content-Disposition": f"attachment; filename=converted_{datetime.now().timestamp()}.{request.output_format}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice conversion failed: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


@router.post("/batch-synthesize")
async def batch_synthesize(request: BatchSynthesisRequest):
    """
    Synthesize multiple texts in batch
    
    - **texts**: List of texts to synthesize
    - **voice_profile_id**: Voice profile to use
    - **parallel**: Process in parallel or sequentially
    """
    
    try:
        # Synthesize all texts
        audio_results = await voice_system.batch_synthesis(
            texts=request.texts,
            voice_profile_id=request.voice_profile_id,
            parallel=request.parallel
        )
        
        # Create a zip file with all audio files
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, (text, audio) in enumerate(zip(request.texts, audio_results)):
                # Create audio buffer
                audio_buffer = BytesIO()
                sf.write(audio_buffer, audio, 22050, format=request.output_format.upper())
                audio_buffer.seek(0)
                
                # Add to zip
                filename = f"audio_{i+1}_{text[:30]}.{request.output_format}"
                zip_file.writestr(filename, audio_buffer.read())
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=batch_synthesis_{datetime.now().timestamp()}.zip"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch synthesis failed: {str(e)}")


@router.get("/profiles")
async def list_voice_profiles():
    """
    Get all available voice profiles
    """
    
    profiles = voice_system.get_voice_profiles()
    
    return {
        "profiles": profiles,
        "total": len(profiles)
    }


@router.get("/profiles/{profile_id}")
async def get_voice_profile(profile_id: str):
    """
    Get details of a specific voice profile
    """
    
    if profile_id not in voice_system.voice_profiles:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    profile = voice_system.voice_profiles[profile_id]
    
    return {
        "profile_id": profile.profile_id,
        "name": profile.name,
        "created_at": profile.created_at.isoformat(),
        "characteristics": profile.characteristics,
        "has_custom_model": profile.model_checkpoint is not None,
        "metadata": profile.metadata
    }


@router.delete("/profiles/{profile_id}")
async def delete_voice_profile(profile_id: str):
    """
    Delete a voice profile
    """
    
    success = voice_system.delete_voice_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    return {
        "success": True,
        "message": f"Voice profile {profile_id} deleted successfully"
    }


@router.post("/profiles/{profile_id}/export")
async def export_voice_profile(profile_id: str):
    """
    Export a voice profile for sharing
    """
    
    if profile_id not in voice_system.voice_profiles:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    
    try:
        # Create temp file for export
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            export_path = tmp_file.name
        
        # Export profile
        success = await voice_system.export_voice_profile(profile_id, export_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="Export failed")
        
        # Return file
        return FileResponse(
            export_path,
            media_type="application/json",
            filename=f"voice_profile_{profile_id}.json"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/profiles/import")
async def import_voice_profile(
    profile_file: UploadFile = File(..., description="Voice profile JSON file")
):
    """
    Import a voice profile from file
    """
    
    if not profile_file.content_type == 'application/json':
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")
    
    temp_file = None
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            content = await profile_file.read()
            tmp_file.write(content.decode('utf-8'))
            temp_file = tmp_file.name
        
        # Import profile
        profile_id = await voice_system.import_voice_profile(temp_file)
        
        return {
            "success": True,
            "profile_id": profile_id,
            "message": "Voice profile imported successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


@router.post("/analyze")
async def analyze_voice(
    audio_file: UploadFile = File(..., description="Audio file to analyze")
):
    """
    Analyze voice characteristics from an audio file
    """
    
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail=f"Invalid file type: {audio_file.content_type}")
    
    temp_file = None
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            temp_file = tmp_file.name
        
        # Analyze voice characteristics
        characteristics = await voice_system._analyze_voice_characteristics([temp_file])
        
        return {
            "characteristics": characteristics,
            "filename": audio_file.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


@router.websocket("/stream-synthesis")
async def stream_synthesis(websocket):
    """
    WebSocket endpoint for real-time speech synthesis streaming
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive synthesis request
            data = await websocket.receive_json()
            
            request = TextToSpeechRequest(**data)
            
            # Create synthesis request
            synth_request = SynthesisRequest(
                text=request.text,
                voice_profile_id=request.voice_profile_id,
                emotion=request.emotion,
                speed=request.speed,
                pitch_shift=request.pitch_shift
            )
            
            # Synthesize speech
            audio, sr = await voice_system.synthesize_speech(synth_request)
            
            # Convert to bytes and send chunks
            audio_bytes = (audio * 32767).astype(np.int16).tobytes()
            
            chunk_size = 4096
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i+chunk_size]
                await websocket.send_bytes(chunk)
            
            # Send end marker
            await websocket.send_json({"status": "complete", "sample_rate": sr})
            
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()