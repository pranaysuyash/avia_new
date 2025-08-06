#!/usr/bin/env python3
"""
Unified Media Processing API Endpoints
Provides RESTful API for integrated image-text workflow
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import tempfile
import os
import json

from api.dependencies import get_db, get_current_user
from database.models import User
from image_text_integration import (
    ImageTextIntegrationPipeline,
    CrossModalRecommendationEngine,
    WorkflowResult,
    MediaContent
)

router = APIRouter()

# Global pipeline instance (in production, use proper state management)
pipeline = ImageTextIntegrationPipeline()
recommendation_engine = CrossModalRecommendationEngine(pipeline)

@router.post("/unified/process")
async def process_media_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    content_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process any media file through the unified pipeline"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        # Process file
        result = pipeline.process_media_file(temp_path, content_type)
        
        # Clean up
        os.unlink(temp_path)
        
        # Return result
        return {
            "content_id": result.content_id,
            "content_type": result.content_type,
            "processing_time": result.processing_time,
            "text_sources": list(result.text_sources.keys()),
            "entity_count": sum(len(v) for v in result.entities.values()),
            "keyword_count": len(result.keywords),
            "has_summary": result.summary is not None,
            "similar_content_count": len(result.similar_content),
            "processing_steps": result.processing_steps
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified/content/{content_id}")
async def get_content_details(
    content_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about processed content"""
    try:
        if content_id not in pipeline.media_contents:
            raise HTTPException(status_code=404, detail="Content not found")
        
        content = pipeline.media_contents[content_id]
        
        return {
            "content_id": content.content_id,
            "content_type": content.content_type,
            "source_path": os.path.basename(content.source_path),
            "text_sources": {
                "transcript": content.transcript_text is not None,
                "ocr": content.ocr_text is not None,
                "caption": content.caption_text is not None,
                "annotation": content.annotation_text is not None
            },
            "combined_text_length": len(pipeline._combine_text_sources(content)),
            "entities": content.entities,
            "metadata": content.metadata,
            "created_at": content.created_at.isoformat(),
            "updated_at": content.updated_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unified/search")
async def search_unified_content(
    query: str,
    media_types: Optional[List[str]] = Query(None),
    top_k: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search across all processed media content"""
    try:
        results = pipeline.search_across_media(query, media_types, top_k)
        
        return {
            "query": query,
            "filters": {"media_types": media_types} if media_types else {},
            "result_count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified/recommendations/{content_id}")
async def get_content_recommendations(
    content_id: str,
    cross_modal: bool = Query(True, description="Prefer cross-modal recommendations"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get content recommendations based on similarity"""
    try:
        if content_id not in pipeline.media_contents:
            raise HTTPException(status_code=404, detail="Content not found")
        
        recommendations = recommendation_engine.get_recommendations(
            content_id,
            cross_modal=cross_modal,
            top_k=top_k
        )
        
        return {
            "source_content_id": content_id,
            "cross_modal": cross_modal,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified/analytics")
async def get_unified_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics across all processed content"""
    try:
        analytics = pipeline.get_content_analytics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analytics": analytics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unified/export")
async def export_unified_dataset(
    format: str = Query("json", enum=["json", "csv"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all processed content as a dataset"""
    try:
        # Create export
        if format == "json":
            # Export to temporary file
            temp_path = tempfile.mktemp(suffix='.json')
            pipeline.export_unified_dataset(temp_path)
            
            # Read content
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            # Clean up
            os.unlink(temp_path)
            
            return data
        
        elif format == "csv":
            # Convert to CSV format
            import pandas as pd
            
            # Collect data
            rows = []
            for content_id, content in pipeline.media_contents.items():
                row = {
                    'content_id': content_id,
                    'content_type': content.content_type,
                    'source_path': content.source_path,
                    'has_transcript': content.transcript_text is not None,
                    'has_ocr': content.ocr_text is not None,
                    'has_caption': content.caption_text is not None,
                    'text_length': len(pipeline._combine_text_sources(content)),
                    'entity_count': sum(len(v) for v in content.entities.values()),
                    'created_at': content.created_at.isoformat()
                }
                rows.append(row)
            
            # Create DataFrame
            df = pd.DataFrame(rows)
            
            # Return as dict (FastAPI will convert to JSON)
            return {
                "format": "csv",
                "columns": list(df.columns),
                "data": df.to_dict('records')
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unified/batch/process")
async def batch_process_media(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process multiple media files in batch"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Process files in background
        task_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            process_batch_files,
            files,
            task_id
        )
        
        return {
            "task_id": task_id,
            "file_count": len(files),
            "status": "processing",
            "message": "Batch processing started. Check status endpoint for progress."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_batch_files(files: List[UploadFile], task_id: str):
    """Background task to process multiple files"""
    results = []
    
    for file in files:
        try:
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_path = tmp.name
            
            # Process file
            result = pipeline.process_media_file(temp_path)
            results.append({
                "filename": file.filename,
                "content_id": result.content_id,
                "status": "success"
            })
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            })
    
    # Store results (in production, use proper storage)
    # For now, we'll just log them
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Batch {task_id} completed: {results}")

@router.get("/unified/text/{content_id}")
async def get_combined_text(
    content_id: str,
    source: Optional[str] = Query(None, enum=["transcript", "ocr", "caption", "annotation", "all"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get text content from specific source or combined"""
    try:
        if content_id not in pipeline.media_contents:
            raise HTTPException(status_code=404, detail="Content not found")
        
        content = pipeline.media_contents[content_id]
        
        if source == "all" or source is None:
            # Return all text combined
            return {
                "content_id": content_id,
                "source": "combined",
                "text": pipeline._combine_text_sources(content)
            }
        else:
            # Return specific source
            text_map = {
                "transcript": content.transcript_text,
                "ocr": content.ocr_text,
                "caption": content.caption_text,
                "annotation": content.annotation_text
            }
            
            text = text_map.get(source)
            if text is None:
                raise HTTPException(status_code=404, detail=f"No {source} text available for this content")
            
            return {
                "content_id": content_id,
                "source": source,
                "text": text
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/unified/content/{content_id}")
async def delete_content(
    content_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete processed content"""
    try:
        if content_id not in pipeline.media_contents:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Remove from pipeline
        del pipeline.media_contents[content_id]
        
        # Remove from search index
        # Note: In a real implementation, we'd also remove from the search engines
        
        return {
            "content_id": content_id,
            "status": "deleted",
            "message": "Content successfully deleted"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))