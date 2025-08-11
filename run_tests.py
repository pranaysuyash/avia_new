#!/usr/bin/env python3
"""
Test runner for Whisper Advanced Integration
Provides different test execution modes and reporting options
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False)
    end_time = time.time()
    
    print(f"\nCompleted in {end_time - start_time:.2f} seconds")
    print(f"Exit code: {result.returncode}")
    
    return result.returncode == 0

def run_unit_tests():
    """Run unit tests only"""
    cmd = "python -m pytest -m unit -v --tb=short"
    return run_command(cmd, "Unit Tests")

def run_integration_tests():
    """Run integration tests only"""
    cmd = "python -m pytest -m integration -v --tb=short"
    return run_command(cmd, "Integration Tests")

def run_api_tests():
    """Run API tests only"""
    cmd = "python -m pytest -m api -v --tb=short"
    return run_command(cmd, "API Tests")

def run_performance_tests():
    """Run performance tests only"""
    cmd = "python -m pytest -m performance -v --tb=short --durations=0"
    return run_command(cmd, "Performance Tests")

def run_all_tests():
    """Run all tests with coverage"""
    cmd = """python -m pytest -v --tb=short \
        --cov=whisper_advanced_processor \
        --cov=whisper_audio_preprocessor \
        --cov=whisper_advanced_exceptions \
        --cov=api.endpoints.whisper_advanced \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        --cov-report=xml:coverage.xml \
        --junit-xml=test-results.xml"""
    return run_command(cmd, "All Tests with Coverage")

def run_fast_tests():
    """Run fast tests only (exclude slow and performance tests)"""
    cmd = "python -m pytest -v --tb=short -m 'not slow and not performance'"
    return run_command(cmd, "Fast Tests")

def run_smoke_tests():
    """Run smoke tests to verify basic functionality"""
    cmd = "python -m pytest -v --tb=short -k 'test_initialization or test_config_validation or test_health'"
    return run_command(cmd, "Smoke Tests")

def run_security_tests():
    """Run security-focused tests"""
    cmd = "python -m pytest -v --tb=short -k 'security or auth or validation'"
    return run_command(cmd, "Security Tests")

def run_load_tests():
    """Run load and stress tests"""
    cmd = "python -m pytest -v --tb=short -k 'load or concurrent or batch' --durations=0"
    return run_command(cmd, "Load Tests")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-asyncio',
        'fastapi',
        'numpy',
        'librosa',
        'whisper',
        'noisereduce'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("\nAll dependencies are installed!")
    return True

def generate_test_report():
    """Generate a comprehensive test report"""
    print("Generating comprehensive test report...")
    
    # Run tests with detailed reporting
    cmd = """python -m pytest --tb=short \
        --cov=whisper_advanced_processor \
        --cov=whisper_audio_preprocessor \
        --cov=whisper_advanced_exceptions \
        --cov=api.endpoints.whisper_advanced \
        --cov-report=html:htmlcov \
        --cov-report=term \
        --junit-xml=test-results.xml \
        --html=test-report.html --self-contained-html"""
    
    success = run_command(cmd, "Comprehensive Test Report Generation")
    
    if success:
        print("\nTest reports generated:")
        print("- HTML Coverage Report: htmlcov/index.html")
        print("- Test Report: test-report.html")
        print("- JUnit XML: test-results.xml")
        print("- Coverage XML: coverage.xml")
    
    return success

def clean_test_artifacts():
    """Clean up test artifacts and cache files"""
    print("Cleaning test artifacts...")
    
    artifacts = [
        '__pycache__',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        'test-results.xml',
        'test-report.html',
        'coverage.xml',
        'test_data'
    ]
    
    for artifact in artifacts:
        if os.path.exists(artifact):
            if os.path.isdir(artifact):
                import shutil
                shutil.rmtree(artifact)
                print(f"Removed directory: {artifact}")
            else:
                os.remove(artifact)
                print(f"Removed file: {artifact}")
    
    print("Test artifacts cleaned!")

def main():
    parser = argparse.ArgumentParser(description="Whisper Advanced Integration Test Runner")
    parser.add_argument('--mode', choices=[
        'unit', 'integration', 'api', 'performance', 'all', 'fast', 'smoke', 
        'security', 'load', 'report'
    ], default='all', help='Test mode to run')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--clean', action='store_true', help='Clean test artifacts')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Set environment variables for testing
    os.environ['TESTING'] = '1'
    os.environ['LOG_LEVEL'] = 'INFO' if args.verbose else 'WARNING'
    
    success = True
    
    if args.clean:
        clean_test_artifacts()
        return
    
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        return
    
    # Run tests based on mode
    if args.mode == 'unit':
        success = run_unit_tests()
    elif args.mode == 'integration':
        success = run_integration_tests()
    elif args.mode == 'api':
        success = run_api_tests()
    elif args.mode == 'performance':
        success = run_performance_tests()
    elif args.mode == 'fast':
        success = run_fast_tests()
    elif args.mode == 'smoke':
        success = run_smoke_tests()
    elif args.mode == 'security':
        success = run_security_tests()
    elif args.mode == 'load':
        success = run_load_tests()
    elif args.mode == 'report':
        success = generate_test_report()
    else:  # 'all'
        success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()