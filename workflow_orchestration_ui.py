#!/usr/bin/env python3
"""
Workflow Orchestration Streamlit UI
Interactive dashboard for managing enterprise workflow orchestration
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Any, Optional
import uuid
from dataclasses import asdict
import yaml

# Import our workflow systems
from workflow_orchestration_system import WorkflowEngine, WorkflowTemplates
from enterprise_workflow_management import EnterpriseWorkflowManager, WorkflowCategory
from workflow_templates_automation import WorkflowTemplateLibrary, AutomationEngine

# Page configuration
st.set_page_config(
    page_title="Workflow Orchestration",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
.workflow-metric {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin: 0.5rem 0;
}

.workflow-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #4f46e5;
    margin: 1rem 0;
}

.status-running {
    color: #3b82f6;
    font-weight: bold;
}

.status-completed {
    color: #10b981;
    font-weight: bold;
}

.status-failed {
    color: #ef4444;
    font-weight: bold;
}

.status-paused {
    color: #f59e0b;
    font-weight: bold;
}

.execution-progress {
    background: #f3f4f6;
    border-radius: 5px;
    padding: 0.5rem;
    margin: 0.5rem 0;
}

.node-status {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    margin: 0.125rem;
}

.node-completed { background-color: #dcfce7; color: #166534; }
.node-running { background-color: #dbeafe; color: #1d4ed8; }
.node-pending { background-color: #f3f4f6; color: #6b7280; }
.node-failed { background-color: #fee2e2; color: #dc2626; }

.template-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.template-card:hover {
    border-color: #4f46e5;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.system-health-good { color: #10b981; }
.system-health-warning { color: #f59e0b; }
.system-health-critical { color: #ef4444; }

.workflow-timeline {
    position: relative;
    padding-left: 2rem;
}

.workflow-timeline::before {
    content: '';
    position: absolute;
    left: 1rem;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e5e7eb;
}

.timeline-item {
    position: relative;
    margin: 1rem 0;
    padding: 1rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.timeline-item::before {
    content: '';
    position: absolute;
    left: -1.875rem;
    top: 1.5rem;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #4f46e5;
}
</style>
""", unsafe_allow_html=True)

class WorkflowOrchestrationUI:
    """Main UI class for workflow orchestration dashboard"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
        self.enterprise_manager = EnterpriseWorkflowManager()
        self.template_library = WorkflowTemplateLibrary()
        self.automation_engine = AutomationEngine()
        
        # Initialize session state
        if 'workflows' not in st.session_state:
            st.session_state.workflows = {}
        if 'executions' not in st.session_state:
            st.session_state.executions = {}
        if 'selected_workflow' not in st.session_state:
            st.session_state.selected_workflow = None
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'system_metrics' not in st.session_state:
            st.session_state.system_metrics = self._generate_mock_metrics()

    def _generate_mock_metrics(self) -> Dict[str, Any]:
        """Generate mock system metrics for demonstration"""
        import random
        return {
            'cpu_usage': random.uniform(20, 80),
            'memory_usage': random.uniform(30, 90),
            'disk_usage': random.uniform(40, 85),
            'network_latency': random.uniform(10, 100),
            'active_workflows': random.randint(5, 25),
            'completed_executions_today': random.randint(50, 200),
            'failed_executions_today': random.randint(2, 15),
            'queue_length': random.randint(0, 20),
            'timestamp': datetime.now()
        }

    def render_sidebar(self):
        """Render the sidebar with navigation and controls"""
        st.sidebar.title("🔄 Workflow Orchestration")
        
        # Navigation
        page = st.sidebar.selectbox(
            "Navigate to",
            [
                "Dashboard Overview",
                "Workflow Management",
                "Execution Monitor",
                "Template Library",
                "System Health",
                "Automation Rules",
                "Analytics"
            ]
        )
        
        st.sidebar.divider()
        
        # Auto-refresh control
        st.session_state.auto_refresh = st.sidebar.toggle(
            "Auto Refresh", 
            value=st.session_state.auto_refresh,
            help="Automatically refresh data every 30 seconds"
        )
        
        if st.sidebar.button("🔄 Refresh Now", use_container_width=True):
            st.session_state.system_metrics = self._generate_mock_metrics()
            st.rerun()
        
        # Quick actions
        st.sidebar.subheader("Quick Actions")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("➕ New", use_container_width=True):
                st.session_state.show_new_workflow_modal = True
        with col2:
            if st.button("📊 Export", use_container_width=True):
                self._export_workflow_data()
        
        # System status indicator
        st.sidebar.subheader("System Status")
        metrics = st.session_state.system_metrics
        
        # Health indicator
        health_score = (100 - metrics['cpu_usage'] + 100 - metrics['memory_usage']) / 2
        if health_score > 70:
            status_class = "system-health-good"
            status_text = "🟢 Healthy"
        elif health_score > 50:
            status_class = "system-health-warning" 
            status_text = "🟡 Warning"
        else:
            status_class = "system-health-critical"
            status_text = "🔴 Critical"
        
        st.sidebar.markdown(
            f'<div class="{status_class}">{status_text}</div>',
            unsafe_allow_html=True
        )
        
        # Quick metrics
        st.sidebar.metric("Active Workflows", metrics['active_workflows'])
        st.sidebar.metric("Queue Length", metrics['queue_length'])
        st.sidebar.metric("Success Rate", f"{((metrics['completed_executions_today'] - metrics['failed_executions_today']) / max(metrics['completed_executions_today'], 1) * 100):.1f}%")
        
        return page

    def render_dashboard_overview(self):
        """Render the main dashboard overview"""
        st.title("🔄 Workflow Orchestration Dashboard")
        st.markdown("Monitor and manage enterprise workflow executions in real-time")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = st.session_state.system_metrics
        
        with col1:
            st.markdown("""
            <div class="workflow-metric">
                <h3>🔄 Active Workflows</h3>
                <h2>{}</h2>
                <p>Currently running</p>
            </div>
            """.format(metrics['active_workflows']), unsafe_allow_html=True)
        
        with col2:
            success_rate = (metrics['completed_executions_today'] - metrics['failed_executions_today']) / max(metrics['completed_executions_today'], 1) * 100
            st.markdown("""
            <div class="workflow-metric">
                <h3>✅ Success Rate</h3>
                <h2>{:.1f}%</h2>
                <p>Last 24 hours</p>
            </div>
            """.format(success_rate), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="workflow-metric">
                <h3>⚡ Throughput</h3>
                <h2>{}</h2>
                <p>Executions today</p>
            </div>
            """.format(metrics['completed_executions_today']), unsafe_allow_html=True)
        
        with col4:
            avg_duration = 4.2  # Mock average duration in minutes
            st.markdown("""
            <div class="workflow-metric">
                <h3>⏱️ Avg Duration</h3>
                <h2>{:.1f}min</h2>
                <p>Per execution</p>
            </div>
            """.format(avg_duration), unsafe_allow_html=True)
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Execution Trends")
            # Generate sample data for the last 7 days
            dates = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
            successful = [45, 52, 38, 61, 48, 55, metrics['completed_executions_today'] - metrics['failed_executions_today']]
            failed = [3, 5, 2, 8, 4, 6, metrics['failed_executions_today']]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=successful, name='Successful', 
                line=dict(color='#10b981'), fill='tonexty'
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=failed, name='Failed',
                line=dict(color='#ef4444'), fill='tozeroy'
            ))
            fig.update_layout(
                showlegend=True, height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis_title="Executions"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏷️ Workflow Distribution")
            categories = ['Medical', 'Quality', 'Business', 'Legal', 'Research']
            values = [35, 25, 20, 15, 5]
            
            fig = px.pie(
                values=values, names=categories,
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.4
            )
            fig.update_layout(
                showlegend=True, height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent executions
        st.subheader("🕒 Recent Executions")
        self._render_recent_executions()
        
        # System health overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💻 System Resources")
            resource_fig = go.Figure()
            
            resources = ['CPU', 'Memory', 'Disk', 'Network']
            values = [
                metrics['cpu_usage'],
                metrics['memory_usage'], 
                metrics['disk_usage'],
                metrics['network_latency']
            ]
            
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
            
            for i, (resource, value, color) in enumerate(zip(resources, values, colors)):
                resource_fig.add_trace(go.Bar(
                    x=[resource], y=[value],
                    name=resource, marker_color=color,
                    text=f'{value:.1f}%', textposition='outside'
                ))
            
            resource_fig.update_layout(
                showlegend=False, height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                yaxis=dict(range=[0, 100], title="Usage %")
            )
            st.plotly_chart(resource_fig, use_container_width=True)
        
        with col2:
            st.subheader("🔔 Active Alerts")
            alerts = [
                {"type": "warning", "message": "High memory usage on workflow-engine-02", "time": "5 min ago"},
                {"type": "info", "message": "Workflow template updated: Medical Analysis v2.1", "time": "15 min ago"},
                {"type": "success", "message": "Quality assessment pipeline optimization complete", "time": "1 hour ago"}
            ]
            
            for alert in alerts:
                alert_color = {
                    "warning": "#f59e0b",
                    "error": "#ef4444", 
                    "info": "#3b82f6",
                    "success": "#10b981"
                }.get(alert["type"], "#6b7280")
                
                st.markdown(f"""
                <div style="border-left: 4px solid {alert_color}; padding: 12px; margin: 8px 0; background: white; border-radius: 4px;">
                    <strong>{alert["message"]}</strong><br>
                    <small style="color: #6b7280;">{alert["time"]}</small>
                </div>
                """, unsafe_allow_html=True)

    def _render_recent_executions(self):
        """Render recent workflow executions"""
        # Sample execution data
        executions = [
            {
                "id": "exec_001",
                "name": "Medical Consultation Analysis",
                "status": "running",
                "progress": 73,
                "started": datetime.now() - timedelta(minutes=15),
                "duration": "15m",
                "nodes_completed": "8/12"
            },
            {
                "id": "exec_002", 
                "name": "Quality Assessment Pipeline",
                "status": "completed",
                "progress": 100,
                "started": datetime.now() - timedelta(minutes=45),
                "duration": "7m",
                "nodes_completed": "6/6"
            },
            {
                "id": "exec_003",
                "name": "Legal Document Processing",
                "status": "failed",
                "progress": 25,
                "started": datetime.now() - timedelta(hours=1),
                "duration": "3m",
                "nodes_completed": "2/8"
            },
            {
                "id": "exec_004",
                "name": "Meeting Minutes Extraction",
                "status": "paused",
                "progress": 60,
                "started": datetime.now() - timedelta(hours=2),
                "duration": "12m",
                "nodes_completed": "4/7"
            }
        ]
        
        for execution in executions:
            status_class = f"status-{execution['status']}"
            
            st.markdown(f"""
            <div class="workflow-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4>{execution['name']}</h4>
                    <span class="{status_class}">{execution['status'].upper()}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; font-size: 0.875rem;">
                    <div><strong>ID:</strong> {execution['id']}</div>
                    <div><strong>Started:</strong> {execution['started'].strftime('%H:%M')}</div>
                    <div><strong>Duration:</strong> {execution['duration']}</div>
                    <div><strong>Nodes:</strong> {execution['nodes_completed']}</div>
                </div>
                {f'<div class="execution-progress"><div style="background: #4f46e5; width: {execution["progress"]}%; height: 8px; border-radius: 4px; transition: width 0.3s ease;"></div></div>' if execution['status'] == 'running' else ''}
            </div>
            """, unsafe_allow_html=True)

    def render_workflow_management(self):
        """Render workflow management interface"""
        st.title("⚙️ Workflow Management")
        
        # Control bar
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search workflows", placeholder="Search by name, description, or tags...")
        
        with col2:
            status_filter = st.selectbox("Status", ["All", "Active", "Draft", "Deprecated"])
        
        with col3:
            category_filter = st.selectbox("Category", ["All", "Medical", "Quality", "Business", "Legal", "Research"])
        
        with col4:
            if st.button("➕ Create New", use_container_width=True):
                st.session_state.show_create_workflow = True
        
        # Workflow list
        self._render_workflow_list(search_term, status_filter, category_filter)
        
        # Create workflow modal
        if st.session_state.get('show_create_workflow', False):
            self._render_create_workflow_modal()

    def _render_workflow_list(self, search_term: str, status_filter: str, category_filter: str):
        """Render the list of workflows with filtering"""
        # Sample workflow data
        workflows = [
            {
                "id": "wf_001",
                "name": "Medical Consultation Analysis", 
                "description": "Advanced medical transcript processing with clinical insights and HIPAA compliance",
                "category": "Medical",
                "status": "Active",
                "version": "2.3.1",
                "nodes": 12,
                "executions": 342,
                "success_rate": 96.8,
                "avg_duration": "4.8min",
                "last_executed": datetime.now() - timedelta(hours=2),
                "tags": ["medical", "hipaa", "clinical", "ner"]
            },
            {
                "id": "wf_002",
                "name": "Real-time Quality Monitor",
                "description": "Continuous quality assessment with automated alerts and remediation",
                "category": "Quality", 
                "status": "Active",
                "version": "1.8.0",
                "nodes": 8,
                "executions": 1247,
                "success_rate": 99.1,
                "avg_duration": "2.2min",
                "last_executed": datetime.now() - timedelta(minutes=30),
                "tags": ["quality", "monitoring", "alerts", "realtime"]
            },
            {
                "id": "wf_003",
                "name": "Legal Document Processing",
                "description": "Analyze legal documents with privilege detection and compliance checks",
                "category": "Legal",
                "status": "Active", 
                "version": "1.5.2",
                "nodes": 15,
                "executions": 89,
                "success_rate": 94.4,
                "avg_duration": "7.2min",
                "last_executed": datetime.now() - timedelta(hours=6),
                "tags": ["legal", "privilege", "compliance"]
            },
            {
                "id": "wf_004",
                "name": "Meeting Minutes Automation",
                "description": "Extract action items and generate structured meeting summaries",
                "category": "Business",
                "status": "Draft",
                "version": "1.0.0",
                "nodes": 6,
                "executions": 23,
                "success_rate": 87.0, 
                "avg_duration": "3.2min",
                "last_executed": datetime.now() - timedelta(days=2),
                "tags": ["business", "meetings", "action-items"]
            }
        ]
        
        # Filter workflows
        filtered_workflows = []
        for workflow in workflows:
            # Text search
            if search_term and search_term.lower() not in workflow['name'].lower() and \
               search_term.lower() not in workflow['description'].lower() and \
               not any(search_term.lower() in tag for tag in workflow['tags']):
                continue
            
            # Status filter
            if status_filter != "All" and workflow['status'] != status_filter:
                continue
            
            # Category filter  
            if category_filter != "All" and workflow['category'] != category_filter:
                continue
            
            filtered_workflows.append(workflow)
        
        # Display workflows
        if not filtered_workflows:
            st.info("No workflows found matching the current filters.")
            return
        
        for workflow in filtered_workflows:
            with st.expander(f"**{workflow['name']}** (v{workflow['version']}) - {workflow['status']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(workflow['description'])
                    
                    # Tags
                    tag_html = " ".join([f'<span style="background: #e5e7eb; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-right: 4px;">{tag}</span>' for tag in workflow['tags']])
                    st.markdown(tag_html, unsafe_allow_html=True)
                    
                    # Metrics grid
                    met_col1, met_col2, met_col3, met_col4 = st.columns(4)
                    with met_col1:
                        st.metric("Nodes", workflow['nodes'])
                    with met_col2:
                        st.metric("Executions", workflow['executions'])
                    with met_col3:
                        st.metric("Success Rate", f"{workflow['success_rate']}%")
                    with met_col4:
                        st.metric("Avg Duration", workflow['avg_duration'])
                
                with col2:
                    st.write(f"**Category:** {workflow['category']}")
                    st.write(f"**Last Executed:** {workflow['last_executed'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Action buttons
                    act_col1, act_col2, act_col3 = st.columns(3)
                    with act_col1:
                        if st.button("▶️ Execute", key=f"execute_{workflow['id']}"):
                            self._execute_workflow(workflow['id'])
                    with act_col2:
                        if st.button("✏️ Edit", key=f"edit_{workflow['id']}"):
                            st.session_state.edit_workflow_id = workflow['id']
                    with act_col3:
                        if st.button("📊 Analytics", key=f"analytics_{workflow['id']}"):
                            st.session_state.analytics_workflow_id = workflow['id']

    def render_execution_monitor(self):
        """Render execution monitoring interface"""
        st.title("📊 Execution Monitor")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status Filter", ["All", "Running", "Completed", "Failed", "Paused"])
        with col2:
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Live execution timeline
        st.subheader("🔴 Live Execution Timeline")
        
        # Sample execution timeline data
        executions = [
            {
                "id": "exec_001",
                "workflow": "Medical Consultation Analysis",
                "status": "running",
                "progress": 73,
                "started": datetime.now() - timedelta(minutes=15),
                "current_node": "Clinical NER Processing",
                "estimated_completion": datetime.now() + timedelta(minutes=5)
            },
            {
                "id": "exec_002", 
                "workflow": "Quality Assessment Pipeline",
                "status": "completed",
                "progress": 100,
                "started": datetime.now() - timedelta(minutes=45),
                "completed": datetime.now() - timedelta(minutes=38),
                "duration": timedelta(minutes=7)
            },
            {
                "id": "exec_003",
                "workflow": "Legal Document Processing", 
                "status": "failed",
                "progress": 25,
                "started": datetime.now() - timedelta(hours=1),
                "failed_at": datetime.now() - timedelta(minutes=57),
                "error": "Failed to connect to legal database"
            }
        ]
        
        # Render timeline
        st.markdown('<div class="workflow-timeline">', unsafe_allow_html=True)
        
        for execution in executions:
            status_color = {
                "running": "#3b82f6",
                "completed": "#10b981", 
                "failed": "#ef4444",
                "paused": "#f59e0b"
            }.get(execution['status'], "#6b7280")
            
            timeline_html = f"""
            <div class="timeline-item" style="border-left: 4px solid {status_color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4 style="margin: 0; color: #1f2937;">{execution['workflow']}</h4>
                    <span style="color: {status_color}; font-weight: bold; text-transform: uppercase;">{execution['status']}</span>
                </div>
                <p style="margin: 0.25rem 0; color: #6b7280;">ID: {execution['id']}</p>
                <p style="margin: 0.25rem 0; color: #6b7280;">Started: {execution['started'].strftime('%H:%M:%S')}</p>
            """
            
            if execution['status'] == 'running':
                timeline_html += f"""
                <p style="margin: 0.25rem 0; color: #6b7280;">Current: {execution.get('current_node', 'Processing...')}</p>
                <div style="background: #f3f4f6; border-radius: 10px; overflow: hidden; margin: 0.5rem 0;">
                    <div style="background: {status_color}; width: {execution['progress']}%; height: 8px; transition: width 0.3s ease;"></div>
                </div>
                <p style="margin: 0; color: #6b7280; font-size: 0.875rem;">Progress: {execution['progress']}%</p>
                """
            elif execution['status'] == 'completed':
                timeline_html += f"""
                <p style="margin: 0.25rem 0; color: #10b981;">✅ Completed in {execution['duration'].total_seconds() / 60:.1f} minutes</p>
                """
            elif execution['status'] == 'failed':
                timeline_html += f"""
                <p style="margin: 0.25rem 0; color: #ef4444;">❌ Failed: {execution.get('error', 'Unknown error')}</p>
                """
            
            timeline_html += "</div>"
            st.markdown(timeline_html, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Execution statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Execution Statistics")
            
            # Generate sample hourly execution data
            hours = list(range(24))
            successful_executions = [max(0, int(30 + 20 * (0.5 - abs(h - 12) / 24))) for h in hours]
            failed_executions = [max(0, int(3 + 2 * (abs(h - 12) / 24))) for h in hours]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=hours, y=successful_executions,
                name='Successful', marker_color='#10b981'
            ))
            fig.add_trace(go.Bar(
                x=hours, y=failed_executions,
                name='Failed', marker_color='#ef4444'
            ))
            
            fig.update_layout(
                title="Executions by Hour (Last 24h)",
                xaxis_title="Hour of Day",
                yaxis_title="Number of Executions",
                barmode='stack',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⏱️ Performance Metrics")
            
            # Performance over time
            dates = [datetime.now() - timedelta(days=i) for i in range(6, -1, -1)]
            avg_durations = [4.2, 3.8, 4.5, 3.9, 4.1, 4.3, 3.7]  # Minutes
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=avg_durations,
                mode='lines+markers',
                name='Avg Duration',
                line=dict(color='#8b5cf6', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Average Execution Duration",
                xaxis_title="Date",
                yaxis_title="Duration (minutes)",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)

    def render_template_library(self):
        """Render workflow template library"""
        st.title("📚 Template Library")
        st.markdown("Browse and deploy pre-built workflow templates")
        
        # Categories
        categories = ["All", "Medical", "Quality", "Business", "Legal", "Research", "Audio/Video"]
        selected_category = st.selectbox("Category", categories)
        
        # Template grid
        templates = [
            {
                "name": "Medical Consultation Processing",
                "description": "Comprehensive medical transcript analysis with clinical NER, quality assessment, and HIPAA compliance validation.",
                "category": "Medical",
                "difficulty": "Advanced",
                "nodes": 12,
                "estimated_time": "15-30 minutes",
                "popularity": 95,
                "features": ["Clinical NER", "Drug Recognition", "HIPAA Compliance", "Quality Assessment"],
                "use_cases": ["Medical consultations", "Clinical documentation", "Patient records"]
            },
            {
                "name": "Real-time Quality Monitor", 
                "description": "Continuous quality assessment pipeline with automated alerts and performance optimization.",
                "category": "Quality",
                "difficulty": "Intermediate",
                "nodes": 8,
                "estimated_time": "5-10 minutes",
                "popularity": 87,
                "features": ["Real-time monitoring", "Automated alerts", "Performance tracking", "Trend analysis"],
                "use_cases": ["Quality control", "Performance monitoring", "SLA compliance"]
            },
            {
                "name": "Meeting Minutes Automation",
                "description": "Extract action items, decisions, and key points from meeting recordings.",
                "category": "Business",
                "difficulty": "Beginner",
                "nodes": 6,
                "estimated_time": "5-15 minutes",
                "popularity": 78,
                "features": ["Action item extraction", "Speaker identification", "Summary generation", "Task assignment"],
                "use_cases": ["Team meetings", "Board meetings", "Client calls"]
            },
            {
                "name": "Legal Document Analysis",
                "description": "Analyze legal documents with privilege detection, entity extraction, and compliance checking.",
                "category": "Legal", 
                "difficulty": "Advanced",
                "nodes": 15,
                "estimated_time": "20-45 minutes",
                "popularity": 82,
                "features": ["Privilege detection", "Legal entity extraction", "Compliance validation", "Risk assessment"],
                "use_cases": ["Contract analysis", "Legal discovery", "Compliance audits"]
            },
            {
                "name": "Research Interview Processing",
                "description": "Process research interviews with thematic analysis, sentiment detection, and insight extraction.",
                "category": "Research",
                "difficulty": "Intermediate", 
                "nodes": 10,
                "estimated_time": "10-25 minutes",
                "popularity": 71,
                "features": ["Thematic analysis", "Sentiment analysis", "Insight extraction", "Data visualization"],
                "use_cases": ["Academic research", "Market research", "User interviews"]
            },
            {
                "name": "Podcast Production Pipeline",
                "description": "End-to-end podcast processing with transcription, enhancement, and distribution preparation.",
                "category": "Audio/Video",
                "difficulty": "Intermediate",
                "nodes": 11,
                "estimated_time": "30-60 minutes", 
                "popularity": 65,
                "features": ["Audio enhancement", "Transcription", "Chapter generation", "Distribution prep"],
                "use_cases": ["Podcast production", "Content creation", "Media distribution"]
            }
        ]
        
        # Filter templates
        if selected_category != "All":
            templates = [t for t in templates if t['category'] == selected_category]
        
        # Display templates in grid
        cols = st.columns(2)
        for i, template in enumerate(templates):
            with cols[i % 2]:
                difficulty_color = {
                    "Beginner": "#10b981",
                    "Intermediate": "#f59e0b", 
                    "Advanced": "#ef4444"
                }.get(template['difficulty'], "#6b7280")
                
                st.markdown(f"""
                <div class="template-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: #1f2937;">{template['name']}</h3>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <span style="background: {difficulty_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">{template['difficulty']}</span>
                            <span style="color: #6b7280; font-size: 0.875rem;">❤️ {template['popularity']}%</span>
                        </div>
                    </div>
                    
                    <p style="color: #6b7280; margin: 0.5rem 0; font-size: 0.875rem;">{template['description']}</p>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; font-size: 0.875rem;">
                        <div><strong>Nodes:</strong> {template['nodes']}</div>
                        <div><strong>Duration:</strong> {template['estimated_time']}</div>
                        <div><strong>Category:</strong> {template['category']}</div>
                        <div><strong>Popularity:</strong> {template['popularity']}%</div>
                    </div>
                    
                    <div style="margin: 1rem 0;">
                        <strong style="font-size: 0.875rem;">Key Features:</strong><br>
                        {' | '.join(template['features'][:3])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Deploy", key=f"deploy_{i}"):
                        self._deploy_template(template)
                with col2:
                    if st.button("👁️ Preview", key=f"preview_{i}"):
                        self._preview_template(template)

    def render_system_health(self):
        """Render system health monitoring"""
        st.title("💻 System Health")
        
        metrics = st.session_state.system_metrics
        
        # Health overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_color = "#ef4444" if metrics['cpu_usage'] > 80 else "#f59e0b" if metrics['cpu_usage'] > 60 else "#10b981"
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; border-left: 4px solid {cpu_color};">
                <h2 style="margin: 0; color: {cpu_color};">{metrics['cpu_usage']:.1f}%</h2>
                <p style="margin: 0; color: #6b7280;">CPU Usage</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            mem_color = "#ef4444" if metrics['memory_usage'] > 85 else "#f59e0b" if metrics['memory_usage'] > 70 else "#10b981"
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; border-left: 4px solid {mem_color};">
                <h2 style="margin: 0; color: {mem_color};">{metrics['memory_usage']:.1f}%</h2>
                <p style="margin: 0; color: #6b7280;">Memory Usage</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            disk_color = "#ef4444" if metrics['disk_usage'] > 90 else "#f59e0b" if metrics['disk_usage'] > 75 else "#10b981"
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; border-left: 4px solid {disk_color};">
                <h2 style="margin: 0; color: {disk_color};">{metrics['disk_usage']:.1f}%</h2>
                <p style="margin: 0; color: #6b7280;">Disk Usage</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            latency_color = "#ef4444" if metrics['network_latency'] > 100 else "#f59e0b" if metrics['network_latency'] > 50 else "#10b981"
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: white; border-radius: 10px; border-left: 4px solid {latency_color};">
                <h2 style="margin: 0; color: {latency_color};">{metrics['network_latency']:.1f}ms</h2>
                <p style="margin: 0; color: #6b7280;">Network Latency</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Resource usage over time
        st.subheader("📈 Resource Usage Trends")
        
        # Generate sample time series data
        time_points = [datetime.now() - timedelta(minutes=i*5) for i in range(12, 0, -1)]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("CPU Usage", "Memory Usage", "Disk I/O", "Network Traffic"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # CPU usage
        cpu_data = [max(0, min(100, metrics['cpu_usage'] + (i-6)*2 + ((-1)**i)*5)) for i in range(12)]
        fig.add_trace(
            go.Scatter(x=time_points, y=cpu_data, name="CPU %", line=dict(color="#3b82f6")),
            row=1, col=1
        )
        
        # Memory usage  
        mem_data = [max(0, min(100, metrics['memory_usage'] + (i-6)*1.5 + ((-1)**i)*3)) for i in range(12)]
        fig.add_trace(
            go.Scatter(x=time_points, y=mem_data, name="Memory %", line=dict(color="#10b981")),
            row=1, col=2
        )
        
        # Disk I/O (MB/s)
        disk_data = [max(0, 50 + (i-6)*3 + ((-1)**i)*10) for i in range(12)]
        fig.add_trace(
            go.Scatter(x=time_points, y=disk_data, name="Disk I/O", line=dict(color="#f59e0b")),
            row=2, col=1
        )
        
        # Network traffic (MB/s)
        net_data = [max(0, 25 + (i-6)*2 + ((-1)**i)*8) for i in range(12)]
        fig.add_trace(
            go.Scatter(x=time_points, y=net_data, name="Network", line=dict(color="#8b5cf6")),
            row=2, col=2
        )
        
        fig.update_layout(height=500, showlegend=False, margin=dict(l=0, r=0, t=50, b=0))
        fig.update_yaxes(title_text="Usage %", row=1, col=1)
        fig.update_yaxes(title_text="Usage %", row=1, col=2) 
        fig.update_yaxes(title_text="MB/s", row=2, col=1)
        fig.update_yaxes(title_text="MB/s", row=2, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # System logs
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔍 Recent Logs")
            logs = [
                {"time": "14:23:15", "level": "INFO", "message": "Workflow execution completed successfully"},
                {"time": "14:22:48", "level": "WARN", "message": "High memory usage detected on node worker-02"},
                {"time": "14:21:33", "level": "INFO", "message": "New workflow template deployed: Legal Analysis v1.5.2"},
                {"time": "14:20:17", "level": "ERROR", "message": "Failed to connect to external API endpoint"},
                {"time": "14:19:45", "level": "INFO", "message": "Automatic scaling triggered: +2 worker nodes"}
            ]
            
            for log in logs:
                level_color = {
                    "ERROR": "#ef4444",
                    "WARN": "#f59e0b", 
                    "INFO": "#3b82f6"
                }.get(log['level'], "#6b7280")
                
                st.markdown(f"""
                <div style="font-family: monospace; font-size: 0.875rem; margin: 0.5rem 0; padding: 0.5rem; background: #f9fafb; border-radius: 4px; border-left: 3px solid {level_color};">
                    <span style="color: #6b7280;">{log['time']}</span> 
                    <span style="color: {level_color}; font-weight: bold;">[{log['level']}]</span> 
                    {log['message']}
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.subheader("⚙️ Service Status")
            services = [
                {"name": "Workflow Engine", "status": "healthy", "uptime": "99.9%", "version": "2.1.0"},
                {"name": "Template Manager", "status": "healthy", "uptime": "99.8%", "version": "1.5.3"},
                {"name": "Execution Monitor", "status": "healthy", "uptime": "100%", "version": "1.2.1"},
                {"name": "Quality Assessor", "status": "warning", "uptime": "98.5%", "version": "3.0.1"},
                {"name": "Automation Engine", "status": "healthy", "uptime": "99.7%", "version": "2.3.0"}
            ]
            
            for service in services:
                status_color = {
                    "healthy": "#10b981",
                    "warning": "#f59e0b",
                    "critical": "#ef4444"
                }.get(service['status'], "#6b7280")
                
                status_icon = {
                    "healthy": "🟢",
                    "warning": "🟡", 
                    "critical": "🔴"
                }.get(service['status'], "⚪")
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; margin: 0.5rem 0; background: white; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <div>
                        <div style="font-weight: 600; color: #1f2937;">{status_icon} {service['name']}</div>
                        <div style="font-size: 0.875rem; color: #6b7280;">v{service['version']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {status_color}; font-weight: 600; text-transform: capitalize;">{service['status']}</div>
                        <div style="font-size: 0.875rem; color: #6b7280;">{service['uptime']} uptime</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    def _deploy_template(self, template: Dict[str, Any]):
        """Deploy a workflow template"""
        st.success(f"✅ Template '{template['name']}' deployed successfully!")
        st.balloons()
        
    def _preview_template(self, template: Dict[str, Any]):
        """Preview a workflow template"""
        st.info(f"👁️ Previewing template: {template['name']}")
        
        # Show template details in expandable section
        with st.expander("Template Details", expanded=True):
            st.write(f"**Description:** {template['description']}")
            st.write(f"**Category:** {template['category']}")
            st.write(f"**Difficulty:** {template['difficulty']}")
            st.write(f"**Estimated Time:** {template['estimated_time']}")
            
            st.write("**Key Features:**")
            for feature in template['features']:
                st.write(f"• {feature}")
            
            st.write("**Use Cases:**")
            for use_case in template['use_cases']:
                st.write(f"• {use_case}")

    def _execute_workflow(self, workflow_id: str):
        """Execute a workflow"""
        st.success(f"🚀 Workflow {workflow_id} execution started!")
        st.info("Check the Execution Monitor tab to track progress.")
        
    def _export_workflow_data(self):
        """Export workflow data"""
        export_data = {
            "workflows": st.session_state.workflows,
            "executions": st.session_state.executions,
            "system_metrics": st.session_state.system_metrics,
            "exported_at": datetime.now().isoformat()
        }
        
        # Convert to JSON for download
        json_data = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="📥 Download Workflow Data",
            data=json_data,
            file_name=f"workflow_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    def run(self):
        """Main application runner"""
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time.sleep(30)  # Refresh every 30 seconds
            st.rerun()
        
        # Render sidebar and get selected page
        page = self.render_sidebar()
        
        # Render the selected page
        if page == "Dashboard Overview":
            self.render_dashboard_overview()
        elif page == "Workflow Management":
            self.render_workflow_management()
        elif page == "Execution Monitor":
            self.render_execution_monitor()
        elif page == "Template Library":
            self.render_template_library()
        elif page == "System Health":
            self.render_system_health()
        elif page == "Automation Rules":
            st.title("🤖 Automation Rules")
            st.info("Automation rules configuration coming soon...")
        elif page == "Analytics":
            st.title("📊 Analytics")
            st.info("Advanced analytics dashboard coming soon...")

# Run the application
if __name__ == "__main__":
    app = WorkflowOrchestrationUI()
    app.run()