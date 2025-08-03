"""
Processing Queue API Endpoints
REST API for managing transcription processing queue
"""

from fastapi import APIRouter, Depends, HTTPException, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio
import json
from pydantic import BaseModel

from api.auth import auth_required, create_api_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queue", tags=["Processing Queue"])

# Data models
class QueueItem(BaseModel):
    id: str
    filename: str
    file_size: int
    status: str  # pending, processing, completed, failed, cancelled
    progress: float  # 0-100
    estimated_time: Optional[int] = None  # seconds
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high
    user_id: str
    created_at: str
    updated_at: str

class QueueStats(BaseModel):
    total_items: int
    pending: int
    processing: int
    completed: int
    failed: int
    cancelled: int
    avg_processing_time: float
    estimated_queue_time: int

class QueueResponse(BaseModel):
    items: List[QueueItem]
    stats: QueueStats

# In-memory queue storage (replace with Redis or database in production)
processing_queue: Dict[str, QueueItem] = {}
websocket_connections: List[WebSocket] = []

def generate_mock_queue_items() -> List[QueueItem]:
    """Generate mock queue data"""
    import random
    from datetime import datetime, timedelta
    
    items = []
    statuses = ["pending", "processing", "completed", "failed"]
    
    for i in range(10):
        status = random.choice(statuses)
        created_date = datetime.now() - timedelta(minutes=random.randint(1, 120))
        
        item = QueueItem(
            id=f"queue_{i+1:03d}",
            filename=f"audio_file_{i+1}.wav",
            file_size=random.randint(1000000, 50000000),
            status=status,
            progress=random.uniform(0, 100) if status == "processing" else (100 if status == "completed" else 0),
            estimated_time=random.randint(30, 300) if status in ["pending", "processing"] else None,
            started_at=created_date.isoformat() if status in ["processing", "completed", "failed"] else None,
            completed_at=(created_date + timedelta(minutes=random.randint(1, 30))).isoformat() if status in ["completed", "failed"] else None,
            error_message="Processing failed due to audio quality" if status == "failed" else None,
            priority=random.randint(1, 3),
            user_id="test_user",
            created_at=created_date.isoformat(),
            updated_at=datetime.now().isoformat()
        )
        items.append(item)
    
    return items

async def broadcast_queue_update(message: dict):
    """Broadcast queue updates to all connected WebSocket clients"""
    if websocket_connections:
        for websocket in websocket_connections.copy():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                logger.debug("WebSocket client disconnected during broadcast")
                websocket_connections.remove(websocket)
            except ConnectionError as e:
                logger.warning(f"WebSocket connection error: {e}")
                websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"Unexpected WebSocket error: {e}", exc_info=True)
                websocket_connections.remove(websocket)

@router.get("/status", response_model=QueueResponse)
async def get_queue_status(
    user_id: str = "test_user"
):
    """Get current processing queue status"""
    try:
        # Get queue items (mock data for now)
        items = generate_mock_queue_items()
        
        # Calculate stats
        total_items = len(items)
        pending = len([item for item in items if item.status == "pending"])
        processing = len([item for item in items if item.status == "processing"])
        completed = len([item for item in items if item.status == "completed"])
        failed = len([item for item in items if item.status == "failed"])
        cancelled = len([item for item in items if item.status == "cancelled"])
        
        # Calculate average processing time
        completed_items = [item for item in items if item.status == "completed" and item.started_at and item.completed_at]
        if completed_items:
            total_processing_time = 0
            for item in completed_items:
                start = datetime.fromisoformat(item.started_at)
                end = datetime.fromisoformat(item.completed_at)
                total_processing_time += (end - start).total_seconds()
            avg_processing_time = total_processing_time / len(completed_items)
        else:
            avg_processing_time = 0
        
        # Estimate queue time
        estimated_queue_time = pending * 120 + processing * 60  # rough estimate
        
        stats = QueueStats(
            total_items=total_items,
            pending=pending,
            processing=processing,
            completed=completed,
            failed=failed,
            cancelled=cancelled,
            avg_processing_time=avg_processing_time,
            estimated_queue_time=estimated_queue_time
        )
        
        return QueueResponse(items=items, stats=stats)
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue status")

@router.post("/add")
async def add_to_queue(
    file_id: str,
    priority: int = 1,
    user_id: str = "test_user"
):
    """Add a file to the processing queue"""
    try:
        import uuid
        
        queue_id = f"queue_{uuid.uuid4().hex[:8]}"
        
        queue_item = {
            "id": queue_id,
            "file_id": file_id,
            "status": "pending",
            "progress": 0,
            "priority": priority,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "estimated_position": len([item for item in processing_queue.values() if item.status == "pending"]) + 1
        }
        
        # Add to queue storage
        processing_queue[queue_id] = queue_item
        
        # Broadcast update
        await broadcast_queue_update({
            "type": "item_added",
            "data": queue_item
        })
        
        logger.info(f"Added file {file_id} to queue as {queue_id}")
        
        return create_api_response(queue_item, "File added to processing queue")
        
    except ValueError as e:
        logger.error(f"Invalid queue data: {e}")
        raise HTTPException(status_code=400, detail="Invalid queue parameters")
    except Exception as e:
        logger.error(f"Unexpected error adding to queue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add file to queue")

@router.post("/{queue_id}/cancel")
async def cancel_queue_item(
    queue_id: str = Path(...),
    user_id: str = "test_user"
):
    """Cancel a queued or processing item"""
    try:
        # Check if item exists (mock check)
        if not queue_id.startswith("queue_"):
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        # Update status
        cancel_data = {
            "queue_id": queue_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "cancelled_by": user_id
        }
        
        # Broadcast update
        await broadcast_queue_update({
            "type": "item_cancelled",
            "data": cancel_data
        })
        
        logger.info(f"Cancelled queue item {queue_id}")
        
        return create_api_response(cancel_data, "Queue item cancelled successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel queue item: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel queue item")

@router.get("/{queue_id}/progress")
async def get_queue_item_progress(
    queue_id: str = Path(...),
    user_id: str = "test_user"
):
    """Get detailed progress information for a specific queue item"""
    try:
        if not queue_id.startswith("queue_"):
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        # Mock progress data
        import random
        
        progress_data = {
            "queue_id": queue_id,
            "status": "processing",
            "progress": round(random.uniform(0, 100), 1),
            "current_step": "Extracting audio features",
            "steps": [
                {"name": "File validation", "status": "completed", "duration": 2.1},
                {"name": "Audio preprocessing", "status": "completed", "duration": 15.3},
                {"name": "Speech recognition", "status": "processing", "progress": 45.2},
                {"name": "Entity extraction", "status": "pending"},
                {"name": "Post-processing", "status": "pending"}
            ],
            "estimated_completion": (datetime.now() + timedelta(minutes=random.randint(2, 10))).isoformat(),
            "processing_time": random.randint(30, 180),
            "log_messages": [
                {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "Starting transcription process"},
                {"timestamp": (datetime.now() - timedelta(seconds=30)).isoformat(), "level": "INFO", "message": "Audio preprocessing completed"},
                {"timestamp": (datetime.now() - timedelta(seconds=15)).isoformat(), "level": "INFO", "message": "Speech recognition in progress"}
            ]
        }
        
        return create_api_response(progress_data, "Queue item progress retrieved successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get queue item progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue item progress")

@router.post("/{queue_id}/retry")
async def retry_failed_item(
    queue_id: str = Path(...),
    user_id: str = "test_user"
):
    """Retry a failed queue item"""
    try:
        if not queue_id.startswith("queue_"):
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        retry_data = {
            "queue_id": queue_id,
            "status": "pending",
            "retried_at": datetime.now().isoformat(),
            "retry_count": 1,
            "estimated_position": 1  # Add to front of queue for retry
        }
        
        # Broadcast update
        await broadcast_queue_update({
            "type": "item_retried",
            "data": retry_data
        })
        
        logger.info(f"Retrying queue item {queue_id}")
        
        return create_api_response(retry_data, "Queue item added for retry")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry queue item: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry queue item")

@router.delete("/clear")
async def clear_completed_items(
    user_id: str = "test_user"
):
    """Clear all completed and failed items from the queue"""
    try:
        # Mock clearing logic
        cleared_count = len([item for item in processing_queue.values() 
                           if item.status in ["completed", "failed", "cancelled"]])
        
        # Remove completed items (mock)
        processing_queue.clear()
        
        # Broadcast update
        await broadcast_queue_update({
            "type": "queue_cleared",
            "data": {"cleared_count": cleared_count}
        })
        
        logger.info(f"Cleared {cleared_count} completed items from queue")
        
        return create_api_response(
            {"cleared_count": cleared_count},
            f"Cleared {cleared_count} completed items from queue"
        )
        
    except Exception as e:
        logger.error(f"Failed to clear queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear queue")

@router.websocket("/ws")
async def queue_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time queue updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send initial queue status
        queue_data = await get_queue_status()
        await websocket.send_text(json.dumps({
            "type": "initial_data",
            "data": queue_data.dict()
        }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe_to_item":
                    # Client wants updates for specific queue item
                    queue_id = message.get("queue_id")
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "queue_id": queue_id
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Background task to simulate queue processing
async def simulate_queue_processing():
    """Background task to simulate queue item processing"""
    while True:
        try:
            # Find processing items and update their progress
            for queue_id, item in processing_queue.items():
                if item.status == "processing":
                    # Simulate progress update
                    item.progress = min(100, item.progress + random.uniform(5, 15))
                    
                    if item.progress >= 100:
                        item.status = "completed"
                        item.completed_at = datetime.now().isoformat()
                    
                    # Broadcast progress update
                    await broadcast_queue_update({
                        "type": "progress_update",
                        "data": item.dict()
                    })
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except asyncio.CancelledError:
            logger.info("Queue processing simulation cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in queue simulation: {e}", exc_info=True)
            await asyncio.sleep(5)