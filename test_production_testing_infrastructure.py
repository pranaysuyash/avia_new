"""
Comprehensive tests for Production Testing Infrastructure System

Tests all major functionality including:
- Test case and suite management
- Test execution and reporting
- Performance benchmarking and load testing
- Security testing and vulnerability scanning
- Mock service management
- Test data generation
- Database operations and analytics

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

from production_testing_infrastructure import (
    ProductionTestingInfrastructure,
    TestCase,
    TestSuite,
    TestRun,
    PerformanceBenchmark,
    SecurityTestResult,
    TestType,
    TestStatus,
    TestPriority,
    MockServiceType,
    MockServiceManager,
    TestDataGenerator,
    PerformanceTester,
    SecurityTester,
    TestDatabase
)


class TestProductionTestingInfrastructure(unittest.TestCase):
    """Test suite for Production Testing Infrastructure"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_testing_infrastructure.db")
        self.testing_system = ProductionTestingInfrastructure(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsInstance(self.testing_system, ProductionTestingInfrastructure)
        self.assertIsInstance(self.testing_system.db, TestDatabase)
        self.assertIsInstance(self.testing_system.mock_service_manager, MockServiceManager)
        self.assertIsInstance(self.testing_system.test_data_generator, TestDataGenerator)
        self.assertIsInstance(self.testing_system.performance_tester, PerformanceTester)
        self.assertIsInstance(self.testing_system.security_tester, SecurityTester)
        self.assertIsNotNone(self.testing_system.config)
        self.assertGreater(len(self.testing_system.test_suites), 0)
    
    def test_test_case_dataclass(self):
        """Test TestCase dataclass"""
        test_case = TestCase(
            test_id="test_001",
            name="Test Authentication",
            description="Test user authentication flow",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH,
            module="auth_tests",
            function_name="test_user_auth",
            tags=["auth", "api"],
            metadata={"timeout": 30}
        )
        
        self.assertEqual(test_case.test_id, "test_001")
        self.assertEqual(test_case.name, "Test Authentication")
        self.assertEqual(test_case.test_type, TestType.INTEGRATION)
        self.assertEqual(test_case.priority, TestPriority.HIGH)
        self.assertEqual(test_case.status, TestStatus.PENDING)
        self.assertEqual(len(test_case.tags), 2)
        self.assertIn("timeout", test_case.metadata)
        self.assertIsInstance(test_case.created_at, datetime)
    
    def test_test_suite_dataclass(self):
        """Test TestSuite dataclass"""
        test_suite = TestSuite(
            suite_id="integration_suite",
            name="Integration Tests",
            description="API integration tests",
            parallel_execution=True,
            timeout=600,
            retry_count=1
        )
        
        self.assertEqual(test_suite.suite_id, "integration_suite")
        self.assertEqual(test_suite.name, "Integration Tests")
        self.assertTrue(test_suite.parallel_execution)
        self.assertEqual(test_suite.timeout, 600)
        self.assertEqual(test_suite.retry_count, 1)
        self.assertIsInstance(test_suite.created_at, datetime)
    
    def test_test_run_dataclass(self):
        """Test TestRun dataclass"""
        test_run = TestRun(
            run_id="run_001",
            suite_id="unit_tests",
            trigger="manual",
            status=TestStatus.RUNNING,
            started_at=datetime.now(),
            total_tests=10,
            passed_tests=8,
            failed_tests=1,
            skipped_tests=1
        )
        
        self.assertEqual(test_run.run_id, "run_001")
        self.assertEqual(test_run.suite_id, "unit_tests")
        self.assertEqual(test_run.trigger, "manual")
        self.assertEqual(test_run.status, TestStatus.RUNNING)
        self.assertEqual(test_run.total_tests, 10)
        self.assertEqual(test_run.passed_tests, 8)
        self.assertEqual(test_run.failed_tests, 1)
        self.assertEqual(test_run.skipped_tests, 1)
    
    def test_performance_benchmark_dataclass(self):
        """Test PerformanceBenchmark dataclass"""
        benchmark = PerformanceBenchmark(
            benchmark_id="bench_001",
            name="test_function",
            test_function="module.test_function",
            execution_time=0.5,
            memory_usage=10.2,
            cpu_usage=15.5,
            throughput=100.0,
            success_rate=95.0
        )
        
        self.assertEqual(benchmark.benchmark_id, "bench_001")
        self.assertEqual(benchmark.name, "test_function")
        self.assertEqual(benchmark.execution_time, 0.5)
        self.assertEqual(benchmark.memory_usage, 10.2)
        self.assertEqual(benchmark.cpu_usage, 15.5)
        self.assertEqual(benchmark.throughput, 100.0)
        self.assertEqual(benchmark.success_rate, 95.0)
        self.assertFalse(benchmark.performance_regression)
        self.assertIsInstance(benchmark.timestamp, datetime)
    
    def test_security_test_result_dataclass(self):
        """Test SecurityTestResult dataclass"""
        security_result = SecurityTestResult(
            test_id="sec_001",
            vulnerability_type="SQL Injection",
            severity="high",
            description="Potential SQL injection vulnerability",
            affected_component="User input validation",
            remediation="Use parameterized queries",
            status="open"
        )
        
        self.assertEqual(security_result.test_id, "sec_001")
        self.assertEqual(security_result.vulnerability_type, "SQL Injection")
        self.assertEqual(security_result.severity, "high")
        self.assertEqual(security_result.status, "open")
        self.assertIsInstance(security_result.discovered_at, datetime)
    
    def test_mock_service_manager(self):
        """Test mock service manager"""
        mock_manager = MockServiceManager()
        
        # Test mock data retrieval
        openai_response = mock_manager.get_mock_response(
            MockServiceType.OPENAI_API, "transcription"
        )
        self.assertIn("text", openai_response)
        self.assertIn("confidence", openai_response)
        
        # Test mock server creation
        server_info = mock_manager.create_mock_server(
            MockServiceType.GOOGLE_TRANSLATE, port=8081
        )
        self.assertEqual(server_info["port"], 8081)
        self.assertIn("endpoints", server_info)
        self.assertGreater(len(server_info["endpoints"]), 0)
        
        # Test OAuth mock data
        oauth_token = mock_manager.get_mock_response(
            MockServiceType.OAUTH_PROVIDER, "token"
        )
        self.assertIn("access_token", oauth_token)
        self.assertIn("expires_in", oauth_token)
    
    def test_test_data_generator(self):
        """Test test data generator"""
        data_generator = TestDataGenerator()
        
        # Test user data generation
        self.assertGreater(len(data_generator.test_users), 0)
        user = data_generator.test_users[0]
        self.assertIn("user_id", user)
        self.assertIn("email", user)
        self.assertIn("role", user)
        
        # Test audio file data
        self.assertGreater(len(data_generator.test_audio_files), 0)
        audio = data_generator.test_audio_files[0]
        self.assertIn("file_id", audio)
        self.assertIn("duration", audio)
        self.assertIn("speakers", audio)
        
        # Test transcript generation
        transcript = data_generator.generate_test_transcript(duration_minutes=5)
        self.assertIsInstance(transcript, str)
        self.assertGreater(len(transcript), 0)
        self.assertIn("Speaker", transcript)
        
        # Test performance test data generation
        perf_data = data_generator.generate_performance_test_data("medium")
        self.assertIn("test_audio", perf_data)
        self.assertIn("test_transcript", perf_data)
        self.assertIn("concurrent_users", perf_data)
        self.assertEqual(perf_data["concurrent_users"], 100)
    
    def test_performance_tester(self):
        """Test performance tester"""
        perf_tester = PerformanceTester()
        
        # Define test function
        def test_function(x, y):
            time.sleep(0.01)  # Simulate some work
            return x + y
        
        # Benchmark the function
        benchmark = perf_tester.benchmark_function(test_function, 2, 3)
        
        self.assertIsInstance(benchmark, PerformanceBenchmark)
        self.assertEqual(benchmark.name, "test_function")
        self.assertGreater(benchmark.execution_time, 0)
        self.assertGreaterEqual(benchmark.memory_usage, 0)
        self.assertGreaterEqual(benchmark.cpu_usage, 0)
        self.assertEqual(benchmark.success_rate, 100.0)
        
        # Test function with error
        def error_function():
            raise ValueError("Test error")
        
        error_benchmark = perf_tester.benchmark_function(error_function)
        self.assertEqual(error_benchmark.success_rate, 0.0)
        self.assertIn("error", error_benchmark.metadata)
    
    async def test_load_testing(self):
        """Test load testing functionality"""
        perf_tester = PerformanceTester()
        
        # Define target function
        def target_function():
            time.sleep(0.001)  # Very short simulation
            return "success"
        
        # Run load test
        results = await perf_tester.load_test(
            target_function, concurrent_users=3, duration_seconds=2
        )
        
        self.assertIn("concurrent_users", results)
        self.assertIn("duration", results)
        self.assertIn("total_requests", results)
        self.assertIn("successful_requests", results)
        self.assertIn("failed_requests", results)
        self.assertIn("average_response_time", results)
        self.assertIn("requests_per_second", results)
        
        self.assertEqual(results["concurrent_users"], 3)
        self.assertEqual(results["duration"], 2)
        self.assertGreater(results["total_requests"], 0)
        self.assertGreaterEqual(results["successful_requests"], 0)
    
    def test_security_tester(self):
        """Test security tester"""
        security_tester = SecurityTester()
        
        # Test security scan
        results = security_tester.run_security_scan("http://test.example.com")
        
        # Results should be empty for our mock tests (no vulnerabilities)
        self.assertIsInstance(results, list)
        # In our mock implementation, no vulnerabilities are found
        self.assertEqual(len(results), 0)
        
        # Test individual security test methods
        sql_result = security_tester._test_sql_injection("http://test.com")
        self.assertIsNone(sql_result)  # No vulnerability in mock
        
        xss_result = security_tester._test_xss_protection("http://test.com")
        self.assertIsNone(xss_result)  # No vulnerability in mock
    
    def test_database_operations(self):
        """Test database operations"""
        db = TestDatabase(self.db_path)
        
        # Test test case storage
        test_case = TestCase(
            test_id="db_test_001",
            name="Database Test Case",
            description="Test database operations",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM,
            module="db_tests",
            function_name="test_database"
        )
        
        case_id = db.create_test_case(test_case)
        self.assertEqual(case_id, test_case.test_id)
        
        # Test test run storage
        test_run = TestRun(
            run_id="db_run_001",
            suite_id="unit_tests",
            trigger="manual",
            status=TestStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_tests=5,
            passed_tests=4,
            failed_tests=1
        )
        
        run_id = db.create_test_run(test_run)
        self.assertEqual(run_id, test_run.run_id)
        
        # Test performance benchmark storage
        benchmark = PerformanceBenchmark(
            benchmark_id="db_bench_001",
            name="test_performance",
            test_function="module.test_performance",
            execution_time=0.25,
            memory_usage=15.0,
            cpu_usage=20.0
        )
        
        bench_id = db.store_performance_benchmark(benchmark)
        self.assertEqual(bench_id, benchmark.benchmark_id)
        
        # Test security test storage
        security_result = SecurityTestResult(
            test_id="db_sec_001",
            vulnerability_type="XSS",
            severity="medium",
            description="Cross-site scripting vulnerability",
            affected_component="Input forms",
            remediation="Sanitize user inputs",
            status="open"
        )
        
        sec_id = db.store_security_test(security_result)
        self.assertEqual(sec_id, security_result.test_id)
        
        # Test statistics retrieval
        stats = db.get_test_statistics()
        self.assertIn("test_statistics", stats)
        self.assertIn("recent_runs", stats)
        self.assertIn("performance_trends", stats)
        self.assertIn("security_status", stats)
    
    def test_test_case_creation(self):
        """Test test case creation"""
        test_case = self.testing_system.create_test_case(
            name="Sample Test",
            description="A sample test case",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH,
            module="sample_tests",
            function_name="test_sample",
            tags=["sample", "test"],
            metadata={"author": "test_user"}
        )
        
        self.assertIsInstance(test_case, TestCase)
        self.assertEqual(test_case.name, "Sample Test")
        self.assertEqual(test_case.test_type, TestType.INTEGRATION)
        self.assertEqual(test_case.priority, TestPriority.HIGH)
        self.assertEqual(len(test_case.tags), 2)
        self.assertIn("author", test_case.metadata)
    
    def test_test_suite_execution(self):
        """Test test suite execution"""
        # Test unit test suite
        unit_results = self.testing_system.run_test_suite("unit_tests")
        self.assertIsInstance(unit_results, TestRun)
        self.assertEqual(unit_results.suite_id, "unit_tests")
        self.assertIn(unit_results.status, [TestStatus.PASSED, TestStatus.FAILED])
        self.assertGreater(unit_results.total_tests, 0)
        self.assertIsNotNone(unit_results.execution_time)
        
        # Test integration test suite
        integration_results = self.testing_system.run_test_suite("integration_tests")
        self.assertIsInstance(integration_results, TestRun)
        self.assertEqual(integration_results.suite_id, "integration_tests")
        
        # Test performance test suite
        perf_results = self.testing_system.run_test_suite("performance_tests")
        self.assertIsInstance(perf_results, TestRun)
        self.assertEqual(perf_results.suite_id, "performance_tests")
        
        # Test security test suite
        security_results = self.testing_system.run_test_suite("security_tests")
        self.assertIsInstance(security_results, TestRun)
        self.assertEqual(security_results.suite_id, "security_tests")
    
    async def test_load_test_integration(self):
        """Test load testing integration"""
        def dummy_api_function():
            time.sleep(0.001)
            return {"status": "ok"}
        
        load_results = await self.testing_system.run_load_test(
            dummy_api_function, concurrent_users=2, duration_seconds=1
        )
        
        self.assertIn("total_requests", load_results)
        self.assertIn("successful_requests", load_results)
        self.assertIn("requests_per_second", load_results)
        self.assertGreater(load_results["total_requests"], 0)
    
    def test_test_report_generation(self):
        """Test test report generation"""
        # First run some tests to generate data
        self.testing_system.run_test_suite("unit_tests")
        self.testing_system.run_test_suite("integration_tests")
        
        # Generate report
        report = self.testing_system.generate_test_report()
        
        self.assertIn("report_id", report)
        self.assertIn("generated_at", report)
        self.assertIn("summary", report)
        self.assertIn("detailed_statistics", report)
        self.assertIn("recommendations", report)
        
        # Check summary fields
        summary = report["summary"]
        self.assertIn("total_test_cases", summary)
        self.assertIn("recent_test_runs", summary)
        self.assertIn("performance_health", summary)
        
        # Check recommendations
        recommendations = report["recommendations"]
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_system_status(self):
        """Test system status reporting"""
        status = self.testing_system.get_testing_status()
        
        self.assertEqual(status["infrastructure_status"], "operational")
        self.assertIn("available_test_suites", status)
        self.assertIn("configuration", status)
        self.assertIn("features", status)
        
        # Check test suites
        suites = status["available_test_suites"]
        self.assertIn("unit_tests", suites)
        self.assertIn("integration_tests", suites)
        self.assertIn("e2e_tests", suites)
        self.assertIn("performance_tests", suites)
        self.assertIn("security_tests", suites)
        
        # Check features
        features = status["features"]
        self.assertIn("pytest_available", features)
        self.assertIn("coverage_available", features)
        self.assertIn("http_testing", features)
    
    def test_enum_values(self):
        """Test enum value consistency"""
        # Test TestType enum
        test_types = [
            TestType.UNIT,
            TestType.INTEGRATION,
            TestType.END_TO_END,
            TestType.PERFORMANCE,
            TestType.SECURITY,
            TestType.LOAD,
            TestType.SMOKE,
            TestType.REGRESSION
        ]
        
        for test_type in test_types:
            self.assertIsInstance(test_type.value, str)
        
        # Test TestStatus enum
        test_statuses = [
            TestStatus.PENDING,
            TestStatus.RUNNING,
            TestStatus.PASSED,
            TestStatus.FAILED,
            TestStatus.SKIPPED,
            TestStatus.ERROR
        ]
        
        for status in test_statuses:
            self.assertIsInstance(status.value, str)
        
        # Test TestPriority enum
        test_priorities = [
            TestPriority.CRITICAL,
            TestPriority.HIGH,
            TestPriority.MEDIUM,
            TestPriority.LOW
        ]
        
        for priority in test_priorities:
            self.assertIsInstance(priority.value, str)
        
        # Test MockServiceType enum
        mock_services = [
            MockServiceType.OPENAI_API,
            MockServiceType.GOOGLE_TRANSLATE,
            MockServiceType.OAUTH_PROVIDER,
            MockServiceType.PAYMENT_GATEWAY,
            MockServiceType.EMAIL_SERVICE,
            MockServiceType.STORAGE_SERVICE
        ]
        
        for service in mock_services:
            self.assertIsInstance(service.value, str)
    
    def test_configuration_management(self):
        """Test configuration management"""
        config = self.testing_system.config
        
        # Check required configuration keys
        required_keys = [
            "parallel_execution",
            "max_workers", 
            "default_timeout",
            "retry_failed_tests",
            "generate_coverage_report",
            "run_security_tests",
            "performance_baseline",
            "test_environments"
        ]
        
        for key in required_keys:
            self.assertIn(key, config)
        
        # Check configuration values
        self.assertIsInstance(config["parallel_execution"], bool)
        self.assertIsInstance(config["max_workers"], int)
        self.assertIsInstance(config["default_timeout"], int)
        self.assertIsInstance(config["test_environments"], list)
        
        # Test environment list
        environments = config["test_environments"]
        self.assertIn("test", environments)
        self.assertIn("staging", environments)
        self.assertIn("production", environments)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test invalid test suite execution
        with self.assertRaises(ValueError):
            self.testing_system.run_test_suite("invalid_suite")
        
        # Test mock service with invalid service type
        mock_manager = MockServiceManager()
        invalid_response = mock_manager.get_mock_response(
            MockServiceType.OPENAI_API, "invalid_operation"
        )
        self.assertEqual(invalid_response, {})


class TestAsyncFunctionality(unittest.TestCase):
    """Test async functionality separately"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_async.db")
        self.testing_system = ProductionTestingInfrastructure(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    async def test_async_load_testing(self):
        """Test async load testing"""
        async def async_target_function():
            await asyncio.sleep(0.001)
            return "async result"
        
        perf_tester = PerformanceTester()
        results = await perf_tester.load_test(
            async_target_function, concurrent_users=2, duration_seconds=1
        )
        
        self.assertGreater(results["total_requests"], 0)
        self.assertGreaterEqual(results["successful_requests"], 0)
    
    async def test_comprehensive_testing_workflow(self):
        """Test complete testing workflow"""
        # 1. Create test cases
        test_case = self.testing_system.create_test_case(
            name="Comprehensive Test",
            description="End-to-end workflow test",
            test_type=TestType.END_TO_END,
            priority=TestPriority.CRITICAL,
            module="workflow_tests",
            function_name="test_comprehensive_workflow"
        )
        self.assertIsNotNone(test_case)
        
        # 2. Run multiple test suites
        suites_to_run = ["unit_tests", "integration_tests", "performance_tests"]
        results = []
        
        for suite_id in suites_to_run:
            result = self.testing_system.run_test_suite(suite_id)
            results.append(result)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, TestRun)
        
        # 3. Run load test
        def test_function():
            time.sleep(0.001)
            return "test"
        
        load_result = await self.testing_system.run_load_test(
            test_function, concurrent_users=2, duration_seconds=1
        )
        self.assertIn("total_requests", load_result)
        
        # 4. Generate comprehensive report
        report = self.testing_system.generate_test_report()
        self.assertIn("summary", report)
        self.assertIn("recommendations", report)
        
        print("✅ Comprehensive testing workflow completed successfully")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("=== Running Comprehensive Production Testing Infrastructure Tests ===\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestProductionTestingInfrastructure))
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestAsyncFunctionality))
    
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
        test_instance = TestAsyncFunctionality()
        test_instance.setUp()
        
        try:
            # Run async tests
            await test_instance.test_async_load_testing()
            await test_instance.test_comprehensive_testing_workflow()
            
            print("✅ All async tests passed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Async test failed: {e}")
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