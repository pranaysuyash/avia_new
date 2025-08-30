#!/usr/bin/env python3
"""
Demo script for AI Performance Monitoring System
Demonstrates comprehensive performance monitoring capabilities
"""

import asyncio
import time
import random
from datetime import datetime, timedelta
from typing import List

from ai_performance_monitoring import (
    PerformanceMonitor, RequestMetrics, AlertThreshold, 
    MetricType, AlertSeverity, ResourceUsage
)

class PerformanceMonitoringDemo:
    """Comprehensive demo of AI Performance Monitoring System"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor(max_history_size=1000)
        self.models = [
            "gpt-4", "gpt-3.5-turbo", "claude-3-opus", 
            "claude-3-sonnet", "local-llama-7b", "local-llama-13b"
        ]
        self.providers = {
            "gpt-4": "openai",
            "gpt-3.5-turbo": "openai", 
            "claude-3-opus": "anthropic",
            "claude-3-sonnet": "anthropic",
            "local-llama-7b": "local",
            "local-llama-13b": "local"
        }
    
    async def run_complete_demo(self):
        """Run complete performance monitoring demonstration"""
        print("🚀 AI Performance Monitoring System Demo")
        print("=" * 60)
        
        # Start monitoring
        print("\n1. Starting Performance Monitor...")
        self.monitor.start_monitoring()
        print("✅ Monitor started successfully")
        
        # Configure alerts
        print("\n2. Configuring Alert Thresholds...")
        await self._setup_alert_thresholds()
        print("✅ Alert thresholds configured")
        
        # Generate sample data
        print("\n3. Generating Sample Performance Data...")
        await self._generate_sample_data()
        print("✅ Sample data generated")
        
        # Demonstrate real-time monitoring
        print("\n4. Real-time Performance Monitoring...")
        await self._demonstrate_realtime_monitoring()
        
        # Demonstrate analytics
        print("\n5. Performance Analytics...")
        await self._demonstrate_analytics()
        
        # Demonstrate trend analysis
        print("\n6. Trend Analysis...")
        await self._demonstrate_trend_analysis()
        
        # Demonstrate model comparison
        print("\n7. Model Comparison...")
        await self._demonstrate_model_comparison()
        
        # Demonstrate alert system
        print("\n8. Alert System...")
        await self._demonstrate_alert_system()
        
        # Export metrics
        print("\n9. Metrics Export...")
        await self._demonstrate_export()
        
        # Clean up
        print("\n10. Cleanup...")
        self.monitor.stop_monitoring()
        print("✅ Demo completed successfully!")
    
    async def _setup_alert_thresholds(self):
        """Set up alert thresholds for monitoring"""
        thresholds = [
            # Latency alerts
            AlertThreshold(
                metric_type=MetricType.LATENCY,
                threshold_value=1000.0,  # 1 second
                comparison="gt",
                severity=AlertSeverity.HIGH
            ),
            AlertThreshold(
                metric_type=MetricType.LATENCY,
                threshold_value=2000.0,  # 2 seconds
                comparison="gt",
                severity=AlertSeverity.CRITICAL
            ),
            # Error rate alerts
            AlertThreshold(
                metric_type=MetricType.ERROR_RATE,
                threshold_value=10.0,  # 10%
                comparison="gt",
                severity=AlertSeverity.MEDIUM
            ),
            # Cost alerts
            AlertThreshold(
                metric_type=MetricType.COST,
                threshold_value=0.1,  # $0.10 per request
                comparison="gt",
                severity=AlertSeverity.HIGH
            )
        ]
        
        for model in self.models:
            for threshold in thresholds:
                self.monitor.set_alert_threshold(model, threshold)
        
        print(f"   📊 Configured {len(thresholds)} alert types for {len(self.models)} models")
    
    async def _generate_sample_data(self):
        """Generate realistic sample performance data"""
        print("   📈 Generating performance data...")
        
        # Generate data over the last 24 hours
        base_time = datetime.now() - timedelta(hours=24)
        total_requests = 500
        
        for i in range(total_requests):
            # Select random model
            model = random.choice(self.models)
            provider = self.providers[model]
            
            # Generate realistic metrics based on model type
            latency_ms = self._generate_realistic_latency(model)
            success = self._generate_success_rate(model)
            cost = self._generate_realistic_cost(model)
            quality_score = self._generate_quality_score(model)
            
            # Create request timestamp
            request_time = base_time + timedelta(
                minutes=random.randint(0, 24 * 60)
            )
            
            request_metrics = RequestMetrics(
                request_id=f"demo_{i:04d}",
                model_id=model,
                provider=provider,
                start_time=request_time,
                end_time=request_time + timedelta(milliseconds=latency_ms),
                latency_ms=latency_ms,
                success=success,
                input_tokens=random.randint(50, 2000),
                output_tokens=random.randint(20, 800),
                cost=cost,
                quality_score=quality_score,
                resource_usage=ResourceUsage(
                    cpu_percent=random.uniform(10, 90),
                    memory_mb=random.uniform(100, 2000),
                    gpu_percent=random.uniform(0, 100) if "local" in model else 0,
                    network_mbps=random.uniform(1, 100),
                    storage_mb=random.uniform(50, 500)
                )
            )
            
            self.monitor.track_request(request_metrics)
            
            # Show progress
            if (i + 1) % 100 == 0:
                print(f"   📊 Generated {i + 1}/{total_requests} requests...")
        
        print(f"   ✅ Generated {total_requests} sample requests")
    
    async def _demonstrate_realtime_monitoring(self):
        """Demonstrate real-time monitoring capabilities"""
        print("   🔄 Real-time monitoring demonstration...")
        
        for model in self.models[:3]:  # Show top 3 models
            realtime_data = self.monitor.get_realtime_metrics(model)
            
            if realtime_data:
                print(f"   📊 {model}:")
                print(f"      Throughput: {realtime_data.get('current_throughput', 0):.2f} RPS")
                print(f"      Avg Latency: {realtime_data.get('avg_latency', 0):.1f} ms")
                print(f"      Error Rate: {realtime_data.get('error_rate', 0):.2f}%")
                print(f"      Total Requests: {realtime_data.get('total_requests', 0):,}")
            else:
                print(f"   ⚠️  No real-time data for {model}")
    
    async def _demonstrate_analytics(self):
        """Demonstrate performance analytics"""
        print("   📊 Performance analytics demonstration...")
        
        for model in self.models[:2]:  # Analyze top 2 models
            metrics = self.monitor.get_performance_metrics(
                model, 
                timeframe=timedelta(hours=24)
            )
            
            if metrics:
                print(f"\n   📈 Analytics for {model}:")
                print(f"      Total Requests: {metrics.total_requests:,}")
                print(f"      Success Rate: {(metrics.successful_requests/metrics.total_requests)*100:.1f}%")
                print(f"      Avg Latency: {metrics.avg_latency_ms:.1f} ms")
                print(f"      P95 Latency: {metrics.p95_latency_ms:.1f} ms")
                print(f"      P99 Latency: {metrics.p99_latency_ms:.1f} ms")
                print(f"      Throughput: {metrics.throughput_rps:.2f} RPS")
                print(f"      Total Cost: ${metrics.total_cost:.4f}")
                print(f"      Avg Cost/Request: ${metrics.avg_cost_per_request:.6f}")
                print(f"      Avg Quality Score: {metrics.avg_quality_score:.3f}")
                print(f"      CPU Usage: {metrics.resource_usage.cpu_percent:.1f}%")
                print(f"      Memory Usage: {metrics.resource_usage.memory_mb:.1f} MB")
            else:
                print(f"   ⚠️  No analytics data for {model}")
    
    async def _demonstrate_trend_analysis(self):
        """Demonstrate trend analysis capabilities"""
        print("   📉 Trend analysis demonstration...")
        
        metrics_to_analyze = [MetricType.LATENCY, MetricType.ERROR_RATE, MetricType.COST]
        
        for model in self.models[:2]:
            print(f"\n   📊 Trend Analysis for {model}:")
            
            for metric_type in metrics_to_analyze:
                trend = self.monitor.analyze_trends(
                    model, 
                    metric_type, 
                    period=timedelta(hours=12)
                )
                
                if trend:
                    direction_emoji = {
                        "improving": "📈",
                        "degrading": "📉",
                        "stable": "➡️"
                    }
                    
                    print(f"      {metric_type.value.replace('_', ' ').title()}:")
                    print(f"        Direction: {direction_emoji.get(trend.trend_direction, '❓')} {trend.trend_direction}")
                    print(f"        Strength: {trend.trend_strength:.2f}")
                    print(f"        Prediction: {trend.prediction:.2f}")
                    print(f"        Confidence: {trend.confidence:.2f}")
                    print(f"        Data Points: {trend.data_points}")
                else:
                    print(f"      {metric_type.value}: No trend data available")
    
    async def _demonstrate_model_comparison(self):
        """Demonstrate model comparison capabilities"""
        print("   ⚖️  Model comparison demonstration...")
        
        comparison_metrics = [MetricType.LATENCY, MetricType.COST, MetricType.THROUGHPUT]
        
        for metric_type in comparison_metrics:
            print(f"\n   📊 Comparing models by {metric_type.value.replace('_', ' ').title()}:")
            
            comparison = self.monitor.get_model_comparison(
                self.models, 
                metric_type, 
                timeframe=timedelta(hours=6)
            )
            
            if comparison and comparison.get("rankings"):
                rankings = comparison["rankings"]
                
                print(f"      Best Model: 🏆 {comparison.get('best_model', 'Unknown')}")
                print("      Rankings:")
                
                for i, (model, data) in enumerate(rankings[:5], 1):
                    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1] if i <= 5 else f"{i}."
                    print(f"        {medal} {model}: {data['value']:.3f} ({data['total_requests']} requests)")
            else:
                print(f"      No comparison data available for {metric_type.value}")
    
    async def _demonstrate_alert_system(self):
        """Demonstrate alert system capabilities"""
        print("   🚨 Alert system demonstration...")
        
        # Generate some high-latency requests to trigger alerts
        print("   📊 Generating high-latency requests to trigger alerts...")
        
        for i in range(5):
            high_latency_request = RequestMetrics(
                request_id=f"alert_trigger_{i}",
                model_id=random.choice(self.models),
                provider="openai",
                start_time=datetime.now() - timedelta(seconds=2),
                end_time=datetime.now() - timedelta(seconds=1),
                latency_ms=random.uniform(1500, 3000),  # High latency to trigger alerts
                success=random.random() > 0.2,  # Some failures
                cost=random.uniform(0.05, 0.15),  # High cost
                quality_score=random.uniform(0.6, 0.9)
            )
            
            self.monitor.track_request(high_latency_request)
        
        # Wait a moment for alert processing
        await asyncio.sleep(1)
        
        # Show active alerts
        active_alerts = self.monitor.get_active_alerts()
        
        if active_alerts:
            print(f"   🚨 Found {len(active_alerts)} active alerts:")
            
            for alert in active_alerts[:5]:  # Show first 5 alerts
                severity_emoji = {
                    AlertSeverity.LOW: "🟡",
                    AlertSeverity.MEDIUM: "🟠", 
                    AlertSeverity.HIGH: "🔴",
                    AlertSeverity.CRITICAL: "🚨"
                }
                
                print(f"      {severity_emoji.get(alert.severity, '⚪')} {alert.severity.value.upper()}: {alert.message}")
                print(f"         Model: {alert.model_id}")
                print(f"         Time: {alert.timestamp.strftime('%H:%M:%S')}")
                print(f"         Resolved: {'✅' if alert.resolved else '❌'}")
        else:
            print("   ✅ No active alerts found")
    
    async def _demonstrate_export(self):
        """Demonstrate metrics export capabilities"""
        print("   📤 Metrics export demonstration...")
        
        # Export metrics
        export_data = self.monitor.export_metrics("json")
        
        # Show export summary
        import json
        try:
            data = json.loads(export_data)
            print(f"   📊 Export Summary:")
            print(f"      Timestamp: {data.get('timestamp', 'Unknown')}")
            print(f"      Total Requests: {data.get('total_requests', 0):,}")
            print(f"      Active Alerts: {data.get('active_alerts', 0)}")
            print(f"      Models Tracked: {len(data.get('models', {}))}")
            print(f"      Export Size: {len(export_data):,} characters")
        except json.JSONDecodeError:
            print("   ⚠️  Error parsing export data")
        
        # Save to file
        filename = f"performance_metrics_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                f.write(export_data)
            print(f"   💾 Metrics exported to: {filename}")
        except Exception as e:
            print(f"   ⚠️  Error saving export file: {e}")
    
    def _generate_realistic_latency(self, model: str) -> float:
        """Generate realistic latency based on model type"""
        base_latencies = {
            "gpt-4": 800,
            "gpt-3.5-turbo": 400,
            "claude-3-opus": 1200,
            "claude-3-sonnet": 600,
            "local-llama-7b": 200,
            "local-llama-13b": 400
        }
        
        base = base_latencies.get(model, 500)
        # Add some variance
        return max(50, random.gauss(base, base * 0.3))
    
    def _generate_success_rate(self, model: str) -> bool:
        """Generate realistic success rates"""
        success_rates = {
            "gpt-4": 0.98,
            "gpt-3.5-turbo": 0.97,
            "claude-3-opus": 0.96,
            "claude-3-sonnet": 0.97,
            "local-llama-7b": 0.92,
            "local-llama-13b": 0.94
        }
        
        rate = success_rates.get(model, 0.95)
        return random.random() < rate
    
    def _generate_realistic_cost(self, model: str) -> float:
        """Generate realistic costs based on model type"""
        base_costs = {
            "gpt-4": 0.06,
            "gpt-3.5-turbo": 0.002,
            "claude-3-opus": 0.075,
            "claude-3-sonnet": 0.015,
            "local-llama-7b": 0.001,
            "local-llama-13b": 0.002
        }
        
        base = base_costs.get(model, 0.01)
        # Add some variance
        return max(0.0001, random.gauss(base, base * 0.2))
    
    def _generate_quality_score(self, model: str) -> float:
        """Generate realistic quality scores"""
        base_quality = {
            "gpt-4": 0.95,
            "gpt-3.5-turbo": 0.88,
            "claude-3-opus": 0.93,
            "claude-3-sonnet": 0.90,
            "local-llama-7b": 0.82,
            "local-llama-13b": 0.86
        }
        
        base = base_quality.get(model, 0.85)
        # Add some variance but keep in valid range
        return max(0.1, min(1.0, random.gauss(base, 0.05)))

async def run_quick_demo():
    """Run a quick demonstration of key features"""
    print("🚀 Quick AI Performance Monitoring Demo")
    print("=" * 50)
    
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Add some sample requests
    models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
    
    print("📊 Adding sample requests...")
    for i in range(20):
        model = random.choice(models)
        
        request = RequestMetrics(
            request_id=f"quick_{i:03d}",
            model_id=model,
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=2),
            end_time=datetime.now() - timedelta(seconds=1),
            latency_ms=random.uniform(100, 800),
            success=random.random() > 0.05,
            cost=random.uniform(0.001, 0.05),
            quality_score=random.uniform(0.8, 1.0)
        )
        
        monitor.track_request(request)
    
    # Show metrics for each model
    print("\n📈 Performance Metrics:")
    for model in models:
        metrics = monitor.get_performance_metrics(model)
        if metrics:
            print(f"  {model}:")
            print(f"    Requests: {metrics.total_requests}")
            print(f"    Avg Latency: {metrics.avg_latency_ms:.1f} ms")
            print(f"    Success Rate: {(metrics.successful_requests/metrics.total_requests)*100:.1f}%")
            print(f"    Total Cost: ${metrics.total_cost:.4f}")
    
    # Model comparison
    print("\n⚖️  Model Comparison (Latency):")
    comparison = monitor.get_model_comparison(models, MetricType.LATENCY)
    if comparison and comparison.get("rankings"):
        for i, (model, data) in enumerate(comparison["rankings"], 1):
            print(f"  {i}. {model}: {data['value']:.1f} ms")
    
    monitor.stop_monitoring()
    print("\n✅ Quick demo completed!")

async def main():
    """Main demo function"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        await run_quick_demo()
    else:
        demo = PerformanceMonitoringDemo()
        await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main())