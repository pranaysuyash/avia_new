#!/usr/bin/env python3
"""
Demo script for Image-Text Workflow Integration
Shows the complete workflow from image to unified search
"""

import os
import tempfile
from PIL import Image, ImageDraw, ImageFont
from image_text_integration_lite import (
    ImageTextIntegrationPipelineLite,
    MediaContent
)

def create_sample_image(text_content: str, filename: str) -> str:
    """Create a sample image with text"""
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
    except:
        font = ImageFont.load_default()
    
    # Draw text
    y = 50
    for line in text_content.split('\n'):
        draw.text((50, y), line, fill='black', font=font)
        y += 40
    
    # Save
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    img.save(temp_path)
    return temp_path

def main():
    """Run the demo"""
    print("Image-Text Workflow Integration Demo")
    print("=" * 60)
    
    # Initialize pipeline
    print("\n1. Initializing pipeline...")
    pipeline = ImageTextIntegrationPipelineLite()
    
    # Create sample images with different content
    print("\n2. Creating sample content...")
    
    # Financial report image
    financial_img = create_sample_image(
        "Financial Report Q4 2024\n" +
        "Revenue: $2.5M (+25% YoY)\n" +
        "Profit Margin: 18%\n" +
        "CEO: Sarah Johnson\n" +
        "Location: San Francisco",
        "financial_report.png"
    )
    print("   ✓ Created financial report image")
    
    # Technical documentation image
    tech_img = create_sample_image(
        "API Documentation\n" +
        "Version: 2.5.0\n" +
        "Endpoints: /api/v2/users\n" +
        "Authentication: OAuth 2.0\n" +
        "Lead: Mike Chen",
        "tech_docs.png"
    )
    print("   ✓ Created technical documentation image")
    
    # Meeting notes image
    meeting_img = create_sample_image(
        "Meeting Notes - Product Launch\n" +
        "Date: December 15, 2024\n" +
        "Attendees: Sarah Johnson, Mike Chen\n" +
        "Budget: $500K\n" +
        "Timeline: Q1 2025",
        "meeting_notes.png"
    )
    print("   ✓ Created meeting notes image")
    
    # Simulate audio transcript
    audio_content = MediaContent(
        content_type='audio',
        source_path='quarterly_call.mp3',
        transcript_text=(
            "Welcome to our Q4 earnings call. I'm Sarah Johnson, CEO. "
            "This quarter we achieved record revenue of 2.5 million dollars. "
            "Our technical team led by Mike Chen has made significant progress on the API. "
            "Looking ahead to Q1 2025, we're planning a major product launch."
        )
    )
    
    # Process all content
    print("\n3. Processing content through pipeline...")
    
    # Process images
    financial_result = pipeline.process_media_file(financial_img, 'image')
    print(f"   ✓ Processed financial report ({financial_result.processing_time:.2f}s)")
    
    tech_result = pipeline.process_media_file(tech_img, 'image')
    print(f"   ✓ Processed tech documentation ({tech_result.processing_time:.2f}s)")
    
    meeting_result = pipeline.process_media_file(meeting_img, 'image')
    print(f"   ✓ Processed meeting notes ({meeting_result.processing_time:.2f}s)")
    
    # Add audio content
    audio_content.entities = pipeline._extract_entities(audio_content.transcript_text)
    audio_content.embeddings = pipeline.embedding_model.encode(audio_content.transcript_text)
    pipeline.media_contents[audio_content.content_id] = audio_content
    print("   ✓ Added audio transcript")
    
    # Display processing results
    print("\n4. Processing Results:")
    for result in [financial_result, tech_result, meeting_result]:
        print(f"\n   {result.original_path}:")
        print(f"   - Text extracted: {len(result.all_text)} characters")
        print(f"   - Entities found: {sum(len(v) for v in result.entities.values())}")
        print(f"   - Keywords: {result.keywords[:3]}")
    
    # Demonstrate unified search
    print("\n5. Unified Search Demo:")
    
    # Search for financial information
    print("\n   Searching for 'revenue financial'...")
    results = pipeline.search_across_media("revenue financial", top_k=3)
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"   {i+1}. {result['content_type']}: {result['source_path']}")
    
    # Search for people
    print("\n   Searching for 'Sarah Johnson CEO'...")
    results = pipeline.search_across_media("Sarah Johnson CEO", top_k=3)
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"   {i+1}. {result['content_type']}: {result['source_path']}")
    
    # Search across specific media types
    print("\n   Searching for 'Mike' in images only...")
    results = pipeline.search_across_media("Mike", media_types=['image'], top_k=3)
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"   {i+1}. {result['content_type']}: {result['source_path']}")
    
    # Show analytics
    print("\n6. Content Analytics:")
    analytics = pipeline.get_content_analytics()
    print(f"   Total content items: {analytics['total_content']}")
    print(f"   Content by type: {analytics['content_by_type']}")
    print(f"   Total entities extracted: {analytics['total_entities']}")
    print(f"   Text sources used: {analytics['text_sources']}")
    
    # Clean up
    print("\n7. Cleaning up...")
    for img_path in [financial_img, tech_img, meeting_img]:
        try:
            os.unlink(img_path)
        except:
            pass
    
    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("- Unified processing of images and audio")
    print("- OCR text extraction from images")
    print("- Entity extraction and keyword identification")
    print("- Cross-media search capabilities")
    print("- Content analytics and insights")

if __name__ == "__main__":
    main()