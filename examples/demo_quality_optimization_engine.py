#!/usr/bin/env python3
"""
Demo: Quality Optimization Engine - Intent-First Transformation
Demonstrates the transformation from technical provider management to quality-focused user experience
"""

import asyncio
from datetime import datetime
from quality_optimization_engine import (
    QualityOptimizationEngine, QualityTier, TaskComplexity, UserFeedback
)
from multi_llm_provider_system import LLMRequest, TaskType, LLMProvider

async def demo_quality_transformation():
    """Demonstrate the Intent-First transformation"""
    
    print("🎯 QUALITY OPTIMIZATION ENGINE DEMO")
    print("=" * 70)
    print("Intent-First Transformation: Technical Provider Management → Quality-Focused Experience")
    print("=" * 70)
    
    engine = QualityOptimizationEngine()
    
    # Demo 1: Legal Document Analysis Request
    print("\n📋 DEMO 1: LEGAL DOCUMENT ANALYSIS")
    print("-" * 50)
    
    legal_request = LLMRequest(
        prompt="Analyze this contract clause for potential legal risks and provide recommendations: 'The contractor shall indemnify and hold harmless the client from any claims arising from the performance of services.'",
        task_type=TaskType.ANALYSIS,
        max_tokens=800,
        temperature=0.3
    )
    
    print(f"📝 Request: Legal contract analysis")
    print(f"🎯 Task Type: {legal_request.task_type.value}")
    print(f"📏 Complexity: High (legal analysis)")
    
    # Get recommendation
    recommendation = await engine.get_optimal_provider_recommendation(
        legal_request, "legal_user_001", "balanced"
    )
    
    print(f"\n✅ RECOMMENDATION:")
    print(f"   🎯 Provider: {recommendation.recommended_provider.value.upper()}")
    print(f"   ⭐ Quality Tier: {recommendation.quality_tier.value.upper()}")
    print(f"   📊 Quality Score: {recommendation.quality_score:.1%}")
    print(f"   💰 Cost Estimate: ${recommendation.cost_estimate:.3f}")
    print(f"   🎯 Confidence: {recommendation.confidence:.1%}")
    print(f"   💡 Reasoning: {recommendation.reasoning}")
    
    if recommendation.alternatives:
        print(f"\n🔄 ALTERNATIVES:")
        for i, alt in enumerate(recommendation.alternatives[:2], 1):
            print(f"   {i}. {alt.provider.value}: {alt.quality_score:.1%} quality, ${alt.cost_estimate:.3f}")
            print(f"      📝 {alt.description}")
            if alt.pros:
                print(f"      ✅ Pros: {', '.join(alt.pros[:2])}")
            if alt.cons:
                print(f"      ❌ Cons: {', '.join(alt.cons[:2])}")
    
    # Demo 2: Simple Translation Request
    print(f"\n📋 DEMO 2: SIMPLE TRANSLATION TASK")
    print("-" * 50)
    
    translation_request = LLMRequest(
        prompt="Translate 'Hello, how are you?' to Spanish",
        task_type=TaskType.TRANSLATION,
        max_tokens=50,
        temperature=0.1
    )
    
    print(f"📝 Request: Simple translation")
    print(f"🎯 Task Type: {translation_request.task_type.value}")
    print(f"📏 Complexity: Simple (basic translation)")
    
    translation_rec = await engine.get_optimal_provider_recommendation(
        translation_request, "casual_user_002", "economy"
    )
    
    print(f"\n✅ RECOMMENDATION:")
    print(f"   🎯 Provider: {translation_rec.recommended_provider.value.upper()}")
    print(f"   ⭐ Quality Tier: {translation_rec.quality_tier.value.upper()}")
    print(f"   📊 Quality Score: {translation_rec.quality_score:.1%}")
    print(f"   💰 Cost Estimate: ${translation_rec.cost_estimate:.3f}")
    print(f"   💡 Reasoning: {translation_rec.reasoning}")
    
    # Demo 3: Provider Quality Comparison
    print(f"\n📊 DEMO 3: PROVIDER QUALITY COMPARISON")
    print("-" * 50)
    
    code_request = LLMRequest(
        prompt="Write a Python function to calculate the Fibonacci sequence",
        task_type=TaskType.CODE_GENERATION,
        max_tokens=300
    )
    
    print(f"📝 Request: Code generation task")
    comparison = await engine.get_quality_comparison(code_request)
    
    print(f"\n📊 QUALITY COMPARISON RESULTS:")
    print(f"{'Provider':<12} {'Quality':<8} {'Accuracy':<9} {'Speed':<8} {'Cost':<8} {'Recommendation'}")
    print("-" * 80)
    
    for provider, metrics in comparison.items():
        print(f"{provider.value:<12} "
              f"{metrics['quality_score']:.1%}    "
              f"{metrics['accuracy']:.1%}     "
              f"{metrics['speed_score']:.1%}    "
              f"${metrics['cost_estimate']:.3f}   "
              f"{metrics['recommendation'][:30]}...")
    
    # Demo 4: User Feedback and Learning
    print(f"\n💬 DEMO 4: USER FEEDBACK & LEARNING")
    print("-" * 50)
    
    # Simulate user feedback
    feedback_scenarios = [
        UserFeedback(
            user_id="power_user_003",
            provider=LLMProvider.CLAUDE,
            task_type=TaskType.ANALYSIS,
            quality_rating=4.8,
            speed_rating=3.2,
            satisfaction_rating=4.5,
            text_feedback="Excellent analysis quality, but a bit slow"
        ),
        UserFeedback(
            user_id="power_user_003", 
            provider=LLMProvider.GROQ,
            task_type=TaskType.CODE_GENERATION,
            quality_rating=4.2,
            speed_rating=4.9,
            satisfaction_rating=4.6,
            text_feedback="Very fast and good code quality"
        ),
        UserFeedback(
            user_id="power_user_003",
            provider=LLMProvider.OPENAI,
            task_type=TaskType.SUMMARIZATION,
            quality_rating=4.5,
            speed_rating=4.0,
            satisfaction_rating=4.3,
            text_feedback="Reliable and well-balanced performance"
        )
    ]
    
    print("📝 Recording user feedback...")
    for feedback in feedback_scenarios:
        await engine.record_user_feedback(feedback)
        print(f"   ✅ {feedback.provider.value}: Quality {feedback.quality_rating}/5, "
              f"Speed {feedback.speed_rating}/5, Satisfaction {feedback.satisfaction_rating}/5")
    
    # Get personalized insights
    print(f"\n📈 PERSONALIZED INSIGHTS:")
    insights = await engine.get_user_quality_insights("power_user_003")
    
    print(f"   📊 Total Interactions: {insights['total_interactions']}")
    print(f"   ⭐ Average Satisfaction: {insights['average_satisfaction']:.1f}/5.0")
    print(f"   🎯 Average Quality Rating: {insights['average_quality_rating']:.1f}/5.0")
    
    if insights['preferred_providers']:
        print(f"\n   🏆 PREFERRED PROVIDERS:")
        for provider_info in insights['preferred_providers']:
            print(f"      • {provider_info['provider'].title()}: "
                  f"{provider_info['satisfaction']:.1f}/5.0 satisfaction "
                  f"({provider_info['usage_count']} uses)")
    
    if insights['recommendations']:
        print(f"\n   💡 PERSONALIZED RECOMMENDATIONS:")
        for rec in insights['recommendations']:
            print(f"      • {rec}")

async def demo_before_after_comparison():
    """Demonstrate before vs after transformation"""
    
    print(f"\n🔄 BEFORE vs AFTER TRANSFORMATION")
    print("=" * 70)
    
    print("❌ BEFORE (Technical Provider Management):")
    print("   • Provider selection based on availability and load balancing")
    print("   • Cost optimization without quality consideration")
    print("   • No user transparency in provider selection")
    print("   • Generic fallback mechanisms")
    print("   • No learning from user preferences")
    print("   • Technical metrics: 'Using OpenAI (available, 45ms latency)'")
    
    print("\n✅ AFTER (Quality-Focused User Experience):")
    print("   • Provider selection optimized for task-specific quality")
    print("   • Transparent cost-quality trade-offs")
    print("   • Clear reasoning for recommendations")
    print("   • Personalized suggestions based on user feedback")
    print("   • Continuous learning and improvement")
    print("   • User-friendly messaging: 'Using Claude for legal analysis (best accuracy for legal tasks)'")
    
    print(f"\n🎯 TRANSFORMATION BENEFITS:")
    print("   ✨ User Benefits:")
    print("      • Clear understanding of why a provider was chosen")
    print("      • Transparent cost estimates before processing")
    print("      • Quality-optimized results for specific task types")
    print("      • Personalized recommendations that improve over time")
    print("      • Ability to choose cost vs quality preferences")
    
    print("\n   📈 Business Benefits:")
    print("      • Higher user satisfaction with AI outputs")
    print("      • Reduced support tickets about poor quality")
    print("      • Increased user trust through transparency")
    print("      • Better cost optimization based on actual user needs")
    print("      • Data-driven provider performance insights")

async def demo_real_world_scenarios():
    """Demonstrate real-world usage scenarios"""
    
    print(f"\n🌍 REAL-WORLD USAGE SCENARIOS")
    print("=" * 70)
    
    engine = QualityOptimizationEngine()
    
    scenarios = [
        {
            'name': 'Medical Professional',
            'request': LLMRequest(
                prompt="Analyze these patient symptoms and suggest potential diagnoses: fatigue, joint pain, morning stiffness",
                task_type=TaskType.ANALYSIS,
                max_tokens=600,
                temperature=0.2
            ),
            'user_id': 'doctor_smith',
            'preference': 'premium'
        },
        {
            'name': 'Student on Budget',
            'request': LLMRequest(
                prompt="Summarize the key points of photosynthesis for my biology homework",
                task_type=TaskType.SUMMARIZATION,
                max_tokens=300,
                temperature=0.5
            ),
            'user_id': 'student_jane',
            'preference': 'economy'
        },
        {
            'name': 'Software Developer',
            'request': LLMRequest(
                prompt="Debug this Python code and explain the issue: def factorial(n): return n * factorial(n-1)",
                task_type=TaskType.CODE_GENERATION,
                max_tokens=400,
                temperature=0.3
            ),
            'user_id': 'dev_alex',
            'preference': 'balanced'
        },
        {
            'name': 'Marketing Manager',
            'request': LLMRequest(
                prompt="Create a compelling product description for our new eco-friendly water bottle",
                task_type=TaskType.TEXT_GENERATION,
                max_tokens=250,
                temperature=0.8
            ),
            'user_id': 'marketing_sarah',
            'preference': 'balanced'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n👤 SCENARIO: {scenario['name']}")
        print(f"   📝 Request: {scenario['request'].prompt[:60]}...")
        print(f"   💰 Preference: {scenario['preference']}")
        
        recommendation = await engine.get_optimal_provider_recommendation(
            scenario['request'], scenario['user_id'], scenario['preference']
        )
        
        print(f"   🎯 Recommended: {recommendation.recommended_provider.value}")
        print(f"   ⭐ Quality: {recommendation.quality_score:.1%}")
        print(f"   💰 Cost: ${recommendation.cost_estimate:.3f}")
        print(f"   💡 Why: {recommendation.reasoning[:80]}...")

async def demo_quality_learning():
    """Demonstrate quality learning and adaptation"""
    
    print(f"\n🧠 QUALITY LEARNING & ADAPTATION DEMO")
    print("=" * 70)
    
    engine = QualityOptimizationEngine()
    
    print("📚 Simulating user feedback over time...")
    
    # Simulate feedback patterns
    learning_scenarios = [
        {
            'week': 1,
            'feedback': [
                UserFeedback("user_001", LLMProvider.OPENAI, TaskType.ANALYSIS, 4.0, 4.0, 4.0),
                UserFeedback("user_001", LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.8, 3.5, 4.5),
            ]
        },
        {
            'week': 2,
            'feedback': [
                UserFeedback("user_001", LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.9, 3.2, 4.7),
                UserFeedback("user_001", LLMProvider.GROQ, TaskType.CODE_GENERATION, 4.2, 4.9, 4.5),
            ]
        },
        {
            'week': 3,
            'feedback': [
                UserFeedback("user_001", LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.7, 3.8, 4.6),
                UserFeedback("user_001", LLMProvider.GROQ, TaskType.CODE_GENERATION, 4.4, 4.8, 4.6),
            ]
        }
    ]
    
    for scenario in learning_scenarios:
        print(f"\n📅 Week {scenario['week']}:")
        for feedback in scenario['feedback']:
            await engine.record_user_feedback(feedback)
            print(f"   📝 {feedback.provider.value} ({feedback.task_type.value}): "
                  f"Quality {feedback.quality_rating}/5, Satisfaction {feedback.satisfaction_rating}/5")
    
    # Show learning results
    print(f"\n🎯 LEARNING RESULTS:")
    insights = await engine.get_user_quality_insights("user_001")
    
    print(f"   📊 Total Feedback: {insights['total_interactions']} interactions")
    print(f"   📈 Quality Trend: {insights['quality_trends'].get('quality_trend', 'stable').title()}")
    print(f"   ⭐ Current Satisfaction: {insights['average_satisfaction']:.1f}/5.0")
    
    # Test recommendation with learned preferences
    test_request = LLMRequest(
        prompt="Analyze the competitive landscape for our SaaS product",
        task_type=TaskType.ANALYSIS,
        max_tokens=500
    )
    
    final_recommendation = await engine.get_optimal_provider_recommendation(
        test_request, "user_001", "balanced"
    )
    
    print(f"\n🎯 PERSONALIZED RECOMMENDATION (After Learning):")
    print(f"   Provider: {final_recommendation.recommended_provider.value}")
    print(f"   Reasoning: {final_recommendation.reasoning}")
    print(f"   Quality Score: {final_recommendation.quality_score:.1%}")
    
    print(f"\n✅ The system learned that this user:")
    print(f"   • Prefers Claude for analysis tasks (high quality ratings)")
    print(f"   • Values quality over speed for complex tasks")
    print(f"   • Has consistent satisfaction with premium providers")

async def main():
    """Main demo function"""
    await demo_quality_transformation()
    await demo_before_after_comparison()
    await demo_real_world_scenarios()
    await demo_quality_learning()
    
    print(f"\n🎯 DEMO COMPLETE")
    print("=" * 70)
    print("The Quality Optimization Engine successfully transforms")
    print("technical provider management into a quality-focused")
    print("user experience that:")
    print("• Optimizes for user outcomes, not just technical metrics")
    print("• Provides transparent cost-quality trade-offs")
    print("• Learns from user feedback to improve recommendations")
    print("• Matches providers to specific task requirements")
    print("• Builds user trust through clear reasoning")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())