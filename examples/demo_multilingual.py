#!/usr/bin/env python3
"""
Demo script for Multi-Language Support
Shows language detection, code-switching, and multilingual entity extraction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from language_support import (
    language_detector, multilingual_extractor, 
    get_supported_languages, SUPPORTED_LANGUAGES
)
from ner_multilingual import extract_entities_multilingual

def demo_language_detection():
    """Demo automatic language detection"""
    print("=== Language Detection Demo ===")
    print()
    
    # Test texts in different languages
    test_texts = [
        ("Hello, this is a test in English.", "English"),
        ("Bonjour, ceci est un test en français.", "French"),
        ("Hola, esto es una prueba en español.", "Spanish"),
        ("こんにちは、これは日本語のテストです。", "Japanese"),
        ("مرحبا، هذا اختبار باللغة العربية.", "Arabic"),
        ("Привет, это тест на русском языке.", "Russian"),
        ("你好，这是中文测试。", "Chinese"),
    ]
    
    for text, expected_lang in test_texts:
        result = language_detector.detect_language(text)
        print(f"Text: {text}")
        print(f"Expected: {expected_lang}")
        print(f"Detected: {result.primary_language} (confidence: {result.confidence:.2f})")
        print(f"All languages: {result.all_languages[:3]}")  # Top 3
        print("-" * 50)

def demo_code_switching():
    """Demo code-switching detection"""
    print("\n=== Code-Switching Detection Demo ===")
    print()
    
    # Mixed language texts
    mixed_texts = [
        "Hello everyone, today we'll learn about machine learning. Bonjour à tous!",
        "The meeting is scheduled for tomorrow. La reunión está programada para mañana.",
        "これは example of code-switching です。Very interesting!",
        "Привет! How are you doing today? Todo bien?",
    ]
    
    for text in mixed_texts:
        result = language_detector.detect_language(text)
        print(f"Text: {text}")
        print(f"Primary language: {result.primary_language}")
        print(f"Has code-switching: {result.has_code_switching}")
        
        if result.has_code_switching and result.segments:
            print("Segments:")
            for seg in result.segments:
                print(f"  - [{seg['language']}] {seg['text']}")
        
        print("-" * 50)

def demo_multilingual_ner():
    """Demo multilingual entity extraction"""
    print("\n=== Multilingual Entity Extraction Demo ===")
    print()
    
    # Test texts with entities in different languages
    test_cases = [
        {
            'text': "Apple CEO Tim Cook announced the new iPhone in Cupertino.",
            'language': 'en'
        },
        {
            'text': "Le président Emmanuel Macron visitera Paris demain.",
            'language': 'fr'
        },
        {
            'text': "El presidente Pedro Sánchez se reunió con Angela Merkel en Madrid.",
            'language': 'es'
        },
        {
            'text': "Microsoft und Google haben neue Büros in Berlin eröffnet.",
            'language': 'de'
        },
        {
            'text': "東京でソニーとトヨタが新しい技術を発表しました。",
            'language': 'ja'
        }
    ]
    
    for case in test_cases:
        print(f"\nLanguage: {SUPPORTED_LANGUAGES[case['language']]['name']}")
        print(f"Text: {case['text']}")
        
        result = extract_entities_multilingual(
            case['text'], 
            language=case['language']
        )
        
        print(f"Entities found:")
        for entity_type, entities in result['entities'].items():
            if entities:
                print(f"  {entity_type}: {', '.join(entities)}")
        
        if result.get('model_used'):
            print(f"Model used: {result['model_used']}")
        else:
            print("Model used: regex fallback (no spaCy model available)")

def demo_supported_languages():
    """Show all supported languages"""
    print("\n=== Supported Languages ===")
    print()
    
    languages = get_supported_languages()
    print(f"Total supported languages: {len(languages)}")
    print()
    
    # Group by NER support
    with_ner = [lang for lang in languages if lang['has_ner']]
    without_ner = [lang for lang in languages if not lang['has_ner']]
    
    print(f"Languages with full NER support ({len(with_ner)}):")
    for lang in with_ner[:10]:  # Show first 10
        rtl_marker = " (RTL)" if lang['is_rtl'] else ""
        print(f"  • {lang['name']} ({lang['code']}){rtl_marker}")
    if len(with_ner) > 10:
        print(f"  ... and {len(with_ner) - 10} more")
    
    print(f"\nLanguages with basic support ({len(without_ner)}):")
    for lang in without_ner[:10]:  # Show first 10
        rtl_marker = " (RTL)" if lang['is_rtl'] else ""
        print(f"  • {lang['name']} ({lang['code']}){rtl_marker}")
    if len(without_ner) > 10:
        print(f"  ... and {len(without_ner) - 10} more")

def demo_complex_multilingual():
    """Demo complex multilingual text processing"""
    print("\n=== Complex Multilingual Processing Demo ===")
    print()
    
    # Complex text with multiple languages and entities
    complex_text = """
    Good morning! I'm John Smith from Microsoft. Bonjour à tous! 
    Je m'appelle Marie Dubois et je travaille chez Google à Paris.
    Mañana tenemos una reunión con el equipo de Amazon en Madrid a las 3:00 PM.
    Please contact us at info@example.com or call +1-555-123-4567.
    """
    
    print("Complex multilingual text:")
    print(complex_text)
    print()
    
    # Process with code-switching detection
    result = extract_entities_multilingual(
        complex_text,
        detect_code_switching=True
    )
    
    print("Analysis Results:")
    print(f"Primary language: {result.get('primary_language', 'unknown')}")
    print(f"Has code-switching: {result.get('has_code_switching', False)}")
    
    if result.get('language_distribution'):
        print("\nLanguage distribution:")
        for lang, percentage in result['language_distribution'].items():
            print(f"  • {lang}: {percentage:.1%}")
    
    print("\nExtracted entities:")
    for entity_type, entities in result['entities'].items():
        if entities:
            print(f"  {entity_type}: {', '.join(entities)}")
    
    if result.get('all_entities'):
        print("\nDetailed entity information:")
        for entity in result['all_entities'][:5]:  # Show first 5
            lang = entity.get('language', 'unknown')
            print(f"  • [{entity['label']}] {entity['text']} (lang: {lang})")

def main():
    """Run all demos"""
    print("🌐 Multi-Language Support Demo")
    print("=" * 60)
    
    # Run demos
    demo_language_detection()
    demo_code_switching()
    demo_multilingual_ner()
    demo_supported_languages()
    demo_complex_multilingual()
    
    print("\n✅ Multi-language demo completed!")
    print("\nNote: For full functionality, install language-specific spaCy models:")
    print("  python -m spacy download es_core_news_sm  # Spanish")
    print("  python -m spacy download fr_core_news_sm  # French")
    print("  python -m spacy download de_core_news_sm  # German")
    print("  ... and others as needed")

if __name__ == "__main__":
    main()