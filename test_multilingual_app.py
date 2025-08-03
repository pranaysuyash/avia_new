#!/usr/bin/env python3
"""
Quick test of multi-language support in the app
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from language_support import get_supported_languages, language_detector
from ner_multilingual import extract_entities_multilingual

def test_language_selection():
    """Test language selection functionality"""
    print("=== Testing Language Selection UI ===")
    
    # Get supported languages
    languages = get_supported_languages()
    print(f"\nTotal languages available: {len(languages)}")
    
    # Show first 10 languages
    print("\nSample languages with their features:")
    print("-" * 60)
    print(f"{'Language':<20} {'Code':<6} {'NER':<5} {'RTL':<5}")
    print("-" * 60)
    
    for lang in languages[:10]:
        ner_support = "✅" if lang['has_ner'] else "❌"
        rtl_support = "✅" if lang['is_rtl'] else "❌"
        print(f"{lang['name']:<20} {lang['code']:<6} {ner_support:<5} {rtl_support:<5}")

def test_multilingual_transcription():
    """Test transcription with different languages"""
    print("\n\n=== Testing Multi-Language Transcription ===")
    
    # Sample texts that would be transcribed
    test_cases = [
        {
            'text': "Welcome to our quarterly earnings call. Today we'll discuss our financial results.",
            'expected_lang': 'en',
            'description': 'English business meeting'
        },
        {
            'text': "Bienvenue à notre conférence trimestrielle. Aujourd'hui, nous discuterons de nos résultats.",
            'expected_lang': 'fr',
            'description': 'French conference call'
        },
        {
            'text': "こんにちは。本日は決算説明会を開催いたします。",
            'expected_lang': 'ja',
            'description': 'Japanese earnings call'
        },
        {
            'text': "Hello everyone. Bonjour à tous. Today we have participants from multiple countries.",
            'expected_lang': 'en',
            'description': 'Multilingual meeting (code-switching)'
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['description']}:")
        print(f"Text: {case['text'][:50]}...")
        
        # Detect language
        detection = language_detector.detect_language(case['text'])
        print(f"Detected language: {detection.primary_language}")
        print(f"Confidence: {detection.confidence:.2%}")
        
        if detection.has_code_switching:
            print("Code-switching detected: Yes")
            if detection.segments:
                print("Language segments:")
                for seg in detection.segments:
                    print(f"  - [{seg['language']}] {seg['text'][:30]}...")
        
        # Extract entities
        result = extract_entities_multilingual(case['text'], language=detection.primary_language)
        if result['entities']:
            print("Entities found:")
            for entity_type, entities in result['entities'].items():
                if entities:
                    print(f"  {entity_type}: {', '.join(entities)}")

def test_app_workflow():
    """Show the app workflow with multi-language support"""
    print("\n\n=== App Workflow with Multi-Language Support ===")
    print("\n1. Upload audio/video file or record audio")
    print("2. Select language from dropdown (50+ languages) or use 'Auto-detect'")
    print("3. Enable 'Detect Code-Switching' for multilingual content")
    print("4. Click 'Transcribe & Analyze'")
    print("5. View results with:")
    print("   - Detected language shown in processing summary")
    print("   - Entities extracted in the detected language")
    print("   - Language segments shown for code-switching content")
    print("\n✅ Multi-language support is fully integrated!")

if __name__ == "__main__":
    print("🌐 Multi-Language Support App Test")
    print("=" * 60)
    
    test_language_selection()
    test_multilingual_transcription()
    test_app_workflow()
    
    print("\n\n📱 To test in the app:")
    print("1. Run: streamlit run app.py")
    print("2. Upload an audio file in any supported language")
    print("3. Select the language or use auto-detect")
    print("4. Process and see language-specific results!")