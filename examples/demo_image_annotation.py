#!/usr/bin/env python3
"""
Demo Script for Image Annotation System
Shows core functionality and usage examples
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw
import tempfile
import os
from datetime import datetime

from image_annotation_system import (
    AnnotationManager, AnnotationType, Point, Color, AnnotationStyle,
    BoundingBoxAnnotation, CircleAnnotation, TextAnnotation,
    PolygonAnnotation, LineAnnotation, ArrowAnnotation,
    FreehandAnnotation, BlurAnnotation, HighlightAnnotation
)

def create_sample_image():
    """Create a sample image for demonstration"""
    # Create a blank white image
    width, height = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Draw some sample content
    cv2.rectangle(image, (50, 50), (250, 200), (200, 200, 200), -1)
    cv2.circle(image, (400, 150), 80, (180, 180, 180), -1)
    cv2.putText(image, "Sample Image", (300, 400), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
    
    # Draw a simple scene
    cv2.rectangle(image, (500, 300), (750, 550), (220, 220, 220), -1)  # Building
    cv2.rectangle(image, (550, 400), (600, 480), (150, 150, 150), -1)  # Door
    cv2.rectangle(image, (620, 350), (670, 400), (150, 150, 150), -1)  # Window
    cv2.rectangle(image, (680, 350), (730, 400), (150, 150, 150), -1)  # Window
    
    # Save to temporary file
    temp_path = tempfile.mktemp(suffix='.jpg')
    cv2.imwrite(temp_path, image)
    
    return temp_path

def demo_basic_annotations():
    """Demonstrate basic annotation functionality"""
    print("=== Basic Annotations Demo ===\n")
    
    # Create annotation manager
    manager = AnnotationManager()
    
    # Create sample image
    image_path = create_sample_image()
    print(f"Created sample image: {image_path}")
    
    # Create annotated image
    annotated_image = manager.create_annotated_image(image_path)
    print(f"Created annotated image with ID: {annotated_image.image_id}")
    
    # Add bounding box annotation
    bbox = BoundingBoxAnnotation(
        label="Object 1",
        top_left=Point(50, 50),
        bottom_right=Point(250, 200),
        style=AnnotationStyle(
            stroke_color=Color(255, 0, 0),
            stroke_width=3
        )
    )
    manager.add_annotation(annotated_image.image_id, bbox)
    print("Added bounding box annotation")
    
    # Add circle annotation
    circle = CircleAnnotation(
        label="Circle Area",
        center=Point(400, 150),
        radius=80,
        style=AnnotationStyle(
            stroke_color=Color(0, 255, 0),
            fill_color=Color(0, 255, 0, 50),
            stroke_width=2
        )
    )
    manager.add_annotation(annotated_image.image_id, circle)
    print("Added circle annotation")
    
    # Add text annotation
    text = TextAnnotation(
        position=Point(300, 450),
        text="Important Note",
        style=AnnotationStyle(
            stroke_color=Color(0, 0, 255),
            font_size=20
        )
    )
    manager.add_annotation(annotated_image.image_id, text)
    print("Added text annotation")
    
    # Add arrow annotation
    arrow = ArrowAnnotation(
        label="Points to building",
        start=Point(450, 250),
        end=Point(600, 350),
        arrow_size=15,
        style=AnnotationStyle(
            stroke_color=Color(255, 0, 255),
            stroke_width=3
        )
    )
    manager.add_annotation(annotated_image.image_id, arrow)
    print("Added arrow annotation")
    
    # Add polygon annotation for the building
    polygon = PolygonAnnotation(
        label="Building",
        points=[
            Point(500, 300),
            Point(750, 300),
            Point(750, 550),
            Point(500, 550)
        ],
        closed=True,
        style=AnnotationStyle(
            stroke_color=Color(128, 0, 128),
            stroke_width=2
        )
    )
    manager.add_annotation(annotated_image.image_id, polygon)
    print("Added polygon annotation")
    
    # Render and save annotated image
    rendered = manager.render_image(annotated_image.image_id)
    output_path = "demo_annotated_basic.jpg"
    cv2.imwrite(output_path, rendered)
    print(f"\nSaved annotated image to: {output_path}")
    
    # Clean up
    os.unlink(image_path)
    
    return manager, annotated_image

def demo_advanced_annotations():
    """Demonstrate advanced annotation features"""
    print("\n=== Advanced Annotations Demo ===\n")
    
    # Create annotation manager
    manager = AnnotationManager()
    
    # Create sample image
    image_path = create_sample_image()
    
    # Create annotated image
    annotated_image = manager.create_annotated_image(image_path)
    
    # Add highlight annotation
    highlight = HighlightAnnotation(
        label="Important Area",
        top_left=Point(300, 380),
        bottom_right=Point(450, 420),
        highlight_color=Color(255, 255, 0, 100),
        style=AnnotationStyle()
    )
    manager.add_annotation(annotated_image.image_id, highlight)
    print("Added highlight annotation")
    
    # Add blur annotation (for privacy)
    blur = BlurAnnotation(
        label="Private Info",
        top_left=Point(620, 350),
        bottom_right=Point(670, 400),
        blur_strength=25,
        style=AnnotationStyle()
    )
    manager.add_annotation(annotated_image.image_id, blur)
    print("Added blur annotation")
    
    # Add freehand annotation
    freehand_points = []
    for i in range(50):
        angle = i * 0.2
        x = 150 + 50 * np.cos(angle)
        y = 400 + 50 * np.sin(angle)
        freehand_points.append(Point(x, y))
    
    freehand = FreehandAnnotation(
        label="Freehand Drawing",
        points=freehand_points,
        smooth=True,
        style=AnnotationStyle(
            stroke_color=Color(255, 128, 0),
            stroke_width=3
        )
    )
    manager.add_annotation(annotated_image.image_id, freehand)
    print("Added freehand annotation")
    
    # Render and save
    rendered = manager.render_image(annotated_image.image_id)
    output_path = "demo_annotated_advanced.jpg"
    cv2.imwrite(output_path, rendered)
    print(f"\nSaved advanced annotated image to: {output_path}")
    
    # Clean up
    os.unlink(image_path)
    
    return manager, annotated_image

def demo_undo_redo():
    """Demonstrate undo/redo functionality"""
    print("\n=== Undo/Redo Demo ===\n")
    
    # Use existing manager from basic demo
    manager, annotated_image = demo_basic_annotations()
    
    # Count initial annotations
    initial_count = len(annotated_image.annotations)
    print(f"\nInitial annotation count: {initial_count}")
    
    # Undo last operation
    manager.undo(annotated_image.image_id)
    print(f"After undo: {len(annotated_image.annotations)} annotations")
    
    # Undo again
    manager.undo(annotated_image.image_id)
    print(f"After second undo: {len(annotated_image.annotations)} annotations")
    
    # Redo
    manager.redo(annotated_image.image_id)
    print(f"After redo: {len(annotated_image.annotations)} annotations")
    
    # Redo again
    manager.redo(annotated_image.image_id)
    print(f"After second redo: {len(annotated_image.annotations)} annotations")

def demo_export_import():
    """Demonstrate export/import functionality"""
    print("\n=== Export/Import Demo ===\n")
    
    # Use existing manager from basic demo
    manager, annotated_image = demo_basic_annotations()
    
    # Export to JSON
    json_export = manager.export_annotations(annotated_image.image_id, "json")
    print("Exported to JSON format")
    
    # Save to file
    with open("demo_annotations.json", "w") as f:
        f.write(json_export)
    print("Saved JSON export to: demo_annotations.json")
    
    # Export to COCO format
    coco_export = manager.export_annotations(annotated_image.image_id, "coco")
    print("\nExported to COCO format")
    
    # Export to YOLO format
    yolo_export = manager.export_annotations(annotated_image.image_id, "yolo")
    print("Exported to YOLO format")
    
    # Clear annotations
    annotated_image.annotations = []
    print("\nCleared all annotations")
    
    # Re-import from JSON
    success = manager.import_annotations(annotated_image.image_id, json_export, "json")
    if success:
        print(f"Successfully imported annotations. Count: {len(annotated_image.annotations)}")
    else:
        print("Failed to import annotations")

def demo_annotation_queries():
    """Demonstrate querying annotations"""
    print("\n=== Annotation Query Demo ===\n")
    
    # Use existing manager from basic demo
    manager, annotated_image = demo_basic_annotations()
    
    # Test point inside bounding box
    test_point = Point(150, 100)
    annotations_at_point = manager.get_annotations_at_point(
        annotated_image.image_id, test_point
    )
    print(f"Annotations at point ({test_point.x}, {test_point.y}): {len(annotations_at_point)}")
    for ann in annotations_at_point:
        print(f"  - {ann.annotation_type.value}: {ann.label}")
    
    # Test point inside circle
    test_point2 = Point(400, 150)
    annotations_at_point2 = manager.get_annotations_at_point(
        annotated_image.image_id, test_point2
    )
    print(f"\nAnnotations at point ({test_point2.x}, {test_point2.y}): {len(annotations_at_point2)}")
    for ann in annotations_at_point2:
        print(f"  - {ann.annotation_type.value}: {ann.label}")

def demo_visibility_control():
    """Demonstrate annotation visibility control"""
    print("\n=== Visibility Control Demo ===\n")
    
    # Use existing manager from basic demo
    manager, annotated_image = demo_basic_annotations()
    
    # Hide specific annotation
    if annotated_image.annotations:
        first_annotation = annotated_image.annotations[0]
        print(f"Hiding annotation: {first_annotation.label}")
        
        manager.update_annotation(
            annotated_image.image_id,
            first_annotation.annotation_id,
            {'visible': False}
        )
        
        # Render with hidden annotation
        rendered = manager.render_image(annotated_image.image_id)
        cv2.imwrite("demo_annotated_hidden.jpg", rendered)
        print("Saved image with hidden annotation to: demo_annotated_hidden.jpg")
        
        # Show again
        manager.update_annotation(
            annotated_image.image_id,
            first_annotation.annotation_id,
            {'visible': True}
        )
        print("Annotation made visible again")

def main():
    """Run all demos"""
    print("Image Annotation System Demo")
    print("=" * 50)
    
    # Run demos
    demo_basic_annotations()
    demo_advanced_annotations()
    demo_undo_redo()
    demo_export_import()
    demo_annotation_queries()
    demo_visibility_control()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nGenerated files:")
    print("- demo_annotated_basic.jpg")
    print("- demo_annotated_advanced.jpg")
    print("- demo_annotated_hidden.jpg")
    print("- demo_annotations.json")

if __name__ == "__main__":
    main()