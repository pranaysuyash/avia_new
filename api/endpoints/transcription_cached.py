"""
Cached Transcription API Endpoints
Handles transcription with Redis caching
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from api.database import get_db, User
from api.auth import get_current_active_user
from services.transcription_service_cached import CachedTranscriptionService
from api.cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/transcription/cached",
    tags=["transcription-cached"],
    responses={404: {"description": "Not found"}},
)


class TranscriptionRequest(BaseModel):
    """Request model for transcription"""
    file_key: str = Field(..., description="S3 file key from upload")
    language: Optional[str] = Field(None, description="Language code (auto-detect if none)")
    prompt: Optional[str] = Field(None, description="Optional context prompt")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Model temperature")
    use_cache: bool = Field(True, description="Whether to use cache")


class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    transcript_id: str
    text: str
    segments: list
    language: str
    duration: float
    cached: bool
    created_at: str


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    connected: bool
    used_memory: Optional[str]
    total_keys: Optional[int]
    hit_rate: Optional[float]
    evicted_keys: Optional[int]


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_with_cache(
    request: TranscriptionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Transcribe audio/video file with Redis caching.
    
    This endpoint uses Redis to cache transcription results,
    significantly improving response times for repeated requests.
    """
    service = CachedTranscriptionService(db)
    
    try:
        # Download file from S3 using presigned URLs
        local_file_path = f"/tmp/{request.file_key}"
        
        # Implement S3 download using presigned URLs
        try:
            import boto3
            from botocore.exceptions import ClientError
            import os
            
            # Get S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
            
            # Download file using presigned URL
            bucket_name = os.getenv('S3_BUCKET_NAME', 'transcription-files')
            s3_client.download_file(bucket_name, request.file_key, local_file_path)
            
            logger.info(f"Downloaded file {request.file_key} from S3 to {local_file_path}")
            
        except ClientError as e:
            logger.error(f"S3 download failed for {request.file_key}: {e}")
            # Fallback to local file if it exists
            if not os.path.exists(local_file_path):
                raise HTTPException(status_code=404, detail=f"File {request.file_key} not found")
        
        # Transcribe with caching
        result = await service.transcribe_file(
            file_path=local_file_path,
            user_id=str(current_user.id),
            language=request.language,
            prompt=request.prompt,
            temperature=request.temperature,
            use_cache=request.use_cache
        )
        
        # Check if result was from cache
        cached = "file_hash" in result and request.use_cache
        
        # Clean up file in background
        background_tasks.add_task(cleanup_file, local_file_path)
        
        return TranscriptionResponse(
            transcript_id=result["transcript_id"],
            text=result["text"],
            segments=result["segments"],
            language=result["language"],
            duration=result["duration"],
            cached=cached,
            created_at=result["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/invalidate-cache")
async def invalidate_user_cache(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Invalidate all cached transcriptions for the current user.
    
    This is useful when you want to force re-processing of files.
    """
    service = CachedTranscriptionService(db)
    service.invalidate_user_cache(str(current_user.id))
    
    return {
        "success": True,
        "message": "Cache invalidated for user"
    }


@router.get("/cache-stats", response_model=CacheStatsResponse)
async def get_cache_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get Redis cache statistics.
    
    Shows memory usage, hit rate, and other cache metrics.
    """
    service = CachedTranscriptionService(db)
    stats = service.get_cache_stats()
    
    return CacheStatsResponse(**stats)


@router.get("/transcripts", response_model=list)
async def get_user_transcripts(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's transcripts with caching.
    
    Results are cached for 5 minutes to improve performance.
    """
    service = CachedTranscriptionService(db)
    
    transcripts = await service.get_user_transcripts(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset
    )
    
    return transcripts


@router.post("/warm-cache")
async def warm_cache(
    transcript_ids: list[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Pre-warm cache with specific transcripts.
    
    Useful for pre-loading frequently accessed transcripts.
    """
    # Implement cache warming
    try:
        service = CachedTranscriptionService(db)
        
        warmed_count = 0
        failed_count = 0
        
        # Warm cache for each transcript
        for transcript_id in transcript_ids:
            try:
                # Get transcript from database
                transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
                if not transcript:
                    failed_count += 1
                    continue
                
                # Warm the cache by loading the transcript
                cache_key = f"transcript_{transcript_id}"
                service.cache.set(cache_key, {
                    "transcript": transcript.transcript,
                    "entities": transcript.entities,
                    "summary": transcript.summary,
                    "created_at": transcript.created_at.isoformat() if transcript.created_at else None
                })
                
                warmed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to warm cache for transcript {transcript_id}: {e}")
                failed_count += 1
        
        return {
            "success": True,
            "message": f"Warmed cache with {warmed_count} transcripts ({failed_count} failed)",
            "warmed_count": warmed_count,
            "failed_count": failed_count
        }
        
    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        return {
            "success": False,
            "message": f"Cache warming failed: {str(e)}",
            "warmed_count": 0,
            "failed_count": len(transcript_ids)
        }


def cleanup_file(file_path: str):
    """Clean up temporary file"""
    try:
        import os
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Failed to cleanup file {file_path}: {e}")