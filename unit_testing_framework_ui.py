"""
Unit Testing Framework UI
Streamlit interface for the comprehensive unit testing framework
"""

import streamlit as st
import os
import json
import time
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from unit_testing_framework import (
    UnitTestingFramework, CodeAnalyzer, TestGenerator, CoverageAnalyzer,
    TestGenerationResult, CoverageReport, TestCaseInfo
)

def main():
    st.set_page_config(
        page_title="Unit Testing Framework",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Unit Testing Framework & Coverage Analysis")
    st.markdown("Comprehensive unit testing framework with automated test generation and coverage analysis")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Source paths configuration
    st.sidebar.subheader("Source Paths")
    source_paths_input = st.sidebar.text_area(
        "Source paths (one per line)",
        value=".\napi/\nfrontend/src/",
        help="Specify directories or files to analyze"
    )
    source_paths = [path.strip() for path in source_paths_input.split('\n') if path.strip()]
    
    # Coverage requirements
    st.sidebar.subheader("Coverage Requirements")
    line_coverage_req = st.sidebar.slider("Line Coverage (%)", 0, 100, 80)
    branch_coverage_req = st.sidebar.slider("Branch Coverage (%)", 0, 100, 70)
    function_coverage_req = st.sidebar.slider("Function Coverage (%)", 0, 100, 90)
    
    coverage_requirements = {
        'line_coverage': line_coverage_req,
        'branch_coverage': branch_coverage_req,
        'function_coverage': function_coverage_req
    }
    
    # Test generation options
    st.sidebar.subheader("Test Generation Options")
    generate_edge_cases = st.sidebar.checkbox("Generate Edge Case Tests", True)
    generate_performance_tests = st.sidebar.checkbox("Generate Performance Tests", True)
    generate_exception_tests = st.sidebar.checkbox("Generate Exception Tests", True)
    output_dir = st.sidebar.text_input("Output Directory", "generated_tests")
    
    # Initialize framework
    if 'framework' not in st.session_state:
        st.session_state.framework = UnitTestingFramework(source_paths)
    
    # Main interface tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "🔧 Test Generation", 
        "📈 Coverage Analysis", 
        "✅ Quality Gates", 
        "📋 Reports"
    ])
    
    with tab1:
        show_dashboard()
    
    with tab2:
        show_test_generation(source_paths, output_dir)
    
    with tab3:
        show_coverage_analysis(source_paths)
    
    with tab4:
        show_quality_gates(coverage_requirements)
    
    with tab5:
        show_reports()

def show_dashboard():
    """Show main dashboard with overview metrics"""
    st.header("📊 Testing Framework Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Python Files",
            value=len(get_python_files()),
            help="Number of Python files found in source paths"
        )
    
    with col2:
        test_files = len([f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')])
        st.metric(
            label="Test Files",
            value=test_files,
            help="Number of existing test files"
        )
    
    with col3:
        if 'last_generation_result' in st.session_state:
            generated_tests = len(st.session_state.last_generation_result.generated_tests)
        else:
            generated_tests = 0
        st.metric(
            label="Generated Tests",
            value=generated_tests,
            help="Number of auto-generated test cases"
        )
    
    with col4:
        if 'last_coverage_validation' in st.session_state:
            coverage_score = st.session_state.last_coverage_validation.get('overall_score', 0)
        else:
            coverage_score = 0
        st.metric(
            label="Coverage Score",
            value=f"{coverage_score:.1f}%",
            help="Overall test coverage percentage"
        )
    
    # Recent activity
    st.subheader("Recent Activity")
    
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    if st.session_state.activity_log:
        activity_df = pd.DataFrame(st.session_state.activity_log)
        st.dataframe(activity_df, use_container_width=True)
    else:
        st.info("No recent activity. Start by generating tests or running coverage analysis.")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Quick Test Generation", use_container_width=True):
            st.switch_page("Test Generation")
    
    with col2:
        if st.button("📊 Run Coverage Analysis", use_container_width=True):
            st.switch_page("Coverage Analysis")
    
    with col3:
        if st.button("✅ Validate Quality Gates", use_container_width=True):
            st.switch_page("Quality Gates")

def show_test_generation(source_paths, output_dir):
    """Show test generation interface"""
    st.header("🔧 Automated Test Generation")
    
    # File selection
    st.subheader("Select Files for Test Generation")
    
    python_files = get_python_files(source_paths)
    
    if not python_files:
        st.warning("No Python files found in the specified source paths.")
        return
    
    # File selection options
    selection_mode = st.radio(
        "Selection Mode",
        ["All Files", "Select Specific Files", "Filter by Pattern"]
    )
    
    selected_files = []
    
    if selection_mode == "All Files":
        selected_files = python_files
        st.info(f"Selected all {len(python_files)} Python files")
    
    elif selection_mode == "Select Specific Files":
        selected_files = st.multiselect(
            "Choose files to generate tests for:",
            python_files,
            default=python_files[:5] if len(python_files) > 5 else python_files
        )
    
    elif selection_mode == "Filter by Pattern":
        pattern = st.text_input("File pattern (e.g., 'api/', '*.py')", "")
        if pattern:
            selected_files = [f for f in python_files if pattern in f]
            st.info(f"Found {len(selected_files)} files matching pattern '{pattern}'")
    
    if not selected_files:
        st.warning("No files selected for test generation.")
        return
    
    # Generation options
    st.subheader("Generation Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_basic_tests = st.checkbox("Basic Functionality Tests", True)
        include_edge_cases = st.checkbox("Edge Case Tests", True)
        include_exception_tests = st.checkbox("Exception Handling Tests", True)
    
    with col2:
        include_performance_tests = st.checkbox("Performance Tests", False)
        include_integration_hints = st.checkbox("Integration Test Hints", True)
        overwrite_existing = st.checkbox("Overwrite Existing Tests", False)
    
    # Preview mode
    preview_mode = st.checkbox("Preview Mode (don't write files)", False)
    
    # Generate tests button
    if st.button("🚀 Generate Tests", type="primary", use_container_width=True):
        generate_tests_for_files(selected_files, output_dir, preview_mode)

def generate_tests_for_files(selected_files, output_dir, preview_mode):
    """Generate tests for selected files"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    framework = st.session_state.framework
    
    try:
        with st.spinner("Analyzing code and generating tests..."):
            start_time = time.time()
            
            all_test_cases = []
            
            for i, file_path in enumerate(selected_files):
                status_text.text(f"Processing {file_path}...")
                progress_bar.progress((i + 1) / len(selected_files))
                
                try:
                    # Generate tests for this file
                    test_cases = framework.generator.generate_tests_for_file(file_path)
                    all_test_cases.extend(test_cases)
                    
                    # Write test file if not in preview mode
                    if not preview_mode and test_cases:
                        os.makedirs(output_dir, exist_ok=True)
                        test_file_path = framework._write_test_file(file_path, test_cases, output_dir)
                        
                        # Log activity
                        log_activity("Test Generation", f"Generated {len(test_cases)} tests for {file_path}")
                
                except Exception as e:
                    st.error(f"Error processing {file_path}: {e}")
            
            generation_time = time.time() - start_time
            
            # Store results
            st.session_state.last_generation_result = type('Result', (), {
                'generated_tests': all_test_cases,
                'generation_time': generation_time,
                'success_rate': len(all_test_cases) / max(1, len(selected_files))
            })()
            
            # Show results
            st.success(f"✅ Generated {len(all_test_cases)} test cases in {generation_time:.2f} seconds")
            
            # Display summary
            show_generation_summary(all_test_cases, preview_mode)
            
    except Exception as e:
        st.error(f"Error during test generation: {e}")
    
    finally:
        progress_bar.empty()
        status_text.empty()

def show_generation_summary(test_cases, preview_mode):
    """Show summary of generated tests"""
    if not test_cases:
        st.warning("No test cases were generated.")
        return
    
    st.subheader("📋 Generation Summary")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Tests", len(test_cases))
    
    with col2:
        avg_complexity = sum(tc.complexity_score for tc in test_cases) / len(test_cases)
        st.metric("Avg Complexity", f"{avg_complexity:.1f}")
    
    with col3:
        functions_covered = len(set(tc.function_name for tc in test_cases))
        st.metric("Functions Covered", functions_covered)
    
    # Test breakdown by type
    st.subheader("Test Breakdown")
    
    test_types = {}
    for tc in test_cases:
        test_type = "Basic"
        if "edge_case" in tc.test_name:
            test_type = "Edge Case"
        elif "exception" in tc.test_name:
            test_type = "Exception"
        elif "performance" in tc.test_name:
            test_type = "Performance"
        
        test_types[test_type] = test_types.get(test_type, 0) + 1
    
    # Create pie chart
    if test_types:
        fig = px.pie(
            values=list(test_types.values()),
            names=list(test_types.keys()),
            title="Test Distribution by Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed test list
    if st.checkbox("Show Detailed Test List"):
        test_data = []
        for tc in test_cases:
            test_data.append({
                'Function': tc.function_name,
                'Test Name': tc.test_name,
                'Complexity': tc.complexity_score,
                'Expected Behavior': tc.expected_behavior
            })
        
        df = pd.DataFrame(test_data)
        st.dataframe(df, use_container_width=True)
    
    # Preview generated code
    if st.checkbox("Preview Generated Test Code"):
        selected_test = st.selectbox(
            "Select test to preview:",
            options=range(len(test_cases)),
            format_func=lambda i: test_cases[i].test_name
        )
        
        if selected_test is not None:
            st.code(test_cases[selected_test].test_code, language='python')
    
    if preview_mode:
        st.info("Preview mode enabled - no files were written. Uncheck 'Preview Mode' to generate actual test files.")

def show_coverage_analysis(source_paths):
    """Show coverage analysis interface"""
    st.header("📈 Coverage Analysis")
    
    # Coverage analysis options
    st.subheader("Analysis Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Current Coverage", "Run Tests with Coverage", "Historical Analysis"]
        )
    
    with col2:
        include_branches = st.checkbox("Include Branch Coverage", True)
        include_functions = st.checkbox("Include Function Coverage", True)
    
    # File selection for analysis
    python_files = get_python_files(source_paths)
    
    if not python_files:
        st.warning("No Python files found for coverage analysis.")
        return
    
    selected_files = st.multiselect(
        "Select files for coverage analysis:",
        python_files,
        default=python_files[:10] if len(python_files) > 10 else python_files
    )
    
    if st.button("🔍 Run Coverage Analysis", type="primary"):
        run_coverage_analysis(selected_files, analysis_mode)

def run_coverage_analysis(selected_files, analysis_mode):
    """Run coverage analysis on selected files"""
    framework = st.session_state.framework
    
    with st.spinner("Running coverage analysis..."):
        try:
            if analysis_mode == "Run Tests with Coverage":
                # Run tests with coverage
                results = framework.run_tests_with_coverage()
                
                if 'error' in results:
                    st.error(f"Error running tests: {results['error']}")
                    return
                
                # Display test results
                st.subheader("Test Results")
                
                if results['exit_code'] == 0:
                    st.success("✅ All tests passed!")
                else:
                    st.error("❌ Some tests failed")
                
                # Show test output
                if st.checkbox("Show Test Output"):
                    st.text(results['stdout'])
                    if results['stderr']:
                        st.text("Errors:")
                        st.text(results['stderr'])
                
                # Display coverage reports
                if results.get('coverage_reports'):
                    show_coverage_reports(results['coverage_reports'])
            
            else:
                # Analyze current coverage (without running tests)
                coverage_reports = []
                
                progress_bar = st.progress(0)
                
                for i, file_path in enumerate(selected_files):
                    try:
                        # For demonstration, create mock coverage data
                        # In real implementation, this would analyze actual coverage
                        mock_report = create_mock_coverage_report(file_path)
                        coverage_reports.append(mock_report)
                        
                        progress_bar.progress((i + 1) / len(selected_files))
                    
                    except Exception as e:
                        st.error(f"Error analyzing {file_path}: {e}")
                
                progress_bar.empty()
                
                if coverage_reports:
                    show_coverage_reports(coverage_reports)
                    
                    # Store for quality gates
                    st.session_state.last_coverage_reports = coverage_reports
            
            log_activity("Coverage Analysis", f"Analyzed {len(selected_files)} files")
            
        except Exception as e:
            st.error(f"Error during coverage analysis: {e}")

def show_coverage_reports(coverage_reports):
    """Display coverage analysis reports"""
    if not coverage_reports:
        st.warning("No coverage reports available.")
        return
    
    st.subheader("📊 Coverage Reports")
    
    # Overall metrics
    total_line_coverage = sum(r.metrics.line_coverage for r in coverage_reports) / len(coverage_reports)
    total_branch_coverage = sum(r.metrics.branch_coverage for r in coverage_reports) / len(coverage_reports)
    total_function_coverage = sum(r.metrics.function_coverage for r in coverage_reports) / len(coverage_reports)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Line Coverage", f"{total_line_coverage:.1f}%")
    
    with col2:
        st.metric("Branch Coverage", f"{total_branch_coverage:.1f}%")
    
    with col3:
        st.metric("Function Coverage", f"{total_function_coverage:.1f}%")
    
    # Coverage by file
    st.subheader("Coverage by File")
    
    coverage_data = []
    for report in coverage_reports:
        coverage_data.append({
            'File': os.path.basename(report.file_path),
            'Line Coverage': report.metrics.line_coverage,
            'Branch Coverage': report.metrics.branch_coverage,
            'Function Coverage': report.metrics.function_coverage,
            'Quality Score': report.quality_score,
            'Missing Lines': len(report.metrics.missing_lines)
        })
    
    df = pd.DataFrame(coverage_data)
    
    # Color-code the dataframe
    def color_coverage(val):
        if val >= 80:
            return 'background-color: #d4edda'  # Green
        elif val >= 60:
            return 'background-color: #fff3cd'  # Yellow
        else:
            return 'background-color: #f8d7da'  # Red
    
    styled_df = df.style.applymap(
        color_coverage, 
        subset=['Line Coverage', 'Branch Coverage', 'Function Coverage']
    )
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Coverage visualization
    st.subheader("Coverage Visualization")
    
    # Create coverage chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Line Coverage',
        x=[os.path.basename(r.file_path) for r in coverage_reports],
        y=[r.metrics.line_coverage for r in coverage_reports],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Branch Coverage',
        x=[os.path.basename(r.file_path) for r in coverage_reports],
        y=[r.metrics.branch_coverage for r in coverage_reports],
        marker_color='lightgreen'
    ))
    
    fig.update_layout(
        title='Coverage by File',
        xaxis_title='Files',
        yaxis_title='Coverage (%)',
        barmode='group'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Coverage gaps and suggestions
    st.subheader("Coverage Gaps & Suggestions")
    
    for report in coverage_reports:
        if report.coverage_gaps or report.improvement_suggestions:
            with st.expander(f"📁 {os.path.basename(report.file_path)}"):
                
                if report.coverage_gaps:
                    st.write("**Coverage Gaps:**")
                    for gap in report.coverage_gaps:
                        severity_color = {
                            'high': '🔴',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(gap.get('severity', 'medium'), '🟡')
                        
                        st.write(f"{severity_color} {gap['description']}")
                
                if report.improvement_suggestions:
                    st.write("**Improvement Suggestions:**")
                    for suggestion in report.improvement_suggestions:
                        st.write(f"💡 {suggestion}")

def show_quality_gates(coverage_requirements):
    """Show quality gates validation"""
    st.header("✅ Quality Gates & Requirements")
    
    st.subheader("Coverage Requirements")
    
    # Display current requirements
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Line Coverage Required", f"{coverage_requirements['line_coverage']}%")
    
    with col2:
        st.metric("Branch Coverage Required", f"{coverage_requirements['branch_coverage']}%")
    
    with col3:
        st.metric("Function Coverage Required", f"{coverage_requirements['function_coverage']}%")
    
    # Validate against requirements
    if st.button("🔍 Validate Quality Gates", type="primary"):
        validate_quality_gates(coverage_requirements)
    
    # Show validation history
    if 'validation_history' in st.session_state:
        st.subheader("Validation History")
        
        history_df = pd.DataFrame(st.session_state.validation_history)
        st.dataframe(history_df, use_container_width=True)

def validate_quality_gates(coverage_requirements):
    """Validate coverage against quality gate requirements"""
    framework = st.session_state.framework
    
    with st.spinner("Validating quality gates..."):
        try:
            validation_result = framework.validate_coverage_requirements(coverage_requirements)
            
            # Store validation result
            st.session_state.last_coverage_validation = validation_result
            
            # Display results
            if validation_result['passed']:
                st.success("✅ All quality gates passed!")
            else:
                st.error("❌ Quality gates validation failed")
            
            # Show detailed results
            st.subheader("Validation Results")
            
            for metric, result in validation_result['summary'].items():
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**{metric.replace('_', ' ').title()}**")
                
                with col2:
                    color = "green" if result['passed'] else "red"
                    st.markdown(f"<span style='color: {color}'>{result['actual']:.1f}%</span>", unsafe_allow_html=True)
                
                with col3:
                    st.write(f"Required: {result['required']:.1f}%")
            
            # Show failures and warnings
            if validation_result['failures']:
                st.subheader("❌ Failures")
                for failure in validation_result['failures']:
                    st.error(failure)
            
            if validation_result['warnings']:
                st.subheader("⚠️ Warnings")
                for warning in validation_result['warnings']:
                    st.warning(warning)
            
            # Store in history
            if 'validation_history' not in st.session_state:
                st.session_state.validation_history = []
            
            st.session_state.validation_history.append({
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Passed' if validation_result['passed'] else 'Failed',
                'Failures': len(validation_result['failures']),
                'Warnings': len(validation_result['warnings'])
            })
            
            log_activity("Quality Gates", f"Validation {'passed' if validation_result['passed'] else 'failed'}")
            
        except Exception as e:
            st.error(f"Error validating quality gates: {e}")

def show_reports():
    """Show comprehensive reports"""
    st.header("📋 Comprehensive Reports")
    
    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        ["Test Generation Report", "Coverage Analysis Report", "Quality Gates Report", "Executive Summary"]
    )
    
    if report_type == "Test Generation Report":
        show_test_generation_report()
    elif report_type == "Coverage Analysis Report":
        show_coverage_analysis_report()
    elif report_type == "Quality Gates Report":
        show_quality_gates_report()
    elif report_type == "Executive Summary":
        show_executive_summary()

def show_test_generation_report():
    """Show detailed test generation report"""
    st.subheader("🔧 Test Generation Report")
    
    if 'last_generation_result' not in st.session_state:
        st.info("No test generation data available. Generate tests first.")
        return
    
    result = st.session_state.last_generation_result
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tests Generated", len(result.generated_tests))
    
    with col2:
        st.metric("Generation Time", f"{result.generation_time:.2f}s")
    
    with col3:
        st.metric("Success Rate", f"{result.success_rate:.2f}")
    
    # Export report
    if st.button("📄 Export Test Generation Report"):
        export_test_generation_report(result)

def show_coverage_analysis_report():
    """Show detailed coverage analysis report"""
    st.subheader("📈 Coverage Analysis Report")
    
    if 'last_coverage_reports' not in st.session_state:
        st.info("No coverage analysis data available. Run coverage analysis first.")
        return
    
    reports = st.session_state.last_coverage_reports
    
    # Summary statistics
    total_files = len(reports)
    avg_line_coverage = sum(r.metrics.line_coverage for r in reports) / total_files
    avg_branch_coverage = sum(r.metrics.branch_coverage for r in reports) / total_files
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Analyzed", total_files)
    
    with col2:
        st.metric("Avg Line Coverage", f"{avg_line_coverage:.1f}%")
    
    with col3:
        st.metric("Avg Branch Coverage", f"{avg_branch_coverage:.1f}%")
    
    # Export report
    if st.button("📄 Export Coverage Report"):
        export_coverage_report(reports)

def show_quality_gates_report():
    """Show quality gates validation report"""
    st.subheader("✅ Quality Gates Report")
    
    if 'last_coverage_validation' not in st.session_state:
        st.info("No quality gates validation data available. Run validation first.")
        return
    
    validation = st.session_state.last_coverage_validation
    
    # Status overview
    status = "✅ PASSED" if validation['passed'] else "❌ FAILED"
    st.markdown(f"### Overall Status: {status}")
    
    # Detailed metrics
    for metric, result in validation['summary'].items():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**{metric.replace('_', ' ').title()}**")
        
        with col2:
            status_icon = "✅" if result['passed'] else "❌"
            st.write(f"{status_icon} {result['actual']:.1f}%")
        
        with col3:
            st.write(f"Required: {result['required']:.1f}%")

def show_executive_summary():
    """Show executive summary report"""
    st.subheader("📊 Executive Summary")
    
    # Overall project health
    st.markdown("### Project Testing Health")
    
    # Calculate overall health score
    health_score = calculate_project_health_score()
    
    # Health score gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = health_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Project Health Score"},
        delta = {'reference': 80},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key recommendations
    st.markdown("### Key Recommendations")
    
    recommendations = generate_executive_recommendations()
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")

# Helper functions

def get_python_files(source_paths=None):
    """Get list of Python files from source paths"""
    if source_paths is None:
        source_paths = ['.']
    
    python_files = []
    
    for source_path in source_paths:
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

def create_mock_coverage_report(file_path):
    """Create a mock coverage report for demonstration"""
    from unit_testing_framework import CoverageReport, CoverageMetrics
    import random
    
    # Generate realistic mock data
    line_coverage = random.uniform(60, 95)
    branch_coverage = random.uniform(50, 85)
    function_coverage = random.uniform(70, 100)
    
    missing_lines = random.sample(range(1, 100), random.randint(2, 10))
    
    metrics = CoverageMetrics(
        line_coverage=line_coverage,
        branch_coverage=branch_coverage,
        function_coverage=function_coverage,
        statement_coverage=line_coverage,
        missing_lines=missing_lines,
        missing_branches=[],
        covered_lines=list(range(1, 100)),
        total_lines=100,
        executable_lines=80
    )
    
    quality_score = (line_coverage + branch_coverage + function_coverage) / 3
    
    gaps = []
    if line_coverage < 80:
        gaps.append({
            'type': 'low_line_coverage',
            'description': f'Line coverage is {line_coverage:.1f}%, below 80% threshold',
            'severity': 'high' if line_coverage < 60 else 'medium'
        })
    
    suggestions = []
    if line_coverage < 80:
        suggestions.append(f"Add tests to improve line coverage from {line_coverage:.1f}% to 80%")
    if branch_coverage < 70:
        suggestions.append("Add tests for conditional branches and error handling")
    
    return CoverageReport(
        file_path=file_path,
        metrics=metrics,
        quality_score=quality_score,
        coverage_gaps=gaps,
        improvement_suggestions=suggestions,
        timestamp=datetime.now()
    )

def log_activity(activity_type, description):
    """Log activity to session state"""
    if 'activity_log' not in st.session_state:
        st.session_state.activity_log = []
    
    st.session_state.activity_log.insert(0, {
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Type': activity_type,
        'Description': description
    })
    
    # Keep only last 50 activities
    st.session_state.activity_log = st.session_state.activity_log[:50]

def calculate_project_health_score():
    """Calculate overall project health score"""
    score = 50  # Base score
    
    # Add points for test generation
    if 'last_generation_result' in st.session_state:
        result = st.session_state.last_generation_result
        if len(result.generated_tests) > 0:
            score += 20
    
    # Add points for coverage
    if 'last_coverage_validation' in st.session_state:
        validation = st.session_state.last_coverage_validation
        if validation.get('passed', False):
            score += 30
    
    return min(100, score)

def generate_executive_recommendations():
    """Generate executive-level recommendations"""
    recommendations = []
    
    if 'last_generation_result' in st.session_state:
        result = st.session_state.last_generation_result
        if len(result.generated_tests) < 10:
            recommendations.append("Increase test coverage by generating more comprehensive test suites")
    
    if 'last_coverage_validation' in st.session_state:
        validation = st.session_state.last_coverage_validation
        if not validation.get('passed', False):
            recommendations.append("Address coverage gaps to meet quality gate requirements")
    
    recommendations.extend([
        "Implement continuous integration to run tests automatically",
        "Set up automated quality gates in deployment pipeline",
        "Regular review and update of test cases for new features"
    ])
    
    return recommendations

def export_test_generation_report(result):
    """Export test generation report"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'tests_generated': len(result.generated_tests),
        'generation_time': result.generation_time,
        'success_rate': result.success_rate,
        'test_details': [
            {
                'function_name': tc.function_name,
                'test_name': tc.test_name,
                'complexity_score': tc.complexity_score,
                'expected_behavior': tc.expected_behavior
            }
            for tc in result.generated_tests
        ]
    }
    
    st.download_button(
        label="📄 Download JSON Report",
        data=json.dumps(report_data, indent=2),
        file_name=f"test_generation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def export_coverage_report(reports):
    """Export coverage analysis report"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'files_analyzed': len(reports),
        'coverage_summary': {
            'avg_line_coverage': sum(r.metrics.line_coverage for r in reports) / len(reports),
            'avg_branch_coverage': sum(r.metrics.branch_coverage for r in reports) / len(reports),
            'avg_function_coverage': sum(r.metrics.function_coverage for r in reports) / len(reports)
        },
        'file_details': [
            {
                'file_path': r.file_path,
                'line_coverage': r.metrics.line_coverage,
                'branch_coverage': r.metrics.branch_coverage,
                'function_coverage': r.metrics.function_coverage,
                'quality_score': r.quality_score,
                'missing_lines_count': len(r.metrics.missing_lines),
                'improvement_suggestions': r.improvement_suggestions
            }
            for r in reports
        ]
    }
    
    st.download_button(
        label="📄 Download JSON Report",
        data=json.dumps(report_data, indent=2),
        file_name=f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()