#!/usr/bin/env python3
"""
Image Annotation API Endpoints
Provides RESTful API for image annotation and markup functionality
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
import io
import base64
from PIL import Image
import numpy as np
import cv2

from api.dependencies import get_db, get_current_user
from database.models import User
from image_annotation_system import (
    AnnotationManager, AnnotationRenderer, AnnotationType, DrawingMode,
    Point, Color, AnnotationStyle, Annotation, BoundingBoxAnnotation,
    CircleAnnotation, TextAnnotation, PolygonAnnotation, LineAnnotation,
    ArrowAnnotation, FreehandAnnotation, BlurAnnotation, HighlightAnnotation
)

router = APIRouter()

# Global annotation manager (in production, use proper storage)
annotation_manager = AnnotationManager()

from pydantic import BaseModel, Field

class AnnotationRequest(BaseModel):
    """Base annotation request model"""
    annotation_type: str = Field(..., description="Type of annotation")
    label: Optional[str] = Field(None, description="Annotation label")
    style: Dict[str, Any] = Field(default_factory=dict, description="Style properties")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class BoundingBoxRequest(AnnotationRequest):
    """Bounding box annotation request"""
    top_left: Dict[str, float] = Field(..., description="Top-left coordinate")
    bottom_right: Dict[str, float] = Field(..., description="Bottom-right coordinate")

class CircleRequest(AnnotationRequest):
    """Circle annotation request"""
    center: Dict[str, float] = Field(..., description="Center coordinate")
    radius: float = Field(..., description="Circle radius")

class TextRequest(AnnotationRequest):
    """Text annotation request"""
    position: Dict[str, float] = Field(..., description="Text position")
    text: str = Field(..., description="Text content")

class PolygonRequest(AnnotationRequest):
    """Polygon annotation request"""
    points: List[Dict[str, float]] = Field(..., description="Polygon points")
    closed: bool = Field(True, description="Whether polygon is closed")

class LineRequest(AnnotationRequest):
    """Line annotation request"""
    start: Dict[str, float] = Field(..., description="Line start point")
    end: Dict[str, float] = Field(..., description="Line end point")

class ArrowRequest(AnnotationRequest):
    """Arrow annotation request"""
    start: Dict[str, float] = Field(..., description="Arrow start point")
    end: Dict[str, float] = Field(..., description="Arrow end point")
    arrow_size: float = Field(10.0, description="Arrow size")

class FreehandRequest(AnnotationRequest):
    """Freehand annotation request"""
    points: List[Dict[str, float]] = Field(..., description="Freehand points")
    smooth: bool = Field(True, description="Apply smoothing")

@router.post("/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload an image for annotation"""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        contents = await file.read()
        
        # Save temporarily and create annotated image
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(contents)
            temp_path = tmp.name
        
        # Create annotated image
        annotated_image = annotation_manager.create_annotated_image(temp_path)
        
        # Clean up
        import os
        os.unlink(temp_path)
        
        return {
            "image_id": annotated_image.image_id,
            "width": annotated_image.width,
            "height": annotated_image.height,
            "created_at": annotated_image.created_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{image_id}")
async def get_image_info(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get image information and annotations"""
    try:
        if image_id not in annotation_manager.annotated_images:
            raise HTTPException(status_code=404, detail="Image not found")
        
        annotated_image = annotation_manager.annotated_images[image_id]
        
        return {
            "image_id": annotated_image.image_id,
            "width": annotated_image.width,
            "height": annotated_image.height,
            "annotations": [
                {
                    "id": ann.annotation_id,
                    "type": ann.annotation_type.value,
                    "label": ann.label,
                    "visible": ann.visible,
                    "locked": ann.locked,
                    "created_at": ann.created_at.isoformat(),
                    "updated_at": ann.updated_at.isoformat()
                }
                for ann in annotated_image.annotations
            ],
            "created_at": annotated_image.created_at.isoformat(),
            "updated_at": annotated_image.updated_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/annotations/bbox")
async def add_bounding_box(
    image_id: str,
    request: BoundingBoxRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a bounding box annotation"""
    try:
        # Create style
        style = create_style_from_dict(request.style)
        
        # Create annotation
        bbox = BoundingBoxAnnotation(
            label=request.label or "",
            top_left=Point(request.top_left["x"], request.top_left["y"]),
            bottom_right=Point(request.bottom_right["x"], request.bottom_right["y"]),
            style=style,
            metadata=request.metadata
        )
        
        # Add to image
        success = annotation_manager.add_annotation(image_id, bbox)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "annotation_id": bbox.annotation_id,
            "message": "Bounding box added successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/annotations/circle")
async def add_circle(
    image_id: str,
    request: CircleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a circle annotation"""
    try:
        # Create style
        style = create_style_from_dict(request.style)
        
        # Create annotation
        circle = CircleAnnotation(
            label=request.label or "",
            center=Point(request.center["x"], request.center["y"]),
            radius=request.radius,
            style=style,
            metadata=request.metadata
        )
        
        # Add to image
        success = annotation_manager.add_annotation(image_id, circle)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "annotation_id": circle.annotation_id,
            "message": "Circle added successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/annotations/text")
async def add_text(
    image_id: str,
    request: TextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a text annotation"""
    try:
        # Create style
        style = create_style_from_dict(request.style)
        
        # Create annotation
        text_ann = TextAnnotation(
            position=Point(request.position["x"], request.position["y"]),
            text=request.text,
            style=style,
            metadata=request.metadata
        )
        
        # Add to image
        success = annotation_manager.add_annotation(image_id, text_ann)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "annotation_id": text_ann.annotation_id,
            "message": "Text added successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/annotations/polygon")
async def add_polygon(
    image_id: str,
    request: PolygonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a polygon annotation"""
    try:
        # Create style
        style = create_style_from_dict(request.style)
        
        # Create points
        points = [Point(p["x"], p["y"]) for p in request.points]
        
        # Create annotation
        polygon = PolygonAnnotation(
            label=request.label or "",
            points=points,
            closed=request.closed,
            style=style,
            metadata=request.metadata
        )
        
        # Add to image
        success = annotation_manager.add_annotation(image_id, polygon)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {
            "annotation_id": polygon.annotation_id,
            "message": "Polygon added successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/images/{image_id}/annotations/{annotation_id}")
async def delete_annotation(
    image_id: str,
    annotation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an annotation"""
    try:
        success = annotation_manager.remove_annotation(image_id, annotation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image or annotation not found")
        
        return {"message": "Annotation deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/images/{image_id}/annotations/{annotation_id}")
async def update_annotation(
    image_id: str,
    annotation_id: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an annotation"""
    try:
        success = annotation_manager.update_annotation(image_id, annotation_id, updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Image or annotation not found")
        
        return {"message": "Annotation updated successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{image_id}/render")
async def render_image(
    image_id: str,
    format: str = Query("base64", enum=["base64", "url"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Render image with annotations"""
    try:
        # Render image
        rendered = annotation_manager.render_image(image_id)
        
        if rendered is None:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Convert to base64
        _, buffer = cv2.imencode('.jpg', rendered)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        if format == "base64":
            return {
                "format": "base64",
                "data": image_base64
            }
        else:
            # In production, upload to storage and return URL
            return {
                "format": "url",
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{image_id}/export")
async def export_annotations(
    image_id: str,
    format: str = Query("json", enum=["json", "coco", "yolo"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export annotations in various formats"""
    try:
        exported = annotation_manager.export_annotations(image_id, format)
        
        if exported is None:
            raise HTTPException(status_code=404, detail="Image not found or export failed")
        
        return {
            "format": format,
            "data": exported if format == "json" else exported,
            "filename": f"annotations_{image_id}.{format}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/import")
async def import_annotations(
    image_id: str,
    file: UploadFile = File(...),
    format: str = Query("json", enum=["json", "coco", "yolo"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import annotations from file"""
    try:
        # Read file content
        content = await file.read()
        data = content.decode('utf-8')
        
        # Import annotations
        success = annotation_manager.import_annotations(image_id, data, format)
        
        if not success:
            raise HTTPException(status_code=400, detail="Import failed")
        
        return {"message": "Annotations imported successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/undo")
async def undo_annotation(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Undo last annotation operation"""
    try:
        success = annotation_manager.undo(image_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="No operations to undo")
        
        return {"message": "Operation undone successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/images/{image_id}/redo")
async def redo_annotation(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Redo last undone operation"""
    try:
        success = annotation_manager.redo(image_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="No operations to redo")
        
        return {"message": "Operation redone successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images/{image_id}/annotations/at-point")
async def get_annotations_at_point(
    image_id: str,
    x: float = Query(..., description="X coordinate"),
    y: float = Query(..., description="Y coordinate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all annotations at a specific point"""
    try:
        point = Point(x, y)
        annotations = annotation_manager.get_annotations_at_point(image_id, point)
        
        return {
            "point": {"x": x, "y": y},
            "annotations": [
                {
                    "id": ann.annotation_id,
                    "type": ann.annotation_type.value,
                    "label": ann.label
                }
                for ann in annotations
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_style_from_dict(style_dict: Dict[str, Any]) -> AnnotationStyle:
    """Create annotation style from dictionary"""
    style = AnnotationStyle()
    
    if "stroke_color" in style_dict:
        color = style_dict["stroke_color"]
        if isinstance(color, str) and color.startswith("#"):
            # Parse hex color
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            style.stroke_color = Color(r, g, b)
        elif isinstance(color, dict):
            style.stroke_color = Color(
                color.get("r", 255),
                color.get("g", 0),
                color.get("b", 0),
                color.get("a", 255)
            )
    
    if "fill_color" in style_dict and style_dict["fill_color"]:
        color = style_dict["fill_color"]
        if isinstance(color, str) and color.startswith("#"):
            # Parse hex color
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            style.fill_color = Color(r, g, b, 128)
        elif isinstance(color, dict):
            style.fill_color = Color(
                color.get("r", 255),
                color.get("g", 255),
                color.get("b", 0),
                color.get("a", 128)
            )
    
    if "stroke_width" in style_dict:
        style.stroke_width = style_dict["stroke_width"]
    
    if "font_size" in style_dict:
        style.font_size = style_dict["font_size"]
    
    if "opacity" in style_dict:
        style.opacity = style_dict["opacity"]
    
    return style