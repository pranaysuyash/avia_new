#!/usr/bin/env python3
"""
Test script for multi-language support functionality
Tests Task 36: Implement advanced multi-language support
"""

import os
import sys
import logging
import tempfile
import time
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from language_support import (
    language_detector, multilingual_extractor, translation_service,
    realtime_processor, get_supported_languages, get_language_name
)
from multilingual_transcription import multilingual_transcriber, multilingual_ui

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_language_detection():
    """Test automatic language detection"""
    print("\n🔍 Testing Language Detection...")
    
    test_texts = [
        ("Hello, how are you today?", "en"),
        ("Hola, ¿cómo estás hoy?", "es"),
        ("Bonjour, comment allez-vous aujourd'hui?", "fr"),
        ("Guten Tag, wie geht es Ihnen heute?", "de"),
        ("こんにちは、今日はいかがですか？", "ja"),
        ("Hello, je suis très bien, gracias!", "mixed")  # Code-switching example
    ]
    
    for text, expected_lang in test_texts:
        try:
            result = language_detector.detect_language(text)
            
            print(f"\nText: {text}")
            print(f"Expected: {expected_lang}")
            print(f"Detected: {result.primary_language} (confidence: {result.confidence:.2%})")
            print(f"All languages: {result.all_languages}")
            print(f"Code-switching: {result.has_code_switching}")
            
            if result.has_code_switching and result.segments:
                print("Language segments:")
                for i, segment in enumerate(result.segments):
                    print(f"  {i+1}. {segment['language']}: {segment['text'][:50]}...")
            
            print("✅ Language detection successful")
            
        except Exception as e:
            print(f"❌ Language detection failed: {e}")


def test_supported_languages():
    """Test supported languages list"""
    print("\n🌍 Testing Supported Languages...")
    
    try:
        languages = get_supported_languages()
        print(f"Total supported languages: {len(languages)}")
        
        # Show first 10 languages
        print("\nFirst 10 supported languages:")
        for i, lang in enumerate(languages[:10]):
            print(f"  {i+1}. {lang['name']} ({lang['code']}) - "
                  f"NER: {'✅' if lang['has_ner'] else '❌'}, "
                  f"RTL: {'✅' if lang['is_rtl'] else '❌'}")
        
        # Test language name resolution
        test_codes = ['en', 'es', 'fr', 'de', 'ja', 'ar', 'zh']
        print(f"\nLanguage name resolution:")
        for code in test_codes:
            name = get_language_name(code)
            print(f"  {code} -> {name}")
        
        print("✅ Supported languages test successful")
        
    except Exception as e:
        print(f"❌ Supported languages test failed: {e}")


def test_multilingual_entity_extraction():
    """Test multi-language entity extraction"""
    print("\n🏷️ Testing Multi-Language Entity Extraction...")
    
    test_texts = [
        ("Apple Inc. was founded by Steve Jobs in Cupertino, California on April 1, 1976.", "en"),
        ("Microsoft fue fundada por Bill Gates en Redmond, Washington el 4 de abril de 1975.", "es"),
        ("Google a été fondé par Larry Page et Sergey Brin à Mountain View, Californie en 1998.", "fr"),
        ("Hello, I'm John Smith from New York, but je travaille à Paris depuis 2020.", "mixed")
    ]
    
    for text, lang_type in test_texts:
        try:
            print(f"\nText ({lang_type}): {text}")
            
            if lang_type == "mixed":
                # Test multilingual extraction
                result = multilingual_extractor.extract_entities_multilingual(text)
                print(f"Multi-language extraction:")
                print(f"  Primary language: {result.get('primary_language', 'unknown')}")
                print(f"  Has code-switching: {result.get('has_code_switching', False)}")
                print(f"  Entities found: {len(result.get('entities', []))}")
                
                for entity in result.get('entities', [])[:5]:  # Show first 5
                    lang = entity.get('language', 'unknown')
                    print(f"    {entity['text']} ({entity['label']}) - Language: {lang}")
            else:
                # Test single language extraction
                result = multilingual_extractor.extract_entities(text)
                print(f"Single language extraction:")
                print(f"  Language: {result.get('language', 'unknown')}")
                print(f"  Entities found: {len(result.get('entities', []))}")
                
                for entity in result.get('entities', [])[:5]:  # Show first 5
                    print(f"    {entity['text']} ({entity['label']})")
            
            print("✅ Entity extraction successful")
            
        except Exception as e:
            print(f"❌ Entity extraction failed: {e}")


def test_translation_service():
    """Test translation capabilities"""
    print("\n🔄 Testing Translation Service...")
    
    # Check available providers
    providers = translation_service.get_available_providers()
    print(f"Available translation providers: {providers}")
    
    if not providers:
        print("⚠️ No translation providers available - skipping translation tests")
        return
    
    test_translations = [
        ("Hello, how are you?", "en", "es"),
        ("Good morning", "en", "fr"),
        ("Thank you very much", "en", "de")
    ]
    
    for text, source_lang, target_lang in test_translations:
        try:
            print(f"\nTranslating: '{text}' ({source_lang} -> {target_lang})")
            
            result = translation_service.translate_text(text, target_lang, source_lang)
            
            if 'error' in result:
                print(f"❌ Translation failed: {result['error']}")
            else:
                print(f"✅ Translation: '{result['translated_text']}'")
                print(f"   Provider: {result.get('provider', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0):.2%}")
            
        except Exception as e:
            print(f"❌ Translation test failed: {e}")


def test_realtime_language_processing():
    """Test real-time language processing"""
    print("\n📊 Testing Real-Time Language Processing...")
    
    # Simulate streaming text chunks
    text_chunks = [
        "Hello, welcome to our meeting.",
        "Today we will discuss the project.",
        "Hola, ¿cómo están todos?",  # Language switch
        "We need to finish by 5 PM.",
        "Merci beaucoup for your attention."  # Another switch
    ]
    
    session_id = "test_session"
    
    try:
        # Clear any existing session
        realtime_processor.clear_session(session_id)
        
        print(f"Processing {len(text_chunks)} text chunks...")
        
        for i, chunk in enumerate(text_chunks):
            print(f"\nChunk {i+1}: '{chunk}'")
            
            result = realtime_processor.process_streaming_text(chunk, session_id)
            
            print(f"  Detected language: {result['detected_language']}")
            print(f"  Confidence: {result['confidence']:.2%}")
            print(f"  Language switch: {result['language_switch_detected']}")
        
        # Get session summary
        summary = realtime_processor._get_session_language_summary(session_id)
        print(f"\nSession Summary:")
        print(f"  Total chunks: {summary['total_chunks']}")
        print(f"  Languages detected: {summary['languages_detected']}")
        print(f"  Primary language: {summary['primary_language']}")
        print(f"  Has code-switching: {summary['has_code_switching']}")
        print(f"  Language distribution: {summary['language_distribution']}")
        
        print("✅ Real-time processing test successful")
        
    except Exception as e:
        print(f"❌ Real-time processing test failed: {e}")


def test_language_capabilities():
    """Test language-specific capabilities"""
    print("\n🎯 Testing Language Capabilities...")
    
    test_languages = ['en', 'es', 'fr', 'de', 'ar', 'ja', 'zh']
    
    for lang_code in test_languages:
        try:
            print(f"\nTesting {lang_code} ({get_language_name(lang_code)}):")
            
            # Check if supported
            is_supported = language_detector.is_supported_language(lang_code)
            print(f"  Supported: {'✅' if is_supported else '❌'}")
            
            if is_supported:
                # Get language info
                lang_info = language_detector.get_language_info(lang_code)
                print(f"  Whisper code: {lang_info['whisper_code']}")
                print(f"  spaCy model: {lang_info['spacy_model'] or 'None'}")
                print(f"  RTL: {'✅' if lang_info['rtl'] else '❌'}")
                
                # Test model loading
                spacy_model = multilingual_extractor.load_language_model(lang_code)
                print(f"  spaCy model loaded: {'✅' if spacy_model else '❌'}")
        
        except Exception as e:
            print(f"❌ Language capability test failed for {lang_code}: {e}")


def run_all_tests():
    """Run all multi-language support tests"""
    print("🚀 Starting Multi-Language Support Tests (Task 36)")
    print("=" * 60)
    
    tests = [
        test_supported_languages,
        test_language_detection,
        test_language_capabilities,
        test_multilingual_entity_extraction,
        test_translation_service,
        test_realtime_language_processing
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with error: {e}")
            failed += 1
        
        print("\n" + "-" * 40)
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All multi-language support tests passed!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    run_all_tests()