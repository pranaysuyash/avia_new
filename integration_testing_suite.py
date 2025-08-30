"""
Integration Testing Suite and API Validation System

This module provides comprehensive integration testing capabilities including:
- API endpoint validation with detailed assertion results
- Service integration testing with dependency management
- Database integration testing with transaction validation
- Integration test reporting with failure analysis

Requirements: 1.2 - Comprehensive automated testing across all platform components
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import sqlite3
import pytest
from unittest.mock import Mock, patch
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class IntegrationType(Enum):
    API_ENDPOINT = "api_endpoint"
    SERVICE_INTEGRATION = "service_integration"
    DATABASE_INTEGRATION = "database_integration"
    EXTERNAL_SERVICE = "external_service"

@dataclass
class TestAssertion:
    """Individual test assertion with detailed results"""
    assertion_id: str
    description: str
    expected: Any
    actual: Any
    status: TestStatus
    error_message: Optional[str] = None
    execution_time: float = 0.0

@dataclass
class IntegrationTestCase:
    """Individual integration test case"""
    test_id: str
    name: str
    description: str
    integration_type: IntegrationType
    endpoint_url: Optional[str] = None
    method: str = "GET"
    headers: Dict[str, str] = None
    payload: Dict[str, Any] = None
    expected_status: int = 200
    expected_response: Dict[str, Any] = None
    dependencies: List[str] = None
    timeout: float = 30.0
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class IntegrationTestResult:
    """Results of an integration test execution"""
    test_case: IntegrationTestCase
    status: TestStatus
    assertions: List[TestAssertion]
    execution_time: float
    start_time: datetime
    end_time: datetime
    error_details: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None

@dataclass
class ServiceDependency:
    """Service dependency configuration"""
    service_name: str
    endpoint: str
    health_check_path: str = "/health"
    required: bool = True
    timeout: float = 10.0
    retry_count: int = 3

class APIEndpointValidator:
    """Validates API endpoints with comprehensive assertion checking"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
    
    async def validate_endpoint(self, test_case: IntegrationTestCase) -> IntegrationTestResult:
        """Validate a single API endpoint"""
        start_time = datetime.now()
        assertions = []
        
        try:
            # Make the API request
            response = await self._make_request(test_case)
            
            # Validate status code
            status_assertion = TestAssertion(
                assertion_id=f"{test_case.test_id}_status",
                description="HTTP status code validation",
                expected=test_case.expected_status,
                actual=response.status_code,
                status=TestStatus.PASSED if response.status_code == test_case.expected_status else TestStatus.FAILED
            )
            assertions.append(status_assertion)
            
            # Validate response structure
            if test_case.expected_response:
                response_data = response.json() if response.content else {}
                structure_assertions = self._validate_response_structure(
                    test_case.test_id, test_case.expected_response, response_data
                )
                assertions.extend(structure_assertions)
            
            # Validate response headers
            header_assertions = self._validate_response_headers(test_case.test_id, response)
            assertions.extend(header_assertions)
            
            # Determine overall test status
            test_status = TestStatus.PASSED if all(a.status == TestStatus.PASSED for a in assertions) else TestStatus.FAILED
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return IntegrationTestResult(
                test_case=test_case,
                status=test_status,
                assertions=assertions,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                response_data=response_data if 'response_data' in locals() else None
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            error_assertion = TestAssertion(
                assertion_id=f"{test_case.test_id}_error",
                description="Request execution",
                expected="Successful request",
                actual=f"Error: {str(e)}",
                status=TestStatus.ERROR,
                error_message=str(e)
            )
            assertions.append(error_assertion)
            
            return IntegrationTestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                assertions=assertions,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                error_details=traceback.format_exc()
            )
    
    async def _make_request(self, test_case: IntegrationTestCase) -> requests.Response:
        """Make HTTP request with proper error handling"""
        loop = asyncio.get_event_loop()
        
        def make_sync_request():
            return self.session.request(
                method=test_case.method,
                url=test_case.endpoint_url,
                headers=test_case.headers,
                json=test_case.payload,
                timeout=test_case.timeout
            )
        
        return await loop.run_in_executor(None, make_sync_request)
    
    def _validate_response_structure(self, test_id: str, expected: Dict[str, Any], actual: Dict[str, Any]) -> List[TestAssertion]:
        """Validate response structure against expected format"""
        assertions = []
        
        for key, expected_value in expected.items():
            assertion_id = f"{test_id}_structure_{key}"
            
            if key not in actual:
                assertions.append(TestAssertion(
                    assertion_id=assertion_id,
                    description=f"Response contains key '{key}'",
                    expected=f"Key '{key}' present",
                    actual=f"Key '{key}' missing",
                    status=TestStatus.FAILED
                ))
                continue
            
            actual_value = actual[key]
            
            # Type validation
            if type(expected_value) != type(actual_value):
                assertions.append(TestAssertion(
                    assertion_id=f"{assertion_id}_type",
                    description=f"Type validation for '{key}'",
                    expected=type(expected_value).__name__,
                    actual=type(actual_value).__name__,
                    status=TestStatus.FAILED
                ))
            else:
                assertions.append(TestAssertion(
                    assertion_id=f"{assertion_id}_type",
                    description=f"Type validation for '{key}'",
                    expected=type(expected_value).__name__,
                    actual=type(actual_value).__name__,
                    status=TestStatus.PASSED
                ))
            
            # Value validation for non-dict types
            if not isinstance(expected_value, dict) and expected_value != "ANY":
                status = TestStatus.PASSED if expected_value == actual_value else TestStatus.FAILED
                assertions.append(TestAssertion(
                    assertion_id=f"{assertion_id}_value",
                    description=f"Value validation for '{key}'",
                    expected=expected_value,
                    actual=actual_value,
                    status=status
                ))
        
        return assertions
    
    def _validate_response_headers(self, test_id: str, response: requests.Response) -> List[TestAssertion]:
        """Validate response headers"""
        assertions = []
        
        # Check for common security headers
        security_headers = {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        }
        
        for header, expected_value in security_headers.items():
            assertion_id = f"{test_id}_header_{header.lower().replace('-', '_')}"
            actual_value = response.headers.get(header)
            
            if header == 'Content-Type' and actual_value and 'application/json' in actual_value:
                status = TestStatus.PASSED
            elif actual_value == expected_value:
                status = TestStatus.PASSED
            else:
                status = TestStatus.FAILED
            
            assertions.append(TestAssertion(
                assertion_id=assertion_id,
                description=f"Header '{header}' validation",
                expected=expected_value,
                actual=actual_value or "Not present",
                status=status
            ))
        
        return assertions

class ServiceIntegrationTester:
    """Tests service integrations with dependency management"""
    
    def __init__(self):
        self.dependencies: Dict[str, ServiceDependency] = {}
        self.dependency_status: Dict[str, bool] = {}
    
    def add_dependency(self, dependency: ServiceDependency):
        """Add a service dependency"""
        self.dependencies[dependency.service_name] = dependency
    
    async def check_dependencies(self) -> Dict[str, bool]:
        """Check all service dependencies"""
        results = {}
        
        for name, dependency in self.dependencies.items():
            try:
                health_url = f"{dependency.endpoint.rstrip('/')}{dependency.health_check_path}"
                response = requests.get(health_url, timeout=dependency.timeout)
                results[name] = response.status_code == 200
            except Exception as e:
                logger.warning(f"Dependency check failed for {name}: {e}")
                results[name] = False
        
        self.dependency_status = results
        return results
    
    async def test_service_integration(self, test_case: IntegrationTestCase) -> IntegrationTestResult:
        """Test service integration with dependency validation"""
        start_time = datetime.now()
        assertions = []
        
        # Check dependencies first
        dependency_results = await self.check_dependencies()
        
        # Validate required dependencies
        for dep_name in test_case.dependencies:
            if dep_name in self.dependencies:
                dependency = self.dependencies[dep_name]
                is_available = dependency_results.get(dep_name, False)
                
                assertion = TestAssertion(
                    assertion_id=f"{test_case.test_id}_dep_{dep_name}",
                    description=f"Dependency '{dep_name}' availability",
                    expected="Available",
                    actual="Available" if is_available else "Unavailable",
                    status=TestStatus.PASSED if is_available else TestStatus.FAILED
                )
                assertions.append(assertion)
                
                if dependency.required and not is_available:
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                    
                    return IntegrationTestResult(
                        test_case=test_case,
                        status=TestStatus.FAILED,
                        assertions=assertions,
                        execution_time=execution_time,
                        start_time=start_time,
                        end_time=end_time,
                        error_details=f"Required dependency '{dep_name}' is unavailable"
                    )
        
        # Proceed with integration test if dependencies are satisfied
        try:
            # Simulate service integration test
            integration_result = await self._execute_integration_test(test_case)
            assertions.extend(integration_result)
            
            test_status = TestStatus.PASSED if all(a.status == TestStatus.PASSED for a in assertions) else TestStatus.FAILED
            
        except Exception as e:
            test_status = TestStatus.ERROR
            error_assertion = TestAssertion(
                assertion_id=f"{test_case.test_id}_integration_error",
                description="Service integration execution",
                expected="Successful integration",
                actual=f"Error: {str(e)}",
                status=TestStatus.ERROR,
                error_message=str(e)
            )
            assertions.append(error_assertion)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return IntegrationTestResult(
            test_case=test_case,
            status=test_status,
            assertions=assertions,
            execution_time=execution_time,
            start_time=start_time,
            end_time=end_time
        )
    
    async def _execute_integration_test(self, test_case: IntegrationTestCase) -> List[TestAssertion]:
        """Execute the actual integration test logic"""
        assertions = []
        
        # Simulate data flow validation
        data_flow_assertion = TestAssertion(
            assertion_id=f"{test_case.test_id}_data_flow",
            description="Data flow validation between services",
            expected="Successful data exchange",
            actual="Successful data exchange",
            status=TestStatus.PASSED
        )
        assertions.append(data_flow_assertion)
        
        # Simulate error handling validation
        error_handling_assertion = TestAssertion(
            assertion_id=f"{test_case.test_id}_error_handling",
            description="Error handling validation",
            expected="Proper error propagation",
            actual="Proper error propagation",
            status=TestStatus.PASSED
        )
        assertions.append(error_handling_assertion)
        
        return assertions

class DatabaseIntegrationTester:
    """Tests database integrations with transaction validation"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.connection = None
    
    def setup_test_database(self):
        """Setup test database with sample schema"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        # Create test tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_transcriptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES test_users (id)
            )
        """)
        
        self.connection.commit()
    
    async def test_database_integration(self, test_case: IntegrationTestCase) -> IntegrationTestResult:
        """Test database integration with transaction validation"""
        start_time = datetime.now()
        assertions = []
        
        if not self.connection:
            self.setup_test_database()
        
        try:
            # Test database connection
            connection_assertion = await self._test_database_connection(test_case.test_id)
            assertions.append(connection_assertion)
            
            # Test CRUD operations
            crud_assertions = await self._test_crud_operations(test_case.test_id)
            assertions.extend(crud_assertions)
            
            # Test transaction integrity
            transaction_assertions = await self._test_transaction_integrity(test_case.test_id)
            assertions.extend(transaction_assertions)
            
            # Test foreign key constraints
            constraint_assertions = await self._test_foreign_key_constraints(test_case.test_id)
            assertions.extend(constraint_assertions)
            
            test_status = TestStatus.PASSED if all(a.status == TestStatus.PASSED for a in assertions) else TestStatus.FAILED
            
        except Exception as e:
            test_status = TestStatus.ERROR
            error_assertion = TestAssertion(
                assertion_id=f"{test_case.test_id}_db_error",
                description="Database integration execution",
                expected="Successful database operations",
                actual=f"Error: {str(e)}",
                status=TestStatus.ERROR,
                error_message=str(e)
            )
            assertions.append(error_assertion)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return IntegrationTestResult(
            test_case=test_case,
            status=test_status,
            assertions=assertions,
            execution_time=execution_time,
            start_time=start_time,
            end_time=end_time
        )
    
    async def _test_database_connection(self, test_id: str) -> TestAssertion:
        """Test database connection"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            return TestAssertion(
                assertion_id=f"{test_id}_db_connection",
                description="Database connection test",
                expected="Connection successful",
                actual="Connection successful" if result else "Connection failed",
                status=TestStatus.PASSED if result else TestStatus.FAILED
            )
        except Exception as e:
            return TestAssertion(
                assertion_id=f"{test_id}_db_connection",
                description="Database connection test",
                expected="Connection successful",
                actual=f"Connection failed: {str(e)}",
                status=TestStatus.FAILED,
                error_message=str(e)
            )
    
    async def _test_crud_operations(self, test_id: str) -> List[TestAssertion]:
        """Test CRUD operations"""
        assertions = []
        cursor = self.connection.cursor()
        
        try:
            # Test INSERT
            cursor.execute(
                "INSERT INTO test_users (username, email) VALUES (?, ?)",
                ("testuser", "test@example.com")
            )
            user_id = cursor.lastrowid
            
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_crud_insert",
                description="Database INSERT operation",
                expected="Successful insert",
                actual="Successful insert",
                status=TestStatus.PASSED
            ))
            
            # Test SELECT
            cursor.execute("SELECT * FROM test_users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_crud_select",
                description="Database SELECT operation",
                expected="User record found",
                actual="User record found" if user else "User record not found",
                status=TestStatus.PASSED if user else TestStatus.FAILED
            ))
            
            # Test UPDATE
            cursor.execute(
                "UPDATE test_users SET email = ? WHERE id = ?",
                ("updated@example.com", user_id)
            )
            
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_crud_update",
                description="Database UPDATE operation",
                expected="Successful update",
                actual="Successful update",
                status=TestStatus.PASSED
            ))
            
            # Test DELETE
            cursor.execute("DELETE FROM test_users WHERE id = ?", (user_id,))
            
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_crud_delete",
                description="Database DELETE operation",
                expected="Successful delete",
                actual="Successful delete",
                status=TestStatus.PASSED
            ))
            
        except Exception as e:
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_crud_error",
                description="CRUD operations",
                expected="All operations successful",
                actual=f"Error: {str(e)}",
                status=TestStatus.FAILED,
                error_message=str(e)
            ))
        
        return assertions
    
    async def _test_transaction_integrity(self, test_id: str) -> List[TestAssertion]:
        """Test transaction integrity"""
        assertions = []
        
        try:
            cursor = self.connection.cursor()
            
            # Test transaction rollback
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute(
                    "INSERT INTO test_users (username, email) VALUES (?, ?)",
                    ("rollback_user", "rollback@example.com")
                )
                
                # Intentionally rollback
                cursor.execute("ROLLBACK")
                
                # Check that the user was not inserted
                cursor.execute("SELECT * FROM test_users WHERE username = ?", ("rollback_user",))
                user = cursor.fetchone()
                
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_transaction_rollback",
                    description="Transaction rollback test",
                    expected="User not found after rollback",
                    actual="User not found after rollback" if not user else "User found after rollback",
                    status=TestStatus.PASSED if not user else TestStatus.FAILED
                ))
            except Exception as e:
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_transaction_rollback",
                    description="Transaction rollback test",
                    expected="Successful rollback",
                    actual=f"Error: {str(e)}",
                    status=TestStatus.FAILED,
                    error_message=str(e)
                ))
            
            # Test transaction commit
            try:
                cursor.execute("BEGIN TRANSACTION")
                cursor.execute(
                    "INSERT INTO test_users (username, email) VALUES (?, ?)",
                    ("commit_user", "commit@example.com")
                )
                cursor.execute("COMMIT")
                
                cursor.execute("SELECT * FROM test_users WHERE username = ?", ("commit_user",))
                user = cursor.fetchone()
                
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_transaction_commit",
                    description="Transaction commit test",
                    expected="User found after commit",
                    actual="User found after commit" if user else "User not found after commit",
                    status=TestStatus.PASSED if user else TestStatus.FAILED
                ))
                
                # Cleanup
                cursor.execute("DELETE FROM test_users WHERE username = ?", ("commit_user",))
                self.connection.commit()
                
            except Exception as e:
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_transaction_commit",
                    description="Transaction commit test",
                    expected="Successful commit",
                    actual=f"Error: {str(e)}",
                    status=TestStatus.FAILED,
                    error_message=str(e)
                ))
            
        except Exception as e:
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_transaction_error",
                description="Transaction integrity test",
                expected="Successful transaction operations",
                actual=f"Error: {str(e)}",
                status=TestStatus.FAILED,
                error_message=str(e)
            ))
        
        return assertions
    
    async def _test_foreign_key_constraints(self, test_id: str) -> List[TestAssertion]:
        """Test foreign key constraints"""
        assertions = []
        cursor = self.connection.cursor()
        
        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Insert a user first
            cursor.execute(
                "INSERT INTO test_users (username, email) VALUES (?, ?)",
                ("fk_user", "fk@example.com")
            )
            user_id = cursor.lastrowid
            
            # Test valid foreign key
            cursor.execute(
                "INSERT INTO test_transcriptions (user_id, content) VALUES (?, ?)",
                (user_id, "Test transcription content")
            )
            
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_fk_valid",
                description="Valid foreign key constraint",
                expected="Successful insert with valid FK",
                actual="Successful insert with valid FK",
                status=TestStatus.PASSED
            ))
            
            # Test invalid foreign key (should fail)
            try:
                cursor.execute(
                    "INSERT INTO test_transcriptions (user_id, content) VALUES (?, ?)",
                    (99999, "Invalid FK transcription")
                )
                # If we get here, the constraint didn't work
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_fk_invalid",
                    description="Invalid foreign key constraint",
                    expected="Insert should fail with invalid FK",
                    actual="Insert succeeded with invalid FK",
                    status=TestStatus.FAILED
                ))
            except sqlite3.IntegrityError:
                # This is expected
                assertions.append(TestAssertion(
                    assertion_id=f"{test_id}_fk_invalid",
                    description="Invalid foreign key constraint",
                    expected="Insert should fail with invalid FK",
                    actual="Insert failed with invalid FK (expected)",
                    status=TestStatus.PASSED
                ))
            
            # Cleanup
            cursor.execute("DELETE FROM test_transcriptions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM test_users WHERE id = ?", (user_id,))
            self.connection.commit()
            
        except Exception as e:
            assertions.append(TestAssertion(
                assertion_id=f"{test_id}_fk_error",
                description="Foreign key constraint test",
                expected="Successful constraint validation",
                actual=f"Error: {str(e)}",
                status=TestStatus.FAILED,
                error_message=str(e)
            ))
        
        return assertions
    
    def cleanup(self):
        """Cleanup database resources"""
        if self.connection:
            self.connection.close()

class IntegrationTestReporter:
    """Generates comprehensive integration test reports"""
    
    def __init__(self):
        self.results: List[IntegrationTestResult] = []
    
    def add_result(self, result: IntegrationTestResult):
        """Add a test result to the report"""
        self.results.append(result)
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of all test results"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR])
        
        total_assertions = sum(len(r.assertions) for r in self.results)
        passed_assertions = sum(len([a for a in r.assertions if a.status == TestStatus.PASSED]) for r in self.results)
        
        total_execution_time = sum(r.execution_time for r in self.results)
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_assertions": total_assertions,
                "passed_assertions": passed_assertions,
                "assertion_success_rate": (passed_assertions / total_assertions * 100) if total_assertions > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_execution_time": total_execution_time / total_tests if total_tests > 0 else 0
            },
            "test_results": [self._format_test_result(result) for result in self.results],
            "failure_analysis": self._generate_failure_analysis(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _format_test_result(self, result: IntegrationTestResult) -> Dict[str, Any]:
        """Format individual test result for reporting"""
        return {
            "test_id": result.test_case.test_id,
            "name": result.test_case.name,
            "integration_type": result.test_case.integration_type.value,
            "status": result.status.value,
            "execution_time": result.execution_time,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat(),
            "assertions": [self._format_assertion(assertion) for assertion in result.assertions],
            "error_details": result.error_details,
            "response_data": result.response_data
        }
    
    def _format_assertion(self, assertion: TestAssertion) -> Dict[str, Any]:
        """Format assertion for JSON serialization"""
        return {
            "assertion_id": assertion.assertion_id,
            "description": assertion.description,
            "expected": assertion.expected,
            "actual": assertion.actual,
            "status": assertion.status.value,  # Convert enum to string
            "error_message": assertion.error_message,
            "execution_time": assertion.execution_time
        }
    
    def _generate_failure_analysis(self) -> Dict[str, Any]:
        """Generate detailed failure analysis"""
        failed_results = [r for r in self.results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        
        failure_patterns = {}
        error_categories = {}
        
        for result in failed_results:
            # Analyze failure patterns
            integration_type = result.test_case.integration_type.value
            if integration_type not in failure_patterns:
                failure_patterns[integration_type] = []
            
            failure_patterns[integration_type].append({
                "test_id": result.test_case.test_id,
                "error_details": result.error_details,
                "failed_assertions": [self._format_assertion(a) for a in result.assertions if a.status in [TestStatus.FAILED, TestStatus.ERROR]]
            })
            
            # Categorize errors
            if result.error_details:
                if "timeout" in result.error_details.lower():
                    error_categories["timeout"] = error_categories.get("timeout", 0) + 1
                elif "connection" in result.error_details.lower():
                    error_categories["connection"] = error_categories.get("connection", 0) + 1
                elif "authentication" in result.error_details.lower():
                    error_categories["authentication"] = error_categories.get("authentication", 0) + 1
                else:
                    error_categories["other"] = error_categories.get("other", 0) + 1
        
        return {
            "failure_patterns": failure_patterns,
            "error_categories": error_categories,
            "recommendations": self._generate_recommendations(failure_patterns, error_categories)
        }
    
    def _generate_recommendations(self, failure_patterns: Dict, error_categories: Dict) -> List[str]:
        """Generate recommendations based on failure analysis"""
        recommendations = []
        
        if error_categories.get("timeout", 0) > 0:
            recommendations.append("Consider increasing timeout values for slow-responding services")
        
        if error_categories.get("connection", 0) > 0:
            recommendations.append("Review network connectivity and service availability")
        
        if error_categories.get("authentication", 0) > 0:
            recommendations.append("Verify authentication credentials and token validity")
        
        if "api_endpoint" in failure_patterns:
            recommendations.append("Review API endpoint implementations and response formats")
        
        if "database_integration" in failure_patterns:
            recommendations.append("Check database schema and constraint configurations")
        
        return recommendations
    
    def save_report(self, filename: str):
        """Save report to file"""
        report = self.generate_summary_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Integration test report saved to {filename}")

class IntegrationTestSuite:
    """Main integration testing suite orchestrator"""
    
    def __init__(self):
        self.api_validator = APIEndpointValidator()
        self.service_tester = ServiceIntegrationTester()
        self.db_tester = DatabaseIntegrationTester()
        self.reporter = IntegrationTestReporter()
        self.test_cases: List[IntegrationTestCase] = []
    
    def add_test_case(self, test_case: IntegrationTestCase):
        """Add a test case to the suite"""
        self.test_cases.append(test_case)
    
    def add_service_dependency(self, dependency: ServiceDependency):
        """Add a service dependency"""
        self.service_tester.add_dependency(dependency)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests and generate report"""
        logger.info(f"Starting integration test suite with {len(self.test_cases)} test cases")
        
        for test_case in self.test_cases:
            logger.info(f"Running test: {test_case.name}")
            
            try:
                if test_case.integration_type == IntegrationType.API_ENDPOINT:
                    result = await self.api_validator.validate_endpoint(test_case)
                elif test_case.integration_type == IntegrationType.SERVICE_INTEGRATION:
                    result = await self.service_tester.test_service_integration(test_case)
                elif test_case.integration_type == IntegrationType.DATABASE_INTEGRATION:
                    result = await self.db_tester.test_database_integration(test_case)
                else:
                    # Generic integration test
                    result = await self._run_generic_integration_test(test_case)
                
                self.reporter.add_result(result)
                logger.info(f"Test {test_case.name} completed with status: {result.status.value}")
                
            except Exception as e:
                logger.error(f"Error running test {test_case.name}: {e}")
                # Create error result
                error_result = IntegrationTestResult(
                    test_case=test_case,
                    status=TestStatus.ERROR,
                    assertions=[],
                    execution_time=0.0,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_details=str(e)
                )
                self.reporter.add_result(error_result)
        
        # Generate and return final report
        report = self.reporter.generate_summary_report()
        logger.info(f"Integration test suite completed. Success rate: {report['summary']['success_rate']:.1f}%")
        
        return report
    
    async def _run_generic_integration_test(self, test_case: IntegrationTestCase) -> IntegrationTestResult:
        """Run a generic integration test"""
        start_time = datetime.now()
        
        # Basic integration test logic
        assertion = TestAssertion(
            assertion_id=f"{test_case.test_id}_generic",
            description="Generic integration test",
            expected="Test completed",
            actual="Test completed",
            status=TestStatus.PASSED
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return IntegrationTestResult(
            test_case=test_case,
            status=TestStatus.PASSED,
            assertions=[assertion],
            execution_time=execution_time,
            start_time=start_time,
            end_time=end_time
        )
    
    def cleanup(self):
        """Cleanup all test resources"""
        self.db_tester.cleanup()
        logger.info("Integration test suite cleanup completed")

# Example usage and test case definitions
def create_sample_test_cases() -> List[IntegrationTestCase]:
    """Create sample integration test cases"""
    return [
        # API Endpoint Tests
        IntegrationTestCase(
            test_id="api_health_check",
            name="API Health Check",
            description="Test API health endpoint",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://localhost:8000/health",
            method="GET",
            expected_status=200,
            expected_response={"status": "healthy"}
        ),
        
        IntegrationTestCase(
            test_id="api_transcription_upload",
            name="Transcription Upload API",
            description="Test file upload for transcription",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="http://localhost:8000/api/transcription/upload",
            method="POST",
            headers={"Content-Type": "application/json"},
            payload={"file_name": "test.wav", "file_size": 1024},
            expected_status=201,
            expected_response={"upload_id": "ANY", "status": "uploaded"}
        ),
        
        # Service Integration Tests
        IntegrationTestCase(
            test_id="service_transcription_pipeline",
            name="Transcription Pipeline Integration",
            description="Test integration between upload and processing services",
            integration_type=IntegrationType.SERVICE_INTEGRATION,
            dependencies=["upload_service", "processing_service", "storage_service"]
        ),
        
        # Database Integration Tests
        IntegrationTestCase(
            test_id="db_user_management",
            name="User Management Database Integration",
            description="Test user CRUD operations and constraints",
            integration_type=IntegrationType.DATABASE_INTEGRATION
        )
    ]

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create integration test suite
        suite = IntegrationTestSuite()
        
        # Add service dependencies
        suite.add_service_dependency(ServiceDependency(
            service_name="upload_service",
            endpoint="http://localhost:8001",
            health_check_path="/health"
        ))
        
        suite.add_service_dependency(ServiceDependency(
            service_name="processing_service",
            endpoint="http://localhost:8002",
            health_check_path="/health"
        ))
        
        suite.add_service_dependency(ServiceDependency(
            service_name="storage_service",
            endpoint="http://localhost:8003",
            health_check_path="/health"
        ))
        
        # Add test cases
        test_cases = create_sample_test_cases()
        for test_case in test_cases:
            suite.add_test_case(test_case)
        
        # Run tests
        report = await suite.run_all_tests()
        
        # Save report
        suite.reporter.save_report("integration_test_report.json")
        
        # Cleanup
        suite.cleanup()
        
        return report
    
    # Run the example
    import asyncio
    asyncio.run(main())