#!/usr/bin/env python3
"""
Quick verification script for multi-language implementation
Tests core functionality without requiring full setup
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test language detection
        import langdetect
        from langdetect import detect, detect_langs
        print("✅ langdetect imported successfully")
        
        # Test country/language info
        import pycountry
        print("✅ pycountry imported successfully")
        
        # Test spaCy
        import spacy
        print("✅ spaCy imported successfully")
        
        # Test our modules
        from language_support import (
            language_detector, multilingual_extractor, 
            get_supported_languages, get_language_name
        )
        print("✅ language_support module imported successfully")
        
        from multilingual_transcription import (
            multilingual_transcriber, multilingual_ui
        )
        print("✅ multilingual_transcription module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic multi-language functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from language_support import language_detector, get_supported_languages
        
        # Test language detection
        test_texts = [
            ("Hello, how are you?", "en"),
            ("Hola, ¿cómo estás?", "es"),
            ("Bonjour, comment allez-vous?", "fr")
        ]
        
        for text, expected in test_texts:
            result = language_detector.detect_language(text)
            print(f"Text: '{text[:30]}...'")
            print(f"  Expected: {expected}, Detected: {result.primary_language}")
            print(f"  Confidence: {result.confidence:.2%}")
        
        # Test supported languages
        languages = get_supported_languages()
        print(f"\n✅ {len(languages)} languages supported")
        
        # Show first 10 languages
        print("Sample supported languages:")
        for lang in languages[:10]:
            print(f"  {lang['code']}: {lang['name']} (NER: {'✅' if lang['has_ner'] else '❌'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spacy_models():
    """Test spaCy model availability"""
    print("\n📚 Testing spaCy models...")
    
    try:
        import spacy
        
        # Test English model (required)
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("Hello world")
            print(f"✅ English model working: {len(doc)} tokens")
        except OSError:
            print("❌ English model not found. Run: python -m spacy download en_core_web_sm")
            return False
        
        # Test other models (optional)
        optional_models = [
            ("es_core_news_sm", "Spanish"),
            ("fr_core_news_sm", "French"),
            ("de_core_news_sm", "German")
        ]
        
        for model, language in optional_models:
            try:
                nlp = spacy.load(model)
                print(f"✅ {language} model available")
            except OSError:
                print(f"⚠️ {language} model not available (optional)")
        
        return True
        
    except Exception as e:
        print(f"❌ spaCy model test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🌍 Multi-Language Implementation Verification")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Functionality Test", test_basic_functionality),
        ("spaCy Models Test", test_spacy_models)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed!")
        print("\n🚀 Multi-language support is ready to use!")
        print("\nTo use multi-language features:")
        print("1. Run: streamlit run app.py")
        print("2. Select '🌍 Multi-Language' mode")
        print("3. Upload audio/video and enjoy 50+ language support!")
    else:
        print(f"⚠️ {total - passed} test(s) failed.")
        print("\nTo fix issues:")
        print("1. Run setup script: ./setup_multilingual.sh")
        print("2. Install missing dependencies")
        print("3. Download required spaCy models")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)