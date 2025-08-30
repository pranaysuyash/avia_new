"""
Integration Testing Suite Demo

Demonstrates the comprehensive integration testing capabilities including:
- API endpoint validation with detailed assertions
- Service integration testing with dependency management
- Database integration testing with transaction validation
- Integration test reporting with failure analysis
"""

import asyncio
import json
import logging
from datetime import datetime
import time

from integration_testing_suite import (
    IntegrationTestSuite, IntegrationTestCase, ServiceDependency,
    IntegrationType, TestStatus, create_sample_test_cases
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_api_endpoint_testing():
    """Demonstrate API endpoint testing capabilities"""
    print("\n" + "="*60)
    print("🔌 API ENDPOINT TESTING DEMO")
    print("="*60)
    
    # Create API validator
    from integration_testing_suite import APIEndpointValidator
    validator = APIEndpointValidator()
    
    # Create sample API test cases
    api_test_cases = [
        IntegrationTestCase(
            test_id="api_health_demo",
            name="API Health Check Demo",
            description="Test a mock health endpoint",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="https://httpbin.org/status/200",  # Mock endpoint
            method="GET",
            expected_status=200,
            timeout=10.0
        ),
        
        IntegrationTestCase(
            test_id="api_json_demo",
            name="JSON Response Demo",
            description="Test JSON response validation",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="https://httpbin.org/json",  # Returns JSON
            method="GET",
            expected_status=200,
            expected_response={
                "slideshow": "ANY"  # We expect a slideshow key but don't care about exact value
            },
            timeout=10.0
        ),
        
        IntegrationTestCase(
            test_id="api_post_demo",
            name="POST Request Demo",
            description="Test POST request with payload",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="https://httpbin.org/post",
            method="POST",
            headers={"Content-Type": "application/json"},
            payload={"test_key": "test_value", "timestamp": datetime.now().isoformat()},
            expected_status=200,
            timeout=10.0
        )
    ]
    
    print(f"Running {len(api_test_cases)} API endpoint tests...\n")
    
    for test_case in api_test_cases:
        print(f"🧪 Testing: {test_case.name}")
        print(f"   Endpoint: {test_case.method} {test_case.endpoint_url}")
        
        try:
            result = await validator.validate_endpoint(test_case)
            
            # Display results
            status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
            print(f"   Result: {status_icon} {result.status.value.upper()}")
            print(f"   Execution Time: {result.execution_time:.2f}s")
            print(f"   Assertions: {len([a for a in result.assertions if a.status == TestStatus.PASSED])}/{len(result.assertions)} passed")
            
            # Show failed assertions
            failed_assertions = [a for a in result.assertions if a.status == TestStatus.FAILED]
            if failed_assertions:
                print("   Failed Assertions:")
                for assertion in failed_assertions:
                    print(f"     - {assertion.description}: Expected '{assertion.expected}', Got '{assertion.actual}'")
            
            if result.error_details:
                print(f"   Error: {result.error_details}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
        
        print()

async def demo_service_integration_testing():
    """Demonstrate service integration testing"""
    print("\n" + "="*60)
    print("🔗 SERVICE INTEGRATION TESTING DEMO")
    print("="*60)
    
    # Create service integration tester
    from integration_testing_suite import ServiceIntegrationTester
    tester = ServiceIntegrationTester()
    
    # Add mock service dependencies
    dependencies = [
        ServiceDependency(
            service_name="auth_service",
            endpoint="https://httpbin.org",  # Mock service
            health_check_path="/status/200",
            required=True,
            timeout=10.0
        ),
        ServiceDependency(
            service_name="storage_service",
            endpoint="https://httpbin.org",
            health_check_path="/status/200",
            required=True,
            timeout=10.0
        ),
        ServiceDependency(
            service_name="notification_service",
            endpoint="https://httpbin.org",
            health_check_path="/status/503",  # This will fail
            required=False,
            timeout=5.0
        )
    ]
    
    print("Adding service dependencies:")
    for dep in dependencies:
        tester.add_dependency(dep)
        required_text = "Required" if dep.required else "Optional"
        print(f"  📡 {dep.service_name}: {dep.endpoint} ({required_text})")
    
    print("\n🔍 Checking service dependencies...")
    dependency_results = await tester.check_dependencies()
    
    for service, status in dependency_results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {service}: {'Available' if status else 'Unavailable'}")
    
    # Create service integration test
    integration_test = IntegrationTestCase(
        test_id="service_integration_demo",
        name="Multi-Service Integration Demo",
        description="Test integration between multiple services",
        integration_type=IntegrationType.SERVICE_INTEGRATION,
        dependencies=["auth_service", "storage_service", "notification_service"]
    )
    
    print(f"\n🧪 Running service integration test: {integration_test.name}")
    result = await tester.test_service_integration(integration_test)
    
    status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
    print(f"Result: {status_icon} {result.status.value.upper()}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Assertions: {len([a for a in result.assertions if a.status == TestStatus.PASSED])}/{len(result.assertions)} passed")
    
    # Show assertion details
    print("\nAssertion Details:")
    for assertion in result.assertions:
        status_icon = "✅" if assertion.status == TestStatus.PASSED else "❌"
        print(f"  {status_icon} {assertion.description}")
        if assertion.status == TestStatus.FAILED:
            print(f"      Expected: {assertion.expected}")
            print(f"      Actual: {assertion.actual}")

async def demo_database_integration_testing():
    """Demonstrate database integration testing"""
    print("\n" + "="*60)
    print("🗄️ DATABASE INTEGRATION TESTING DEMO")
    print("="*60)
    
    # Create database integration tester
    from integration_testing_suite import DatabaseIntegrationTester
    tester = DatabaseIntegrationTester(":memory:")  # Use in-memory database
    
    print("Setting up test database...")
    tester.setup_test_database()
    print("✅ Test database initialized with sample schema")
    
    # Create database integration test
    db_test = IntegrationTestCase(
        test_id="database_integration_demo",
        name="Database CRUD Operations Demo",
        description="Test database operations and transaction integrity",
        integration_type=IntegrationType.DATABASE_INTEGRATION
    )
    
    print(f"\n🧪 Running database integration test: {db_test.name}")
    result = await tester.test_database_integration(db_test)
    
    status_icon = "✅" if result.status == TestStatus.PASSED else "❌"
    print(f"Result: {status_icon} {result.status.value.upper()}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Assertions: {len([a for a in result.assertions if a.status == TestStatus.PASSED])}/{len(result.assertions)} passed")
    
    # Show assertion details by category
    print("\nAssertion Details:")
    
    categories = {
        "connection": "Database Connection",
        "crud": "CRUD Operations", 
        "transaction": "Transaction Integrity",
        "fk": "Foreign Key Constraints"
    }
    
    for category, title in categories.items():
        category_assertions = [a for a in result.assertions if category in a.assertion_id]
        if category_assertions:
            print(f"\n  📋 {title}:")
            for assertion in category_assertions:
                status_icon = "✅" if assertion.status == TestStatus.PASSED else "❌"
                print(f"    {status_icon} {assertion.description}")
                if assertion.status == TestStatus.FAILED:
                    print(f"        Expected: {assertion.expected}")
                    print(f"        Actual: {assertion.actual}")
    
    # Cleanup
    tester.cleanup()
    print("\n✅ Database cleanup completed")

async def demo_comprehensive_test_suite():
    """Demonstrate comprehensive integration test suite"""
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE INTEGRATION TEST SUITE DEMO")
    print("="*60)
    
    # Create integration test suite
    suite = IntegrationTestSuite()
    
    # Add service dependencies
    dependencies = [
        ServiceDependency("api_gateway", "https://httpbin.org", "/status/200"),
        ServiceDependency("auth_service", "https://httpbin.org", "/status/200"),
        ServiceDependency("data_service", "https://httpbin.org", "/status/200")
    ]
    
    print("Configuring service dependencies:")
    for dep in dependencies:
        suite.add_service_dependency(dep)
        print(f"  📡 {dep.service_name}: {dep.endpoint}")
    
    # Create comprehensive test cases
    test_cases = [
        # API Tests
        IntegrationTestCase(
            test_id="api_gateway_health",
            name="API Gateway Health Check",
            description="Validate API gateway availability",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="https://httpbin.org/status/200",
            method="GET",
            expected_status=200
        ),
        
        IntegrationTestCase(
            test_id="api_user_creation",
            name="User Creation API",
            description="Test user creation endpoint",
            integration_type=IntegrationType.API_ENDPOINT,
            endpoint_url="https://httpbin.org/post",
            method="POST",
            headers={"Content-Type": "application/json"},
            payload={"username": "testuser", "email": "test@example.com"},
            expected_status=200,
            dependencies=["auth_service"]
        ),
        
        # Service Integration Tests
        IntegrationTestCase(
            test_id="auth_data_integration",
            name="Authentication-Data Service Integration",
            description="Test integration between auth and data services",
            integration_type=IntegrationType.SERVICE_INTEGRATION,
            dependencies=["auth_service", "data_service"]
        ),
        
        # Database Tests
        IntegrationTestCase(
            test_id="database_operations",
            name="Database Operations Test",
            description="Comprehensive database operation validation",
            integration_type=IntegrationType.DATABASE_INTEGRATION
        )
    ]
    
    print(f"\nAdding {len(test_cases)} test cases to suite:")
    for test_case in test_cases:
        suite.add_test_case(test_case)
        print(f"  🧪 {test_case.name} ({test_case.integration_type.value})")
    
    print(f"\n🚀 Running comprehensive integration test suite...")
    start_time = time.time()
    
    # Run all tests
    report = await suite.run_all_tests()
    
    execution_time = time.time() - start_time
    
    # Display results
    print(f"\n📊 TEST SUITE RESULTS")
    print("-" * 40)
    
    summary = report['summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']} ✅")
    print(f"Failed: {summary['failed_tests']} ❌")
    print(f"Errors: {summary['error_tests']} ⚠️")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Total Execution Time: {execution_time:.2f}s")
    print(f"Average Test Time: {summary['average_execution_time']:.2f}s")
    
    # Show individual test results
    print(f"\n📋 INDIVIDUAL TEST RESULTS")
    print("-" * 40)
    
    for test_result in report['test_results']:
        status_map = {
            'passed': '✅',
            'failed': '❌', 
            'error': '⚠️'
        }
        
        status_icon = status_map.get(test_result['status'], '❓')
        print(f"{status_icon} {test_result['name']}")
        print(f"   Status: {test_result['status'].upper()}")
        print(f"   Time: {test_result['execution_time']:.2f}s")
        print(f"   Assertions: {len([a for a in test_result['assertions'] if a['status'] == 'passed'])}/{len(test_result['assertions'])} passed")
        
        # Show failed assertions
        failed_assertions = [a for a in test_result['assertions'] if a['status'] in ['failed', 'error']]
        if failed_assertions:
            print("   Failed Assertions:")
            for assertion in failed_assertions[:3]:  # Show first 3 failures
                print(f"     - {assertion['description']}")
        print()
    
    # Show failure analysis if there are failures
    if summary['failed_tests'] > 0 or summary['error_tests'] > 0:
        failure_analysis = report['failure_analysis']
        
        print(f"\n🔍 FAILURE ANALYSIS")
        print("-" * 40)
        
        if failure_analysis['error_categories']:
            print("Error Categories:")
            for category, count in failure_analysis['error_categories'].items():
                print(f"  - {category.title()}: {count}")
        
        if failure_analysis['recommendations']:
            print("\nRecommendations:")
            for i, recommendation in enumerate(failure_analysis['recommendations'], 1):
                print(f"  {i}. {recommendation}")
    
    # Save report
    report_filename = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    suite.reporter.save_report(report_filename)
    print(f"\n💾 Detailed report saved to: {report_filename}")
    
    # Cleanup
    suite.cleanup()
    print("🧹 Test suite cleanup completed")
    
    return report

async def demo_test_reporting():
    """Demonstrate test reporting capabilities"""
    print("\n" + "="*60)
    print("📊 TEST REPORTING DEMO")
    print("="*60)
    
    # Create sample test results for reporting demo
    from integration_testing_suite import IntegrationTestReporter, IntegrationTestResult, TestAssertion
    
    reporter = IntegrationTestReporter()
    
    # Create mock test results
    sample_results = []
    
    for i in range(5):
        # Create mock test case
        test_case = IntegrationTestCase(
            test_id=f"test_{i}",
            name=f"Sample Test {i+1}",
            description=f"Sample test case {i+1}",
            integration_type=IntegrationType.API_ENDPOINT
        )
        
        # Create mock assertions
        assertions = []
        for j in range(3):
            status = TestStatus.PASSED if (i + j) % 4 != 0 else TestStatus.FAILED
            assertion = TestAssertion(
                assertion_id=f"test_{i}_assertion_{j}",
                description=f"Assertion {j+1}",
                expected="Expected value",
                actual="Expected value" if status == TestStatus.PASSED else "Different value",
                status=status
            )
            assertions.append(assertion)
        
        # Create test result
        result_status = TestStatus.PASSED if all(a.status == TestStatus.PASSED for a in assertions) else TestStatus.FAILED
        
        result = IntegrationTestResult(
            test_case=test_case,
            status=result_status,
            assertions=assertions,
            execution_time=1.5 + (i * 0.3),
            start_time=datetime.now(),
            end_time=datetime.now()
        )
        
        reporter.add_result(result)
        sample_results.append(result)
    
    print(f"Generated {len(sample_results)} sample test results")
    
    # Generate comprehensive report
    print("\n📋 Generating comprehensive report...")
    report = reporter.generate_summary_report()
    
    # Display report summary
    summary = report['summary']
    print(f"\nReport Summary:")
    print(f"  Total Tests: {summary['total_tests']}")
    print(f"  Success Rate: {summary['success_rate']:.1f}%")
    print(f"  Total Assertions: {summary['total_assertions']}")
    print(f"  Assertion Success Rate: {summary['assertion_success_rate']:.1f}%")
    print(f"  Average Execution Time: {summary['average_execution_time']:.2f}s")
    
    # Show failure analysis
    if 'failure_analysis' in report:
        failure_analysis = report['failure_analysis']
        print(f"\nFailure Analysis:")
        
        if failure_analysis['error_categories']:
            print("  Error Categories:")
            for category, count in failure_analysis['error_categories'].items():
                print(f"    - {category}: {count}")
        
        if failure_analysis['recommendations']:
            print("  Recommendations:")
            for rec in failure_analysis['recommendations']:
                print(f"    • {rec}")
    
    # Save report
    report_filename = f"sample_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    reporter.save_report(report_filename)
    print(f"\n💾 Sample report saved to: {report_filename}")
    
    # Display report structure
    print(f"\nReport Structure:")
    print(f"  - Summary metrics and statistics")
    print(f"  - Individual test results with assertions")
    print(f"  - Failure analysis and recommendations")
    print(f"  - Execution timestamps and performance data")

async def main():
    """Run all integration testing demos"""
    print("🧪 INTEGRATION TESTING SUITE COMPREHENSIVE DEMO")
    print("=" * 80)
    print("This demo showcases the complete integration testing capabilities")
    print("including API validation, service integration, and database testing.")
    print("=" * 80)
    
    try:
        # Run individual demos
        await demo_api_endpoint_testing()
        await demo_service_integration_testing()
        await demo_database_integration_testing()
        await demo_test_reporting()
        
        # Run comprehensive suite demo
        await demo_comprehensive_test_suite()
        
        print("\n" + "="*80)
        print("✅ INTEGRATION TESTING SUITE DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("• API endpoint validation with detailed assertions")
        print("• Service integration testing with dependency management")
        print("• Database integration testing with transaction validation")
        print("• Comprehensive test reporting with failure analysis")
        print("• Test suite orchestration and execution monitoring")
        print("\nThe integration testing suite provides enterprise-grade")
        print("testing capabilities for validating complex system integrations.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())