#!/usr/bin/env python3
"""
Image Annotation and Markup System
Provides tools for interactive image annotation with bounding boxes, text overlays, and markup
"""

import os
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnnotationType(Enum):
    """Types of annotations supported"""
    BOUNDING_BOX = "bounding_box"
    POLYGON = "polygon"
    CIRCLE = "circle"
    LINE = "line"
    ARROW = "arrow"
    TEXT = "text"
    FREEHAND = "freehand"
    BLUR = "blur"
    HIGHLIGHT = "highlight"

class DrawingMode(Enum):
    """Drawing modes for annotations"""
    SELECT = "select"
    DRAW = "draw"
    EDIT = "edit"
    DELETE = "delete"

@dataclass
class Point:
    """Represents a 2D point"""
    x: float
    y: float
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def to_int_tuple(self) -> Tuple[int, int]:
        return (int(self.x), int(self.y))

@dataclass
class Color:
    """Represents a color"""
    r: int = 255
    g: int = 0
    b: int = 0
    a: int = 255  # Alpha channel
    
    def to_bgr(self) -> Tuple[int, int, int]:
        """Convert to BGR format for OpenCV"""
        return (self.b, self.g, self.r)
    
    def to_rgba(self) -> Tuple[int, int, int, int]:
        """Convert to RGBA format"""
        return (self.r, self.g, self.b, self.a)
    
    def to_hex(self) -> str:
        """Convert to hex color string"""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

@dataclass
class AnnotationStyle:
    """Style properties for annotations"""
    stroke_color: Color = field(default_factory=lambda: Color(255, 0, 0))
    fill_color: Optional[Color] = None
    stroke_width: int = 2
    font_size: int = 16
    font_family: str = "Arial"
    opacity: float = 1.0
    dash_pattern: Optional[List[int]] = None

@dataclass
class Annotation:
    """Base class for all annotations"""
    annotation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    annotation_type: AnnotationType = AnnotationType.BOUNDING_BOX
    label: str = ""
    style: AnnotationStyle = field(default_factory=AnnotationStyle)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    visible: bool = True
    locked: bool = False

@dataclass
class BoundingBoxAnnotation(Annotation):
    """Bounding box annotation"""
    annotation_type: AnnotationType = AnnotationType.BOUNDING_BOX
    top_left: Point = field(default_factory=lambda: Point(0, 0))
    bottom_right: Point = field(default_factory=lambda: Point(100, 100))
    
    @property
    def width(self) -> float:
        return abs(self.bottom_right.x - self.top_left.x)
    
    @property
    def height(self) -> float:
        return abs(self.bottom_right.y - self.top_left.y)
    
    @property
    def center(self) -> Point:
        return Point(
            (self.top_left.x + self.bottom_right.x) / 2,
            (self.top_left.y + self.bottom_right.y) / 2
        )
    
    def contains_point(self, point: Point) -> bool:
        """Check if point is inside bounding box"""
        return (self.top_left.x <= point.x <= self.bottom_right.x and
                self.top_left.y <= point.y <= self.bottom_right.y)

@dataclass
class PolygonAnnotation(Annotation):
    """Polygon annotation"""
    annotation_type: AnnotationType = AnnotationType.POLYGON
    points: List[Point] = field(default_factory=list)
    closed: bool = True

@dataclass
class CircleAnnotation(Annotation):
    """Circle annotation"""
    annotation_type: AnnotationType = AnnotationType.CIRCLE
    center: Point = field(default_factory=lambda: Point(50, 50))
    radius: float = 25.0

@dataclass
class LineAnnotation(Annotation):
    """Line annotation"""
    annotation_type: AnnotationType = AnnotationType.LINE
    start: Point = field(default_factory=lambda: Point(0, 0))
    end: Point = field(default_factory=lambda: Point(100, 100))

@dataclass
class ArrowAnnotation(LineAnnotation):
    """Arrow annotation (line with arrowhead)"""
    annotation_type: AnnotationType = AnnotationType.ARROW
    arrow_size: float = 10.0

@dataclass
class TextAnnotation(Annotation):
    """Text overlay annotation"""
    annotation_type: AnnotationType = AnnotationType.TEXT
    position: Point = field(default_factory=lambda: Point(50, 50))
    text: str = "Text"
    background: bool = True
    padding: int = 5

@dataclass
class FreehandAnnotation(Annotation):
    """Freehand drawing annotation"""
    annotation_type: AnnotationType = AnnotationType.FREEHAND
    points: List[Point] = field(default_factory=list)
    smooth: bool = True

@dataclass
class BlurAnnotation(BoundingBoxAnnotation):
    """Blur region annotation"""
    annotation_type: AnnotationType = AnnotationType.BLUR
    blur_strength: int = 25

@dataclass
class HighlightAnnotation(BoundingBoxAnnotation):
    """Highlight region annotation"""
    annotation_type: AnnotationType = AnnotationType.HIGHLIGHT
    highlight_color: Color = field(default_factory=lambda: Color(255, 255, 0, 128))

@dataclass
class AnnotatedImage:
    """Represents an image with annotations"""
    image_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    width: int = 0
    height: int = 0
    annotations: List[Annotation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class AnnotationRenderer:
    """Renders annotations on images"""
    
    def __init__(self):
        """Initialize the renderer"""
        self.font_cache = {}
        
    def render_annotations(self, image: np.ndarray, annotations: List[Annotation]) -> np.ndarray:
        """Render all annotations on the image"""
        # Create a copy to avoid modifying original
        rendered_image = image.copy()
        
        # Sort annotations by type (blur and highlight first)
        sorted_annotations = sorted(annotations, key=lambda a: (
            a.annotation_type not in [AnnotationType.BLUR, AnnotationType.HIGHLIGHT],
            a.created_at
        ))
        
        for annotation in sorted_annotations:
            if not annotation.visible:
                continue
                
            if isinstance(annotation, BoundingBoxAnnotation):
                rendered_image = self._render_bounding_box(rendered_image, annotation)
            elif isinstance(annotation, PolygonAnnotation):
                rendered_image = self._render_polygon(rendered_image, annotation)
            elif isinstance(annotation, CircleAnnotation):
                rendered_image = self._render_circle(rendered_image, annotation)
            elif isinstance(annotation, LineAnnotation):
                rendered_image = self._render_line(rendered_image, annotation)
            elif isinstance(annotation, ArrowAnnotation):
                rendered_image = self._render_arrow(rendered_image, annotation)
            elif isinstance(annotation, TextAnnotation):
                rendered_image = self._render_text(rendered_image, annotation)
            elif isinstance(annotation, FreehandAnnotation):
                rendered_image = self._render_freehand(rendered_image, annotation)
            elif isinstance(annotation, BlurAnnotation):
                rendered_image = self._render_blur(rendered_image, annotation)
            elif isinstance(annotation, HighlightAnnotation):
                rendered_image = self._render_highlight(rendered_image, annotation)
        
        return rendered_image
    
    def _render_bounding_box(self, image: np.ndarray, annotation: BoundingBoxAnnotation) -> np.ndarray:
        """Render a bounding box"""
        pt1 = annotation.top_left.to_int_tuple()
        pt2 = annotation.bottom_right.to_int_tuple()
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        # Draw rectangle
        cv2.rectangle(image, pt1, pt2, color, thickness)
        
        # Draw label if present
        if annotation.label:
            self._draw_label(image, annotation.label, pt1, annotation.style)
        
        return image
    
    def _render_polygon(self, image: np.ndarray, annotation: PolygonAnnotation) -> np.ndarray:
        """Render a polygon"""
        if len(annotation.points) < 2:
            return image
        
        pts = np.array([p.to_int_tuple() for p in annotation.points], np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        if annotation.closed and annotation.style.fill_color:
            # Filled polygon
            fill_color = annotation.style.fill_color.to_bgr()
            cv2.fillPoly(image, [pts], fill_color)
        
        # Draw outline
        cv2.polylines(image, [pts], annotation.closed, color, thickness)
        
        return image
    
    def _render_circle(self, image: np.ndarray, annotation: CircleAnnotation) -> np.ndarray:
        """Render a circle"""
        center = annotation.center.to_int_tuple()
        radius = int(annotation.radius)
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        if annotation.style.fill_color:
            # Filled circle
            fill_color = annotation.style.fill_color.to_bgr()
            cv2.circle(image, center, radius, fill_color, -1)
        
        # Draw outline
        cv2.circle(image, center, radius, color, thickness)
        
        return image
    
    def _render_line(self, image: np.ndarray, annotation: LineAnnotation) -> np.ndarray:
        """Render a line"""
        pt1 = annotation.start.to_int_tuple()
        pt2 = annotation.end.to_int_tuple()
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        cv2.line(image, pt1, pt2, color, thickness)
        
        return image
    
    def _render_arrow(self, image: np.ndarray, annotation: ArrowAnnotation) -> np.ndarray:
        """Render an arrow"""
        pt1 = annotation.start.to_int_tuple()
        pt2 = annotation.end.to_int_tuple()
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        # Draw line
        cv2.line(image, pt1, pt2, color, thickness)
        
        # Calculate arrowhead
        angle = np.arctan2(pt2[1] - pt1[1], pt2[0] - pt1[0])
        arrow_length = annotation.arrow_size
        
        # Arrowhead points
        pt3 = (int(pt2[0] - arrow_length * np.cos(angle - np.pi/6)),
               int(pt2[1] - arrow_length * np.sin(angle - np.pi/6)))
        pt4 = (int(pt2[0] - arrow_length * np.cos(angle + np.pi/6)),
               int(pt2[1] - arrow_length * np.sin(angle + np.pi/6)))
        
        # Draw arrowhead
        cv2.line(image, pt2, pt3, color, thickness)
        cv2.line(image, pt2, pt4, color, thickness)
        
        return image
    
    def _render_text(self, image: np.ndarray, annotation: TextAnnotation) -> np.ndarray:
        """Render text overlay"""
        # Convert to PIL for better text rendering
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)
        
        # Get font
        try:
            font = ImageFont.truetype(annotation.style.font_family, annotation.style.font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), annotation.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        pos = annotation.position.to_int_tuple()
        
        # Draw background if requested
        if annotation.background:
            padding = annotation.padding
            bg_color = annotation.style.fill_color or Color(255, 255, 255, 200)
            draw.rectangle(
                [pos[0] - padding, pos[1] - padding,
                 pos[0] + text_width + padding, pos[1] + text_height + padding],
                fill=bg_color.to_rgba()
            )
        
        # Draw text
        text_color = annotation.style.stroke_color.to_rgba()
        draw.text(pos, annotation.text, font=font, fill=text_color)
        
        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    def _render_freehand(self, image: np.ndarray, annotation: FreehandAnnotation) -> np.ndarray:
        """Render freehand drawing"""
        if len(annotation.points) < 2:
            return image
        
        color = annotation.style.stroke_color.to_bgr()
        thickness = annotation.style.stroke_width
        
        # Draw lines between consecutive points
        for i in range(1, len(annotation.points)):
            pt1 = annotation.points[i-1].to_int_tuple()
            pt2 = annotation.points[i].to_int_tuple()
            cv2.line(image, pt1, pt2, color, thickness)
        
        return image
    
    def _render_blur(self, image: np.ndarray, annotation: BlurAnnotation) -> np.ndarray:
        """Render blur effect"""
        x1, y1 = annotation.top_left.to_int_tuple()
        x2, y2 = annotation.bottom_right.to_int_tuple()
        
        # Ensure coordinates are within image bounds
        h, w = image.shape[:2]
        x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
        
        if x2 > x1 and y2 > y1:
            # Extract region
            roi = image[y1:y2, x1:x2]
            
            # Apply blur
            blurred = cv2.GaussianBlur(roi, (annotation.blur_strength, annotation.blur_strength), 0)
            
            # Replace region
            image[y1:y2, x1:x2] = blurred
        
        return image
    
    def _render_highlight(self, image: np.ndarray, annotation: HighlightAnnotation) -> np.ndarray:
        """Render highlight effect"""
        # Create overlay
        overlay = image.copy()
        
        pt1 = annotation.top_left.to_int_tuple()
        pt2 = annotation.bottom_right.to_int_tuple()
        color = annotation.highlight_color.to_bgr()
        
        # Draw filled rectangle on overlay
        cv2.rectangle(overlay, pt1, pt2, color, -1)
        
        # Blend with original image
        alpha = annotation.highlight_color.a / 255.0
        image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        return image
    
    def _draw_label(self, image: np.ndarray, label: str, position: Tuple[int, int], style: AnnotationStyle):
        """Draw a label near an annotation"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = style.font_size / 30.0
        thickness = max(1, style.stroke_width // 2)
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, thickness
        )
        
        # Position above the annotation
        text_x = position[0]
        text_y = position[1] - 5
        
        # Draw background
        padding = 3
        cv2.rectangle(
            image,
            (text_x - padding, text_y - text_height - padding),
            (text_x + text_width + padding, text_y + padding),
            (255, 255, 255),
            -1
        )
        
        # Draw text
        cv2.putText(
            image, label,
            (text_x, text_y),
            font, font_scale,
            style.stroke_color.to_bgr(),
            thickness
        )

class AnnotationManager:
    """Manages annotations for images"""
    
    def __init__(self):
        """Initialize the annotation manager"""
        self.annotated_images: Dict[str, AnnotatedImage] = {}
        self.renderer = AnnotationRenderer()
        self.undo_stack: Dict[str, List[Dict[str, Any]]] = {}
        self.redo_stack: Dict[str, List[Dict[str, Any]]] = {}
        
    def create_annotated_image(self, image_path: str) -> AnnotatedImage:
        """Create a new annotated image"""
        # Load image to get dimensions
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        height, width = image.shape[:2]
        
        # Create annotated image
        annotated_image = AnnotatedImage(
            file_path=image_path,
            width=width,
            height=height
        )
        
        # Store in manager
        self.annotated_images[annotated_image.image_id] = annotated_image
        self.undo_stack[annotated_image.image_id] = []
        self.redo_stack[annotated_image.image_id] = []
        
        logger.info(f"Created annotated image: {annotated_image.image_id}")
        return annotated_image
    
    def add_annotation(self, image_id: str, annotation: Annotation) -> bool:
        """Add an annotation to an image"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return False
        
        # Save state for undo
        self._save_state(image_id)
        
        # Add annotation
        self.annotated_images[image_id].annotations.append(annotation)
        self.annotated_images[image_id].updated_at = datetime.now()
        
        logger.info(f"Added {annotation.annotation_type.value} annotation to image {image_id}")
        return True
    
    def remove_annotation(self, image_id: str, annotation_id: str) -> bool:
        """Remove an annotation from an image"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return False
        
        # Save state for undo
        self._save_state(image_id)
        
        # Remove annotation
        image = self.annotated_images[image_id]
        image.annotations = [a for a in image.annotations if a.annotation_id != annotation_id]
        image.updated_at = datetime.now()
        
        logger.info(f"Removed annotation {annotation_id} from image {image_id}")
        return True
    
    def update_annotation(self, image_id: str, annotation_id: str, updates: Dict[str, Any]) -> bool:
        """Update an annotation"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return False
        
        # Save state for undo
        self._save_state(image_id)
        
        # Find and update annotation
        image = self.annotated_images[image_id]
        for annotation in image.annotations:
            if annotation.annotation_id == annotation_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(annotation, key):
                        setattr(annotation, key, value)
                annotation.updated_at = datetime.now()
                image.updated_at = datetime.now()
                
                logger.info(f"Updated annotation {annotation_id} in image {image_id}")
                return True
        
        logger.error(f"Annotation not found: {annotation_id}")
        return False
    
    def get_annotations_at_point(self, image_id: str, point: Point) -> List[Annotation]:
        """Get all annotations at a specific point"""
        if image_id not in self.annotated_images:
            return []
        
        annotations = []
        for annotation in self.annotated_images[image_id].annotations:
            if isinstance(annotation, BoundingBoxAnnotation):
                if annotation.contains_point(point):
                    annotations.append(annotation)
            elif isinstance(annotation, CircleAnnotation):
                distance = np.sqrt((point.x - annotation.center.x)**2 + 
                                 (point.y - annotation.center.y)**2)
                if distance <= annotation.radius:
                    annotations.append(annotation)
            # Add other annotation types as needed
        
        return annotations
    
    def render_image(self, image_id: str) -> Optional[np.ndarray]:
        """Render image with all annotations"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return None
        
        annotated_image = self.annotated_images[image_id]
        
        # Load base image
        image = cv2.imread(annotated_image.file_path)
        if image is None:
            logger.error(f"Failed to load image: {annotated_image.file_path}")
            return None
        
        # Render annotations
        rendered = self.renderer.render_annotations(image, annotated_image.annotations)
        
        return rendered
    
    def export_annotations(self, image_id: str, format: str = "json") -> Optional[str]:
        """Export annotations to various formats"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return None
        
        annotated_image = self.annotated_images[image_id]
        
        if format == "json":
            return self._export_json(annotated_image)
        elif format == "coco":
            return self._export_coco(annotated_image)
        elif format == "yolo":
            return self._export_yolo(annotated_image)
        else:
            logger.error(f"Unsupported export format: {format}")
            return None
    
    def import_annotations(self, image_id: str, data: str, format: str = "json") -> bool:
        """Import annotations from various formats"""
        if image_id not in self.annotated_images:
            logger.error(f"Image not found: {image_id}")
            return False
        
        # Save state for undo
        self._save_state(image_id)
        
        if format == "json":
            return self._import_json(image_id, data)
        elif format == "coco":
            return self._import_coco(image_id, data)
        elif format == "yolo":
            return self._import_yolo(image_id, data)
        else:
            logger.error(f"Unsupported import format: {format}")
            return False
    
    def undo(self, image_id: str) -> bool:
        """Undo last annotation operation"""
        if image_id not in self.undo_stack or not self.undo_stack[image_id]:
            return False
        
        # Save current state to redo stack
        current_state = self._get_state(image_id)
        if image_id not in self.redo_stack:
            self.redo_stack[image_id] = []
        self.redo_stack[image_id].append(current_state)
        
        # Restore previous state
        previous_state = self.undo_stack[image_id].pop()
        self._restore_state(image_id, previous_state)
        
        logger.info(f"Undone last operation on image {image_id}")
        return True
    
    def redo(self, image_id: str) -> bool:
        """Redo last undone operation"""
        if image_id not in self.redo_stack or not self.redo_stack[image_id]:
            return False
        
        # Save current state to undo stack (don't clear redo)
        self._save_state(image_id, clear_redo=False)
        
        # Restore next state
        next_state = self.redo_stack[image_id].pop()
        self._restore_state(image_id, next_state)
        
        logger.info(f"Redone last operation on image {image_id}")
        return True
    
    def _save_state(self, image_id: str, clear_redo: bool = True):
        """Save current state for undo"""
        if image_id in self.annotated_images:
            state = self._get_state(image_id)
            if image_id not in self.undo_stack:
                self.undo_stack[image_id] = []
            self.undo_stack[image_id].append(state)
            
            # Clear redo stack only for new operations
            if clear_redo:
                if image_id not in self.redo_stack:
                    self.redo_stack[image_id] = []
                self.redo_stack[image_id] = []
            
            # Limit undo stack size
            if len(self.undo_stack[image_id]) > 50:
                self.undo_stack[image_id].pop(0)
    
    def _get_state(self, image_id: str) -> Dict[str, Any]:
        """Get current state of annotations"""
        if image_id not in self.annotated_images:
            return {}
        
        # Deep copy annotations
        annotations_data = []
        for annotation in self.annotated_images[image_id].annotations:
            ann_dict = asdict(annotation)
            annotations_data.append(ann_dict)
        
        return {
            'annotations': annotations_data,
            'updated_at': self.annotated_images[image_id].updated_at
        }
    
    def _restore_state(self, image_id: str, state: Dict[str, Any]):
        """Restore annotations from saved state"""
        if image_id not in self.annotated_images:
            return
        
        # Clear current annotations
        self.annotated_images[image_id].annotations = []
        
        # Recreate annotations from state
        for ann_data in state.get('annotations', []):
            annotation = self._create_annotation_from_dict(ann_data)
            if annotation:
                self.annotated_images[image_id].annotations.append(annotation)
        
        self.annotated_images[image_id].updated_at = state.get('updated_at', datetime.now())
    
    def _create_annotation_from_dict(self, data: Dict[str, Any]) -> Optional[Annotation]:
        """Create annotation object from dictionary"""
        ann_type = AnnotationType(data.get('annotation_type'))
        
        # Convert nested objects
        if 'style' in data:
            style_data = data['style']
            if 'stroke_color' in style_data:
                style_data['stroke_color'] = Color(**style_data['stroke_color'])
            if 'fill_color' in style_data and style_data['fill_color']:
                style_data['fill_color'] = Color(**style_data['fill_color'])
            data['style'] = AnnotationStyle(**style_data)
        
        # Convert datetime strings
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Create appropriate annotation type
        if ann_type == AnnotationType.BOUNDING_BOX:
            data['top_left'] = Point(**data['top_left'])
            data['bottom_right'] = Point(**data['bottom_right'])
            return BoundingBoxAnnotation(**data)
        elif ann_type == AnnotationType.CIRCLE:
            data['center'] = Point(**data['center'])
            return CircleAnnotation(**data)
        elif ann_type == AnnotationType.TEXT:
            data['position'] = Point(**data['position'])
            return TextAnnotation(**data)
        # Add other types as needed
        
        return None
    
    def _export_json(self, annotated_image: AnnotatedImage) -> str:
        """Export annotations as JSON"""
        data = {
            'image_id': annotated_image.image_id,
            'file_path': annotated_image.file_path,
            'width': annotated_image.width,
            'height': annotated_image.height,
            'annotations': []
        }
        
        for annotation in annotated_image.annotations:
            ann_dict = asdict(annotation)
            # Convert enum to string
            ann_dict['annotation_type'] = ann_dict['annotation_type'].value
            # Convert datetime to string
            ann_dict['created_at'] = ann_dict['created_at'].isoformat()
            ann_dict['updated_at'] = ann_dict['updated_at'].isoformat()
            # Convert Color objects in style
            if 'style' in ann_dict:
                style = ann_dict['style']
                if 'stroke_color' in style:
                    style['stroke_color'] = {
                        'r': style['stroke_color']['r'],
                        'g': style['stroke_color']['g'],
                        'b': style['stroke_color']['b'],
                        'a': style['stroke_color']['a']
                    }
                if 'fill_color' in style and style['fill_color']:
                    style['fill_color'] = {
                        'r': style['fill_color']['r'],
                        'g': style['fill_color']['g'],
                        'b': style['fill_color']['b'],
                        'a': style['fill_color']['a']
                    }
            # Convert Point objects
            for key in ['top_left', 'bottom_right', 'center', 'position', 'start', 'end']:
                if key in ann_dict and ann_dict[key]:
                    ann_dict[key] = {'x': ann_dict[key]['x'], 'y': ann_dict[key]['y']}
            if 'points' in ann_dict and ann_dict['points']:
                ann_dict['points'] = [{'x': p['x'], 'y': p['y']} for p in ann_dict['points']]
            data['annotations'].append(ann_dict)
        
        return json.dumps(data, indent=2)
    
    def _export_coco(self, annotated_image: AnnotatedImage) -> str:
        """Export annotations in COCO format"""
        # Simplified COCO format export
        coco_data = {
            'images': [{
                'id': 1,
                'file_name': os.path.basename(annotated_image.file_path),
                'width': annotated_image.width,
                'height': annotated_image.height
            }],
            'annotations': [],
            'categories': []
        }
        
        # Extract unique labels as categories
        labels = set()
        for annotation in annotated_image.annotations:
            if annotation.label:
                labels.add(annotation.label)
        
        # Create categories
        label_to_id = {}
        for i, label in enumerate(labels, 1):
            coco_data['categories'].append({
                'id': i,
                'name': label,
                'supercategory': 'object'
            })
            label_to_id[label] = i
        
        # Convert annotations
        for i, annotation in enumerate(annotated_image.annotations):
            if isinstance(annotation, BoundingBoxAnnotation) and annotation.label:
                x = annotation.top_left.x
                y = annotation.top_left.y
                w = annotation.width
                h = annotation.height
                
                coco_data['annotations'].append({
                    'id': i + 1,
                    'image_id': 1,
                    'category_id': label_to_id.get(annotation.label, 1),
                    'bbox': [x, y, w, h],
                    'area': w * h,
                    'iscrowd': 0
                })
        
        return json.dumps(coco_data, indent=2)
    
    def _export_yolo(self, annotated_image: AnnotatedImage) -> str:
        """Export annotations in YOLO format"""
        # YOLO format: class_id center_x center_y width height (normalized)
        yolo_lines = []
        
        # Get unique labels
        labels = list(set(a.label for a in annotated_image.annotations if a.label))
        
        for annotation in annotated_image.annotations:
            if isinstance(annotation, BoundingBoxAnnotation) and annotation.label:
                # Get class ID
                class_id = labels.index(annotation.label) if annotation.label in labels else 0
                
                # Calculate normalized coordinates
                cx = annotation.center.x / annotated_image.width
                cy = annotation.center.y / annotated_image.height
                w = annotation.width / annotated_image.width
                h = annotation.height / annotated_image.height
                
                yolo_lines.append(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        
        return '\n'.join(yolo_lines)
    
    def _import_json(self, image_id: str, data: str) -> bool:
        """Import annotations from JSON"""
        try:
            json_data = json.loads(data)
            
            # Clear existing annotations
            self.annotated_images[image_id].annotations = []
            
            # Import annotations
            for ann_data in json_data.get('annotations', []):
                annotation = self._create_annotation_from_dict(ann_data)
                if annotation:
                    self.annotated_images[image_id].annotations.append(annotation)
            
            self.annotated_images[image_id].updated_at = datetime.now()
            logger.info(f"Imported {len(self.annotated_images[image_id].annotations)} annotations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import JSON: {e}")
            return False
    
    def _import_coco(self, image_id: str, data: str) -> bool:
        """Import annotations from COCO format"""
        # Implementation for COCO import
        # This would parse COCO format and convert to our annotation format
        logger.warning("COCO import not yet implemented")
        return False
    
    def _import_yolo(self, image_id: str, data: str) -> bool:
        """Import annotations from YOLO format"""
        # Implementation for YOLO import
        # This would parse YOLO format and convert to our annotation format
        logger.warning("YOLO import not yet implemented")
        return False

# Example usage
if __name__ == "__main__":
    # Create annotation manager
    manager = AnnotationManager()
    
    # Create annotated image
    # annotated_image = manager.create_annotated_image("sample_image.jpg")
    
    # Add some annotations
    # bbox = BoundingBoxAnnotation(
    #     label="Person",
    #     top_left=Point(100, 100),
    #     bottom_right=Point(200, 300)
    # )
    # manager.add_annotation(annotated_image.image_id, bbox)
    
    # Render and save
    # rendered = manager.render_image(annotated_image.image_id)
    # cv2.imwrite("annotated_output.jpg", rendered)
    
    print("Image annotation system initialized")