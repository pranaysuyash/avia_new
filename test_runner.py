#!/usr/bin/env python3
"""
Comprehensive test runner for the audio transcription application
Orchestrates all test suites and generates detailed reports
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import pytest

class TestRunner:
    """Comprehensive test runner and reporter"""
    
    def __init__(self):
        """Initialize test runner"""
        self.start_time = time.time()
        self.results = {
            "summary": {},
            "suites": {},
            "coverage": {},
            "performance": {},
            "errors": []
        }
        
        # Test suite configurations
        self.test_suites = {
            "unit": {
                "description": "Unit tests for individual modules",
                "files": [
                    "test_media.py",
                    "test_stt.py", 
                    "test_ner_basic.py",
                    "test_ner_advanced.py",
                    "test_tts.py"
                ],
                "markers": [],
                "timeout": 300  # 5 minutes
            },
            "integration": {
                "description": "Integration tests for component interaction",
                "files": [
                    "test_integration_workflow.py",
                    "test_integration_comprehensive.py",
                    "test_complete_integration.py"
                ],
                "markers": ["integration"],
                "timeout": 600  # 10 minutes
            },
            "error_handling": {
                "description": "Error handling and recovery tests",
                "files": [
                    "test_error_handling.py",
                    "test_integration_error_handling.py"
                ],
                "markers": ["error_handling"],
                "timeout": 300  # 5 minutes
            },
            "performance": {
                "description": "Performance and scalability tests",
                "files": [
                    "test_performance.py"
                ],
                "markers": ["performance"],
                "timeout": 900  # 15 minutes
            }
        }
    
    def setup_test_environment(self):
        """Set up test environment and dependencies"""
        print("🔧 Setting up test environment...")
        
        # Set test environment variables
        os.environ['OPENAI_API_KEY'] = 'test-key-for-testing'
        os.environ['ELEVENLABS_API_KEY'] = 'test-key-for-testing'
        os.environ['LOG_LEVEL'] = 'WARNING'  # Reduce log noise during tests
        
        # Generate test data
        try:
            from test_data_generator import TestDataGenerator
            generator = TestDataGenerator()
            generator.generate_all_test_data()
            print("  ✅ Test data generated successfully")
        except Exception as e:
            print(f"  ⚠️ Test data generation failed: {e}")
            self.results["errors"].append(f"Test data generation: {e}")
        
        # Check dependencies
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("📋 Checking dependencies...")
        
        required_packages = [
            ("pytest", "pytest"),
            ("pytest-cov", "pytest_cov"), 
            ("numpy", "numpy"),
            ("streamlit", "streamlit"),
            ("openai", "openai"),
            ("spacy", "spacy"),
            ("ffmpeg-python", "ffmpeg"),
            ("elevenlabs", "elevenlabs")
        ]
        
        missing_packages = []
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                print(f"  ✅ {package_name}")
            except ImportError:
                missing_packages.append(package_name)
                print(f"  ❌ {package_name}")
        
        if missing_packages:
            print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False
        
        return True
    
    def run_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test suite"""
        print(f"\n🧪 Running {suite_name} tests...")
        print(f"   {suite_config['description']}")
        
        suite_start = time.time()
        suite_results = {
            "name": suite_name,
            "description": suite_config["description"],
            "files": suite_config["files"],
            "start_time": suite_start,
            "status": "running",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration": 0,
            "coverage": 0,
            "errors": []
        }
        
        try:
            # Build pytest command
            cmd = ["python", "-m", "pytest", "-v", "--tb=short"]
            
            # Add coverage if requested
            if suite_name in ["unit", "integration"]:
                cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=json"])
            
            # Add markers
            if suite_config["markers"]:
                for marker in suite_config["markers"]:
                    cmd.extend(["-m", marker])
            
            # Add timeout
            cmd.extend(["--timeout", str(suite_config["timeout"])])
            
            # Add test files
            existing_files = []
            for test_file in suite_config["files"]:
                if os.path.exists(test_file):
                    existing_files.append(test_file)
                    cmd.append(test_file)
                else:
                    print(f"  ⚠️ Test file not found: {test_file}")
            
            if not existing_files:
                suite_results["status"] = "skipped"
                suite_results["errors"].append("No test files found")
                return suite_results
            
            # Run tests
            print(f"  Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite_config["timeout"]
            )
            
            # Parse results
            suite_results["return_code"] = result.returncode
            suite_results["stdout"] = result.stdout
            suite_results["stderr"] = result.stderr
            
            # Extract test counts from output
            self.parse_pytest_output(result.stdout, suite_results)
            
            # Determine status
            if result.returncode == 0:
                suite_results["status"] = "passed"
            elif result.returncode == 5:  # No tests collected
                suite_results["status"] = "skipped"
            else:
                suite_results["status"] = "failed"
            
        except subprocess.TimeoutExpired:
            suite_results["status"] = "timeout"
            suite_results["errors"].append(f"Tests timed out after {suite_config['timeout']} seconds")
            
        except Exception as e:
            suite_results["status"] = "error"
            suite_results["errors"].append(str(e))
        
        suite_results["duration"] = time.time() - suite_start
        
        # Print summary
        self.print_suite_summary(suite_results)
        
        return suite_results
    
    def parse_pytest_output(self, output: str, suite_results: Dict[str, Any]):
        """Parse pytest output to extract test statistics"""
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for test result summary
            if "passed" in line and "failed" in line:
                # Parse line like "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        suite_results["tests_passed"] = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        suite_results["tests_failed"] = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        suite_results["tests_skipped"] = int(parts[i-1])
            
            # Look for individual test results
            elif "::" in line and ("PASSED" in line or "FAILED" in line or "SKIPPED" in line):
                suite_results["tests_run"] += 1
        
        # Calculate total if not found in summary
        if suite_results["tests_run"] == 0:
            suite_results["tests_run"] = (
                suite_results["tests_passed"] + 
                suite_results["tests_failed"] + 
                suite_results["tests_skipped"]
            )
    
    def print_suite_summary(self, suite_results: Dict[str, Any]):
        """Print summary for a test suite"""
        status_emoji = {
            "passed": "✅",
            "failed": "❌", 
            "skipped": "⏭️",
            "timeout": "⏰",
            "error": "💥"
        }
        
        emoji = status_emoji.get(suite_results["status"], "❓")
        print(f"\n{emoji} {suite_results['name'].upper()} TESTS {suite_results['status'].upper()}")
        print(f"   Duration: {suite_results['duration']:.2f}s")
        print(f"   Tests run: {suite_results['tests_run']}")
        print(f"   Passed: {suite_results['tests_passed']}")
        print(f"   Failed: {suite_results['tests_failed']}")
        print(f"   Skipped: {suite_results['tests_skipped']}")
        
        if suite_results["errors"]:
            print("   Errors:")
            for error in suite_results["errors"]:
                print(f"     • {error}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting comprehensive test suite...")
        print("=" * 70)
        
        # Setup
        self.setup_test_environment()
        
        # Run each test suite
        for suite_name, suite_config in self.test_suites.items():
            suite_results = self.run_test_suite(suite_name, suite_config)
            self.results["suites"][suite_name] = suite_results
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_duration = time.time() - self.start_time
        
        # Calculate totals
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        suites_passed = 0
        suites_failed = 0
        
        for suite_results in self.results["suites"].values():
            total_tests += suite_results["tests_run"]
            total_passed += suite_results["tests_passed"]
            total_failed += suite_results["tests_failed"]
            total_skipped += suite_results["tests_skipped"]
            
            if suite_results["status"] == "passed":
                suites_passed += 1
            elif suite_results["status"] in ["failed", "error", "timeout"]:
                suites_failed += 1
        
        # Update summary
        self.results["summary"] = {
            "total_duration": total_duration,
            "total_suites": len(self.test_suites),
            "suites_passed": suites_passed,
            "suites_failed": suites_failed,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Print final report
        self.print_final_report()
        
        # Save detailed report
        self.save_detailed_report()
    
    def print_final_report(self):
        """Print final test report"""
        summary = self.results["summary"]
        
        print("\n" + "=" * 70)
        print("🎯 FINAL TEST REPORT")
        print("=" * 70)
        
        # Overall status
        if summary["suites_failed"] == 0 and summary["total_failed"] == 0:
            print("🎉 ALL TESTS PASSED!")
            overall_status = "SUCCESS"
        else:
            print("❌ SOME TESTS FAILED")
            overall_status = "FAILURE"
        
        print(f"\nOverall Status: {overall_status}")
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        # Suite summary
        print(f"\n📊 Test Suite Summary:")
        print(f"   Total Suites: {summary['total_suites']}")
        print(f"   Suites Passed: {summary['suites_passed']}")
        print(f"   Suites Failed: {summary['suites_failed']}")
        
        # Test summary
        print(f"\n🧪 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['total_passed']}")
        print(f"   Failed: {summary['total_failed']}")
        print(f"   Skipped: {summary['total_skipped']}")
        
        # Suite details
        print(f"\n📋 Suite Details:")
        for suite_name, suite_results in self.results["suites"].items():
            status_emoji = {"passed": "✅", "failed": "❌", "skipped": "⏭️", "timeout": "⏰", "error": "💥"}
            emoji = status_emoji.get(suite_results["status"], "❓")
            
            print(f"   {emoji} {suite_name}: {suite_results['tests_passed']}/{suite_results['tests_run']} passed ({suite_results['duration']:.1f}s)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if summary["total_failed"] > 0:
            print("   • Review failed tests and fix underlying issues")
            print("   • Check error logs for detailed failure information")
        
        if summary["total_skipped"] > 0:
            print("   • Review skipped tests - may indicate missing dependencies")
        
        if summary["success_rate"] < 90:
            print("   • Consider improving test coverage and reliability")
        
        if summary["success_rate"] >= 95:
            print("   • Excellent test coverage! Consider adding more edge cases")
        
        print("\n" + "=" * 70)
    
    def save_detailed_report(self):
        """Save detailed report to JSON file"""
        report_file = "test_report.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"📄 Detailed report saved to: {report_file}")
            
        except Exception as e:
            print(f"⚠️ Failed to save detailed report: {e}")
    
    def run_specific_suite(self, suite_name: str):
        """Run a specific test suite"""
        if suite_name not in self.test_suites:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(self.test_suites.keys())}")
            return
        
        print(f"🚀 Running {suite_name} test suite...")
        print("=" * 50)
        
        self.setup_test_environment()
        suite_config = self.test_suites[suite_name]
        suite_results = self.run_test_suite(suite_name, suite_config)
        
        # Simple report for single suite
        print(f"\n📊 {suite_name.upper()} RESULTS:")
        print(f"   Status: {suite_results['status']}")
        print(f"   Duration: {suite_results['duration']:.2f}s")
        print(f"   Tests: {suite_results['tests_passed']}/{suite_results['tests_run']} passed")
        
        if suite_results["errors"]:
            print("   Errors:")
            for error in suite_results["errors"]:
                print(f"     • {error}")


def main():
    """Main entry point"""
    runner = TestRunner()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        if suite_name == "--help":
            print("Usage: python test_runner.py [suite_name]")
            print("\nAvailable test suites:")
            for name, config in runner.test_suites.items():
                print(f"  {name}: {config['description']}")
            print("\nRun without arguments to execute all test suites.")
            return
        
        runner.run_specific_suite(suite_name)
    else:
        runner.run_all_tests()


if __name__ == "__main__":
    main()