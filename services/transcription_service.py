"""
Transcription Service
Production implementation with Whisper and advanced features
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from pathlib import Path

import whisper
from faster_whisper import WhisperModel
import torch
import numpy as np
from pydub import AudioSegment
import redis
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

# Import database models
from database.models import (
    Transcript, TranscriptSegment, TranscriptWord,
    User, Team, TranscriptionSession
)

# Import other services
from services.storage_service import StorageService
from services.cache_service import CacheService
from services.webhook_service import WebhookService
from services.audit_logging_service import AuditLogger

# Import utilities
from utils.audio_processing import AudioProcessor
from utils.text_processing import TextProcessor

logger = logging.getLogger(__name__)


class TranscriptionStatus(Enum):
    """Transcription job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TranscriptionEngine(Enum):
    """Available transcription engines"""
    WHISPER = "whisper"
    FASTER_WHISPER = "faster_whisper"
    WHISPER_API = "whisper_api"
    CUSTOM = "custom"


class TranscriptionService:
    """Production transcription service with full feature support"""
    
    def __init__(
        self,
        db: Session,
        storage_service: Optional[StorageService] = None,
        cache_service: Optional[CacheService] = None,
        webhook_service: Optional[WebhookService] = None,
        audit_logger: Optional[AuditLogger] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.db = db
        self.storage_service = storage_service or StorageService()
        self.cache_service = cache_service or CacheService()
        self.webhook_service = webhook_service or WebhookService()
        self.audit_logger = audit_logger or AuditLogger(db)
        self.config = config or {}
        
        # Initialize transcription models
        self._initialize_models()
        
        # Initialize audio processor
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
        
        # Processing queue
        self.processing_queue = asyncio.Queue()
        self.active_jobs = {}
        
    def _initialize_models(self):
        """Initialize transcription models"""
        self.models = {}
        
        # Load Whisper model
        if self.config.get('enable_whisper', True):
            try:
                model_size = self.config.get('whisper_model', 'base')
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.models['whisper'] = whisper.load_model(model_size, device=device)
                logger.info(f"Loaded Whisper model: {model_size} on {device}")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
        
        # Load Faster Whisper model
        if self.config.get('enable_faster_whisper', True):
            try:
                model_size = self.config.get('faster_whisper_model', 'base')
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                compute_type = 'float16' if device == 'cuda' else 'float32'
                
                self.models['faster_whisper'] = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type
                )
                logger.info(f"Loaded Faster Whisper model: {model_size}")
            except Exception as e:
                logger.error(f"Failed to load Faster Whisper model: {e}")
    
    async def create_transcript(
        self,
        file_path: str,
        user_id: int,
        team_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        engine: TranscriptionEngine = TranscriptionEngine.FASTER_WHISPER,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new transcription job"""
        
        try:
            # Validate file
            if not os.path.exists(file_path):
                raise ValueError(f"File not found: {file_path}")
            
            # Create database entry
            transcript = Transcript(
                user_id=user_id,
                team_id=team_id,
                file_path=file_path,
                file_name=os.path.basename(file_path),
                status=TranscriptionStatus.PENDING.value,
                engine=engine.value,
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            
            self.db.add(transcript)
            self.db.commit()
            self.db.refresh(transcript)
            
            # Log audit event
            if self.audit_logger:
                await self.audit_logger.log_event(
                    user_id=user_id,
                    action="transcript_created",
                    resource_type="transcript",
                    resource_id=transcript.id,
                    details={"file_name": transcript.file_name, "engine": engine.value}
                )
            
            # Add to processing queue
            job_data = {
                'transcript_id': transcript.id,
                'file_path': file_path,
                'user_id': user_id,
                'engine': engine,
                'config': config or {}
            }
            
            await self.processing_queue.put(job_data)
            
            # Start processing in background
            asyncio.create_task(self._process_transcription(job_data))
            
            return {
                'id': transcript.id,
                'status': transcript.status,
                'file_name': transcript.file_name,
                'created_at': transcript.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create transcript: {e}")
            raise
    
    async def _process_transcription(self, job_data: Dict[str, Any]):
        """Process transcription job"""
        
        transcript_id = job_data['transcript_id']
        
        try:
            # Update status
            transcript = self.db.query(Transcript).filter_by(id=transcript_id).first()
            if not transcript:
                raise ValueError(f"Transcript {transcript_id} not found")
            
            transcript.status = TranscriptionStatus.PROCESSING.value
            transcript.started_at = datetime.utcnow()
            self.db.commit()
            
            # Preprocess audio
            processed_audio = await self.audio_processor.process_audio(
                job_data['file_path'],
                normalize=True,
                remove_noise=True,
                enhance_speech=True
            )
            
            # Perform transcription based on engine
            if job_data['engine'] == TranscriptionEngine.FASTER_WHISPER:
                result = await self._transcribe_faster_whisper(
                    processed_audio,
                    job_data['config']
                )
            elif job_data['engine'] == TranscriptionEngine.WHISPER:
                result = await self._transcribe_whisper(
                    processed_audio,
                    job_data['config']
                )
            else:
                raise ValueError(f"Unsupported engine: {job_data['engine']}")
            
            # Save transcription results
            await self._save_transcription_results(transcript_id, result)
            
            # Update status
            transcript.status = TranscriptionStatus.COMPLETED.value
            transcript.completed_at = datetime.utcnow()
            transcript.duration = result.get('duration', 0)
            transcript.word_count = len(result.get('text', '').split())
            self.db.commit()
            
            # Send webhook notification
            if self.webhook_service and transcript.metadata.get('webhook_url'):
                await self.webhook_service.send_notification(
                    transcript.metadata['webhook_url'],
                    {
                        'event': 'transcription_completed',
                        'transcript_id': transcript_id,
                        'status': 'completed'
                    }
                )
            
            # Cache result
            if self.cache_service:
                await self.cache_service.set(
                    f"transcript:{transcript_id}",
                    result,
                    ttl=3600
                )
            
            logger.info(f"Transcription completed: {transcript_id}")
            
        except Exception as e:
            logger.error(f"Transcription failed for {transcript_id}: {e}")
            
            # Update status
            transcript = self.db.query(Transcript).filter_by(id=transcript_id).first()
            if transcript:
                transcript.status = TranscriptionStatus.FAILED.value
                transcript.error_message = str(e)
                self.db.commit()
            
            # Send failure webhook
            if self.webhook_service and transcript.metadata.get('webhook_url'):
                await self.webhook_service.send_notification(
                    transcript.metadata['webhook_url'],
                    {
                        'event': 'transcription_failed',
                        'transcript_id': transcript_id,
                        'error': str(e)
                    }
                )
    
    async def _transcribe_faster_whisper(
        self,
        audio_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transcribe using Faster Whisper"""
        
        model = self.models.get('faster_whisper')
        if not model:
            raise ValueError("Faster Whisper model not loaded")
        
        # Transcribe
        segments, info = model.transcribe(
            audio_path,
            language=config.get('language'),
            initial_prompt=config.get('prompt'),
            beam_size=config.get('beam_size', 5),
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=config.get('vad_parameters')
        )
        
        # Process segments
        result_segments = []
        full_text = ""
        words = []
        
        for segment in segments:
            seg_data = {
                'id': len(result_segments),
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'confidence': segment.avg_logprob
            }
            
            # Extract word-level timestamps
            if segment.words:
                for word in segment.words:
                    words.append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'confidence': word.probability
                    })
            
            result_segments.append(seg_data)
            full_text += segment.text + " "
        
        return {
            'text': full_text.strip(),
            'segments': result_segments,
            'words': words,
            'language': info.language,
            'duration': info.duration,
            'language_probability': info.language_probability
        }
    
    async def _transcribe_whisper(
        self,
        audio_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper"""
        
        model = self.models.get('whisper')
        if not model:
            raise ValueError("Whisper model not loaded")
        
        # Transcribe
        result = model.transcribe(
            audio_path,
            language=config.get('language'),
            initial_prompt=config.get('prompt'),
            temperature=config.get('temperature', 0),
            compression_ratio_threshold=config.get('compression_ratio_threshold'),
            logprob_threshold=config.get('logprob_threshold'),
            no_speech_threshold=config.get('no_speech_threshold'),
            word_timestamps=True,
            prepend_punctuations=config.get('prepend_punctuations'),
            append_punctuations=config.get('append_punctuations')
        )
        
        # Process segments
        segments = []
        words = []
        
        for segment in result.get('segments', []):
            segments.append({
                'id': segment['id'],
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('avg_logprob', 0)
            })
            
            # Extract word timestamps
            for word_data in segment.get('words', []):
                words.append({
                    'word': word_data['word'],
                    'start': word_data['start'],
                    'end': word_data['end'],
                    'confidence': word_data.get('probability', 0)
                })
        
        return {
            'text': result['text'],
            'segments': segments,
            'words': words,
            'language': result.get('language'),
            'duration': segments[-1]['end'] if segments else 0
        }
    
    async def _save_transcription_results(
        self,
        transcript_id: int,
        result: Dict[str, Any]
    ):
        """Save transcription results to database"""
        
        try:
            # Save full text
            transcript = self.db.query(Transcript).filter_by(id=transcript_id).first()
            transcript.text = result['text']
            transcript.language = result.get('language', 'en')
            
            # Save segments
            for segment_data in result.get('segments', []):
                segment = TranscriptSegment(
                    transcript_id=transcript_id,
                    segment_number=segment_data['id'],
                    start_time=segment_data['start'],
                    end_time=segment_data['end'],
                    text=segment_data['text'],
                    confidence=segment_data.get('confidence', 0)
                )
                self.db.add(segment)
            
            # Save word-level timestamps
            for word_data in result.get('words', []):
                word = TranscriptWord(
                    transcript_id=transcript_id,
                    word=word_data['word'],
                    start_time=word_data['start'],
                    end_time=word_data['end'],
                    confidence=word_data.get('confidence', 0)
                )
                self.db.add(word)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save transcription results: {e}")
            self.db.rollback()
            raise
    
    def get_transcript(
        self,
        transcript_id: int,
        user_id: int,
        include_segments: bool = False,
        include_words: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get transcript by ID"""
        
        # Check cache first
        if self.cache_service:
            cached = self.cache_service.get(f"transcript:{transcript_id}")
            if cached:
                return cached
        
        # Query database
        transcript = self.db.query(Transcript).filter(
            and_(
                Transcript.id == transcript_id,
                or_(
                    Transcript.user_id == user_id,
                    Transcript.team_id.in_(
                        self.db.query(Team.id).filter(
                            Team.members.any(User.id == user_id)
                        )
                    )
                )
            )
        ).first()
        
        if not transcript:
            return None
        
        result = {
            'id': transcript.id,
            'file_name': transcript.file_name,
            'status': transcript.status,
            'text': transcript.text,
            'language': transcript.language,
            'duration': transcript.duration,
            'word_count': transcript.word_count,
            'created_at': transcript.created_at.isoformat(),
            'completed_at': transcript.completed_at.isoformat() if transcript.completed_at else None
        }
        
        # Include segments if requested
        if include_segments:
            segments = self.db.query(TranscriptSegment).filter_by(
                transcript_id=transcript_id
            ).order_by(TranscriptSegment.segment_number).all()
            
            result['segments'] = [
                {
                    'id': seg.id,
                    'start': seg.start_time,
                    'end': seg.end_time,
                    'text': seg.text,
                    'confidence': seg.confidence
                }
                for seg in segments
            ]
        
        # Include word timestamps if requested
        if include_words:
            words = self.db.query(TranscriptWord).filter_by(
                transcript_id=transcript_id
            ).order_by(TranscriptWord.start_time).all()
            
            result['words'] = [
                {
                    'word': w.word,
                    'start': w.start_time,
                    'end': w.end_time,
                    'confidence': w.confidence
                }
                for w in words
            ]
        
        # Cache result
        if self.cache_service:
            self.cache_service.set(
                f"transcript:{transcript_id}",
                result,
                ttl=3600
            )
        
        return result
    
    def list_transcripts(
        self,
        user_id: int,
        team_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List user's transcripts"""
        
        query = self.db.query(Transcript)
        
        # Filter by user/team
        if team_id:
            query = query.filter_by(team_id=team_id)
        else:
            query = query.filter_by(user_id=user_id)
        
        # Filter by status
        if status:
            query = query.filter_by(status=status)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        transcripts = query.order_by(
            desc(Transcript.created_at)
        ).limit(limit).offset(offset).all()
        
        return {
            'total': total,
            'transcripts': [
                {
                    'id': t.id,
                    'file_name': t.file_name,
                    'status': t.status,
                    'duration': t.duration,
                    'word_count': t.word_count,
                    'language': t.language,
                    'created_at': t.created_at.isoformat(),
                    'completed_at': t.completed_at.isoformat() if t.completed_at else None
                }
                for t in transcripts
            ],
            'limit': limit,
            'offset': offset
        }
    
    async def update_transcript(
        self,
        transcript_id: int,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update transcript metadata or text"""
        
        transcript = self.db.query(Transcript).filter(
            and_(
                Transcript.id == transcript_id,
                Transcript.user_id == user_id
            )
        ).first()
        
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Update allowed fields
        allowed_fields = ['text', 'metadata', 'tags']
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(transcript, field, value)
        
        transcript.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Clear cache
        if self.cache_service:
            self.cache_service.delete(f"transcript:{transcript_id}")
        
        # Log audit event
        if self.audit_logger:
            await self.audit_logger.log_event(
                user_id=user_id,
                action="transcript_updated",
                resource_type="transcript",
                resource_id=transcript_id,
                details={"fields": list(updates.keys())}
            )
        
        return {
            'id': transcript.id,
            'status': 'updated',
            'updated_at': transcript.updated_at.isoformat()
        }
    
    async def delete_transcript(
        self,
        transcript_id: int,
        user_id: int
    ) -> bool:
        """Delete transcript"""
        
        transcript = self.db.query(Transcript).filter(
            and_(
                Transcript.id == transcript_id,
                Transcript.user_id == user_id
            )
        ).first()
        
        if not transcript:
            return False
        
        # Delete associated data
        self.db.query(TranscriptSegment).filter_by(transcript_id=transcript_id).delete()
        self.db.query(TranscriptWord).filter_by(transcript_id=transcript_id).delete()
        
        # Delete file from storage
        if self.storage_service and transcript.file_path:
            await self.storage_service.delete_file(transcript.file_path)
        
        # Delete transcript
        self.db.delete(transcript)
        self.db.commit()
        
        # Clear cache
        if self.cache_service:
            self.cache_service.delete(f"transcript:{transcript_id}")
        
        # Log audit event
        if self.audit_logger:
            await self.audit_logger.log_event(
                user_id=user_id,
                action="transcript_deleted",
                resource_type="transcript",
                resource_id=transcript_id,
                details={"file_name": transcript.file_name}
            )
        
        return True
    
    async def search_transcripts(
        self,
        user_id: int,
        query: str,
        team_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search transcripts by content"""
        
        # Use full-text search if available
        base_query = self.db.query(Transcript)
        
        if team_id:
            base_query = base_query.filter_by(team_id=team_id)
        else:
            base_query = base_query.filter_by(user_id=user_id)
        
        # Search in text
        transcripts = base_query.filter(
            Transcript.text.ilike(f"%{query}%")
        ).limit(limit).all()
        
        results = []
        for transcript in transcripts:
            # Find matching segments
            segments = self.db.query(TranscriptSegment).filter(
                and_(
                    TranscriptSegment.transcript_id == transcript.id,
                    TranscriptSegment.text.ilike(f"%{query}%")
                )
            ).all()
            
            results.append({
                'transcript_id': transcript.id,
                'file_name': transcript.file_name,
                'matches': [
                    {
                        'text': seg.text,
                        'start': seg.start_time,
                        'end': seg.end_time
                    }
                    for seg in segments
                ]
            })
        
        return results
    
    def get_statistics(
        self,
        user_id: int,
        team_id: Optional[int] = None,
        period: str = 'month'
    ) -> Dict[str, Any]:
        """Get transcription statistics"""
        
        # Calculate time range
        if period == 'week':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == 'month':
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == 'year':
            start_date = datetime.utcnow() - timedelta(days=365)
        else:
            start_date = datetime.min
        
        query = self.db.query(Transcript).filter(
            Transcript.created_at >= start_date
        )
        
        if team_id:
            query = query.filter_by(team_id=team_id)
        else:
            query = query.filter_by(user_id=user_id)
        
        transcripts = query.all()
        
        # Calculate statistics
        total_duration = sum(t.duration or 0 for t in transcripts)
        total_words = sum(t.word_count or 0 for t in transcripts)
        
        # Language distribution
        language_dist = {}
        for t in transcripts:
            lang = t.language or 'unknown'
            language_dist[lang] = language_dist.get(lang, 0) + 1
        
        # Status distribution
        status_dist = {}
        for t in transcripts:
            status_dist[t.status] = status_dist.get(t.status, 0) + 1
        
        return {
            'total_transcripts': len(transcripts),
            'total_duration_minutes': total_duration / 60,
            'total_words': total_words,
            'average_duration_minutes': (total_duration / len(transcripts) / 60) if transcripts else 0,
            'average_words': (total_words / len(transcripts)) if transcripts else 0,
            'language_distribution': language_dist,
            'status_distribution': status_dist,
            'period': period
        }
    
    async def export_transcript(
        self,
        transcript_id: int,
        user_id: int,
        format: str = 'json'
    ) -> Union[str, Dict[str, Any]]:
        """Export transcript in various formats"""
        
        transcript_data = self.get_transcript(
            transcript_id,
            user_id,
            include_segments=True,
            include_words=True
        )
        
        if not transcript_data:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        if format == 'json':
            return json.dumps(transcript_data, indent=2)
        
        elif format == 'srt':
            # Generate SRT subtitle format
            srt_content = []
            for i, segment in enumerate(transcript_data.get('segments', []), 1):
                start = self._format_timestamp(segment['start'])
                end = self._format_timestamp(segment['end'])
                srt_content.append(f"{i}\n{start} --> {end}\n{segment['text']}\n")
            return '\n'.join(srt_content)
        
        elif format == 'vtt':
            # Generate WebVTT format
            vtt_content = ["WEBVTT\n"]
            for segment in transcript_data.get('segments', []):
                start = self._format_timestamp(segment['start'], vtt=True)
                end = self._format_timestamp(segment['end'], vtt=True)
                vtt_content.append(f"{start} --> {end}\n{segment['text']}\n")
            return '\n'.join(vtt_content)
        
        elif format == 'txt':
            # Plain text
            return transcript_data.get('text', '')
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _format_timestamp(self, seconds: float, vtt: bool = False) -> str:
        """Format timestamp for subtitles"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if vtt:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            # SRT format
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')