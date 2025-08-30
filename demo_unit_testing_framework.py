#!/usr/bin/env python3
"""
Demo script for Unit Testing Framework and Coverage Analysis
Demonstrates comprehensive unit testing capabilities with automated test generation
"""

import os
import sys
import time
import json
from pathlib import Path
from unit_testing_framework import (
    UnitTestingFramework, CodeAnalyzer, TestGenerator, CoverageAnalyzer,
    TestGenerationResult, CoverageReport
)

def create_sample_code_files():
    """Create sample Python files for testing the framework"""
    print("📁 Creating sample code files for demonstration...")
    
    # Create sample directory
    sample_dir = "sample_code"
    os.makedirs(sample_dir, exist_ok=True)
    
    # Sample calculator module
    calculator_code = '''"""
Simple calculator module for demonstration
"""

class Calculator:
    """A simple calculator class"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        """Add two numbers"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract two numbers"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Divide two numbers"""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        if b == 0:
            raise ValueError("Cannot divide by zero")
        
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base, exponent):
        """Calculate power of a number"""
        if not isinstance(base, (int, float)) or not isinstance(exponent, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        result = base ** exponent
        self.history.append(f"{base} ** {exponent} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()
    
    @property
    def last_result(self):
        """Get the last calculation result"""
        if not self.history:
            return None
        
        last_calc = self.history[-1]
        return float(last_calc.split(" = ")[1])

def factorial(n):
    """Calculate factorial of a number"""
    if not isinstance(n, int):
        raise TypeError("Argument must be an integer")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result

def fibonacci(n):
    """Generate Fibonacci sequence up to n terms"""
    if not isinstance(n, int):
        raise TypeError("Argument must be an integer")
    
    if n <= 0:
        raise ValueError("Number of terms must be positive")
    
    sequence = []
    
    if n >= 1:
        sequence.append(0)
    if n >= 2:
        sequence.append(1)
    
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    
    return sequence

def is_prime(n):
    """Check if a number is prime"""
    if not isinstance(n, int):
        raise TypeError("Argument must be an integer")
    
    if n < 2:
        return False
    
    if n == 2:
        return True
    
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    
    return True
'''
    
    with open(os.path.join(sample_dir, "calculator.py"), "w") as f:
        f.write(calculator_code)
    
    # Sample string utilities module
    string_utils_code = '''"""
String utility functions for demonstration
"""

import re
from typing import List, Optional

class StringProcessor:
    """String processing utilities"""
    
    def __init__(self, case_sensitive=True):
        self.case_sensitive = case_sensitive
        self.processed_count = 0
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        # Remove extra whitespace
        cleaned = re.sub(r'\\s+', ' ', text.strip())
        
        # Handle case sensitivity
        if not self.case_sensitive:
            cleaned = cleaned.lower()
        
        self.processed_count += 1
        return cleaned
    
    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        emails = re.findall(email_pattern, text)
        
        if not self.case_sensitive:
            emails = [email.lower() for email in emails]
        
        return emails
    
    def count_words(self, text: str) -> int:
        """Count words in text"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        if not text.strip():
            return 0
        
        words = text.split()
        return len(words)
    
    def reverse_words(self, text: str) -> str:
        """Reverse the order of words in text"""
        if not isinstance(text, str):
            raise TypeError("Input must be a string")
        
        words = text.split()
        return ' '.join(reversed(words))
    
    @property
    def processing_stats(self):
        """Get processing statistics"""
        return {
            'processed_count': self.processed_count,
            'case_sensitive': self.case_sensitive
        }

def validate_password(password: str) -> dict:
    """Validate password strength"""
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    
    result = {
        'valid': True,
        'score': 0,
        'issues': []
    }
    
    # Length check
    if len(password) < 8:
        result['issues'].append("Password must be at least 8 characters long")
        result['valid'] = False
    else:
        result['score'] += 1
    
    # Uppercase check
    if not re.search(r'[A-Z]', password):
        result['issues'].append("Password must contain at least one uppercase letter")
        result['valid'] = False
    else:
        result['score'] += 1
    
    # Lowercase check
    if not re.search(r'[a-z]', password):
        result['issues'].append("Password must contain at least one lowercase letter")
        result['valid'] = False
    else:
        result['score'] += 1
    
    # Number check
    if not re.search(r'\\d', password):
        result['issues'].append("Password must contain at least one number")
        result['valid'] = False
    else:
        result['score'] += 1
    
    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['issues'].append("Password must contain at least one special character")
        result['valid'] = False
    else:
        result['score'] += 1
    
    return result

def format_phone_number(phone: str, country_code: str = "US") -> Optional[str]:
    """Format phone number based on country code"""
    if not isinstance(phone, str):
        raise TypeError("Phone number must be a string")
    
    # Remove all non-digit characters
    digits = re.sub(r'\\D', '', phone)
    
    if country_code == "US":
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            raise ValueError("Invalid US phone number format")
    
    # Add more country formats as needed
    return None
'''
    
    with open(os.path.join(sample_dir, "string_utils.py"), "w") as f:
        f.write(string_utils_code)
    
    # Sample data processor module
    data_processor_code = '''"""
Data processing utilities for demonstration
"""

import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

class DataProcessor:
    """Process and analyze data"""
    
    def __init__(self):
        self.processed_records = 0
        self.errors = []
    
    def process_json_data(self, json_string: str) -> Dict[str, Any]:
        """Process JSON data"""
        try:
            data = json.loads(json_string)
            self.processed_records += 1
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            self.errors.append(error_msg)
            raise ValueError(error_msg)
    
    def validate_record(self, record: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that record contains required fields"""
        if not isinstance(record, dict):
            raise TypeError("Record must be a dictionary")
        
        if not isinstance(required_fields, list):
            raise TypeError("Required fields must be a list")
        
        missing_fields = [field for field in required_fields if field not in record]
        
        if missing_fields:
            error_msg = f"Missing required fields: {missing_fields}"
            self.errors.append(error_msg)
            return False
        
        return True
    
    def aggregate_data(self, records: List[Dict[str, Any]], group_by: str, aggregate_field: str) -> Dict[str, float]:
        """Aggregate numeric data by grouping field"""
        if not isinstance(records, list):
            raise TypeError("Records must be a list")
        
        if not records:
            return {}
        
        aggregated = {}
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            if group_by not in record or aggregate_field not in record:
                continue
            
            group_value = record[group_by]
            numeric_value = record[aggregate_field]
            
            if not isinstance(numeric_value, (int, float)):
                continue
            
            if group_value not in aggregated:
                aggregated[group_value] = 0
            
            aggregated[group_value] += numeric_value
        
        return aggregated
    
    def filter_records(self, records: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter records based on criteria"""
        if not isinstance(records, list):
            raise TypeError("Records must be a list")
        
        if not isinstance(filters, dict):
            raise TypeError("Filters must be a dictionary")
        
        filtered = []
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            matches = True
            for field, value in filters.items():
                if field not in record or record[field] != value:
                    matches = False
                    break
            
            if matches:
                filtered.append(record)
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'processed_records': self.processed_records,
            'error_count': len(self.errors),
            'errors': self.errors.copy()
        }

def parse_csv_file(file_path: str) -> List[Dict[str, str]]:
    """Parse CSV file and return list of dictionaries"""
    if not isinstance(file_path, str):
        raise TypeError("File path must be a string")
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """Calculate basic statistics for a list of numbers"""
    if not isinstance(numbers, list):
        raise TypeError("Input must be a list")
    
    if not numbers:
        raise ValueError("List cannot be empty")
    
    # Validate all elements are numbers
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise TypeError("All elements must be numbers")
    
    stats = {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': sum(numbers) / len(numbers),
        'min': min(numbers),
        'max': max(numbers)
    }
    
    # Calculate median
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        stats['median'] = (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        stats['median'] = sorted_numbers[n//2]
    
    # Calculate variance and standard deviation
    mean = stats['mean']
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    stats['variance'] = variance
    stats['std_dev'] = variance ** 0.5
    
    return stats
'''
    
    with open(os.path.join(sample_dir, "data_processor.py"), "w") as f:
        f.write(data_processor_code)
    
    print(f"✅ Created sample code files in '{sample_dir}' directory")
    return sample_dir

def demonstrate_code_analysis():
    """Demonstrate code analysis capabilities"""
    print("\n🔍 Demonstrating Code Analysis...")
    
    analyzer = CodeAnalyzer()
    
    # Analyze sample files
    sample_files = [
        "sample_code/calculator.py",
        "sample_code/string_utils.py",
        "sample_code/data_processor.py"
    ]
    
    for file_path in sample_files:
        if os.path.exists(file_path):
            print(f"\n📄 Analyzing {file_path}:")
            
            analysis = analyzer.analyze_file(file_path)
            
            print(f"  Functions found: {len(analysis.get('functions', []))}")
            print(f"  Classes found: {len(analysis.get('classes', []))}")
            print(f"  Total complexity: {analysis.get('complexity', {}).get('total', 0)}")
            
            # Show function details
            for func in analysis.get('functions', [])[:3]:  # Show first 3 functions
                print(f"    - {func['name']}() [complexity: {func['complexity']}]")
            
            # Show class details
            for cls in analysis.get('classes', []):
                print(f"    - class {cls['name']} [{len(cls['methods'])} methods]")

def demonstrate_test_generation():
    """Demonstrate automated test generation"""
    print("\n🧪 Demonstrating Automated Test Generation...")
    
    framework = UnitTestingFramework(source_paths=["sample_code"])
    
    # Generate tests for the sample project
    print("Generating comprehensive test suite...")
    start_time = time.time()
    
    result = framework.generate_tests_for_project(output_dir="demo_generated_tests")
    
    generation_time = time.time() - start_time
    
    print(f"\n✅ Test Generation Results:")
    print(f"  Generated tests: {len(result.generated_tests)}")
    print(f"  Generation time: {result.generation_time:.2f} seconds")
    print(f"  Success rate: {result.success_rate:.2f}")
    
    # Show sample generated tests
    print(f"\n📋 Sample Generated Tests:")
    for i, test_case in enumerate(result.generated_tests[:5]):  # Show first 5
        print(f"  {i+1}. {test_case.test_name}")
        print(f"     Function: {test_case.function_name}")
        print(f"     Complexity: {test_case.complexity_score}")
        print(f"     Behavior: {test_case.expected_behavior}")
    
    if len(result.generated_tests) > 5:
        print(f"     ... and {len(result.generated_tests) - 5} more tests")
    
    # Show recommendations
    print(f"\n💡 Recommendations:")
    for rec in result.recommendations[:3]:  # Show first 3 recommendations
        print(f"  - {rec}")
    
    return result

def demonstrate_coverage_analysis():
    """Demonstrate coverage analysis"""
    print("\n📊 Demonstrating Coverage Analysis...")
    
    framework = UnitTestingFramework(source_paths=["sample_code"])
    
    # Create mock coverage analysis (since we don't have actual test execution)
    print("Analyzing code coverage...")
    
    sample_files = [
        "sample_code/calculator.py",
        "sample_code/string_utils.py",
        "sample_code/data_processor.py"
    ]
    
    coverage_reports = []
    
    for file_path in sample_files:
        if os.path.exists(file_path):
            # Create mock coverage report for demonstration
            from unit_testing_framework import CoverageMetrics, CoverageReport
            from datetime import datetime
            import random
            
            # Generate realistic mock coverage data
            line_coverage = random.uniform(65, 95)
            branch_coverage = random.uniform(55, 85)
            function_coverage = random.uniform(75, 100)
            
            metrics = CoverageMetrics(
                line_coverage=line_coverage,
                branch_coverage=branch_coverage,
                function_coverage=function_coverage,
                statement_coverage=line_coverage,
                missing_lines=random.sample(range(1, 50), random.randint(2, 8)),
                missing_branches=[],
                covered_lines=list(range(1, 50)),
                total_lines=50,
                executable_lines=40
            )
            
            quality_score = (line_coverage + branch_coverage + function_coverage) / 3
            
            gaps = []
            suggestions = []
            
            if line_coverage < 80:
                gaps.append({
                    'type': 'low_line_coverage',
                    'description': f'Line coverage {line_coverage:.1f}% below 80% threshold',
                    'severity': 'high' if line_coverage < 60 else 'medium'
                })
                suggestions.append(f"Increase line coverage from {line_coverage:.1f}% to 80%")
            
            if branch_coverage < 70:
                suggestions.append("Add tests for conditional branches and error paths")
            
            report = CoverageReport(
                file_path=file_path,
                metrics=metrics,
                quality_score=quality_score,
                coverage_gaps=gaps,
                improvement_suggestions=suggestions,
                timestamp=datetime.now()
            )
            
            coverage_reports.append(report)
    
    # Display coverage results
    print(f"\n📈 Coverage Analysis Results:")
    
    total_line_coverage = sum(r.metrics.line_coverage for r in coverage_reports) / len(coverage_reports)
    total_branch_coverage = sum(r.metrics.branch_coverage for r in coverage_reports) / len(coverage_reports)
    total_function_coverage = sum(r.metrics.function_coverage for r in coverage_reports) / len(coverage_reports)
    
    print(f"  Overall Line Coverage: {total_line_coverage:.1f}%")
    print(f"  Overall Branch Coverage: {total_branch_coverage:.1f}%")
    print(f"  Overall Function Coverage: {total_function_coverage:.1f}%")
    
    print(f"\n📋 File-by-File Coverage:")
    for report in coverage_reports:
        filename = os.path.basename(report.file_path)
        print(f"  {filename}:")
        print(f"    Line: {report.metrics.line_coverage:.1f}%")
        print(f"    Branch: {report.metrics.branch_coverage:.1f}%")
        print(f"    Quality Score: {report.quality_score:.1f}")
        
        if report.improvement_suggestions:
            print(f"    Suggestions: {report.improvement_suggestions[0]}")
    
    return coverage_reports

def demonstrate_quality_gates():
    """Demonstrate quality gates validation"""
    print("\n✅ Demonstrating Quality Gates Validation...")
    
    framework = UnitTestingFramework(source_paths=["sample_code"])
    
    # Define quality requirements
    requirements = {
        'line_coverage': 80.0,
        'branch_coverage': 70.0,
        'function_coverage': 90.0,
        'statement_coverage': 80.0
    }
    
    print(f"Quality Gate Requirements:")
    for metric, threshold in requirements.items():
        print(f"  {metric.replace('_', ' ').title()}: {threshold}%")
    
    # Validate requirements (using mock data for demonstration)
    print(f"\nValidating quality gates...")
    
    # Create mock validation result
    validation_result = {
        'passed': False,
        'failures': [],
        'warnings': [],
        'summary': {}
    }
    
    # Mock current coverage values
    current_coverage = {
        'line_coverage': 75.5,
        'branch_coverage': 65.2,
        'function_coverage': 92.1,
        'statement_coverage': 75.5
    }
    
    for metric, required_value in requirements.items():
        actual_value = current_coverage[metric]
        passed = actual_value >= required_value
        
        validation_result['summary'][metric] = {
            'required': required_value,
            'actual': actual_value,
            'passed': passed
        }
        
        if not passed:
            validation_result['failures'].append(
                f"{metric}: {actual_value:.1f}% < {required_value:.1f}% (required)"
            )
        elif actual_value < required_value + 5:  # Warning threshold
            validation_result['warnings'].append(
                f"{metric}: {actual_value:.1f}% is close to minimum {required_value:.1f}%"
            )
    
    validation_result['passed'] = len(validation_result['failures']) == 0
    
    # Display validation results
    print(f"\n🎯 Quality Gate Results:")
    
    if validation_result['passed']:
        print("  ✅ All quality gates PASSED!")
    else:
        print("  ❌ Quality gates FAILED")
    
    print(f"\n📊 Detailed Results:")
    for metric, result in validation_result['summary'].items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {metric.replace('_', ' ').title()}: {result['actual']:.1f}% / {result['required']:.1f}% {status}")
    
    if validation_result['failures']:
        print(f"\n❌ Failures:")
        for failure in validation_result['failures']:
            print(f"  - {failure}")
    
    if validation_result['warnings']:
        print(f"\n⚠️ Warnings:")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    
    return validation_result

def demonstrate_comprehensive_workflow():
    """Demonstrate the complete testing workflow"""
    print("\n🔄 Demonstrating Comprehensive Testing Workflow...")
    
    workflow_steps = [
        "1. Code Analysis & Discovery",
        "2. Automated Test Generation", 
        "3. Coverage Analysis",
        "4. Quality Gates Validation",
        "5. Report Generation"
    ]
    
    print("Workflow Steps:")
    for step in workflow_steps:
        print(f"  {step}")
    
    print(f"\nExecuting complete workflow...")
    
    # Step 1: Code Analysis
    print(f"\n📍 Step 1: Code Analysis")
    demonstrate_code_analysis()
    
    # Step 2: Test Generation
    print(f"\n📍 Step 2: Test Generation")
    generation_result = demonstrate_test_generation()
    
    # Step 3: Coverage Analysis
    print(f"\n📍 Step 3: Coverage Analysis")
    coverage_reports = demonstrate_coverage_analysis()
    
    # Step 4: Quality Gates
    print(f"\n📍 Step 4: Quality Gates Validation")
    validation_result = demonstrate_quality_gates()
    
    # Step 5: Generate Summary Report
    print(f"\n📍 Step 5: Summary Report Generation")
    
    summary_report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'workflow_completed': True,
        'test_generation': {
            'tests_generated': len(generation_result.generated_tests),
            'generation_time': generation_result.generation_time,
            'success_rate': generation_result.success_rate
        },
        'coverage_analysis': {
            'files_analyzed': len(coverage_reports),
            'avg_line_coverage': sum(r.metrics.line_coverage for r in coverage_reports) / len(coverage_reports),
            'avg_branch_coverage': sum(r.metrics.branch_coverage for r in coverage_reports) / len(coverage_reports)
        },
        'quality_gates': {
            'passed': validation_result['passed'],
            'failures': len(validation_result['failures']),
            'warnings': len(validation_result['warnings'])
        }
    }
    
    # Save report
    report_file = f"testing_workflow_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    print(f"📄 Workflow Summary Report:")
    print(f"  Tests Generated: {summary_report['test_generation']['tests_generated']}")
    print(f"  Files Analyzed: {summary_report['coverage_analysis']['files_analyzed']}")
    print(f"  Average Coverage: {summary_report['coverage_analysis']['avg_line_coverage']:.1f}%")
    print(f"  Quality Gates: {'PASSED' if summary_report['quality_gates']['passed'] else 'FAILED'}")
    print(f"  Report saved: {report_file}")
    
    return summary_report

def cleanup_demo_files():
    """Clean up demo files"""
    print("\n🧹 Cleaning up demo files...")
    
    import shutil
    
    cleanup_paths = [
        "sample_code",
        "demo_generated_tests",
        "htmlcov",
        "coverage.xml",
        "test-results.xml"
    ]
    
    for path in cleanup_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"  Removed directory: {path}")
            else:
                os.remove(path)
                print(f"  Removed file: {path}")
    
    # Remove report files
    for file in os.listdir('.'):
        if file.startswith('testing_workflow_report_') and file.endswith('.json'):
            os.remove(file)
            print(f"  Removed report: {file}")

def main():
    """Main demo function"""
    print("🧪 Unit Testing Framework & Coverage Analysis Demo")
    print("=" * 60)
    
    try:
        # Create sample code for testing
        sample_dir = create_sample_code_files()
        
        # Demonstrate individual components
        demonstrate_code_analysis()
        demonstrate_test_generation()
        demonstrate_coverage_analysis()
        demonstrate_quality_gates()
        
        # Demonstrate complete workflow
        print("\n" + "=" * 60)
        workflow_report = demonstrate_comprehensive_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✅ Automated code analysis and complexity calculation")
        print("  ✅ Intelligent test case generation with multiple test types")
        print("  ✅ Comprehensive coverage analysis with detailed metrics")
        print("  ✅ Quality gates validation with configurable thresholds")
        print("  ✅ Detailed reporting and improvement recommendations")
        print("  ✅ Complete testing workflow orchestration")
        
        print(f"\nGenerated Files:")
        print(f"  📁 Sample code: {sample_dir}/")
        print(f"  📁 Generated tests: demo_generated_tests/")
        print(f"  📄 Workflow report: testing_workflow_report_*.json")
        
        # Ask if user wants to clean up
        cleanup = input("\nClean up demo files? (y/N): ").lower().strip()
        if cleanup == 'y':
            cleanup_demo_files()
            print("✅ Cleanup completed!")
        else:
            print("📁 Demo files preserved for inspection")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n👋 Thank you for trying the Unit Testing Framework!")

if __name__ == "__main__":
    main()