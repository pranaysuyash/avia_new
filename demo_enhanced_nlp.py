#!/usr/bin/env python3
"""
Demo: Enhanced NLP Model Manager
Showcases intelligent model selection, multi-model support, and performance optimization
"""

import asyncio
import sys
import os
from typing import List
from unittest.mock import Mock, AsyncMock

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_nlp_model_manager import (
        EnhancedNLPModelManager,
        NLPModelType,
        ProcessingContext,
        create_processing_context,
        estimate_text_complexity
    )
    from unified_nlp_foundation import NLPCapability, NLPResult
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires the enhanced NLP components to be available.")
    sys.exit(1)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title: str):
    """Print formatted section"""
    print(f"\n--- {title} ---")

async def demo_model_selection():
    """Demonstrate intelligent model selection"""
    print_header("Enhanced NLP Model Manager Demo")
    
    # Mock the UnifiedNLPFoundation to avoid dependency issues
    mock_nlp_foundation = Mock()
    
    # Create mock results for different scenarios
    def create_mock_result(text: str, model_used: str) -> NLPResult:
        return NLPResult(
            text=text,
            capabilities_used=["advanced_ner", "sentiment_analysis"],
            entities=[
                {"text": "John", "label": "PERSON", "start": 0, "end": 4, "confidence": 0.9},
                {"text": "quarterly", "label": "DATE", "start": 20, "end": 29, "confidence": 0.8}
            ],
            sentiment={"polarity": 0.3, "subjectivity": 0.6},
            emotions={"joy": 0.4, "neutral": 0.6},
            topics=[{"topic": "business_meeting", "confidence": 0.85}],
            summary="Meeting discussion about quarterly results",
            questions=["What are the next steps?"],
            intent="meeting_discussion",
            confidence_scores={"ner": 0.9, "sentiment": 0.8},
            processing_time=0.15,
            model_info={"ner": model_used, "sentiment": model_used}
        )
    
    mock_nlp_foundation.process_text = AsyncMock(side_effect=lambda text, caps, ctx=None: 
        create_mock_result(text, ctx.get('preferred_model', 'spacy_small') if ctx else 'spacy_small'))
    
    # Initialize manager with mocked foundation
    manager = EnhancedNLPModelManager()
    manager.nlp_foundation = mock_nlp_foundation
    
    print("✅ Enhanced NLP Model Manager initialized successfully!")
    
    # Demo 1: Model Selection for Different Scenarios
    print_section("1. Intelligent Model Selection")
    
    scenarios = [
        {
            "name": "Quick Chat Analysis",
            "text": "Hey, how's it going? Everything good?",
            "content_type": "conversation",
            "quality_target": "speed"
        },
        {
            "name": "Business Meeting Minutes",
            "text": """In today's quarterly review meeting, CEO John Smith discussed the company's 
            performance metrics and strategic initiatives. The team agreed to implement 
            new customer acquisition strategies, with Sarah leading the marketing efforts 
            and Mike handling technical implementation. Action items include finalizing 
            the budget proposal by next Friday and scheduling follow-up meetings.""",
            "content_type": "meeting",
            "quality_target": "balanced"
        },
        {
            "name": "Technical Document Analysis",
            "text": """The implementation of advanced machine learning algorithms requires careful 
            consideration of architectural patterns, optimization methodologies, and 
            comprehensive evaluation frameworks. The system must incorporate robust 
            performance metrics and scalability considerations to ensure enterprise-grade 
            deployment capabilities.""",
            "content_type": "document",
            "quality_target": "accuracy"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📝 Scenario: {scenario['name']}")
        print(f"   Content Type: {scenario['content_type']}")
        print(f"   Quality Target: {scenario['quality_target']}")
        print(f"   Text Length: {len(scenario['text'])} characters")
        
        # Create processing context
        context = create_processing_context(
            content_type=scenario['content_type'],
            text=scenario['text'],
            quality_target=scenario['quality_target']
        )
        
        print(f"   Complexity Estimate: {context.complexity_estimate:.2f}")
        
        # Select optimal model
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.SENTIMENT_ANALYSIS]
        selected_model = manager.select_optimal_nlp_model(context, capabilities)
        
        model_info = selected_model
        print(f"   🎯 Selected Model: {selected_model.value}")
        print(f"   📊 Model Size: {model_info.model_size}")
        print(f"   ⚡ Processing Speed: {model_info.processing_speed}")
        print(f"   🎯 Accuracy Level: {model_info.accuracy_level}")
        print(f"   💡 Use Cases: {', '.join(model_info.use_cases[:2])}")
    
    # Demo 2: Resource Constraint Handling
    print_section("2. Resource Constraint Handling")
    
    constraint_scenarios = [
        {
            "name": "Low Memory Environment",
            "constraints": {"max_memory_mb": 100, "gpu_available": False},
            "description": "Limited to 100MB RAM, no GPU"
        },
        {
            "name": "GPU-Enabled Server",
            "constraints": {"max_memory_mb": 2000, "gpu_available": True, "max_gpu_memory_mb": 4000},
            "description": "High-end server with GPU support"
        },
        {
            "name": "Mobile Device",
            "constraints": {"max_memory_mb": 200, "max_cpu_cores": 2, "gpu_available": False},
            "description": "Mobile device with limited resources"
        }
    ]
    
    base_text = "Analyze this business meeting transcript for key insights and action items."
    
    for scenario in constraint_scenarios:
        print(f"\n🔧 Environment: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        context = ProcessingContext(
            content_type="meeting",
            content_length=len(base_text),
            complexity_estimate=0.6,
            quality_target="balanced",
            resource_constraints=scenario['constraints']
        )
        
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.SENTIMENT_ANALYSIS]
        selected_model = manager.select_optimal_nlp_model(context, capabilities)
        
        print(f"   🎯 Optimal Model: {selected_model.value}")
        
        # Check if model meets constraints
        config = manager.model_configs[selected_model]
        meets_constraints = manager._check_resource_constraints(config, scenario['constraints'])
        print(f"   ✅ Meets Constraints: {meets_constraints}")
        print(f"   💾 Memory Required: {config.resource_requirements['memory_mb']}MB")
        print(f"   🖥️  CPU Cores: {config.resource_requirements['cpu_cores']}")
        print(f"   🎮 GPU Required: {config.resource_requirements.get('gpu_required', False)}")
    
    # Demo 3: Processing with Different Models
    print_section("3. Processing with Optimal Model Selection")
    
    sample_texts = [
        {
            "text": "Great meeting today! John and Sarah presented excellent quarterly results. We should celebrate this success and plan for Q4 growth.",
            "type": "meeting",
            "target": "balanced"
        },
        {
            "text": "The system architecture requires optimization. Performance bottlenecks identified in the database layer need immediate attention.",
            "type": "document", 
            "target": "accuracy"
        },
        {
            "text": "Quick question - are we still on for the 3pm call?",
            "type": "conversation",
            "target": "speed"
        }
    ]
    
    for i, sample in enumerate(sample_texts, 1):
        print(f"\n📄 Processing Sample {i}")
        print(f"   Text: {sample['text'][:50]}...")
        
        context = create_processing_context(
            content_type=sample['type'],
            text=sample['text'],
            quality_target=sample['target']
        )
        
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.SENTIMENT_ANALYSIS]
        
        try:
            result = await manager.process_with_optimal_model(sample['text'], context, capabilities)
            
            print(f"   ⏱️  Processing Time: {result.processing_time:.3f}s")
            print(f"   🏷️  Entities Found: {len(result.entities)}")
            print(f"   😊 Sentiment: {result.sentiment.get('polarity', 0):.2f}")
            print(f"   🎯 Confidence: {result.confidence_scores.get('ner', 0):.2f}")
            print(f"   🤖 Model Used: {result.model_info.get('ner', 'unknown')}")
            
            if result.entities:
                print(f"   📋 Sample Entity: {result.entities[0]['text']} ({result.entities[0]['label']})")
            
        except Exception as e:
            print(f"   ❌ Processing failed: {str(e)}")
    
    # Demo 4: Performance Statistics
    print_section("4. Performance Statistics & Analytics")
    
    stats = manager.get_nlp_statistics()
    
    print("📊 Model Selection Statistics:")
    for model, count in stats['model_selections'].items():
        if count > 0:
            print(f"   {model}: {count} selections")
    
    print("\n📈 Content Type Preferences:")
    for content_type, prefs in stats['content_type_preferences'].items():
        if prefs:
            print(f"   {content_type}:")
            for model, count in prefs.items():
                print(f"     - {model}: {count} times")
    
    print("\n🔧 Available Model Configurations:")
    for model_name, config in stats['model_configurations'].items():
        print(f"   {model_name}:")
        print(f"     Size: {config['size']}")
        print(f"     Accuracy: {config['accuracy_level']}")
        print(f"     Speed: {config['processing_speed']}")
    
    # Demo 5: Complexity Estimation
    print_section("5. Text Complexity Analysis")
    
    complexity_samples = [
        "Hello world!",
        "The meeting went well and we discussed the quarterly results.",
        "The implementation of advanced machine learning algorithms requires comprehensive evaluation of architectural patterns and optimization methodologies.",
        "In accordance with the aforementioned regulatory compliance framework, the organization must implement sophisticated algorithmic methodologies to ensure optimal performance metrics."
    ]
    
    print("📊 Text Complexity Estimation:")
    for i, text in enumerate(complexity_samples, 1):
        complexity = estimate_text_complexity(text)
        print(f"   Sample {i}: {complexity:.2f}")
        print(f"     Text: {text[:60]}...")
        print(f"     Length: {len(text)} chars")
        
        if complexity < 0.3:
            level = "Low"
        elif complexity < 0.7:
            level = "Medium"
        else:
            level = "High"
        print(f"     Complexity Level: {level}")
    
    print_section("Demo Complete!")
    print("✅ Enhanced NLP Model Manager demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Intelligent model selection based on content and requirements")
    print("• Resource constraint handling for different environments")
    print("• Performance optimization and caching")
    print("• Comprehensive statistics and analytics")
    print("• Text complexity analysis")
    print("• Fallback mechanisms for reliability")

def main():
    """Main demo function"""
    try:
        asyncio.run(demo_model_selection())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()