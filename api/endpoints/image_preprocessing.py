"""
REST API endpoints for Image Preprocessing System (Task 82)
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import base64
import io
import logging
from datetime import datetime
import tempfile
import os
import json
import uuid
import numpy as np
import cv2
from PIL import Image

from api.auth_middleware import get_current_user
from api.middleware.quota_enforcement import require_quota, track_api_call
from database.connection import get_db
from sqlalchemy.orm import Session

# Import preprocessing functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from image_preprocessing_system import ImagePreprocessor, PreprocessingConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/image")

# Global preprocessor instance
image_preprocessor = ImagePreprocessor()

# Pydantic models
class ImagePreprocessingRequest(BaseModel):
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preprocessing configuration options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_data": "base64_encoded_image_here",
                "config": {
                    "enable_denoising": True,
                    "denoise_method": "bilateral",
                    "auto_contrast": True,
                    "enable_sharpening": True,
                    "auto_deskew": True,
                    "upscale_factor": 2.0
                }
            }
        }

class ImagePreprocessingResponse(BaseModel):
    task_id: str
    status: str
    processed_image: Optional[str] = None  # Base64 encoded
    original_image: Optional[str] = None   # Base64 encoded
    operations_applied: List[str] = []
    quality_metrics: Dict[str, float] = {}
    processing_time: float = 0.0
    metadata: Dict[str, Any] = {}
    message: Optional[str] = None

class BatchProcessingRequest(BaseModel):
    images: List[str] = Field(..., description="List of base64 encoded images")
    config: Dict[str, Any] = Field(default_factory=dict)
    
class ConfigurationRequest(BaseModel):
    preset: str = Field("default", description="Preset configuration name")
    custom_config: Optional[Dict[str, Any]] = None

# In-memory task storage (in production, use Redis or database)
processing_tasks = {}

@router.post("/preprocess", response_model=ImagePreprocessingResponse)
async def preprocess_image(
    request: ImagePreprocessingRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("image_processing"))
):
    """
    Preprocess a single image with advanced enhancement algorithms
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Validate input
        if not request.image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Create preprocessing config
        config = PreprocessingConfig(**request.config)
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.image_data)
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Invalid image data")
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image data: {str(e)}")
        
        # Initialize task
        processing_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now(),
            "user_id": current_user.get("user_id") if current_user else "anonymous"
        }
        
        # Start background processing
        background_tasks.add_task(
            process_image_background, 
            task_id, 
            image, 
            config,
            request.image_data
        )
        
        # Track API usage
        await track_api_call("image_preprocessing", current_user)
        
        return ImagePreprocessingResponse(
            task_id=task_id,
            status="processing",
            message="Image preprocessing started"
        )
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preprocess/upload")
async def preprocess_uploaded_image(
    file: UploadFile = File(...),
    config: str = Form("{}"),
    background_tasks: BackgroundTasks = None,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("image_processing"))
):
    """
    Preprocess an uploaded image file
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
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid config JSON")
        
        # Create request
        request = ImagePreprocessingRequest(
            image_data=image_base64,
            config=config_dict
        )
        
        return await preprocess_image(request, background_tasks, current_user, quota_check)
        
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/preprocess")
async def batch_preprocess_images(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    quota_check=Depends(require_quota("batch_processing"))
):
    """
    Process multiple images in batch
    """
    try:
        if len(request.images) > 50:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size too large. Maximum 50 images.")
        
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Process each image
        for i, image_data in enumerate(request.images):
            task_id = f"{batch_id}_{i:03d}"
            task_ids.append(task_id)
            
            # Decode image
            try:
                image_bytes = base64.b64decode(image_data)
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if image is None:
                    continue
                    
            except Exception:
                continue
            
            # Create config
            config = PreprocessingConfig(**request.config)
            
            # Initialize task
            processing_tasks[task_id] = {
                "status": "processing",
                "started_at": datetime.now(),
                "batch_id": batch_id,
                "user_id": current_user.get("user_id") if current_user else "anonymous"
            }
            
            # Start processing
            background_tasks.add_task(
                process_image_background,
                task_id,
                image,
                config,
                image_data
            )
        
        await track_api_call("batch_image_processing", current_user)
        
        return {
            "batch_id": batch_id,
            "task_ids": task_ids,
            "status": "processing",
            "total_images": len(task_ids)
        }
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}", response_model=ImagePreprocessingResponse)
async def get_processing_status(
    task_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of an image preprocessing task
    """
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = processing_tasks[task_id]
    
    return ImagePreprocessingResponse(
        task_id=task_id,
        status=task["status"],
        processed_image=task.get("processed_image"),
        original_image=task.get("original_image"),
        operations_applied=task.get("operations_applied", []),
        quality_metrics=task.get("quality_metrics", {}),
        processing_time=task.get("processing_time", 0.0),
        metadata=task.get("metadata", {}),
        message=task.get("message")
    )

@router.get("/batch/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    current_user=Depends(get_current_user)
):
    """
    Get the status of a batch processing job
    """
    batch_tasks = {k: v for k, v in processing_tasks.items() 
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

@router.get("/presets")
async def get_configuration_presets():
    """
    Get available preprocessing configuration presets
    """
    presets = {
        "default": {
            "enable_denoising": True,
            "auto_contrast": True,
            "enable_sharpening": True,
            "auto_deskew": True
        },
        "ocr_optimized": {
            "enable_denoising": True,
            "denoise_method": "bilateral",
            "auto_contrast": True,
            "enable_sharpening": True,
            "sharpen_method": "unsharp_mask",
            "auto_threshold": True,
            "upscale_factor": 2.0,
            "output_format": "GRAY"
        },
        "high_quality": {
            "enable_denoising": True,
            "denoise_method": "nlm",
            "auto_contrast": True,
            "enable_sharpening": True,
            "sharpen_method": "unsharp_mask",
            "auto_deskew": True,
            "perspective_correction": True,
            "upscale_factor": 1.5,
            "remove_borders": True
        },
        "fast_processing": {
            "enable_denoising": True,
            "denoise_method": "gaussian",
            "auto_contrast": True,
            "enable_sharpening": False,
            "auto_deskew": False,
            "upscale_factor": 1.0
        }
    }
    
    return {"presets": presets}

@router.post("/config/validate")
async def validate_configuration(config: Dict[str, Any]):
    """
    Validate a preprocessing configuration
    """
    try:
        # Try to create PreprocessingConfig instance
        preprocessing_config = PreprocessingConfig(**config)
        
        return {
            "valid": True,
            "config": preprocessing_config.__dict__,
            "message": "Configuration is valid"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "message": "Invalid configuration"
        }

# Background task functions
async def process_image_background(task_id: str, image: np.ndarray, config: PreprocessingConfig, original_image_data: str):
    """
    Background task for image processing
    """
    try:
        # Update task status
        processing_tasks[task_id]["status"] = "processing"
        
        # Process image
        result = image_preprocessor.preprocess_image(image, config)
        
        # Encode processed image
        _, buffer = cv2.imencode('.png', result.processed_image)
        processed_image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Update task with results
        processing_tasks[task_id].update({
            "status": "completed",
            "processed_image": processed_image_base64,
            "original_image": original_image_data,
            "operations_applied": result.operations_applied,
            "quality_metrics": result.quality_metrics,
            "processing_time": result.processing_time,
            "metadata": result.metadata,
            "completed_at": datetime.now()
        })
        
    except Exception as e:
        # Update task with error
        processing_tasks[task_id].update({
            "status": "failed",
            "message": str(e),
            "failed_at": datetime.now()
        })
        logger.error(f"Background image processing failed for task {task_id}: {e}")

# Cleanup endpoint for removing old tasks
@router.delete("/tasks/cleanup")
async def cleanup_old_tasks(
    hours: int = 24,
    current_user=Depends(get_current_user)
):
    """
    Clean up tasks older than specified hours
    """
    cutoff_time = datetime.now().timestamp() - (hours * 3600)
    
    removed_count = 0
    for task_id in list(processing_tasks.keys()):
        task = processing_tasks[task_id]
        task_time = task.get("started_at", datetime.now()).timestamp()
        
        if task_time < cutoff_time:
            del processing_tasks[task_id]
            removed_count += 1
    
    return {"removed_tasks": removed_count}

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check for image preprocessing service
    """
    return {
        "status": "healthy",
        "service": "image_preprocessing",
        "active_tasks": len([t for t in processing_tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(processing_tasks),
        "timestamp": datetime.now().isoformat()
    }