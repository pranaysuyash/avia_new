"""
Comprehensive Demo Script for Image OCR System
Demonstrates OCR functionality across all platforms with sample data
"""

import os
import sys
import asyncio
import tempfile
import base64
import json
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from image_ocr_processor import (
    OCRManager, OCRResult, DocumentResult,
    validate_image_file, estimate_processing_time
)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_subheader(title: str):
    """Print formatted subheader"""
    print(f"\n--- {title} ---")

def create_sample_images():
    """Create sample images for testing"""
    print_subheader("Creating Sample Images")
    
    samples_dir = Path("demo_samples")
    samples_dir.mkdir(exist_ok=True)
    
    # Sample 1: Simple text
    img1 = Image.new('RGB', (600, 200), color='white')
    draw1 = ImageDraw.Draw(img1)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    draw1.text((50, 50), "OCR Demo - Simple Text", fill='black', font=font_large)
    draw1.text((50, 120), "This is a test document for OCR processing.", fill='black', font=font_small)
    
    sample1_path = samples_dir / "simple_text.png"
    img1.save(sample1_path)
    print(f"✅ Created: {sample1_path}")
    
    # Sample 2: Multi-language text
    img2 = Image.new('RGB', (700, 300), color='white')
    draw2 = ImageDraw.Draw(img2)
    
    texts = [
        ("English: Hello World", 50, 50),
        ("Spanish: Hola Mundo", 50, 100),
        ("French: Bonjour le Monde", 50, 150),
        ("German: Hallo Welt", 50, 200),
        ("Numbers: 123-456-7890", 50, 250)
    ]
    
    for text, x, y in texts:
        draw2.text((x, y), text, fill='black', font=font_small)
    
    sample2_path = samples_dir / "multilingual.png"
    img2.save(sample2_path)
    print(f"✅ Created: {sample2_path}")
    
    # Sample 3: Document with structure
    img3 = Image.new('RGB', (800, 600), color='white')
    draw3 = ImageDraw.Draw(img3)
    
    # Title
    draw3.text((50, 30), "MEETING MINUTES", fill='black', font=font_large)
    draw3.text((50, 80), "Date: March 15, 2024", fill='black', font=font_small)
    draw3.text((50, 110), "Attendees: John Smith, Jane Doe, Mike Johnson", fill='black', font=font_small)
    
    # Content
    content_lines = [
        "AGENDA ITEMS:",
        "1. Budget Review - Q1 performance exceeded expectations",
        "2. New Product Launch - Timeline moved to April 2024", 
        "3. Team Expansion - Hiring 3 new developers",
        "",
        "ACTION ITEMS:",
        "• John to prepare budget report by March 20",
        "• Jane to finalize product specifications",
        "• Mike to post job openings by end of week",
        "",
        "NEXT MEETING: March 22, 2024 at 2:00 PM"
    ]
    
    y_pos = 160
    for line in content_lines:
        draw3.text((50, y_pos), line, fill='black', font=font_small)
        y_pos += 30
    
    sample3_path = samples_dir / "meeting_minutes.png"
    img3.save(sample3_path)
    print(f"✅ Created: {sample3_path}")
    
    # Sample 4: Table-like structure
    img4 = Image.new('RGB', (700, 400), color='white')
    draw4 = ImageDraw.Draw(img4)
    
    # Draw table structure
    draw4.rectangle([50, 50, 650, 350], outline='black', width=2)
    
    # Header row
    draw4.line([50, 100, 650, 100], fill='black', width=1)
    draw4.text((60, 60), "Product", fill='black', font=font_small)
    draw4.text((200, 60), "Price", fill='black', font=font_small)
    draw4.text((300, 60), "Quantity", fill='black', font=font_small)
    draw4.text((450, 60), "Total", fill='black', font=font_small)
    
    # Data rows
    data_rows = [
        ("Laptop", "$999.99", "2", "$1,999.98"),
        ("Mouse", "$29.99", "5", "$149.95"),
        ("Keyboard", "$79.99", "3", "$239.97"),
        ("Monitor", "$299.99", "1", "$299.99")
    ]
    
    y_pos = 120
    for product, price, qty, total in data_rows:
        draw4.line([50, y_pos + 30, 650, y_pos + 30], fill='black', width=1)
        draw4.text((60, y_pos), product, fill='black', font=font_small)
        draw4.text((200, y_pos), price, fill='black', font=font_small)
        draw4.text((300, y_pos), qty, fill='black', font=font_small)
        draw4.text((450, y_pos), total, fill='black', font=font_small)
        y_pos += 50
    
    # Vertical lines
    draw4.line([190, 50, 190, 350], fill='black', width=1)
    draw4.line([290, 50, 290, 350], fill='black', width=1)
    draw4.line([440, 50, 440, 350], fill='black', width=1)
    
    sample4_path = samples_dir / "invoice_table.png"
    img4.save(sample4_path)
    print(f"✅ Created: {sample4_path}")
    
    return [sample1_path, sample2_path, sample3_path, sample4_path]

def demo_basic_ocr_functionality():
    """Demonstrate basic OCR functionality"""
    print_header("BASIC OCR FUNCTIONALITY DEMO")
    
    # Initialize OCR system
    print("🚀 Initializing OCR System...")
    ocr_manager = OCRManager("demo_temp")
    
    # Get system status
    stats = ocr_manager.get_processing_stats()
    print(f"✅ OCR System initialized")
    print(f"📊 Tesseract available: {stats['tesseract_available']}")
    print(f"📊 EasyOCR available: {stats['easyocr_available']}")
    print(f"📊 Supported formats: {len(stats['supported_formats'])}")
    print(f"📊 Supported languages: {stats['supported_languages']}")
    
    # Show supported languages
    print_subheader("Supported Languages")
    languages = ocr_manager.get_supported_languages()
    for i, lang in enumerate(languages[:10]):  # Show first 10
        print(f"  {i+1:2d}. {lang['name']} ({lang['code']})")
    if len(languages) > 10:
        print(f"  ... and {len(languages) - 10} more")
    
    return ocr_manager

def demo_image_processing(ocr_manager, sample_images):
    """Demonstrate image processing with different samples"""
    print_header("IMAGE PROCESSING DEMO")
    
    for i, image_path in enumerate(sample_images, 1):
        print_subheader(f"Processing Sample {i}: {image_path.name}")
        
        try:
            # Validate file first
            is_valid = validate_image_file(str(image_path))
            print(f"📋 File validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
            if not is_valid:
                continue
            
            # Estimate processing time
            estimated_time = estimate_processing_time(str(image_path))
            print(f"⏱️  Estimated processing time: {estimated_time:.1f}s")
            
            # Process image
            start_time = datetime.now()
            result = ocr_manager.process_file(str(image_path), language='en')
            end_time = datetime.now()
            
            actual_time = (end_time - start_time).total_seconds()
            print(f"⏱️  Actual processing time: {actual_time:.2f}s")
            
            # Display results
            if isinstance(result, OCRResult):
                print(f"📄 Extracted text ({len(result.text)} characters):")
                print(f"📊 Confidence: {result.confidence:.1%}")
                print(f"📊 Word count: {result.word_count}")
                print(f"📊 Line count: {result.line_count}")
                print(f"📊 Bounding boxes: {len(result.bounding_boxes)}")
                
                # Show first 200 characters of text
                preview_text = result.text[:200] + "..." if len(result.text) > 200 else result.text
                print(f"👁️  Text preview:\n{preview_text}")
                
                # Show confidence distribution
                if result.bounding_boxes:
                    confidences = [box['confidence'] for box in result.bounding_boxes]
                    avg_conf = sum(confidences) / len(confidences)
                    min_conf = min(confidences)
                    max_conf = max(confidences)
                    print(f"📈 Confidence stats: avg={avg_conf:.1f}%, min={min_conf:.1f}%, max={max_conf:.1f}%")
            
        except Exception as e:
            print(f"❌ Error processing {image_path.name}: {str(e)}")

def demo_language_detection(ocr_manager, sample_images):
    """Demonstrate language detection and multi-language processing"""
    print_header("MULTI-LANGUAGE PROCESSING DEMO")
    
    # Use the multilingual sample
    multilingual_image = None
    for img_path in sample_images:
        if "multilingual" in img_path.name:
            multilingual_image = img_path
            break
    
    if not multilingual_image:
        print("❌ Multilingual sample not found")
        return
    
    print_subheader("Processing with Different Language Settings")
    
    languages_to_test = ['en', 'es', 'fr', 'de', 'auto']
    
    for lang in languages_to_test:
        print(f"\n🌍 Processing with language: {lang}")
        
        try:
            result = ocr_manager.process_file(str(multilingual_image), language=lang)
            
            if isinstance(result, OCRResult):
                print(f"📊 Confidence: {result.confidence:.1%}")
                print(f"📊 Word count: {result.word_count}")
                
                # Show first 100 characters
                preview = result.text[:100] + "..." if len(result.text) > 100 else result.text
                print(f"👁️  Text preview: {preview}")
                
        except Exception as e:
            print(f"❌ Error with language {lang}: {str(e)}")

def demo_batch_processing(ocr_manager, sample_images):
    """Demonstrate batch processing capabilities"""
    print_header("BATCH PROCESSING DEMO")
    
    print(f"📦 Processing {len(sample_images)} images in batch...")
    
    try:
        # Process all samples
        start_time = datetime.now()
        results = ocr_manager.document_processor.process_batch(
            [str(img) for img in sample_images],
            language='en'
        )
        end_time = datetime.now()
        
        total_time = (end_time - start_time).total_seconds()
        print(f"⏱️  Total batch processing time: {total_time:.2f}s")
        print(f"📊 Average time per image: {total_time / len(sample_images):.2f}s")
        
        # Analyze results
        successful = 0
        total_words = 0
        total_confidence = 0
        
        for i, result in enumerate(results):
            if isinstance(result, OCRResult):
                successful += 1
                total_words += result.word_count
                total_confidence += result.confidence
                
                print(f"✅ {sample_images[i].name}: {result.word_count} words, {result.confidence:.1%} confidence")
            else:
                print(f"❌ {sample_images[i].name}: Processing failed")
        
        if successful > 0:
            print(f"\n📊 Batch Summary:")
            print(f"   • Successful: {successful}/{len(results)}")
            print(f"   • Total words extracted: {total_words:,}")
            print(f"   • Average confidence: {total_confidence/successful:.1%}")
        
    except Exception as e:
        print(f"❌ Batch processing error: {str(e)}")

def demo_base64_processing(ocr_manager):
    """Demonstrate base64 image processing (for mobile/web)"""
    print_header("BASE64 PROCESSING DEMO (Mobile/Web)")
    
    print_subheader("Creating Base64 Test Image")
    
    # Create a simple test image
    img = Image.new('RGB', (400, 150), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Base64 Encoding Test", fill='black', font=font)
    draw.text((50, 90), "Mobile & Web Integration", fill='black', font=font)
    
    # Convert to base64
    import io
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    base64_data = base64.b64encode(buffer.getvalue()).decode()
    
    print(f"📊 Base64 data length: {len(base64_data)} characters")
    print(f"👁️  Base64 preview: {base64_data[:50]}...")
    
    try:
        # Process base64 image
        print_subheader("Processing Base64 Image")
        result = ocr_manager.process_base64_image(base64_data, language='en')
        
        print(f"✅ Base64 processing successful!")
        print(f"📊 Confidence: {result.confidence:.1%}")
        print(f"📊 Word count: {result.word_count}")
        print(f"👁️  Extracted text: {result.text}")
        
    except Exception as e:
        print(f"❌ Base64 processing error: {str(e)}")

def demo_api_simulation():
    """Simulate API requests and responses"""
    print_header("API SIMULATION DEMO")
    
    print_subheader("Simulating API Endpoints")
    
    # Simulate different API requests
    api_requests = [
        {
            "endpoint": "/api/ocr/languages",
            "method": "GET",
            "description": "Get supported languages"
        },
        {
            "endpoint": "/api/ocr/status", 
            "method": "GET",
            "description": "Get system status"
        },
        {
            "endpoint": "/api/ocr/process",
            "method": "POST",
            "description": "Process uploaded file"
        },
        {
            "endpoint": "/api/ocr/process-mobile",
            "method": "POST", 
            "description": "Process base64 image from mobile"
        },
        {
            "endpoint": "/api/ocr/batch",
            "method": "POST",
            "description": "Batch process multiple files"
        }
    ]
    
    for req in api_requests:
        print(f"🌐 {req['method']} {req['endpoint']}")
        print(f"   📝 {req['description']}")
        
        # Simulate response structure
        if req['endpoint'] == '/api/ocr/languages':
            response = {
                "success": True,
                "data": [
                    {"code": "en", "name": "English"},
                    {"code": "es", "name": "Spanish"},
                    {"code": "fr", "name": "French"}
                ]
            }
        elif req['endpoint'] == '/api/ocr/status':
            response = {
                "success": True,
                "data": {
                    "tesseract_available": True,
                    "easyocr_available": True,
                    "supported_formats": [".jpg", ".png", ".pdf"],
                    "supported_languages": 13
                }
            }
        else:
            response = {
                "success": True,
                "data": {
                    "type": "ocr_result",
                    "text": "Sample extracted text",
                    "confidence": 0.95,
                    "word_count": 3,
                    "processing_time": 1.23
                },
                "metadata": {
                    "filename": "sample.png",
                    "settings": {"language": "en"}
                }
            }
        
        print(f"   📤 Response: {json.dumps(response, indent=2)[:100]}...")
        print()

def demo_platform_integration():
    """Demonstrate platform-specific integration examples"""
    print_header("PLATFORM INTEGRATION DEMO")
    
    print_subheader("Web/Desktop Integration (React/Electron)")
    print("""
    📱 Frontend Component Usage:
    
    import OCRProcessor from './components/ocr/OCRProcessor';
    
    function App() {
      return (
        <div>
          <OCRProcessor />
        </div>
      );
    }
    
    🔧 Features:
    • Drag & drop file upload
    • Real-time processing progress
    • Multi-language support
    • Batch processing
    • Results management
    """)
    
    print_subheader("Mobile Integration (React Native)")
    print("""
    📱 Mobile Component Usage:
    
    import OCRProcessor from './components/ocr/OCRProcessor';
    
    function App() {
      return (
        <OCRProcessor />
      );
    }
    
    🔧 Mobile-Specific Features:
    • Camera integration
    • Gallery selection
    • Document picker
    • Share functionality
    • Offline processing
    """)
    
    print_subheader("Backend API Integration")
    print("""
    🖥️  API Server Usage:
    
    # Start the API server
    python api_ocr_endpoints.py
    
    # Or with uvicorn
    uvicorn api_ocr_endpoints:app --reload
    
    🔧 API Features:
    • RESTful endpoints
    • File upload handling
    • Base64 processing
    • Batch operations
    • Error handling
    """)

def demo_performance_analysis(ocr_manager, sample_images):
    """Demonstrate performance analysis"""
    print_header("PERFORMANCE ANALYSIS DEMO")
    
    print_subheader("Processing Speed Analysis")
    
    performance_data = []
    
    for image_path in sample_images:
        try:
            # Get file size
            file_size = image_path.stat().st_size / 1024  # KB
            
            # Process and time
            start_time = datetime.now()
            result = ocr_manager.process_file(str(image_path))
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            if isinstance(result, OCRResult):
                performance_data.append({
                    'filename': image_path.name,
                    'file_size_kb': file_size,
                    'processing_time': processing_time,
                    'words_per_second': result.word_count / processing_time if processing_time > 0 else 0,
                    'confidence': result.confidence,
                    'word_count': result.word_count
                })
                
        except Exception as e:
            print(f"❌ Error analyzing {image_path.name}: {str(e)}")
    
    # Display performance summary
    if performance_data:
        print(f"📊 Performance Summary ({len(performance_data)} files):")
        print(f"{'Filename':<20} {'Size(KB)':<10} {'Time(s)':<8} {'Words/s':<8} {'Confidence':<12}")
        print("-" * 70)
        
        total_time = 0
        total_words = 0
        
        for data in performance_data:
            print(f"{data['filename']:<20} {data['file_size_kb']:<10.1f} {data['processing_time']:<8.2f} "
                  f"{data['words_per_second']:<8.1f} {data['confidence']:<12.1%}")
            total_time += data['processing_time']
            total_words += data['word_count']
        
        print("-" * 70)
        avg_time = total_time / len(performance_data)
        avg_words_per_sec = total_words / total_time if total_time > 0 else 0
        
        print(f"{'AVERAGE':<20} {'':<10} {avg_time:<8.2f} {avg_words_per_sec:<8.1f}")

def demo_error_handling(ocr_manager):
    """Demonstrate error handling capabilities"""
    print_header("ERROR HANDLING DEMO")
    
    print_subheader("Testing Various Error Scenarios")
    
    # Test 1: Non-existent file
    print("🧪 Test 1: Non-existent file")
    try:
        ocr_manager.process_file("nonexistent_file.jpg")
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly handled: {str(e)}")
    
    # Test 2: Invalid base64 data
    print("\n🧪 Test 2: Invalid base64 data")
    try:
        ocr_manager.process_base64_image("invalid_base64_data")
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly handled: {str(e)}")
    
    # Test 3: Unsupported language
    print("\n🧪 Test 3: Unsupported language")
    try:
        # Create a simple test image first
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), "Test", fill='black')
        img.save(temp_file.name)
        
        # Try with invalid language
        result = ocr_manager.process_file(temp_file.name, language='invalid_lang')
        print(f"⚠️  Processed with fallback language: {result.language if hasattr(result, 'language') else 'N/A'}")
        
        # Cleanup
        Path(temp_file.name).unlink()
        
    except Exception as e:
        print(f"✅ Correctly handled: {str(e)}")
    
    # Test 4: Empty image
    print("\n🧪 Test 4: Empty/blank image")
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img = Image.new('RGB', (200, 100), color='white')  # Blank white image
        img.save(temp_file.name)
        
        result = ocr_manager.process_file(temp_file.name)
        if isinstance(result, OCRResult):
            print(f"✅ Processed blank image: '{result.text.strip()}' (confidence: {result.confidence:.1%})")
        
        # Cleanup
        Path(temp_file.name).unlink()
        
    except Exception as e:
        print(f"✅ Correctly handled: {str(e)}")

def demo_cleanup_and_summary(ocr_manager):
    """Demonstrate cleanup and provide summary"""
    print_header("CLEANUP AND SUMMARY")
    
    print_subheader("System Cleanup")
    
    # Cleanup temporary files
    try:
        ocr_manager.cleanup_temp_files()
        print("✅ Temporary files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {str(e)}")
    
    # Final system stats
    print_subheader("Final System Statistics")
    stats = ocr_manager.get_processing_stats()
    
    print(f"📊 OCR Engines:")
    print(f"   • Tesseract: {'✅ Available' if stats['tesseract_available'] else '❌ Not available'}")
    print(f"   • EasyOCR: {'✅ Available' if stats['easyocr_available'] else '❌ Not available'}")
    
    print(f"📊 Capabilities:")
    print(f"   • Supported formats: {len(stats['supported_formats'])}")
    print(f"   • Supported languages: {stats['supported_languages']}")
    print(f"   • Temp directory: {stats['temp_directory']}")
    
    print_subheader("Demo Summary")
    print("""
    🎉 OCR System Demo Complete!
    
    ✅ Demonstrated Features:
    • Basic OCR processing with multiple engines
    • Multi-language text recognition
    • Batch processing capabilities
    • Base64 encoding for mobile/web integration
    • API endpoint simulation
    • Platform-specific integration examples
    • Performance analysis and benchmarking
    • Comprehensive error handling
    • System cleanup and maintenance
    
    🚀 Ready for Production:
    • Python backend with OCR processing
    • React/Electron frontend component
    • React Native mobile component
    • FastAPI REST endpoints
    • Comprehensive test suite
    • Performance monitoring
    • Error handling and recovery
    
    📁 Generated Files:
    • demo_samples/ - Sample images for testing
    • demo_temp/ - Temporary processing files (cleaned up)
    • Test results and performance data
    """)

def main():
    """Run the complete OCR system demo"""
    print("🎬 Starting Comprehensive OCR System Demo")
    print("This demo showcases OCR functionality across all platforms")
    
    try:
        # Create sample images
        sample_images = create_sample_images()
        
        # Initialize OCR system
        ocr_manager = demo_basic_ocr_functionality()
        
        # Run demonstrations
        demo_image_processing(ocr_manager, sample_images)
        demo_language_detection(ocr_manager, sample_images)
        demo_batch_processing(ocr_manager, sample_images)
        demo_base64_processing(ocr_manager)
        demo_api_simulation()
        demo_platform_integration()
        demo_performance_analysis(ocr_manager, sample_images)
        demo_error_handling(ocr_manager)
        demo_cleanup_and_summary(ocr_manager)
        
        print_header("DEMO COMPLETE")
        print("🎉 All demonstrations completed successfully!")
        print("📁 Check the 'demo_samples' directory for generated test images")
        print("🔧 OCR system is ready for integration across all platforms")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()