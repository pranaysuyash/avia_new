#!/usr/bin/env python3
"""
Test script to verify all API endpoints are properly configured
"""

import requests
import json
from typing import Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

# Test authentication token (you'll need to replace this with a valid token)
AUTH_TOKEN = "your-auth-token-here"

# Headers with authentication
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, description: str = ""):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing: {description or endpoint}")
    print(f"Method: {method}")
    print(f"URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        else:
            print(f"Unknown method: {method}")
            return
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code < 300:
            print("✓ Success")
            if response.text:
                try:
                    print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")
                except:
                    print(f"Response: {response.text[:200]}...")
        else:
            print("✗ Failed")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")


def main():
    """Test all API endpoints"""
    print("API Endpoint Testing")
    print("=" * 60)
    
    # 1. Test TTS endpoints
    print("\n\n### TEXT-TO-SPEECH ENDPOINTS ###")
    
    test_endpoint("GET", "/tts/voices", description="List available TTS voices")
    test_endpoint("GET", "/tts/languages", description="List supported languages")
    test_endpoint("POST", "/tts/synthesize", 
                  data={
                      "text": "Hello, this is a test.",
                      "voice": "default",
                      "language": "en"
                  },
                  description="Synthesize speech from text")
    
    # 2. Test Audio Enhancement endpoints
    print("\n\n### AUDIO ENHANCEMENT ENDPOINTS ###")
    
    test_endpoint("GET", "/audio/presets", description="Get audio enhancement presets")
    test_endpoint("POST", "/audio/enhance",
                  data={
                      "audio_data": "base64_audio_data_here",
                      "enhancement_options": {
                          "noise_reduction": True,
                          "normalize": True
                      }
                  },
                  description="Enhance audio")
    
    # 3. Test Collaboration endpoints
    print("\n\n### COLLABORATION ENDPOINTS ###")
    
    test_endpoint("GET", "/collaboration/comments/test-transcript-id", 
                  description="Get comments for transcript")
    test_endpoint("POST", "/collaboration/comments",
                  data={
                      "transcript_id": "test-transcript-id",
                      "text": "This is a test comment"
                  },
                  description="Create a comment")
    test_endpoint("GET", "/collaboration/annotations/test-transcript-id",
                  description="Get annotations for transcript")
    test_endpoint("POST", "/collaboration/sessions",
                  data={"transcript_id": "test-transcript-id"},
                  description="Create collaboration session")
    
    # 4. Test AI Customization endpoints
    print("\n\n### AI CUSTOMIZATION ENDPOINTS ###")
    
    test_endpoint("GET", "/ai/models/available", 
                  description="Get available AI models")
    test_endpoint("GET", "/ai/models/presets",
                  description="Get model configuration presets")
    test_endpoint("GET", "/ai/models/config",
                  description="List model configurations")
    test_endpoint("POST", "/ai/models/config",
                  data={
                      "name": "Test Model Config",
                      "description": "Test configuration",
                      "model_type": "transcription",
                      "base_model": "whisper-base",
                      "parameters": {
                          "language": "en",
                          "temperature": 0.7
                      }
                  },
                  description="Create model configuration")
    test_endpoint("GET", "/ai/prompts",
                  description="List custom prompts")
    test_endpoint("POST", "/ai/prompts",
                  data={
                      "name": "Test Prompt",
                      "prompt_type": "system",
                      "content": "You are a helpful assistant.",
                      "tags": ["test"]
                  },
                  description="Create custom prompt")
    
    # 5. Test other core endpoints
    print("\n\n### OTHER CORE ENDPOINTS ###")
    
    test_endpoint("GET", "/health", description="Health check")
    test_endpoint("GET", "/transcription/status", description="Transcription status")
    test_endpoint("GET", "/analytics/dashboard", description="Analytics dashboard")
    test_endpoint("GET", "/history/transcriptions", description="Transcription history")
    test_endpoint("GET", "/queue/status", description="Queue status")
    test_endpoint("GET", "/settings/user", description="User settings")
    
    print("\n\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()