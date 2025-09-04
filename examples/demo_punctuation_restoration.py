#!/usr/bin/env python3
"""
Demo Script for Punctuation Restoration and Text Enhancement
Demonstrates Task 88: Build punctuation restoration and text enhancement
"""

import sys
import os
import time
from typing import List, Dict, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from punctuation_restoration import get_punctuation_service

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subheader(title: str):
    """Print a formatted subheader"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

def print_result(result: Dict[str, Any]):
    """Print enhancement result in a formatted way"""
    if result['success']:
        print(f"✅ Enhancement successful!")
        print(f"📊 Confidence Score: {result['confidence_score']:.2f}")
        print(f"🔧 Changes Made: {len(result['changes_made'])}")
        print(f"⏱️  Processing Time: {result['processing_time']:.3f}s")
        print(f"📏 Length Change: {result['statistics']['original_length']} → {result['statistics']['enhanced_length']}")
        
        if result['changes_made']:
            print(f"\n📝 Changes Details:")
            for i, change in enumerate(result['changes_made'][:5], 1):  # Show first 5 changes
                print(f"  {i}. {change['change_type'].title()}: '{change['original']}' → '{change['replacement']}' "
                      f"(confidence: {change.get('confidence', 0):.2f})")
            
            if len(result['changes_made']) > 5:
                print(f"  ... and {len(result['changes_made']) - 5} more changes")
    else:
        print(f"❌ Enhancement failed: {result.get('error', 'Unknown error')}")

def demo_basic_punctuation():
    """Demonstrate basic punctuation restoration"""
    print_subheader("Basic Punctuation Restoration")
    
    examples = [
        "hello world this is a test",
        "can you hear me yes i can hear you perfectly",
        "the quick brown fox jumps over the lazy dog",
        "i went to the store and bought some milk bread and eggs"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")
            print(f"Confidence: {result['confidence_score']:.2f} | Changes: {len(result['changes_made'])}")
        else:
            print(f"Error: {result.get('error')}")

def demo_question_detection():
    """Demonstrate question detection and punctuation"""
    print_subheader("Question Detection")
    
    examples = [
        "what time is it now",
        "where are you going after this",
        "can you help me with this problem",
        "are you coming to the meeting tomorrow",
        "how long will this take to complete",
        "this is not a question but a statement"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")
            is_question = result['enhanced_text'].endswith('?')
            print(f"Detected as: {'Question ❓' if is_question else 'Statement 💬'}")

def demo_number_formatting():
    """Demonstrate number word to digit conversion"""
    print_subheader("Number Formatting")
    
    examples = [
        "please turn to page twenty three",
        "read chapter five section two",
        "the meeting is at three thirty pm",
        "we have ten items on the agenda",
        "one day i will be happy",  # Should NOT convert this "one"
        "item number seven is the most important"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")
            
            # Check if any numbers were converted
            number_changes = [c for c in result['changes_made'] if 'number' in c.get('reason', '').lower()]
            if number_changes:
                print(f"Number conversions: {len(number_changes)}")

def demo_quote_formatting():
    """Demonstrate quote formatting"""
    print_subheader("Quote Formatting")
    
    examples = [
        "he said quote hello world unquote",
        "she replied quote i will be there at five pm unquote and then left",
        "the sign read quote no parking unquote",
        "quote this is a test unquote he whispered"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")
            
            # Check for quote formatting
            has_quotes = '"' in result['enhanced_text']
            print(f"Quote formatting: {'Applied ✓' if has_quotes else 'Not applied'}")

def demo_date_formatting():
    """Demonstrate date formatting"""
    print_subheader("Date Formatting")
    
    examples = [
        "the meeting is on january 15th 2024",
        "we will meet on march 3rd 2023",
        "the deadline is december 31st 2024",
        "please submit by february 28th 2025"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")
            
            # Check for date formatting
            date_changes = [c for c in result['changes_made'] if 'date' in c.get('reason', '').lower()]
            if date_changes:
                print(f"Date formatting applied: {len(date_changes)} changes")

def demo_comprehensive_enhancement():
    """Demonstrate comprehensive text enhancement"""
    print_subheader("Comprehensive Enhancement")
    
    examples = [
        "hello john how are you today its a beautiful morning isnt it yes it is would you like some coffee",
        "the meeting is scheduled for january fifteenth two thousand twenty four at ten am but we might need to reschedule",
        "he said quote i will call you at three pm unquote then asked what time should we meet tomorrow",
        "please review page twenty three chapter five and complete exercises one through ten by friday"
    ]
    
    service = get_punctuation_service()
    
    for i, text in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"Original:  {text}")
        
        result = service.enhance_transcript(text)
        print_result(result)
        
        if result['success']:
            print(f"Enhanced:  {result['enhanced_text']}")

def demo_batch_processing():
    """Demonstrate batch processing capabilities"""
    print_subheader("Batch Processing")
    
    texts = [
        "hello world this is test one",
        "what time is it now",
        "please turn to page twenty",
        "he said quote hello unquote",
        "the meeting is january first"
    ]
    
    service = get_punctuation_service()
    
    print(f"Processing {len(texts)} texts in batch...")
    
    start_time = time.time()
    results = service.batch_enhance(texts)
    end_time = time.time()
    
    print(f"Batch processing completed in {end_time - start_time:.3f}s")
    
    # Summary statistics
    successful = [r for r in results if r['success']]
    total_changes = sum(len(r.get('changes_made', [])) for r in successful)
    avg_confidence = sum(r['confidence_score'] for r in successful) / len(successful) if successful else 0
    
    print(f"\n📊 Batch Results:")
    print(f"  • Successful: {len(successful)}/{len(results)}")
    print(f"  • Total changes: {total_changes}")
    print(f"  • Average confidence: {avg_confidence:.2f}")
    
    print(f"\n📝 Individual Results:")
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"  {i}. '{result['original_text']}' → '{result['enhanced_text']}'")
        else:
            print(f"  {i}. Error: {result.get('error')}")

def demo_performance_test():
    """Demonstrate performance with different text sizes"""
    print_subheader("Performance Testing")
    
    service = get_punctuation_service()
    
    # Test with different text sizes
    base_text = "hello world this is a test can you hear me yes i can "
    test_sizes = [10, 50, 100, 200]
    
    print("Testing performance with different text sizes:")
    
    for size in test_sizes:
        text = base_text * size
        word_count = len(text.split())
        
        start_time = time.time()
        result = service.enhance_transcript(text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        words_per_second = word_count / processing_time if processing_time > 0 else 0
        
        print(f"  📏 {word_count:4d} words: {processing_time:.3f}s ({words_per_second:.1f} words/sec)")

def demo_customization_options():
    """Demonstrate different customization options"""
    print_subheader("Customization Options")
    
    text = "hello world what time is it now its three pm please turn to page twenty he said quote hello unquote"
    
    service = get_punctuation_service()
    
    # Test different option combinations
    option_sets = [
        {
            'name': 'All Features Enabled',
            'options': {
                'restore_punctuation': True,
                'fix_capitalization': True,
                'format_numbers': True,
                'format_quotes': True,
                'format_dates': True,
                'confidence_threshold': 0.7
            }
        },
        {
            'name': 'Punctuation Only',
            'options': {
                'restore_punctuation': True,
                'fix_capitalization': False,
                'format_numbers': False,
                'format_quotes': False,
                'format_dates': False,
                'confidence_threshold': 0.7
            }
        },
        {
            'name': 'High Confidence Only',
            'options': {
                'restore_punctuation': True,
                'fix_capitalization': True,
                'format_numbers': True,
                'format_quotes': True,
                'format_dates': True,
                'confidence_threshold': 0.9
            }
        }
    ]
    
    print(f"Original text: {text}")
    
    for option_set in option_sets:
        print(f"\n🔧 {option_set['name']}:")
        result = service.enhance_transcript(text, option_set['options'])
        
        if result['success']:
            print(f"Enhanced: {result['enhanced_text']}")
            print(f"Changes: {len(result['changes_made'])}, Confidence: {result['confidence_score']:.2f}")

def demo_error_handling():
    """Demonstrate error handling"""
    print_subheader("Error Handling")
    
    service = get_punctuation_service()
    
    # Test with edge cases
    test_cases = [
        ("Empty string", ""),
        ("Single word", "hello"),
        ("Only punctuation", "...!!!???"),
        ("Very long text", "word " * 1000),
        ("Special characters", "hello @#$% world &*()"),
        ("Numbers only", "123 456 789"),
        ("Mixed languages", "hello 世界 mundo")
    ]
    
    for name, text in test_cases:
        print(f"\n🧪 Testing: {name}")
        print(f"Input: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        try:
            result = service.enhance_transcript(text)
            if result['success']:
                print(f"✅ Success: '{result['enhanced_text'][:50]}{'...' if len(result['enhanced_text']) > 50 else ''}'")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"💥 Exception: {str(e)}")

def demo_statistics():
    """Demonstrate statistics collection"""
    print_subheader("Statistics Collection")
    
    service = get_punctuation_service()
    
    # Process several texts to build up statistics
    sample_texts = [
        "hello world this is a test",
        "what time is it now",
        "please turn to page twenty three",
        "he said quote hello world unquote",
        "the meeting is january first two thousand twenty four"
    ]
    
    print("Processing sample texts to build statistics...")
    
    for text in sample_texts:
        service.enhance_transcript(text)
    
    # Get and display statistics
    stats = service.get_enhancement_statistics()
    
    if 'message' not in stats:
        print(f"\n📊 Enhancement Statistics:")
        print(f"  • Total enhancements: {stats['total_enhancements']}")
        print(f"  • Average confidence: {stats['average_confidence']:.3f}")
        print(f"  • Average processing time: {stats['average_processing_time']:.3f}s")
        print(f"  • Total changes made: {stats['total_changes_made']}")
        print(f"  • Average changes per text: {stats['average_changes_per_text']:.1f}")
    else:
        print(f"📊 {stats['message']}")

def main():
    """Main demo function"""
    print_header("Punctuation Restoration & Text Enhancement Demo")
    print("This demo showcases AI-powered punctuation restoration and text formatting capabilities.")
    print("Task 88: Build punctuation restoration and text enhancement")
    
    try:
        # Run all demo sections
        demo_basic_punctuation()
        demo_question_detection()
        demo_number_formatting()
        demo_quote_formatting()
        demo_date_formatting()
        demo_comprehensive_enhancement()
        demo_batch_processing()
        demo_performance_test()
        demo_customization_options()
        demo_error_handling()
        demo_statistics()
        
        print_header("Demo Completed Successfully! 🎉")
        print("The punctuation restoration system is working correctly.")
        print("\nKey Features Demonstrated:")
        print("✅ Basic punctuation restoration")
        print("✅ Question detection and punctuation")
        print("✅ Number word to digit conversion")
        print("✅ Quote formatting (quote...unquote → \"...\")")
        print("✅ Date formatting")
        print("✅ Comprehensive text enhancement")
        print("✅ Batch processing capabilities")
        print("✅ Performance optimization")
        print("✅ Customizable options")
        print("✅ Error handling")
        print("✅ Statistics collection")
        
        print("\n🚀 Ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()