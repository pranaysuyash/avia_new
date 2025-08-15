"""
FastAPI endpoints for Media Ingestion Controller
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import tempfile
import os
import logging

from media_ingestion_controller import (
    MediaIngestionController, ProcessingOptions, IngestionResult
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/media-ingestion", tags=["Media Ingestion"])

# Global controller instance
controller = MediaIngestionController()


@router.post("/ingest")
async def ingest_media(
    file: UploadFile = File(...),
    enable_preprocessing: bool = True,
    enable_optimization: bool = False,
    target_quality: str = "high",
    max_width: Optional[int] = None,
    max_height: Optional[int] = None
):
    """
    Ingest media file with intelligent processing
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Configure processing options
            options = ProcessingOptions(
                enable_preprocessing=enable_preprocessing,
                enable_optimization=enable_optimization,
                target_quality=target_quality,
                max_resolution=(max_width, max_height) if max_width and max_height else None
            )
            
            # Perform ingestion
            result = await controller.ingest_media(temp_path, file.filename, options)
            
            # Convert result to JSON-serializable format
            response_data = {
                "success": result.success,
                "processing_time": result.processing_time,
                "operations_applied": result.operations_applied,
                "warnings": result.warnings,
                "errors": result.errors,
                "media_file": {
                    "id": result.media_file.id,
                    "original_filename": file.filename,
                    "file_size": len(content),
                    "processing_status": result.media_file.processing_status,
                    "format": {
                        "file_type": result.media_file.format.file_type if result.media_file.format else None,
                        "mime_type": result.media_file.format.mime_type if result.media_file.format else None,
                        "extension": result.media_file.format.extension if result.media_file.format else None,
                        "is_supported": result.media_file.format.is_supported if result.media_file.format else False
                    } if result.media_file.format else None,
                    "quality_metrics": {
                        "file_size": result.media_file.quality_metrics.file_size if result.media_file.quality_metrics else len(content),
                        "quality_score": result.media_file.quality_metrics.quality_score if result.media_file.quality_metrics else 0,
                        "resolution": result.media_file.quality_metrics.resolution if result.media_file.quality_metrics else None,
                        "duration": result.media_file.quality_metrics.duration if result.media_file.quality_metrics else None,
                        "bitrate": result.media_file.quality_metrics.bitrate if result.media_file.quality_metrics else None
                    } if result.media_file.quality_metrics else None
                }
            }
            
            return JSONResponse(content=response_data)
            
        finally:
            # Cleanup temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Media ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Media ingestion failed: {str(e)}")


@router.post("/detect-format")
async def detect_format(file: UploadFile = File(...)):
    """
    Detect media format without full processing
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Detect format
            format_info = await controller.detect_format(temp_path, file.filename)
            
            return {
                "filename": file.filename,
                "file_size": len(content),
                "format": {
                    "file_type": format_info.file_type,
                    "mime_type": format_info.mime_type,
                    "extension": format_info.extension,
                    "codec": format_info.codec,
                    "container": format_info.container,
                    "is_supported": format_info.is_supported
                }
            }
            
        finally:
            # Cleanup temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Format detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Format detection failed: {str(e)}")


@router.get("/upload-progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """
    Get upload progress for streaming uploads
    """
    progress = controller.get_upload_progress(upload_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return {
        "upload_id": upload_id,
        "total_size": progress.total_size,
        "uploaded_size": progress.uploaded_size,
        "progress_percentage": progress.progress_percentage,
        "upload_speed": progress.upload_speed,
        "estimated_time_remaining": progress.estimated_time_remaining,
        "status": progress.status
    }


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported media formats
    """
    from media_ingestion_controller import (
        SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_FORMATS,
        SUPPORTED_IMAGE_FORMATS, SUPPORTED_DOCUMENT_FORMATS
    )
    
    return {
        "audio": list(SUPPORTED_AUDIO_FORMATS),
        "video": list(SUPPORTED_VIDEO_FORMATS),
        "image": list(SUPPORTED_IMAGE_FORMATS),
        "document": list(SUPPORTED_DOCUMENT_FORMATS)
    }