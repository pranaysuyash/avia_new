"""
Integration Testing Suite API Endpoints

FastAPI endpoints for the Integration Testing Suite and API Validation system.
Provides REST API access to testing capabilities, execution monitoring, and results management.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
import uuid
import os

from integration_testing_suite import (
    IntegrationTestSuite, IntegrationTestCase, ServiceDependency,
    IntegrationType, TestStatus, create_sample_test_cases
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/integration-testing", tags=["Integration Testing"])

# Global test suite instance (in production, this would be managed differently)
test_suite_instances: Dict[str, IntegrationTestSuite] = {}
test_execution_status: Dict[str, Dict[str, Any]] = {}

# Pydantic models for API
class TestCaseRequest(BaseModel):
    test_id: str = Field(..., description="Unique test identifier")
    name: str = Field(..., description="Test case name")
    description: str = Field(..., description="Test case description")
    integration_type: str = Field(..., description="Type of integration test")
    endpoint_url: Optional[str] = Field(None, description="API endpoint URL")
    method: str = Field("GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    expected_status: int = Field(200, description="Expected HTTP status code")
    expected_response: Optional[Dict[str, Any]] = Field(None, description="Expected response structure")
    dependencies: List[str] = Field(default_factory=list, description="Service dependencies")
    timeout: float = Field(30.0, description="Request timeout in seconds")

class ServiceDependencyRequest(BaseModel):
    service_name: str = Field(..., description="Service name")
    endpoint: str = Field(..., description="Service endpoint URL")
    health_check_path: str = Field("/health", description="Health check path")
    required: bool = Field(True, description="Whether service is required")
    timeout: float = Field(10.0, description="Health check timeout")

class TestExecutionRequest(BaseModel):
    test_ids: Optional[List[str]] = Field(None, description="Specific test IDs to run (all if None)")
    parallel_execution: bool = Field(True, description="Enable parallel execution")
    stop_on_failure: bool = Field(False, description="Stop execution on first failure")

class TestSuiteResponse(BaseModel):
    suite_id: str
    test_cases: List[Dict[str, Any]]
    service_dependencies: List[Dict[str, Any]]
    created_at: str

class TestExecutionResponse(BaseModel):
    execution_id: str
    status: str
    started_at: str
    progress: Dict[str, Any]

class TestResultsResponse(BaseModel):
    execution_id: str
    summary: Dict[str, Any]
    test_results: List[Dict[str, Any]]
    failure_analysis: Dict[str, Any]
    generated_at: str

@router.post("/suites", response_model=TestSuiteResponse)
async def create_test_suite():
    """Create a new integration test suite"""
    try:
        suite_id = str(uuid.uuid4())
        suite = IntegrationTestSuite()
        test_suite_instances[suite_id] = suite
        
        logger.info(f"Created new test suite: {suite_id}")
        
        return TestSuiteResponse(
            suite_id=suite_id,
            test_cases=[],
            service_dependencies=[],
            created_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error creating test suite: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create test suite: {str(e)}")

@router.get("/suites/{suite_id}", response_model=TestSuiteResponse)
async def get_test_suite(suite_id: str):
    """Get test suite information"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    suite = test_suite_instances[suite_id]
    
    return TestSuiteResponse(
        suite_id=suite_id,
        test_cases=[
            {
                "test_id": tc.test_id,
                "name": tc.name,
                "description": tc.description,
                "integration_type": tc.integration_type.value,
                "endpoint_url": tc.endpoint_url,
                "method": tc.method,
                "dependencies": tc.dependencies
            }
            for tc in suite.test_cases
        ],
        service_dependencies=[
            {
                "service_name": name,
                "endpoint": dep.endpoint,
                "health_check_path": dep.health_check_path,
                "required": dep.required,
                "timeout": dep.timeout
            }
            for name, dep in suite.service_tester.dependencies.items()
        ],
        created_at=datetime.now().isoformat()
    )

@router.post("/suites/{suite_id}/test-cases")
async def add_test_case(suite_id: str, test_case: TestCaseRequest):
    """Add a test case to the suite"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        suite = test_suite_instances[suite_id]
        
        # Convert request to IntegrationTestCase
        integration_test_case = IntegrationTestCase(
            test_id=test_case.test_id,
            name=test_case.name,
            description=test_case.description,
            integration_type=IntegrationType(test_case.integration_type),
            endpoint_url=test_case.endpoint_url,
            method=test_case.method,
            headers=test_case.headers,
            payload=test_case.payload,
            expected_status=test_case.expected_status,
            expected_response=test_case.expected_response,
            dependencies=test_case.dependencies,
            timeout=test_case.timeout
        )
        
        suite.add_test_case(integration_test_case)
        
        logger.info(f"Added test case {test_case.test_id} to suite {suite_id}")
        
        return {"message": f"Test case '{test_case.name}' added successfully", "test_id": test_case.test_id}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid integration type: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding test case: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add test case: {str(e)}")

@router.post("/suites/{suite_id}/dependencies")
async def add_service_dependency(suite_id: str, dependency: ServiceDependencyRequest):
    """Add a service dependency to the suite"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        suite = test_suite_instances[suite_id]
        
        # Convert request to ServiceDependency
        service_dependency = ServiceDependency(
            service_name=dependency.service_name,
            endpoint=dependency.endpoint,
            health_check_path=dependency.health_check_path,
            required=dependency.required,
            timeout=dependency.timeout
        )
        
        suite.add_service_dependency(service_dependency)
        
        logger.info(f"Added service dependency {dependency.service_name} to suite {suite_id}")
        
        return {"message": f"Service dependency '{dependency.service_name}' added successfully"}
    
    except Exception as e:
        logger.error(f"Error adding service dependency: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add service dependency: {str(e)}")

@router.post("/suites/{suite_id}/sample-tests")
async def load_sample_test_cases(suite_id: str):
    """Load sample test cases into the suite"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        suite = test_suite_instances[suite_id]
        sample_cases = create_sample_test_cases()
        
        for test_case in sample_cases:
            suite.add_test_case(test_case)
        
        logger.info(f"Loaded {len(sample_cases)} sample test cases to suite {suite_id}")
        
        return {
            "message": f"Loaded {len(sample_cases)} sample test cases",
            "test_cases": [tc.test_id for tc in sample_cases]
        }
    
    except Exception as e:
        logger.error(f"Error loading sample test cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load sample test cases: {str(e)}")

@router.get("/suites/{suite_id}/dependencies/check")
async def check_service_dependencies(suite_id: str):
    """Check the status of all service dependencies"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        suite = test_suite_instances[suite_id]
        dependency_results = await suite.service_tester.check_dependencies()
        
        return {
            "dependency_status": dependency_results,
            "all_available": all(dependency_results.values()),
            "checked_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check dependencies: {str(e)}")

@router.post("/suites/{suite_id}/execute", response_model=TestExecutionResponse)
async def execute_tests(
    suite_id: str,
    execution_request: TestExecutionRequest,
    background_tasks: BackgroundTasks
):
    """Execute integration tests"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        suite = test_suite_instances[suite_id]
        
        if not suite.test_cases:
            raise HTTPException(status_code=400, detail="No test cases configured in suite")
        
        execution_id = str(uuid.uuid4())
        
        # Initialize execution status
        test_execution_status[execution_id] = {
            "suite_id": suite_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "progress": {
                "total_tests": len(suite.test_cases),
                "completed_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "current_test": None
            },
            "results": None
        }
        
        # Start test execution in background
        background_tasks.add_task(
            run_integration_tests,
            execution_id,
            suite,
            execution_request.test_ids,
            execution_request.parallel_execution,
            execution_request.stop_on_failure
        )
        
        logger.info(f"Started test execution {execution_id} for suite {suite_id}")
        
        return TestExecutionResponse(
            execution_id=execution_id,
            status="running",
            started_at=test_execution_status[execution_id]["started_at"],
            progress=test_execution_status[execution_id]["progress"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting test execution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start test execution: {str(e)}")

async def run_integration_tests(
    execution_id: str,
    suite: IntegrationTestSuite,
    test_ids: Optional[List[str]],
    parallel_execution: bool,
    stop_on_failure: bool
):
    """Background task to run integration tests"""
    try:
        # Filter test cases if specific IDs provided
        if test_ids:
            original_cases = suite.test_cases.copy()
            suite.test_cases = [tc for tc in suite.test_cases if tc.test_id in test_ids]
        
        # Update progress callback
        def update_progress(current_test: str, completed: int, passed: int, failed: int):
            if execution_id in test_execution_status:
                test_execution_status[execution_id]["progress"].update({
                    "completed_tests": completed,
                    "passed_tests": passed,
                    "failed_tests": failed,
                    "current_test": current_test
                })
        
        # Run tests
        report = await suite.run_all_tests()
        
        # Store results
        test_execution_status[execution_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "results": report
        })
        
        # Restore original test cases if filtered
        if test_ids:
            suite.test_cases = original_cases
        
        logger.info(f"Test execution {execution_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Test execution {execution_id} failed: {e}")
        test_execution_status[execution_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })

@router.get("/executions/{execution_id}/status", response_model=TestExecutionResponse)
async def get_execution_status(execution_id: str):
    """Get test execution status"""
    if execution_id not in test_execution_status:
        raise HTTPException(status_code=404, detail="Test execution not found")
    
    execution_info = test_execution_status[execution_id]
    
    return TestExecutionResponse(
        execution_id=execution_id,
        status=execution_info["status"],
        started_at=execution_info["started_at"],
        progress=execution_info["progress"]
    )

@router.get("/executions/{execution_id}/results", response_model=TestResultsResponse)
async def get_execution_results(execution_id: str):
    """Get test execution results"""
    if execution_id not in test_execution_status:
        raise HTTPException(status_code=404, detail="Test execution not found")
    
    execution_info = test_execution_status[execution_id]
    
    if execution_info["status"] == "running":
        raise HTTPException(status_code=400, detail="Test execution still in progress")
    
    if execution_info["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Test execution failed: {execution_info.get('error', 'Unknown error')}")
    
    results = execution_info["results"]
    
    return TestResultsResponse(
        execution_id=execution_id,
        summary=results["summary"],
        test_results=results["test_results"],
        failure_analysis=results["failure_analysis"],
        generated_at=results["generated_at"]
    )

@router.get("/executions/{execution_id}/report")
async def download_execution_report(execution_id: str, format: str = Query("json", regex="^(json|csv)$")):
    """Download test execution report"""
    if execution_id not in test_execution_status:
        raise HTTPException(status_code=404, detail="Test execution not found")
    
    execution_info = test_execution_status[execution_id]
    
    if execution_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test execution not completed")
    
    try:
        results = execution_info["results"]
        
        if format == "json":
            # Generate JSON report
            report_filename = f"integration_test_report_{execution_id}.json"
            report_path = f"/tmp/{report_filename}"
            
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            return FileResponse(
                path=report_path,
                filename=report_filename,
                media_type="application/json"
            )
        
        elif format == "csv":
            # Generate CSV report
            import pandas as pd
            
            # Convert test results to DataFrame
            test_data = []
            for test_result in results["test_results"]:
                test_data.append({
                    "test_id": test_result["test_id"],
                    "name": test_result["name"],
                    "integration_type": test_result["integration_type"],
                    "status": test_result["status"],
                    "execution_time": test_result["execution_time"],
                    "assertions_passed": len([a for a in test_result["assertions"] if a["status"] == "passed"]),
                    "assertions_total": len(test_result["assertions"])
                })
            
            df = pd.DataFrame(test_data)
            
            report_filename = f"integration_test_report_{execution_id}.csv"
            report_path = f"/tmp/{report_filename}"
            
            df.to_csv(report_path, index=False)
            
            return FileResponse(
                path=report_path,
                filename=report_filename,
                media_type="text/csv"
            )
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/executions")
async def list_executions(
    suite_id: Optional[str] = Query(None, description="Filter by suite ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """List test executions"""
    executions = []
    
    for exec_id, exec_info in test_execution_status.items():
        # Apply filters
        if suite_id and exec_info.get("suite_id") != suite_id:
            continue
        
        if status and exec_info.get("status") != status:
            continue
        
        executions.append({
            "execution_id": exec_id,
            "suite_id": exec_info.get("suite_id"),
            "status": exec_info.get("status"),
            "started_at": exec_info.get("started_at"),
            "completed_at": exec_info.get("completed_at"),
            "progress": exec_info.get("progress", {})
        })
    
    # Sort by start time (most recent first)
    executions.sort(key=lambda x: x["started_at"], reverse=True)
    
    return {
        "executions": executions[:limit],
        "total": len(executions)
    }

@router.delete("/suites/{suite_id}")
async def delete_test_suite(suite_id: str):
    """Delete a test suite"""
    if suite_id not in test_suite_instances:
        raise HTTPException(status_code=404, detail="Test suite not found")
    
    try:
        # Cleanup suite resources
        suite = test_suite_instances[suite_id]
        suite.cleanup()
        
        # Remove from instances
        del test_suite_instances[suite_id]
        
        # Remove related executions
        executions_to_remove = [
            exec_id for exec_id, exec_info in test_execution_status.items()
            if exec_info.get("suite_id") == suite_id
        ]
        
        for exec_id in executions_to_remove:
            del test_execution_status[exec_id]
        
        logger.info(f"Deleted test suite {suite_id}")
        
        return {"message": f"Test suite {suite_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting test suite: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete test suite: {str(e)}")

@router.get("/integration-types")
async def get_integration_types():
    """Get available integration test types"""
    return {
        "integration_types": [
            {
                "value": integration_type.value,
                "name": integration_type.value.replace('_', ' ').title(),
                "description": f"{integration_type.value.replace('_', ' ').title()} testing"
            }
            for integration_type in IntegrationType
        ]
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Integration Testing Suite API",
        "timestamp": datetime.now().isoformat(),
        "active_suites": len(test_suite_instances),
        "active_executions": len([e for e in test_execution_status.values() if e.get("status") == "running"])
    }

# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid value: {str(exc)}"}
    )

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )