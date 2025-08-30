"""
Comprehensive test suite for Unit Testing Framework and Coverage Analysis
Tests all components of the automated testing framework
"""

import pytest
import os
import tempfile
import json
import ast
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from unit_testing_framework import (
    UnitTestingFramework, CodeAnalyzer, TestGenerator, CoverageAnalyzer,
    TestCaseInfo, CoverageMetrics, CoverageReport, TestGenerationResult
)

class TestCodeAnalyzer:
    """Test cases for CodeAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = CodeAnalyzer()
        self.sample_code = '''
def simple_function(x, y):
    """A simple function for testing"""
    if x > y:
        return x + y
    else:
        return x - y

class SampleClass:
    """A sample class for testing"""
    
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
    
    @property
    def doubled_value(self):
        return self.value * 2
    
    @staticmethod
    def static_method():
        return "static"
'''
    
    def test_analyze_file_success(self):
        """Test successful file analysis"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.sample_code)
            f.flush()
            
            try:
                analysis = self.analyzer.analyze_file(f.name)
                
                assert 'functions' in analysis
                assert 'classes' in analysis
                assert 'imports' in analysis
                assert 'complexity' in analysis
                
                # Check functions
                functions = analysis['functions']
                assert len(functions) >= 1
                
                simple_func = next((f for f in functions if f['name'] == 'simple_function'), None)
                assert simple_func is not None
                assert simple_func['args'] == ['x', 'y']
                assert simple_func['complexity'] >= 2  # Has if-else
                
                # Check classes
                classes = analysis['classes']
                assert len(classes) >= 1
                
                sample_class = next((c for c in classes if c['name'] == 'SampleClass'), None)
                assert sample_class is not None
                assert len(sample_class['methods']) >= 2
                assert len(sample_class['properties']) >= 1
                
            finally:
                os.unlink(f.name)
    
    def test_analyze_nonexistent_file(self):
        """Test analysis of non-existent file"""
        result = self.analyzer.analyze_file("nonexistent_file.py")
        assert result == {}
    
    def test_extract_functions(self):
        """Test function extraction"""
        tree = ast.parse(self.sample_code)
        functions = self.analyzer._extract_functions(tree)
        
        assert len(functions) >= 1
        
        # Check simple_function
        simple_func = next((f for f in functions if f['name'] == 'simple_function'), None)
        assert simple_func is not None
        assert simple_func['args'] == ['x', 'y']
        assert simple_func['docstring'] == "A simple function for testing"
        assert simple_func['complexity'] >= 2
    
    def test_extract_classes(self):
        """Test class extraction"""
        tree = ast.parse(self.sample_code)
        classes = self.analyzer._extract_classes(tree)
        
        assert len(classes) >= 1
        
        sample_class = next((c for c in classes if c['name'] == 'SampleClass'), None)
        assert sample_class is not None
        assert sample_class['docstring'] == "A sample class for testing"
        assert len(sample_class['methods']) >= 2
        assert len(sample_class['properties']) >= 1
    
    def test_calculate_complexity(self):
        """Test complexity calculation"""
        complex_code = '''
def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                try:
                    result = i / (i - 1)
                except ZeroDivisionError:
                    continue
            else:
                while i > 0:
                    i -= 1
    return x
'''
        tree = ast.parse(complex_code)
        complexity = self.analyzer._calculate_complexity(tree)
        
        assert complexity['total'] > 5  # Should be quite complex
        assert 'complex_function' in complexity['functions']
        assert complexity['functions']['complex_function'] > 5

class TestTestGenerator:
    """Test cases for TestGenerator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = CodeAnalyzer()
        self.generator = TestGenerator(self.analyzer)
        
        self.sample_file_content = '''
def add_numbers(a, b):
    """Add two numbers together"""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Arguments must be numbers")
    return a + b

class Calculator:
    def __init__(self):
        self.history = []
    
    def multiply(self, x, y):
        result = x * y
        self.history.append(result)
        return result
    
    @property
    def last_result(self):
        return self.history[-1] if self.history else None
'''
    
    def test_generate_tests_for_file(self):
        """Test test generation for a file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.sample_file_content)
            f.flush()
            
            try:
                test_cases = self.generator.generate_tests_for_file(f.name)
                
                assert len(test_cases) > 0
                
                # Check that we have tests for the function
                function_tests = [tc for tc in test_cases if 'add_numbers' in tc.function_name]
                assert len(function_tests) > 0
                
                # Check that we have tests for the class
                class_tests = [tc for tc in test_cases if 'Calculator' in tc.function_name]
                assert len(class_tests) > 0
                
                # Verify test case structure
                for test_case in test_cases:
                    assert isinstance(test_case, TestCaseInfo)
                    assert test_case.function_name
                    assert test_case.test_name
                    assert test_case.test_code
                    assert test_case.expected_behavior
                    assert test_case.complexity_score > 0
                
            finally:
                os.unlink(f.name)
    
    def test_generate_function_tests(self):
        """Test function test generation"""
        func_info = {
            'name': 'test_function',
            'args': ['x', 'y'],
            'complexity': 3,
            'has_exceptions': True
        }
        
        test_cases = self.generator._generate_function_tests(func_info, "test_file.py")
        
        assert len(test_cases) > 0
        
        # Should have basic test
        basic_tests = [tc for tc in test_cases if 'basic_functionality' in tc.test_name]
        assert len(basic_tests) > 0
        
        # Should have edge case tests
        edge_tests = [tc for tc in test_cases if 'edge_case' in tc.test_name or 'empty_input' in tc.test_name]
        assert len(edge_tests) > 0
        
        # Should have exception tests
        exception_tests = [tc for tc in test_cases if 'exception' in tc.test_name]
        assert len(exception_tests) > 0
    
    def test_generate_class_tests(self):
        """Test class test generation"""
        class_info = {
            'name': 'TestClass',
            'methods': [
                {'name': 'method1', 'complexity': 2},
                {'name': 'method2', 'complexity': 1}
            ],
            'properties': [
                {'name': 'prop1'}
            ]
        }
        
        test_cases = self.generator._generate_class_tests(class_info, "test_file.py")
        
        assert len(test_cases) > 0
        
        # Should have initialization test
        init_tests = [tc for tc in test_cases if 'initialization' in tc.test_name]
        assert len(init_tests) > 0
        
        # Should have method tests
        method_tests = [tc for tc in test_cases if 'method1' in tc.test_name or 'method2' in tc.test_name]
        assert len(method_tests) > 0
        
        # Should have property tests
        prop_tests = [tc for tc in test_cases if 'prop1' in tc.test_name]
        assert len(prop_tests) > 0
    
    def test_create_basic_test(self):
        """Test basic test creation"""
        func_info = {
            'name': 'sample_function',
            'args': ['param1', 'param2']
        }
        
        test_case = self.generator._create_basic_test(func_info, "sample_module.py")
        
        assert isinstance(test_case, TestCaseInfo)
        assert test_case.function_name == 'sample_function'
        assert 'test_sample_function_basic_functionality' in test_case.test_name
        assert 'def test_sample_function_basic_functionality' in test_case.test_code
        assert 'from sample_module import sample_function' in test_case.test_code

class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = CoverageAnalyzer()
    
    def test_start_stop_coverage_tracking(self):
        """Test coverage tracking start/stop"""
        # Test starting coverage
        self.analyzer.start_coverage_tracking(['.'])
        assert self.analyzer.coverage_instance is not None
        
        # Test stopping coverage
        self.analyzer.stop_coverage_tracking()
        # Coverage instance should still exist but be stopped
        assert self.analyzer.coverage_instance is not None
    
    @patch('coverage.Coverage')
    def test_analyze_coverage_success(self, mock_coverage_class):
        """Test successful coverage analysis"""
        # Mock coverage instance
        mock_coverage = Mock()
        mock_coverage_class.return_value = mock_coverage
        
        # Mock analysis results
        mock_coverage.analysis2.return_value = (
            'test_file.py',  # filename
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # statements
            [],  # excluded
            [3, 7],  # missing
            []  # missing_branches
        )
        
        mock_coverage.load.return_value = None
        
        self.analyzer.coverage_instance = mock_coverage
        
        report = self.analyzer.analyze_coverage('test_file.py')
        
        assert isinstance(report, CoverageReport)
        assert report.file_path == 'test_file.py'
        assert report.metrics.line_coverage == 80.0  # 8/10 covered
        assert len(report.metrics.missing_lines) == 2
        assert 3 in report.metrics.missing_lines
        assert 7 in report.metrics.missing_lines
    
    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        metrics = CoverageMetrics(
            line_coverage=85.0,
            branch_coverage=75.0,
            function_coverage=90.0,
            statement_coverage=85.0,
            missing_lines=[],
            missing_branches=[],
            covered_lines=[],
            total_lines=100,
            executable_lines=80
        )
        
        score = self.analyzer._calculate_quality_score(metrics)
        
        assert 0 <= score <= 100
        assert score > 80  # Should be high with good coverage
    
    def test_identify_coverage_gaps(self):
        """Test coverage gap identification"""
        metrics = CoverageMetrics(
            line_coverage=65.0,  # Below 80%
            branch_coverage=45.0,  # Below 70%
            function_coverage=90.0,
            statement_coverage=65.0,
            missing_lines=[1, 2, 3, 4, 5],
            missing_branches=[(1, 2), (3, 4)],
            covered_lines=[],
            total_lines=100,
            executable_lines=80
        )
        
        gaps = self.analyzer._identify_coverage_gaps('test_file.py', metrics)
        
        assert len(gaps) > 0
        
        # Should identify missing lines
        missing_lines_gap = next((g for g in gaps if g['type'] == 'missing_lines'), None)
        assert missing_lines_gap is not None
        
        # Should identify missing branches
        missing_branches_gap = next((g for g in gaps if g['type'] == 'missing_branches'), None)
        assert missing_branches_gap is not None
        
        # Should identify low coverage
        low_coverage_gap = next((g for g in gaps if g['type'] == 'low_coverage'), None)
        assert low_coverage_gap is not None
    
    def test_generate_improvement_suggestions(self):
        """Test improvement suggestion generation"""
        metrics = CoverageMetrics(
            line_coverage=65.0,
            branch_coverage=55.0,
            function_coverage=85.0,
            statement_coverage=65.0,
            missing_lines=[1, 2, 3],
            missing_branches=[(1, 2)],
            covered_lines=[],
            total_lines=100,
            executable_lines=80
        )
        
        gaps = [
            {'type': 'missing_lines', 'severity': 'high'},
            {'type': 'missing_branches', 'severity': 'medium'}
        ]
        
        suggestions = self.analyzer._generate_improvement_suggestions(metrics, gaps)
        
        assert len(suggestions) > 0
        
        # Should suggest improving line coverage
        line_suggestion = next((s for s in suggestions if 'line coverage' in s.lower()), None)
        assert line_suggestion is not None
        
        # Should suggest improving branch coverage
        branch_suggestion = next((s for s in suggestions if 'branch coverage' in s.lower()), None)
        assert branch_suggestion is not None

class TestUnitTestingFramework:
    """Test cases for UnitTestingFramework class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.framework = UnitTestingFramework(source_paths=['.'])
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.sample_files = []
        
        # Create sample Python file
        sample_content = '''
def sample_function(x):
    """Sample function for testing"""
    return x * 2

class SampleClass:
    def __init__(self, value):
        self.value = value
    
    def get_double(self):
        return self.value * 2
'''
        
        sample_file = os.path.join(self.temp_dir, 'sample.py')
        with open(sample_file, 'w') as f:
            f.write(sample_content)
        
        self.sample_files.append(sample_file)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test framework initialization"""
        framework = UnitTestingFramework(source_paths=['test_path'])
        
        assert framework.source_paths == ['test_path']
        assert isinstance(framework.analyzer, CodeAnalyzer)
        assert isinstance(framework.generator, TestGenerator)
        assert isinstance(framework.coverage_analyzer, CoverageAnalyzer)
    
    def test_find_python_files(self):
        """Test Python file discovery"""
        framework = UnitTestingFramework(source_paths=[self.temp_dir])
        python_files = framework._find_python_files()
        
        assert len(python_files) > 0
        assert any('sample.py' in f for f in python_files)
    
    def test_generate_tests_for_project(self):
        """Test project-wide test generation"""
        framework = UnitTestingFramework(source_paths=[self.temp_dir])
        
        output_dir = os.path.join(self.temp_dir, 'generated_tests')
        result = framework.generate_tests_for_project(output_dir)
        
        assert isinstance(result, TestGenerationResult)
        assert len(result.generated_tests) > 0
        assert result.generation_time > 0
        assert result.success_rate >= 0
        assert len(result.recommendations) > 0
        
        # Check that test files were created
        assert os.path.exists(output_dir)
        test_files = [f for f in os.listdir(output_dir) if f.startswith('test_') and f.endswith('.py')]
        assert len(test_files) > 0
    
    def test_write_test_file(self):
        """Test test file writing"""
        test_cases = [
            TestCaseInfo(
                function_name='test_func',
                test_name='test_test_func_basic',
                test_code='def test_test_func_basic():\n    pass',
                parameters=[],
                expected_behavior='Test behavior',
                complexity_score=1.0,
                coverage_targets=['test_func:basic']
            )
        ]
        
        output_dir = os.path.join(self.temp_dir, 'test_output')
        os.makedirs(output_dir, exist_ok=True)
        
        test_file_path = self.framework._write_test_file(
            self.sample_files[0], test_cases, output_dir
        )
        
        assert os.path.exists(test_file_path)
        
        # Check file content
        with open(test_file_path, 'r') as f:
            content = f.read()
        
        assert 'def test_test_func_basic():' in content
        assert 'TEST_METADATA' in content
    
    def test_validate_coverage_requirements(self):
        """Test coverage requirements validation"""
        requirements = {
            'line_coverage': 80.0,
            'branch_coverage': 70.0,
            'function_coverage': 90.0
        }
        
        # Mock the coverage analysis to return specific values
        with patch.object(self.framework.coverage_analyzer, 'analyze_coverage') as mock_analyze:
            mock_report = Mock()
            mock_report.metrics.line_coverage = 75.0  # Below requirement
            mock_report.metrics.branch_coverage = 85.0  # Above requirement
            mock_report.metrics.function_coverage = 95.0  # Above requirement
            mock_analyze.return_value = mock_report
            
            validation = self.framework.validate_coverage_requirements(requirements)
            
            assert 'passed' in validation
            assert 'failures' in validation
            assert 'warnings' in validation
            assert 'summary' in validation
            
            # Should fail due to low line coverage
            assert not validation['passed']
            assert len(validation['failures']) > 0
            
            # Check summary
            assert 'line_coverage' in validation['summary']
            assert validation['summary']['line_coverage']['actual'] == 75.0
            assert validation['summary']['line_coverage']['required'] == 80.0
            assert not validation['summary']['line_coverage']['passed']

class TestIntegration:
    """Integration tests for the complete framework"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a more complex sample project
        self.create_sample_project()
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_sample_project(self):
        """Create a sample project for integration testing"""
        # Main module
        main_content = '''
"""Main module for integration testing"""

def calculate_area(length, width):
    """Calculate area of rectangle"""
    if length <= 0 or width <= 0:
        raise ValueError("Dimensions must be positive")
    return length * width

def calculate_volume(length, width, height):
    """Calculate volume of rectangular prism"""
    area = calculate_area(length, width)
    if height <= 0:
        raise ValueError("Height must be positive")
    return area * height

class Shape:
    """Base shape class"""
    
    def __init__(self, name):
        self.name = name
    
    def get_name(self):
        return self.name
    
    def area(self):
        raise NotImplementedError("Subclasses must implement area method")

class Rectangle(Shape):
    """Rectangle shape"""
    
    def __init__(self, length, width):
        super().__init__("Rectangle")
        self.length = length
        self.width = width
    
    def area(self):
        return calculate_area(self.length, self.width)
    
    @property
    def perimeter(self):
        return 2 * (self.length + self.width)
'''
        
        with open(os.path.join(self.temp_dir, 'main.py'), 'w') as f:
            f.write(main_content)
        
        # Utility module
        utils_content = '''
"""Utility functions for integration testing"""

import math

def is_even(number):
    """Check if number is even"""
    if not isinstance(number, int):
        raise TypeError("Input must be an integer")
    return number % 2 == 0

def factorial(n):
    """Calculate factorial"""
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def prime_factors(n):
    """Find prime factors of a number"""
    if not isinstance(n, int) or n <= 1:
        raise ValueError("Input must be an integer greater than 1")
    
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors
'''
        
        with open(os.path.join(self.temp_dir, 'utils.py'), 'w') as f:
            f.write(utils_content)
    
    def test_complete_workflow(self):
        """Test the complete testing workflow"""
        framework = UnitTestingFramework(source_paths=[self.temp_dir])
        
        # Step 1: Generate tests
        output_dir = os.path.join(self.temp_dir, 'generated_tests')
        result = framework.generate_tests_for_project(output_dir)
        
        # Verify test generation
        assert isinstance(result, TestGenerationResult)
        assert len(result.generated_tests) > 0
        
        # Should have tests for functions and classes
        function_tests = [tc for tc in result.generated_tests if '.' not in tc.function_name]
        class_tests = [tc for tc in result.generated_tests if '.' in tc.function_name]
        
        assert len(function_tests) > 0
        assert len(class_tests) > 0
        
        # Step 2: Validate coverage requirements
        requirements = {
            'line_coverage': 70.0,
            'branch_coverage': 60.0,
            'function_coverage': 80.0
        }
        
        # Mock coverage analysis for integration test
        with patch.object(framework.coverage_analyzer, 'analyze_coverage') as mock_analyze:
            mock_report = Mock()
            mock_report.metrics.line_coverage = 85.0
            mock_report.metrics.branch_coverage = 75.0
            mock_report.metrics.function_coverage = 90.0
            mock_analyze.return_value = mock_report
            
            validation = framework.validate_coverage_requirements(requirements)
            
            # Should pass all requirements
            assert validation['passed']
            assert len(validation['failures']) == 0
        
        # Step 3: Verify generated test files
        assert os.path.exists(output_dir)
        test_files = [f for f in os.listdir(output_dir) if f.startswith('test_') and f.endswith('.py')]
        assert len(test_files) >= 2  # Should have tests for main.py and utils.py
        
        # Verify test file content
        for test_file in test_files:
            test_file_path = os.path.join(output_dir, test_file)
            with open(test_file_path, 'r') as f:
                content = f.read()
            
            # Should contain proper test structure
            assert 'def test_' in content
            assert 'import pytest' in content
            assert 'TEST_METADATA' in content
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        framework = UnitTestingFramework(source_paths=[self.temp_dir])
        
        # Test with invalid source path
        invalid_framework = UnitTestingFramework(source_paths=['/nonexistent/path'])
        result = invalid_framework.generate_tests_for_project()
        
        # Should handle gracefully
        assert isinstance(result, TestGenerationResult)
        assert len(result.generated_tests) == 0
        
        # Test with invalid file
        with patch.object(framework.generator, 'generate_tests_for_file') as mock_generate:
            mock_generate.side_effect = Exception("Test error")
            
            result = framework.generate_tests_for_project()
            
            # Should handle errors gracefully
            assert isinstance(result, TestGenerationResult)
    
    def test_performance_characteristics(self):
        """Test performance characteristics of the framework"""
        framework = UnitTestingFramework(source_paths=[self.temp_dir])
        
        import time
        start_time = time.time()
        
        result = framework.generate_tests_for_project()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (less than 10 seconds for small project)
        assert execution_time < 10.0
        
        # Should have reasonable success rate
        assert result.success_rate > 0.5
        
        # Should generate reasonable number of tests
        files_analyzed = len(framework._find_python_files())
        if files_analyzed > 0:
            tests_per_file = len(result.generated_tests) / files_analyzed
            assert tests_per_file > 1  # At least 1 test per file on average

# Performance and stress tests
class TestPerformance:
    """Performance tests for the framework"""
    
    @pytest.mark.performance
    def test_large_file_analysis(self):
        """Test analysis of large Python files"""
        # Create a large Python file
        large_content = '''
"""Large file for performance testing"""

'''
        
        # Add many functions
        for i in range(100):
            large_content += f'''
def function_{i}(param1, param2=None):
    """Function {i} for testing"""
    if param1 is None:
        return param2
    elif param2 is None:
        return param1
    else:
        return param1 + param2
'''
        
        # Add many classes
        for i in range(20):
            large_content += f'''
class Class_{i}:
    """Class {i} for testing"""
    
    def __init__(self, value):
        self.value = value
    
    def method_{i}(self):
        return self.value * {i}
    
    @property
    def property_{i}(self):
        return self.value + {i}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            f.flush()
            
            try:
                analyzer = CodeAnalyzer()
                
                import time
                start_time = time.time()
                
                analysis = analyzer.analyze_file(f.name)
                
                end_time = time.time()
                analysis_time = end_time - start_time
                
                # Should complete analysis in reasonable time
                assert analysis_time < 5.0  # Less than 5 seconds
                
                # Should find all functions and classes
                assert len(analysis['functions']) >= 100
                assert len(analysis['classes']) >= 20
                
            finally:
                os.unlink(f.name)
    
    @pytest.mark.performance
    def test_concurrent_test_generation(self):
        """Test concurrent test generation performance"""
        import threading
        import time
        
        framework = UnitTestingFramework(source_paths=['.'])
        
        # Create multiple temporary files
        temp_files = []
        for i in range(5):
            content = f'''
def test_function_{i}(x):
    return x * {i}

class TestClass_{i}:
    def method(self):
        return {i}
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                f.flush()
                temp_files.append(f.name)
        
        try:
            results = []
            threads = []
            
            def generate_tests(file_path):
                test_cases = framework.generator.generate_tests_for_file(file_path)
                results.append(len(test_cases))
            
            start_time = time.time()
            
            # Start concurrent test generation
            for file_path in temp_files:
                thread = threading.Thread(target=generate_tests, args=(file_path,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete in reasonable time
            assert total_time < 10.0
            
            # Should generate tests for all files
            assert len(results) == len(temp_files)
            assert all(count > 0 for count in results)
            
        finally:
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])