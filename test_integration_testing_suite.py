"""
Test Suite for Integration Testing Suite

Comprehensive tests for the integration testing framework including:
- API endpoint validation testing
- Service integration testing validation
- Database integration testing validation
- Test reporting functionality validation
"""

import pytest
import asyncio
import json
import sqlite3
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import requests_mock

from integration_testing_suite import (
    IntegrationTestSuite, IntegrationTestCase, ServiceDependency,
    APIEndpointValidator, ServiceIntegrationTester, DatabaseIntegrationTester,
    IntegrationTestReporter, IntegrationTestResult, TestAssertion,
    IntegrationType, TestStatus, create_sample_test_cases
)

class TestIntegrationTestCase:
    """Test IntegrationTestCase data model"""
    
    def test_integration_test_case_creation(self):
        """Test creating an integration test case"""
        test_case = IntegrationTestCase(
            test_id="test_001",
            name="Sample Test",
            description="A sample test case",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://localhost:8000/api/test",
            method="GET",
            expected_status=200
        )
        
        assert test_case.test_id == "test_001"
        assert test_case.name == "Sample Test"
        assert test_case.integration_type == IntegrationType.API_ENDPOINT
        assert test_case.method == "GET"
        assert test_case.expected_status == 200
        assert test_case.headers == {}
        assert test_case.dependencies == []
    
    def test_integration_test_case_with_dependencies(self):
        """Test creating test case with dependencies"""
        test_case = IntegrationTestCase(
            test_id="test_002",
            name="Dependent Test",
            description="Test with dependencies",
            integration_type=IntegrationType.SERVICE_INTEGRATION,
            dependencies=["service_a", "service_b"]
        )
        
        assert test_case.dependencies == ["service_a", "service_b"]

class TestAPIEndpointValidator:
    """Test API endpoint validation functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create API endpoint validator"""
        return APIEndpointValidator()
    
    @pytest.fixture
    def sample_api_test_case(self):
        """Create sample API test case"""
        return IntegrationTestCase(
            test_id="api_test",
            name="API Test",
            description="Test API endpoint",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://test.example.com/api/health",
            method="GET",
            expected_status=200,
            expected_response={"status": "healthy"}
        )
    
    @pytest.mark.asyncio
    async def test_successful_api_validation(self, validator, sample_api_test_case):
        """Test successful API endpoint validation"""
        with requests_mock.Mocker() as m:
            # Mock successful API response
            m.get(
                "http://test.example.com/api/health",
                json={"status": "healthy"},
                status_code=200,
                headers={"Content-Type": "application/json"}
            )
            
            result = await validator.validate_endpoint(sample_api_test_case)
            
            assert result.status == TestStatus.PASSED
            assert result.test_case.test_id == "api_test"
            assert len(result.assertions) > 0
            
            # Check that status code assertion passed
            status_assertions = [a for a in result.assertions if "status" in a.assertion_id]
            assert len(status_assertions) > 0
            assert status_assertions[0].status == TestStatus.PASSED
    
    @pytest.mark.asyncio
    async def test_failed_api_validation_wrong_status(self, validator, sample_api_test_case):
        """Test API validation with wrong status code"""
        with requests_mock.Mocker() as m:
            # Mock API response with wrong status
            m.get(
                "http://test.example.com/api/health",
                json={"status": "unhealthy"},
                status_code=500
            )
            
            result = await validator.validate_endpoint(sample_api_test_case)
            
            assert result.status == TestStatus.FAILED
            
            # Check that status code assertion failed
            status_assertions = [a for a in result.assertions if "status" in a.assertion_id]
            assert len(status_assertions) > 0
            assert status_assertions[0].status == TestStatus.FAILED
            assert status_assertions[0].expected == 200
            assert status_assertions[0].actual == 500
    
    @pytest.mark.asyncio
    async def test_api_validation_connection_error(self, validator, sample_api_test_case):
        """Test API validation with connection error"""
        # Use invalid URL to trigger connection error
        sample_api_test_case.endpoint_url = "http://invalid.nonexistent.domain/api/health"
        
        result = await validator.validate_endpoint(sample_api_test_case)
        
        assert result.status == TestStatus.ERROR
        assert result.error_details is not None
        assert len(result.assertions) > 0
        
        # Check that error assertion was created
        error_assertions = [a for a in result.assertions if a.status == TestStatus.ERROR]
        assert len(error_assertions) > 0
    
    @pytest.mark.asyncio
    async def test_response_structure_validation(self, validator):
        """Test response structure validation"""
        test_case = IntegrationTestCase(
            test_id="structure_test",
            name="Structure Test",
            description="Test response structure",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://test.example.com/api/data",
            method="GET",
            expected_status=200,
            expected_response={
                "id": 123,
                "name": "test",
                "active": True
            }
        )
        
        with requests_mock.Mocker() as m:
            # Mock response with matching structure
            m.get(
                "http://test.example.com/api/data",
                json={"id": 123, "name": "test", "active": True},
                status_code=200
            )
            
            result = await validator.validate_endpoint(test_case)
            
            assert result.status == TestStatus.PASSED
            
            # Check structure assertions
            structure_assertions = [a for a in result.assertions if "structure" in a.assertion_id]
            assert len(structure_assertions) > 0
    
    def test_response_structure_validation_logic(self, validator):
        """Test response structure validation logic"""
        expected = {"id": 123, "name": "test", "active": True}
        actual = {"id": 123, "name": "test", "active": True}
        
        assertions = validator._validate_response_structure("test", expected, actual)
        
        # Should have type and value assertions for each key
        assert len(assertions) >= len(expected) * 2
        
        # All assertions should pass
        passed_assertions = [a for a in assertions if a.status == TestStatus.PASSED]
        assert len(passed_assertions) == len(assertions)
    
    def test_response_structure_validation_type_mismatch(self, validator):
        """Test response structure validation with type mismatch"""
        expected = {"id": 123, "name": "test"}
        actual = {"id": "123", "name": "test"}  # id is string instead of int
        
        assertions = validator._validate_response_structure("test", expected, actual)
        
        # Should have failed type assertion for id
        failed_assertions = [a for a in assertions if a.status == TestStatus.FAILED]
        assert len(failed_assertions) > 0
        
        # Check specific type assertion failure
        id_type_assertions = [a for a in failed_assertions if "id_type" in a.assertion_id]
        assert len(id_type_assertions) > 0

class TestServiceIntegrationTester:
    """Test service integration testing functionality"""
    
    @pytest.fixture
    def tester(self):
        """Create service integration tester"""
        return ServiceIntegrationTester()
    
    @pytest.fixture
    def sample_dependencies(self):
        """Create sample service dependencies"""
        return [
            ServiceDependency(
                service_name="auth_service",
                endpoint="http://auth.example.com",
                health_check_path="/health",
                required=True
            ),
            ServiceDependency(
                service_name="data_service",
                endpoint="http://data.example.com",
                health_check_path="/health",
                required=True
            ),
            ServiceDependency(
                service_name="cache_service",
                endpoint="http://cache.example.com",
                health_check_path="/health",
                required=False
            )
        ]
    
    def test_add_dependency(self, tester, sample_dependencies):
        """Test adding service dependencies"""
        for dep in sample_dependencies:
            tester.add_dependency(dep)
        
        assert len(tester.dependencies) == 3
        assert "auth_service" in tester.dependencies
        assert "data_service" in tester.dependencies
        assert "cache_service" in tester.dependencies
    
    @pytest.mark.asyncio
    async def test_check_dependencies_success(self, tester, sample_dependencies):
        """Test successful dependency checking"""
        for dep in sample_dependencies:
            tester.add_dependency(dep)
        
        with requests_mock.Mocker() as m:
            # Mock all health checks as successful
            m.get("http://auth.example.com/health", status_code=200)
            m.get("http://data.example.com/health", status_code=200)
            m.get("http://cache.example.com/health", status_code=200)
            
            results = await tester.check_dependencies()
            
            assert len(results) == 3
            assert all(results.values())  # All should be True
    
    @pytest.mark.asyncio
    async def test_check_dependencies_failure(self, tester, sample_dependencies):
        """Test dependency checking with failures"""
        for dep in sample_dependencies:
            tester.add_dependency(dep)
        
        with requests_mock.Mocker() as m:
            # Mock mixed health check results
            m.get("http://auth.example.com/health", status_code=200)
            m.get("http://data.example.com/health", status_code=500)
            m.get("http://cache.example.com/health", status_code=200)
            
            results = await tester.check_dependencies()
            
            assert results["auth_service"] is True
            assert results["data_service"] is False
            assert results["cache_service"] is True
    
    @pytest.mark.asyncio
    async def test_service_integration_test_success(self, tester, sample_dependencies):
        """Test successful service integration test"""
        for dep in sample_dependencies:
            tester.add_dependency(dep)
        
        test_case = IntegrationTestCase(
            test_id="integration_test",
            name="Integration Test",
            description="Test service integration",
            integration_type=IntegrationType.SERVICE_INTEGRATION,
            dependencies=["auth_service", "data_service"]
        )
        
        with requests_mock.Mocker() as m:
            # Mock successful health checks
            m.get("http://auth.example.com/health", status_code=200)
            m.get("http://data.example.com/health", status_code=200)
            m.get("http://cache.example.com/health", status_code=200)
            
            result = await tester.test_service_integration(test_case)
            
            assert result.status == TestStatus.PASSED
            assert len(result.assertions) > 0
            
            # Check dependency assertions
            dep_assertions = [a for a in result.assertions if "dep_" in a.assertion_id]
            assert len(dep_assertions) >= 2  # At least auth_service and data_service
    
    @pytest.mark.asyncio
    async def test_service_integration_test_required_dependency_failure(self, tester, sample_dependencies):
        """Test service integration test with required dependency failure"""
        for dep in sample_dependencies:
            tester.add_dependency(dep)
        
        test_case = IntegrationTestCase(
            test_id="integration_test",
            name="Integration Test",
            description="Test service integration",
            integration_type=IntegrationType.SERVICE_INTEGRATION,
            dependencies=["auth_service", "data_service"]
        )
        
        with requests_mock.Mocker() as m:
            # Mock auth service failure
            m.get("http://auth.example.com/health", status_code=500)
            m.get("http://data.example.com/health", status_code=200)
            m.get("http://cache.example.com/health", status_code=200)
            
            result = await tester.test_service_integration(test_case)
            
            assert result.status == TestStatus.FAILED
            assert "Required dependency" in result.error_details

class TestDatabaseIntegrationTester:
    """Test database integration testing functionality"""
    
    @pytest.fixture
    def tester(self):
        """Create database integration tester"""
        return DatabaseIntegrationTester(":memory:")
    
    def test_setup_test_database(self, tester):
        """Test database setup"""
        tester.setup_test_database()
        
        # Verify tables were created
        cursor = tester.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "test_users" in tables
        assert "test_transcriptions" in tables
    
    @pytest.mark.asyncio
    async def test_database_connection_test(self, tester):
        """Test database connection testing"""
        tester.setup_test_database()
        
        assertion = await tester._test_database_connection("test")
        
        assert assertion.status == TestStatus.PASSED
        assert "connection" in assertion.assertion_id
    
    @pytest.mark.asyncio
    async def test_crud_operations(self, tester):
        """Test CRUD operations testing"""
        tester.setup_test_database()
        
        assertions = await tester._test_crud_operations("test")
        
        # Should have assertions for INSERT, SELECT, UPDATE, DELETE
        assert len(assertions) >= 4
        
        # All CRUD operations should pass
        passed_assertions = [a for a in assertions if a.status == TestStatus.PASSED]
        assert len(passed_assertions) == len(assertions)
    
    @pytest.mark.asyncio
    async def test_transaction_integrity(self, tester):
        """Test transaction integrity testing"""
        tester.setup_test_database()
        
        assertions = await tester._test_transaction_integrity("test")
        
        # Should have rollback and commit assertions
        rollback_assertions = [a for a in assertions if "rollback" in a.assertion_id]
        commit_assertions = [a for a in assertions if "commit" in a.assertion_id]
        
        assert len(rollback_assertions) > 0
        assert len(commit_assertions) > 0
        
        # Both should pass
        assert all(a.status == TestStatus.PASSED for a in rollback_assertions)
        assert all(a.status == TestStatus.PASSED for a in commit_assertions)
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, tester):
        """Test foreign key constraint testing"""
        tester.setup_test_database()
        
        assertions = await tester._test_foreign_key_constraints("test")
        
        # Should have valid and invalid FK assertions
        valid_fk_assertions = [a for a in assertions if "fk_valid" in a.assertion_id]
        invalid_fk_assertions = [a for a in assertions if "fk_invalid" in a.assertion_id]
        
        assert len(valid_fk_assertions) > 0
        assert len(invalid_fk_assertions) > 0
        
        # Valid FK should pass, invalid FK should pass (because it properly failed)
        assert all(a.status == TestStatus.PASSED for a in valid_fk_assertions)
        assert all(a.status == TestStatus.PASSED for a in invalid_fk_assertions)
    
    @pytest.mark.asyncio
    async def test_complete_database_integration(self, tester):
        """Test complete database integration test"""
        test_case = IntegrationTestCase(
            test_id="db_test",
            name="Database Test",
            description="Complete database integration test",
            integration_type=IntegrationType.DATABASE_INTEGRATION
        )
        
        result = await tester.test_database_integration(test_case)
        
        assert result.status == TestStatus.PASSED
        assert len(result.assertions) > 0
        assert result.execution_time > 0
        
        # Should have assertions for all database test categories
        assertion_categories = set()
        for assertion in result.assertions:
            if "connection" in assertion.assertion_id:
                assertion_categories.add("connection")
            elif "crud" in assertion.assertion_id:
                assertion_categories.add("crud")
            elif "transaction" in assertion.assertion_id:
                assertion_categories.add("transaction")
            elif "fk" in assertion.assertion_id:
                assertion_categories.add("fk")
        
        assert len(assertion_categories) >= 3  # Should test multiple categories

class TestIntegrationTestReporter:
    """Test integration test reporting functionality"""
    
    @pytest.fixture
    def reporter(self):
        """Create integration test reporter"""
        return IntegrationTestReporter()
    
    @pytest.fixture
    def sample_results(self):
        """Create sample test results"""
        results = []
        
        for i in range(3):
            test_case = IntegrationTestCase(
                test_id=f"test_{i}",
                name=f"Test {i}",
                description=f"Test case {i}",
                integration_type=IntegrationType.API_ENDPOINT
            )
            
            assertions = [
                TestAssertion(
                    assertion_id=f"test_{i}_assertion_1",
                    description="First assertion",
                    expected="expected",
                    actual="expected" if i < 2 else "different",
                    status=TestStatus.PASSED if i < 2 else TestStatus.FAILED
                )
            ]
            
            result = IntegrationTestResult(
                test_case=test_case,
                status=TestStatus.PASSED if i < 2 else TestStatus.FAILED,
                assertions=assertions,
                execution_time=1.0 + i,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
            
            results.append(result)
        
        return results
    
    def test_add_result(self, reporter, sample_results):
        """Test adding results to reporter"""
        for result in sample_results:
            reporter.add_result(result)
        
        assert len(reporter.results) == 3
    
    def test_generate_summary_report(self, reporter, sample_results):
        """Test generating summary report"""
        for result in sample_results:
            reporter.add_result(result)
        
        report = reporter.generate_summary_report()
        
        # Check report structure
        assert "summary" in report
        assert "test_results" in report
        assert "failure_analysis" in report
        assert "generated_at" in report
        
        # Check summary data
        summary = report["summary"]
        assert summary["total_tests"] == 3
        assert summary["passed_tests"] == 2
        assert summary["failed_tests"] == 1
        assert summary["success_rate"] == (2/3) * 100
    
    def test_failure_analysis(self, reporter, sample_results):
        """Test failure analysis generation"""
        for result in sample_results:
            reporter.add_result(result)
        
        report = reporter.generate_summary_report()
        failure_analysis = report["failure_analysis"]
        
        assert "failure_patterns" in failure_analysis
        assert "error_categories" in failure_analysis
        assert "recommendations" in failure_analysis
        
        # Should have failure patterns for API endpoints
        assert "api_endpoint" in failure_analysis["failure_patterns"]
    
    def test_save_report(self, reporter, sample_results, tmp_path):
        """Test saving report to file"""
        for result in sample_results:
            reporter.add_result(result)
        
        report_file = tmp_path / "test_report.json"
        reporter.save_report(str(report_file))
        
        # Verify file was created and contains valid JSON
        assert report_file.exists()
        
        with open(report_file) as f:
            saved_report = json.load(f)
        
        assert "summary" in saved_report
        assert saved_report["summary"]["total_tests"] == 3

class TestIntegrationTestSuite:
    """Test complete integration test suite functionality"""
    
    @pytest.fixture
    def suite(self):
        """Create integration test suite"""
        return IntegrationTestSuite()
    
    def test_add_test_case(self, suite):
        """Test adding test cases to suite"""
        test_case = IntegrationTestCase(
            test_id="test_001",
            name="Test Case",
            description="A test case",
            integration_type=IntegrationType.API_ENDPOINT
        )
        
        suite.add_test_case(test_case)
        
        assert len(suite.test_cases) == 1
        assert suite.test_cases[0].test_id == "test_001"
    
    def test_add_service_dependency(self, suite):
        """Test adding service dependencies"""
        dependency = ServiceDependency(
            service_name="test_service",
            endpoint="http://test.example.com",
            health_check_path="/health"
        )
        
        suite.add_service_dependency(dependency)
        
        assert "test_service" in suite.service_tester.dependencies
    
    @pytest.mark.asyncio
    async def test_run_all_tests_empty_suite(self, suite):
        """Test running tests with empty suite"""
        report = await suite.run_all_tests()
        
        assert report["summary"]["total_tests"] == 0
        assert report["summary"]["success_rate"] == 0
    
    @pytest.mark.asyncio
    async def test_run_all_tests_with_cases(self, suite):
        """Test running tests with test cases"""
        # Add sample test cases
        test_cases = create_sample_test_cases()
        for test_case in test_cases:
            suite.add_test_case(test_case)
        
        # Mock external dependencies
        with requests_mock.Mocker() as m:
            # Mock all HTTP requests
            m.get(requests_mock.ANY, status_code=200, json={"status": "ok"})
            m.post(requests_mock.ANY, status_code=201, json={"upload_id": "123", "status": "uploaded"})
            
            report = await suite.run_all_tests()
            
            assert report["summary"]["total_tests"] > 0
            assert len(report["test_results"]) > 0
    
    def test_cleanup(self, suite):
        """Test suite cleanup"""
        # Add a test case that uses database
        test_case = IntegrationTestCase(
            test_id="db_test",
            name="DB Test",
            description="Database test",
            integration_type=IntegrationType.DATABASE_INTEGRATION
        )
        suite.add_test_case(test_case)
        
        # Setup database
        suite.db_tester.setup_test_database()
        
        # Cleanup should not raise errors
        suite.cleanup()

class TestSampleTestCases:
    """Test sample test case generation"""
    
    def test_create_sample_test_cases(self):
        """Test creating sample test cases"""
        test_cases = create_sample_test_cases()
        
        assert len(test_cases) > 0
        
        # Check that we have different types of tests
        integration_types = set(tc.integration_type for tc in test_cases)
        assert IntegrationType.API_ENDPOINT in integration_types
        assert IntegrationType.SERVICE_INTEGRATION in integration_types
        assert IntegrationType.DATABASE_INTEGRATION in integration_types
        
        # Verify test case structure
        for test_case in test_cases:
            assert test_case.test_id
            assert test_case.name
            assert test_case.description
            assert isinstance(test_case.integration_type, IntegrationType)

@pytest.mark.asyncio
async def test_end_to_end_integration_testing():
    """End-to-end integration testing workflow"""
    # Create suite
    suite = IntegrationTestSuite()
    
    # Add service dependencies
    suite.add_service_dependency(ServiceDependency(
        service_name="test_service",
        endpoint="http://test.example.com",
        health_check_path="/health"
    ))
    
    # Add test cases
    test_cases = [
        IntegrationTestCase(
            test_id="e2e_api_test",
            name="E2E API Test",
            description="End-to-end API test",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://test.example.com/api/test",
            method="GET",
            expected_status=200
        ),
        IntegrationTestCase(
            test_id="e2e_db_test",
            name="E2E Database Test",
            description="End-to-end database test",
            integration_type=IntegrationType.DATABASE_INTEGRATION
        )
    ]
    
    for test_case in test_cases:
        suite.add_test_case(test_case)
    
    # Mock external calls
    with requests_mock.Mocker() as m:
        m.get("http://test.example.com/health", status_code=200)
        m.get("http://test.example.com/api/test", status_code=200, json={"result": "success"})
        
        # Run tests
        report = await suite.run_all_tests()
        
        # Verify results
        assert report["summary"]["total_tests"] == 2
        assert "test_results" in report
        assert "failure_analysis" in report
        
        # Cleanup
        suite.cleanup()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])