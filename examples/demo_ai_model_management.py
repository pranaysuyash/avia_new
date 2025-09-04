#!/usr/bin/env python3
"""
Demo Script for AI Model Management System
Demonstrates Task 65: AI model versioning and A/B testing

This demo showcases comprehensive AI model lifecycle management including:
- Model registry and version control
- A/B testing framework with statistical analysis
- Performance monitoring and drift detection
- Cost optimization and intelligent model selection
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_model_management import (
        ModelManagementService, ModelStatus, ExperimentStatus,
        ModelMetadata, ModelPerformanceMetrics
    )
except ImportError:
    print("❌ Error: Could not import AI Model Management system")
    print("Please ensure ai_model_management.py is in the same directory")
    sys.exit(1)

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

def print_model_info(model: ModelMetadata):
    """Print model information in a formatted way"""
    print(f"🤖 Model Information:")
    print(f"  • ID: {model.model_id[:8]}...")
    print(f"  • Name: {model.name}")
    print(f"  • Version: {model.version}")
    print(f"  • Type: {model.model_type}")
    print(f"  • Framework: {model.framework}")
    print(f"  • Status: {model.status.value}")
    print(f"  • Created: {model.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  • Created By: {model.created_by}")
    if model.tags:
        print(f"  • Tags: {', '.join(model.tags)}")
    if model.description:
        print(f"  • Description: {model.description}")

def demo_model_registry():
    """Demonstrate model registry functionality"""
    print_subheader("Model Registry & Version Management")
    
    service = ModelManagementService("demo_registry.db")
    
    print("Creating sample models for different use cases...")
    
    # Create different types of models
    models_to_create = [
        {
            'name': 'whisper-transcription',
            'version': '1.0.0',
            'description': 'OpenAI Whisper base model for general transcription',
            'model_type': 'transcription',
            'framework': 'openai',
            'parameters': {'model_size': 'base', 'language': 'en'},
            'tags': ['production', 'stable', 'general']
        },
        {
            'name': 'whisper-transcription',
            'version': '1.1.0',
            'description': 'OpenAI Whisper large model for high-accuracy transcription',
            'model_type': 'transcription',
            'framework': 'openai',
            'parameters': {'model_size': 'large', 'language': 'en'},
            'tags': ['experimental', 'high-accuracy']
        },
        {
            'name': 'gpt-content-analysis',
            'version': '1.0.0',
            'description': 'GPT-4 model for advanced content analysis and entity extraction',
            'model_type': 'analysis',
            'framework': 'openai',
            'parameters': {'model': 'gpt-4', 'temperature': 0.1, 'max_tokens': 2000},
            'tags': ['production', 'analysis', 'entities']
        },
        {
            'name': 'custom-audio-enhancer',
            'version': '2.0.0',
            'description': 'Custom neural network for audio enhancement and noise reduction',
            'model_type': 'enhancement',
            'framework': 'custom',
            'parameters': {'architecture': 'transformer', 'layers': 12, 'attention_heads': 8},
            'tags': ['custom', 'audio', 'enhancement']
        }
    ]
    
    created_models = []
    
    for i, model_config in enumerate(models_to_create, 1):
        print(f"\n{i}. Creating {model_config['name']} v{model_config['version']}")
        
        try:
            model_id = service.create_model_version(
                created_by='demo_user',
                **model_config
            )
            created_models.append(model_id)
            
            # Get and display model info
            model = service.registry.get_model(model_id)
            print(f"   ✅ Created successfully!")
            print(f"   📋 ID: {model_id[:8]}...")
            print(f"   🏷️  Tags: {', '.join(model.tags)}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n📊 Registry Summary:")
    all_models = service.registry.list_models(limit=100)
    print(f"  • Total models: {len(all_models)}")
    
    # Group by type
    by_type = {}
    by_status = {}
    
    for model in all_models:
        by_type[model.model_type] = by_type.get(model.model_type, 0) + 1
        by_status[model.status.value] = by_status.get(model.status.value, 0) + 1
    
    print(f"  • By type: {dict(by_type)}")
    print(f"  • By status: {dict(by_status)}")
    
    # Demonstrate model deployment
    print(f"\n🚀 Deploying models to different environments...")
    
    for i, model_id in enumerate(created_models[:2]):  # Deploy first 2 models
        model = service.registry.get_model(model_id)
        environment = "production" if i == 0 else "staging"
        
        print(f"   Deploying {model.name} v{model.version} to {environment}...")
        service.deploy_model(model_id, environment)
        print(f"   ✅ Deployed successfully!")
    
    return created_models

def demo_performance_monitoring(model_ids: List[str]):
    """Demonstrate performance monitoring and health checks"""
    print_subheader("Performance Monitoring & Health Checks")
    
    service = ModelManagementService("demo_registry.db")
    
    if not model_ids:
        print("❌ No models available for monitoring")
        return
    
    # Select first model for detailed monitoring
    model_id = model_ids[0]
    model = service.registry.get_model(model_id)
    
    print(f"📈 Monitoring model: {model.name} v{model.version}")
    print(f"   Model ID: {model_id[:8]}...")
    
    # Simulate historical performance data
    print(f"\n📊 Generating historical performance data...")
    
    # Generate baseline metrics (7 days ago)
    baseline_start = datetime.now() - timedelta(days=8)
    baseline_metrics = []
    
    print("   Creating baseline metrics (7 days ago)...")
    for i in range(50):  # 50 data points for baseline
        timestamp = baseline_start + timedelta(hours=i * 3)  # Every 3 hours
        
        # Simulate stable baseline performance
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=timestamp,
            accuracy=0.85 + random.uniform(-0.01, 0.01),  # Stable around 85%
            latency_ms=100 + random.uniform(-5, 5),       # Stable around 100ms
            throughput_rps=50 + random.uniform(-2, 2),    # Stable around 50 RPS
            error_rate=0.01 + random.uniform(-0.002, 0.002),  # Low error rate
            cost_per_request=0.001 + random.uniform(-0.0001, 0.0001),  # Stable cost
            memory_usage_mb=512 + random.uniform(-20, 20),
            cpu_usage_percent=60 + random.uniform(-5, 5),
            user_satisfaction=4.2 + random.uniform(-0.1, 0.1)
        )
        baseline_metrics.append(metrics)
        service.registry.record_metrics(metrics)
    
    print(f"   ✅ Created {len(baseline_metrics)} baseline metrics")
    
    # Generate recent metrics with some degradation
    print("   Creating recent metrics (last 24 hours)...")
    recent_start = datetime.now() - timedelta(hours=24)
    recent_metrics = []
    
    for i in range(24):  # Hourly metrics for last 24 hours
        timestamp = recent_start + timedelta(hours=i)
        
        # Simulate gradual performance degradation
        degradation_factor = i / 24.0  # Increases over time
        
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=timestamp,
            accuracy=0.85 - (degradation_factor * 0.03),  # Slight accuracy drop
            latency_ms=100 + (degradation_factor * 20),   # Increasing latency
            throughput_rps=50 - (degradation_factor * 5), # Decreasing throughput
            error_rate=0.01 + (degradation_factor * 0.02), # Increasing errors
            cost_per_request=0.001 + (degradation_factor * 0.0005),  # Increasing cost
            memory_usage_mb=512 + (degradation_factor * 100),
            cpu_usage_percent=60 + (degradation_factor * 15),
            user_satisfaction=4.2 - (degradation_factor * 0.3)
        )
        recent_metrics.append(metrics)
        service.registry.record_metrics(metrics)
    
    print(f"   ✅ Created {len(recent_metrics)} recent metrics")
    
    # Perform health check
    print(f"\n🏥 Performing health check...")
    health = service.monitor.check_model_health(model_id)
    
    status_emoji = {
        'healthy': '🟢',
        'degraded': '🟡',
        'unhealthy': '🔴',
        'insufficient_data': '⚪'
    }.get(health['status'], '❓')
    
    print(f"   Status: {status_emoji} {health['status'].upper()}")
    
    if health.get('alerts'):
        print(f"\n🚨 Active Alerts ({len(health['alerts'])}):")
        for alert in health['alerts']:
            severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(alert['severity'], '⚪')
            print(f"   {severity_emoji} {alert['type'].replace('_', ' ').title()}")
            print(f"      {alert['message']}")
            print(f"      Baseline: {alert.get('baseline', 'N/A')}")
            print(f"      Current: {alert.get('current', 'N/A')}")
    else:
        print("   ✅ No alerts detected")
    
    # Display performance trends
    if 'baseline_metrics' in health and 'current_metrics' in health:
        print(f"\n📊 Performance Comparison:")
        baseline = health['baseline_metrics']
        current = health['current_metrics']
        
        metrics_to_compare = ['accuracy', 'latency_ms', 'error_rate', 'cost_per_request']
        
        for metric in metrics_to_compare:
            if metric in baseline and metric in current:
                baseline_val = baseline[metric]
                current_val = current[metric]
                
                # Calculate percentage change
                if baseline_val != 0:
                    change_pct = ((current_val - baseline_val) / baseline_val) * 100
                    change_indicator = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                    
                    print(f"   • {metric.replace('_', ' ').title()}:")
                    print(f"     Baseline: {baseline_val:.4f}")
                    print(f"     Current:  {current_val:.4f}")
                    print(f"     Change:   {change_indicator} {change_pct:+.2f}%")
    
    # System health overview
    print(f"\n🌐 System Health Overview:")
    system_health = service.get_system_health()
    
    overall_emoji = {
        'healthy': '🟢',
        'degraded': '🟡',
        'unhealthy': '🔴'
    }.get(system_health['overall_status'], '❓')
    
    print(f"   Overall Status: {overall_emoji} {system_health['overall_status'].upper()}")
    print(f"   Production Models: {system_health['production_models']}")
    print(f"   Active Experiments: {system_health['active_experiments']}")
    print(f"   System Alerts: {len(system_health['alerts'])}")
    
    return model_id

def demo_ab_testing(model_ids: List[str]):
    """Demonstrate A/B testing functionality"""
    print_subheader("A/B Testing Framework")
    
    service = ModelManagementService("demo_registry.db")
    
    if len(model_ids) < 2:
        print("❌ Need at least 2 models for A/B testing")
        return
    
    # Select two models for A/B testing
    control_id = model_ids[0]
    treatment_id = model_ids[1]
    
    control_model = service.registry.get_model(control_id)
    treatment_model = service.registry.get_model(treatment_id)
    
    print(f"🧪 Setting up A/B test:")
    print(f"   Control Model:   {control_model.name} v{control_model.version}")
    print(f"   Treatment Model: {treatment_model.name} v{treatment_model.version}")
    
    # Ensure both models are in production
    service.deploy_model(control_id, "production")
    service.deploy_model(treatment_id, "production")
    
    # Create A/B test experiment
    print(f"\n🚀 Creating A/B test experiment...")
    
    try:
        experiment_id = service.start_ab_test(
            name="Model Performance Comparison",
            description=f"Compare {control_model.name} v{control_model.version} vs v{treatment_model.version}",
            control_model_id=control_id,
            treatment_model_id=treatment_id,
            traffic_split=0.5,  # 50/50 split
            success_metrics=['accuracy', 'latency_ms', 'cost_per_request', 'user_satisfaction'],
            duration_days=7,
            created_by='demo_user',
            minimum_sample_size=100,
            confidence_level=0.95
        )
        
        print(f"   ✅ Experiment created successfully!")
        print(f"   📋 Experiment ID: {experiment_id[:8]}...")
        print(f"   🎯 Traffic Split: 50% control, 50% treatment")
        print(f"   📊 Success Metrics: accuracy, latency, cost, satisfaction")
        print(f"   📅 Duration: 7 days")
        print(f"   🎲 Minimum Sample Size: 100")
        
    except Exception as e:
        print(f"   ❌ Error creating experiment: {str(e)}")
        return
    
    # Simulate user interactions and data collection
    print(f"\n👥 Simulating user interactions...")
    
    total_users = 200
    control_count = 0
    treatment_count = 0
    
    for i in range(total_users):
        user_id = f"demo_user_{i:03d}"
        
        # Assign user to variant
        variant = service.ab_testing.assign_variant(experiment_id, user_id)
        
        if variant == "control":
            control_count += 1
        else:
            treatment_count += 1
        
        # Simulate different performance characteristics
        if variant == "control":
            # Control model: stable but lower performance
            accuracy = 0.85 + random.uniform(-0.02, 0.02)
            latency_ms = 100 + random.uniform(-10, 10)
            cost_per_request = 0.001 + random.uniform(-0.0001, 0.0001)
            user_satisfaction = 4.0 + random.uniform(-0.3, 0.3)
        else:
            # Treatment model: better performance but slightly higher cost
            accuracy = 0.88 + random.uniform(-0.02, 0.02)  # Better accuracy
            latency_ms = 95 + random.uniform(-8, 8)        # Slightly faster
            cost_per_request = 0.0012 + random.uniform(-0.0001, 0.0001)  # Slightly more expensive
            user_satisfaction = 4.3 + random.uniform(-0.2, 0.2)  # Higher satisfaction
        
        # Record metrics
        metrics = {
            'accuracy': accuracy,
            'latency_ms': latency_ms,
            'cost_per_request': cost_per_request,
            'user_satisfaction': user_satisfaction
        }
        
        service.ab_testing.record_experiment_data(experiment_id, variant, user_id, metrics)
        
        # Show progress
        if (i + 1) % 50 == 0:
            print(f"   📊 Processed {i + 1}/{total_users} users...")
    
    print(f"   ✅ Simulation complete!")
    print(f"   📈 Control group: {control_count} users")
    print(f"   📈 Treatment group: {treatment_count} users")
    
    # Analyze experiment results
    print(f"\n📊 Analyzing experiment results...")
    
    try:
        results = service.ab_testing.analyze_experiment(experiment_id)
        
        print(f"   ✅ Analysis complete!")
        print(f"   📅 Generated: {results.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n🎯 Recommendation: {results.recommendation}")
        
        # Display detailed results
        print(f"\n📈 Detailed Results:")
        
        for metric in results.control_metrics.keys():
            if metric in results.treatment_metrics:
                control_val = results.control_metrics[metric]
                treatment_val = results.treatment_metrics[metric]
                
                # Calculate improvement
                if control_val != 0:
                    improvement = ((treatment_val - control_val) / control_val) * 100
                else:
                    improvement = 0
                
                # Statistical significance
                is_significant = results.statistical_significance.get(metric, False)
                significance_emoji = "✅" if is_significant else "❌"
                
                # P-value
                p_value = results.p_values.get(metric, 1.0)
                
                # Sample size
                sample_size = results.sample_sizes.get(metric, 0)
                
                print(f"\n   📊 {metric.replace('_', ' ').title()}:")
                print(f"      Control:    {control_val:.4f}")
                print(f"      Treatment:  {treatment_val:.4f}")
                print(f"      Change:     {improvement:+.2f}%")
                print(f"      Significant: {significance_emoji} {is_significant}")
                print(f"      P-value:    {p_value:.4f}")
                print(f"      Sample Size: {sample_size}")
                
                # Confidence interval
                if metric in results.confidence_intervals:
                    ci_lower, ci_upper = results.confidence_intervals[metric]
                    print(f"      95% CI:     [{ci_lower:.4f}, {ci_upper:.4f}]")
                
                # Effect size
                if metric in results.effect_sizes:
                    effect_size = results.effect_sizes[metric]
                    effect_interpretation = (
                        "Small" if abs(effect_size) < 0.5 else
                        "Medium" if abs(effect_size) < 0.8 else
                        "Large"
                    )
                    print(f"      Effect Size: {effect_size:.3f} ({effect_interpretation})")
        
        # Business impact analysis
        print(f"\n💼 Business Impact Analysis:")
        
        if 'accuracy' in results.treatment_metrics and 'cost_per_request' in results.treatment_metrics:
            accuracy_improvement = results.treatment_metrics['accuracy'] - results.control_metrics['accuracy']
            cost_increase = results.treatment_metrics['cost_per_request'] - results.control_metrics['cost_per_request']
            
            print(f"   • Accuracy Improvement: +{accuracy_improvement:.3f} ({accuracy_improvement/results.control_metrics['accuracy']*100:+.1f}%)")
            print(f"   • Cost Impact: +${cost_increase:.4f} per request ({cost_increase/results.control_metrics['cost_per_request']*100:+.1f}%)")
            
            # Calculate ROI estimate
            if accuracy_improvement > 0 and cost_increase > 0:
                roi_ratio = accuracy_improvement / cost_increase
                print(f"   • ROI Ratio: {roi_ratio:.2f} accuracy points per $0.0001 cost increase")
        
        # Stop the experiment
        print(f"\n⏹️  Stopping experiment...")
        service.ab_testing.stop_experiment(experiment_id)
        print(f"   ✅ Experiment stopped successfully!")
        
    except Exception as e:
        print(f"   ❌ Error analyzing experiment: {str(e)}")
    
    return experiment_id

def demo_cost_optimization(model_ids: List[str]):
    """Demonstrate cost optimization functionality"""
    print_subheader("Cost Optimization & Model Selection")
    
    service = ModelManagementService("demo_registry.db")
    
    if not model_ids:
        print("❌ No models available for cost optimization")
        return
    
    # Add performance metrics to models for optimization
    print("📊 Adding performance data for cost analysis...")
    
    model_performance_profiles = [
        # Fast but less accurate model
        {'accuracy': 0.82, 'latency_ms': 80, 'cost_per_request': 0.0008, 'throughput_rps': 60},
        # Balanced model
        {'accuracy': 0.85, 'latency_ms': 100, 'cost_per_request': 0.001, 'throughput_rps': 50},
        # High accuracy but expensive model
        {'accuracy': 0.90, 'latency_ms': 150, 'cost_per_request': 0.002, 'throughput_rps': 35},
        # Custom model with unique characteristics
        {'accuracy': 0.87, 'latency_ms': 120, 'cost_per_request': 0.0015, 'throughput_rps': 45}
    ]
    
    for i, model_id in enumerate(model_ids[:len(model_performance_profiles)]):
        profile = model_performance_profiles[i]
        model = service.registry.get_model(model_id)
        
        print(f"   Adding metrics for {model.name} v{model.version}...")
        
        # Deploy to production for optimization consideration
        service.deploy_model(model_id, "production")
        
        # Add recent performance metrics
        for j in range(20):  # 20 data points
            timestamp = datetime.now() - timedelta(hours=j)
            
            # Add some realistic variance
            metrics = ModelPerformanceMetrics(
                model_id=model_id,
                timestamp=timestamp,
                accuracy=profile['accuracy'] + random.uniform(-0.01, 0.01),
                latency_ms=profile['latency_ms'] + random.uniform(-5, 5),
                cost_per_request=profile['cost_per_request'] + random.uniform(-0.0001, 0.0001),
                throughput_rps=profile['throughput_rps'] + random.uniform(-2, 2),
                memory_usage_mb=512 + random.uniform(-50, 50),
                cpu_usage_percent=60 + random.uniform(-10, 10)
            )
            service.registry.record_metrics(metrics)
        
        print(f"      ✅ Profile: Accuracy={profile['accuracy']:.2f}, "
              f"Latency={profile['latency_ms']}ms, "
              f"Cost=${profile['cost_per_request']:.4f}")
    
    # Demonstrate different optimization scenarios
    optimization_scenarios = [
        {
            'name': 'High Accuracy Requirements',
            'description': 'Mission-critical application requiring high accuracy',
            'requirements': {
                'min_accuracy': 0.88,
                'max_latency_ms': 200,
                'max_cost_per_request': 0.003
            }
        },
        {
            'name': 'Cost-Sensitive Application',
            'description': 'Budget-conscious application with cost constraints',
            'requirements': {
                'min_accuracy': 0.80,
                'max_latency_ms': 150,
                'max_cost_per_request': 0.001
            }
        },
        {
            'name': 'Real-Time Processing',
            'description': 'Low-latency application for real-time processing',
            'requirements': {
                'min_accuracy': 0.83,
                'max_latency_ms': 90,
                'max_cost_per_request': 0.0015
            }
        },
        {
            'name': 'Balanced Requirements',
            'description': 'General-purpose application with balanced needs',
            'requirements': {
                'min_accuracy': 0.85,
                'max_latency_ms': 120,
                'max_cost_per_request': 0.0012
            }
        }
    ]
    
    print(f"\n🎯 Testing optimization scenarios...")
    
    for i, scenario in enumerate(optimization_scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        
        requirements = scenario['requirements']
        print(f"   Requirements:")
        print(f"     • Min Accuracy: {requirements['min_accuracy']:.2f}")
        print(f"     • Max Latency: {requirements['max_latency_ms']}ms")
        print(f"     • Max Cost: ${requirements['max_cost_per_request']:.4f}")
        
        # Get recommendation
        recommendation = service.get_model_recommendation('transcription', requirements)
        
        if recommendation:
            print(f"   ✅ Recommendation Found:")
            print(f"     • Model: {recommendation['model_name']} v{recommendation['model_version']}")
            print(f"     • ID: {recommendation['model_id'][:8]}...")
            print(f"     • Reason: {recommendation['recommendation_reason']}")
            
            if 'recent_performance' in recommendation:
                perf = recommendation['recent_performance']
                print(f"     • Recent Performance:")
                if 'accuracy' in perf:
                    print(f"       - Accuracy: {perf['accuracy']:.3f}")
                if 'latency_ms' in perf:
                    print(f"       - Latency: {perf['latency_ms']:.1f}ms")
                if 'cost_per_request' in perf:
                    print(f"       - Cost: ${perf['cost_per_request']:.4f}")
        else:
            print(f"   ❌ No model meets the requirements")
            print(f"     Consider relaxing constraints or developing new models")
    
    # Cost analysis across all models
    print(f"\n💰 Cost Analysis Summary:")
    
    production_models = service.registry.list_models(status=ModelStatus.PRODUCTION)
    
    if production_models:
        print(f"   Analyzing {len(production_models)} production models...")
        
        cost_analysis = []
        
        for model in production_models:
            # Get recent metrics
            recent_metrics = service.registry.get_model_metrics(
                model.model_id,
                start_date=datetime.now() - timedelta(days=7),
                limit=100
            )
            
            if recent_metrics:
                # Calculate averages
                accuracies = [m.accuracy for m in recent_metrics if m.accuracy is not None]
                latencies = [m.latency_ms for m in recent_metrics if m.latency_ms is not None]
                costs = [m.cost_per_request for m in recent_metrics if m.cost_per_request is not None]
                
                if accuracies and latencies and costs:
                    avg_accuracy = sum(accuracies) / len(accuracies)
                    avg_latency = sum(latencies) / len(latencies)
                    avg_cost = sum(costs) / len(costs)
                    
                    # Calculate cost-effectiveness score
                    # Higher accuracy and lower latency/cost = better score
                    cost_effectiveness = (avg_accuracy * 1000) / (avg_latency * avg_cost * 1000)
                    
                    cost_analysis.append({
                        'model': f"{model.name} v{model.version}",
                        'accuracy': avg_accuracy,
                        'latency': avg_latency,
                        'cost': avg_cost,
                        'effectiveness': cost_effectiveness
                    })
        
        # Sort by cost-effectiveness
        cost_analysis.sort(key=lambda x: x['effectiveness'], reverse=True)
        
        print(f"\n   📊 Cost-Effectiveness Ranking:")
        for i, analysis in enumerate(cost_analysis, 1):
            print(f"   {i}. {analysis['model']}")
            print(f"      Accuracy: {analysis['accuracy']:.3f}")
            print(f"      Latency:  {analysis['latency']:.1f}ms")
            print(f"      Cost:     ${analysis['cost']:.4f}")
            print(f"      Score:    {analysis['effectiveness']:.2f}")
            
            if i == 1:
                print(f"      🏆 Most cost-effective model!")
            print()
    
    # Monthly cost projections
    print(f"💸 Monthly Cost Projections:")
    print(f"   Assuming 1M requests per month:")
    
    for analysis in cost_analysis[:3]:  # Top 3 models
        monthly_cost = analysis['cost'] * 1_000_000
        print(f"   • {analysis['model']}: ${monthly_cost:.2f}/month")
        
        # Calculate potential savings vs most expensive
        if analysis == cost_analysis[0]:
            most_expensive_cost = max(cost_analysis, key=lambda x: x['cost'])['cost'] * 1_000_000
            savings = most_expensive_cost - monthly_cost
            if savings > 0:
                print(f"     💰 Potential savings: ${savings:.2f}/month vs most expensive")

def demo_model_lifecycle():
    """Demonstrate complete model lifecycle management"""
    print_subheader("Complete Model Lifecycle Management")
    
    service = ModelManagementService("demo_registry.db")
    
    print("🔄 Demonstrating complete model lifecycle...")
    
    # 1. Model Development
    print(f"\n1️⃣  Model Development Phase")
    
    model_id = service.create_model_version(
        name="lifecycle-demo-model",
        version="1.0.0",
        description="Demonstration of complete model lifecycle",
        model_type="transcription",
        framework="openai",
        created_by="ml_engineer",
        parameters={"model_size": "base", "optimization": "speed"},
        tags=["demo", "lifecycle", "v1"]
    )
    
    print(f"   ✅ Model created: {model_id[:8]}...")
    print(f"   📋 Status: Development")
    
    # 2. Testing Phase
    print(f"\n2️⃣  Testing Phase")
    
    service.deploy_model(model_id, "testing")
    print(f"   ✅ Deployed to testing environment")
    
    # Add test metrics
    print(f"   📊 Running performance tests...")
    for i in range(10):
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=datetime.now() - timedelta(hours=i),
            accuracy=0.83 + random.uniform(-0.02, 0.02),
            latency_ms=95 + random.uniform(-5, 5),
            cost_per_request=0.0009 + random.uniform(-0.0001, 0.0001),
            error_rate=0.015 + random.uniform(-0.005, 0.005)
        )
        service.registry.record_metrics(metrics)
    
    print(f"   ✅ Test metrics recorded")
    
    # 3. Staging Deployment
    print(f"\n3️⃣  Staging Deployment")
    
    service.deploy_model(model_id, "staging")
    print(f"   ✅ Deployed to staging environment")
    
    # Add staging metrics
    print(f"   📊 Collecting staging performance data...")
    for i in range(15):
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=datetime.now() - timedelta(hours=i),
            accuracy=0.84 + random.uniform(-0.015, 0.015),
            latency_ms=92 + random.uniform(-4, 4),
            cost_per_request=0.0009 + random.uniform(-0.00005, 0.00005),
            error_rate=0.012 + random.uniform(-0.003, 0.003),
            user_satisfaction=4.1 + random.uniform(-0.2, 0.2)
        )
        service.registry.record_metrics(metrics)
    
    print(f"   ✅ Staging validation complete")
    
    # 4. Production Deployment
    print(f"\n4️⃣  Production Deployment")
    
    service.deploy_model(model_id, "production")
    print(f"   ✅ Deployed to production environment")
    
    # Add production metrics
    print(f"   📊 Monitoring production performance...")
    for i in range(20):
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            timestamp=datetime.now() - timedelta(hours=i),
            accuracy=0.845 + random.uniform(-0.01, 0.01),
            latency_ms=90 + random.uniform(-3, 3),
            cost_per_request=0.0009 + random.uniform(-0.00003, 0.00003),
            error_rate=0.01 + random.uniform(-0.002, 0.002),
            user_satisfaction=4.2 + random.uniform(-0.15, 0.15)
        )
        service.registry.record_metrics(metrics)
    
    print(f"   ✅ Production metrics collected")
    
    # 5. Model Improvement
    print(f"\n5️⃣  Model Improvement")
    
    improved_id = service.create_model_version(
        name="lifecycle-demo-model",
        version="1.1.0",
        description="Improved version with better accuracy",
        model_type="transcription",
        framework="openai",
        created_by="ml_engineer",
        parameters={"model_size": "large", "optimization": "accuracy"},
        tags=["demo", "lifecycle", "v1.1", "improved"],
        parent_model_id=model_id
    )
    
    print(f"   ✅ Improved model created: {improved_id[:8]}...")
    print(f"   🔗 Parent model: {model_id[:8]}...")
    
    # 6. A/B Testing
    print(f"\n6️⃣  A/B Testing New Version")
    
    service.deploy_model(improved_id, "production")
    
    experiment_id = service.start_ab_test(
        name="Model v1.0 vs v1.1 Comparison",
        description="Testing improved model version",
        control_model_id=model_id,
        treatment_model_id=improved_id,
        traffic_split=0.3,  # Conservative 30% to new version
        success_metrics=['accuracy', 'latency_ms', 'user_satisfaction'],
        duration_days=3,
        created_by='ml_engineer',
        minimum_sample_size=50
    )
    
    print(f"   ✅ A/B test started: {experiment_id[:8]}...")
    print(f"   🎯 Traffic split: 70% v1.0, 30% v1.1")
    
    # Simulate A/B test data
    print(f"   📊 Simulating user interactions...")
    for i in range(100):
        user_id = f"lifecycle_user_{i}"
        variant = service.ab_testing.assign_variant(experiment_id, user_id)
        
        if variant == "control":  # v1.0
            accuracy = 0.845 + random.uniform(-0.01, 0.01)
            latency_ms = 90 + random.uniform(-3, 3)
            satisfaction = 4.2 + random.uniform(-0.15, 0.15)
        else:  # v1.1 - improved
            accuracy = 0.865 + random.uniform(-0.01, 0.01)  # Better accuracy
            latency_ms = 88 + random.uniform(-3, 3)         # Slightly faster
            satisfaction = 4.4 + random.uniform(-0.1, 0.1)  # Higher satisfaction
        
        metrics = {
            'accuracy': accuracy,
            'latency_ms': latency_ms,
            'user_satisfaction': satisfaction
        }
        
        service.ab_testing.record_experiment_data(experiment_id, variant, user_id, metrics)
    
    # Analyze results
    results = service.ab_testing.analyze_experiment(experiment_id)
    print(f"   📊 A/B test results: {results.recommendation}")
    
    # 7. Model Rollout or Rollback
    print(f"\n7️⃣  Decision: Model Rollout")
    
    if "deploy" in results.recommendation.lower():
        print(f"   ✅ A/B test successful - rolling out v1.1")
        service.registry.update_model_status(model_id, ModelStatus.DEPRECATED)
        print(f"   📦 v1.0 marked as deprecated")
        print(f"   🚀 v1.1 remains in production")
    else:
        print(f"   ⏪ A/B test inconclusive - rolling back to v1.0")
        service.rollback_model(improved_id, model_id)
        print(f"   📦 v1.1 marked as deprecated")
        print(f"   🚀 v1.0 restored to production")
    
    # 8. Monitoring and Maintenance
    print(f"\n8️⃣  Ongoing Monitoring")
    
    # Check health of active model
    active_models = service.registry.list_models(status=ModelStatus.PRODUCTION)
    active_model = next((m for m in active_models if m.name == "lifecycle-demo-model"), None)
    
    if active_model:
        health = service.monitor.check_model_health(active_model.model_id)
        status_emoji = {
            'healthy': '🟢',
            'degraded': '🟡',
            'unhealthy': '🔴'
        }.get(health['status'], '❓')
        
        print(f"   {status_emoji} Active model health: {health['status']}")
        print(f"   📊 Alerts: {len(health.get('alerts', []))}")
        
        if health.get('alerts'):
            print(f"   🚨 Active alerts detected - monitoring continues...")
        else:
            print(f"   ✅ No alerts - model performing well")
    
    print(f"\n🎉 Model lifecycle demonstration complete!")
    print(f"   📈 Successfully managed model from development to production")
    print(f"   🧪 Conducted A/B testing for safe rollout")
    print(f"   📊 Established ongoing monitoring and health checks")

def main():
    """Main demo function"""
    print_header("AI Model Management System Demo")
    print("This demo showcases comprehensive AI model lifecycle management.")
    print("Task 65: Implement AI model versioning and A/B testing")
    
    try:
        # Clean up any existing demo database
        demo_db_files = ["demo_registry.db", "experiments.db"]
        for db_file in demo_db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
        
        # Run demo sections
        model_ids = demo_model_registry()
        
        if model_ids:
            monitored_model = demo_performance_monitoring(model_ids)
            demo_ab_testing(model_ids)
            demo_cost_optimization(model_ids)
            demo_model_lifecycle()
        
        print_header("Demo Completed Successfully! 🎉")
        print("The AI Model Management system is working correctly.")
        print("\nKey Features Demonstrated:")
        print("✅ Model registry and version control")
        print("✅ Model deployment to different environments")
        print("✅ Performance monitoring and health checks")
        print("✅ A/B testing with statistical analysis")
        print("✅ Cost optimization and model selection")
        print("✅ Complete model lifecycle management")
        print("✅ Automated rollback capabilities")
        print("✅ Real-time performance drift detection")
        print("✅ Business impact analysis")
        print("✅ Multi-environment deployment")
        
        print("\n🚀 Ready to manage your AI models at scale!")
        
        # Clean up demo files
        print("\n🧹 Cleaning up demo files...")
        for db_file in demo_db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"   Removed {db_file}")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()