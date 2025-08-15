"""
Celery Tasks
Background tasks for transcription processing and maintenance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import tempfile

from celery import Task
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
        
        # Log task arguments for debugging
        if args or kwargs:
            logger.debug(f"Task {task_id} arguments - args: {args}, kwargs: {kwargs}")
        
        # Update task metrics
        try:
            # In a real implementation, you would update metrics in a database
            logger.info(f"Task {task_id} completed successfully")
        except Exception as e:
            logger.warning(f"Could not update success metrics for task {task_id}: {e}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback"""
        logger.error(f"Task {task_id} failed with exception: {exc}")
        
        # Log task arguments for debugging
        if args or kwargs:
            logger.error(f"Task {task_id} arguments - args: {args}, kwargs: {kwargs}")
        
        # Log traceback information
        if einfo:
            logger.error(f"Task {task_id} traceback: {einfo.traceback}")
        
        # Update failure metrics
        try:
            # In a real implementation, you would update metrics in a database
            logger.info(f"Task {task_id} failure recorded")
        except Exception as e:
            logger.warning(f"Could not update failure metrics for task {task_id}: {e}")

@celery_app.task(base=CallbackTask, bind=True, name="api.tasks.process_transcription")
def process_transcription(task_self, transcription_id: int, object_key: str):
    """
    Process audio/video file for transcription
    
    Args:
        task_self: Celery task instance (used for callbacks and progress tracking)
        transcription_id: Database ID of the transcription record
        object_key: S3/MinIO object key for the uploaded file
    """
    logger.info(f"Starting transcription processing for ID: {transcription_id}")
    
    try:
        # Update task progress
        task_self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100})
        
        # Get transcription record
        transcript = db_session.query(Transcript).filter(Transcript.id == transcription_id).first()
        if not transcript:
            logger.error(f"Transcription record not found: {transcription_id}")
            return {"status": "error", "message": "Transcription record not found"}
        
        # Download file from storage
        temp_file_path = f"/tmp/transcript_{transcription_id}"
        storage_service.download_file(object_key, temp_file_path)
        
        task_self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100})
        
        # Process audio/video file
        try:
            # Convert to WAV if needed
            wav_file_path = f"{temp_file_path}.wav"
            if not temp_file_path.endswith('.wav'):
                logger.info(f"Converting {temp_file_path} to WAV format")
                (
                    ffmpeg
                    .input(temp_file_path)
                    .output(wav_file_path, acodec='pcm_s16le', ar=16000, ac=1)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            else:
                wav_file_path = temp_file_path
            
            task_self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100})
            
            # Transcribe using Whisper
            logger.info(f"Transcribing file: {wav_file_path}")
            model = whisper.load_model("base")
            result = model.transcribe(wav_file_path, language="en")
            
            task_self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100})
            
            # Extract entities
            entities = extract_entities(result["text"])
            
            # Update database record
            transcript.transcript = result["text"]
            transcript.entities = json.dumps(entities)
            transcript.processed_at = datetime.now()
            transcript.status = "completed"
            db_session.commit()
            
            task_self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100})
            
            # Clean up temporary files
            import os
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(wav_file_path) and wav_file_path != temp_file_path:
                os.remove(wav_file_path)
            
            task_self.update_state(state='SUCCESS', meta={
                'current': 100, 
                'total': 100,
                'transcription_id': transcription_id,
                'entities_extracted': len(entities)
            })
            
            logger.info(f"Transcription processing completed for ID: {transcription_id}")
            return {
                "status": "success",
                "transcription_id": transcription_id,
                "text": result["text"],
                "entities": entities,
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            logger.error(f"Error processing file {object_key}: {e}")
            # Update database with error status
            transcript.status = "failed"
            transcript.error_message = str(e)
            db_session.commit()
            raise
            
    except Exception as e:
        logger.error(f"Error processing transcription {transcription_id}: {e}")
        # Clean up temporary files on error
        import os
        temp_files = [f"/tmp/transcript_{transcription_id}", f"/tmp/transcript_{transcription_id}.wav"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        return {"status": "error", "message": str(e)}

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
    
    try:
        # Update task progress
        self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100})
        
        # Download video file from storage
        temp_video_path = f"/tmp/video_{transcription_id}.mp4"
        storage_service.download_file(object_key, temp_video_path)
        
        self.update_state(state='PROGRESS', meta={'current': 20, 'total': 100})
        
        # Process video using OpenCV
        import cv2
        import numpy as np
        from PIL import Image
        import json
        import os
        
        # Open video file
        cap = cv2.VideoCapture(temp_video_path)
        
        if not cap.isOpened():
            logger.error(f"Could not open video file: {temp_video_path}")
            return {"status": "error", "message": "Could not open video file"}
        
        # Extract metadata
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        metadata = {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "codec": cap.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT),
            "bit_rate": cap.get(cv2.CAP_PROP_BITRATE)
        }
        
        logger.info(f"Video metadata extracted: {metadata}")
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100})
        
        # Initialize results
        results = {
            "status": "success",
            "transcription_id": transcription_id,
            "metadata": metadata,
            "key_frames": [],
            "thumbnails": [],
            "scenes": []
        }
        
        # Extract key frames if requested
        if extract_frames:
            logger.info("Extracting key frames...")
            self.update_state(state='PROGRESS', meta={'current': 40, 'total': 100})
            
            # Calculate frame interval (every 10 seconds)
            frame_interval = int(fps * 10) if fps > 0 else 300
            
            # Extract frames
            frame_counter = 0
            extracted_frames = 0
            max_frames = 50  # Limit to prevent excessive storage usage
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract key frames at intervals
                if frame_counter % frame_interval == 0 and extracted_frames < max_frames:
                    # Save frame as image
                    frame_filename = f"key_frame_{transcription_id}_{extracted_frames}.jpg"
                    frame_path = f"/tmp/{frame_filename}"
                    
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(rgb_frame)
                    pil_image.save(frame_path, "JPEG", quality=85)
                    
                    # Upload to storage
                    storage_key = f"transcriptions/{transcription_id}/key_frames/{frame_filename}"
                    storage_service.upload_file(frame_path, storage_key)
                    
                    # Add to results
                    results["key_frames"].append({
                        "frame_number": frame_counter,
                        "timestamp": frame_counter / fps if fps > 0 else 0,
                        "storage_key": storage_key,
                        "url": storage_service.get_public_url(storage_key)
                    })
                    
                    extracted_frames += 1
                
                frame_counter += 1
            
            logger.info(f"Extracted {extracted_frames} key frames")
            self.update_state(state='PROGRESS', meta={'current': 70, 'total': 100})
        
        # Generate thumbnail
        logger.info("Generating thumbnail...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(int(frame_count / 2), frame_count - 1))  # Middle frame
        ret, frame = cap.read()
        if ret:
            # Resize for thumbnail (max 320px width)
            thumbnail_height = int((320 / width) * height)
            thumbnail = cv2.resize(frame, (320, thumbnail_height))
            
            # Save thumbnail
            thumb_filename = f"thumbnail_{transcription_id}.jpg"
            thumb_path = f"/tmp/{thumb_filename}"
            
            # Convert BGR to RGB
            rgb_thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
            pil_thumb = Image.fromarray(rgb_thumbnail)
            pil_thumb.save(thumb_path, "JPEG", quality=80)
            
            # Upload to storage
            thumb_storage_key = f"transcriptions/{transcription_id}/thumbnails/{thumb_filename}"
            storage_service.upload_file(thumb_path, thumb_storage_key)
            
            results["thumbnails"].append({
                "storage_key": thumb_storage_key,
                "url": storage_service.get_public_url(thumb_storage_key),
                "width": 320,
                "height": thumbnail_height
            })
            
            logger.info(f"Thumbnail generated and uploaded: {thumb_storage_key}")
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100})
        
        # Scene detection using color histogram comparison
        logger.info("Performing scene detection...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to beginning
        
        scene_changes = []
        prev_hist = None
        frame_counter = 0
        scene_threshold = 0.7  # Adjust based on sensitivity needs
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every 30th frame for efficiency
            if frame_counter % 30 == 0:
                # Convert to HSV for better color comparison
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Calculate histogram
                hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                # Compare with previous frame
                if prev_hist is not None:
                    # Calculate correlation between histograms
                    correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                    
                    # If correlation is below threshold, it's likely a scene change
                    if correlation < scene_threshold:
                        scene_changes.append({
                            "frame_number": frame_counter,
                            "timestamp": frame_counter / fps if fps > 0 else 0,
                            "correlation": float(correlation)
                        })
                
                prev_hist = hist
            
            frame_counter += 1
        
        results["scenes"] = scene_changes
        logger.info(f"Detected {len(scene_changes)} scene changes")
        
        # Clean up
        cap.release()
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        
        # Clean up temporary files
        for frame_data in results["key_frames"]:
            temp_path = f"/tmp/{os.path.basename(frame_data['storage_key'])}"
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        if results["thumbnails"]:
            temp_thumb_path = f"/tmp/{os.path.basename(results['thumbnails'][0]['storage_key'])}"
            if os.path.exists(temp_thumb_path):
                os.remove(temp_thumb_path)
        
        self.update_state(state='SUCCESS', meta={
            'current': 100, 
            'total': 100,
            'transcription_id': transcription_id,
            'key_frames_extracted': len(results["key_frames"]),
            'scene_changes_detected': len(scene_changes)
        })
        
        logger.info(f"Video processing completed for ID: {transcription_id}")
        return results
        
    except Exception as e:
        logger.error(f"Error processing video for ID {transcription_id}: {e}")
        # Clean up any temporary files
        try:
            cap.release()
        except:
            pass
        
        # Clean up temporary files
        temp_files = [
            f"/tmp/video_{transcription_id}.mp4",
            f"/tmp/thumbnail_{transcription_id}.jpg"
        ]
        
        for i in range(50):
            temp_files.append(f"/tmp/key_frame_{transcription_id}_{i}.jpg")
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        
        return {"status": "error", "message": str(e)}

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