#!/usr/bin/env python3
"""
Demo script for LLM Provider Optimization System
Demonstrates A/B testing, cost analysis, performance benchmarking, and optimization recommendations
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_provider_optimization import (
    LLMProviderOptimizer, OptimizationStrategy, ABTestConfig, ABTestStatus,
    ProviderMetrics, CostAnalysis, PerformanceBenchmark, TaskType
)
from multi_llm_provider_system import MultiLLMProviderSystem, LLMProvider, LLMRequest

class LLMProviderOptimizationDemo:
    """Demo class for LLM provider optimization system"""
    
    def __init__(self):
        print("🚀 Initializing LLM Provider Optimization System...")
        self.provider_system = MultiLLMProviderSystem()
        self.optimizer = LLMProviderOptimizer(self.provider_system)
        print("✅ System initialized successfully!")
    
    def simulate_provider_usage(self):
        """Simulate provider usage to generate metrics"""
        print("\\n📊 Simulating provider usage...")
        
        # Simulate different provider performance characteristics
        provider_configs = {
            LLMProvider.OPENAI: {
                'latency_range': (1.0, 3.0),
                'success_rate': 0.95,
                'cost_per_token': 0.002,
                'quality_score': 4.2
            },
            LLMProvider.CLAUDE: {
                'latency_range': (0.8, 2.5),
                'success_rate': 0.97,
                'cost_per_token': 0.003,
                'quality_score': 4.5
            },
            LLMProvider.GEMINI: {
                'latency_range': (1.2, 4.0),
                'success_rate': 0.92,
                'cost_per_token': 0.0015,
                'quality_score': 4.0
            },
            LLMProvider.GROQ: {
                'latency_range': (0.3, 1.0),
                'success_rate': 0.90,
                'cost_per_token': 0.001,
                'quality_score': 3.8
            }
        }
        
        import random
        
        # Simulate 100 requests per provider
        for provider, config in provider_configs.items():
            print(f"   Simulating {provider.value} usage...")
            
            for _ in range(100):
                # Create mock response
                class MockResponse:
                    def __init__(self, success, latency, token_count, cost, quality_score):
                        self.success = success
                        self.latency = latency
                        self.token_count = token_count
                        self.cost = cost
                        self.quality_score = quality_score
                
                # Generate realistic response data
                success = random.random() < config['success_rate']
                latency = random.uniform(*config['latency_range'])
                token_count = random.randint(50, 200)
                cost = token_count * config['cost_per_token']
                quality_score = config['quality_score'] + random.uniform(-0.3, 0.3)
                
                response = MockResponse(success, latency, token_count, cost, quality_score)
                self.optimizer.update_provider_metrics(provider, response)
        
        print("✅ Provider usage simulation completed!")
    
    def demonstrate_ab_testing(self):
        """Demonstrate A/B testing functionality"""
        print("\\n🧪 Demonstrating A/B Testing...")
        
        # Create A/B test configuration
        ab_config = ABTestConfig(
            test_id="demo_ab_test_001",
            name="OpenAI vs Claude Performance Test",
            description="Compare OpenAI GPT-3.5 and Claude for text generation tasks",
            providers=[LLMProvider.OPENAI, LLMProvider.CLAUDE],
            traffic_split={LLMProvider.OPENAI: 0.6, LLMProvider.CLAUDE: 0.4},
            task_types=[TaskType.TEXT_GENERATION],
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=7),
            min_samples=50,
            confidence_level=0.95
        )
        
        # Create the A/B test
        test_id = self.optimizer.create_ab_test(ab_config)
        print(f"✅ Created A/B test: {test_id}")
        
        # Simulate test requests
        print("   Simulating A/B test requests...")
        
        for i in range(100):
            request = LLMRequest(
                prompt=f"Generate a summary for document {i}",
                task_type=TaskType.TEXT_GENERATION,
                max_tokens=150
            )
            
            # Check if request should use A/B test
            selected_provider = self.optimizer.should_use_ab_test(request)
            if selected_provider:
                print(f"     Request {i+1}: Using {selected_provider.value} (A/B test)")
            else:
                print(f"     Request {i+1}: Using default provider")
            
            # Only show first 5 for brevity
            if i >= 4:
                print(f"     ... (simulated {100-5} more requests)")
                break
        
        # Analyze A/B test results
        print("   Analyzing A/B test results...")
        results = self.optimizer.analyze_ab_test_results(test_id)
        
        if results:
            print("   📊 A/B Test Results:")
            for result in results:
                print(f"     {result.provider_type.value}:")
                print(f"       Sample Size: {result.sample_size}")
                print(f"       Success Rate: {result.metrics.success_rate:.1f}%")
                print(f"       Avg Latency: {result.metrics.average_latency:.2f}s")
                print(f"       Statistical Significance: {'✅' if result.statistical_significance else '❌'}")
                print(f"       P-Value: {result.p_value:.4f}")
        else:
            print("   ℹ️ Not enough data for statistical analysis yet")
    
    def demonstrate_cost_analysis(self):
        """Demonstrate cost analysis functionality"""
        print("\\n💰 Demonstrating Cost Analysis...")
        
        # Analyze costs over the last 30 days
        cost_analyses = self.optimizer.analyze_costs(period_days=30)
        
        if cost_analyses:
            print("   📊 Cost Analysis Results:")
            
            total_cost = sum(analysis.total_cost for analysis in cost_analyses)
            print(f"   Total Cost (30 days): ${total_cost:.2f}")
            
            for analysis in cost_analyses:
                print(f"\\n   {analysis.provider_type.value}:")
                print(f"     Total Cost: ${analysis.total_cost:.2f}")
                print(f"     Total Requests: {analysis.total_requests:,}")
                print(f"     Total Tokens: {analysis.total_tokens:,}")
                print(f"     Cost per Request: ${analysis.cost_per_request:.4f}")
                print(f"     Cost per Token: ${analysis.cost_per_token:.6f}")
                print(f"     Projected Monthly: ${analysis.projected_monthly_cost:.2f}")
        else:
            print("   ℹ️ No cost data available")
    
    def demonstrate_performance_benchmarking(self):
        """Demonstrate performance benchmarking"""
        print("\\n🏃 Demonstrating Performance Benchmarking...")
        
        # Run benchmarks for available providers
        available_providers = [LLMProvider.OPENAI, LLMProvider.CLAUDE, LLMProvider.GEMINI]
        task_types = [TaskType.TEXT_GENERATION, TaskType.SUMMARIZATION]
        
        print("   Running performance benchmarks...")
        benchmarks = self.optimizer.run_performance_benchmark(available_providers, task_types)
        
        if benchmarks:
            print("   📊 Benchmark Results:")
            
            for benchmark in benchmarks:
                print(f"\\n   {benchmark.provider_type.value} - {benchmark.task_type.value}:")
                print(f"     Overall Score: {benchmark.overall_score:.1f}/100")
                print(f"     Latency P50: {benchmark.latency_p50:.2f}s")
                print(f"     Latency P95: {benchmark.latency_p95:.2f}s")
                print(f"     Throughput: {benchmark.throughput_rps:.1f} req/s")
                print(f"     Quality Score: {benchmark.quality_score:.2f}/5.0")
                print(f"     Reliability: {benchmark.reliability_score:.1f}%")
                print(f"     Cost Efficiency: {benchmark.cost_efficiency_score:.2f}")
        else:
            print("   ℹ️ No benchmark data available")
    
    def demonstrate_optimization_strategies(self):
        """Demonstrate different optimization strategies"""
        print("\\n⚙️ Demonstrating Optimization Strategies...")
        
        strategies = [
            OptimizationStrategy.COST_OPTIMIZED,
            OptimizationStrategy.PERFORMANCE_OPTIMIZED,
            OptimizationStrategy.QUALITY_OPTIMIZED,
            OptimizationStrategy.BALANCED
        ]
        
        mock_request = LLMRequest(
            prompt="Test request for optimization",
            task_type=TaskType.TEXT_GENERATION,
            max_tokens=100
        )
        
        for strategy in strategies:
            self.optimizer.set_optimization_strategy(strategy)
            optimal_provider = self.optimizer.get_smart_provider_recommendation(mock_request)
            
            print(f"   {strategy.value.replace('_', ' ').title()}: {optimal_provider.value}")
    
    def demonstrate_provider_comparison(self):
        """Demonstrate provider comparison functionality"""
        print("\\n🔍 Demonstrating Provider Comparison...")
        
        comparison = self.optimizer.get_provider_comparison()
        
        if comparison['providers']:
            print("   📊 Provider Comparison:")
            
            # Display comparison table
            print(f"\\n   {'Provider':<12} {'Cost/Token':<12} {'Avg Latency':<12} {'Success Rate':<12} {'Quality':<8}")
            print("   " + "-" * 60)
            
            for provider_name, provider_data in comparison['providers'].items():
                metrics = provider_data['metrics']
                print(f"   {provider_name:<12} "
                      f"${metrics['cost_per_token']:<11.6f} "
                      f"{metrics['average_latency']:<11.2f}s "
                      f"{metrics['success_rate']:<11.1f}% "
                      f"{metrics['average_quality_score']:<7.2f}")
            
            print("\\n   💡 Recommendations:")
            for rec in comparison['recommendations']:
                print(f"     • {rec}")
        else:
            print("   ℹ️ No provider data available for comparison")
    
    def demonstrate_optimization_recommendations(self):
        """Demonstrate optimization recommendations"""
        print("\\n💡 Demonstrating Optimization Recommendations...")
        
        recommendations = self.optimizer.get_optimization_recommendations()
        
        if recommendations:
            print("   📋 Optimization Recommendations:")
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\\n   {i}. {rec.recommendation_type.replace('_', ' ').title()}")
                print(f"      Provider: {rec.provider_type.value}")
                if rec.task_type:
                    print(f"      Task Type: {rec.task_type.value}")
                print(f"      Description: {rec.description}")
                print(f"      Current Cost: ${rec.current_cost:.2f}")
                print(f"      Projected Cost: ${rec.projected_cost:.2f}")
                print(f"      Potential Savings: ${rec.potential_savings:.2f}")
                print(f"      Confidence: {rec.confidence_score:.1%}")
                
                print(f"      Action Items:")
                for action in rec.action_items:
                    print(f"        • {action}")
        else:
            print("   ✅ No optimization recommendations - system is performing well!")
    
    def demonstrate_metrics_export(self):
        """Demonstrate metrics export functionality"""
        print("\\n📤 Demonstrating Metrics Export...")
        
        # Export metrics as JSON
        exported_data = self.optimizer.export_metrics("json")
        
        print("   📊 Exported metrics summary:")
        import json
        data = json.loads(exported_data)
        
        print(f"     Timestamp: {data['timestamp']}")
        print(f"     Optimization Strategy: {data['optimization_strategy']}")
        print(f"     Providers Monitored: {len(data['provider_metrics'])}")
        print(f"     Active A/B Tests: {len(data['active_ab_tests'])}")
        
        # Save to file
        filename = f"optimization_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            f.write(exported_data)
        
        print(f"   💾 Metrics exported to: {filename}")
    
    def run_comprehensive_demo(self):
        """Run comprehensive demo of the optimization system"""
        print("🎯 LLM Provider Optimization System - Comprehensive Demo")
        print("=" * 70)
        
        try:
            # 1. Simulate provider usage
            self.simulate_provider_usage()
            
            # 2. Demonstrate A/B testing
            self.demonstrate_ab_testing()
            
            # 3. Demonstrate cost analysis
            self.demonstrate_cost_analysis()
            
            # 4. Demonstrate performance benchmarking
            self.demonstrate_performance_benchmarking()
            
            # 5. Demonstrate optimization strategies
            self.demonstrate_optimization_strategies()
            
            # 6. Demonstrate provider comparison
            self.demonstrate_provider_comparison()
            
            # 7. Demonstrate optimization recommendations
            self.demonstrate_optimization_recommendations()
            
            # 8. Demonstrate metrics export
            self.demonstrate_metrics_export()
            
            print("\\n🎉 Demo Completed Successfully!")
            print("=" * 70)
            
            print("\\n🚀 System Capabilities Demonstrated:")
            print("   ✅ Multi-provider metrics tracking")
            print("   ✅ A/B testing with statistical analysis")
            print("   ✅ Cost analysis and optimization")
            print("   ✅ Performance benchmarking")
            print("   ✅ Multiple optimization strategies")
            print("   ✅ Provider comparison and recommendations")
            print("   ✅ Automated optimization recommendations")
            print("   ✅ Metrics export and reporting")
            
            print("\\n💡 Next Steps:")
            print("   • Integrate with your LLM applications")
            print("   • Set up monitoring dashboards")
            print("   • Configure automated optimization rules")
            print("   • Schedule regular performance reviews")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main function"""
    try:
        demo = LLMProviderOptimizationDemo()
        demo.run_comprehensive_demo()
        
    except Exception as e:
        print(f"❌ Demo initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()