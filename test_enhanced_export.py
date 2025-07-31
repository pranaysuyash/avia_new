#!/usr/bin/env python3
"""
Test script for enhanced export functionality
"""

from datetime import datetime
from export_enhanced import ExportManager, DocxExportError
from session_manager import TranscriptionResults


def test_export_manager():
    """Test the ExportManager functionality"""
    print("Testing Enhanced Export Functionality")
    print("=" * 50)
    
    # Create sample TranscriptionResults
    sample_results = TranscriptionResults(
        transcript="This is a sample transcript for testing export functionality. It contains multiple sentences to demonstrate the formatting capabilities.",
        entities={
            "PERSON": ["John Doe", "Jane Smith"],
            "ORGANIZATION": ["OpenAI", "Microsoft"],
            "LOCATION": ["New York", "California"]
        },
        summary="This is a test summary of the transcript content.",
        confidence=0.95,
        processing_time=12.5,
        model_used="whisper-large",
        language="en",
        word_count=20
    )
    
    # Initialize export manager
    export_manager = ExportManager()
    
    # Test available formats
    print(f"Available export formats: {export_manager.get_available_formats()}")
    print()
    
    # Test each format
    formats_to_test = ['text', 'json', 'markdown']
    
    # Add docx if available
    if export_manager.is_format_available('docx'):
        formats_to_test.append('docx')
        print("✅ DOCX export available")
    else:
        print("⚠️  DOCX export not available (python-docx not installed)")
    print()
    
    for format_type in formats_to_test:
        print(f"Testing {format_type.upper()} export...")
        try:
            export_result = export_manager.export_results(
                results=sample_results,
                format_type=format_type,
                filename="test_transcript",
                export_options={
                    'include_metadata': True,
                    'include_entities': True
                }
            )
            
            print(f"  ✅ Success! Generated {export_result['filename']}")
            print(f"  📄 MIME type: {export_result['mime_type']}")
            print(f"  📊 Content size: {len(export_result['content'])} {'bytes' if isinstance(export_result['content'], bytes) else 'characters'}")
            
            # Show preview for text formats
            if format_type in ['text', 'markdown'] and isinstance(export_result['content'], str):
                preview = export_result['content'][:200] + "..." if len(export_result['content']) > 200 else export_result['content']
                print(f"  👀 Preview: {preview}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()


def test_docx_specific_features():
    """Test DOCX-specific features if available"""
    print("Testing DOCX-Specific Features")
    print("=" * 50)
    
    try:
        export_manager = ExportManager()
        
        if not export_manager.is_format_available('docx'):
            print("⏭️  Skipping DOCX tests - python-docx not available")
            return
        
        # Create sample results with more complex content
        complex_results = TranscriptionResults(
            transcript="""Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data. 

Key concepts include:
- Supervised learning
- Unsupervised learning  
- Reinforcement learning

The field has grown rapidly in recent years due to advances in computing power and data availability.""",
            entities={
                "TECHNOLOGY": ["Machine Learning", "artificial intelligence", "algorithms"],
                "CONCEPT": ["Supervised learning", "Unsupervised learning", "Reinforcement learning"],
                "FACTOR": ["computing power", "data availability"]
            },
            summary="An introduction to machine learning covering key concepts and recent growth factors.",
            confidence=0.98,
            processing_time=8.2,
            model_used="whisper-large-v2",
            language="en",
            word_count=45
        )
        
        # Test DOCX export with custom options
        export_result = export_manager.export_results(
            results=complex_results,
            format_type='docx',
            filename="machine_learning_transcript",
            export_options={
                'include_metadata': True,
                'include_entities': True
            }
        )
        
        print(f"✅ DOCX export successful!")
        print(f"📄 Filename: {export_result['filename']}")
        print(f"📊 Document size: {len(export_result['content'])} bytes")
        print(f"🎯 MIME type: {export_result['mime_type']}")
        
        # Save to temp file for manual inspection
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.docx',
            prefix='test_export_'
        )
        temp_file.write(export_result['content'])
        temp_file.close()
        
        print(f"💾 Temporary file saved: {temp_file.name}")
        print("   You can open this file in Microsoft Word to verify formatting")
        
    except DocxExportError as e:
        print(f"⚠️  DOCX export error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")


def test_export_options():
    """Test various export options"""
    print("\nTesting Export Options")
    print("=" * 50)
    
    export_manager = ExportManager()
    
    sample_results = TranscriptionResults(
        transcript="Sample transcript content for options testing.",
        entities={"PERSON": ["Test User"]},
        summary="Test summary",
        confidence=0.90,
        processing_time=5.0,
        model_used="test-model",
        language="en",
        word_count=8
    )
    
    # Test with different option combinations
    test_cases = [
        {'include_metadata': True, 'include_entities': True},
        {'include_metadata': False, 'include_entities': True},
        {'include_metadata': True, 'include_entities': False},
        {'include_metadata': False, 'include_entities': False}
    ]
    
    for i, options in enumerate(test_cases, 1):
        print(f"Test case {i}: {options}")
        
        try:
            export_result = export_manager.export_results(
                results=sample_results,
                format_type='text',
                filename=f"test_case_{i}",
                export_options=options
            )
            
            content_length = len(export_result['content'])
            print(f"  ✅ Export successful - {content_length} characters")
            
            # Check if metadata is included
            has_metadata = "METADATA" in export_result['content']
            has_entities = "ENTITIES" in export_result['content']
            
            print(f"  📊 Contains metadata: {has_metadata} (expected: {options['include_metadata']})")
            print(f"  🏷️  Contains entities: {has_entities} (expected: {options['include_entities']})")
            
            # Validate expectations
            if has_metadata == options['include_metadata'] and has_entities == options['include_entities']:
                print("  ✅ Options working correctly")
            else:
                print("  ⚠️  Options not working as expected")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()


if __name__ == "__main__":
    try:
        test_export_manager()
        test_docx_specific_features()
        test_export_options()
        
        print("🎉 All export tests completed!")
        print("\nNOTE: To enable Word (.docx) export, install python-docx:")
        print("pip install python-docx")
        
    except Exception as e:
        print(f"💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()