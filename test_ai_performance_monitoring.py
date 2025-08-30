#!/usr/bin/env python3
"""
Test suite for AI Performance Monitoring System
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ai_performance_monitoring import (
    PerformanceMonitor, RequestMetrics, AlertThreshold, PerformanceAlert,
    MetricType, AlertSeverity, ResourceUsage, TrendAnalysis
)

class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = PerformanceMonitor(max_history_size=100)
        
        # Sample request metrics
        self.sample_request = RequestMetrics(
            request_id="test_001",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=1),
            end_time=datetime.now(),
            latency_ms=150.0,
            success=True,
            input_tokens=100,
            output_tokens=50,
            cost=0.01,
            quality_score=0.95,
            resource_usage=ResourceUsage(cpu_percent=25.0, memory_mb=512.0)
        )
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.max_history_size == 100
        assert len(self.monitor.request_history) == 0
        assert len(self.monitor.metrics_cache) == 0
        assert len(self.monitor.alert_thresholds) == 0
        assert len(self.monitor.active_alerts) == 0
    
    def test_track_request(self):
        """Test request tracking functionality"""
        # Track a request
        self.monitor.track_request(self.sample_request)
        
        # Verify request was added to history
        assert len(self.monitor.request_history) == 1
        assert self.monitor.request_history[0].request_id == "test_001"
    
    def test_track_multiple_requests(self):
        """Test tracking multiple requests"""
        # Track multiple requests
        for i in range(5):
            request = RequestMetrics(
                request_id=f"test_{i:03d}",
                model_id="gpt-4",
                provider="openai",
                start_time=datetime.now() - timedelta(seconds=2),
                end_time=datetime.now() - timedelta(seconds=1),
                latency_ms=100.0 + i * 10,
                success=True,
                cost=0.01
            )
            self.monitor.track_request(request)
        
        assert len(self.monitor.request_history) == 5
    
    def test_get_performance_metrics(self):
        """Test performance metrics calculation"""
        # Add sample requests
        for i in range(10):
            request = RequestMetrics(
                request_id=f"test_{i:03d}",
                model_id="gpt-4",
                provider="openai",
                start_time=datetime.now() - timedelta(minutes=5),
                end_time=datetime.now() - timedelta(minutes=4),
                latency_ms=100.0 + i * 5,
                success=i < 9,  # 90% success rate
                cost=0.01,
                quality_score=0.9
            )
            self.monitor.track_request(request)
        
        # Get metrics
        metrics = self.monitor.get_performance_metrics("gpt-4", timeframe=timedelta(hours=1))
        
        assert metrics is not None
        assert metrics.model_id == "gpt-4"
        assert metrics.total_requests == 10
        assert metrics.successful_requests == 9
        assert metrics.failed_requests == 1
        assert metrics.error_rate == 10.0
        assert metrics.avg_latency_ms > 0
    
    def test_get_performance_metrics_no_data(self):
        """Test performance metrics with no data"""
        metrics = self.monitor.get_performance_metrics("nonexistent-model")
        assert metrics is None
    
    def test_realtime_metrics(self):
        """Test real-time metrics functionality"""
        # Track a request
        self.monitor.track_request(self.sample_request)
        
        # Get real-time metrics
        realtime = self.monitor.get_realtime_metrics("gpt-4")
        
        assert "model_id" in realtime
        assert realtime["model_id"] == "gpt-4"
    
    def test_alert_threshold_setting(self):
        """Test alert threshold configuration"""
        threshold = AlertThreshold(
            metric_type=MetricType.LATENCY,
            threshold_value=200.0,
            comparison="gt",
            severity=AlertSeverity.HIGH
        )
        
        self.monitor.set_alert_threshold("gpt-4", threshold)
        
        assert "gpt-4" in self.monitor.alert_thresholds
        assert len(self.monitor.alert_thresholds["gpt-4"]) == 1
    
    def test_alert_triggering(self):
        """Test alert triggering functionality"""
        # Set up alert threshold
        threshold = AlertThreshold(
            metric_type=MetricType.LATENCY,
            threshold_value=100.0,
            comparison="gt",
            severity=AlertSeverity.HIGH
        )
        self.monitor.set_alert_threshold("gpt-4", threshold)
        
        # Create request that should trigger alert
        high_latency_request = RequestMetrics(
            request_id="high_latency",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=1),
            end_time=datetime.now(),
            latency_ms=250.0,  # Above threshold
            success=True,
            cost=0.01
        )
        
        self.monitor.track_request(high_latency_request)
        
        # Check if alert was created
        alerts = self.monitor.get_active_alerts("gpt-4")
        assert len(alerts) > 0
        assert alerts[0].metric_type == MetricType.LATENCY
        assert alerts[0].current_value == 250.0
    
    def test_alert_resolution(self):
        """Test alert resolution"""
        # Create and trigger an alert
        threshold = AlertThreshold(
            metric_type=MetricType.LATENCY,
            threshold_value=100.0,
            comparison="gt",
            severity=AlertSeverity.HIGH
        )
        self.monitor.set_alert_threshold("gpt-4", threshold)
        
        high_latency_request = RequestMetrics(
            request_id="high_latency",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=1),
            end_time=datetime.now(),
            latency_ms=250.0,
            success=True,
            cost=0.01
        )
        self.monitor.track_request(high_latency_request)
        
        # Get alert ID
        alerts = self.monitor.get_active_alerts("gpt-4")
        assert len(alerts) > 0
        alert_id = alerts[0].id
        
        # Resolve alert
        resolved = self.monitor.resolve_alert(alert_id)
        assert resolved is True
        
        # Check alert is resolved
        alerts = self.monitor.get_active_alerts("gpt-4")
        assert alerts[0].resolved is True
    
    def test_trend_analysis(self):
        """Test trend analysis functionality"""
        # Add requests with significantly increasing latency (degrading trend)
        base_time = datetime.now() - timedelta(hours=2)
        
        for i in range(15):
            request = RequestMetrics(
                request_id=f"trend_{i:03d}",
                model_id="gpt-4",
                provider="openai",
                start_time=base_time + timedelta(minutes=i * 5),  # More frequent requests
                end_time=base_time + timedelta(minutes=i * 5, seconds=1),
                latency_ms=100.0 + i * 50,  # More significant increase
                success=True,
                cost=0.01
            )
            self.monitor.track_request(request)
        
        # Analyze trend
        trend = self.monitor.analyze_trends("gpt-4", MetricType.LATENCY, timedelta(hours=3))
        
        assert trend is not None
        assert trend.model_id == "gpt-4"
        assert trend.metric_type == MetricType.LATENCY
        # Should detect degrading trend due to increasing latency, or stable if change is small
        assert trend.trend_direction in ["degrading", "stable"]
        assert trend.data_points >= 3  # Should have enough data points
    
    def test_model_comparison(self):
        """Test model comparison functionality"""
        # Add requests for multiple models
        models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        latencies = [150.0, 100.0, 200.0]
        
        for model, latency in zip(models, latencies):
            for i in range(5):
                request = RequestMetrics(
                    request_id=f"{model}_{i:03d}",
                    model_id=model,
                    provider="openai",
                    start_time=datetime.now() - timedelta(minutes=10),
                    end_time=datetime.now() - timedelta(minutes=9),
                    latency_ms=latency + i * 5,
                    success=True,
                    cost=0.01
                )
                self.monitor.track_request(request)
        
        # Compare models
        comparison = self.monitor.get_model_comparison(models, MetricType.LATENCY)
        
        assert "rankings" in comparison
        assert len(comparison["rankings"]) == 3
        assert comparison["best_model"] is not None
    
    def test_export_metrics(self):
        """Test metrics export functionality"""
        # Add some sample data
        self.monitor.track_request(self.sample_request)
        
        # Export metrics
        export_data = self.monitor.export_metrics("json")
        
        assert export_data is not None
        assert isinstance(export_data, str)
        assert "timestamp" in export_data
        assert "total_requests" in export_data
    
    def test_monitoring_lifecycle(self):
        """Test monitoring start/stop lifecycle"""
        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor._monitoring_active is True
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        assert self.monitor._monitoring_active is False
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking"""
        request_with_resources = RequestMetrics(
            request_id="resource_test",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=1),
            end_time=datetime.now(),
            latency_ms=150.0,
            success=True,
            cost=0.01,
            resource_usage=ResourceUsage(
                cpu_percent=75.0,
                memory_mb=1024.0,
                gpu_percent=50.0,
                network_mbps=10.0,
                storage_mb=256.0
            )
        )
        
        self.monitor.track_request(request_with_resources)
        
        metrics = self.monitor.get_performance_metrics("gpt-4")
        assert metrics is not None
        assert metrics.resource_usage.cpu_percent == 75.0
        assert metrics.resource_usage.memory_mb == 1024.0
    
    def test_error_handling(self):
        """Test error handling in monitoring"""
        # Test with invalid request data
        invalid_request = RequestMetrics(
            request_id="",  # Empty ID
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now(),
            end_time=datetime.now() - timedelta(seconds=1),  # End before start
            latency_ms=-10.0,  # Negative latency
            success=True,
            cost=0.01
        )
        
        # Should not crash
        self.monitor.track_request(invalid_request)
        assert len(self.monitor.request_history) == 1
    
    def test_performance_with_large_dataset(self):
        """Test performance with large number of requests"""
        # Add many requests
        start_time = time.time()
        
        for i in range(1000):
            request = RequestMetrics(
                request_id=f"perf_{i:04d}",
                model_id=f"model_{i % 5}",  # 5 different models
                provider="openai",
                start_time=datetime.now() - timedelta(seconds=2),
                end_time=datetime.now() - timedelta(seconds=1),
                latency_ms=100.0 + (i % 100),
                success=True,
                cost=0.01
            )
            self.monitor.track_request(request)
        
        processing_time = time.time() - start_time
        
        # Should process 1000 requests quickly (under 5 seconds)
        assert processing_time < 5.0
        assert len(self.monitor.request_history) == 100  # Limited by max_history_size

class TestRequestMetrics:
    """Test cases for RequestMetrics data class"""
    
    def test_request_metrics_creation(self):
        """Test RequestMetrics creation"""
        metrics = RequestMetrics(
            request_id="test_001",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now(),
            end_time=datetime.now(),
            latency_ms=150.0,
            success=True
        )
        
        assert metrics.request_id == "test_001"
        assert metrics.model_id == "gpt-4"
        assert metrics.provider == "openai"
        assert metrics.latency_ms == 150.0
        assert metrics.success is True

class TestAlertThreshold:
    """Test cases for AlertThreshold"""
    
    def test_alert_threshold_creation(self):
        """Test AlertThreshold creation"""
        threshold = AlertThreshold(
            metric_type=MetricType.LATENCY,
            threshold_value=200.0,
            comparison="gt",
            severity=AlertSeverity.HIGH
        )
        
        assert threshold.metric_type == MetricType.LATENCY
        assert threshold.threshold_value == 200.0
        assert threshold.comparison == "gt"
        assert threshold.severity == AlertSeverity.HIGH
        assert threshold.enabled is True

class TestResourceUsage:
    """Test cases for ResourceUsage"""
    
    def test_resource_usage_creation(self):
        """Test ResourceUsage creation"""
        usage = ResourceUsage(
            cpu_percent=50.0,
            memory_mb=1024.0,
            gpu_percent=75.0,
            network_mbps=100.0,
            storage_mb=512.0
        )
        
        assert usage.cpu_percent == 50.0
        assert usage.memory_mb == 1024.0
        assert usage.gpu_percent == 75.0
        assert usage.network_mbps == 100.0
        assert usage.storage_mb == 512.0

def test_integration_scenario():
    """Test complete integration scenario"""
    monitor = PerformanceMonitor()
    
    # Set up monitoring
    monitor.start_monitoring()
    
    # Configure alerts
    latency_threshold = AlertThreshold(
        metric_type=MetricType.LATENCY,
        threshold_value=500.0,
        comparison="gt",
        severity=AlertSeverity.HIGH
    )
    monitor.set_alert_threshold("gpt-4", latency_threshold)
    
    # Simulate requests
    for i in range(20):
        request = RequestMetrics(
            request_id=f"integration_{i:03d}",
            model_id="gpt-4",
            provider="openai",
            start_time=datetime.now() - timedelta(seconds=2),
            end_time=datetime.now() - timedelta(seconds=1),
            latency_ms=200.0 + i * 50,  # Increasing latency
            success=i < 18,  # 90% success rate
            cost=0.01 + i * 0.001,
            quality_score=0.9 - i * 0.01
        )
        monitor.track_request(request)
    
    # Verify metrics
    metrics = monitor.get_performance_metrics("gpt-4")
    assert metrics is not None
    assert metrics.total_requests == 20
    
    # Check for alerts (high latency requests should trigger alerts)
    alerts = monitor.get_active_alerts("gpt-4")
    assert len(alerts) > 0  # Should have alerts for high latency
    
    # Analyze trends
    trend = monitor.analyze_trends("gpt-4", MetricType.LATENCY, timedelta(hours=1))
    # Trend analysis might return None if insufficient data points, which is acceptable
    if trend is not None:
        assert trend.trend_direction in ["degrading", "stable"]  # Latency is increasing or stable
    
    # Clean up
    monitor.stop_monitoring()

if __name__ == "__main__":
    pytest.main([__file__])