#!/usr/bin/env python3
"""
Minimal test for Image-Text Integration - tests core functionality without heavy dependencies
"""

import os
import sys
import tempfile
from PIL import Image, ImageDraw

# Test the core MediaContent and WorkflowResult classes
def test_data_structures():
    """Test basic data structures"""
    print("Testing Data Structures...")
    
    try:
        from image_text_integration_lite import MediaContent, WorkflowResult
        import numpy as np
        
        # Create MediaContent
        content = MediaContent(
            content_type="image",
            source_path="test.png",
            ocr_text="Sample OCR text",
            entities={"PERSON": ["John"], "ORG": ["TechCorp"]}
        )
        
        print(f"✓ Created MediaContent with ID: {content.content_id}")
        print(f"✓ Content type: {content.content_type}")
        print(f"✓ OCR text: {content.ocr_text}")
        print(f"✓ Entities: {content.entities}")
        
        # Create WorkflowResult
        result = WorkflowResult(
            content_id=content.content_id,
            original_path="test.png",
            content_type="image",
            all_text="Sample OCR text",
            text_sources={"ocr": "Sample OCR text"},
            entities=content.entities,
            keywords=["John", "TechCorp"],
            processing_time=1.5,
            processing_steps=["ocr_extraction", "entity_extraction"]
        )
        
        print(f"✓ Created WorkflowResult")
        print(f"✓ Keywords: {result.keywords}")
        print(f"✓ Processing steps: {result.processing_steps}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_text_combination():
    """Test text combination logic"""
    print("\nTesting Text Combination...")
    
    try:
        from image_text_integration_lite import MediaContent, ImageTextIntegrationPipelineLite as ImageTextIntegrationPipeline
        
        # Create media content with multiple text sources
        content = MediaContent(
            transcript_text="This is a transcript.",
            ocr_text="This is OCR text.",
            caption_text="This is a caption.",
            annotation_text="This is an annotation."
        )
        
        # Test combining text sources
        pipeline = ImageTextIntegrationPipeline()
        combined_text = pipeline._combine_text_sources(content)
        
        assert "transcript" in combined_text
        assert "OCR" in combined_text
        assert "caption" in combined_text
        assert "annotation" in combined_text
        
        print(f"✓ Combined text length: {len(combined_text)} characters")
        print(f"✓ Combined text preview: {combined_text[:100]}...")
        
        # Test getting text sources
        sources = pipeline._get_text_sources(content)
        assert len(sources) == 4
        print(f"✓ Text sources: {list(sources.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_entity_extraction():
    """Test entity extraction"""
    print("\nTesting Entity Extraction...")
    
    try:
        from image_text_integration_lite import ImageTextIntegrationPipelineLite as ImageTextIntegrationPipeline
        
        pipeline = ImageTextIntegrationPipeline()
        
        # Test text
        text = "John Smith is the CEO of TechCorp in New York. The company reported $1.2M in revenue."
        
        # Extract entities
        entities = pipeline._extract_entities(text)
        
        print(f"✓ Extracted entity types: {list(entities.keys())}")
        for entity_type, values in entities.items():
            if values:
                print(f"  - {entity_type}: {values}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_keyword_extraction():
    """Test keyword extraction"""
    print("\nTesting Keyword Extraction...")
    
    try:
        from image_text_integration_lite import ImageTextIntegrationPipelineLite as ImageTextIntegrationPipeline
        
        pipeline = ImageTextIntegrationPipeline()
        
        # Test text
        text = "TechCorp announced quarterly earnings. CEO John Smith reported strong growth in New York market."
        
        # Extract keywords
        keywords = pipeline._extract_keywords(text, max_keywords=5)
        
        print(f"✓ Extracted {len(keywords)} keywords: {keywords}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_file_type_detection():
    """Test file type detection"""
    print("\nTesting File Type Detection...")
    
    try:
        from image_text_integration_lite import ImageTextIntegrationPipelineLite as ImageTextIntegrationPipeline
        
        pipeline = ImageTextIntegrationPipeline()
        
        # Test various file types
        test_files = [
            ("image.jpg", "image"),
            ("document.pdf", "document"),
            ("audio.mp3", "audio"),
            ("video.mp4", "video"),
            ("unknown.xyz", "unknown")
        ]
        
        all_correct = True
        for filename, expected_type in test_files:
            detected_type = pipeline._detect_content_type(filename)
            if detected_type == expected_type:
                print(f"✓ {filename} -> {detected_type}")
            else:
                print(f"❌ {filename} -> {detected_type} (expected {expected_type})")
                all_correct = False
        
        return all_correct
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all minimal tests"""
    print("Image-Text Integration Minimal Tests")
    print("=" * 50)
    
    tests = [
        test_data_structures,
        test_text_combination,
        test_entity_extraction,
        test_keyword_extraction,
        test_file_type_detection
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All minimal tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())