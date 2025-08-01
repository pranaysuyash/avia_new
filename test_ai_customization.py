#!/usr/bin/env python3
"""
Test script for AI Model Customization functionality
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import customization components
from ai_model_customization import (
    AIModelCustomization, CustomVocabulary, VoiceProfile, 
    CustomEntityType, ModelConfiguration,
    create_custom_vocabulary, create_voice_profile, 
    create_custom_entity_type
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_custom_vocabulary():
    """Test custom vocabulary creation and usage"""
    print("\n🧪 Testing Custom Vocabulary...")
    
    try:
        # Create a medical vocabulary
        medical_terms = [
            "cardiomyopathy",
            "myocardial infarction", 
            "atherosclerosis",
            "hypertension",
            "bradycardia"
        ]
        
        replacements = {
            "cardio mixopathy": "cardiomyopathy",
            "heart attack": "myocardial infarction"
        }
        
        vocabulary = create_custom_vocabulary(
            name="Medical Terms",
            domain="medical",
            terms=medical_terms,
            replacements=replacements
        )
        
        print(f"✅ Created vocabulary: {vocabulary.name}")
        print(f"   Domain: {vocabulary.domain}")
        print(f"   Terms: {len(vocabulary.terms)}")
        print(f"   Replacements: {len(vocabulary.replacements)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom vocabulary test failed: {e}")
        return False

def test_voice_profile():
    """Test voice profile creation"""
    print("\n🧪 Testing Voice Profile...")
    
    try:
        # Create mock audio segments
        audio_segments = [
            {
                'file_name': 'sample1.wav',
                'duration': 12.5,
                'confidence': 0.85,
                'text': 'This is a sample audio segment for testing',
                'features': {'pitch': 120, 'tone': 'neutral'}
            },
            {
                'file_name': 'sample2.wav', 
                'duration': 8.3,
                'confidence': 0.90,
                'text': 'Another sample with different characteristics',
                'features': {'pitch': 125, 'tone': 'professional'}
            }
        ]
        
        profile = create_voice_profile(
            name="John Doe - CEO",
            audio_segments=audio_segments
        )
        
        print(f"✅ Created voice profile: {profile.name}")
        print(f"   Profile ID: {profile.profile_id}")
        print(f"   Sample segments: {len(profile.sample_segments)}")
        print(f"   Features: {list(profile.speaker_features.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice profile test failed: {e}")
        return False

def test_custom_entity_type():
    """Test custom entity type creation"""
    print("\n🧪 Testing Custom Entity Type...")
    
    try:
        # Create a stock symbol entity type
        patterns = [
            r'[A-Z]{3,5}',  # 3-5 letter stock symbols
            r'\$[A-Z]{3,5}',  # Symbols with $ prefix
        ]
        
        examples = [
            "AAPL", "GOOGL", "TSLA", "AMZN", "MSFT"
        ]
        
        context_clues = [
            "stock", "ticker", "symbol", "shares", "trading"
        ]
        
        entity_type = create_custom_entity_type(
            name="Stock Symbol",
            category="financial",
            patterns=patterns,
            examples=examples
        )
        
        print(f"✅ Created entity type: {entity_type.name}")
        print(f"   Category: {entity_type.category}")
        print(f"   Patterns: {len(entity_type.patterns)}")
        print(f"   Examples: {len(entity_type.examples)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom entity type test failed: {e}")
        return False

def test_full_integration():
    """Test full AI customization integration"""
    print("\n🧪 Testing Full Integration...")
    
    try:
        # Initialize AI customization system
        customization = AIModelCustomization()
        
        # Get statistics
        stats = customization.get_customization_stats()
        
        print(f"✅ System initialized successfully")
        print(f"   Vocabularies: {stats['vocabularies']['total']}")
        print(f"   Voice profiles: {stats['voice_profiles']['total']}")
        print(f"   Entity types: {stats['entity_types']['total']}")
        print(f"   Status: {stats['system_status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting AI Model Customization Tests")
    print("=" * 50)
    
    tests = [
        ("Custom Vocabulary", test_custom_vocabulary),
        ("Voice Profile", test_voice_profile), 
        ("Custom Entity Type", test_custom_entity_type),
        ("Full Integration", test_full_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! AI Model Customization is ready!")
    else:
        print(f"\n⚠️ {failed} tests failed. Please check the implementation.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)