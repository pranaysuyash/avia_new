#!/usr/bin/env python3
"""
Demo script for Multi-LLM Provider System
Demonstrates the capabilities of managing multiple LLM providers with fallback,
cost optimization, and performance monitoring.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_llm_provider_system import (
    MultiLLMProviderSystem, LLMRequest, LLMProvider, TaskType,
    ProviderConfig, ProviderStats
)

class MultiLLMProviderDemo:
    """Demo class for multi-LLM provider system"""
    
    def __init__(self):
        print("🚀 Initializing Multi-LLM Provider System...")
        self.system = MultiLLMProviderSystem()
        print("✅ System initialized successfully!")
        
        # Demo requests for testing
        self.demo_requests = [
            LLMRequest(
                prompt="Explain the concept of machine learning in simple terms",
                task_type=TaskType.TEXT_GENERATION,
                max_tokens=200,
                temperature=0.7,
                system_message="You are an educational AI assistant"
            ),
            LLMRequest(
                prompt="Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term 'artificial intelligence' is often used to describe machines that mimic 'cognitive' functions that humans associate with the human mind, such as 'learning' and 'problem solving'.",
                task_type=TaskType.SUMMARIZATION,
                max_tokens=100,
                temperature=0.3
            ),
            LLMRequest(
                prompt="Extract entities from this text: Apple Inc. was founded by Steve Jobs, Steve Wozniak, and Ronald Wayne in April 1976 in Cupertino, California. The company went public on December 12, 1980.",
                task_type=TaskType.ENTITY_EXTRACTION,
                max_tokens=150,
                temperature=0.1
            ),
            LLMRequest(
                prompt="Classify the sentiment of this review: 'This product is absolutely amazing! I love everything about it and would definitely recommend it to others.'",
                task_type=TaskType.CLASSIFICATION,
                max_tokens=50,
                temperature=0.0
            ),
            LLMRequest(
                prompt="What are the main benefits of renewable energy?",
                task_type=TaskType.QUESTION_ANSWERING,
                max_tokens=200,
                temperature=0.5
            )
        ]
    
    def print_system_status(self):
        """Print current system status"""
        print("\n📊 System Status")
        print("=" * 50)
        
        available_providers = list(self.system.providers.keys())
        print(f"Available Providers: {len(available_providers)}")
        
        for provider in LLMProvider:
            status = "✅ Available" if provider in available_providers else "❌ Not Available"
            print(f"  {provider.value}: {status}")
        
        print(f"Cache Size: {len(self.system.request_cache)}")
        
        # Show fallback chains
        print(f"\n🔄 Fallback Chains:")
        for task_type, providers in self.system.fallback_chains.items():
            provider_names = [p.value for p in providers]
            print(f"  {task_type.value}: {' → '.join(provider_names)}")
    
    async def demo_basic_generation(self):
        """Demonstrate basic text generation with fallback"""
        print("\n🧪 Demo: Basic Generation with Fallback")
        print("=" * 50)
        
        for i, request in enumerate(self.demo_requests[:3], 1):
            print(f"\n📝 Request {i}: {request.task_type.value}")
            print(f"Prompt: {request.prompt[:60]}...")
            
            try:
                start_time = datetime.now()
                response = await self.system.generate(request)
                end_time = datetime.now()
                
                print(f"✅ Success with {response.provider.value}")
                print(f"   Model: {response.model}")
                print(f"   Content: {response.content[:100]}...")
                print(f"   Tokens: {response.tokens_used}")
                print(f"   Cost: ${response.cost:.4f}")
                print(f"   Latency: {response.latency:.2f}s")
                print(f"   Confidence: {response.confidence:.1%}")
                
            except Exception as e:
                print(f"❌ Failed: {e}")
    
    async def demo_provider_comparison(self):
        """Demonstrate provider comparison"""
        print("\n🔄 Demo: Provider Comparison")
        print("=" * 50)
        
        # Use a simple request for comparison
        request = LLMRequest(
            prompt="Write a haiku about artificial intelligence",
            task_type=TaskType.TEXT_GENERATION,
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"📝 Comparing providers for: {request.prompt}")
        
        try:
            # Get available providers for comparison
            available_providers = list(self.system.providers.keys())[:3]  # Limit to first 3
            
            results = await self.system.generate_with_comparison(request, available_providers)
            
            print(f"\n📊 Comparison Results ({len(results)} providers):")
            print("-" * 60)
            
            # Sort by cost for comparison
            sorted_results = sorted(results.items(), key=lambda x: x[1].cost)
            
            for provider, response in sorted_results:
                print(f"\n🤖 {provider.value}:")
                print(f"   Content: {response.content[:80]}...")
                print(f"   Tokens: {response.tokens_used}")
                print(f"   Cost: ${response.cost:.4f}")
                print(f"   Latency: {response.latency:.2f}s")
                print(f"   Confidence: {response.confidence:.1%}")
            
            # Find best provider for different criteria
            cheapest = min(sorted_results, key=lambda x: x[1].cost)
            fastest = min(sorted_results, key=lambda x: x[1].latency)
            most_confident = max(sorted_results, key=lambda x: x[1].confidence)
            
            print(f"\n🏆 Best Providers:")
            print(f"   💰 Cheapest: {cheapest[0].value} (${cheapest[1].cost:.4f})")
            print(f"   ⚡ Fastest: {fastest[0].value} ({fastest[1].latency:.2f}s)")
            print(f"   🎯 Most Confident: {most_confident[0].value} ({most_confident[1].confidence:.1%})")
            
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
    
    async def demo_task_optimization(self):
        """Demonstrate task-specific provider optimization"""
        print("\n🎯 Demo: Task-Specific Optimization")
        print("=" * 50)
        
        for task_type in [TaskType.SUMMARIZATION, TaskType.ENTITY_EXTRACTION, TaskType.CLASSIFICATION]:
            best_provider = self.system.get_best_provider_for_task(task_type)
            
            if best_provider:
                print(f"📋 {task_type.value}: Best provider is {best_provider.value}")
            else:
                print(f"📋 {task_type.value}: No provider available")
    
    def demo_caching(self):
        """Demonstrate response caching"""
        print("\n💾 Demo: Response Caching")
        print("=" * 50)
        
        # Create a simple request
        request = LLMRequest(
            prompt="What is the capital of France?",
            task_type=TaskType.QUESTION_ANSWERING,
            max_tokens=50
        )
        
        print(f"📝 Testing cache with: {request.prompt}")
        
        async def test_cache():
            # First request (should hit provider)
            print("\n🔄 First request (cache miss):")
            start_time = datetime.now()
            response1 = await self.system.generate(request, use_cache=True)
            end_time = datetime.now()
            first_latency = (end_time - start_time).total_seconds()
            
            print(f"   Provider: {response1.provider.value}")
            print(f"   Latency: {first_latency:.2f}s")
            print(f"   Cache size: {len(self.system.request_cache)}")
            
            # Second request (should hit cache)
            print("\n⚡ Second request (cache hit):")
            start_time = datetime.now()
            response2 = await self.system.generate(request, use_cache=True)
            end_time = datetime.now()
            second_latency = (end_time - start_time).total_seconds()
            
            print(f"   Provider: {response2.provider.value}")
            print(f"   Latency: {second_latency:.2f}s")
            print(f"   Cache size: {len(self.system.request_cache)}")
            print(f"   Speed improvement: {(first_latency / second_latency):.1f}x faster")
        
        asyncio.run(test_cache())
    
    def demo_statistics(self):
        """Demonstrate statistics and monitoring"""
        print("\n📊 Demo: Statistics and Monitoring")
        print("=" * 50)
        
        stats = self.system.get_provider_stats()
        
        if not stats:
            print("No statistics available yet. Run some requests first.")
            return
        
        print("Provider Statistics:")
        print("-" * 60)
        
        for provider, stat in stats.items():
            print(f"\n🤖 {provider.value}:")
            print(f"   Total Requests: {stat.total_requests}")
            print(f"   Success Rate: {stat.success_rate:.1%}")
            print(f"   Total Tokens: {stat.total_tokens}")
            print(f"   Total Cost: ${stat.total_cost:.4f}")
            print(f"   Average Latency: {stat.average_latency:.2f}s")
            print(f"   Last Used: {stat.last_used.strftime('%H:%M:%S') if stat.last_used else 'Never'}")
        
        # Overall statistics
        total_requests = sum(stat.total_requests for stat in stats.values())
        total_cost = sum(stat.total_cost for stat in stats.values())
        total_tokens = sum(stat.total_tokens for stat in stats.values())
        avg_success_rate = sum(stat.success_rate for stat in stats.values()) / len(stats) if stats else 0
        
        print(f"\n🎯 Overall Statistics:")
        print(f"   Total Requests: {total_requests}")
        print(f"   Total Cost: ${total_cost:.4f}")
        print(f"   Total Tokens: {total_tokens}")
        print(f"   Average Success Rate: {avg_success_rate:.1%}")
    
    def demo_configuration(self):
        """Demonstrate configuration management"""
        print("\n⚙️ Demo: Configuration Management")
        print("=" * 50)
        
        # Show current configurations
        print("Current Provider Configurations:")
        print("-" * 40)
        
        for provider, config in self.system.configs.items():
            print(f"\n🔧 {provider.value}:")
            print(f"   Enabled: {config.enabled}")
            print(f"   Model: {config.model}")
            print(f"   Priority: {config.priority}")
            print(f"   Cost per Token: ${config.cost_per_token:.4f}")
            print(f"   Rate Limit: {config.rate_limit} req/min")
            print(f"   Timeout: {config.timeout}s")
        
        # Demonstrate adding a custom configuration
        print(f"\n🔄 Adding custom configuration...")
        
        custom_config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key="demo_key",
            model="gpt-4",
            priority=1,
            cost_per_token=0.03,
            rate_limit=50,
            timeout=60,
            enabled=False  # Disabled for demo
        )
        
        self.system.add_provider_config(custom_config)
        print(f"✅ Custom configuration added for {custom_config.provider.value}")
    
    def save_demo_results(self):
        """Save demo results to file"""
        print("\n💾 Saving Demo Results")
        print("=" * 50)
        
        try:
            # Export comprehensive statistics
            export_data = self.system.export_stats()
            
            # Add demo metadata
            export_data['demo_metadata'] = {
                'demo_run_time': datetime.now().isoformat(),
                'demo_requests_count': len(self.demo_requests),
                'system_version': '1.0.0'
            }
            
            # Save to file
            filename = f"multi_llm_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Demo results saved to: {filename}")
            
            # Print summary
            print(f"\n📋 Export Summary:")
            print(f"   Providers: {len(export_data.get('provider_stats', {}))}")
            print(f"   Cache Size: {export_data.get('cache_size', 0)}")
            print(f"   Available Providers: {len(export_data.get('available_providers', []))}")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demo of the multi-LLM provider system"""
        print("🎯 Starting Comprehensive Multi-LLM Provider Demo")
        print("=" * 60)
        
        # 1. System Status
        self.print_system_status()
        
        # 2. Basic Generation Demo
        await self.demo_basic_generation()
        
        # 3. Provider Comparison Demo
        await self.demo_provider_comparison()
        
        # 4. Task Optimization Demo
        await self.demo_task_optimization()
        
        # 5. Caching Demo
        self.demo_caching()
        
        # 6. Statistics Demo
        self.demo_statistics()
        
        # 7. Configuration Demo
        self.demo_configuration()
        
        # 8. Save Results
        self.save_demo_results()
        
        print("\n🎉 Demo Completed Successfully!")
        print("=" * 60)
        
        print(f"✅ Demonstrated multi-LLM provider capabilities:")
        print(f"   • Provider fallback and redundancy")
        print(f"   • Cost and performance optimization")
        print(f"   • Response caching for efficiency")
        print(f"   • Comprehensive monitoring and statistics")
        print(f"   • Task-specific provider selection")
        print(f"   • Configuration management")
        print(f"   • Provider comparison and benchmarking")
        
        return True

async def main():
    """Main function"""
    try:
        demo = MultiLLMProviderDemo()
        success = await demo.run_comprehensive_demo()
        
        if success:
            print("\n🎯 Demo completed successfully!")
            print("Check the generated JSON file for detailed results.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())