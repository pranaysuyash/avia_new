"""
Celery Tasks
Background tasks for transcription processing and maintenance
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import subprocess
import json
import tempfile

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
import whisper
import ffmpeg

from api.celery_app import celery_app, db_session
from api.database import Transcript, User
from api.storage import storage_service
from api.ner_service import extract_entities

logger = logging.getLogger(__name__)

class CallbackTask(Task):
    """Base task with callbacks"""
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback"""
        logger.error(f"Task {task_id} failed with exception: {exc}")

@celery_app.task(base=CallbackTask, bind=True, name="api.tasks.process_transcription")
def process_transcription(self, transcription_id: int, object_key: str):
    """
    Process audio/video file for transcription
    
    Args:
        transcription_id: Database ID of the transcription record
        object_key: S3/MinIO object key for the uploaded file
    """
    logger.info(f"Starting transcription processing for ID: {transcription_id}")
    
    try:
        # Get transcription record
        transcript = db_session.query(Transcript).filter(
            Transcript.id == transcription_id
        ).first()
        
        if not transcript:
            logger.error(f"Transcription {transcription_id} not found")
            return {"error": "Transcription not found"}
        
        # Update status
        transcript.processing_time = time.time()
        db_session.commit()
        
        # Download file from storage
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(transcript.file_name)[1]) as tmp_file:
            logger.info(f"Downloading file {object_key}")
            file_data = storage_service.download_file(object_key)
            tmp_file.write(file_data)
            tmp_file.flush()
            
            # Get audio duration
            try:
                probe = ffmpeg.probe(tmp_file.name)
                duration = float(probe['format']['duration'])
                transcript.duration = duration
                db_session.commit()
            except Exception as e:
                logger.warning(f"Could not extract duration: {e}")
            
            # Convert video to audio if needed
            audio_file = tmp_file.name
            if transcript.file_name.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                logger.info("Converting video to audio")
                audio_file = tmp_file.name + '.wav'
                try:
                    ffmpeg.input(tmp_file.name).output(
                        audio_file,
                        acodec='pcm_s16le',
                        ac=1,
                        ar='16k'
                    ).overwrite_output().run(capture_stdout=True, capture_stderr=True)
                except ffmpeg.Error as e:
                    logger.error(f"FFmpeg error: {e.stderr.decode()}")
                    raise
            
            # Load Whisper model
            model_name = transcript.model_used or 'base'
            logger.info(f"Loading Whisper model: {model_name}")
            model = whisper.load_model(model_name)
            
            # Transcribe
            logger.info("Starting transcription")
            result = model.transcribe(
                audio_file,
                language=transcript.language if transcript.language != 'auto' else None,
                task='transcribe',
                verbose=False
            )
            
            # Update transcript with results
            transcript.content = result['text']
            transcript.language = result['language']
            
            # Extract segments with timestamps
            segments = []
            for segment in result.get('segments', []):
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })
            
            # Store segments in entities field temporarily
            transcript.entities = {'segments': segments}
            
            # Calculate confidence (average of segment probabilities)
            if segments:
                avg_prob = sum(seg.get('avg_logprob', 0) for seg in result.get('segments', [])) / len(segments)
                transcript.confidence = min(max(0.0, avg_prob + 1.0), 1.0)  # Normalize to 0-1
            
            # Extract named entities
            if transcript.content:
                entities = extract_entities(transcript.content)
                transcript.entities['entities'] = entities
            
            # Update processing time
            transcript.processing_time = time.time() - transcript.processing_time
            
            # Mark as completed
            transcript.word_count = len(transcript.content.split())
            
            db_session.commit()
            
            logger.info(f"Transcription completed for ID: {transcription_id}")
            
            return {
                "transcription_id": transcription_id,
                "status": "completed",
                "word_count": transcript.word_count,
                "duration": transcript.duration,
                "language": transcript.language,
                "confidence": transcript.confidence
            }
            
    except SoftTimeLimitExceeded:
        logger.error(f"Task timeout for transcription {transcription_id}")
        if 'transcript' in locals():
            transcript.content = "Transcription failed: Processing timeout"
            db_session.commit()
        raise
    except Exception as e:
        logger.error(f"Error processing transcription {transcription_id}: {e}")
        if 'transcript' in locals():
            transcript.content = f"Transcription failed: {str(e)}"
            db_session.commit()
        raise
    finally:
        # Clean up temporary audio file if created
        if 'audio_file' in locals() and audio_file != tmp_file.name:
            try:
                os.remove(audio_file)
            except:
                pass

@celery_app.task(base=CallbackTask, name="api.tasks.cleanup_old_files")
def cleanup_old_files(days: int = 30):
    """
    Clean up old files from storage
    
    Args:
        days: Delete files older than this many days
    """
    logger.info(f"Starting cleanup of files older than {days} days")
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find old transcriptions
        old_transcripts = db_session.query(Transcript).filter(
            Transcript.created_at < cutoff_date,
            Transcript.content != ""  # Only completed transcriptions
        ).all()
        
        deleted_count = 0
        for transcript in old_transcripts:
            # Get object key from summary field
            object_key = transcript.summary
            if object_key:
                try:
                    storage_service.delete_file(object_key)
                    transcript.summary = None  # Clear the object key
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete file {object_key}: {e}")
        
        db_session.commit()
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} files")
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

@celery_app.task(base=CallbackTask, name="api.tasks.update_storage_stats")
def update_storage_stats():
    """Update storage statistics for all users"""
    logger.info("Updating storage statistics")
    
    try:
        users = db_session.query(User).filter(User.is_active == True).all()
        
        stats = []
        for user in users:
            user_stats = storage_service.get_storage_stats(user.id)
            stats.append({
                "user_id": user.id,
                "email": user.email,
                "total_size_mb": user_stats["total_size_mb"],
                "file_count": user_stats["file_count"]
            })
        
        logger.info(f"Updated storage stats for {len(users)} users")
        return {"users_updated": len(users), "stats": stats}
        
    except Exception as e:
        logger.error(f"Error updating storage stats: {e}")
        raise

@celery_app.task(base=CallbackTask, bind=True, name="api.tasks.process_video")
def process_video(self, transcription_id: int, object_key: str, extract_frames: bool = False):
    """
    Process video file for advanced features
    
    Args:
        transcription_id: Database ID of the transcription record
        object_key: S3/MinIO object key for the uploaded file
        extract_frames: Whether to extract key frames
    """
    logger.info(f"Starting video processing for ID: {transcription_id}")
    
    # TODO: Implement video processing
    # - Extract key frames
    # - Generate thumbnails
    # - Extract metadata
    # - Scene detection
    
    return {"status": "not_implemented"}

# Helper function for NER (simplified version)
def extract_entities(text: str) -> Dict[str, list]:
    """
    Extract named entities from text
    This is a simplified version - in production, use spaCy or similar
    """
    import re
    
    entities = {
        "PERSON": [],
        "ORG": [],
        "LOC": [],
        "DATE": [],
        "EMAIL": [],
        "URL": []
    }
    
    # Simple patterns for demonstration
    # Email pattern
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    entities["EMAIL"] = list(set(emails))
    
    # URL pattern
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    entities["URL"] = list(set(urls))
    
    # Date pattern (simple)
    dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)
    entities["DATE"] = list(set(dates))
    
    # In production, use spaCy or similar for proper NER
    # import spacy
    # nlp = spacy.load("en_core_web_sm")
    # doc = nlp(text)
    # for ent in doc.ents:
    #     if ent.label_ in entities:
    #         entities[ent.label_].append(ent.text)
    
    return entities

# Export all tasks
__all__ = [
    "process_transcription",
    "cleanup_old_files",
    "update_storage_stats",
    "process_video"
]