#!/usr/bin/env python3
"""
Simple test script for Image-Text Integration
"""

import os
import tempfile
from PIL import Image, ImageDraw

from image_text_integration import ImageTextIntegrationPipeline

def test_basic_functionality():
    """Test basic pipeline functionality"""
    print("Testing Image-Text Integration Pipeline...")
    
    try:
        # Initialize pipeline
        pipeline = ImageTextIntegrationPipeline()
        print("✓ Pipeline initialized")
        
        # Create a simple test image
        img = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "Test Image", fill='black')
        draw.text((50, 100), "Financial Report", fill='black')
        draw.text((50, 150), "Revenue: $1M", fill='black')
        
        # Save to temp file
        temp_path = tempfile.mktemp(suffix='.png')
        img.save(temp_path)
        print("✓ Created test image")
        
        # Process image
        result = pipeline.process_media_file(temp_path, content_type='image')
        print(f"✓ Processed image in {result.processing_time:.2f}s")
        
        # Check results
        print(f"✓ Processing steps: {result.processing_steps}")
        print(f"✓ Text sources: {list(result.text_sources.keys())}")
        print(f"✓ Entity count: {sum(len(v) for v in result.entities.values())}")
        print(f"✓ Keywords: {result.keywords[:5]}")
        
        # Test search
        if pipeline.media_contents:
            search_results = pipeline.search_across_media("financial")
            print(f"✓ Search returned {len(search_results)} results")
        
        # Clean up
        os.unlink(temp_path)
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_basic_functionality()