"""
Demo script for Media Ingestion Controller
"""

import asyncio
import tempfile
import os
from pathlib import Path

from media_ingestion_controller import MediaIngestionController, ProcessingOptions


async def demo_basic_functionality():
    """Basic demo of media ingestion controller"""
    print("🎬 Media Ingestion Controller Demo")
    print("=" * 50)
    
    controller = MediaIngestionController()
    
    # Create a simple text file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("This is a test document for media ingestion.")
        test_file = f.name
    
    try:
        filename = Path(test_file).name
        print(f"Testing with file: {filename}")
        
        # Test format detection
        format_info = await controller.detect_format(test_file, filename)
        print(f"Detected format: {format_info.file_type} ({format_info.mime_type})")
        
        # Test full ingestion
        options = ProcessingOptions(enable_preprocessing=True)
        result = await controller.ingest_media(test_file, filename, options)
        
        if result.success:
            print("✅ Ingestion successful!")
            print(f"Processing time: {result.processing_time:.2f}s")
            if result.operations_applied:
                print(f"Operations: {', '.join(result.operations_applied)}")
        else:
            print("❌ Ingestion failed")
            for error in result.errors:
                print(f"Error: {error}")
    
    finally:
        os.unlink(test_file)


if __name__ == "__main__":
    asyncio.run(demo_basic_functionality())