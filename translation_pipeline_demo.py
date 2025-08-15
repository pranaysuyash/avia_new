#!/usr/bin/env python3
"""
Translation Pipeline Demo with Mock Translations
Demonstrates the comprehensive translation pipeline functionality
"""

import asyncio
from comprehensive_translation_pipeline import (
    ComprehensiveTranslationPipeline,
    TranslationRequest,
    TranslationProvider,
    QualityLevel
)


async def demo_translation_pipeline():
    """Demo the translation pipeline with mock translations."""
    
    # Initialize pipeline (will use mock translations)
    pipeline = ComprehensiveTranslationPipeline()
    
    # Override the transformers translator to use mock
    pipeline.transformers_translator = None  # Force fallback to mock
    
    print("🌍 Translation Pipeline Demo (Mock Translations)")
    print("=" * 55)
    
    # Test basic translations
    basic_texts = [
        "hello",
        "goodbye", 
        "thank you",
        "yes",
        "no"
    ]
    
    target_languages = ['es', 'fr', 'de']
    
    print("\n🎯 Basic Translation Tests:")
    for target_lang in target_languages:
        print(f"\n📍 Translating to {target_lang.upper()}:")
        
        for text in basic_texts:
            request = TranslationRequest(
                text=text,
                source_language='en',
                target_language=target_lang,
                use_translation_memory=True
            )
            
            result = await pipeline.translate(request)
            print(f"  {text} → {result.translated_text} (quality: {result.quality_score:.3f})")
    
    # Test advanced features
    print(f"\n🔧 Advanced Features Test:")
    
    # Cultural adaptation test
    business_text = "We will have a meeting at 3:00 PM on 12/25/2024. The budget is $10,000.50."
    
    request = TranslationRequest(
        text=business_text,
        source_language='en',
        target_language='de',
        cultural_adaptation=True,
        use_translation_memory=True
    )
    
    result = await pipeline.translate(request)
    
    print(f"\nOriginal: {business_text}")
    print(f"Translated: {result.translated_text}")
    print(f"Quality Score: {result.quality_score:.3f}")
    print(f"Confidence: {result.confidence_score:.3f}")
    print(f"Processing Time: {result.processing_time:.3f}s")
    
    if result.cultural_adaptations:
        print(f"Cultural Adaptations Applied:")
        for adaptation in result.cultural_adaptations:
            print(f"  - {adaptation}")
    
    # Back-translation test
    print(f"\n🔄 Back-Translation Validation Test:")
    
    request.enable_back_translation = True
    result = await pipeline.translate(request)
    
    print(f"Original: {request.text}")
    print(f"Forward Translation: {result.translated_text}")
    if result.back_translation:
        print(f"Back Translation: {result.back_translation}")
        print(f"Back-Translation Score: {result.back_translation_score:.3f}")
    
    # Batch translation test
    print(f"\n🚀 Batch Translation Test:")
    
    batch_texts = [
        "Hello world",
        "Good morning",
        "How are you?",
        "See you later",
        "Thank you very much"
    ]
    
    batch_results = await pipeline.batch_translate(
        batch_texts, 
        'en', 
        'es',
        use_translation_memory=True,
        cultural_adaptation=True
    )
    
    print("English → Spanish:")
    for i, result in enumerate(batch_results):
        print(f"  {i+1}. {batch_texts[i]} → {result.translated_text}")
    
    # Translation memory test
    print(f"\n💾 Translation Memory Test:")
    
    # Translate the same text twice to test memory
    repeated_text = "hello"
    
    print("First translation (should be fresh):")
    request1 = TranslationRequest(
        text=repeated_text,
        source_language='en',
        target_language='es',
        use_translation_memory=True
    )
    result1 = await pipeline.translate(request1)
    print(f"  {repeated_text} → {result1.translated_text}")
    print(f"  Source: {result1.metadata.get('source', 'fresh_translation')}")
    print(f"  Processing time: {result1.processing_time:.4f}s")
    
    print("\nSecond translation (should use memory):")
    result2 = await pipeline.translate(request1)  # Same request
    print(f"  {repeated_text} → {result2.translated_text}")
    print(f"  Source: {result2.metadata.get('source', 'fresh_translation')}")
    print(f"  Processing time: {result2.processing_time:.4f}s")
    
    # Language detection test
    print(f"\n🔍 Language Detection Test:")
    
    detection_tests = [
        "Hello, how are you today?",  # English
        "Hola, ¿cómo estás hoy?",    # Spanish  
        "Bonjour, comment allez-vous aujourd'hui?",  # French
        "Hallo, wie geht es dir heute?"  # German
    ]
    
    for text in detection_tests:
        detected_lang, confidence = pipeline.language_detector.detect_language(text)
        print(f"  '{text[:30]}...' → {detected_lang} ({confidence:.3f})")
    
    # Quality assessment breakdown
    print(f"\n📊 Quality Assessment Breakdown:")
    
    test_text = "The quick brown fox jumps over the lazy dog."
    request = TranslationRequest(
        text=test_text,
        source_language='en',
        target_language='es'
    )
    
    result = await pipeline.translate(request)
    
    print(f"Original: {test_text}")
    print(f"Translation: {result.translated_text}")
    print(f"\nQuality Metrics:")
    
    if result.metadata and 'quality_breakdown' in result.metadata:
        quality_breakdown = result.metadata['quality_breakdown']
        for metric, score in quality_breakdown.items():
            print(f"  {metric.replace('_', ' ').title()}: {score:.3f}")
    
    # Statistics summary
    print(f"\n📈 Pipeline Statistics Summary:")
    stats = pipeline.get_pipeline_statistics()
    
    print(f"Total Translations: {stats.get('total_translations', 0)}")
    
    if 'top_language_pairs' in stats:
        print("Top Language Pairs:")
        for pair in stats['top_language_pairs'][:5]:
            print(f"  {pair[0]} → {pair[1]}: {pair[2]} translations")
    
    if 'quality_stats' in stats:
        quality = stats['quality_stats']
        print(f"Quality Statistics:")
        print(f"  Average: {quality.get('average', 0):.3f}")
        print(f"  Range: {quality.get('minimum', 0):.3f} - {quality.get('maximum', 0):.3f}")
    
    if 'performance_stats' in stats:
        perf = stats['performance_stats']
        print(f"Performance Statistics:")
        print(f"  Average Processing Time: {perf.get('average_time', 0):.4f}s")
        print(f"  Fastest: {perf.get('fastest', 0):.4f}s")
        print(f"  Slowest: {perf.get('slowest', 0):.4f}s")
    
    if 'translation_memory' in stats:
        tm_stats = stats['translation_memory']
        print(f"Translation Memory:")
        print(f"  Total Stored: {tm_stats.get('total_translations', 0)}")
    
    print(f"\n✅ Translation pipeline demo completed successfully!")
    

if __name__ == "__main__":
    asyncio.run(demo_translation_pipeline())