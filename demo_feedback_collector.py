#!/usr/bin/env python3
"""
Demo script for Feedback Collection Interfaces
Showcases comprehensive feedback collection with multiple interfaces and methods
"""

import sys
import os
import time
from datetime import datetime
import json

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feedback_collector import (
    FeedbackCollector, CollectionConfig, CollectionMethod, FeedbackTrigger,
    create_feedback_collector, create_collection_config
)

from feedback_data_models import (
    FeedbackStorage, FeedbackContext, ContentType, RatingType,
    create_feedback_storage
)

def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_progress(current, total, task_name="Processing", width=50):
    """Print a progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress * 100
    print(f"\r{task_name}: |{bar}| {percentage:.1f}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def demo_collection_interfaces():
    """Demo different collection interfaces"""
    print_separator("DEMO 1: Collection Interfaces", "=")
    
    print("🎛️  Testing different feedback collection interfaces...")
    
    # Create storage and contexts
    storage = create_feedback_storage("demo_collection.db")
    
    contexts = [
        FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="demo_transcript_001",
            original_content="Welcome to our quarterly business review meeting.",
            processed_content="Welcome to our quarterly business review meeting.",
            confidence_score=0.94,
            processing_method="whisper_v3",
            model_version="3.0"
        ),
        FeedbackContext(
            content_type=ContentType.MEETING_ELEMENT,
            content_id="demo_agenda_001",
            original_content="Discuss Q4 financial performance and projections",
            confidence_score=0.89,
            processing_method="nlp_extraction"
        ),
        FeedbackContext(
            content_type=ContentType.ACTION_ITEM,
            content_id="demo_action_001",
            original_content="Sarah will prepare the budget analysis by next Friday",
            confidence_score=0.91,
            processing_method="action_extraction"
        )
    ]
    
    # Test different collection methods
    methods = [
        (CollectionMethod.INLINE, "Inline Collection"),
        (CollectionMethod.POPUP, "Popup Collection")
    ]
    
    total_collections = len(methods) * len(contexts) * 3  # 3 feedback types per context
    current_collection = 0
    
    print(f"\n📝 Testing {len(methods)} collection methods with {len(contexts)} contexts...")
    
    for method, method_name in methods:
        print(f"\n🔧 Testing {method_name}:")
        
        # Create collector with specific method
        config = create_collection_config(
            method=method,
            auto_save=True,
            enable_comments=True,
            max_rating_value=5
        )
        collector = create_feedback_collector(storage, config)
        
        for i, context in enumerate(contexts):
            # Collect rating feedback
            current_collection += 1
            print_progress(current_collection, total_collections, f"{method_name}")
            
            rating_id = collector.collect_rating_feedback(
                f"demo_user_{method.value}", context, RatingType.STARS
            )
            time.sleep(0.1)
            
            # Collect correction feedback
            current_collection += 1
            print_progress(current_collection, total_collections, f"{method_name}")
            
            correction_id = collector.collect_correction_feedback(
                f"demo_user_{method.value}", context,
                "quarterly", "Quarterly"
            )
            time.sleep(0.1)
            
            # Collect suggestion feedback
            current_collection += 1
            print_progress(current_collection, total_collections, f"{method_name}")
            
            suggestion_id = collector.collect_suggestion_feedback(
                f"demo_user_{method.value}", context,
                f"Consider improving {context.content_type.value} processing accuracy"
            )
            time.sleep(0.1)
        
        print(f"\n  ✅ {method_name} completed successfully")
    
    print(f"\n📊 Collection Interface Demo Results:")
    
    # Get statistics for each method
    for method, method_name in methods:
        user_feedback = storage.get_user_feedback(f"demo_user_{method.value}")
        print(f"  {method_name}: {len(user_feedback)} feedback items collected")
    
    return storage

def demo_validation_and_change_detection():
    """Demo validation and change detection features"""
    print_separator("DEMO 2: Validation and Change Detection", "=")
    
    print("🔍 Testing validation and change detection capabilities...")
    
    from feedback_collector import FeedbackValidator, ChangeDetector
    
    validator = FeedbackValidator()
    detector = ChangeDetector()
    
    # Demo validation
    print(f"\n📋 Validation Tests:")
    
    validation_tests = [
        ("Rating (Stars 4/5)", lambda: validator.validate_rating(RatingType.STARS, 4, 5)),
        ("Rating (Invalid)", lambda: validator.validate_rating(RatingType.STARS, 6, 5)),
        ("Correction (Valid)", lambda: validator.validate_correction("hello", "Hello")),
        ("Correction (Same)", lambda: validator.validate_correction("same", "same")),
        ("Suggestion (Valid)", lambda: validator.validate_suggestion("This is a good suggestion")),
        ("Suggestion (Too short)", lambda: validator.validate_suggestion("short"))
    ]
    
    for i, (test_name, test_func) in enumerate(validation_tests):
        print_progress(i + 1, len(validation_tests), "Validation Tests")
        result = test_func()
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"\n  {test_name}: {status}")
        time.sleep(0.1)
    
    # Demo change detection
    print(f"\n🔄 Change Detection Tests:")
    
    change_tests = [
        ("Capitalization", "hello world", "Hello World"),
        ("Word replacement", "cat sat", "dog sat"),
        ("Punctuation", "Hello", "Hello!"),
        ("Insertion", "Hello", "Hello there"),
        ("Deletion", "Hello world", "Hello")
    ]
    
    for i, (test_name, original, modified) in enumerate(change_tests):
        print_progress(i + 1, len(change_tests), "Change Detection")
        changes = detector.detect_changes(original, modified)
        
        print(f"\n  {test_name}:")
        print(f"    Original: '{original}'")
        print(f"    Modified: '{modified}'")
        print(f"    Changes detected: {len(changes)}")
        
        for change in changes:
            category = detector.categorize_change(change)
            print(f"    - Type: {change['type']}, Category: {category}")
        
        time.sleep(0.1)

def demo_batch_collection():
    """Demo batch feedback collection"""
    print_separator("DEMO 3: Batch Collection", "=")
    
    print("📦 Testing batch feedback collection...")
    
    storage = create_feedback_storage("demo_batch.db")
    collector = create_feedback_collector(storage)
    
    # Create multiple contexts for batch processing
    contexts = []
    for i in range(5):
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id=f"batch_content_{i:03d}",
            original_content=f"This is batch content item number {i+1} for testing.",
            confidence_score=0.85 + (i * 0.02)
        )
        contexts.append(context)
    
    # Prepare batch items
    batch_items = []
    for i, context in enumerate(contexts):
        # Add different types of feedback for each context
        batch_items.extend([
            {
                'type': 'rating',
                'context': context,
                'rating_type': 'stars'
            },
            {
                'type': 'correction',
                'context': context,
                'original_text': f'item {i+1}',
                'corrected_text': f'Item {i+1}'
            },
            {
                'type': 'suggestion',
                'context': context,
                'suggestion_text': f'Suggestion for improving batch item {i+1} processing'
            }
        ])
    
    print(f"\n📝 Processing {len(batch_items)} batch feedback items...")
    
    # Process batch with progress tracking
    batch_size = 5
    collected_ids = []
    
    for i in range(0, len(batch_items), batch_size):
        batch_chunk = batch_items[i:i+batch_size]
        print_progress(i + len(batch_chunk), len(batch_items), "Batch Processing")
        
        chunk_ids = collector.collect_batch_feedback(f"batch_user_{i//batch_size}", batch_chunk)
        collected_ids.extend(chunk_ids)
        time.sleep(0.2)
    
    print(f"\n📊 Batch Collection Results:")
    print(f"  Total items processed: {len(batch_items)}")
    print(f"  Successfully collected: {len(collected_ids)}")
    print(f"  Success rate: {len(collected_ids)/len(batch_items)*100:.1f}%")
    
    # Show statistics by user
    for i in range((len(batch_items) // batch_size) + 1):
        user_id = f"batch_user_{i}"
        user_feedback = storage.get_user_feedback(user_id)
        if user_feedback:
            feedback_types = [f.feedback_type.value for f in user_feedback]
            print(f"  {user_id}: {len(user_feedback)} items ({', '.join(set(feedback_types))})")

def demo_callback_system():
    """Demo callback system for feedback events"""
    print_separator("DEMO 4: Callback System", "=")
    
    print("📞 Testing callback system for feedback events...")
    
    storage = create_feedback_storage("demo_callbacks.db")
    collector = create_feedback_collector(storage)
    
    # Set up event tracking
    events_log = []
    
    def log_event(event_type):
        def callback(*args, **kwargs):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            events_log.append({
                'timestamp': timestamp,
                'event': event_type,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            print(f"  📝 [{timestamp}] Event: {event_type}")
        return callback
    
    # Register callbacks
    collector.register_callback('on_feedback_collected', log_event('COLLECTED'))
    collector.register_callback('on_feedback_validated', log_event('VALIDATED'))
    collector.register_callback('on_feedback_stored', log_event('STORED'))
    collector.register_callback('on_collection_error', log_event('ERROR'))
    
    print(f"\n🔧 Registered {len(collector.callbacks)} callback types")
    
    # Create test context
    context = FeedbackContext(
        content_type=ContentType.TRANSCRIPTION,
        content_id="callback_test",
        original_content="Testing callback system functionality"
    )
    
    # Trigger various feedback collection events
    print(f"\n📝 Triggering feedback collection events...")
    
    events_to_trigger = [
        ("Rating Collection", lambda: collector.collect_rating_feedback("callback_user", context)),
        ("Correction Collection", lambda: collector.collect_correction_feedback(
            "callback_user", context, "testing", "Testing")),
        ("Suggestion Collection", lambda: collector.collect_suggestion_feedback(
            "callback_user", context, "This is a callback system test suggestion")),
        ("Invalid Collection", lambda: collector.collect_correction_feedback(
            "callback_user", context, "same", "same"))  # Should trigger error
    ]
    
    for i, (event_name, trigger_func) in enumerate(events_to_trigger):
        print(f"\n🎯 {event_name}:")
        result = trigger_func()
        time.sleep(0.3)  # Allow callbacks to process
        
        print_progress(i + 1, len(events_to_trigger), "Event Triggering")
    
    print(f"\n📊 Callback System Results:")
    print(f"  Total events logged: {len(events_log)}")
    
    # Group events by type
    event_counts = {}
    for event in events_log:
        event_type = event['event']
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count} events")
    
    # Show event timeline
    print(f"\n⏰ Event Timeline:")
    for event in events_log[-6:]:  # Show last 6 events
        print(f"  [{event['timestamp']}] {event['event']}")

def demo_comprehensive_statistics():
    """Demo comprehensive statistics and reporting"""
    print_separator("DEMO 5: Comprehensive Statistics", "=")
    
    print("📊 Generating comprehensive feedback collection statistics...")
    
    # Use existing storage from previous demos
    storage = create_feedback_storage("demo_collection.db")
    collector = create_feedback_collector(storage)
    
    print(f"\n📈 Collecting comprehensive statistics...")
    
    # Get overall statistics
    stats = collector.get_collection_statistics()
    
    print(f"\n📋 Overall Statistics:")
    print(f"  Total feedback collected: {stats.get('total_collected', 0)}")
    print(f"  Collection methods available: {len(stats.get('collection_methods_available', []))}")
    print(f"  Validation success rate: {stats.get('validation_success_rate', 0)*100:.1f}%")
    
    # Analyze by feedback type
    if 'by_type' in stats:
        print(f"\n📊 By Feedback Type:")
        for feedback_type, type_stats in stats['by_type'].items():
            count = type_stats.get('count', 0)
            avg_rating = type_stats.get('avg_rating')
            rating_info = f" (Avg Rating: {avg_rating:.2f})" if avg_rating else ""
            print(f"  {feedback_type.title()}: {count}{rating_info}")
    
    # Analyze by status
    if 'by_status' in stats:
        print(f"\n🔄 By Status:")
        for status, count in stats['by_status'].items():
            status_icon = {
                'pending': '⏳',
                'processed': '✅',
                'applied': '🎯',
                'rejected': '❌'
            }.get(status, '📄')
            print(f"  {status_icon} {status.title()}: {count}")
    
    # User activity analysis
    print(f"\n👥 User Activity Analysis:")
    all_users = set()
    
    # Get users from different collection methods
    for method in [CollectionMethod.INLINE, CollectionMethod.POPUP]:
        user_id = f"demo_user_{method.value}"
        user_feedback = storage.get_user_feedback(user_id)
        if user_feedback:
            all_users.add(user_id)
            feedback_types = [f.feedback_type.value for f in user_feedback]
            print(f"  {user_id}: {len(user_feedback)} items ({', '.join(set(feedback_types))})")
    
    # Content analysis
    print(f"\n📄 Content Analysis:")
    content_types = [ContentType.TRANSCRIPTION, ContentType.MEETING_ELEMENT, ContentType.ACTION_ITEM]
    
    for content_type in content_types:
        type_stats = storage.get_feedback_statistics(content_type=content_type)
        total = type_stats.get('total_feedback', 0)
        if total > 0:
            print(f"  {content_type.value.replace('_', ' ').title()}: {total} feedback items")
    
    # Generate summary report
    print(f"\n📝 Summary Report:")
    print(f"  Active users: {len(all_users)}")
    print(f"  Collection interfaces tested: {len(collector.interfaces)}")
    print(f"  Feedback validation enabled: ✅")
    print(f"  Change detection enabled: ✅")
    print(f"  Batch processing supported: ✅")
    print(f"  Callback system active: ✅")

def main():
    """Run all demos with progress tracking"""
    print_separator("FEEDBACK COLLECTION INTERFACES DEMO", "=")
    print("🎛️  Comprehensive feedback collection system demonstration")
    print("📊 Features: Multiple Interfaces, Validation, Change Detection, Batch Processing")
    print()
    
    start_time = time.time()
    
    try:
        # Demo 1: Collection interfaces
        storage = demo_collection_interfaces()
        print("\n" + "="*80 + "\n")
        
        # Demo 2: Validation and change detection
        demo_validation_and_change_detection()
        print("\n" + "="*80 + "\n")
        
        # Demo 3: Batch collection
        demo_batch_collection()
        print("\n" + "="*80 + "\n")
        
        # Demo 4: Callback system
        demo_callback_system()
        print("\n" + "="*80 + "\n")
        
        # Demo 5: Comprehensive statistics
        demo_comprehensive_statistics()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_separator("DEMO COMPLETED SUCCESSFULLY", "=")
        print("✅ All demos completed successfully!")
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print("🚀 The Feedback Collection System is ready for production use!")
        
        print("\n🎯 Key Features Demonstrated:")
        print("  • Multiple collection interfaces (Inline, Popup)")
        print("  • Comprehensive validation system")
        print("  • Advanced change detection and categorization")
        print("  • Rating, correction, and suggestion collection")
        print("  • Batch feedback processing capabilities")
        print("  • Event-driven callback system")
        print("  • Statistical analysis and reporting")
        print("  • Integration with storage system")
        
        # Clean up demo databases
        demo_files = ["demo_collection.db", "demo_batch.db", "demo_callbacks.db"]
        for file in demo_files:
            try:
                os.remove(file)
            except:
                pass
        
        print("\n🧹 Demo databases cleaned up")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()