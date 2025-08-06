"""
Processing Queue API Endpoints - Improved Exception Handling
REST API for managing transcription processing queue with specific exception handling
"""

from fastapi import APIRouter, Depends, HTTPException, Path, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio
import json
from pydantic import BaseModel, ValidationError
import uuid

from api.dependencies import auth_required, create_api_response

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
    if not websocket_connections:
        return
        
    disconnected_clients = []
    
    for websocket in websocket_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except WebSocketDisconnect:
            logger.debug("WebSocket client disconnected during broadcast")
            disconnected_clients.append(websocket)
        except ConnectionError as e:
            logger.warning(f"WebSocket connection error: {e}")
            disconnected_clients.append(websocket)
        except RuntimeError as e:
            # WebSocket might be closed
            logger.warning(f"WebSocket runtime error: {e}")
            disconnected_clients.append(websocket)
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode message as JSON: {e}")
            # Don't disconnect client for encoding errors
        except Exception as e:
            # Catch any other unexpected errors but be specific in logging
            logger.error(f"Unexpected WebSocket broadcast error: {type(e).__name__}: {e}")
            disconnected_clients.append(websocket)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        if client in websocket_connections:
            websocket_connections.remove(client)

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
        avg_processing_time = 0.0
        completed_items = [item for item in items if item.status == "completed" and item.started_at and item.completed_at]
        
        if completed_items:
            total_processing_time = 0
            valid_items = 0
            
            for item in completed_items:
                try:
                    start = datetime.fromisoformat(item.started_at)
                    end = datetime.fromisoformat(item.completed_at)
                    processing_time = (end - start).total_seconds()
                    
                    # Sanity check - processing time should be positive and reasonable
                    if 0 < processing_time < 86400:  # Less than 24 hours
                        total_processing_time += processing_time
                        valid_items += 1
                except ValueError as e:
                    logger.warning(f"Invalid datetime format in queue item {item.id}: {e}")
                    continue
                except TypeError as e:
                    logger.warning(f"Invalid datetime data in queue item {item.id}: {e}")
                    continue
            
            if valid_items > 0:
                avg_processing_time = total_processing_time / valid_items
        
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
        
    except ValidationError as e:
        logger.error(f"Data validation error in queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid queue data format"
        )
    except MemoryError as e:
        logger.error(f"Memory error retrieving queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to process queue data"
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving queue status: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving queue status"
        )

@router.post("/add")
async def add_to_queue(
    file_id: str,
    priority: int = 1,
    user_id: str = "test_user"
):
    """Add a file to the processing queue"""
    try:
        # Validate priority
        if not isinstance(priority, int) or priority < 1 or priority > 3:
            raise ValueError(f"Invalid priority: {priority}. Must be 1, 2, or 3")
        
        # Validate file_id
        if not file_id or not isinstance(file_id, str):
            raise ValueError("Invalid file_id")
        
        # Generate queue ID
        try:
            queue_id = f"queue_{uuid.uuid4().hex[:8]}"
        except (AttributeError, IndexError) as e:
            logger.error(f"Failed to generate queue ID: {e}")
            queue_id = f"queue_{int(datetime.now().timestamp())}"
        
        queue_item = {
            "id": queue_id,
            "file_id": file_id,
            "status": "pending",
            "progress": 0,
            "priority": priority,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "estimated_position": len([item for item in processing_queue.values() if item.get('status') == "pending"]) + 1
        }
        
        # Add to queue storage
        processing_queue[queue_id] = queue_item
        
        # Broadcast update
        try:
            await broadcast_queue_update({
                "type": "item_added",
                "data": queue_item
            })
        except Exception as e:
            # Log but don't fail the request if broadcast fails
            logger.warning(f"Failed to broadcast queue update: {e}")
        
        logger.info(f"Added file {file_id} to queue as {queue_id}")
        
        return create_api_response(queue_item, "File added to processing queue")
        
    except ValueError as e:
        logger.error(f"Invalid queue parameters: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required parameter: {e}"
        )

@router.post("/{queue_id}/cancel")
async def cancel_queue_item(
    queue_id: str = Path(..., description="Queue item ID"),
    user_id: str = "test_user"
):
    """Cancel a queued or processing item"""
    try:
        # Validate queue_id format
        if not queue_id or not isinstance(queue_id, str):
            raise ValueError("Invalid queue_id")
        
        # Check if item exists (mock check for now)
        if not queue_id.startswith("queue_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue item '{queue_id}' not found"
            )
        
        # In production, check if item belongs to user and is cancellable
        # For now, just update status
        cancel_data = {
            "queue_id": queue_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "cancelled_by": user_id
        }
        
        # Broadcast update
        try:
            await broadcast_queue_update({
                "type": "item_cancelled",
                "data": cancel_data
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast cancellation: {e}")
        
        logger.info(f"Cancelled queue item {queue_id}")
        
        return create_api_response(cancel_data, "Queue item cancelled successfully")
        
    except ValueError as e:
        logger.error(f"Invalid cancel request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise

@router.get("/{queue_id}/progress")
async def get_queue_item_progress(
    queue_id: str = Path(..., description="Queue item ID"),
    user_id: str = "test_user"
):
    """Get detailed progress information for a specific queue item"""
    try:
        # Validate queue_id
        if not queue_id or not isinstance(queue_id, str):
            raise ValueError("Invalid queue_id")
            
        if not queue_id.startswith("queue_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue item '{queue_id}' not found"
            )
        
        # Mock progress data
        import random
        
        try:
            progress_value = round(random.uniform(0, 100), 1)
            estimated_minutes = random.randint(2, 10)
            processing_seconds = random.randint(30, 180)
        except (ValueError, TypeError) as e:
            logger.error(f"Random value generation error: {e}")
            progress_value = 50.0
            estimated_minutes = 5
            processing_seconds = 90
        
        progress_data = {
            "queue_id": queue_id,
            "status": "processing",
            "progress": progress_value,
            "current_step": "Extracting audio features",
            "steps": [
                {"name": "File validation", "status": "completed", "duration": 2.1},
                {"name": "Audio preprocessing", "status": "completed", "duration": 15.3},
                {"name": "Speech recognition", "status": "processing", "progress": 45.2},
                {"name": "Entity extraction", "status": "pending"},
                {"name": "Post-processing", "status": "pending"}
            ],
            "estimated_completion": (datetime.now() + timedelta(minutes=estimated_minutes)).isoformat(),
            "processing_time": processing_seconds,
            "log_messages": [
                {"timestamp": datetime.now().isoformat(), "level": "INFO", "message": "Starting transcription process"},
                {"timestamp": (datetime.now() - timedelta(seconds=30)).isoformat(), "level": "INFO", "message": "Audio preprocessing completed"},
                {"timestamp": (datetime.now() - timedelta(seconds=15)).isoformat(), "level": "INFO", "message": "Speech recognition in progress"}
            ]
        }
        
        return create_api_response(progress_data, "Queue item progress retrieved successfully")
        
    except ValueError as e:
        logger.error(f"Invalid progress request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise

@router.post("/{queue_id}/retry")
async def retry_failed_item(
    queue_id: str = Path(..., description="Queue item ID"),
    user_id: str = "test_user"
):
    """Retry a failed queue item"""
    try:
        # Validate queue_id
        if not queue_id or not isinstance(queue_id, str):
            raise ValueError("Invalid queue_id")
            
        if not queue_id.startswith("queue_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue item '{queue_id}' not found"
            )
        
        # In production, verify item is in failed state and belongs to user
        retry_data = {
            "queue_id": queue_id,
            "status": "pending",
            "retried_at": datetime.now().isoformat(),
            "retry_count": 1,
            "estimated_position": 1  # Add to front of queue for retry
        }
        
        # Broadcast update
        try:
            await broadcast_queue_update({
                "type": "item_retried",
                "data": retry_data
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast retry update: {e}")
        
        logger.info(f"Retrying queue item {queue_id}")
        
        return create_api_response(retry_data, "Queue item added for retry")
        
    except ValueError as e:
        logger.error(f"Invalid retry request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise

@router.delete("/clear")
async def clear_completed_items(
    user_id: str = "test_user"
):
    """Clear all completed and failed items from the queue"""
    try:
        # Count items to clear
        cleared_count = 0
        items_to_clear = []
        
        for queue_id, item in processing_queue.items():
            try:
                if isinstance(item, dict) and item.get('status') in ["completed", "failed", "cancelled"]:
                    items_to_clear.append(queue_id)
                    cleared_count += 1
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid queue item structure: {e}")
                continue
        
        # Remove items
        for queue_id in items_to_clear:
            try:
                del processing_queue[queue_id]
            except KeyError:
                # Item might have been removed by another process
                pass
        
        # Broadcast update
        try:
            await broadcast_queue_update({
                "type": "queue_cleared",
                "data": {"cleared_count": cleared_count}
            })
        except Exception as e:
            logger.warning(f"Failed to broadcast clear update: {e}")
        
        logger.info(f"Cleared {cleared_count} completed items from queue")
        
        return create_api_response(
            {"cleared_count": cleared_count},
            f"Cleared {cleared_count} completed items from queue"
        )
        
    except MemoryError as e:
        logger.error(f"Memory error clearing queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail="Insufficient memory to clear queue"
        )

@router.websocket("/ws")
async def queue_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time queue updates"""
    try:
        await websocket.accept()
        websocket_connections.append(websocket)
        
        # Send initial queue status
        try:
            queue_data = await get_queue_status()
            await websocket.send_text(json.dumps({
                "type": "initial_data",
                "data": queue_data.dict()
            }))
        except json.JSONEncodeError as e:
            logger.error(f"Failed to encode initial data: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to send initial data"
            }))
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Set a timeout for receiving messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                try:
                    message = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from WebSocket client: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    continue
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe_to_item":
                    queue_id = message.get("queue_id")
                    if queue_id:
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "queue_id": queue_id
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Missing queue_id for subscription"
                        }))
                
            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except:
                    break
            except WebSocketDisconnect:
                break
            except ConnectionError as e:
                logger.debug(f"WebSocket connection error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {type(e).__name__}: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

# Background task to simulate queue processing
async def simulate_queue_processing():
    """Background task to simulate queue item processing"""
    while True:
        try:
            # Find processing items and update their progress
            for queue_id, item in list(processing_queue.items()):
                try:
                    if isinstance(item, dict) and item.get('status') == "processing":
                        # Simulate progress update
                        current_progress = item.get('progress', 0)
                        
                        try:
                            import random
                            increment = random.uniform(5, 15)
                        except (ImportError, ValueError) as e:
                            logger.error(f"Random generation error: {e}")
                            increment = 10
                        
                        item['progress'] = min(100, current_progress + increment)
                        
                        if item['progress'] >= 100:
                            item['status'] = "completed"
                            item['completed_at'] = datetime.now().isoformat()
                        
                        # Broadcast progress update
                        try:
                            await broadcast_queue_update({
                                "type": "progress_update",
                                "data": item
                            })
                        except Exception as e:
                            logger.warning(f"Failed to broadcast progress: {e}")
                            
                except (KeyError, TypeError) as e:
                    logger.warning(f"Invalid queue item in processing: {e}")
                    continue
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except asyncio.CancelledError:
            logger.info("Queue processing simulation cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in queue simulation: {type(e).__name__}: {e}")
            await asyncio.sleep(5)  # Wait longer on error