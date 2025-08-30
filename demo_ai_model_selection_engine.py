"""
Demo Script for AI Model Selection Engine

Demonstrates intelligent model selection capabilities with various scenarios
including performance optimization, cost management, and fallback strategies.
"""

import asyncio
import time
import random
from datetime import datetime
from typing import Dict, List

from ai_model_selection_engine import (
    ModelSelectionEngine, AIRequest, UserPreferences, RequestContext,
    ModelCapability, ModelProvider, SelectionCriteria, AIModel, ModelMetrics
)

class ModelSelectionDemo:
    """Demonstration of AI Model Selection Engine capabilities"""
    
    def __init__(self):
        self.engine = ModelSelectionEngine("demo_model_selection.db")
        self.demo_results = []
    
    async def run_all_demos(self):
        """Run all demonstration scenarios"""
        print("🤖 AI Model Selection Engine Demo")
        print("=" * 50)
        
        await self.demo_basic_selection()
        await self.demo_preference_based_selection()
        await self.demo_privacy_focused_selection()
        await self.demo_cost_optimization()
        await self.demo_speed_optimization()
        await self.demo_quality_optimization()
        await self.demo_fallback_strategies()
        await self.demo_performance_learning()
        await self.demo_concurrent_selections()
        await self.demo_custom_model_integration()
        
        self.print_summary()
    
    async def demo_basic_selection(self):
        """Demonstrate basic model selection"""
        print("\n📋 Demo 1: Basic Model Selection")
        print("-" * 30)
        
        # Create standard request
        user_prefs = UserPreferences(
            quality_threshold=0.8,
            max_latency_ms=5000.0,
            max_cost_per_request=0.05
        )
        
        context = RequestContext(
            user_id="demo_user_1",
            request_type=ModelCapability.TRANSCRIPTION,
            content_size=2048,
            urgency="normal",
            quality_requirement="standard"
        )
        
        request = AIRequest(
            id="demo_basic_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="sample_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request)
        
        print(f"✅ Selected Model: {selection.primary_model.name}")
        print(f"   Provider: {selection.primary_model.provider.value}")
        print(f"   Confidence: {selection.confidence_score:.3f}")
        print(f"   Estimated Cost: ${selection.estimated_cost:.4f}")
        print(f"   Estimated Latency: {selection.estimated_latency:.0f}ms")
        print(f"   Reasoning: {selection.selection_reasoning}")
        print(f"   Fallback Options: {len(selection.fallback_models)} models")
        
        self.demo_results.append({
            "demo": "Basic Selection",
            "model": selection.primary_model.name,
            "confidence": selection.confidence_score,
            "cost": selection.estimated_cost,
            "latency": selection.estimated_latency
        })
    
    async def demo_preference_based_selection(self):
        """Demonstrate preference-based model selection"""
        print("\n🎯 Demo 2: Preference-Based Selection")
        print("-" * 35)
        
        # Test different provider preferences
        providers_to_test = [
            ([ModelProvider.OPENAI], "OpenAI Preferred"),
            ([ModelProvider.LOCAL_WHISPER, ModelProvider.LOCAL_SPACY], "Local Models Preferred"),
            ([ModelProvider.ELEVENLABS], "ElevenLabs Preferred")
        ]
        
        for preferred_providers, description in providers_to_test:
            user_prefs = UserPreferences(
                preferred_providers=preferred_providers,
                quality_threshold=0.75,
                max_latency_ms=4000.0,
                max_cost_per_request=0.03
            )
            
            context = RequestContext(
                user_id="demo_user_2",
                request_type=ModelCapability.TRANSCRIPTION,
                urgency="normal",
                quality_requirement="standard"
            )
            
            request = AIRequest(
                id=f"demo_pref_{len(preferred_providers)}",
                capability=ModelCapability.TRANSCRIPTION,
                content="preference_test.wav",
                context=context,
                preferences=user_prefs
            )
            
            selection = await self.engine.select_model(request)
            
            print(f"\n{description}:")
            print(f"  Selected: {selection.primary_model.name} ({selection.primary_model.provider.value})")
            print(f"  Matches Preference: {selection.primary_model.provider in preferred_providers}")
            print(f"  Confidence: {selection.confidence_score:.3f}")
    
    async def demo_privacy_focused_selection(self):
        """Demonstrate privacy-focused model selection"""
        print("\n🔒 Demo 3: Privacy-Focused Selection")
        print("-" * 35)
        
        # Privacy required scenario
        user_prefs = UserPreferences(
            privacy_required=True,
            quality_threshold=0.7,
            max_latency_ms=10000.0,  # Allow higher latency for privacy
            max_cost_per_request=0.0  # Prefer free local models
        )
        
        context = RequestContext(
            user_id="privacy_user",
            request_type=ModelCapability.TRANSCRIPTION,
            content_size=4096,
            urgency="low",
            quality_requirement="standard"
        )
        
        request = AIRequest(
            id="demo_privacy_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="sensitive_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request)
        
        local_providers = [ModelProvider.LOCAL_WHISPER, ModelProvider.LOCAL_SPACY]
        is_local = selection.primary_model.provider in local_providers
        
        print(f"✅ Privacy-Focused Selection:")
        print(f"   Selected: {selection.primary_model.name}")
        print(f"   Provider: {selection.primary_model.provider.value}")
        print(f"   Is Local Model: {is_local}")
        print(f"   Cost: ${selection.estimated_cost:.4f} (Free: {selection.estimated_cost == 0.0})")
        print(f"   Privacy Score: High" if is_local else "   Privacy Score: Standard")
    
    async def demo_cost_optimization(self):
        """Demonstrate cost-optimized model selection"""
        print("\n💰 Demo 4: Cost Optimization")
        print("-" * 28)
        
        # Cost-sensitive scenario
        user_prefs = UserPreferences(
            quality_threshold=0.75,
            max_latency_ms=8000.0,
            max_cost_per_request=0.005  # Very low cost limit
        )
        
        context = RequestContext(
            user_id="budget_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="low",
            quality_requirement="basic"
        )
        
        # Custom weights heavily favoring cost
        cost_weights = {
            SelectionCriteria.COST: 0.6,
            SelectionCriteria.QUALITY: 0.2,
            SelectionCriteria.SPEED: 0.1,
            SelectionCriteria.AVAILABILITY: 0.05,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        request = AIRequest(
            id="demo_cost_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="budget_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request, cost_weights)
        
        print(f"✅ Cost-Optimized Selection:")
        print(f"   Selected: {selection.primary_model.name}")
        print(f"   Cost: ${selection.estimated_cost:.4f}")
        print(f"   Within Budget: {selection.estimated_cost <= user_prefs.max_cost_per_request}")
        print(f"   Quality: {selection.primary_model.metrics.accuracy_score:.3f}")
        print(f"   Cost Efficiency: {selection.primary_model.metrics.accuracy_score / max(selection.estimated_cost, 0.001):.1f}")
    
    async def demo_speed_optimization(self):
        """Demonstrate speed-optimized model selection"""
        print("\n⚡ Demo 5: Speed Optimization")
        print("-" * 28)
        
        # Speed-critical scenario
        user_prefs = UserPreferences(
            quality_threshold=0.7,
            max_latency_ms=2000.0,  # Very strict latency requirement
            max_cost_per_request=0.1
        )
        
        context = RequestContext(
            user_id="speed_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="high",  # High urgency
            quality_requirement="standard"
        )
        
        # Custom weights heavily favoring speed
        speed_weights = {
            SelectionCriteria.SPEED: 0.6,
            SelectionCriteria.AVAILABILITY: 0.2,
            SelectionCriteria.QUALITY: 0.1,
            SelectionCriteria.COST: 0.05,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        request = AIRequest(
            id="demo_speed_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="urgent_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request, speed_weights)
        
        print(f"✅ Speed-Optimized Selection:")
        print(f"   Selected: {selection.primary_model.name}")
        print(f"   Latency: {selection.estimated_latency:.0f}ms")
        print(f"   Meets Requirement: {selection.estimated_latency <= user_prefs.max_latency_ms}")
        print(f"   Throughput: {selection.primary_model.metrics.throughput_rps:.1f} req/sec")
        print(f"   Speed Score: {1.0 - (selection.estimated_latency / user_prefs.max_latency_ms):.3f}")
    
    async def demo_quality_optimization(self):
        """Demonstrate quality-optimized model selection"""
        print("\n🎯 Demo 6: Quality Optimization")
        print("-" * 30)
        
        # Quality-critical scenario
        user_prefs = UserPreferences(
            quality_threshold=0.9,  # Very high quality requirement
            max_latency_ms=15000.0,  # Allow higher latency for quality
            max_cost_per_request=0.05
        )
        
        context = RequestContext(
            user_id="quality_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="low",
            quality_requirement="high"  # High quality requirement
        )
        
        # Custom weights heavily favoring quality
        quality_weights = {
            SelectionCriteria.QUALITY: 0.7,
            SelectionCriteria.AVAILABILITY: 0.15,
            SelectionCriteria.SPEED: 0.05,
            SelectionCriteria.COST: 0.05,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        request = AIRequest(
            id="demo_quality_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="important_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request, quality_weights)
        
        print(f"✅ Quality-Optimized Selection:")
        print(f"   Selected: {selection.primary_model.name}")
        print(f"   Accuracy: {selection.primary_model.metrics.accuracy_score:.3f}")
        print(f"   Meets Threshold: {selection.primary_model.metrics.accuracy_score >= user_prefs.quality_threshold}")
        print(f"   Error Rate: {selection.primary_model.metrics.error_rate:.3f}")
        print(f"   Quality Rank: {self.get_quality_rank(selection.primary_model)}")
    
    async def demo_fallback_strategies(self):
        """Demonstrate fallback model strategies"""
        print("\n🔄 Demo 7: Fallback Strategies")
        print("-" * 30)
        
        # Get a primary model
        user_prefs = UserPreferences()
        context = RequestContext(
            user_id="fallback_user",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id="demo_fallback_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="fallback_test.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request)
        primary_model = selection.primary_model
        
        print(f"Primary Model: {primary_model.name}")
        print(f"Fallback Models:")
        
        for i, fallback in enumerate(selection.fallback_models, 1):
            print(f"  {i}. {fallback.name} ({fallback.provider.value})")
            print(f"     Latency: {fallback.metrics.latency_ms:.0f}ms")
            print(f"     Accuracy: {fallback.metrics.accuracy_score:.3f}")
            print(f"     Cost: ${fallback.metrics.cost_per_request:.4f}")
        
        # Simulate primary model failure and fallback
        print(f"\n🚨 Simulating {primary_model.name} failure...")
        
        if selection.fallback_models:
            fallback_model = selection.fallback_models[0]
            print(f"✅ Falling back to: {fallback_model.name}")
            print(f"   Fallback Latency: {fallback_model.metrics.latency_ms:.0f}ms")
            print(f"   Fallback Quality: {fallback_model.metrics.accuracy_score:.3f}")
        else:
            print("❌ No fallback models available!")
    
    async def demo_performance_learning(self):
        """Demonstrate performance learning and adaptation"""
        print("\n📈 Demo 8: Performance Learning")
        print("-" * 32)
        
        # Select a model and simulate usage
        user_prefs = UserPreferences()
        context = RequestContext(
            user_id="learning_user",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id="demo_learning_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="learning_test.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request)
        model = selection.primary_model
        
        print(f"Selected Model: {model.name}")
        print(f"Initial Metrics:")
        print(f"  Latency: {model.metrics.latency_ms:.0f}ms")
        print(f"  Cost: ${model.metrics.cost_per_request:.4f}")
        print(f"  Error Rate: {model.metrics.error_rate:.3f}")
        
        # Simulate multiple usage scenarios with varying performance
        print(f"\n🔄 Simulating usage and learning...")
        
        scenarios = [
            (1800.0, 0.007, True, "Good performance"),
            (2500.0, 0.008, True, "Slower but successful"),
            (1200.0, 0.006, True, "Excellent performance"),
            (3000.0, 0.009, False, "Slow with failure"),
            (1900.0, 0.007, True, "Back to normal")
        ]
        
        for i, (latency, cost, success, description) in enumerate(scenarios, 1):
            await self.engine.update_model_metrics(model.id, latency, cost, success)
            
            updated_model = self.engine.models[model.id]
            print(f"  Update {i}: {description}")
            print(f"    Actual: {latency:.0f}ms, ${cost:.4f}, Success: {success}")
            print(f"    Updated Avg: {updated_model.metrics.latency_ms:.0f}ms, "
                  f"${updated_model.metrics.cost_per_request:.4f}, "
                  f"Error Rate: {updated_model.metrics.error_rate:.3f}")
        
        print(f"\n📊 Learning Summary:")
        final_model = self.engine.models[model.id]
        print(f"  Final Latency: {final_model.metrics.latency_ms:.0f}ms "
              f"(Change: {final_model.metrics.latency_ms - model.metrics.latency_ms:+.0f}ms)")
        print(f"  Final Cost: ${final_model.metrics.cost_per_request:.4f} "
              f"(Change: ${final_model.metrics.cost_per_request - model.metrics.cost_per_request:+.4f})")
        print(f"  Final Error Rate: {final_model.metrics.error_rate:.3f}")
    
    async def demo_concurrent_selections(self):
        """Demonstrate concurrent model selections"""
        print("\n🔀 Demo 9: Concurrent Selections")
        print("-" * 31)
        
        # Create multiple concurrent requests
        requests = []
        for i in range(5):
            user_prefs = UserPreferences(
                quality_threshold=0.7 + (i * 0.05),
                max_latency_ms=2000 + (i * 1000),
                max_cost_per_request=0.01 + (i * 0.01)
            )
            
            context = RequestContext(
                user_id=f"concurrent_user_{i}",
                request_type=ModelCapability.TRANSCRIPTION,
                urgency=["low", "normal", "high"][i % 3],
                quality_requirement=["basic", "standard", "high"][i % 3]
            )
            
            request = AIRequest(
                id=f"demo_concurrent_{i}",
                capability=ModelCapability.TRANSCRIPTION,
                content=f"concurrent_audio_{i}.wav",
                context=context,
                preferences=user_prefs
            )
            requests.append(request)
        
        print(f"Processing {len(requests)} concurrent requests...")
        
        start_time = time.time()
        
        # Process all requests concurrently
        tasks = [self.engine.select_model(req) for req in requests]
        selections = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Completed in {total_time:.3f} seconds")
        print(f"Average time per selection: {total_time / len(requests):.3f} seconds")
        
        # Show results
        for i, (request, selection) in enumerate(zip(requests, selections)):
            print(f"  Request {i+1}: {selection.primary_model.name} "
                  f"(Score: {selection.confidence_score:.3f})")
    
    async def demo_custom_model_integration(self):
        """Demonstrate custom model integration"""
        print("\n🔧 Demo 10: Custom Model Integration")
        print("-" * 37)
        
        # Add a custom model
        custom_model = AIModel(
            id="custom_demo_model",
            name="Custom Demo Model",
            provider=ModelProvider.CUSTOM,
            capabilities=[ModelCapability.TRANSCRIPTION, ModelCapability.TEXT_GENERATION],
            metrics=ModelMetrics(
                latency_ms=1500.0,
                accuracy_score=0.88,
                cost_per_request=0.003,
                availability_percent=98.0,
                throughput_rps=12.0,
                error_rate=0.02
            ),
            priority=1
        )
        
        # Register the custom model
        self.engine.models[custom_model.id] = custom_model
        
        print(f"✅ Registered Custom Model: {custom_model.name}")
        print(f"   Capabilities: {[cap.value for cap in custom_model.capabilities]}")
        print(f"   Latency: {custom_model.metrics.latency_ms:.0f}ms")
        print(f"   Accuracy: {custom_model.metrics.accuracy_score:.3f}")
        print(f"   Cost: ${custom_model.metrics.cost_per_request:.4f}")
        
        # Test selection with custom model
        user_prefs = UserPreferences(
            quality_threshold=0.85,
            max_latency_ms=2000.0,
            max_cost_per_request=0.01
        )
        
        context = RequestContext(
            user_id="custom_user",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id="demo_custom_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="custom_test.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await self.engine.select_model(request)
        
        print(f"\n🎯 Selection Result:")
        print(f"   Selected: {selection.primary_model.name}")
        print(f"   Is Custom Model: {selection.primary_model.id == custom_model.id}")
        print(f"   Confidence: {selection.confidence_score:.3f}")
        
        if selection.primary_model.id == custom_model.id:
            print("✅ Custom model was selected!")
        else:
            print(f"ℹ️  Alternative model selected: {selection.primary_model.name}")
    
    def get_quality_rank(self, model: AIModel) -> str:
        """Get quality ranking for a model"""
        accuracy = model.metrics.accuracy_score
        if accuracy >= 0.95:
            return "Excellent"
        elif accuracy >= 0.90:
            return "Very Good"
        elif accuracy >= 0.85:
            return "Good"
        elif accuracy >= 0.80:
            return "Fair"
        else:
            return "Basic"
    
    def print_summary(self):
        """Print demo summary"""
        print("\n" + "=" * 50)
        print("📊 Demo Summary")
        print("=" * 50)
        
        if self.demo_results:
            print(f"Total Demonstrations: {len(self.demo_results)}")
            
            # Calculate averages
            avg_confidence = sum(r["confidence"] for r in self.demo_results) / len(self.demo_results)
            avg_cost = sum(r["cost"] for r in self.demo_results) / len(self.demo_results)
            avg_latency = sum(r["latency"] for r in self.demo_results) / len(self.demo_results)
            
            print(f"Average Confidence Score: {avg_confidence:.3f}")
            print(f"Average Cost: ${avg_cost:.4f}")
            print(f"Average Latency: {avg_latency:.0f}ms")
            
            # Model usage statistics
            model_usage = {}
            for result in self.demo_results:
                model = result["model"]
                model_usage[model] = model_usage.get(model, 0) + 1
            
            print(f"\nModel Usage:")
            for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
                print(f"  {model}: {count} selections")
        
        # Performance summary
        summary = self.engine.get_model_performance_summary()
        print(f"\nRegistered Models: {len(summary)}")
        
        available_models = sum(1 for info in summary.values() if info['is_available'])
        print(f"Available Models: {available_models}")
        
        print(f"\n✅ All demonstrations completed successfully!")
        print("The AI Model Selection Engine demonstrated:")
        print("  • Intelligent multi-criteria model selection")
        print("  • User preference and context awareness")
        print("  • Privacy and security considerations")
        print("  • Cost and performance optimization")
        print("  • Automatic fallback strategies")
        print("  • Performance learning and adaptation")
        print("  • Concurrent request handling")
        print("  • Custom model integration")

async def main():
    """Run the complete demonstration"""
    demo = ModelSelectionDemo()
    await demo.run_all_demos()

if __name__ == "__main__":
    asyncio.run(main())