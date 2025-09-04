#!/usr/bin/env python3
"""
Demo: NLP Model Configuration System
Showcases advanced model configuration management and intelligent selection
"""

import sys
import os
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from nlp_model_configurations import (
        ModelConfigurationManager,
        ModelType,
        ModelSize,
        ProcessingMode,
        ResourceRequirements,
        PerformanceMetrics,
        ModelCapabilities,
        ModelConfiguration
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("This demo requires the NLP configuration components to be available.")
    sys.exit(1)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)

def print_section(title: str):
    """Print formatted section"""
    print(f"\n--- {title} ---")

def print_model_info(config: ModelConfiguration, show_details: bool = True):
    """Print detailed model information"""
    print(f"\n🤖 {config.model_name}")
    print(f"   ID: {config.model_id}")
    print(f"   Type: {config.model_type.value}")
    print(f"   Size: {config.model_size.value}")
    print(f"   Version: {config.version}")
    
    if show_details:
        print(f"   📝 Description: {config.description}")
        
        # Resource requirements
        req = config.resource_requirements
        print(f"   💾 Memory: {req.memory_mb}MB")
        print(f"   🖥️  CPU Cores: {req.cpu_cores}")
        print(f"   🎮 GPU Required: {'Yes' if req.gpu_required else 'No'}")
        if req.gpu_required:
            print(f"   🎮 GPU Memory: {req.gpu_memory_mb}MB")
        
        # Performance metrics
        perf = config.performance_metrics
        print(f"   📊 Overall Score: {perf.overall_score():.2f}")
        print(f"   🎯 Accuracy: {perf.accuracy_score:.2f}")
        print(f"   ⚡ Speed: {perf.speed_score:.2f}")
        print(f"   🧠 Memory Efficiency: {perf.memory_efficiency:.2f}")
        print(f"   ⚙️  CPU Efficiency: {perf.cpu_efficiency:.2f}")
        print(f"   🏷️  NER Accuracy: {perf.ner_accuracy:.2f}")
        print(f"   🔄 Processing Speed: {perf.processing_speed_wps:,} words/sec")
        
        # Capabilities
        capabilities = config.capabilities.get_supported_capabilities()
        print(f"   🛠️  Capabilities ({len(capabilities)}): {', '.join(capabilities[:5])}")
        if len(capabilities) > 5:
            print(f"      ... and {len(capabilities) - 5} more")
        
        # Recommended usage
        print(f"   ✅ Recommended for: {', '.join(config.recommended_for[:3])}")
        if len(config.recommended_for) > 3:
            print(f"      ... and {len(config.recommended_for) - 3} more")
        
        # Processing modes
        modes = [mode.value for mode in config.processing_modes]
        print(f"   ⚙️  Processing Modes: {', '.join(modes)}")

def demo_configuration_management():
    """Demonstrate configuration management features"""
    print_header("NLP Model Configuration System Demo")
    
    # Initialize configuration manager
    print("🚀 Initializing Model Configuration Manager...")
    manager = ModelConfigurationManager()
    print(f"✅ Loaded {len(manager.configurations)} model configurations")
    
    # Demo 1: List all configurations
    print_section("1. Available Model Configurations")
    
    all_configs = manager.list_configurations()
    print(f"📋 Total configurations available: {len(all_configs)}")
    
    for config in all_configs:
        print_model_info(config, show_details=False)
    
    # Demo 2: Filter configurations by type
    print_section("2. Filtering by Model Type")
    
    statistical_models = manager.list_configurations(model_type=ModelType.SPACY_STATISTICAL)
    transformer_models = manager.list_configurations(model_type=ModelType.SPACY_TRANSFORMER)
    
    print(f"📊 Statistical Models ({len(statistical_models)}):")
    for config in statistical_models:
        print(f"   • {config.model_name} ({config.model_size.value})")
    
    print(f"\n🤖 Transformer Models ({len(transformer_models)}):")
    for config in transformer_models:
        print(f"   • {config.model_name} ({config.model_size.value})")
    
    # Demo 3: Filter by processing mode
    print_section("3. Filtering by Processing Mode")
    
    speed_models = manager.list_configurations(processing_mode=ProcessingMode.SPEED_OPTIMIZED)
    accuracy_models = manager.list_configurations(processing_mode=ProcessingMode.ACCURACY_OPTIMIZED)
    balanced_models = manager.list_configurations(processing_mode=ProcessingMode.BALANCED)
    
    print(f"⚡ Speed-Optimized Models ({len(speed_models)}):")
    for config in speed_models:
        print(f"   • {config.model_name} - {config.performance_metrics.processing_speed_wps:,} words/sec")
    
    print(f"\n🎯 Accuracy-Optimized Models ({len(accuracy_models)}):")
    for config in accuracy_models:
        print(f"   • {config.model_name} - {config.performance_metrics.accuracy_score:.2f} accuracy")
    
    print(f"\n⚖️  Balanced Models ({len(balanced_models)}):")
    for config in balanced_models:
        print(f"   • {config.model_name} - {config.performance_metrics.overall_score():.2f} overall")
    
    # Demo 4: Detailed model information
    print_section("4. Detailed Model Information")
    
    # Show details for each model size
    model_sizes = [ModelSize.SMALL, ModelSize.MEDIUM, ModelSize.LARGE, ModelSize.EXTRA_LARGE]
    
    for size in model_sizes:
        size_configs = manager.list_configurations(model_size=size)
        if size_configs:
            print(f"\n📏 {size.value.upper()} Models:")
            for config in size_configs:
                print_model_info(config, show_details=True)
    
    return manager

def demo_intelligent_selection():
    """Demonstrate intelligent model selection"""
    print_section("5. Intelligent Model Selection")
    
    manager = ModelConfigurationManager()
    
    # Scenario 1: Real-time chat analysis
    print("\n🔍 Scenario 1: Real-time Chat Analysis")
    print("   Requirements: Fast processing, basic NER, limited resources")
    
    requirements1 = {
        'capabilities': ['named_entity_recognition', 'tokenization'],
        'processing_mode': 'speed_optimized',
        'content_type': 'real_time_analysis',
        'complexity_estimate': 0.2
    }
    
    resources1 = {
        'max_memory_mb': 100,
        'max_cpu_cores': 2,
        'gpu_available': False
    }
    
    selected1 = manager.select_optimal_model(requirements1, resources1)
    if selected1:
        print(f"   🎯 Selected: {selected1.model_name}")
        print(f"   ⚡ Speed Score: {selected1.performance_metrics.speed_score:.2f}")
        print(f"   💾 Memory Usage: {selected1.resource_requirements.memory_mb}MB")
        print(f"   🔄 Processing Speed: {selected1.performance_metrics.processing_speed_wps:,} words/sec")
    else:
        print("   ❌ No suitable model found")
    
    # Scenario 2: Research document analysis
    print("\n🔍 Scenario 2: Research Document Analysis")
    print("   Requirements: Maximum accuracy, comprehensive NLP, high-end resources")
    
    requirements2 = {
        'capabilities': ['named_entity_recognition', 'dependency_parsing', 'entity_linking', 'coreference_resolution'],
        'processing_mode': 'accuracy_optimized',
        'content_type': 'research',
        'complexity_estimate': 0.9
    }
    
    resources2 = {
        'max_memory_mb': 4000,
        'max_cpu_cores': 8,
        'gpu_available': True,
        'max_gpu_memory_mb': 8000
    }
    
    selected2 = manager.select_optimal_model(requirements2, resources2)
    if selected2:
        print(f"   🎯 Selected: {selected2.model_name}")
        print(f"   🎯 Accuracy Score: {selected2.performance_metrics.accuracy_score:.2f}")
        print(f"   🏷️  NER Accuracy: {selected2.performance_metrics.ner_accuracy:.2f}")
        print(f"   🧠 Capabilities: {len(selected2.capabilities.get_supported_capabilities())}")
    else:
        print("   ❌ No suitable model found")
    
    # Scenario 3: Production web service
    print("\n🔍 Scenario 3: Production Web Service")
    print("   Requirements: Balanced performance, reliable, moderate resources")
    
    requirements3 = {
        'capabilities': ['named_entity_recognition', 'part_of_speech_tagging', 'similarity_matching'],
        'processing_mode': 'balanced',
        'content_type': 'production_systems',
        'complexity_estimate': 0.5
    }
    
    resources3 = {
        'max_memory_mb': 1000,
        'max_cpu_cores': 4,
        'gpu_available': False
    }
    
    selected3 = manager.select_optimal_model(requirements3, resources3)
    if selected3:
        print(f"   🎯 Selected: {selected3.model_name}")
        print(f"   ⚖️  Overall Score: {selected3.performance_metrics.overall_score():.2f}")
        print(f"   🎯 Accuracy: {selected3.performance_metrics.accuracy_score:.2f}")
        print(f"   ⚡ Speed: {selected3.performance_metrics.speed_score:.2f}")
        print(f"   💾 Memory Efficiency: {selected3.performance_metrics.memory_efficiency:.2f}")
    else:
        print("   ❌ No suitable model found")
    
    # Scenario 4: Mobile application
    print("\n🔍 Scenario 4: Mobile Application")
    print("   Requirements: Very limited resources, basic functionality")
    
    requirements4 = {
        'capabilities': ['tokenization', 'named_entity_recognition'],
        'processing_mode': 'resource_constrained',
        'content_type': 'mobile_deployment',
        'complexity_estimate': 0.3
    }
    
    resources4 = {
        'max_memory_mb': 50,
        'max_cpu_cores': 1,
        'gpu_available': False
    }
    
    selected4 = manager.select_optimal_model(requirements4, resources4)
    if selected4:
        print(f"   🎯 Selected: {selected4.model_name}")
        print(f"   💾 Memory Usage: {selected4.resource_requirements.memory_mb}MB")
        print(f"   🖥️  CPU Cores: {selected4.resource_requirements.cpu_cores}")
        print(f"   📱 Mobile Friendly: {'Yes' if selected4.resource_requirements.memory_mb <= 100 else 'No'}")
    else:
        print("   ❌ No suitable model found")

def demo_fallback_chains():
    """Demonstrate fallback chain functionality"""
    print_section("6. Fallback Chain Analysis")
    
    manager = ModelConfigurationManager()
    
    # Show fallback chains for each model
    model_ids = ["en_core_web_trf", "en_core_web_lg", "en_core_web_md", "en_core_web_sm"]
    
    for model_id in model_ids:
        config = manager.get_configuration(model_id)
        if config:
            print(f"\n🔄 Fallback Chain for {config.model_name}:")
            print(f"   Primary: {config.model_name} ({config.model_size.value})")
            
            fallback_chain = manager.get_fallback_chain(model_id)
            if fallback_chain:
                for i, fallback in enumerate(fallback_chain, 1):
                    print(f"   Fallback {i}: {fallback.model_name} ({fallback.model_size.value})")
            else:
                print("   No fallbacks configured")

def demo_performance_comparison():
    """Demonstrate performance comparison across models"""
    print_section("7. Performance Comparison")
    
    manager = ModelConfigurationManager()
    all_configs = manager.list_configurations()
    
    # Create comparison table
    print("\n📊 Performance Comparison Table:")
    print("=" * 100)
    print(f"{'Model':<25} {'Size':<12} {'Accuracy':<10} {'Speed':<10} {'Memory':<10} {'Overall':<10}")
    print("=" * 100)
    
    # Sort by overall performance
    sorted_configs = sorted(all_configs, key=lambda x: x.performance_metrics.overall_score(), reverse=True)
    
    for config in sorted_configs:
        perf = config.performance_metrics
        print(f"{config.model_name:<25} {config.model_size.value:<12} "
              f"{perf.accuracy_score:<10.2f} {perf.speed_score:<10.2f} "
              f"{perf.memory_efficiency:<10.2f} {perf.overall_score():<10.2f}")
    
    print("=" * 100)
    
    # Performance analysis
    print("\n📈 Performance Analysis:")
    
    # Find best in each category
    best_accuracy = max(all_configs, key=lambda x: x.performance_metrics.accuracy_score)
    best_speed = max(all_configs, key=lambda x: x.performance_metrics.speed_score)
    best_memory = max(all_configs, key=lambda x: x.performance_metrics.memory_efficiency)
    best_overall = max(all_configs, key=lambda x: x.performance_metrics.overall_score())
    
    print(f"   🎯 Best Accuracy: {best_accuracy.model_name} ({best_accuracy.performance_metrics.accuracy_score:.2f})")
    print(f"   ⚡ Best Speed: {best_speed.model_name} ({best_speed.performance_metrics.speed_score:.2f})")
    print(f"   💾 Best Memory Efficiency: {best_memory.model_name} ({best_memory.performance_metrics.memory_efficiency:.2f})")
    print(f"   🏆 Best Overall: {best_overall.model_name} ({best_overall.performance_metrics.overall_score():.2f})")

def demo_statistics():
    """Demonstrate configuration statistics"""
    print_section("8. Configuration Statistics")
    
    manager = ModelConfigurationManager()
    stats = manager.get_statistics()
    
    print(f"📊 Configuration Statistics:")
    print(f"   Total Configurations: {stats['total_configurations']}")
    
    print(f"\n   By Type:")
    for model_type, count in stats['by_type'].items():
        print(f"     {model_type}: {count}")
    
    print(f"\n   By Size:")
    for size, count in stats['by_size'].items():
        print(f"     {size}: {count}")
    
    print(f"\n   By Processing Mode:")
    for mode, count in stats['by_processing_mode'].items():
        print(f"     {mode}: {count}")
    
    print(f"\n   Average Performance:")
    avg_perf = stats['average_performance']
    for metric, value in avg_perf.items():
        print(f"     {metric}: {value:.2f}")

def demo_custom_configuration():
    """Demonstrate adding custom configuration"""
    print_section("9. Custom Configuration Management")
    
    manager = ModelConfigurationManager()
    
    print("🛠️  Creating Custom Model Configuration...")
    
    # Create a custom configuration
    custom_config = ModelConfiguration(
        model_id="custom_fast_model",
        model_name="Custom Fast NLP Model",
        model_type=ModelType.LOCAL_CUSTOM,
        model_size=ModelSize.SMALL,
        version="1.0.0",
        description="Custom optimized model for specific use case",
        resource_requirements=ResourceRequirements(
            memory_mb=30,
            cpu_cores=1,
            gpu_required=False
        ),
        performance_metrics=PerformanceMetrics(
            accuracy_score=0.72,
            speed_score=0.98,
            memory_efficiency=0.95,
            cpu_efficiency=0.92,
            ner_accuracy=0.8,
            processing_speed_wps=20000
        ),
        capabilities=ModelCapabilities(
            named_entity_recognition=True,
            tokenization=True,
            part_of_speech_tagging=True,
            custom_components=True
        ),
        recommended_for=["ultra_fast_processing", "edge_computing", "iot_devices"],
        processing_modes=[ProcessingMode.SPEED_OPTIMIZED, ProcessingMode.RESOURCE_CONSTRAINED],
        fallback_models=["en_core_web_sm"],
        fallback_priority=1
    )
    
    # Add to manager
    initial_count = len(manager.configurations)
    manager.add_configuration(custom_config)
    
    print(f"✅ Added custom configuration!")
    print(f"   Configurations before: {initial_count}")
    print(f"   Configurations after: {len(manager.configurations)}")
    
    # Show the custom configuration
    print_model_info(custom_config, show_details=True)
    
    # Test selection with custom model
    print("\n🔍 Testing Selection with Custom Model:")
    requirements = {
        'capabilities': ['named_entity_recognition'],
        'processing_mode': 'speed_optimized',
        'content_type': 'ultra_fast_processing'
    }
    
    selected = manager.select_optimal_model(requirements)
    if selected and selected.model_id == "custom_fast_model":
        print("   ✅ Custom model was selected!")
    else:
        print(f"   ℹ️  Selected: {selected.model_name if selected else 'None'}")

def main():
    """Main demo function"""
    try:
        # Run all demo sections
        manager = demo_configuration_management()
        demo_intelligent_selection()
        demo_fallback_chains()
        demo_performance_comparison()
        demo_statistics()
        demo_custom_configuration()
        
        print_section("Demo Complete!")
        print("✅ NLP Model Configuration System demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("• Comprehensive model configuration management")
        print("• Intelligent model selection based on requirements and resources")
        print("• Performance comparison and analysis")
        print("• Fallback chain management")
        print("• Custom configuration support")
        print("• Statistical analysis and reporting")
        print("• Resource constraint handling")
        print("• Multi-criteria decision making")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()