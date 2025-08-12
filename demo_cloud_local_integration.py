#!/usr/bin/env python3
"""
Demo: Cloud-Local Model Integration
Showcases intelligent fallback between cloud services and local models
"""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from cloud_local_model_integration import (
        CloudLocalModelIntegrator,
        ModelProvider,
        ProcessingStatus,
        ProviderConfig,
        create_integrator
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires the cloud-local integration components to be available.")
    sys.exit(1)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_section(title: str):
    """Print formatted section"""
    print(f"\n--- {title} ---")

def print_result(result, task_type: str, text: str):
    """Print processing result in a formatted way"""
    status_emoji = {
        ProcessingStatus.SUCCESS: "✅",
        ProcessingStatus.FAILED: "❌",
        ProcessingStatus.TIMEOUT: "⏰",
        ProcessingStatus.RATE_LIMITED: "🚫",
        ProcessingStatus.NETWORK_ERROR: "🌐"
    }
    
    emoji = status_emoji.get(result.status, "❓")
    print(f"\n{emoji} {task_type.upper()} Processing Result:")
    print(f"   Text: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"   Status: {result.status.value}")
    print(f"   Provider: {result.provider_used.value if result.provider_used else 'None'}")
    print(f"   Model: {result.model_id or 'Unknown'}")
    print(f"   Processing Time: {result.processing_time:.3f}s")
    print(f"   Confidence: {result.confidence_score:.2f}")
    
    if result.status == ProcessingStatus.SUCCESS and result.data:
        if task_type == "ner" and "entities" in result.data:
            entities = result.data["entities"]
            print(f"   Entities Found: {len(entities)}")
            for entity in entities[:3]:  # Show first 3
                print(f"     • {entity['text']} ({entity['label']}) - {entity['confidence']:.2f}")
            if len(entities) > 3:
                print(f"     ... and {len(entities) - 3} more")
        
        elif task_type == "sentiment" and "sentiment" in result.data:
            sentiment = result.data["sentiment"]
            if isinstance(sentiment, dict):
                if "polarity" in sentiment:
                    polarity = sentiment["polarity"]
                    label = sentiment.get("label", "neutral")
                    print(f"   Sentiment: {label} (polarity: {polarity:.2f})")
                elif "predicted_label" in sentiment:
                    label = sentiment["predicted_label"]
                    confidence = sentiment["confidence"]
                    print(f"   Sentiment: {label} (confidence: {confidence:.2f})")
        
        elif task_type == "classification" and "classification" in result.data:
            classification = result.data["classification"]
            if "predicted_class" in classification:
                pred_class = classification["predicted_class"]
                confidence = classification["confidence"]
                print(f"   Classification: {pred_class} (confidence: {confidence:.2f})")
        
        elif task_type == "pos" and "tokens" in result.data:
            tokens = result.data["tokens"]
            print(f"   Tokens: {len(tokens)}")
            for token in tokens[:5]:  # Show first 5
                print(f"     • {token['text']} ({token['pos']})")
            if len(tokens) > 5:
                print(f"     ... and {len(tokens) - 5} more")
    
    elif result.status != ProcessingStatus.SUCCESS:
        print(f"   Error: {result.error_message}")
        if result.metadata and "attempted_providers" in result.metadata:
            print(f"   Attempted Providers: {result.metadata['attempted_providers']}")

async def demo_basic_processing():
    """Demonstrate basic processing with different providers"""
    print_header("Cloud-Local Model Integration Demo")
    
    print("🚀 Initializing Cloud-Local Model Integrator...")
    integrator = await create_integrator()
    
    print("✅ Integrator initialized successfully!")
    
    # Show available providers
    print_section("1. Available Providers")
    
    provider_status = integrator.get_provider_status()
    print("📋 Provider Status:")
    
    for name, status in provider_status.items():
        status_icon = "🟢" if status['available'] and status['enabled'] else "🔴"
        health_icon = "💚" if status['healthy'] else "💔"
        
        print(f"   {status_icon} {name}:")
        print(f"      Type: {status['provider_type']}")
        print(f"      Model: {status['model_id']}")
        print(f"      Priority: {status['priority']}")
        print(f"      Enabled: {status['enabled']}")
        print(f"      Available: {status['available']}")
        print(f"      Healthy: {health_icon} {status['healthy']}")
        print(f"      Success Rate: {status['success_rate']:.2f}")
        if status['current_usage'] > 0:
            print(f"      Usage: {status['current_usage']}")
            print(f"      Avg Response Time: {status['average_response_time']:.3f}s")
    
    return integrator

async def demo_task_processing(integrator):
    """Demonstrate processing different task types"""
    print_section("2. Task Processing Examples")
    
    # Test samples for different tasks
    test_samples = [
        {
            "text": "Apple Inc. was founded by Steve Jobs and Steve Wozniak in Cupertino, California on April 1, 1976.",
            "task": "ner",
            "description": "Named Entity Recognition - Extract people, organizations, and locations"
        },
        {
            "text": "I absolutely love this new AI technology! It's incredibly helpful and makes my work so much easier.",
            "task": "sentiment",
            "description": "Sentiment Analysis - Determine emotional tone"
        },
        {
            "text": "The latest breakthrough in artificial intelligence and machine learning has revolutionized data processing.",
            "task": "classification",
            "description": "Text Classification - Categorize content by topic"
        },
        {
            "text": "The quick brown fox jumps over the lazy dog.",
            "task": "pos",
            "description": "Part-of-Speech Tagging - Identify grammatical roles"
        }
    ]
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n🔍 Example {i}: {sample['description']}")
        print(f"   Task Type: {sample['task']}")
        
        result = await integrator.process(sample['text'], sample['task'])
        print_result(result, sample['task'], sample['text'])

async def demo_fallback_behavior(integrator):
    """Demonstrate fallback behavior when providers fail"""
    print_section("3. Fallback Behavior Demonstration")
    
    print("🔄 Testing fallback mechanisms...")
    
    # Scenario 1: Disable cloud providers to test local fallback
    print("\n📊 Scenario 1: Cloud Providers Unavailable")
    print("   Simulating cloud provider outage...")
    
    # Temporarily disable cloud providers
    original_states = {}
    for name, config in integrator.provider_configs.items():
        if config.provider in [ModelProvider.OPENAI, ModelProvider.HUGGINGFACE]:
            original_states[name] = config.enabled
            config.enabled = False
    
    test_text = "Microsoft and Google are competing in the cloud computing market."
    result = await integrator.process(test_text, "ner")
    print_result(result, "ner", test_text)
    
    if result.status == ProcessingStatus.SUCCESS:
        print("   ✅ Successfully fell back to local processing!")
    
    # Restore original states
    for name, original_state in original_states.items():
        integrator.provider_configs[name].enabled = original_state
    
    # Scenario 2: Test quota exceeded fallback
    print("\n📊 Scenario 2: Quota Exceeded")
    print("   Simulating quota exceeded for cloud providers...")
    
    # Temporarily set quota exceeded
    original_quotas = {}
    for name, config in integrator.provider_configs.items():
        if config.provider in [ModelProvider.OPENAI, ModelProvider.HUGGINGFACE]:
            original_quotas[name] = (config.monthly_quota, config.current_usage)
            config.monthly_quota = 10
            config.current_usage = 15  # Exceed quota
    
    test_text = "Amazon Web Services provides cloud infrastructure solutions."
    result = await integrator.process(test_text, "ner")
    print_result(result, "ner", test_text)
    
    if result.status == ProcessingStatus.SUCCESS:
        print("   ✅ Successfully handled quota exceeded with fallback!")
    
    # Restore original quotas
    for name, (quota, usage) in original_quotas.items():
        config = integrator.provider_configs[name]
        config.monthly_quota = quota
        config.current_usage = usage

async def demo_provider_preferences(integrator):
    """Demonstrate provider preference and selection"""
    print_section("4. Provider Preference and Selection")
    
    test_text = "Tesla is developing autonomous vehicles using artificial intelligence."
    
    # Test with different preferred providers
    preferences = [
        ("spacy_sm", "Fast local processing"),
        ("spacy_lg", "High-accuracy local processing"),
        (None, "Automatic selection")
    ]
    
    for preferred_provider, description in preferences:
        print(f"\n🎯 Testing: {description}")
        if preferred_provider:
            print(f"   Preferred Provider: {preferred_provider}")
        
        result = await integrator.process(
            test_text, 
            "ner", 
            preferred_provider=preferred_provider
        )
        
        print_result(result, "ner", test_text)
        
        if result.status == ProcessingStatus.SUCCESS:
            actual_provider = result.provider_used.value if result.provider_used else "unknown"
            print(f"   📍 Actually used: {actual_provider}")

async def demo_performance_comparison(integrator):
    """Demonstrate performance comparison across providers"""
    print_section("5. Performance Comparison")
    
    test_texts = [
        "Short text for speed test.",
        "This is a medium-length text sample that contains several entities like Apple, Microsoft, and Google to test processing performance across different providers.",
        "This is a much longer text sample designed to test the performance characteristics of different NLP providers when processing substantial amounts of content. It includes multiple named entities such as organizations like Facebook, Amazon, Netflix, and Tesla, as well as people like Elon Musk, Jeff Bezos, and Mark Zuckerberg. The text also contains various locations including Silicon Valley, New York City, and Seattle to provide a comprehensive test of named entity recognition capabilities across different model sizes and provider types."
    ]
    
    print("⚡ Performance Comparison:")
    print("=" * 80)
    print(f"{'Text Length':<15} {'Provider':<15} {'Time (ms)':<12} {'Entities':<10} {'Confidence':<12}")
    print("=" * 80)
    
    for i, text in enumerate(test_texts):
        length_desc = ["Short", "Medium", "Long"][i]
        
        # Test with different providers by preference
        for provider_name in ["spacy_sm", "spacy_md", "spacy_lg"]:
            if provider_name in integrator.providers:
                result = await integrator.process(
                    text, 
                    "ner", 
                    preferred_provider=provider_name
                )
                
                if result.status == ProcessingStatus.SUCCESS:
                    entity_count = len(result.data.get("entities", [])) if result.data else 0
                    time_ms = result.processing_time * 1000
                    confidence = result.confidence_score
                    
                    print(f"{length_desc:<15} {provider_name:<15} {time_ms:<12.1f} {entity_count:<10} {confidence:<12.2f}")
    
    print("=" * 80)

async def demo_concurrent_processing(integrator):
    """Demonstrate concurrent processing capabilities"""
    print_section("6. Concurrent Processing")
    
    print("🔄 Testing concurrent processing with multiple requests...")
    
    # Create multiple concurrent requests
    test_requests = [
        ("Apple Inc. is a technology company.", "ner"),
        ("I love this new product!", "sentiment"),
        ("This is about artificial intelligence.", "classification"),
        ("Google develops search algorithms.", "ner"),
        ("The weather is terrible today.", "sentiment")
    ]
    
    print(f"   Submitting {len(test_requests)} concurrent requests...")
    
    start_time = asyncio.get_event_loop().time()
    
    # Process all requests concurrently
    tasks = [
        integrator.process(text, task_type)
        for text, task_type in test_requests
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = asyncio.get_event_loop().time()
    total_time = end_time - start_time
    
    print(f"   ✅ Completed {len(results)} requests in {total_time:.3f}s")
    print(f"   📊 Average time per request: {total_time/len(results):.3f}s")
    
    # Show results summary
    successful = sum(1 for r in results if r.status == ProcessingStatus.SUCCESS)
    failed = len(results) - successful
    
    print(f"   📈 Success rate: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    
    if failed > 0:
        print(f"   ⚠️  Failed requests: {failed}")
    
    # Show provider distribution
    provider_usage = {}
    for result in results:
        if result.provider_used:
            provider = result.provider_used.value
            provider_usage[provider] = provider_usage.get(provider, 0) + 1
    
    print("   🔧 Provider usage:")
    for provider, count in provider_usage.items():
        print(f"     {provider}: {count} requests")

async def demo_statistics_and_monitoring(integrator):
    """Demonstrate statistics and monitoring capabilities"""
    print_section("7. Statistics and Monitoring")
    
    # Get comprehensive statistics
    stats = integrator.get_statistics()
    
    print("📊 Processing Statistics:")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Successful Requests: {stats['successful_requests']}")
    print(f"   Failed Requests: {stats['failed_requests']}")
    print(f"   Success Rate: {stats['success_rate']:.2%}")
    
    if stats['provider_usage']:
        print("\n🔧 Provider Usage:")
        for provider, count in stats['provider_usage'].items():
            print(f"   {provider}: {count} requests")
    
    if stats['fallback_usage']:
        print("\n🔄 Fallback Usage:")
        for provider, count in stats['fallback_usage'].items():
            print(f"   {provider}: {count} fallbacks")
    
    if stats['average_response_times']:
        print("\n⚡ Average Response Times:")
        for provider, time_ms in stats['average_response_times'].items():
            print(f"   {provider}: {time_ms*1000:.1f}ms")
    
    if stats['error_types']:
        print("\n❌ Error Types:")
        for error_type, count in stats['error_types'].items():
            print(f"   {error_type}: {count}")
    
    # Provider health summary
    print("\n💚 Provider Health Summary:")
    provider_status = stats['provider_status']
    
    healthy_providers = sum(1 for status in provider_status.values() if status['healthy'])
    total_providers = len(provider_status)
    
    print(f"   Healthy Providers: {healthy_providers}/{total_providers}")
    
    for name, status in provider_status.items():
        if status['enabled']:
            health_icon = "💚" if status['healthy'] else "💔"
            print(f"   {health_icon} {name}: {status['success_rate']:.2%} success rate")

async def demo_custom_provider(integrator):
    """Demonstrate adding custom provider"""
    print_section("8. Custom Provider Integration")
    
    print("🛠️  Adding custom provider...")
    
    # Create a simple custom provider (mock)
    class CustomMockProvider:
        def __init__(self, config):
            self.config = config
        
        async def process(self, text, task_type, **kwargs):
            await asyncio.sleep(0.05)  # Simulate processing
            
            if task_type == "ner":
                return {
                    "status": ProcessingStatus.SUCCESS,
                    "data": {
                        "entities": [
                            {"text": "Custom", "label": "ORG", "start": 0, "end": 6, "confidence": 0.9}
                        ]
                    },
                    "processing_time": 0.05,
                    "provider_used": ModelProvider.CUSTOM_API,
                    "model_id": "custom-model-v1",
                    "confidence_score": 0.9
                }
            
            return {
                "status": ProcessingStatus.FAILED,
                "error_message": "Unsupported task type",
                "provider_used": ModelProvider.CUSTOM_API
            }
        
        def is_healthy(self):
            return True
    
    # Create custom provider config
    custom_config = ProviderConfig(
        provider=ModelProvider.CUSTOM_API,
        model_id="custom-model-v1",
        priority=1,  # High priority
        enabled=True
    )
    
    # Add to integrator
    custom_provider = CustomMockProvider(custom_config)
    integrator.add_provider("custom_mock", custom_provider, custom_config)
    
    # Update fallback chain to include custom provider
    integrator.update_fallback_chain("ner", ["custom_mock", "spacy_lg", "spacy_md", "spacy_sm"])
    
    print("   ✅ Custom provider added successfully!")
    
    # Test with custom provider
    test_text = "Testing custom provider integration."
    result = await integrator.process(test_text, "ner")
    
    print_result(result, "ner", test_text)
    
    if result.model_id == "custom-model-v1":
        print("   🎯 Custom provider was used successfully!")

async def main():
    """Main demo function"""
    try:
        # Initialize integrator
        integrator = await demo_basic_processing()
        
        # Run all demo sections
        await demo_task_processing(integrator)
        await demo_fallback_behavior(integrator)
        await demo_provider_preferences(integrator)
        await demo_performance_comparison(integrator)
        await demo_concurrent_processing(integrator)
        await demo_statistics_and_monitoring(integrator)
        await demo_custom_provider(integrator)
        
        print_section("Demo Complete!")
        print("✅ Cloud-Local Model Integration demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Intelligent fallback between cloud and local models")
        print("• Provider health monitoring and selection")
        print("• Performance comparison across different models")
        print("• Concurrent processing capabilities")
        print("• Comprehensive statistics and monitoring")
        print("• Custom provider integration")
        print("• Quota and resource management")
        print("• Error handling and recovery")
        
        # Final cleanup
        await integrator.cleanup()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())