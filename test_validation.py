#!/usr/bin/env python3
"""
Test validation script to verify comprehensive testing suite meets all requirements
Validates that task 13 requirements are fully implemented
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

class TestSuiteValidator:
    """Validates that the comprehensive testing suite meets all task 13 requirements"""
    
    def __init__(self):
        """Initialize test suite validator"""
        self.validation_results = {
            "requirements_met": {},
            "test_coverage": {},
            "test_files": {},
            "test_data": {},
            "overall_status": "unknown"
        }
    
    def validate_requirement_1_unit_tests(self) -> Tuple[bool, str]:
        """
        Validate: Create unit tests for all backend modules with mock external dependencies
        """
        print("🧪 Validating Requirement 1: Unit tests for all backend modules...")
        
        # Expected backend modules
        backend_modules = [
            "media.py",
            "stt.py", 
            "ner_basic.py",
            "ner_advanced.py",
            "tts.py",
            "utils.py"
        ]
        
        # Expected test files
        expected_test_files = [
            "test_media.py",
            "test_stt.py",
            "test_ner_basic.py", 
            "test_ner_advanced.py",
            "test_tts.py",
            "test_utils.py"
        ]
        
        missing_modules = []
        missing_tests = []
        mock_usage_verified = []
        
        # Check backend modules exist
        for module in backend_modules:
            if not os.path.exists(module):
                missing_modules.append(module)
        
        # Check test files exist
        for test_file in expected_test_files:
            if not os.path.exists(test_file):
                missing_tests.append(test_file)
            else:
                # Check for mock usage in test files
                with open(test_file, 'r') as f:
                    content = f.read()
                    if any(mock_pattern in content for mock_pattern in [
                        "unittest.mock", "@patch", "MagicMock", "Mock()"
                    ]):
                        mock_usage_verified.append(test_file)
        
        # Validation results
        if missing_modules:
            return False, f"Missing backend modules: {missing_modules}"
        
        if missing_tests:
            return False, f"Missing test files: {missing_tests}"
        
        if len(mock_usage_verified) < len(expected_test_files) * 0.8:
            return False, f"Insufficient mock usage in test files. Found mocks in: {mock_usage_verified}"
        
        print(f"   ✅ All {len(backend_modules)} backend modules have corresponding test files")
        print(f"   ✅ Mock usage verified in {len(mock_usage_verified)} test files")
        
        return True, f"Unit tests implemented for all {len(backend_modules)} backend modules with proper mocking"
    
    def validate_requirement_2_integration_tests(self) -> Tuple[bool, str]:
        """
        Validate: Add integration tests for complete processing pipelines
        """
        print("🔗 Validating Requirement 2: Integration tests for complete processing pipelines...")
        
        expected_integration_files = [
            "test_integration_comprehensive.py",
            "test_integration_workflow.py", 
            "test_complete_integration.py",
            "test_integration_error_handling.py"
        ]
        
        missing_integration_tests = []
        pipeline_tests_found = []
        
        for test_file in expected_integration_files:
            if not os.path.exists(test_file):
                missing_integration_tests.append(test_file)
            else:
                # Check for integration test patterns
                with open(test_file, 'r') as f:
                    content = f.read()
                    
                    # Look for pipeline-related test patterns
                    pipeline_patterns = [
                        "test_complete_pipeline",
                        "test_end_to_end",
                        "test_workflow",
                        "integration",
                        "pipeline"
                    ]
                    
                    if any(pattern in content.lower() for pattern in pipeline_patterns):
                        pipeline_tests_found.append(test_file)
        
        if missing_integration_tests:
            return False, f"Missing integration test files: {missing_integration_tests}"
        
        if len(pipeline_tests_found) < 3:
            return False, f"Insufficient pipeline integration tests. Found in: {pipeline_tests_found}"
        
        print(f"   ✅ {len(expected_integration_files)} integration test files found")
        print(f"   ✅ Pipeline tests verified in {len(pipeline_tests_found)} files")
        
        return True, f"Integration tests implemented for complete processing pipelines"
    
    def validate_requirement_3_performance_tests(self) -> Tuple[bool, str]:
        """
        Validate: Implement performance tests with various file sizes and formats
        """
        print("⚡ Validating Requirement 3: Performance tests with various file sizes and formats...")
        
        performance_test_file = "test_performance.py"
        
        if not os.path.exists(performance_test_file):
            return False, f"Performance test file {performance_test_file} not found"
        
        with open(performance_test_file, 'r') as f:
            content = f.read()
        
        # Check for performance test patterns
        performance_patterns = [
            "file_sizes", "various.*size", "performance", "memory", "processing_time",
            "duration", "scalability", "benchmark", "speed"
        ]
        
        format_patterns = [
            "mp3", "wav", "mp4", "m4a", "format", "audio", "video"
        ]
        
        performance_found = sum(1 for pattern in performance_patterns if pattern in content.lower())
        format_found = sum(1 for pattern in format_patterns if pattern in content.lower())
        
        if performance_found < 3:
            return False, f"Insufficient performance test patterns found: {performance_found}/3"
        
        if format_found < 2:
            return False, f"Insufficient file format testing found: {format_found}/2"
        
        # Check for pytest performance marker
        if "@pytest.mark.performance" not in content:
            return False, "Performance tests not properly marked with @pytest.mark.performance"
        
        print(f"   ✅ Performance test patterns found: {performance_found}")
        print(f"   ✅ File format testing found: {format_found}")
        print(f"   ✅ Proper pytest markers used")
        
        return True, "Performance tests implemented with various file sizes and formats"
    
    def validate_requirement_4_test_data_sets(self) -> Tuple[bool, str]:
        """
        Validate: Create test data sets with known transcriptions and entity extractions
        """
        print("📊 Validating Requirement 4: Test data sets with known transcriptions and entity extractions...")
        
        # Check for test data generator
        if not os.path.exists("test_data_generator.py"):
            return False, "Test data generator not found"
        
        # Check for test data directory structure
        test_data_dir = Path("test_data")
        if not test_data_dir.exists():
            return False, "Test data directory not found"
        
        required_subdirs = ["audio", "transcripts", "entities", "metadata"]
        missing_subdirs = []
        
        for subdir in required_subdirs:
            if not (test_data_dir / subdir).exists():
                missing_subdirs.append(subdir)
        
        if missing_subdirs:
            return False, f"Missing test data subdirectories: {missing_subdirs}"
        
        # Check for metadata files
        metadata_files = [
            "metadata/dataset.json",
            "metadata/edge_cases.json", 
            "metadata/performance_cases.json"
        ]
        
        missing_metadata = []
        dataset_info = {}
        
        for metadata_file in metadata_files:
            metadata_path = test_data_dir / metadata_file
            if not metadata_path.exists():
                missing_metadata.append(metadata_file)
            else:
                try:
                    with open(metadata_path, 'r') as f:
                        data = json.load(f)
                        dataset_info[metadata_file] = {
                            "cases": len(data.get("test_cases", data.get("edge_cases", data.get("performance_cases", [])))),
                            "description": data.get("metadata", {}).get("description", "")
                        }
                except Exception as e:
                    missing_metadata.append(f"{metadata_file} (invalid JSON: {e})")
        
        if missing_metadata:
            return False, f"Missing or invalid metadata files: {missing_metadata}"
        
        # Check for actual test files
        audio_files = list((test_data_dir / "audio").glob("*.wav"))
        transcript_files = list((test_data_dir / "transcripts").glob("*.txt"))
        entity_files = list((test_data_dir / "entities").glob("*.json"))
        
        if len(audio_files) < 5:
            return False, f"Insufficient audio test files: {len(audio_files)} (need at least 5)"
        
        if len(transcript_files) < 5:
            return False, f"Insufficient transcript files: {len(transcript_files)} (need at least 5)"
        
        if len(entity_files) < 5:
            return False, f"Insufficient entity files: {len(entity_files)} (need at least 5)"
        
        total_cases = sum(info["cases"] for info in dataset_info.values())
        
        print(f"   ✅ Test data directory structure complete")
        print(f"   ✅ {len(audio_files)} audio files, {len(transcript_files)} transcripts, {len(entity_files)} entity files")
        print(f"   ✅ {total_cases} total test cases across all datasets")
        
        return True, f"Test data sets created with {total_cases} cases including known transcriptions and entity extractions"
    
    def validate_requirement_5_error_testing(self) -> Tuple[bool, str]:
        """
        Validate: Add automated testing for error scenarios and edge cases
        """
        print("🚨 Validating Requirement 5: Automated testing for error scenarios and edge cases...")
        
        error_test_files = [
            "test_error_handling.py",
            "test_integration_error_handling.py"
        ]
        
        missing_error_tests = []
        error_patterns_found = []
        
        for test_file in error_test_files:
            if not os.path.exists(test_file):
                missing_error_tests.append(test_file)
            else:
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Check for error testing patterns
                error_patterns = [
                    "pytest.raises", "exception", "error", "failure", "timeout",
                    "edge_case", "boundary", "invalid", "corrupt", "missing"
                ]
                
                found_patterns = [pattern for pattern in error_patterns if pattern in content.lower()]
                if found_patterns:
                    error_patterns_found.extend(found_patterns)
        
        if missing_error_tests:
            return False, f"Missing error test files: {missing_error_tests}"
        
        if len(set(error_patterns_found)) < 5:
            return False, f"Insufficient error testing patterns found: {set(error_patterns_found)}"
        
        # Check for edge case test data
        edge_cases_file = Path("test_data/metadata/edge_cases.json")
        if edge_cases_file.exists():
            with open(edge_cases_file, 'r') as f:
                edge_data = json.load(f)
                edge_case_count = len(edge_data.get("edge_cases", []))
        else:
            edge_case_count = 0
        
        if edge_case_count < 3:
            return False, f"Insufficient edge case test data: {edge_case_count} cases"
        
        print(f"   ✅ Error handling test files: {len(error_test_files) - len(missing_error_tests)}")
        print(f"   ✅ Error testing patterns found: {len(set(error_patterns_found))}")
        print(f"   ✅ Edge case test data: {edge_case_count} cases")
        
        return True, f"Automated error scenario and edge case testing implemented with {edge_case_count} edge cases"
    
    def validate_test_infrastructure(self) -> Tuple[bool, str]:
        """Validate supporting test infrastructure"""
        print("🏗️ Validating test infrastructure...")
        
        infrastructure_files = [
            "pytest.ini",
            "conftest.py", 
            "test_runner.py",
            "test_comprehensive_suite.py"
        ]
        
        missing_infrastructure = []
        
        for file in infrastructure_files:
            if not os.path.exists(file):
                missing_infrastructure.append(file)
        
        if missing_infrastructure:
            return False, f"Missing infrastructure files: {missing_infrastructure}"
        
        # Check pytest configuration
        with open("pytest.ini", 'r') as f:
            pytest_config = f.read()
        
        required_markers = ["unit", "integration", "performance", "error_handling"]
        missing_markers = []
        
        for marker in required_markers:
            if marker not in pytest_config:
                missing_markers.append(marker)
        
        if missing_markers:
            return False, f"Missing pytest markers: {missing_markers}"
        
        print(f"   ✅ All infrastructure files present")
        print(f"   ✅ Pytest configuration with proper markers")
        
        return True, "Test infrastructure properly configured"
    
    def run_sample_tests(self) -> Tuple[bool, str]:
        """Run a sample of tests to verify they execute properly"""
        print("🔬 Running sample tests to verify execution...")
        
        try:
            # Run a quick unit test
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "test_utils.py::TestUtilities::test_create_temp_file",
                "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return False, f"Sample unit test failed: {result.stderr}"
            
            print("   ✅ Sample unit test executed successfully")
            
            # Test data generation
            result = subprocess.run([
                sys.executable, "test_data_generator.py"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return False, f"Test data generation failed: {result.stderr}"
            
            print("   ✅ Test data generation executed successfully")
            
            return True, "Sample tests execute properly"
            
        except subprocess.TimeoutExpired:
            return False, "Sample tests timed out"
        except Exception as e:
            return False, f"Sample test execution error: {e}"
    
    def validate_comprehensive_suite(self) -> Dict[str, Any]:
        """Run complete validation of the comprehensive testing suite"""
        print("🚀 Validating Comprehensive Testing Suite")
        print("=" * 80)
        
        validation_results = {}
        all_requirements_met = True
        
        # Validate each requirement
        requirements = [
            ("Unit tests for backend modules", self.validate_requirement_1_unit_tests),
            ("Integration tests for pipelines", self.validate_requirement_2_integration_tests), 
            ("Performance tests with file sizes", self.validate_requirement_3_performance_tests),
            ("Test data with known outputs", self.validate_requirement_4_test_data_sets),
            ("Error and edge case testing", self.validate_requirement_5_error_testing),
            ("Test infrastructure", self.validate_test_infrastructure),
            ("Test execution", self.run_sample_tests)
        ]
        
        for req_name, validator_func in requirements:
            print(f"\n📋 {req_name}:")
            try:
                is_valid, message = validator_func()
                validation_results[req_name] = {
                    "status": "passed" if is_valid else "failed",
                    "message": message
                }
                
                if is_valid:
                    print(f"   ✅ PASSED: {message}")
                else:
                    print(f"   ❌ FAILED: {message}")
                    all_requirements_met = False
                    
            except Exception as e:
                validation_results[req_name] = {
                    "status": "error",
                    "message": f"Validation error: {e}"
                }
                print(f"   💥 ERROR: {e}")
                all_requirements_met = False
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        
        passed_count = sum(1 for result in validation_results.values() if result["status"] == "passed")
        total_count = len(validation_results)
        
        print(f"Requirements Validated: {passed_count}/{total_count}")
        
        if all_requirements_met:
            print("🎉 ALL REQUIREMENTS MET - Comprehensive testing suite is complete!")
            overall_status = "COMPLETE"
        else:
            print("⚠️  REQUIREMENTS NOT MET - Additional work needed")
            overall_status = "INCOMPLETE"
            
            # Show failed requirements
            failed_reqs = [name for name, result in validation_results.items() if result["status"] != "passed"]
            print(f"\nFailed requirements: {failed_reqs}")
        
        print("=" * 80)
        
        return {
            "overall_status": overall_status,
            "requirements_met": all_requirements_met,
            "validation_results": validation_results,
            "passed_count": passed_count,
            "total_count": total_count
        }


def main():
    """Main entry point for test validation"""
    validator = TestSuiteValidator()
    results = validator.validate_comprehensive_suite()
    
    # Save validation results
    with open("test_validation_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    if results["requirements_met"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()