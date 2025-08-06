#!/usr/bin/env python3
"""
Simple test script for Image Annotation System
"""

import cv2
import numpy as np
import tempfile
import os

from image_annotation_system import (
    AnnotationManager, AnnotationType, Point, Color, AnnotationStyle,
    BoundingBoxAnnotation, CircleAnnotation, TextAnnotation
)

def test_basic_functionality():
    """Test basic annotation functionality"""
    print("Testing Image Annotation System...")
    
    try:
        # Create annotation manager
        manager = AnnotationManager()
        print("✓ Created annotation manager")
        
        # Create a simple test image
        image = np.ones((400, 600, 3), dtype=np.uint8) * 255
        cv2.putText(image, "Test Image", (200, 200), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Save to temp file
        temp_path = tempfile.mktemp(suffix='.jpg')
        cv2.imwrite(temp_path, image)
        print("✓ Created test image")
        
        # Create annotated image
        annotated_image = manager.create_annotated_image(temp_path)
        print(f"✓ Created annotated image with ID: {annotated_image.image_id}")
        
        # Add bounding box
        bbox = BoundingBoxAnnotation(
            label="Test Box",
            top_left=Point(100, 100),
            bottom_right=Point(300, 300),
            style=AnnotationStyle(stroke_color=Color(255, 0, 0))
        )
        manager.add_annotation(annotated_image.image_id, bbox)
        print("✓ Added bounding box annotation")
        
        # Add circle
        circle = CircleAnnotation(
            label="Test Circle",
            center=Point(450, 200),
            radius=50,
            style=AnnotationStyle(stroke_color=Color(0, 255, 0))
        )
        manager.add_annotation(annotated_image.image_id, circle)
        print("✓ Added circle annotation")
        
        # Add text
        text = TextAnnotation(
            position=Point(200, 350),
            text="Annotation Test",
            style=AnnotationStyle(stroke_color=Color(0, 0, 255))
        )
        manager.add_annotation(annotated_image.image_id, text)
        print("✓ Added text annotation")
        
        # Test annotation count
        assert len(annotated_image.annotations) == 3
        print(f"✓ Annotation count correct: {len(annotated_image.annotations)}")
        
        # Test render
        rendered = manager.render_image(annotated_image.image_id)
        assert rendered is not None
        print("✓ Successfully rendered image")
        
        # Test export
        json_export = manager.export_annotations(annotated_image.image_id, "json")
        assert json_export is not None
        print("✓ Successfully exported annotations")
        
        # Test undo
        initial_count = len(annotated_image.annotations)
        success = manager.undo(annotated_image.image_id)
        assert success and len(annotated_image.annotations) == initial_count - 1
        print("✓ Undo functionality works")
        
        # Test redo
        success = manager.redo(annotated_image.image_id)
        assert success and len(annotated_image.annotations) == initial_count
        print("✓ Redo functionality works")
        
        # Clean up
        os.unlink(temp_path)
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_functionality()