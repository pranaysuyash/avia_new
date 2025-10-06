"""
Transcription Service with Redis Caching
Handles audio/video transcription with caching layer
"""

import os
import hashlib
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json
import tempfile
from pathlib import Path

import openai
from pydub import AudioSegment

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    mp = None
    MOVIEPY_AVAILABLE = False

from api.cache.redis_cache import transcription_cache, cached
from api.models.upload import UploadSession
from api.database import Transcript
from services.vad_service import VADService

logger = logging.getLogger(__name__)


class CachedTranscriptionService:
    """Transcription service with Redis caching"""
    
    def __init__(self, db=None):
        self.db = db
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.vad_service = VADService()
        
        # Configuration
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.chunk_duration = int(os.getenv("AUDIO_CHUNK_DURATION", 60))  # seconds
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", 200 * 1024 * 1024))  # 200MB
    
    async def transcribe_file(
        self,
        file_path: str,
        user_id: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json",
        temperature: float = 0.0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio/video file with caching
        
        Args:
            file_path: Path to the file
            user_id: User ID for tracking
            language: Language code (auto-detect if None)
            prompt: Optional prompt for context
            response_format: Output format
            temperature: Model temperature
            use_cache: Whether to use cache
        
        Returns:
            Transcription result with segments
        """
        # Calculate file hash for cache key
        file_hash = await self._calculate_file_hash(file_path)
        
        # Prepare cache parameters
        cache_params = {
            "language": language,
            "prompt": prompt,
            "response_format": response_format,
            "temperature": temperature,
            "model": self.whisper_model
        }
        
        # Check cache if enabled
        if use_cache:
            cached_result = transcription_cache.get_transcription(file_hash, cache_params)
            if cached_result:
                logger.info(f"Cache hit for file {file_hash}")
                # Update access time
                await self._update_transcript_access(cached_result.get("transcript_id"))
                return cached_result
        
        logger.info(f"Cache miss for file {file_hash}, processing...")
        
        # Process file
        try:
            # Extract audio if video
            audio_path = await self._extract_audio(file_path)
            
            # Perform VAD to identify speech segments
            vad_segments = await self._perform_vad(audio_path)
            
            # Transcribe segments
            segments = await self._transcribe_segments(
                audio_path,
                vad_segments,
                language,
                prompt,
                temperature
            )
            
            # Create transcript record
            transcript = await self._create_transcript_record(
                user_id=user_id,
                file_path=file_path,
                file_hash=file_hash,
                segments=segments,
                language=language or "auto",
                duration=self._get_audio_duration(audio_path)
            )
            
            # Prepare result
            result = {
                "transcript_id": str(transcript.id),
                "text": " ".join([s["text"] for s in segments]),
                "segments": segments,
                "language": transcript.language,
                "duration": transcript.duration,
                "created_at": transcript.created_at.isoformat(),
                "file_hash": file_hash
            }
            
            # Cache result
            if use_cache:
                transcription_cache.set_transcription(
                    file_hash,
                    cache_params,
                    result
                )
            
            # Clean up temp files
            if audio_path != file_path:
                os.unlink(audio_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    async def _extract_audio(self, file_path: str) -> str:
        """Extract audio from video file if needed"""
        file_ext = Path(file_path).suffix.lower()
        
        # If already audio, return as is
        if file_ext in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
            return file_path
        
        # Extract audio from video
        logger.info(f"Extracting audio from video: {file_path}")
        
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy is required for video processing but not installed")
        
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio.close()
        
        video = mp.VideoFileClip(file_path)
        video.audio.write_audiofile(temp_audio.name, logger=None)
        video.close()
        
        return temp_audio.name
    
    async def _perform_vad(self, audio_path: str) -> List[Dict[str, float]]:
        """Perform Voice Activity Detection"""
        segments = await asyncio.to_thread(
            self.vad_service.detect_speech_segments,
            audio_path
        )
        
        # Merge close segments
        merged_segments = []
        for segment in segments:
            if merged_segments and segment['start'] - merged_segments[-1]['end'] < 1.0:
                # Merge with previous segment
                merged_segments[-1]['end'] = segment['end']
            else:
                merged_segments.append(segment)
        
        return merged_segments
    
    async def _transcribe_segments(
        self,
        audio_path: str,
        vad_segments: List[Dict[str, float]],
        language: Optional[str],
        prompt: Optional[str],
        temperature: float
    ) -> List[Dict[str, Any]]:
        """Transcribe audio segments using Whisper"""
        audio = AudioSegment.from_file(audio_path)
        segments = []
        
        for i, vad_segment in enumerate(vad_segments):
            start_ms = int(vad_segment['start'] * 1000)
            end_ms = int(vad_segment['end'] * 1000)
            
            # Extract segment
            segment_audio = audio[start_ms:end_ms]
            
            # Save segment to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_segment:
                segment_audio.export(temp_segment.name, format="wav")
                
                # Transcribe segment
                try:
                    with open(temp_segment.name, "rb") as audio_file:
                        response = await self.openai_client.audio.transcriptions.create(
                            model=self.whisper_model,
                            file=audio_file,
                            language=language,
                            prompt=prompt,
                            temperature=temperature,
                            response_format="verbose_json"
                        )
                    
                    # Process response
                    if hasattr(response, 'segments'):
                        # Adjust timestamps
                        for seg in response.segments:
                            segments.append({
                                "id": len(segments),
                                "start": vad_segment['start'] + seg.start,
                                "end": vad_segment['start'] + seg.end,
                                "text": seg.text,
                                "confidence": getattr(seg, 'confidence', None),
                                "words": getattr(seg, 'words', [])
                            })
                    else:
                        # Simple response
                        segments.append({
                            "id": len(segments),
                            "start": vad_segment['start'],
                            "end": vad_segment['end'],
                            "text": response.text,
                            "confidence": None,
                            "words": []
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to transcribe segment {i}: {e}")
                    # Add empty segment
                    segments.append({
                        "id": len(segments),
                        "start": vad_segment['start'],
                        "end": vad_segment['end'],
                        "text": "[Error transcribing segment]",
                        "confidence": 0.0,
                        "words": []
                    })
                
                finally:
                    os.unlink(temp_segment.name)
        
        return segments
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration in seconds"""
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0
    
    async def _create_transcript_record(
        self,
        user_id: str,
        file_path: str,
        file_hash: str,
        segments: List[Dict[str, Any]],
        language: str,
        duration: float
    ) -> Transcript:
        """Create transcript record in database"""
        transcript = Transcript(
            user_id=int(user_id),
            filename=Path(file_path).name,
            file_hash=file_hash,
            transcript_text=" ".join([s["text"] for s in segments]),
            segments=segments,
            language=language,
            duration=duration,
            word_count=sum(len(s["text"].split()) for s in segments),
            confidence_score=sum(s.get("confidence", 0.9) for s in segments) / len(segments) if segments else 0.0,
            status="completed"
        )
        
        self.db.add(transcript)
        self.db.commit()
        self.db.refresh(transcript)
        
        return transcript
    
    async def _update_transcript_access(self, transcript_id: str):
        """Update last accessed time for transcript"""
        if self.db and transcript_id:
            transcript = self.db.query(Transcript).filter(
                Transcript.id == int(transcript_id)
            ).first()
            
            if transcript:
                transcript.last_accessed = datetime.utcnow()
                self.db.commit()
    
    @cached(ttl=300, prefix="transcript:list:")
    async def get_user_transcripts(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user's transcripts with caching"""
        transcripts = self.db.query(Transcript).filter(
            Transcript.user_id == int(user_id)
        ).order_by(
            Transcript.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return [
            {
                "id": str(t.id),
                "filename": t.filename,
                "duration": t.duration,
                "language": t.language,
                "word_count": t.word_count,
                "created_at": t.created_at.isoformat(),
                "status": t.status
            }
            for t in transcripts
        ]
    
    def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache entries for a user"""
        pattern = f"transcript:list:{user_id}:*"
        count = transcription_cache.cache.clear_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for user {user_id}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not transcription_cache.cache.is_connected():
            return {"connected": False}
        
        info = transcription_cache.cache.client.info()
        return {
            "connected": True,
            "used_memory": info.get("used_memory_human"),
            "total_keys": transcription_cache.cache.client.dbsize(),
            "hit_rate": info.get("keyspace_hits", 0) / 
                       (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1)),
            "evicted_keys": info.get("evicted_keys", 0)
        }