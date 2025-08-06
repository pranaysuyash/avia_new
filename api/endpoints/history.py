"""
History Management API Endpoints
REST API for transcription history management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from api.dependencies import auth_required, create_api_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])

# Data models
class TranscriptionHistoryItem(BaseModel):
    id: str
    title: str
    filename: str
    duration: float
    status: str
    accuracy: float
    created_at: str
    updated_at: str
    file_size: int
    language: str
    entities_count: int
    entities_preview: List[str]
    tags: List[str] = []

class HistoryFilter(BaseModel):
    status: Optional[str] = None
    language: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_accuracy: Optional[float] = None
    has_entities: Optional[bool] = None

class HistoryStats(BaseModel):
    total_items: int
    completed: int
    processing: int
    failed: int
    total_duration: float
    avg_accuracy: float

class HistoryResponse(BaseModel):
    items: List[TranscriptionHistoryItem]
    stats: HistoryStats
    total_pages: int
    current_page: int

def generate_mock_history_items(count: int = 50) -> List[TranscriptionHistoryItem]:
    """Generate mock history data"""
    import random
    from datetime import datetime, timedelta
    
    items = []
    statuses = ["completed", "processing", "failed"]
    languages = ["en", "es", "fr", "de", "it"]
    
    for i in range(count):
        created_date = datetime.now() - timedelta(days=random.randint(0, 90))
        status = random.choice(statuses)
        language = random.choice(languages)
        
        entities_preview = [
            "John Smith", "Microsoft", "New York", "$1000", "2024-01-15"
        ][:random.randint(1, 5)]
        
        items.append(TranscriptionHistoryItem(
            id=f"transcript_{i+1:03d}",
            title=f"Transcription {i+1}",
            filename=f"audio_file_{i+1}.wav",
            duration=round(random.uniform(30, 3600), 1),
            status=status,
            accuracy=round(random.uniform(85, 99), 1) if status == "completed" else 0,
            created_at=created_date.isoformat(),
            updated_at=(created_date + timedelta(minutes=random.randint(1, 60))).isoformat(),
            file_size=random.randint(1000000, 50000000),  # 1MB to 50MB
            language=language,
            entities_count=random.randint(5, 50) if status == "completed" else 0,
            entities_preview=entities_preview if status == "completed" else [],
            tags=[f"tag_{random.randint(1, 10)}" for _ in range(random.randint(0, 3))]
        ))
    
    # Sort by created_at descending
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items

@router.get("/transcriptions", response_model=HistoryResponse)
async def get_transcription_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    user_id: str = "test_user"
):
    """Get paginated transcription history with filtering"""
    try:
        # Generate mock data
        all_items = generate_mock_history_items(100)
        
        # Apply filters
        filtered_items = all_items
        
        if status:
            filtered_items = [item for item in filtered_items if item.status == status]
        
        if language:
            filtered_items = [item for item in filtered_items if item.language == language]
        
        if search:
            search_lower = search.lower()
            filtered_items = [
                item for item in filtered_items 
                if (search_lower in item.title.lower() or 
                    search_lower in item.filename.lower())
            ]
        
        # Calculate pagination
        total_items = len(filtered_items)
        total_pages = (total_items + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        page_items = filtered_items[start_idx:end_idx]
        
        # Calculate stats
        completed_items = [item for item in filtered_items if item.status == "completed"]
        processing_items = [item for item in filtered_items if item.status == "processing"]
        failed_items = [item for item in filtered_items if item.status == "failed"]
        
        stats = HistoryStats(
            total_items=total_items,
            completed=len(completed_items),
            processing=len(processing_items),
            failed=len(failed_items),
            total_duration=sum(item.duration for item in completed_items),
            avg_accuracy=sum(item.accuracy for item in completed_items) / len(completed_items) if completed_items else 0
        )
        
        return HistoryResponse(
            items=page_items,
            stats=stats,
            total_pages=total_pages,
            current_page=page
        )
        
    except Exception as e:
        logger.error(f"Failed to get transcription history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcription history")

@router.get("/transcriptions/{transcription_id}")
async def get_transcription_details(
    transcription_id: str = Path(...),
    user_id: str = "test_user"
):
    """Get detailed information about a specific transcription"""
    try:
        # Mock detailed transcription data
        import random
        from datetime import datetime
        
        # Check if transcription exists (mock check)
        if not transcription_id.startswith("transcript_"):
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        details = {
            "id": transcription_id,
            "title": f"Detailed Transcription {transcription_id.split('_')[1]}",
            "filename": f"audio_file_{transcription_id.split('_')[1]}.wav",
            "file_path": f"/uploads/{transcription_id}/audio.wav",
            "duration": round(random.uniform(60, 3600), 1),
            "status": "completed",
            "accuracy": round(random.uniform(90, 99), 1),
            "language": "en",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "file_size": random.randint(5000000, 100000000),
            "transcript": "This is a sample transcription text. The speaker discusses various topics including technology, business, and future trends. Named entities like John Smith, Microsoft, and New York are mentioned throughout the conversation.",
            "entities": {
                "PERSON": ["John Smith", "Sarah Johnson", "Mike Chen"],
                "ORG": ["Microsoft", "Google", "OpenAI"],
                "LOC": ["New York", "San Francisco", "London"],
                "MONEY": ["$1000", "$50,000"],
                "DATE": ["today", "next week", "2024-01-15"]
            },
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.2,
                    "text": "Welcome to our discussion about technology trends.",
                    "confidence": 0.98
                },
                {
                    "start": 5.2,
                    "end": 12.8,
                    "text": "Today we'll be talking with John Smith from Microsoft.",
                    "confidence": 0.95
                },
                {
                    "start": 12.8,
                    "end": 20.1,
                    "text": "The company is investing heavily in AI technologies.",
                    "confidence": 0.97
                }
            ],
            "metadata": {
                "audio_format": "wav",
                "sample_rate": 44100,
                "channels": 1,
                "bitrate": 1411,
                "processing_time": round(random.uniform(10, 180), 1),
                "model_used": "whisper-large-v2",
                "language_detected": "en",
                "confidence_threshold": 0.8
            },
            "tags": ["business", "technology", "interview"],
            "notes": "High-quality recording with clear audio. Good transcription accuracy achieved."
        }
        
        return create_api_response(details, "Transcription details retrieved successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get transcription details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve transcription details")

@router.delete("/transcriptions/{transcription_id}")
async def delete_transcription(
    transcription_id: str = Path(...),
    user_id: str = "test_user"
):
    """Delete a transcription and its associated files"""
    try:
        # Mock deletion logic
        if not transcription_id.startswith("transcript_"):
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # In real implementation:
        # 1. Delete transcription record from database
        # 2. Delete associated files from storage
        # 3. Clean up any related data
        
        logger.info(f"Deleted transcription {transcription_id}")
        
        return create_api_response(
            {"transcription_id": transcription_id},
            "Transcription deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transcription: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete transcription")

@router.put("/transcriptions/{transcription_id}")
async def update_transcription_metadata(
    transcription_id: str = Path(...),
    title: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
    user_id: str = "test_user"
):
    """Update transcription metadata (title, tags, notes)"""
    try:
        if not transcription_id.startswith("transcript_"):
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        updates = {}
        if title is not None:
            updates["title"] = title
        if tags is not None:
            updates["tags"] = tags
        if notes is not None:
            updates["notes"] = notes
        
        updates["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"Updated transcription {transcription_id} with: {updates}")
        
        return create_api_response(
            {"transcription_id": transcription_id, "updates": updates},
            "Transcription metadata updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update transcription metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to update transcription metadata")

@router.post("/transcriptions/{transcription_id}/duplicate")
async def duplicate_transcription(
    transcription_id: str = Path(...),
    new_title: Optional[str] = None,
    user_id: str = "test_user"
):
    """Create a duplicate of an existing transcription"""
    try:
        if not transcription_id.startswith("transcript_"):
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # Generate new ID for duplicate
        import uuid
        new_id = f"transcript_{uuid.uuid4().hex[:8]}"
        
        duplicate_data = {
            "original_id": transcription_id,
            "new_id": new_id,
            "new_title": new_title or f"Copy of Transcription {transcription_id.split('_')[1]}",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Created duplicate of transcription {transcription_id} as {new_id}")
        
        return create_api_response(duplicate_data, "Transcription duplicated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to duplicate transcription: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate transcription")