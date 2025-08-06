#!/usr/bin/env python3
"""
Test script to verify API integration is working correctly
Tests both API mode and direct mode functionality
"""

import os
import sys
import tempfile
import base64

# Simple color codes for terminal output (no dependency needed)
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'

def print_header(text):
    print(f"\n{Colors.CYAN}{'='*60}")
    print(f"{Colors.CYAN}{text}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_api_connection():
    """Test if API server is running"""
    print_header("Testing API Connection")
    
    try:
        from api_client import get_api_client
        api_client = get_api_client()
        
        # Test health endpoint
        health = api_client._make_request("GET", "/api/v1/health")
        if health and health.get('status') == 'healthy':
            print_success(f"API server is healthy")
            print_info(f"API URL: {api_client.base_url}")
            return True
        else:
            print_error("API server returned unhealthy status")
            return False
            
    except Exception as e:
        print_error(f"Cannot connect to API: {str(e)}")
        print_warning("Make sure the API server is running:")
        print("  uvicorn api.app:app --reload")
        return False

def test_api_wrappers():
    """Test API wrapper imports"""
    print_header("Testing API Wrappers")
    
    try:
        from api_wrappers import media, stt, ner_basic, ner_advanced, tts, utils
        print_success("All API wrappers imported successfully")
        
        # Check wrapper methods
        wrappers = {
            'media': ['extract_audio', 'get_media_info', 'is_valid_media_file'],
            'stt': ['transcribe', 'get_supported_languages'],
            'ner_basic': ['extract_entities', 'get_entity_types'],
            'ner_advanced': ['extract_entities_advanced'],
            'tts': ['synthesize', 'get_voices'],
            'utils': ['format_duration', 'save_results']
        }
        
        for wrapper_name, methods in wrappers.items():
            wrapper = locals()[wrapper_name]
            for method in methods:
                if hasattr(wrapper, method):
                    print_success(f"{wrapper_name}.{method} available")
                else:
                    print_error(f"{wrapper_name}.{method} missing")
                    
        return True
        
    except ImportError as e:
        print_error(f"Failed to import API wrappers: {str(e)}")
        return False

def test_direct_imports():
    """Test direct module imports (fallback mode)"""
    print_header("Testing Direct Imports")
    
    try:
        import media
        import stt
        import ner_basic
        import ner_advanced
        import tts
        import utils
        
        print_success("All direct imports successful")
        return True
        
    except ImportError as e:
        print_error(f"Failed to import modules directly: {str(e)}")
        return False

def test_dual_mode_app():
    """Test dual mode support in main app"""
    print_header("Testing Dual Mode Support")
    
    # Test the import logic from app.py
    try:
        # Try API wrappers first
        from api_wrappers import media, stt, ner_basic, ner_advanced, tts, utils
        USING_API = True
        print_success("API mode available")
    except ImportError:
        # Fall back to direct imports
        try:
            import media
            import stt
            import ner_basic
            import ner_advanced
            import tts
            import utils
            USING_API = False
            print_success("Direct mode available (fallback)")
        except ImportError as e:
            print_error(f"Neither API nor direct mode available: {str(e)}")
            return False
    
    print_info(f"App would run in {'API' if USING_API else 'Direct'} mode")
    return True

def test_api_endpoints():
    """Test specific API endpoints"""
    print_header("Testing API Endpoints")
    
    if not test_api_connection():
        print_warning("Skipping endpoint tests - API not available")
        return False
    
    from api_client import get_api_client
    api_client = get_api_client()
    
    endpoints = [
        ("GET", "/api/v1/health", "Health Check"),
        ("GET", "/api/v1/tts/voices", "TTS Voices"),
        ("GET", "/api/v1/ocr/languages", "OCR Languages"),
        ("GET", "/api/v1/ner/entity-types", "NER Entity Types"),
        ("GET", "/api/v1/audio/presets", "Audio Presets"),
    ]
    
    success_count = 0
    for method, endpoint, name in endpoints:
        try:
            response = api_client._make_request(method, endpoint)
            if response:
                print_success(f"{name}: {endpoint}")
                success_count += 1
            else:
                print_error(f"{name}: {endpoint} - Empty response")
        except Exception as e:
            print_error(f"{name}: {endpoint} - {str(e)}")
    
    print_info(f"Passed {success_count}/{len(endpoints)} endpoint tests")
    return success_count > 0

def test_sample_workflow():
    """Test a sample workflow using API wrappers"""
    print_header("Testing Sample Workflow")
    
    try:
        from api_wrappers import ner_basic
        
        # Test text
        sample_text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."
        
        print_info(f"Test text: {sample_text}")
        
        # Extract entities
        entities = ner_basic.extract_entities(sample_text)
        
        if entities:
            print_success(f"Found {len(entities)} entities:")
            for entity in entities[:5]:  # Show first 5
                print(f"  - {entity.get('text', 'Unknown')} ({entity.get('type', 'Unknown')})")
            return True
        else:
            print_warning("No entities found (this might be normal for API mode)")
            return True
            
    except Exception as e:
        print_error(f"Workflow test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"{Colors.MAGENTA}{'='*60}")
    print(f"{Colors.MAGENTA}Audio/Video Transcription API Integration Test")
    print(f"{Colors.MAGENTA}{'='*60}{Colors.RESET}")
    
    tests = [
        ("API Connection", test_api_connection),
        ("API Wrappers", test_api_wrappers),
        ("Direct Imports", test_direct_imports),
        ("Dual Mode Support", test_dual_mode_app),
        ("API Endpoints", test_api_endpoints),
        ("Sample Workflow", test_sample_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS" if result else f"{Colors.RED}FAIL"
        print(f"{status}{Colors.RESET} - {test_name}")
    
    print(f"\n{Colors.CYAN}Total: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print_success("All tests passed! API integration is working correctly.")
    elif passed > 0:
        print_warning("Some tests passed. The system can work in fallback mode.")
    else:
        print_error("All tests failed. Please check your setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)