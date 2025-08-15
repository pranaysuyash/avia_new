"""
Image Entity Extraction API Endpoints
Provides REST API interface for the Image Entity Extraction System
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import base64
import io
import logging
import os
import sys
import json
import uuid
from datetime import datetime
import tempfile
import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from api.middleware.audit_logging import audit_log
from database.connection import get_db

# Import the entity extraction system
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from image_entity_extraction_system import ImageEntityExtractionSystem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/entity-extraction")

# Global system instance
extraction_system = ImageEntityExtractionSystem()

# In-memory task storage (replace with database in production)
extraction_tasks = {}

# Pydantic models
class EntityExtractionRequest(BaseModel):
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    extraction_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extraction configuration options"
    )
    include_visualization: bool = Field(False, description="Include visualization in response")
    output_format: str = Field("json", description="Output format: json, csv")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_data": "base64_encoded_image_here",
                "extraction_config": {
                    "confidence_threshold": 0.5,
                    "max_entities": 100,
                    "entity_types": ["all"]
                },
                "include_visualization": True,
                "output_format": "json"
            }
        }

class EntityExtractionResponse(BaseModel):
    task_id: str
    status: str
    entities: Optional[List[Dict[str, Any]]] = None
    entity_count: Optional[int] = None
    relationships: Optional[List[Dict[str, Any]]] = None
    visualization_url: Optional[str] = None
    processing_time: Optional[float] = None
    timestamp: Optional[str] = None
    message: Optional[str] = None

class BatchExtractionRequest(BaseModel):
    images: List[str] = Field(..., description="List of base64 encoded images")
    extraction_config: Dict[str, Any] = Field(default_factory=dict)
    include_visualization: bool = Field(False)

class ExtractionStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    result: Optional[EntityExtractionResponse] = None

@router.post("/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("entity_extraction"))
):
    """
    Extract entities from an image
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate input
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Initialize task
        extraction_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "user_id": current_user.get("user_id") if current_user else "anonymous",
            "config": request.extraction_config
        }
        
        # Start background processing
        background_tasks.add_task(
            process_entity_extraction,
            task_id,
            request.image_data,
            request.extraction_config,
            request.include_visualization,
            request.output_format
        )
        
        # Track API usage
        await track_api_call("entity_extraction", current_user)
        
        # Audit log
        await audit_log(
            user_id=current_user.get("user_id") if current_user else None,
            action="entity_extraction_initiated",
            details={"task_id": task_id, "config": request.extraction_config}
        )
        
        return EntityExtractionResponse(
            task_id=task_id,
            status="processing",
            message="Entity extraction started"
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract/upload")
async def extract_entities_upload(
    file: UploadFile = File(...),
    extraction_config: str = Query("{}"),
    include_visualization: bool = Query(False),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("entity_extraction"))
):
    """
    Extract entities from an uploaded image file
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
        
        # Read file
        image_data = await file.read()
        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Parse config
        try:
            config_dict = json.loads(extraction_config) if extraction_config else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in extraction_config")
        
        # Create request
        request = EntityExtractionRequest(
            image_data=image_base64,
            extraction_config=config_dict,
            include_visualization=include_visualization
        )
        
        return await extract_entities(request, background_tasks, current_user, quota_check)
        
    except Exception as e:
        logger.error(f"File upload extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=Dict[str, Any])
async def batch_extract_entities(
    request: BatchExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("batch_entity_extraction"))
):
    """
    Extract entities from multiple images in batch
    """
    try:
        if len(request.images) > 20:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large. Maximum 20 images.")
        
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Process each image
        for i, image_data in enumerate(request.images):
            task_id = f"{batch_id}_img_{i:03d}"
            task_ids.append(task_id)
            
            # Initialize task
            extraction_tasks[task_id] = {
                "status": "processing",
                "started_at": datetime.now().isoformat(),
                "batch_id": batch_id,
                "user_id": current_user.get("user_id") if current_user else "anonymous"
            }
            
            # Start processing
            background_tasks.add_task(
                process_entity_extraction,
                task_id,
                image_data,
                request.extraction_config,
                request.include_visualization,
                "json"
            )
        
        await track_api_call("batch_entity_extraction", current_user)
        
        return {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "status": "processing",
            "total_images": len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of an entity extraction task
    """
    if task_id not in extraction_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = extraction_tasks[task_id]
    
    response = ExtractionStatusResponse(
        task_id=task_id,
        status=task.get("status"),
        progress=task.get("progress"),
        message=task.get("message")
    )
    
    # Include results if completed
    if task.get("status") == "completed":
        response.result = EntityExtractionResponse(
            task_id=task_id,
            status="completed",
            entities=task.get("entities"),
            entity_count=task.get("entity_count"),
            relationships=task.get("relationships"),
            visualization_url=task.get("visualization_url"),
            processing_time=task.get("processing_time"),
            timestamp=task.get("timestamp")
        )
    
    return response

@router.get("/results/{task_id}")
async def get_extraction_results(
    task_id: str,
    format: str = Query("json", description="Output format: json, csv"),
    current_user=Depends(get_current_user)
):
    """
    Get extraction results in specified format
    """
    if task_id not in extraction_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = extraction_tasks[task_id]
    
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    entities = task.get("entities", [])
    
    if format == "csv":
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        if entities:
            writer = csv.DictWriter(output, fieldnames=entities[0].keys())
            writer.writeheader()
            writer.writerows(entities)
        
        return {
            "format": "csv",
            "data": output.getvalue()
        }
    else:
        return {
            "format": "json",
            "data": {
                "entities": entities,
                "relationships": task.get("relationships", []),
                "metadata": {
                    "entity_count": task.get("entity_count", 0),
                    "processing_time": task.get("processing_time", 0),
                    "timestamp": task.get("timestamp")
                }
            }
        }

@router.get("/batch/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of a batch extraction job
    """
    batch_tasks = {k: v for k, v in extraction_tasks.items() 
                   if v.get("batch_id") == batch_id}
    
    if not batch_tasks:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    total = len(batch_tasks)
    completed = sum(1 for task in batch_tasks.values() if task["status"] == "completed")
    failed = sum(1 for task in batch_tasks.values() if task["status"] == "failed")
    processing = total - completed - failed
    
    return {
        "batch_id": batch_id,
        "total": total,
        "completed": completed,
        "failed": failed,
        "processing": processing,
        "progress": completed / total * 100 if total > 0 else 0,
        "tasks": {task_id: task["status"] for task_id, task in batch_tasks.items()}
    }

@router.post("/visualize/{task_id}")
async def create_visualization(
    task_id: str,
    visualization_options: Dict[str, Any] = {},
    current_user=Depends(get_current_user)
):
    """
    Create visualization for extraction results
    """
    if task_id not in extraction_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = extraction_tasks[task_id]
    
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    try:
        # Generate visualization showing detected entities
        import matplotlib.pyplot as plt
        from io import BytesIO
        import base64
        import numpy as np
        
        # Get entities from task
        entities = task.get("entities", [])
        
        # Create visualization figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Extract entity types and confidence scores for visualization
        entity_types = [entity.get("type", "Unknown") for entity in entities]
        
        # Count entity types
        type_counts = {}
        type_confidences = {}
        for entity_type in set(entity_types):  # Use set to avoid duplicates
            count = entity_types.count(entity_type)
            type_counts[entity_type] = count
            # Store confidence scores for this type
            type_confidences[entity_type] = []
        
        # Add confidence scores to each type
        for entity in entities:
            entity_type = entity.get("type", "Unknown")
            confidence = entity.get("confidence", 0)
            if entity_type in type_confidences:
                type_confidences[entity_type].append(confidence)
        
        # Calculate average confidence per type
        avg_confidences = {}
        for entity_type, confidences in type_confidences.items():
            if confidences:
                avg_confidences[entity_type] = np.mean(confidences)
            else:
                avg_confidences[entity_type] = 0
        
        # Create bar chart of entity types with confidence coloring
        entity_types_unique = list(type_counts.keys())
        counts = [type_counts[etype] for etype in entity_types_unique]
        confidences = [avg_confidences.get(etype, 0) for etype in entity_types_unique]
        
        # Create color map based on confidence
        colors = plt.cm.viridis([conf for conf in confidences])
        
        bars = ax.bar(range(len(entity_types_unique)), counts, color=colors)
        ax.set_xlabel('Entity Types')
        ax.set_ylabel('Count')
        ax.set_title('Extracted Entity Distribution with Confidence Levels')
        
        # Add type labels
        ax.set_xticks(range(len(entity_types_unique)))
        ax.set_xticklabels(entity_types_unique, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, count, conf in zip(bars, counts, confidences):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count}\n({conf:.2f})',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Convert to base64 for embedding
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Generate visualization URL
        visualization_url = f"data:image/png;base64,{image_base64}"
        
        # Update task with visualization URL
        extraction_tasks[task_id]["visualization_url"] = visualization_url
        
        return {
            "task_id": task_id,
            "visualization_url": visualization_url,
            "message": "Visualization created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error generating visualization for task {task_id}: {e}")
        # Return a default visualization URL even on error
        default_url = f"/api/v1/entity-extraction/visualization/{task_id}.png"
        extraction_tasks[task_id]["visualization_url"] = default_url
        
        return {
            "task_id": task_id,
            "visualization_url": default_url,
            "message": "Visualization generation failed - using default URL"
        }

@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Delete a task and its results
    """
    if task_id not in extraction_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check ownership
    task = extraction_tasks[task_id]
    if task.get("user_id") != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    
    del extraction_tasks[task_id]
    
    return {"message": "Task deleted successfully"}

@router.get("/stats")
async def get_extraction_stats(
    time_range: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    current_user=Depends(get_current_user)
):
    """
    Get entity extraction statistics
    """
    from datetime import timedelta
    
    # Calculate time cutoff
    now = datetime.now()
    if time_range == "1h":
        cutoff = now - timedelta(hours=1)
    elif time_range == "24h":
        cutoff = now - timedelta(days=1)
    elif time_range == "7d":
        cutoff = now - timedelta(days=7)
    elif time_range == "30d":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = now - timedelta(days=1)
    
    # Filter tasks by time and user
    user_tasks = [
        task for task in extraction_tasks.values()
        if task.get("user_id") == current_user.get("user_id") and
           datetime.fromisoformat(task.get("started_at", "2000-01-01")) > cutoff
    ]
    
    # Calculate statistics
    total_tasks = len(user_tasks)
    completed_tasks = sum(1 for task in user_tasks if task.get("status") == "completed")
    failed_tasks = sum(1 for task in user_tasks if task.get("status") == "failed")
    total_entities = sum(task.get("entity_count", 0) for task in user_tasks if task.get("status") == "completed")
    avg_processing_time = np.mean([task.get("processing_time", 0) for task in user_tasks if task.get("status") == "completed"]) if completed_tasks > 0 else 0
    
    return {
        "time_range": time_range,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": completed_tasks / total_tasks * 100 if total_tasks > 0 else 0,
        "total_entities_extracted": total_entities,
        "average_processing_time": round(avg_processing_time, 2),
        "timestamp": datetime.now().isoformat()
    }

# Background processing function
async def process_entity_extraction(
    task_id: str,
    image_data: str,
    extraction_config: Dict[str, Any],
    include_visualization: bool,
    output_format: str
):
    """
    Background task for entity extraction processing
    """
    try:
        # Update task status
        extraction_tasks[task_id]["status"] = "processing"
        extraction_tasks[task_id]["progress"] = 0.1
        
        # Decode image
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Could not decode image")
        
        # Update progress
        extraction_tasks[task_id]["progress"] = 0.3
        
        # Perform entity extraction
        start_time = datetime.now()
        results = extraction_system.extract_entities(image, extraction_config)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Update progress
        extraction_tasks[task_id]["progress"] = 0.8
        
        # Process results
        entities = []
        relationships = []
        
        if hasattr(results, 'entities'):
            for entity in results.entities:
                entities.append({
                    "id": entity.id,
                    "type": entity.type,
                    "label": entity.label,
                    "confidence": entity.confidence,
                    "bbox": entity.bbox,
                    "attributes": entity.attributes
                })
        
        if hasattr(results, 'relationships'):
            for rel in results.relationships:
                relationships.append({
                    "source": rel.source,
                    "target": rel.target,
                    "type": rel.type,
                    "confidence": rel.confidence
                })
        
        # Generate visualization if requested
        visualization_url = None
        if include_visualization:
            try:
                # Create visualization showing detected entities
                import matplotlib.pyplot as plt
                from io import BytesIO
                import base64
                import numpy as np
                
                # Create visualization figure
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Extract entity types for visualization
                entity_types = [entity.get("type", "Unknown") for entity in entities]
                
                # Count entity types
                type_counts = {}
                for entity_type in set(entity_types):  # Use set to avoid duplicates
                    count = entity_types.count(entity_type)
                    type_counts[entity_type] = count
                
                # Create pie chart of entity distribution
                if type_counts:
                    labels = list(type_counts.keys())
                    sizes = list(type_counts.values())
                    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                    
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                    ax.set_title('Entity Type Distribution')
                else:
                    ax.text(0.5, 0.5, 'No entities detected', horizontalalignment='center', 
                            verticalalignment='center', transform=ax.transAxes)
                    ax.set_title('Entity Type Distribution')
                
                plt.tight_layout()
                
                # Save to buffer
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                plt.close()
                
                # Convert to base64 for embedding
                image_base64 = base64.b64encode(buffer.getvalue()).decode()
                visualization_url = f"data:image/png;base64,{image_base64}"
                
            except Exception as viz_error:
                logger.warning(f"Visualization generation failed: {viz_error}")
                visualization_url = f"/api/v1/entity-extraction/visualization/{task_id}.png"
        
        # Update task with results
        extraction_tasks[task_id].update({
            "status": "completed",
            "progress": 1.0,
            "entities": entities,
            "entity_count": len(entities),
            "relationships": relationships,
            "visualization_url": visualization_url,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        # Update task with error
        extraction_tasks[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": str(e),
            "failed_at": datetime.now().isoformat()
        })
        logger.error(f"Entity extraction failed for task {task_id}: {e}")

@router.get("/health")
async def health_check():
    """
    Health check for entity extraction service
    """
    return {
        "status": "healthy",
        "service": "entity_extraction",
        "active_tasks": len([t for t in extraction_tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(extraction_tasks),
        "timestamp": datetime.now().isoformat()
    }