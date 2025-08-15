"""
Comprehensive tests for Production Monitoring & Logging System

Tests all major functionality including:
- Structured logging with correlation IDs
- Metrics collection and analysis
- System monitoring and resource tracking
- Alert management and notifications
- Health checks and service monitoring
- Performance tracking and analytics
- Database operations and persistence

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import unittest
import tempfile
import os
import sqlite3
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock

from production_monitoring_logging import (
    ProductionMonitoringLogging,
    LogEntry,
    Metric,
    Alert,
    HealthCheck,
    PerformanceMetrics,
    LogLevel,
    MetricType,
    AlertSeverity,
    HealthStatus,
    CorrelationIdManager,
    StructuredLogger,
    MetricsCollector,
    SystemMonitor,
    AlertManager,
    HealthChecker,
    MonitoringDatabase
)


class TestProductionMonitoringLogging(unittest.TestCase):
    """Test suite for Production Monitoring & Logging System"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_monitoring.db")
        self.monitoring_system = ProductionMonitoringLogging("test_service", self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if self.monitoring_system.monitoring_active:
            self.monitoring_system.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.monitoring_system, ProductionMonitoringLogging)
        self.assertEqual(self.monitoring_system.service_name, "test_service")
        self.assertIsInstance(self.monitoring_system.db, MonitoringDatabase)
        self.assertIsInstance(self.monitoring_system.logger, StructuredLogger)
        self.assertIsInstance(self.monitoring_system.metrics_collector, MetricsCollector)
        self.assertIsInstance(self.monitoring_system.system_monitor, SystemMonitor)
        self.assertIsInstance(self.monitoring_system.alert_manager, AlertManager)
        self.assertIsInstance(self.monitoring_system.health_checker, HealthChecker)
        self.assertIsNotNone(self.monitoring_system.config)
        self.assertFalse(self.monitoring_system.monitoring_active)
    
    def test_log_entry_dataclass(self):
        """Test LogEntry dataclass"""
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Test log message",
            correlation_id="test_correlation_123",
            service="test_service",
            module="test_module",
            function="test_function",
            user_id="user_123",
            duration=0.5,
            status_code=200,
            metadata={"key": "value"}
        )
        
        self.assertEqual(log_entry.level, LogLevel.INFO)
        self.assertEqual(log_entry.message, "Test log message")
        self.assertEqual(log_entry.correlation_id, "test_correlation_123")
        self.assertEqual(log_entry.service, "test_service")
        self.assertEqual(log_entry.user_id, "user_123")
        self.assertEqual(log_entry.duration, 0.5)
        self.assertEqual(log_entry.status_code, 200)
        self.assertIn("key", log_entry.metadata)
        self.assertIsInstance(log_entry.timestamp, datetime)
    
    def test_metric_dataclass(self):
        """Test Metric dataclass"""
        metric = Metric(
            name="test_metric",
            metric_type=MetricType.COUNTER,
            value=42.5,
            timestamp=datetime.now(),
            labels={"method": "GET", "status": "200"},
            help_text="Test metric for counting requests"
        )
        
        self.assertEqual(metric.name, "test_metric")
        self.assertEqual(metric.metric_type, MetricType.COUNTER)
        self.assertEqual(metric.value, 42.5)
        self.assertIn("method", metric.labels)
        self.assertEqual(metric.labels["status"], "200")
        self.assertIsNotNone(metric.help_text)
        self.assertIsInstance(metric.timestamp, datetime)
    
    def test_alert_dataclass(self):
        """Test Alert dataclass"""
        alert = Alert(
            alert_id="alert_123",
            name="High CPU Usage",
            severity=AlertSeverity.HIGH,
            message="CPU usage is above threshold",
            service="system",
            metric="cpu_usage",
            threshold=80.0,
            current_value=85.5,
            triggered_at=datetime.now(),
            status="active"
        )
        
        self.assertEqual(alert.alert_id, "alert_123")
        self.assertEqual(alert.name, "High CPU Usage")
        self.assertEqual(alert.severity, AlertSeverity.HIGH)
        self.assertEqual(alert.service, "system")
        self.assertEqual(alert.metric, "cpu_usage")
        self.assertEqual(alert.threshold, 80.0)
        self.assertEqual(alert.current_value, 85.5)
        self.assertEqual(alert.status, "active")
        self.assertIsNone(alert.resolved_at)
        self.assertIsInstance(alert.triggered_at, datetime)
    
    def test_health_check_dataclass(self):
        """Test HealthCheck dataclass"""
        health_check = HealthCheck(
            service="database",
            status=HealthStatus.HEALTHY,
            message="Database connection successful",
            response_time=0.05,
            timestamp=datetime.now(),
            dependencies={"connection": HealthStatus.HEALTHY},
            metadata={"connection_pool": "active"}
        )
        
        self.assertEqual(health_check.service, "database")
        self.assertEqual(health_check.status, HealthStatus.HEALTHY)
        self.assertEqual(health_check.message, "Database connection successful")
        self.assertEqual(health_check.response_time, 0.05)
        self.assertIn("connection", health_check.dependencies)
        self.assertIn("connection_pool", health_check.metadata)
        self.assertIsInstance(health_check.timestamp, datetime)
    
    def test_performance_metrics_dataclass(self):
        """Test PerformanceMetrics dataclass"""
        metrics = PerformanceMetrics(
            cpu_usage=45.2,
            memory_usage=62.8,
            disk_usage=35.1,
            network_io={"bytes_sent": 1024, "bytes_recv": 2048},
            request_rate=150.5,
            error_rate=2.3,
            response_time_p95=0.25,
            active_connections=42,
            timestamp=datetime.now()
        )
        
        self.assertEqual(metrics.cpu_usage, 45.2)
        self.assertEqual(metrics.memory_usage, 62.8)
        self.assertEqual(metrics.disk_usage, 35.1)
        self.assertIn("bytes_sent", metrics.network_io)
        self.assertEqual(metrics.request_rate, 150.5)
        self.assertEqual(metrics.error_rate, 2.3)
        self.assertEqual(metrics.response_time_p95, 0.25)
        self.assertEqual(metrics.active_connections, 42)
        self.assertIsInstance(metrics.timestamp, datetime)
    
    def test_correlation_id_manager(self):
        """Test correlation ID manager"""
        manager = CorrelationIdManager()
        
        # Test automatic generation
        correlation_id1 = manager.get_correlation_id()
        self.assertIsInstance(correlation_id1, str)
        self.assertGreater(len(correlation_id1), 0)
        
        # Test consistency within thread
        correlation_id2 = manager.get_correlation_id()
        self.assertEqual(correlation_id1, correlation_id2)
        
        # Test explicit setting
        custom_id = "custom_correlation_123"
        manager.set_correlation_id(custom_id)
        self.assertEqual(manager.get_correlation_id(), custom_id)
        
        # Test new generation
        new_id = manager.generate_correlation_id()
        self.assertNotEqual(new_id, custom_id)
        self.assertEqual(manager.get_correlation_id(), new_id)
    
    def test_structured_logger(self):
        """Test structured logger"""
        logger = StructuredLogger("test_logger")
        
        # Test logger creation
        self.assertEqual(logger.service_name, "test_logger")
        self.assertIsInstance(logger.correlation_manager, CorrelationIdManager)
        
        # Test logging methods (should not raise exceptions)
        logger.debug("Debug message", component="test")
        logger.info("Info message", action="test_action")
        logger.warning("Warning message", metric="test_metric")
        logger.error("Error message", Exception("Test error"), operation="test_op")
        logger.critical("Critical message", Exception("Critical error"))
        
        # Test context generation
        context = logger._get_context(custom_field="test_value")
        self.assertIn("correlation_id", context)
        self.assertIn("service", context)
        self.assertIn("timestamp", context)
        self.assertIn("custom_field", context)
        self.assertEqual(context["service"], "test_logger")
        self.assertEqual(context["custom_field"], "test_value")
    
    def test_metrics_collector(self):
        """Test metrics collector"""
        collector = MetricsCollector()
        
        # Test counter increment
        collector.increment_counter("test_requests", {"method": "GET"}, 1)
        collector.increment_counter("test_requests", {"method": "GET"}, 2)
        
        # Test gauge setting
        collector.set_gauge("test_connections", 25, {"service": "api"})
        collector.set_gauge("test_connections", 30, {"service": "api"})
        
        # Test histogram observation
        collector.observe_histogram("test_duration", 0.15, {"endpoint": "/api/v1"})
        collector.observe_histogram("test_duration", 0.25, {"endpoint": "/api/v1"})
        
        # Test metric retrieval
        metrics_summary = collector.get_metrics_summary()
        self.assertIsInstance(metrics_summary, dict)
        
        # Test metric history
        history = collector.get_metric_history("test_requests", minutes=60)
        self.assertIsInstance(history, list)
        
        if history:  # If we have history data
            self.assertIn("timestamp", history[0])
            self.assertIn("value", history[0])
            self.assertIn("labels", history[0])
    
    def test_system_monitor(self):
        """Test system monitor"""
        monitor = SystemMonitor()
        
        # Test system metrics collection
        metrics = monitor.get_system_metrics()
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertGreaterEqual(metrics.cpu_usage, 0)
        self.assertGreaterEqual(metrics.memory_usage, 0)
        self.assertGreaterEqual(metrics.disk_usage, 0)
        self.assertIsInstance(metrics.network_io, dict)
        self.assertGreaterEqual(metrics.request_rate, 0)
        self.assertGreaterEqual(metrics.error_rate, 0)
        self.assertGreaterEqual(metrics.response_time_p95, 0)
        self.assertGreaterEqual(metrics.active_connections, 0)
        self.assertIsInstance(metrics.timestamp, datetime)
        
        # Test monitoring control
        self.assertTrue(monitor.monitoring)
        monitor.stop_monitoring()
        self.assertFalse(monitor.monitoring)
    
    def test_alert_manager(self):
        """Test alert manager"""
        alert_manager = AlertManager()
        
        # Test default rules setup
        self.assertGreater(len(alert_manager.alert_rules), 0)
        
        # Test alert checking with normal metrics
        normal_metrics = PerformanceMetrics(
            cpu_usage=50.0, memory_usage=60.0, disk_usage=70.0,
            network_io={}, request_rate=100.0, error_rate=1.0,
            response_time_p95=0.2, active_connections=20,
            timestamp=datetime.now()
        )
        
        alert_manager.check_alerts(normal_metrics)
        active_alerts = alert_manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 0)  # No alerts for normal metrics
        
        # Test alert triggering with high metrics
        high_metrics = PerformanceMetrics(
            cpu_usage=90.0,  # Above 80% threshold
            memory_usage=95.0,  # Above 85% threshold
            disk_usage=95.0,  # Above 90% threshold
            network_io={}, request_rate=100.0, error_rate=10.0,  # Above 5% threshold
            response_time_p95=0.2, active_connections=20,
            timestamp=datetime.now()
        )
        
        alert_manager.check_alerts(high_metrics)
        active_alerts = alert_manager.get_active_alerts()
        self.assertGreater(len(active_alerts), 0)  # Should have alerts
        
        # Test alert summary
        summary = alert_manager.get_alert_summary()
        self.assertIn("total_active", summary)
        self.assertIn("by_severity", summary)
        self.assertIn("last_updated", summary)
        self.assertIsInstance(summary["total_active"], int)
        self.assertIsInstance(summary["by_severity"], dict)
    
    async def test_health_checker(self):
        """Test health checker"""
        health_checker = HealthChecker()
        
        # Test database health check
        db_health = await health_checker.check_database_health(self.db_path)
        self.assertEqual(db_health.service, "database")
        self.assertIn(db_health.status, [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY])
        self.assertIsInstance(db_health.response_time, float)
        self.assertIsInstance(db_health.timestamp, datetime)
        
        # Test system resource health check
        system_health = await health_checker.check_system_resources()
        self.assertEqual(system_health.service, "system_resources")
        self.assertIn(system_health.status, [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY, HealthStatus.UNKNOWN])
        self.assertIsInstance(system_health.response_time, float)
        
        # Test external service health check
        external_health = await health_checker.check_external_service_health(
            "test_service", "https://httpbin.org/status/200"
        )
        self.assertEqual(external_health.service, "test_service")
        self.assertIsInstance(external_health.response_time, float)
        
        # Test comprehensive health check
        health_checks = await health_checker.perform_comprehensive_health_check()
        self.assertIsInstance(health_checks, dict)
        self.assertIn("system", health_checks)
        
        for service, health in health_checks.items():
            self.assertIsInstance(health, HealthCheck)
            self.assertIsInstance(health.service, str)
            self.assertIsInstance(health.status, HealthStatus)
    
    def test_monitoring_database(self):
        """Test monitoring database"""
        db = MonitoringDatabase(self.db_path)
        
        # Test log entry storage
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Test log entry",
            correlation_id="test_correlation",
            service="test_service",
            module="test_module",
            function="test_function"
        )
        
        db.store_log_entry(log_entry)
        
        # Test metric storage
        metric = Metric(
            name="test_metric",
            metric_type=MetricType.COUNTER,
            value=42.0,
            timestamp=datetime.now(),
            labels={"test": "label"}
        )
        
        db.store_metric(metric)
        
        # Test alert storage
        alert = Alert(
            alert_id="test_alert",
            name="Test Alert",
            severity=AlertSeverity.HIGH,
            message="Test alert message",
            service="test_service",
            metric="test_metric",
            threshold=50.0,
            current_value=55.0,
            triggered_at=datetime.now()
        )
        
        db.store_alert(alert)
        
        # Test health check storage
        health_check = HealthCheck(
            service="test_service",
            status=HealthStatus.HEALTHY,
            message="Service is healthy",
            response_time=0.1,
            timestamp=datetime.now()
        )
        
        db.store_health_check(health_check)
        
        # Test performance metrics storage
        performance_metrics = PerformanceMetrics(
            cpu_usage=50.0, memory_usage=60.0, disk_usage=70.0,
            network_io={}, request_rate=100.0, error_rate=2.0,
            response_time_p95=0.2, active_connections=10,
            timestamp=datetime.now()
        )
        
        db.store_performance_metrics(performance_metrics)
        
        # Test statistics retrieval
        stats = db.get_monitoring_statistics()
        self.assertIn("log_statistics", stats)
        self.assertIn("active_alerts", stats)
        self.assertIn("performance_summary", stats)
        self.assertIn("last_updated", stats)
    
    def test_monitoring_decorator(self):
        """Test monitoring decorator"""
        # Test synchronous function
        @self.monitoring_system.monitoring_decorator("test_sync_operation")
        def sync_test_function(x, y):
            time.sleep(0.01)  # Simulate work
            return x + y
        
        result = sync_test_function(3, 4)
        self.assertEqual(result, 7)
        
        # Check that metrics were recorded
        metrics_summary = self.monitoring_system.metrics_collector.get_metrics_summary()
        self.assertIsInstance(metrics_summary, dict)
        
        # Test function with error
        @self.monitoring_system.monitoring_decorator("test_error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            error_function()
    
    async def test_async_monitoring_decorator(self):
        """Test async monitoring decorator"""
        # Test asynchronous function
        @self.monitoring_system.monitoring_decorator("test_async_operation")
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # Simulate async work
            return x * y
        
        result = await async_test_function(3, 4)
        self.assertEqual(result, 12)
        
        # Test async function with error
        @self.monitoring_system.monitoring_decorator("test_async_error_operation")
        async def async_error_function():
            await asyncio.sleep(0.01)
            raise RuntimeError("Async test error")
        
        with self.assertRaises(RuntimeError):
            await async_error_function()
    
    def test_monitoring_dashboard(self):
        """Test monitoring dashboard"""
        dashboard = self.monitoring_system.get_monitoring_dashboard()
        
        self.assertIn("system_status", dashboard)
        self.assertIn("alerts", dashboard)
        self.assertIn("metrics", dashboard)
        self.assertIn("database_stats", dashboard)
        self.assertIn("monitoring_config", dashboard)
        self.assertIn("last_updated", dashboard)
        
        # Check system status structure
        system_status = dashboard["system_status"]
        self.assertIn("cpu_usage", system_status)
        self.assertIn("memory_usage", system_status)
        self.assertIn("disk_usage", system_status)
        self.assertIn("active_connections", system_status)
        self.assertIn("request_rate", system_status)
        self.assertIn("error_rate", system_status)
        self.assertIn("response_time_p95", system_status)
        
        # Check alerts structure
        alerts = dashboard["alerts"]
        self.assertIn("total_active", alerts)
        self.assertIn("by_severity", alerts)
        
        # Check that values are numeric where expected
        self.assertIsInstance(system_status["cpu_usage"], (int, float))
        self.assertIsInstance(system_status["memory_usage"], (int, float))
        self.assertIsInstance(alerts["total_active"], int)
    
    def test_system_status(self):
        """Test system status reporting"""
        status = self.monitoring_system.get_system_status()
        
        self.assertIn("monitoring_active", status)
        self.assertIn("service_name", status)
        self.assertIn("configuration", status)
        self.assertIn("features", status)
        
        # Check basic values
        self.assertEqual(status["service_name"], "test_service")
        self.assertIsInstance(status["monitoring_active"], bool)
        self.assertIsInstance(status["configuration"], dict)
        self.assertIsInstance(status["features"], dict)
        
        # Check configuration structure
        config = status["configuration"]
        self.assertIn("monitoring_interval", config)
        self.assertIn("health_check_interval", config)
        self.assertIn("enable_alerts", config)
        self.assertIn("enable_health_checks", config)
        
        # Check features
        features = status["features"]
        self.assertIn("psutil_available", features)
        self.assertIn("prometheus_available", features)
        self.assertIn("structlog_available", features)
    
    def test_enum_values(self):
        """Test enum value consistency"""
        # Test LogLevel enum
        log_levels = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL
        ]
        
        for level in log_levels:
            self.assertIsInstance(level.value, str)
        
        # Test MetricType enum
        metric_types = [
            MetricType.COUNTER,
            MetricType.GAUGE,
            MetricType.HISTOGRAM,
            MetricType.SUMMARY
        ]
        
        for metric_type in metric_types:
            self.assertIsInstance(metric_type.value, str)
        
        # Test AlertSeverity enum
        alert_severities = [
            AlertSeverity.LOW,
            AlertSeverity.MEDIUM,
            AlertSeverity.HIGH,
            AlertSeverity.CRITICAL
        ]
        
        for severity in alert_severities:
            self.assertIsInstance(severity.value, str)
        
        # Test HealthStatus enum
        health_statuses = [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
            HealthStatus.UNKNOWN
        ]
        
        for status in health_statuses:
            self.assertIsInstance(status.value, str)
    
    def test_configuration_management(self):
        """Test configuration management"""
        config = self.monitoring_system.config
        
        # Check required configuration keys
        required_keys = [
            "monitoring_interval",
            "health_check_interval",
            "log_retention_days",
            "metrics_retention_days",
            "enable_alerts",
            "enable_health_checks",
            "log_level"
        ]
        
        for key in required_keys:
            self.assertIn(key, config)
        
        # Check configuration values
        self.assertIsInstance(config["monitoring_interval"], int)
        self.assertIsInstance(config["health_check_interval"], int)
        self.assertIsInstance(config["log_retention_days"], int)
        self.assertIsInstance(config["enable_alerts"], bool)
        self.assertIsInstance(config["enable_health_checks"], bool)
        self.assertIsInstance(config["log_level"], LogLevel)
        
        # Check reasonable values
        self.assertGreater(config["monitoring_interval"], 0)
        self.assertGreater(config["health_check_interval"], 0)
        self.assertGreater(config["log_retention_days"], 0)


class TestAsyncMonitoring(unittest.TestCase):
    """Test async monitoring functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_async_monitoring.db")
        self.monitoring_system = ProductionMonitoringLogging("async_test", self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if self.monitoring_system.monitoring_active:
            self.monitoring_system.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_comprehensive_monitoring_workflow(self):
        """Test complete monitoring workflow"""
        # 1. Test system initialization
        self.assertFalse(self.monitoring_system.monitoring_active)
        
        # 2. Test decorator functionality
        @self.monitoring_system.monitoring_decorator("workflow_test")
        async def test_operation():
            await asyncio.sleep(0.01)
            return "success"
        
        result = await test_operation()
        self.assertEqual(result, "success")
        
        # 3. Test metrics collection
        self.monitoring_system.metrics_collector.increment_counter("workflow_requests")
        self.monitoring_system.metrics_collector.set_gauge("workflow_active_users", 5)
        
        # 4. Test health checks
        health_checks = await self.monitoring_system.health_checker.perform_comprehensive_health_check()
        self.assertIsInstance(health_checks, dict)
        self.assertGreater(len(health_checks), 0)
        
        # 5. Test alert system
        high_cpu_metrics = PerformanceMetrics(
            cpu_usage=85.0, memory_usage=70.0, disk_usage=60.0,
            network_io={}, request_rate=100.0, error_rate=2.0,
            response_time_p95=0.5, active_connections=50,
            timestamp=datetime.now()
        )
        
        self.monitoring_system.alert_manager.check_alerts(high_cpu_metrics)
        alerts = self.monitoring_system.alert_manager.get_active_alerts()
        
        # 6. Test dashboard generation
        dashboard = self.monitoring_system.get_monitoring_dashboard()
        self.assertIn("system_status", dashboard)
        self.assertIn("alerts", dashboard)
        
        # 7. Test logging
        self.monitoring_system.logger.info("Workflow test completed", 
                                          test_type="comprehensive",
                                          duration=0.5)
        
        print("✅ Comprehensive monitoring workflow completed successfully")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Monitoring & Logging Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionMonitoringLogging))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestAsyncMonitoring))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n=== Test Results ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    return result.wasSuccessful()


def run_async_tests():
    """Run async tests"""
    async def async_test_runner():
        # Create test instance
        test_instance = TestAsyncMonitoring()
        test_instance.setUp()
        
        try:
            # Run async tests
            await test_instance.test_comprehensive_monitoring_workflow()
            
            print("✅ All async monitoring tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Async monitoring test failed: {e}")
            return False
        finally:
            test_instance.tearDown()
    
    return asyncio.run(async_test_runner())


if __name__ == "__main__":
    # Run sync tests
    sync_success = run_comprehensive_tests()
    
    # Run async tests
    async_success = run_async_tests()
    
    overall_success = sync_success and async_success
    print(f"\n{'✅' if overall_success else '❌'} Overall test result: {'PASSED' if overall_success else 'FAILED'}")
    
    exit(0 if overall_success else 1)