#!/usr/bin/env python3
"""
Demo: NLP Performance Optimization and Caching
Showcases intelligent caching, resource management, and performance optimization
"""

import asyncio
import sys
import os
import time
import json
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from nlp_performance_optimization import (
        PerformanceOptimizer,
        ModelCache,
        ResourceManager,
        create_performance_optimizer,
        benchmark_processing
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires the performance optimization components to be available.")
    sys.exit(1)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_section(title: str):
    """Print formatted section"""
    print(f"\n--- {title} ---")

def print_performance_stats(stats: Dict[str, Any], title: str = "Performance Statistics"):
    """Print performance statistics in a formatted way"""
    print(f"\n📊 {title}:")
    
    if 'processing_performance' in stats:
        perf = stats['processing_performance']
        if perf:
            print("   ⚡ Processing Performance:")
            for task_model, metrics in perf.items():
                print(f"     {task_model}:")
                print(f"       Average: {metrics['avg_ms']:.1f}ms")
                print(f"       Min: {metrics['min_ms']:.1f}ms")
                print(f"       Max: {metrics['max_ms']:.1f}ms")
                print(f"       Count: {metrics['count']}")
    
    if 'cache_performance' in stats:
        cache = stats['cache_performance']
        print("   💾 Cache Performance:")
        
        for cache_type in ['result_cache', 'model_cache', 'embedding_cache']:
            if cache_type in cache:
                cache_stats = cache[cache_type]
                hit_rate = cache_stats.get('hit_rate', 0) * 100
                print(f"     {cache_type.replace('_', ' ').title()}:")
                print(f"       Hit Rate: {hit_rate:.1f}%")
                print(f"       Entries: {cache_stats.get('entry_count', 0)}")
                print(f"       Hits: {cache_stats.get('hits', 0)}")
                print(f"       Misses: {cache_stats.get('misses', 0)}")
    
    if 'resource_usage' in stats:
        resource = stats['resource_usage']
        if 'current' in resource:
            current = resource['current']
            print("   🖥️  Resource Usage:")
            print(f"     Memory: {current['memory_percent']:.1f}%")
            print(f"     Available Memory: {current['memory_available_gb']:.1f}GB")
            print(f"     CPU: {current['cpu_percent']:.1f}%")

async def demo_basic_caching():
    """Demonstrate basic caching functionality"""
    print_header("NLP Performance Optimization Demo")
    
    print("🚀 Initializing Performance Optimizer...")
    optimizer = create_performance_optimizer()
    await optimizer.initialize()
    
    print("✅ Performance optimizer initialized!")
    
    # Demo 1: Basic caching behavior
    print_section("1. Basic Caching Behavior")
    
    # Mock processor that simulates real NLP processing
    async def mock_nlp_processor(text: str, task_type: str, **kwargs):
        """Mock NLP processor with realistic delays"""
        # Simulate different processing times for different tasks
        delays = {
            'ner': 0.05,      # 50ms for NER
            'sentiment': 0.03, # 30ms for sentiment
            'classification': 0.08, # 80ms for classification
            'pos': 0.02       # 20ms for POS tagging
        }
        
        delay = delays.get(task_type, 0.05)
        await asyncio.sleep(delay)
        
        # Return mock result
        return {
            'status': 'success',
            'data': {
                'task_type': task_type,
                'text_length': len(text),
                'entities': [{'text': 'mock', 'label': 'TEST'}] if task_type == 'ner' else None,
                'sentiment': {'polarity': 0.5} if task_type == 'sentiment' else None
            },
            'processing_time': delay,
            'model_id': f'{task_type}_model'
        }
    
    test_text = "Apple Inc. is a technology company founded by Steve Jobs."
    
    print(f"📝 Test Text: {test_text}")
    print(f"   Length: {len(test_text)} characters")
    
    # First processing - cache miss
    print("\n🔍 First Processing (Cache Miss):")
    start_time = time.time()
    result1 = await optimizer.optimize_processing(
        test_text, "ner", "ner_model", mock_nlp_processor
    )
    first_time = time.time() - start_time
    
    print(f"   ⏱️  Processing Time: {first_time*1000:.1f}ms")
    print(f"   📊 Result: {result1['data']['task_type']} processing completed")
    
    # Second processing - cache hit
    print("\n🔍 Second Processing (Cache Hit):")
    start_time = time.time()
    result2 = await optimizer.optimize_processing(
        test_text, "ner", "ner_model", mock_nlp_processor
    )
    second_time = time.time() - start_time
    
    print(f"   ⏱️  Processing Time: {second_time*1000:.1f}ms")
    print(f"   🚀 Speedup: {first_time/second_time:.1f}x faster")
    print(f"   💾 Cache Hit: {'Yes' if second_time < first_time/2 else 'No'}")
    
    return optimizer

async def demo_multi_task_caching(optimizer):
    """Demonstrate caching across multiple task types"""
    print_section("2. Multi-Task Caching")
    
    async def mock_processor(text: str, task_type: str, **kwargs):
        delays = {'ner': 0.05, 'sentiment': 0.03, 'classification': 0.08, 'pos': 0.02}
        await asyncio.sleep(delays.get(task_type, 0.05))
        return {'status': 'success', 'data': {'task_type': task_type, 'result': 'mock'}}
    
    test_cases = [
        ("Apple Inc. develops innovative technology products.", "ner"),
        ("I love this new iPhone! It's amazing.", "sentiment"),
        ("This article discusses artificial intelligence advancements.", "classification"),
        ("The quick brown fox jumps over the lazy dog.", "pos")
    ]
    
    print("🔄 Processing multiple tasks...")
    
    results = []
    for text, task_type in test_cases:
        print(f"\n📝 Task: {task_type.upper()}")
        print(f"   Text: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # First run
        start_time = time.time()
        result = await optimizer.optimize_processing(
            text, task_type, f"{task_type}_model", mock_processor
        )
        first_time = time.time() - start_time
        
        # Second run (should hit cache)
        start_time = time.time()
        result = await optimizer.optimize_processing(
            text, task_type, f"{task_type}_model", mock_processor
        )
        second_time = time.time() - start_time
        
        speedup = first_time / second_time if second_time > 0 else float('inf')
        results.append((task_type, first_time, second_time, speedup))
        
        print(f"   ⏱️  First: {first_time*1000:.1f}ms, Second: {second_time*1000:.1f}ms")
        print(f"   🚀 Speedup: {speedup:.1f}x")
    
    # Summary
    print("\n📊 Multi-Task Caching Summary:")
    print("=" * 60)
    print(f"{'Task':<15} {'First (ms)':<12} {'Second (ms)':<13} {'Speedup':<10}")
    print("=" * 60)
    
    for task_type, first, second, speedup in results:
        print(f"{task_type:<15} {first*1000:<12.1f} {second*1000:<13.1f} {speedup:<10.1f}x")
    
    print("=" * 60)

async def demo_model_preloading(optimizer):
    """Demonstrate model preloading optimization"""
    print_section("3. Model Preloading Optimization")
    
    print("🔧 Testing model preloading...")
    
    # Check initial model cache state
    models_to_preload = ["bert_base", "roberta_large", "distilbert", "spacy_lg"]
    
    print(f"📋 Models to preload: {models_to_preload}")
    
    # Check if models are cached before preloading
    print("\n🔍 Before Preloading:")
    for model_id in models_to_preload:
        cached = optimizer.cache.get_model(model_id) is not None
        print(f"   {model_id}: {'✅ Cached' if cached else '❌ Not Cached'}")
    
    # Preload models
    print("\n⚡ Preloading models...")
    start_time = time.time()
    optimizer.preload_models(models_to_preload)
    preload_time = time.time() - start_time
    
    print(f"   ⏱️  Preloading completed in {preload_time*1000:.1f}ms")
    
    # Check cache state after preloading
    print("\n🔍 After Preloading:")
    cached_count = 0
    for model_id in models_to_preload:
        cached = optimizer.cache.get_model(model_id) is not None
        if cached:
            cached_count += 1
        print(f"   {model_id}: {'✅ Cached' if cached else '❌ Not Cached'}")
    
    print(f"\n📊 Preloading Success Rate: {cached_count}/{len(models_to_preload)} ({cached_count/len(models_to_preload)*100:.1f}%)")

async def demo_batch_optimization(optimizer):
    """Demonstrate batch processing optimization"""
    print_section("4. Batch Processing Optimization")
    
    # Create a batch of texts
    batch_texts = [
        "Apple Inc. is a technology company.",
        "Google develops search algorithms.",
        "Microsoft creates software products.",
        "Amazon provides cloud services.",
        "Tesla manufactures electric vehicles.",
        "Apple Inc. is a technology company.",  # Duplicate for cache testing
        "Facebook connects people worldwide.",
        "Netflix streams entertainment content."
    ]
    
    print(f"📦 Batch Processing Test:")
    print(f"   Batch Size: {len(batch_texts)} texts")
    print(f"   Unique Texts: {len(set(batch_texts))}")
    
    # Analyze batch for cache coverage
    task_type = "ner"
    model_id = "ner_model"
    
    print(f"\n🔍 Analyzing batch for cache coverage...")
    batch_analysis = optimizer.optimize_batch_processing(batch_texts, task_type, model_id)
    
    cached_count = sum(1 for _, cached in batch_analysis if cached)
    cache_coverage = cached_count / len(batch_texts) * 100
    
    print(f"   💾 Cache Coverage: {cache_coverage:.1f}% ({cached_count}/{len(batch_texts)})")
    
    # Show detailed analysis
    print("\n📋 Detailed Batch Analysis:")
    for i, (text, cached) in enumerate(batch_analysis, 1):
        status = "🟢 Cached" if cached else "🔴 Process"
        print(f"   {i:2d}. {status} - {text[:40]}{'...' if len(text) > 40 else ''}")
    
    # Process a few items to populate cache
    async def mock_processor(text: str, task_type: str, **kwargs):
        await asyncio.sleep(0.02)
        return {'status': 'success', 'data': {'entities': []}}
    
    print(f"\n⚡ Processing first 3 items to populate cache...")
    for text in batch_texts[:3]:
        await optimizer.optimize_processing(text, task_type, model_id, mock_processor)
    
    # Re-analyze batch
    print(f"\n🔍 Re-analyzing batch after processing...")
    batch_analysis_after = optimizer.optimize_batch_processing(batch_texts, task_type, model_id)
    
    cached_count_after = sum(1 for _, cached in batch_analysis_after if cached)
    cache_coverage_after = cached_count_after / len(batch_texts) * 100
    
    print(f"   💾 New Cache Coverage: {cache_coverage_after:.1f}% ({cached_count_after}/{len(batch_texts)})")
    print(f"   📈 Improvement: +{cache_coverage_after - cache_coverage:.1f}%")

async def demo_resource_monitoring(optimizer):
    """Demonstrate resource monitoring and optimization"""
    print_section("5. Resource Monitoring and Management")
    
    print("🖥️  Resource Monitoring Demo:")
    
    # Get current resource statistics
    resource_stats = optimizer.resource_manager.get_resource_stats()
    
    print(f"\n📊 Current System Resources:")
    current = resource_stats['current']
    print(f"   Memory Usage: {current['memory_percent']:.1f}%")
    print(f"   Available Memory: {current['memory_available_gb']:.1f}GB")
    print(f"   Used Memory: {current['memory_used_gb']:.1f}GB")
    print(f"   CPU Usage: {current['cpu_percent']:.1f}%")
    
    # Show thresholds
    thresholds = resource_stats['thresholds']
    print(f"\n⚠️  Resource Thresholds:")
    print(f"   High Memory: {thresholds['high_memory_threshold']:.1f}%")
    print(f"   Critical Memory: {thresholds['critical_memory_threshold']:.1f}%")
    print(f"   High CPU: {thresholds['high_cpu_threshold']:.1f}%")
    print(f"   Critical CPU: {thresholds['critical_cpu_threshold']:.1f}%")
    
    # Show optimization stats
    opt_stats = resource_stats['optimization_stats']
    print(f"\n🔧 Optimization Statistics:")
    print(f"   Garbage Collections: {opt_stats['gc_collections']}")
    print(f"   Memory Optimizations: {opt_stats['memory_optimizations']}")
    
    # Test resource availability
    print(f"\n🔍 Resource Availability Tests:")
    
    test_cases = [
        (10, 1, "Small task (10MB, 1 core)"),
        (100, 2, "Medium task (100MB, 2 cores)"),
        (1000, 4, "Large task (1GB, 4 cores)"),
        (10000, 8, "Very large task (10GB, 8 cores)")
    ]
    
    for memory_mb, cpu_cores, description in test_cases:
        available = optimizer.resource_manager.is_resource_available(memory_mb, cpu_cores)
        status = "✅ Available" if available else "❌ Not Available"
        print(f"   {status} - {description}")

async def demo_performance_benchmarking(optimizer):
    """Demonstrate performance benchmarking"""
    print_section("6. Performance Benchmarking")
    
    print("🏁 Running Performance Benchmarks...")
    
    # Define benchmark test cases
    test_cases = [
        ("Short text", "ner", "ner_model"),
        ("This is a medium length text for testing performance", "sentiment", "sentiment_model"),
        ("This is a much longer text sample designed to test the performance characteristics of the NLP processing system with various types of content and different complexity levels.", "classification", "classification_model"),
        ("Simple POS test", "pos", "pos_model"),
        ("Another NER test with entities", "ner", "ner_model")
    ]
    
    print(f"📋 Benchmark Configuration:")
    print(f"   Test Cases: {len(test_cases)}")
    print(f"   Iterations per Case: 5")
    print(f"   Total Operations: {len(test_cases) * 5}")
    
    # Run benchmark
    start_time = time.time()
    benchmark_results = await benchmark_processing(optimizer, test_cases, iterations=5)
    total_time = time.time() - start_time
    
    print(f"\n⏱️  Benchmark completed in {total_time:.2f}s")
    
    # Display results
    print(f"\n📊 Benchmark Results:")
    print("=" * 80)
    print(f"{'Text Length':<12} {'Task':<15} {'Model':<15} {'Avg (ms)':<10} {'Min (ms)':<10} {'Max (ms)':<10}")
    print("=" * 80)
    
    for result in benchmark_results['results']:
        print(f"{result['text_length']:<12} {result['task_type']:<15} {result['model_id']:<15} "
              f"{result['avg_ms']:<10.1f} {result['min_ms']:<10.1f} {result['max_ms']:<10.1f}")
    
    print("=" * 80)
    
    # Show summary
    if 'summary' in benchmark_results:
        summary = benchmark_results['summary']
        print(f"\n📈 Benchmark Summary:")
        print(f"   Overall Average: {summary['overall_avg_ms']:.1f}ms")
        print(f"   Fastest Operation: {summary['overall_min_ms']:.1f}ms")
        print(f"   Slowest Operation: {summary['overall_max_ms']:.1f}ms")
        print(f"   Cache Hit Rate: {summary['cache_hit_rate']:.1%}")

async def demo_performance_tuning(optimizer):
    """Demonstrate automatic performance tuning"""
    print_section("7. Automatic Performance Tuning")
    
    print("🎯 Performance Tuning Demo:")
    
    # Add some mock performance data
    optimizer.performance_metrics['processing_times']['slow_task'] = [0.2, 0.25, 0.3, 0.28, 0.22]  # 200-300ms
    optimizer.performance_metrics['processing_times']['fast_task'] = [0.01, 0.015, 0.012, 0.018, 0.014]  # 10-18ms
    
    # Show current strategies
    print(f"\n🔧 Current Optimization Strategies:")
    for strategy, enabled in optimizer.optimization_strategies.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"   {status} - {strategy.replace('_', ' ').title()}")
    
    # Calculate current average performance
    all_times = []
    for times in optimizer.performance_metrics['processing_times'].values():
        all_times.extend(times)
    
    if all_times:
        current_avg_ms = (sum(all_times) / len(all_times)) * 1000
        print(f"\n📊 Current Performance:")
        print(f"   Average Response Time: {current_avg_ms:.1f}ms")
        print(f"   Total Measurements: {len(all_times)}")
    
    # Tune for different targets
    targets = [50.0, 100.0, 200.0]
    
    for target_ms in targets:
        print(f"\n🎯 Tuning for {target_ms}ms target...")
        
        # Store original strategies
        original_strategies = optimizer.optimization_strategies.copy()
        
        # Tune performance
        optimizer.tune_performance(target_response_time_ms=target_ms)
        
        # Show changes
        print(f"   Strategy Changes:")
        for strategy, enabled in optimizer.optimization_strategies.items():
            original = original_strategies[strategy]
            if enabled != original:
                change = "Enabled" if enabled else "Disabled"
                print(f"     🔄 {change}: {strategy.replace('_', ' ').title()}")
        
        # Show optimization events
        events = optimizer.performance_metrics['optimization_events']
        if events:
            latest_event = events[-1]
            print(f"   📝 Latest Event: Tuned for {latest_event['target_ms']}ms (actual: {latest_event['actual_ms']:.1f}ms)")

async def demo_comprehensive_performance_report(optimizer):
    """Demonstrate comprehensive performance reporting"""
    print_section("8. Comprehensive Performance Report")
    
    print("📋 Generating Comprehensive Performance Report...")
    
    # Get full performance report
    report = optimizer.get_performance_report()
    
    print_performance_stats(report, "Complete Performance Analysis")
    
    # Additional insights
    print(f"\n🔍 Performance Insights:")
    
    # Cache efficiency analysis
    cache_perf = report.get('cache_performance', {})
    if 'result_cache' in cache_perf:
        result_cache = cache_perf['result_cache']
        hit_rate = result_cache.get('hit_rate', 0) * 100
        
        if hit_rate > 80:
            print(f"   ✅ Excellent cache performance ({hit_rate:.1f}% hit rate)")
        elif hit_rate > 60:
            print(f"   ⚠️  Good cache performance ({hit_rate:.1f}% hit rate)")
        else:
            print(f"   ❌ Poor cache performance ({hit_rate:.1f}% hit rate) - consider tuning")
    
    # Processing performance analysis
    proc_perf = report.get('processing_performance', {})
    if proc_perf:
        avg_times = [metrics['avg_ms'] for metrics in proc_perf.values()]
        overall_avg = sum(avg_times) / len(avg_times)
        
        if overall_avg < 50:
            print(f"   ✅ Excellent response times (avg: {overall_avg:.1f}ms)")
        elif overall_avg < 100:
            print(f"   ⚠️  Good response times (avg: {overall_avg:.1f}ms)")
        else:
            print(f"   ❌ Slow response times (avg: {overall_avg:.1f}ms) - optimization needed")
    
    # Resource usage analysis
    resource_usage = report.get('resource_usage', {})
    if 'current' in resource_usage:
        current = resource_usage['current']
        memory_pct = current['memory_percent']
        cpu_pct = current['cpu_percent']
        
        if memory_pct < 70:
            print(f"   ✅ Healthy memory usage ({memory_pct:.1f}%)")
        elif memory_pct < 85:
            print(f"   ⚠️  Moderate memory usage ({memory_pct:.1f}%)")
        else:
            print(f"   ❌ High memory usage ({memory_pct:.1f}%) - optimization recommended")
    
    # Optimization recommendations
    print(f"\n💡 Optimization Recommendations:")
    
    if cache_perf.get('result_cache', {}).get('hit_rate', 0) < 0.6:
        print(f"   • Increase cache size or TTL to improve hit rates")
    
    if proc_perf and any(m['avg_ms'] > 100 for m in proc_perf.values()):
        print(f"   • Consider model preloading for frequently used models")
        print(f"   • Enable aggressive caching for slow operations")
    
    if resource_usage.get('current', {}).get('memory_percent', 0) > 80:
        print(f"   • Monitor memory usage and consider garbage collection tuning")
    
    print(f"   • Regular performance monitoring and tuning recommended")

async def main():
    """Main demo function"""
    try:
        # Initialize and run all demo sections
        optimizer = await demo_basic_caching()
        
        await demo_multi_task_caching(optimizer)
        await demo_model_preloading(optimizer)
        await demo_batch_optimization(optimizer)
        await demo_resource_monitoring(optimizer)
        await demo_performance_benchmarking(optimizer)
        await demo_performance_tuning(optimizer)
        await demo_comprehensive_performance_report(optimizer)
        
        print_section("Demo Complete!")
        print("✅ NLP Performance Optimization demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Intelligent caching with LRU eviction")
        print("• Multi-task processing optimization")
        print("• Model preloading and management")
        print("• Batch processing optimization")
        print("• Real-time resource monitoring")
        print("• Performance benchmarking and analysis")
        print("• Automatic performance tuning")
        print("• Comprehensive performance reporting")
        print("• Resource-aware optimization")
        print("• Cache hit rate optimization")
        
        # Final cleanup
        await optimizer.shutdown()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())