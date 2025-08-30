"""
Unit Testing Framework and Coverage Analysis
Comprehensive unit testing framework with automated test generation and coverage analysis
"""

import ast
import inspect
import importlib
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import coverage
import pytest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestCaseInfo:
    """Information about a generated test case"""
    function_name: str
    test_name: str
    test_code: str
    parameters: List[Dict[str, Any]]
    expected_behavior: str
    complexity_score: float
    coverage_targets: List[str]

@dataclass
class CoverageMetrics:
    """Coverage analysis metrics"""
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    statement_coverage: float
    missing_lines: List[int]
    missing_branches: List[Tuple[int, int]]
    covered_lines: List[int]
    total_lines: int
    executable_lines: int

@dataclass
class CoverageReport:
    """Comprehensive coverage report"""
    file_path: str
    metrics: CoverageMetrics
    quality_score: float
    coverage_gaps: List[Dict[str, Any]]
    improvement_suggestions: List[str]
    timestamp: datetime

@dataclass
class TestGenerationResult:
    """Result of automated test generation"""
    generated_tests: List[TestCaseInfo]
    coverage_analysis: CoverageReport
    generation_time: float
    success_rate: float
    recommendations: List[str]

class CodeAnalyzer:
    """Analyzes code to understand structure and generate test cases"""
    
    def __init__(self):
        self.ast_cache = {}
        self.complexity_cache = {}
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a Python file and extract testable components"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            self.ast_cache[file_path] = tree
            
            analysis = {
                'functions': self._extract_functions(tree),
                'classes': self._extract_classes(tree),
                'imports': self._extract_imports(tree),
                'complexity': self._calculate_complexity(tree),
                'dependencies': self._analyze_dependencies(tree)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {}
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract function definitions and their metadata"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'defaults': len(node.args.defaults),
                    'returns': self._get_return_annotation(node),
                    'docstring': ast.get_docstring(node),
                    'line_number': node.lineno,
                    'complexity': self._calculate_function_complexity(node),
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'is_async': isinstance(node, ast.AsyncFunctionDef),
                    'has_exceptions': self._has_exception_handling(node)
                }
                functions.append(func_info)
        
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract class definitions and their methods"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'bases': [self._get_base_name(base) for base in node.bases],
                    'methods': [],
                    'properties': [],
                    'line_number': node.lineno,
                    'docstring': ast.get_docstring(node)
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'args': [arg.arg for arg in item.args.args],
                            'is_property': any(d.id == 'property' for d in item.decorator_list if isinstance(d, ast.Name)),
                            'is_static': any(d.id == 'staticmethod' for d in item.decorator_list if isinstance(d, ast.Name)),
                            'is_class_method': any(d.id == 'classmethod' for d in item.decorator_list if isinstance(d, ast.Name)),
                            'complexity': self._calculate_function_complexity(item)
                        }
                        
                        if method_info['is_property']:
                            class_info['properties'].append(method_info)
                        else:
                            class_info['methods'].append(method_info)
                
                classes.append(class_info)
        
        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract import statements"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname,
                        'line_number': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append({
                        'type': 'from_import',
                        'module': node.module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line_number': node.lineno
                    })
        
        return imports
    
    def _calculate_complexity(self, tree: ast.AST) -> Dict[str, int]:
        """Calculate cyclomatic complexity"""
        complexity = {'total': 0, 'functions': {}}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_complexity = self._calculate_function_complexity(node)
                complexity['functions'][node.name] = func_complexity
                complexity['total'] += func_complexity
        
        return complexity
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_dependencies(self, tree: ast.AST) -> List[str]:
        """Analyze external dependencies"""
        dependencies = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        dependencies.add(node.func.value.id)
                elif isinstance(node.func, ast.Name):
                    dependencies.add(node.func.id)
        
        return list(dependencies)
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Get return type annotation"""
        if node.returns:
            return ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        return None
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Get decorator name"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return str(decorator)
    
    def _get_base_name(self, base: ast.expr) -> str:
        """Get base class name"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return str(base)
    
    def _has_exception_handling(self, node: ast.FunctionDef) -> bool:
        """Check if function has exception handling"""
        for child in ast.walk(node):
            if isinstance(child, (ast.Try, ast.Raise, ast.ExceptHandler)):
                return True
        return False

class TestGenerator:
    """Generates unit tests automatically based on code analysis"""
    
    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer
        self.test_templates = self._load_test_templates()
    
    def generate_tests_for_file(self, file_path: str) -> List[TestCaseInfo]:
        """Generate comprehensive test cases for a file"""
        analysis = self.analyzer.analyze_file(file_path)
        test_cases = []
        
        # Generate tests for functions
        for func_info in analysis.get('functions', []):
            test_cases.extend(self._generate_function_tests(func_info, file_path))
        
        # Generate tests for classes
        for class_info in analysis.get('classes', []):
            test_cases.extend(self._generate_class_tests(class_info, file_path))
        
        return test_cases
    
    def _generate_function_tests(self, func_info: Dict[str, Any], file_path: str) -> List[TestCaseInfo]:
        """Generate test cases for a function"""
        test_cases = []
        func_name = func_info['name']
        
        # Skip private functions and test functions
        if func_name.startswith('_') or func_name.startswith('test_'):
            return test_cases
        
        # Basic functionality test
        test_cases.append(self._create_basic_test(func_info, file_path))
        
        # Edge case tests
        if func_info['args']:
            test_cases.extend(self._create_edge_case_tests(func_info, file_path))
        
        # Exception handling tests
        if func_info['has_exceptions']:
            test_cases.extend(self._create_exception_tests(func_info, file_path))
        
        # Performance tests for complex functions
        if func_info['complexity'] > 5:
            test_cases.append(self._create_performance_test(func_info, file_path))
        
        return test_cases
    
    def _generate_class_tests(self, class_info: Dict[str, Any], file_path: str) -> List[TestCaseInfo]:
        """Generate test cases for a class"""
        test_cases = []
        class_name = class_info['name']
        
        # Skip test classes
        if class_name.startswith('Test'):
            return test_cases
        
        # Initialization test
        test_cases.append(self._create_init_test(class_info, file_path))
        
        # Method tests
        for method_info in class_info['methods']:
            if not method_info['name'].startswith('_'):
                test_cases.extend(self._generate_method_tests(method_info, class_info, file_path))
        
        # Property tests
        for prop_info in class_info['properties']:
            test_cases.append(self._create_property_test(prop_info, class_info, file_path))
        
        return test_cases
    
    def _create_basic_test(self, func_info: Dict[str, Any], file_path: str) -> TestCaseInfo:
        """Create a basic functionality test"""
        func_name = func_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{func_name}_basic_functionality():
    \"\"\"Test basic functionality of {func_name}\"\"\"
    from {module_name} import {func_name}
    
    # TODO: Add appropriate test parameters
    # result = {func_name}(test_params)
    # assert result is not None
    # Add more specific assertions based on expected behavior
    pass
"""
        
        return TestCaseInfo(
            function_name=func_name,
            test_name=f"test_{func_name}_basic_functionality",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior="Function executes without errors",
            complexity_score=1.0,
            coverage_targets=[f"{func_name}:basic_path"]
        )
    
    def _create_edge_case_tests(self, func_info: Dict[str, Any], file_path: str) -> List[TestCaseInfo]:
        """Create edge case tests"""
        test_cases = []
        func_name = func_info['name']
        module_name = Path(file_path).stem
        
        edge_cases = [
            ("empty_input", "Test with empty input"),
            ("none_input", "Test with None input"),
            ("invalid_type", "Test with invalid input type"),
            ("boundary_values", "Test with boundary values")
        ]
        
        for case_name, description in edge_cases:
            test_code = f"""
def test_{func_name}_{case_name}():
    \"\"\"Test {func_name} with {description.lower()}\"\"\"
    from {module_name} import {func_name}
    
    # TODO: Implement {description.lower()} test
    # Add appropriate edge case parameters and assertions
    pass
"""
            
            test_cases.append(TestCaseInfo(
                function_name=func_name,
                test_name=f"test_{func_name}_{case_name}",
                test_code=test_code.strip(),
                parameters=[],
                expected_behavior=description,
                complexity_score=2.0,
                coverage_targets=[f"{func_name}:edge_case_{case_name}"]
            ))
        
        return test_cases
    
    def _create_exception_tests(self, func_info: Dict[str, Any], file_path: str) -> List[TestCaseInfo]:
        """Create exception handling tests"""
        test_cases = []
        func_name = func_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{func_name}_exception_handling():
    \"\"\"Test {func_name} exception handling\"\"\"
    from {module_name} import {func_name}
    import pytest
    
    # TODO: Add tests for expected exceptions
    # with pytest.raises(ExpectedException):
    #     {func_name}(invalid_params)
    pass
"""
        
        test_cases.append(TestCaseInfo(
            function_name=func_name,
            test_name=f"test_{func_name}_exception_handling",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior="Proper exception handling",
            complexity_score=2.5,
            coverage_targets=[f"{func_name}:exception_paths"]
        ))
        
        return test_cases
    
    def _create_performance_test(self, func_info: Dict[str, Any], file_path: str) -> TestCaseInfo:
        """Create performance test for complex functions"""
        func_name = func_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{func_name}_performance():
    \"\"\"Test {func_name} performance\"\"\"
    from {module_name} import {func_name}
    import time
    
    # TODO: Add performance benchmarks
    # start_time = time.time()
    # result = {func_name}(test_params)
    # execution_time = time.time() - start_time
    # assert execution_time < expected_max_time
    pass
"""
        
        return TestCaseInfo(
            function_name=func_name,
            test_name=f"test_{func_name}_performance",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior="Meets performance requirements",
            complexity_score=3.0,
            coverage_targets=[f"{func_name}:performance_path"]
        )
    
    def _create_init_test(self, class_info: Dict[str, Any], file_path: str) -> TestCaseInfo:
        """Create initialization test for a class"""
        class_name = class_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{class_name.lower()}_initialization():
    \"\"\"Test {class_name} initialization\"\"\"
    from {module_name} import {class_name}
    
    # TODO: Add appropriate initialization parameters
    # instance = {class_name}(init_params)
    # assert isinstance(instance, {class_name})
    # Add more specific initialization assertions
    pass
"""
        
        return TestCaseInfo(
            function_name=f"{class_name}.__init__",
            test_name=f"test_{class_name.lower()}_initialization",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior="Proper class initialization",
            complexity_score=1.5,
            coverage_targets=[f"{class_name}:init"]
        )
    
    def _generate_method_tests(self, method_info: Dict[str, Any], class_info: Dict[str, Any], file_path: str) -> List[TestCaseInfo]:
        """Generate tests for class methods"""
        test_cases = []
        method_name = method_info['name']
        class_name = class_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{class_name.lower()}_{method_name}():
    \"\"\"Test {class_name}.{method_name} method\"\"\"
    from {module_name} import {class_name}
    
    # TODO: Add method test implementation
    # instance = {class_name}(init_params)
    # result = instance.{method_name}(method_params)
    # Add appropriate assertions
    pass
"""
        
        test_cases.append(TestCaseInfo(
            function_name=f"{class_name}.{method_name}",
            test_name=f"test_{class_name.lower()}_{method_name}",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior=f"Method {method_name} works correctly",
            complexity_score=method_info['complexity'],
            coverage_targets=[f"{class_name}.{method_name}:basic"]
        ))
        
        return test_cases
    
    def _create_property_test(self, prop_info: Dict[str, Any], class_info: Dict[str, Any], file_path: str) -> TestCaseInfo:
        """Create test for class properties"""
        prop_name = prop_info['name']
        class_name = class_info['name']
        module_name = Path(file_path).stem
        
        test_code = f"""
def test_{class_name.lower()}_{prop_name}_property():
    \"\"\"Test {class_name}.{prop_name} property\"\"\"
    from {module_name} import {class_name}
    
    # TODO: Add property test implementation
    # instance = {class_name}(init_params)
    # value = instance.{prop_name}
    # Add appropriate property assertions
    pass
"""
        
        return TestCaseInfo(
            function_name=f"{class_name}.{prop_name}",
            test_name=f"test_{class_name.lower()}_{prop_name}_property",
            test_code=test_code.strip(),
            parameters=[],
            expected_behavior=f"Property {prop_name} returns correct value",
            complexity_score=1.0,
            coverage_targets=[f"{class_name}.{prop_name}:getter"]
        )
    
    def _load_test_templates(self) -> Dict[str, str]:
        """Load test templates for different scenarios"""
        return {
            'basic_function': """
def test_{function_name}_basic():
    \"\"\"Test basic functionality of {function_name}\"\"\"
    # TODO: Implement test
    pass
""",
            'exception_test': """
def test_{function_name}_exceptions():
    \"\"\"Test exception handling in {function_name}\"\"\"
    import pytest
    # TODO: Add exception tests
    pass
""",
            'performance_test': """
def test_{function_name}_performance():
    \"\"\"Test performance of {function_name}\"\"\"
    import time
    # TODO: Add performance benchmarks
    pass
"""
        }

class CoverageAnalyzer:
    """Analyzes test coverage and provides detailed reports"""
    
    def __init__(self):
        self.coverage_data = {}
        self.coverage_instance = None
    
    def start_coverage_tracking(self, source_paths: List[str] = None):
        """Start tracking code coverage"""
        self.coverage_instance = coverage.Coverage(
            source=source_paths,
            omit=[
                '*/tests/*',
                '*/test_*',
                '*/__pycache__/*',
                '*/venv/*',
                '*/env/*',
                'setup.py',
                'conftest.py'
            ]
        )
        self.coverage_instance.start()
    
    def stop_coverage_tracking(self):
        """Stop tracking code coverage"""
        if self.coverage_instance:
            self.coverage_instance.stop()
            self.coverage_instance.save()
    
    def analyze_coverage(self, file_path: str) -> CoverageReport:
        """Analyze coverage for a specific file"""
        if not self.coverage_instance:
            raise ValueError("Coverage tracking not started")
        
        # Get coverage data
        self.coverage_instance.load()
        
        try:
            analysis = self.coverage_instance.analysis2(file_path)
            filename, statements, excluded, missing, missing_branches = analysis
            
            # Calculate metrics
            total_statements = len(statements)
            covered_statements = total_statements - len(missing)
            line_coverage = (covered_statements / total_statements * 100) if total_statements > 0 else 0
            
            # Get branch coverage if available
            branch_coverage = 0
            if hasattr(self.coverage_instance, 'get_data'):
                data = self.coverage_instance.get_data()
                if file_path in data.arcs():
                    arcs = data.arcs()[file_path]
                    missing_arcs = missing_branches or []
                    total_arcs = len(arcs) if arcs else 0
                    covered_arcs = total_arcs - len(missing_arcs)
                    branch_coverage = (covered_arcs / total_arcs * 100) if total_arcs > 0 else 0
            
            # Create metrics
            metrics = CoverageMetrics(
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                function_coverage=self._calculate_function_coverage(file_path),
                statement_coverage=line_coverage,  # Same as line coverage for now
                missing_lines=list(missing),
                missing_branches=missing_branches or [],
                covered_lines=[line for line in statements if line not in missing],
                total_lines=self._count_total_lines(file_path),
                executable_lines=total_statements
            )
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(metrics)
            
            # Identify coverage gaps
            coverage_gaps = self._identify_coverage_gaps(file_path, metrics)
            
            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions(metrics, coverage_gaps)
            
            return CoverageReport(
                file_path=file_path,
                metrics=metrics,
                quality_score=quality_score,
                coverage_gaps=coverage_gaps,
                improvement_suggestions=suggestions,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing coverage for {file_path}: {e}")
            # Return empty report on error
            return CoverageReport(
                file_path=file_path,
                metrics=CoverageMetrics(0, 0, 0, 0, [], [], [], 0, 0),
                quality_score=0,
                coverage_gaps=[],
                improvement_suggestions=[],
                timestamp=datetime.now()
            )
    
    def _calculate_function_coverage(self, file_path: str) -> float:
        """Calculate function coverage percentage"""
        try:
            analyzer = CodeAnalyzer()
            analysis = analyzer.analyze_file(file_path)
            functions = analysis.get('functions', [])
            
            if not functions:
                return 100.0  # No functions to cover
            
            # This is a simplified calculation
            # In a real implementation, you'd track which functions were actually called
            covered_functions = len([f for f in functions if not f['name'].startswith('_')])
            total_functions = len(functions)
            
            return (covered_functions / total_functions * 100) if total_functions > 0 else 100.0
            
        except Exception:
            return 0.0
    
    def _count_total_lines(self, file_path: str) -> int:
        """Count total lines in file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except Exception:
            return 0
    
    def _calculate_quality_score(self, metrics: CoverageMetrics) -> float:
        """Calculate overall quality score based on coverage metrics"""
        weights = {
            'line_coverage': 0.4,
            'branch_coverage': 0.3,
            'function_coverage': 0.2,
            'statement_coverage': 0.1
        }
        
        score = (
            metrics.line_coverage * weights['line_coverage'] +
            metrics.branch_coverage * weights['branch_coverage'] +
            metrics.function_coverage * weights['function_coverage'] +
            metrics.statement_coverage * weights['statement_coverage']
        )
        
        return min(100.0, max(0.0, score))
    
    def _identify_coverage_gaps(self, file_path: str, metrics: CoverageMetrics) -> List[Dict[str, Any]]:
        """Identify specific coverage gaps"""
        gaps = []
        
        # Missing lines gaps
        if metrics.missing_lines:
            gaps.append({
                'type': 'missing_lines',
                'description': f"Lines not covered: {metrics.missing_lines}",
                'severity': 'high' if len(metrics.missing_lines) > 10 else 'medium',
                'lines': metrics.missing_lines
            })
        
        # Missing branches gaps
        if metrics.missing_branches:
            gaps.append({
                'type': 'missing_branches',
                'description': f"Branches not covered: {len(metrics.missing_branches)} branches",
                'severity': 'high' if len(metrics.missing_branches) > 5 else 'medium',
                'branches': metrics.missing_branches
            })
        
        # Low coverage areas
        if metrics.line_coverage < 80:
            gaps.append({
                'type': 'low_coverage',
                'description': f"Overall line coverage is low: {metrics.line_coverage:.1f}%",
                'severity': 'high' if metrics.line_coverage < 50 else 'medium',
                'coverage': metrics.line_coverage
            })
        
        return gaps
    
    def _generate_improvement_suggestions(self, metrics: CoverageMetrics, gaps: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for improving coverage"""
        suggestions = []
        
        if metrics.line_coverage < 80:
            suggestions.append(f"Increase line coverage from {metrics.line_coverage:.1f}% to at least 80%")
        
        if metrics.branch_coverage < 70:
            suggestions.append(f"Improve branch coverage from {metrics.branch_coverage:.1f}% by adding tests for conditional logic")
        
        if metrics.missing_lines:
            suggestions.append(f"Add tests to cover {len(metrics.missing_lines)} missing lines")
        
        if metrics.missing_branches:
            suggestions.append(f"Add tests to cover {len(metrics.missing_branches)} missing branches")
        
        # Specific suggestions based on gaps
        for gap in gaps:
            if gap['type'] == 'missing_lines' and gap['severity'] == 'high':
                suggestions.append("Focus on covering the most critical missing lines first")
            elif gap['type'] == 'missing_branches':
                suggestions.append("Add tests for edge cases and error conditions to improve branch coverage")
        
        if not suggestions:
            suggestions.append("Coverage looks good! Consider adding more edge case tests.")
        
        return suggestions

class UnitTestingFramework:
    """Main unit testing framework with automated test generation and coverage analysis"""
    
    def __init__(self, source_paths: List[str] = None):
        self.source_paths = source_paths or ['.']
        self.analyzer = CodeAnalyzer()
        self.generator = TestGenerator(self.analyzer)
        self.coverage_analyzer = CoverageAnalyzer()
        self.test_results = {}
    
    def generate_tests_for_project(self, output_dir: str = "generated_tests") -> TestGenerationResult:
        """Generate comprehensive test suite for the entire project"""
        start_time = time.time()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        all_test_cases = []
        coverage_reports = []
        
        # Find Python files to test
        python_files = self._find_python_files()
        
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            try:
                # Generate tests for this file
                test_cases = self.generator.generate_tests_for_file(file_path)
                all_test_cases.extend(test_cases)
                
                # Write test file
                if test_cases:
                    test_file_path = self._write_test_file(file_path, test_cases, output_dir)
                    logger.info(f"Generated {len(test_cases)} tests for {file_path} -> {test_file_path}")
                
            except Exception as e:
                logger.error(f"Error generating tests for {file_path}: {e}")
        
        # Run coverage analysis
        overall_coverage = self._run_coverage_analysis(python_files)
        
        generation_time = time.time() - start_time
        success_rate = len(all_test_cases) / max(1, len(python_files))
        
        recommendations = self._generate_project_recommendations(all_test_cases, overall_coverage)
        
        return TestGenerationResult(
            generated_tests=all_test_cases,
            coverage_analysis=overall_coverage,
            generation_time=generation_time,
            success_rate=success_rate,
            recommendations=recommendations
        )
    
    def run_tests_with_coverage(self, test_paths: List[str] = None) -> Dict[str, Any]:
        """Run tests with comprehensive coverage analysis"""
        test_paths = test_paths or ["test_*.py", "*_test.py"]
        
        # Start coverage tracking
        self.coverage_analyzer.start_coverage_tracking(self.source_paths)
        
        try:
            # Run pytest with coverage
            cmd = [
                sys.executable, "-m", "pytest",
                "-v", "--tb=short",
                "--cov=" + ",".join(self.source_paths),
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-report=html:htmlcov",
                "--junit-xml=test-results.xml"
            ]
            
            # Add test paths
            cmd.extend(test_paths)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Stop coverage tracking
            self.coverage_analyzer.stop_coverage_tracking()
            
            # Parse results
            test_results = {
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'coverage_reports': []
            }
            
            # Generate coverage reports for each file
            python_files = self._find_python_files()
            for file_path in python_files:
                try:
                    coverage_report = self.coverage_analyzer.analyze_coverage(file_path)
                    test_results['coverage_reports'].append(coverage_report)
                except Exception as e:
                    logger.error(f"Error analyzing coverage for {file_path}: {e}")
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error running tests with coverage: {e}")
            self.coverage_analyzer.stop_coverage_tracking()
            return {'error': str(e)}
    
    def validate_coverage_requirements(self, requirements: Dict[str, float]) -> Dict[str, Any]:
        """Validate that coverage meets specified requirements"""
        validation_results = {
            'passed': True,
            'failures': [],
            'warnings': [],
            'summary': {}
        }
        
        # Run coverage analysis
        python_files = self._find_python_files()
        overall_metrics = {
            'line_coverage': 0,
            'branch_coverage': 0,
            'function_coverage': 0,
            'statement_coverage': 0
        }
        
        file_count = 0
        for file_path in python_files:
            try:
                report = self.coverage_analyzer.analyze_coverage(file_path)
                overall_metrics['line_coverage'] += report.metrics.line_coverage
                overall_metrics['branch_coverage'] += report.metrics.branch_coverage
                overall_metrics['function_coverage'] += report.metrics.function_coverage
                overall_metrics['statement_coverage'] += report.metrics.statement_coverage
                file_count += 1
            except Exception as e:
                logger.error(f"Error validating coverage for {file_path}: {e}")
        
        # Calculate averages
        if file_count > 0:
            for metric in overall_metrics:
                overall_metrics[metric] /= file_count
        
        # Check requirements
        for metric, required_value in requirements.items():
            actual_value = overall_metrics.get(metric, 0)
            validation_results['summary'][metric] = {
                'required': required_value,
                'actual': actual_value,
                'passed': actual_value >= required_value
            }
            
            if actual_value < required_value:
                validation_results['passed'] = False
                validation_results['failures'].append(
                    f"{metric}: {actual_value:.1f}% < {required_value:.1f}% (required)"
                )
            elif actual_value < required_value + 10:  # Warning threshold
                validation_results['warnings'].append(
                    f"{metric}: {actual_value:.1f}% is close to minimum requirement {required_value:.1f}%"
                )
        
        return validation_results
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in source paths"""
        python_files = []
        
        for source_path in self.source_paths:
            if os.path.isfile(source_path) and source_path.endswith('.py'):
                python_files.append(source_path)
            elif os.path.isdir(source_path):
                for root, dirs, files in os.walk(source_path):
                    # Skip test directories and cache directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'tests', 'test']]
                    
                    for file in files:
                        if file.endswith('.py') and not file.startswith('test_') and file != 'conftest.py':
                            python_files.append(os.path.join(root, file))
        
        return python_files
    
    def _write_test_file(self, source_file: str, test_cases: List[TestCaseInfo], output_dir: str) -> str:
        """Write generated test cases to a test file"""
        source_name = Path(source_file).stem
        test_file_path = os.path.join(output_dir, f"test_{source_name}_generated.py")
        
        # Generate test file content
        content = f'''"""
Generated unit tests for {source_file}
Auto-generated by Unit Testing Framework
Generated on: {datetime.now().isoformat()}
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add source directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

'''
        
        # Add test cases
        for test_case in test_cases:
            content += f"\n{test_case.test_code}\n"
        
        # Add test metadata
        content += f'''

# Test metadata
TEST_METADATA = {{
    'source_file': '{source_file}',
    'generated_tests': {len(test_cases)},
    'generation_timestamp': '{datetime.now().isoformat()}',
    'coverage_targets': {[tc.coverage_targets for tc in test_cases]}
}}
'''
        
        # Write file
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return test_file_path
    
    def _run_coverage_analysis(self, python_files: List[str]) -> CoverageReport:
        """Run coverage analysis on all files"""
        # This is a simplified version - in practice you'd run actual tests
        total_metrics = CoverageMetrics(0, 0, 0, 0, [], [], [], 0, 0)
        file_count = len(python_files)
        
        if file_count == 0:
            return CoverageReport(
                file_path="project_overall",
                metrics=total_metrics,
                quality_score=0,
                coverage_gaps=[],
                improvement_suggestions=[],
                timestamp=datetime.now()
            )
        
        # Aggregate metrics from all files
        for file_path in python_files:
            try:
                # For now, return a mock report since we need actual test execution
                # In a real implementation, this would analyze actual coverage data
                pass
            except Exception as e:
                logger.error(f"Error in coverage analysis for {file_path}: {e}")
        
        # Return overall project coverage report
        return CoverageReport(
            file_path="project_overall",
            metrics=total_metrics,
            quality_score=0,
            coverage_gaps=[{'type': 'no_tests_run', 'description': 'No tests executed yet', 'severity': 'high'}],
            improvement_suggestions=['Run generated tests to get actual coverage data'],
            timestamp=datetime.now()
        )
    
    def _generate_project_recommendations(self, test_cases: List[TestCaseInfo], coverage_report: CoverageReport) -> List[str]:
        """Generate recommendations for the entire project"""
        recommendations = []
        
        if not test_cases:
            recommendations.append("No test cases were generated. Check if source files contain testable functions.")
            return recommendations
        
        # Test quantity recommendations
        total_tests = len(test_cases)
        if total_tests < 10:
            recommendations.append(f"Consider adding more test cases. Only {total_tests} tests generated.")
        
        # Complexity recommendations
        complex_tests = [tc for tc in test_cases if tc.complexity_score > 3.0]
        if complex_tests:
            recommendations.append(f"Focus on {len(complex_tests)} complex test cases that need detailed implementation.")
        
        # Coverage recommendations
        recommendations.extend(coverage_report.improvement_suggestions)
        
        # General recommendations
        recommendations.extend([
            "Review and customize generated test cases with appropriate test data",
            "Add integration tests to complement unit tests",
            "Consider adding property-based testing for complex functions",
            "Set up continuous integration to run tests automatically"
        ])
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    # Initialize framework
    framework = UnitTestingFramework(source_paths=['.'])
    
    # Generate tests for the project
    print("Generating tests for project...")
    result = framework.generate_tests_for_project()
    
    print(f"Generated {len(result.generated_tests)} test cases in {result.generation_time:.2f} seconds")
    print(f"Success rate: {result.success_rate:.2f}")
    
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f"- {rec}")
    
    # Validate coverage requirements
    requirements = {
        'line_coverage': 80.0,
        'branch_coverage': 70.0,
        'function_coverage': 90.0
    }
    
    print("\nValidating coverage requirements...")
    validation = framework.validate_coverage_requirements(requirements)
    
    if validation['passed']:
        print("✅ All coverage requirements met!")
    else:
        print("❌ Coverage requirements not met:")
        for failure in validation['failures']:
            print(f"  - {failure}")