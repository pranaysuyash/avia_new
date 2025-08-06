#!/usr/bin/env python3
"""
Test script for Image-Text Integration System
"""

import os
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from image_text_integration import (
    ImageTextIntegrationPipeline,
    CrossModalRecommendationEngine,
    MediaContent
)

def create_test_image_with_text():
    """Create a test image with text"""
    # Create image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Financial Report 2024", fill='black', font=font)
    draw.text((50, 150), "Revenue: $1.2M", fill='black', font=font)
    draw.text((50, 200), "Growth: 25%", fill='black', font=font)
    draw.text((50, 250), "CEO: John Smith", fill='black', font=font)
    draw.text((50, 300), "Location: New York", fill='black', font=font)
    
    # Add some shapes
    draw.rectangle([50, 400, 300, 500], outline='blue', width=3)
    draw.text((60, 430), "Q1 Performance", fill='blue')
    
    # Save to temp file
    temp_path = tempfile.mktemp(suffix='.png')
    img.save(temp_path)
    
    return temp_path

def create_test_audio_transcript():
    """Simulate audio transcript"""
    transcript = """
    Welcome to our quarterly earnings call. I'm John Smith, CEO of TechCorp.
    This quarter we achieved record revenue of 1.2 million dollars, 
    representing a 25 percent growth year over year. Our operations in New York
    have been particularly successful. Looking ahead to Q2, we expect continued
    growth in the financial services sector.
    """
    return transcript.strip()

def test_basic_integration():
    """Test basic integration functionality"""
    print("Testing Image-Text Integration Pipeline...")
    
    try:
        # Initialize pipeline
        pipeline = ImageTextIntegrationPipeline()
        print("✓ Pipeline initialized")
        
        # Create test image
        image_path = create_test_image_with_text()
        print("✓ Created test image with text")
        
        # Process image
        result = pipeline.process_media_file(image_path, content_type='image')
        print(f"✓ Processed image file")
        
        # Check OCR results
        assert result.text_sources.get('ocr') is not None
        print(f"✓ OCR extracted text: {len(result.text_sources['ocr'])} characters")
        
        # Check entities
        assert len(result.entities) > 0
        print(f"✓ Extracted {sum(len(v) for v in result.entities.values())} entities")
        
        # Display some entities
        for entity_type, entities in result.entities.items():
            if entities:
                print(f"  - {entity_type}: {entities[:3]}")
        
        # Check keywords
        assert len(result.keywords) > 0
        print(f"✓ Extracted {len(result.keywords)} keywords: {result.keywords[:5]}")
        
        # Clean up
        os.unlink(image_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cross_modal_integration():
    """Test cross-modal content integration"""
    print("\nTesting Cross-Modal Integration...")
    
    try:
        # Initialize pipeline
        pipeline = ImageTextIntegrationPipeline()
        
        # Create and process image
        image_path = create_test_image_with_text()
        image_result = pipeline.process_media_file(image_path, content_type='image')
        print(f"✓ Processed image content")
        
        # Simulate audio content
        audio_content = MediaContent(
            content_type='audio',
            source_path='simulated_audio.mp3',
            transcript_text=create_test_audio_transcript()
        )
        
        # Extract entities from transcript
        audio_content.entities = pipeline._extract_entities(audio_content.transcript_text)
        audio_content.embeddings = pipeline.embedding_model.encode(audio_content.transcript_text)
        
        # Store audio content
        pipeline.media_contents[audio_content.content_id] = audio_content
        print(f"✓ Added simulated audio content")
        
        # Test search across media
        search_results = pipeline.search_across_media("financial revenue")
        assert len(search_results) > 0
        print(f"✓ Cross-modal search found {len(search_results)} results")
        
        # Test recommendations
        rec_engine = CrossModalRecommendationEngine(pipeline)
        recommendations = rec_engine.get_recommendations(
            image_result.content_id,
            cross_modal=True,
            top_k=3
        )
        print(f"✓ Generated {len(recommendations)} cross-modal recommendations")
        
        # Clean up
        os.unlink(image_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_search():
    """Test unified search functionality"""
    print("\nTesting Unified Search...")
    
    try:
        # Initialize pipeline
        pipeline = ImageTextIntegrationPipeline()
        
        # Add multiple content types
        content_items = [
            ("Financial Report Q1", "image"),
            ("Earnings Call Recording", "audio"),
            ("Technical Documentation", "document")
        ]
        
        for title, content_type in content_items:
            content = MediaContent(
                content_type=content_type,
                source_path=f"{title.lower().replace(' ', '_')}.{content_type}",
                ocr_text=f"This is {title} containing financial data and revenue information" if content_type != "audio" else None,
                transcript_text=f"Discussion about {title} with CEO John Smith" if content_type == "audio" else None
            )
            
            # Extract entities and embeddings
            all_text = pipeline._combine_text_sources(content)
            if all_text:
                content.entities = pipeline._extract_entities(all_text)
                content.embeddings = pipeline.embedding_model.encode(all_text)
                pipeline._index_content(content)
            
            pipeline.media_contents[content.content_id] = content
        
        print(f"✓ Added {len(content_items)} different content types")
        
        # Search across all content
        results = pipeline.search_across_media("financial revenue CEO")
        assert len(results) > 0
        print(f"✓ Unified search returned {len(results)} results")
        
        # Filter by media type
        image_results = pipeline.search_across_media("financial", media_types=["image"])
        print(f"✓ Filtered search (images only) returned {len(image_results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analytics():
    """Test analytics functionality"""
    print("\nTesting Analytics...")
    
    try:
        # Initialize pipeline with some content
        pipeline = ImageTextIntegrationPipeline()
        
        # Add various content
        for i in range(5):
            content = MediaContent(
                content_type=['image', 'audio', 'document'][i % 3],
                source_path=f"test_file_{i}.ext",
                ocr_text=f"Sample text {i}" if i % 3 != 1 else None,
                transcript_text=f"Sample transcript {i}" if i % 3 == 1 else None
            )
            content.entities = {'PERSON': [f'Person{i}'], 'ORG': [f'Org{i}']}
            pipeline.media_contents[content.content_id] = content
        
        # Get analytics
        analytics = pipeline.get_content_analytics()
        
        assert analytics['total_content'] == 5
        print(f"✓ Total content: {analytics['total_content']}")
        
        assert analytics['total_entities'] == 10  # 2 entities per content
        print(f"✓ Total entities: {analytics['total_entities']}")
        
        assert len(analytics['content_by_type']) > 0
        print(f"✓ Content types: {analytics['content_by_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Image-Text Integration System Tests")
    print("=" * 50)
    
    tests = [
        test_basic_integration,
        test_cross_modal_integration,
        test_unified_search,
        test_analytics
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")

if __name__ == "__main__":
    main()