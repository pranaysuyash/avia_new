#!/usr/bin/env python3
"""
Advanced Multilingual System Demo
Demonstrates multilingual processing, code-switching detection, and cultural analysis.
"""

import asyncio
from advanced_multilingual_system import AdvancedMultilingualSystem

async def main():
    """Run the advanced multilingual system demo."""
    await demo_multilingual_analysis()

async def demo_multilingual_analysis():
    """Demonstrate the multilingual analysis capabilities."""
    system = AdvancedMultilingualSystem()
    
    print("🌍 Advanced Multilingual System Demo")
    print("=" * 50)
    
    # Test cases with different code-switching patterns
    test_cases = [
        # English-Spanish code-switching
        "I went to the store pero no había nada que me gustara.",
        
        # Spanish-English professional context
        "La reunión es mañana at 3 PM in the conference room.",
        
        # French-English casual conversation
        "C'est vraiment cool, you know what I mean?",
        
        # Multi-language tourist context
        "Excuse me, ¿dónde está la biblioteca? Je cherche la bibliothèque.",
        
        # German-English academic
        "The concept of Gemeinschaft und Gesellschaft is fundamental to sociology.",
        
        # Spanish regional variations
        "¡Órale! That's so cool, hermano. Está padrísimo este lugar.",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Text: {text}")
        print("-" * 40)
        
        # Analyze text
        analysis = await system.analyze_text(text)
        
        # Display results
        print(f"Primary Language: {analysis.primary_language.value}")
        print(f"Detected Languages: {[lang.value for lang in analysis.detected_languages]}")
        print(f"Complexity Score: {analysis.complexity_score:.3f}")
        print(f"Code-Switch Events: {len(analysis.code_switch_events)}")
        
        # Show language segments
        if analysis.language_segments:
            print("Language Segments:")
            for segment in analysis.language_segments:
                dialect_info = f" ({segment.dialect.value})" if segment.dialect else ""
                print(f"  [{segment.language.value}{dialect_info}] '{segment.text}' (conf: {segment.confidence:.3f})")
        
        # Show code-switching events
        if analysis.code_switch_events:
            print("Code-Switch Events:")
            for event in analysis.code_switch_events:
                print(f"  {event.from_language.value} → {event.to_language.value} "
                      f"({event.switch_type.value}, {event.trigger_type})")
        
        # Show cultural markers
        if analysis.cultural_markers:
            print(f"Cultural Markers: {analysis.cultural_markers}")
    
    # System statistics
    print(f"\n📊 System Statistics:")
    stats = system.get_system_statistics()
    print(f"Total Analyses: {stats.get('database_statistics', {}).get('total_analyses', 0)}")
    print(f"Supported Languages: {stats.get('supported_languages', 0)}")
    print(f"System Status: {stats.get('system_status', 'unknown')}")
    
    print(f"\n✅ Advanced multilingual analysis demo completed!")

if __name__ == "__main__":
    asyncio.run(main())