#!/usr/bin/env python3
"""
Debug script to isolate MediaIngestionController import issues
"""

import sys
import traceback

print("=== Testing MediaIngestionController Import ===")

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import os
    import io
    import logging
    import tempfile
    import hashlib
    import mimetypes
    print("✅ Standard library imports successful")
except Exception as e:
    print(f"❌ Standard library import failed: {e}")
    sys.exit(1)

# Test 2: Third-party imports
print("\n2. Testing third-party imports...")
try:
    import ffmpeg
    import magic
    from PIL import Image
    import fitz
    import aiofiles
    print("✅ Third-party imports successful")
except Exception as e:
    print(f"❌ Third-party import failed: {e}")
    traceback.print_exc()

# Test 3: Local module imports
print("\n3. Testing local module imports...")
try:
    from media import validate_media_file, get_media_info
    print("✅ media module imports successful")
except Exception as e:
    print(f"❌ media module import failed: {e}")
    traceback.print_exc()

try:
    from errors import MediaProcessingError, FileProcessingError, ErrorCode
    print("✅ errors module imports successful")
except Exception as e:
    print(f"❌ errors module import failed: {e}")
    traceback.print_exc()

# Test 4: Try to import the controller module step by step
print("\n4. Testing MediaIngestionController module...")
try:
    import media_ingestion_controller
    print("✅ media_ingestion_controller module imported")
    
    # Check what's actually in the module
    attrs = [attr for attr in dir(media_ingestion_controller) if not attr.startswith('_')]
    print(f"Available attributes: {attrs}")
    
    if hasattr(media_ingestion_controller, 'MediaIngestionController'):
        print("✅ MediaIngestionController class found")
        controller = media_ingestion_controller.MediaIngestionController()
        print("✅ MediaIngestionController instantiated")
    else:
        print("❌ MediaIngestionController class not found")
        
except Exception as e:
    print(f"❌ MediaIngestionController import/instantiation failed: {e}")
    traceback.print_exc()

print("\n=== Debug Complete ===")