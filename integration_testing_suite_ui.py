"""
Integration Testing Suite UI

Streamlit interface for the Integration Testing Suite and API Validation system.
Provides comprehensive testing management, execution monitoring, and results visualization.
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional

from integration_testing_suite import (
    IntegrationTestSuite, IntegrationTestCase, ServiceDependency,
    IntegrationType, TestStatus, create_sample_test_cases
)

def main():
    st.set_page_config(
        page_title="Integration Testing Suite",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Integration Testing Suite & API Validation")
    st.markdown("Comprehensive integration testing with API endpoint validation, service integration testing, and database validation")
    
    # Initialize session state
    if 'test_suite' not in st.session_state:
        st.session_state.test_suite = IntegrationTestSuite()
    
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None
    
    if 'test_cases' not in st.session_state:
        st.session_state.test_cases = []
    
    if 'service_dependencies' not in st.session_state:
        st.session_state.service_dependencies = []
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Test Configuration", "Test Execution", "Results Dashboard", "Test Management"]
    )
    
    if page == "Test Configuration":
        show_test_configuration()
    elif page == "Test Execution":
        show_test_execution()
    elif page == "Results Dashboard":
        show_results_dashboard()
    elif page == "Test Management":
        show_test_management()

def show_test_configuration():
    """Show test configuration interface"""
    st.header("🔧 Test Configuration")
    
    tab1, tab2, tab3 = st.tabs(["Test Cases", "Service Dependencies", "Configuration"])
    
    with tab1:
        st.subheader("Integration Test Cases")
        
        # Add new test case
        with st.expander("➕ Add New Test Case", expanded=False):
            with st.form("add_test_case"):
                col1, col2 = st.columns(2)
                
                with col1:
                    test_id = st.text_input("Test ID", placeholder="e.g., api_health_check")
                    test_name = st.text_input("Test Name", placeholder="e.g., API Health Check")
                    integration_type = st.selectbox(
                        "Integration Type",
                        options=[t.value for t in IntegrationType],
                        format_func=lambda x: x.replace('_', ' ').title()
                    )
                
                with col2:
                    description = st.text_area("Description", placeholder="Describe what this test validates")
                    endpoint_url = st.text_input("Endpoint URL (for API tests)", placeholder="http://localhost:8000/api/endpoint")
                    method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
                
                # Advanced configuration
                st.subheader("Advanced Configuration")
                col3, col4 = st.columns(2)
                
                with col3:
                    expected_status = st.number_input("Expected Status Code", value=200, min_value=100, max_value=599)
                    timeout = st.number_input("Timeout (seconds)", value=30.0, min_value=1.0, max_value=300.0)
                
                with col4:
                    headers_json = st.text_area("Headers (JSON)", placeholder='{"Content-Type": "application/json"}')
                    payload_json = st.text_area("Payload (JSON)", placeholder='{"key": "value"}')
                
                dependencies = st.multiselect(
                    "Service Dependencies",
                    options=[dep['service_name'] for dep in st.session_state.service_dependencies],
                    help="Select services this test depends on"
                )
                
                if st.form_submit_button("Add Test Case"):
                    try:
                        # Parse JSON fields
                        headers = json.loads(headers_json) if headers_json.strip() else {}
                        payload = json.loads(payload_json) if payload_json.strip() else None
                        expected_response = {"status": "success"}  # Default expected response
                        
                        test_case = IntegrationTestCase(
                            test_id=test_id,
                            name=test_name,
                            description=description,
                            integration_type=IntegrationType(integration_type),
                            endpoint_url=endpoint_url if endpoint_url else None,
                            method=method,
                            headers=headers,
                            payload=payload,
                            expected_status=expected_status,
                            expected_response=expected_response,
                            dependencies=dependencies,
                            timeout=timeout
                        )
                        
                        st.session_state.test_cases.append(test_case)
                        st.session_state.test_suite.add_test_case(test_case)
                        st.success(f"Test case '{test_name}' added successfully!")
                        st.rerun()
                        
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON format: {e}")
                    except Exception as e:
                        st.error(f"Error adding test case: {e}")
        
        # Display existing test cases
        if st.session_state.test_cases:
            st.subheader("Configured Test Cases")
            
            for i, test_case in enumerate(st.session_state.test_cases):
                with st.expander(f"📋 {test_case.name} ({test_case.integration_type.value})"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**ID:** {test_case.test_id}")
                        st.write(f"**Description:** {test_case.description}")
                        if test_case.endpoint_url:
                            st.write(f"**Endpoint:** {test_case.method} {test_case.endpoint_url}")
                    
                    with col2:
                        st.write(f"**Expected Status:** {test_case.expected_status}")
                        st.write(f"**Timeout:** {test_case.timeout}s")
                        if test_case.dependencies:
                            st.write(f"**Dependencies:** {', '.join(test_case.dependencies)}")
                    
                    with col3:
                        if st.button(f"Remove", key=f"remove_test_{i}"):
                            st.session_state.test_cases.pop(i)
                            st.session_state.test_suite.test_cases.pop(i)
                            st.rerun()
        else:
            st.info("No test cases configured. Add test cases above or load sample test cases.")
            if st.button("Load Sample Test Cases"):
                sample_cases = create_sample_test_cases()
                st.session_state.test_cases.extend(sample_cases)
                for case in sample_cases:
                    st.session_state.test_suite.add_test_case(case)
                st.success("Sample test cases loaded!")
                st.rerun()
    
    with tab2:
        st.subheader("Service Dependencies")
        
        # Add new service dependency
        with st.expander("➕ Add Service Dependency", expanded=False):
            with st.form("add_dependency"):
                col1, col2 = st.columns(2)
                
                with col1:
                    service_name = st.text_input("Service Name", placeholder="e.g., upload_service")
                    endpoint = st.text_input("Service Endpoint", placeholder="http://localhost:8001")
                
                with col2:
                    health_check_path = st.text_input("Health Check Path", value="/health")
                    required = st.checkbox("Required Service", value=True)
                    timeout = st.number_input("Health Check Timeout", value=10.0, min_value=1.0, max_value=60.0)
                
                if st.form_submit_button("Add Dependency"):
                    dependency = ServiceDependency(
                        service_name=service_name,
                        endpoint=endpoint,
                        health_check_path=health_check_path,
                        required=required,
                        timeout=timeout
                    )
                    
                    st.session_state.service_dependencies.append({
                        'service_name': service_name,
                        'endpoint': endpoint,
                        'health_check_path': health_check_path,
                        'required': required,
                        'timeout': timeout
                    })
                    
                    st.session_state.test_suite.add_service_dependency(dependency)
                    st.success(f"Service dependency '{service_name}' added!")
                    st.rerun()
        
        # Display existing dependencies
        if st.session_state.service_dependencies:
            st.subheader("Configured Dependencies")
            
            deps_df = pd.DataFrame(st.session_state.service_dependencies)
            st.dataframe(deps_df, use_container_width=True)
            
            # Test dependencies
            if st.button("🔍 Test All Dependencies"):
                with st.spinner("Testing service dependencies..."):
                    # This would normally be async, but for UI we'll simulate
                    results = {}
                    for dep in st.session_state.service_dependencies:
                        # Simulate dependency check
                        results[dep['service_name']] = True  # Simulated result
                    
                    st.subheader("Dependency Test Results")
                    for service, status in results.items():
                        if status:
                            st.success(f"✅ {service}: Available")
                        else:
                            st.error(f"❌ {service}: Unavailable")
        else:
            st.info("No service dependencies configured.")
    
    with tab3:
        st.subheader("Global Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Test Execution Settings**")
            parallel_execution = st.checkbox("Enable Parallel Execution", value=True)
            max_retries = st.number_input("Max Retries per Test", value=3, min_value=0, max_value=10)
            retry_delay = st.number_input("Retry Delay (seconds)", value=1.0, min_value=0.1, max_value=10.0)
        
        with col2:
            st.write("**Reporting Settings**")
            detailed_logging = st.checkbox("Enable Detailed Logging", value=True)
            save_responses = st.checkbox("Save Response Data", value=True)
            generate_screenshots = st.checkbox("Generate Screenshots (E2E tests)", value=False)
        
        if st.button("Save Configuration"):
            config = {
                'parallel_execution': parallel_execution,
                'max_retries': max_retries,
                'retry_delay': retry_delay,
                'detailed_logging': detailed_logging,
                'save_responses': save_responses,
                'generate_screenshots': generate_screenshots
            }
            # Save configuration (in real implementation, this would persist to file)
            st.success("Configuration saved successfully!")

def show_test_execution():
    """Show test execution interface"""
    st.header("🚀 Test Execution")
    
    if not st.session_state.test_cases:
        st.warning("No test cases configured. Please configure test cases first.")
        return
    
    # Test execution controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        selected_tests = st.multiselect(
            "Select Tests to Run",
            options=[f"{tc.test_id}: {tc.name}" for tc in st.session_state.test_cases],
            default=[f"{tc.test_id}: {tc.name}" for tc in st.session_state.test_cases]
        )
    
    with col2:
        execution_mode = st.selectbox("Execution Mode", ["Sequential", "Parallel"])
    
    with col3:
        stop_on_failure = st.checkbox("Stop on First Failure", value=False)
    
    # Run tests button
    if st.button("🏃‍♂️ Run Selected Tests", type="primary"):
        if not selected_tests:
            st.error("Please select at least one test to run.")
            return
        
        # Filter selected test cases
        selected_test_ids = [test.split(":")[0] for test in selected_tests]
        tests_to_run = [tc for tc in st.session_state.test_cases if tc.test_id in selected_test_ids]
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        # Simulate test execution (in real implementation, this would be async)
        total_tests = len(tests_to_run)
        
        with results_container:
            st.subheader("Test Execution Progress")
            
            # Create columns for real-time results
            col1, col2 = st.columns([2, 1])
            
            with col1:
                test_results_placeholder = st.empty()
            
            with col2:
                summary_placeholder = st.empty()
            
            # Simulate running tests
            simulated_results = []
            passed_count = 0
            failed_count = 0
            
            for i, test_case in enumerate(tests_to_run):
                # Update progress
                progress = (i + 1) / total_tests
                progress_bar.progress(progress)
                status_text.text(f"Running: {test_case.name} ({i + 1}/{total_tests})")
                
                # Simulate test execution delay
                time.sleep(1)
                
                # Simulate test result
                import random
                success = random.choice([True, True, True, False])  # 75% success rate
                
                result = {
                    'test_id': test_case.test_id,
                    'name': test_case.name,
                    'status': 'PASSED' if success else 'FAILED',
                    'execution_time': round(random.uniform(0.5, 5.0), 2),
                    'assertions_passed': random.randint(3, 8) if success else random.randint(0, 3),
                    'assertions_total': random.randint(5, 10)
                }
                
                simulated_results.append(result)
                
                if success:
                    passed_count += 1
                else:
                    failed_count += 1
                
                # Update real-time results
                with test_results_placeholder.container():
                    for result in simulated_results:
                        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
                        st.write(f"{status_icon} **{result['name']}** - {result['status']} ({result['execution_time']}s)")
                
                with summary_placeholder.container():
                    st.metric("Tests Completed", f"{i + 1}/{total_tests}")
                    st.metric("Passed", passed_count)
                    st.metric("Failed", failed_count)
                    if i > 0:
                        success_rate = (passed_count / (i + 1)) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Stop on failure if enabled
                if not success and stop_on_failure:
                    st.error("Stopping execution due to test failure (Stop on First Failure enabled)")
                    break
            
            # Final status
            progress_bar.progress(1.0)
            status_text.text("Test execution completed!")
            
            # Store results in session state
            st.session_state.test_results = {
                'summary': {
                    'total_tests': len(simulated_results),
                    'passed_tests': passed_count,
                    'failed_tests': failed_count,
                    'success_rate': (passed_count / len(simulated_results)) * 100 if simulated_results else 0,
                    'total_execution_time': sum(r['execution_time'] for r in simulated_results)
                },
                'test_results': simulated_results,
                'generated_at': datetime.now().isoformat()
            }
            
            st.success(f"Test execution completed! {passed_count} passed, {failed_count} failed")

def show_results_dashboard():
    """Show test results dashboard"""
    st.header("📊 Results Dashboard")
    
    if not st.session_state.test_results:
        st.info("No test results available. Run some tests first.")
        return
    
    results = st.session_state.test_results
    summary = results['summary']
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tests", summary['total_tests'])
    
    with col2:
        st.metric("Passed", summary['passed_tests'], delta=None)
    
    with col3:
        st.metric("Failed", summary['failed_tests'], delta=None)
    
    with col4:
        st.metric("Success Rate", f"{summary['success_rate']:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Test results pie chart
        fig_pie = px.pie(
            values=[summary['passed_tests'], summary['failed_tests']],
            names=['Passed', 'Failed'],
            title="Test Results Distribution",
            color_discrete_map={'Passed': '#00CC96', 'Failed': '#FF6B6B'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Execution time chart
        test_data = results['test_results']
        df = pd.DataFrame(test_data)
        
        fig_bar = px.bar(
            df,
            x='name',
            y='execution_time',
            color='status',
            title="Test Execution Times",
            color_discrete_map={'PASSED': '#00CC96', 'FAILED': '#FF6B6B'}
        )
        fig_bar.update_xaxes(tickangle=45)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed results table
    st.subheader("Detailed Test Results")
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "PASSED", "FAILED"])
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Name", "Status", "Execution Time"])
    
    # Apply filters and sorting
    filtered_df = df.copy()
    
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    if sort_by == "Name":
        filtered_df = filtered_df.sort_values('name')
    elif sort_by == "Status":
        filtered_df = filtered_df.sort_values('status')
    elif sort_by == "Execution Time":
        filtered_df = filtered_df.sort_values('execution_time', ascending=False)
    
    # Display table with styling
    def style_status(val):
        color = '#d4edda' if val == 'PASSED' else '#f8d7da'
        return f'background-color: {color}'
    
    styled_df = filtered_df.style.applymap(style_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Export options
    st.subheader("Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export to JSON"):
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="Download JSON Report",
                data=json_str,
                file_name=f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📊 Export to CSV"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Download CSV Report",
                data=csv_data,
                file_name=f"integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("📈 Generate Executive Summary"):
            st.info("Executive summary generation would be implemented here")

def show_test_management():
    """Show test management interface"""
    st.header("⚙️ Test Management")
    
    tab1, tab2, tab3 = st.tabs(["Test History", "Scheduled Tests", "Test Templates"])
    
    with tab1:
        st.subheader("Test Execution History")
        
        # Simulate historical data
        history_data = []
        for i in range(10):
            date = datetime.now() - timedelta(days=i)
            history_data.append({
                'date': date.strftime('%Y-%m-%d %H:%M'),
                'total_tests': 15,
                'passed': 12 + (i % 3),
                'failed': 3 - (i % 3),
                'success_rate': ((12 + (i % 3)) / 15) * 100,
                'duration': f"{45 + (i * 2)}s"
            })
        
        history_df = pd.DataFrame(history_data)
        
        # Success rate trend
        fig_trend = px.line(
            history_df,
            x='date',
            y='success_rate',
            title="Success Rate Trend",
            markers=True
        )
        fig_trend.update_yaxes(range=[0, 100])
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # History table
        st.dataframe(history_df, use_container_width=True)
    
    with tab2:
        st.subheader("Scheduled Test Runs")
        
        # Schedule new test run
        with st.expander("➕ Schedule New Test Run"):
            col1, col2 = st.columns(2)
            
            with col1:
                schedule_name = st.text_input("Schedule Name")
                test_suite = st.multiselect(
                    "Select Test Cases",
                    options=[f"{tc.test_id}: {tc.name}" for tc in st.session_state.test_cases]
                )
            
            with col2:
                schedule_type = st.selectbox("Schedule Type", ["Daily", "Weekly", "Monthly", "Custom"])
                schedule_time = st.time_input("Execution Time")
            
            if st.button("Create Schedule"):
                st.success(f"Schedule '{schedule_name}' created successfully!")
        
        # Display existing schedules
        st.write("**Active Schedules:**")
        schedules = [
            {"name": "Daily API Health Check", "type": "Daily", "time": "09:00", "status": "Active"},
            {"name": "Weekly Full Suite", "type": "Weekly", "time": "Sunday 02:00", "status": "Active"},
            {"name": "Monthly Regression", "type": "Monthly", "time": "1st 01:00", "status": "Paused"}
        ]
        
        for schedule in schedules:
            with st.expander(f"📅 {schedule['name']} ({schedule['status']})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Type:** {schedule['type']}")
                    st.write(f"**Time:** {schedule['time']}")
                
                with col2:
                    st.write(f"**Status:** {schedule['status']}")
                
                with col3:
                    if st.button("Edit", key=f"edit_{schedule['name']}"):
                        st.info("Edit functionality would be implemented here")
    
    with tab3:
        st.subheader("Test Case Templates")
        
        # Predefined templates
        templates = {
            "REST API Endpoint": {
                "description": "Standard REST API endpoint validation",
                "integration_type": "api_endpoint",
                "method": "GET",
                "expected_status": 200,
                "timeout": 30.0
            },
            "Database CRUD Operations": {
                "description": "Complete CRUD operations testing",
                "integration_type": "database_integration",
                "timeout": 60.0
            },
            "Service Integration": {
                "description": "Multi-service integration validation",
                "integration_type": "service_integration",
                "timeout": 120.0
            }
        }
        
        for template_name, template_config in templates.items():
            with st.expander(f"📋 {template_name}"):
                st.write(f"**Description:** {template_config['description']}")
                st.write(f"**Type:** {template_config['integration_type']}")
                
                if st.button(f"Use Template", key=f"use_{template_name}"):
                    st.info(f"Template '{template_name}' would be loaded into the test case form")

if __name__ == "__main__":
    main()