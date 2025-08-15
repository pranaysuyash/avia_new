"""
Unified Performance Monitoring System
Integrates all existing monitoring components into a cohesive dashboard
Combines Core Web Vitals, system metrics, application performance, and user experience monitoring
"""

import asyncio
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import psutil
from dataclasses import dataclass
from enum import Enum

# Import existing monitoring components
try:
    from monitoring.metrics_collector import MetricsCollector, Metric, MetricType
    from monitoring.health_check import health_check_endpoint
    from performance.core_web_vitals import PerformanceMonitor, PERFORMANCE_THRESHOLDS
    from streamlit_unified_components import UnifiedComponents
except ImportError:
    # Fallback for demo mode
    st.warning("Some monitoring components not available. Running in demo mode.")


class PerformanceCategory(Enum):
    """Categories of performance metrics"""
    SYSTEM = "system"
    APPLICATION = "application"  
    USER_EXPERIENCE = "user_experience"
    SECURITY = "security"
    BUSINESS = "business"


@dataclass
class PerformanceAlert:
    """Performance alert definition"""
    id: str
    category: PerformanceCategory
    severity: str  # 'critical', 'warning', 'info'
    title: str
    message: str
    threshold: float
    current_value: float
    timestamp: datetime
    resolved: bool = False


class UnifiedPerformanceMonitor:
    """Unified performance monitoring dashboard"""
    
    def __init__(self):
        self.unified = UnifiedComponents()
        self.metrics_collector = self._initialize_metrics_collector()
        self.web_vitals_monitor = self._initialize_web_vitals()
        self.alerts = []
        
        # Initialize session state
        if 'performance_data' not in st.session_state:
            st.session_state.performance_data = {
                'system_metrics': [],
                'web_vitals': [],
                'application_metrics': [],
                'alerts': [],
                'last_update': datetime.now()
            }
    
    def _initialize_metrics_collector(self):
        """Initialize metrics collector if available"""
        try:
            return MetricsCollector(max_history_size=1000)
        except:
            return None
    
    def _initialize_web_vitals(self):
        """Initialize web vitals monitor if available"""
        try:
            return PerformanceMonitor()
        except:
            return None
    
    def render_performance_dashboard(self):
        """Render the unified performance monitoring dashboard"""
        
        # Header
        self.unified.accessibility.add_skip_link("performance-content")
        
        st.markdown("# 📊 Unified Performance Monitoring")
        st.markdown("*Real-time system, application, and user experience monitoring*")
        
        # Auto-refresh toggle
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            refresh_interval = st.selectbox(
                "Refresh Rate",
                [5, 10, 30, 60],
                index=1,
                help="Auto-refresh interval in seconds"
            )
        
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        with col3:
            if st.button("🔄 Refresh Now"):
                self._collect_all_metrics()
                st.rerun()
        
        # Auto refresh logic
        if auto_refresh:
            time_since_update = (datetime.now() - st.session_state.performance_data['last_update']).seconds
            if time_since_update >= refresh_interval:
                self._collect_all_metrics()
                st.rerun()
        
        # Main content
        st.markdown('<div id="performance-content">', unsafe_allow_html=True)
        
        # Alerts section
        self._render_alerts_section()
        
        # Key performance indicators
        self._render_kpi_section()
        
        # Detailed monitoring tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🖥️ System Health",
            "🌐 Web Vitals", 
            "📱 Application Metrics",
            "👥 User Experience",
            "📈 Historical Trends"
        ])
        
        with tab1:
            self._render_system_health()
        
        with tab2:
            self._render_web_vitals()
        
        with tab3:
            self._render_application_metrics()
        
        with tab4:
            self._render_user_experience()
        
        with tab5:
            self._render_historical_trends()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_alerts_section(self):
        """Render active alerts"""
        alerts = st.session_state.performance_data.get('alerts', [])
        active_alerts = [a for a in alerts if not a.get('resolved', False)]
        
        if active_alerts:
            st.markdown("### 🚨 Active Alerts")
            
            for alert in active_alerts[:5]:  # Show top 5 alerts
                severity = alert.get('severity', 'info')
                
                if severity == 'critical':
                    st.error(f"🔴 **{alert.get('title')}**: {alert.get('message')}")
                elif severity == 'warning':
                    st.warning(f"🟡 **{alert.get('title')}**: {alert.get('message')}")
                else:
                    st.info(f"🔵 **{alert.get('title')}**: {alert.get('message')}")
        else:
            st.success("✅ No active performance alerts")
    
    def _render_kpi_section(self):
        """Render key performance indicators"""
        st.markdown("### 📊 Key Performance Indicators")
        
        # Get latest metrics
        system_data = self._get_current_system_metrics()
        web_vitals_data = self._get_current_web_vitals()
        app_data = self._get_current_application_metrics()
        
        # KPI columns
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            cpu_usage = system_data.get('cpu_percent', 0)
            cpu_color = "red" if cpu_usage > 80 else "orange" if cpu_usage > 60 else "green"
            st.metric(
                label="🖥️ CPU Usage",
                value=f"{cpu_usage:.1f}%",
                delta=f"{cpu_usage - 50:.1f}%",
                delta_color="inverse"
            )
        
        with col2:
            memory_usage = system_data.get('memory_percent', 0)
            memory_color = "red" if memory_usage > 85 else "orange" if memory_usage > 70 else "green"
            st.metric(
                label="💾 Memory Usage", 
                value=f"{memory_usage:.1f}%",
                delta=f"{memory_usage - 60:.1f}%",
                delta_color="inverse"
            )
        
        with col3:
            lcp = web_vitals_data.get('lcp', 0) / 1000  # Convert to seconds
            lcp_status = "🟢" if lcp < 2.5 else "🟡" if lcp < 4.0 else "🔴"
            st.metric(
                label=f"{lcp_status} LCP",
                value=f"{lcp:.2f}s",
                delta=f"{lcp - 2.5:.2f}s",
                delta_color="inverse"
            )
        
        with col4:
            fid = web_vitals_data.get('fid', 0)
            fid_status = "🟢" if fid < 100 else "🟡" if fid < 300 else "🔴"
            st.metric(
                label=f"{fid_status} FID",
                value=f"{fid:.0f}ms",
                delta=f"{fid - 100:.0f}ms",
                delta_color="inverse"
            )
        
        with col5:
            response_time = app_data.get('avg_response_time', 0)
            response_status = "🟢" if response_time < 200 else "🟡" if response_time < 500 else "🔴"
            st.metric(
                label=f"{response_status} Response Time",
                value=f"{response_time:.0f}ms",
                delta=f"{response_time - 200:.0f}ms",
                delta_color="inverse"
            )
        
        with col6:
            error_rate = app_data.get('error_rate', 0) * 100
            error_status = "🟢" if error_rate < 1 else "🟡" if error_rate < 5 else "🔴"
            st.metric(
                label=f"{error_status} Error Rate",
                value=f"{error_rate:.2f}%",
                delta=f"{error_rate - 1:.2f}%",
                delta_color="inverse"
            )
    
    def _render_system_health(self):
        """Render system health monitoring"""
        st.markdown("#### 🖥️ System Health Overview")
        
        # Get system metrics
        system_data = self._get_current_system_metrics()
        
        # System overview cards
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU and Memory chart
            fig = go.Figure()
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = system_data.get('cpu_percent', 0),
                domain = {'x': [0, 0.48], 'y': [0, 1]},
                title = {'text': "CPU Usage (%)"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 60], 'color': "lightgreen"},
                        {'range': [60, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number+delta",
                value = system_data.get('memory_percent', 0),
                domain = {'x': [0.52, 1], 'y': [0, 1]},
                title = {'text': "Memory Usage (%)"},
                delta = {'reference': 60},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgreen"},
                        {'range': [70, 85], 'color': "yellow"},
                        {'range': [85, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Disk and Network usage
            disk_data = system_data.get('disk_usage', {})
            network_data = system_data.get('network_io', {})
            
            st.markdown("**💽 Disk Usage**")
            if disk_data:
                disk_percent = disk_data.get('percent', 0)
                disk_free = disk_data.get('free', 0) / (1024**3)  # Convert to GB
                
                st.progress(disk_percent / 100)
                st.caption(f"Used: {disk_percent:.1f}% | Free: {disk_free:.1f} GB")
            
            st.markdown("**🌐 Network I/O**")
            if network_data:
                bytes_sent = network_data.get('bytes_sent', 0) / (1024**2)  # MB
                bytes_recv = network_data.get('bytes_recv', 0) / (1024**2)  # MB
                
                col_sent, col_recv = st.columns(2)
                with col_sent:
                    st.metric("📤 Sent", f"{bytes_sent:.1f} MB")
                with col_recv:
                    st.metric("📥 Received", f"{bytes_recv:.1f} MB")
            
            # System processes
            st.markdown("**⚙️ Top Processes**")
            processes = system_data.get('top_processes', [])
            if processes:
                process_df = pd.DataFrame(processes[:5])
                st.dataframe(
                    process_df[['name', 'cpu_percent', 'memory_percent']],
                    use_container_width=True
                )
    
    def _render_web_vitals(self):
        """Render Core Web Vitals monitoring"""
        st.markdown("#### 🌐 Core Web Vitals")
        
        web_vitals_data = self._get_current_web_vitals()
        
        # Web Vitals score card
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lcp = web_vitals_data.get('lcp', 0) / 1000
            lcp_threshold = PERFORMANCE_THRESHOLDS['lcp']
            lcp_status = "Good" if lcp < lcp_threshold['good']/1000 else "Needs Improvement" if lcp < lcp_threshold['poor']/1000 else "Poor"
            lcp_color = "green" if lcp_status == "Good" else "orange" if lcp_status == "Needs Improvement" else "red"
            
            st.markdown(f"**🎯 Largest Contentful Paint**")
            st.markdown(f"<h2 style='color: {lcp_color}'>{lcp:.2f}s</h2>", unsafe_allow_html=True)
            st.caption(f"Status: {lcp_status}")
        
        with col2:
            fid = web_vitals_data.get('fid', 0)
            fid_threshold = PERFORMANCE_THRESHOLDS['fid']
            fid_status = "Good" if fid < fid_threshold['good'] else "Needs Improvement" if fid < fid_threshold['poor'] else "Poor"
            fid_color = "green" if fid_status == "Good" else "orange" if fid_status == "Needs Improvement" else "red"
            
            st.markdown(f"**⚡ First Input Delay**")
            st.markdown(f"<h2 style='color: {fid_color}'>{fid:.0f}ms</h2>", unsafe_allow_html=True)
            st.caption(f"Status: {fid_status}")
        
        with col3:
            cls = web_vitals_data.get('cls', 0)
            cls_threshold = PERFORMANCE_THRESHOLDS['cls']
            cls_status = "Good" if cls < cls_threshold['good'] else "Needs Improvement" if cls < cls_threshold['poor'] else "Poor"
            cls_color = "green" if cls_status == "Good" else "orange" if cls_status == "Needs Improvement" else "red"
            
            st.markdown(f"**📐 Cumulative Layout Shift**")
            st.markdown(f"<h2 style='color: {cls_color}'>{cls:.3f}</h2>", unsafe_allow_html=True)
            st.caption(f"Status: {cls_status}")
        
        # Performance score
        overall_score = self._calculate_web_vitals_score(web_vitals_data)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = overall_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Performance Score"},
            delta = {'reference': 80},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_application_metrics(self):
        """Render application-specific metrics"""
        st.markdown("#### 📱 Application Performance")
        
        app_data = self._get_current_application_metrics()
        
        # Application metrics overview
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time distribution
            response_times = app_data.get('response_time_history', [])
            if response_times:
                fig = px.histogram(
                    x=response_times,
                    title="Response Time Distribution",
                    labels={'x': 'Response Time (ms)', 'y': 'Frequency'},
                    nbins=20
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No response time data available")
        
        with col2:
            # Error rate over time
            error_data = app_data.get('error_history', [])
            if error_data:
                df = pd.DataFrame(error_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                fig = px.line(
                    df,
                    x='timestamp',
                    y='error_rate',
                    title="Error Rate Over Time",
                    labels={'error_rate': 'Error Rate (%)', 'timestamp': 'Time'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No error rate data available")
        
        # Endpoint performance table
        st.markdown("**🔗 API Endpoint Performance**")
        endpoint_data = app_data.get('endpoint_metrics', [])
        if endpoint_data:
            endpoint_df = pd.DataFrame(endpoint_data)
            st.dataframe(
                endpoint_df[['endpoint', 'avg_response_time', 'request_count', 'error_rate']],
                use_container_width=True
            )
        else:
            st.info("No endpoint performance data available")
    
    def _render_user_experience(self):
        """Render user experience metrics"""
        st.markdown("#### 👥 User Experience Metrics")
        
        # User experience overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 User Satisfaction**")
            
            # Mock user satisfaction data (in real implementation, would come from analytics)
            satisfaction_data = {
                'Very Satisfied': 45,
                'Satisfied': 35, 
                'Neutral': 15,
                'Dissatisfied': 3,
                'Very Dissatisfied': 2
            }
            
            fig = px.pie(
                values=list(satisfaction_data.values()),
                names=list(satisfaction_data.keys()),
                title="User Satisfaction Distribution"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**⏱️ User Engagement**")
            
            # Session duration metrics
            session_metrics = {
                'Average Session Duration': '8.5 min',
                'Pages Per Session': '4.2',
                'Bounce Rate': '25%',
                'Return Visitors': '68%'
            }
            
            for metric, value in session_metrics.items():
                st.metric(metric, value)
    
    def _render_historical_trends(self):
        """Render historical performance trends"""
        st.markdown("#### 📈 Historical Performance Trends")
        
        # Generate historical data for demo
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        # System metrics over time
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU and Memory trends
            cpu_trend = np.random.normal(45, 10, 30).clip(0, 100)
            memory_trend = np.random.normal(65, 8, 30).clip(0, 100)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=cpu_trend, name='CPU %', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=dates, y=memory_trend, name='Memory %', line=dict(color='green')))
            
            fig.update_layout(
                title="System Resources (30 Days)",
                xaxis_title="Date",
                yaxis_title="Usage %",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Response time trends
            response_trend = np.random.normal(250, 50, 30).clip(50, 1000)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=response_trend, name='Response Time', line=dict(color='red')))
            fig.add_hline(y=500, line_dash="dash", line_color="orange", annotation_text="SLA Threshold")
            
            fig.update_layout(
                title="Response Time Trends (30 Days)",
                xaxis_title="Date", 
                yaxis_title="Response Time (ms)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _collect_all_metrics(self):
        """Collect all performance metrics"""
        current_time = datetime.now()
        
        # Collect system metrics
        system_metrics = self._get_current_system_metrics()
        
        # Collect web vitals
        web_vitals = self._get_current_web_vitals()
        
        # Collect application metrics
        app_metrics = self._get_current_application_metrics()
        
        # Check for alerts
        alerts = self._check_performance_alerts(system_metrics, web_vitals, app_metrics)
        
        # Update session state
        st.session_state.performance_data.update({
            'system_metrics': system_metrics,
            'web_vitals': web_vitals,
            'application_metrics': app_metrics,
            'alerts': alerts,
            'last_update': current_time
        })
    
    def _get_current_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # Get system information using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Get top processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:10]
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'disk_usage': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network_io': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'top_processes': processes,
                'timestamp': datetime.now()
            }
        except Exception as e:
            st.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _get_current_web_vitals(self) -> Dict[str, Any]:
        """Get current web vitals metrics"""
        # In real implementation, would get from performance monitoring
        # For demo, return simulated data
        return {
            'lcp': np.random.normal(2000, 500).clip(500, 5000),  # ms
            'fid': np.random.normal(80, 20).clip(10, 300),       # ms  
            'cls': np.random.normal(0.1, 0.05).clip(0, 0.5),    # unitless
            'fcp': np.random.normal(1500, 300).clip(500, 3000), # ms
            'ttfb': np.random.normal(400, 100).clip(100, 1000), # ms
            'timestamp': datetime.now()
        }
    
    def _get_current_application_metrics(self) -> Dict[str, Any]:
        """Get current application metrics"""
        # In real implementation, would get from application monitoring
        # For demo, return simulated data
        return {
            'avg_response_time': np.random.normal(250, 50).clip(50, 1000),
            'error_rate': np.random.beta(1, 20),  # Low error rate
            'request_count': np.random.poisson(100),
            'active_users': np.random.poisson(50),
            'response_time_history': list(np.random.normal(250, 50, 100)),
            'error_history': [
                {'timestamp': datetime.now() - timedelta(minutes=i), 'error_rate': np.random.beta(1, 20) * 100}
                for i in range(60, 0, -1)
            ],
            'endpoint_metrics': [
                {'endpoint': '/api/transcribe', 'avg_response_time': 1200, 'request_count': 45, 'error_rate': 2.1},
                {'endpoint': '/api/analyze', 'avg_response_time': 800, 'request_count': 32, 'error_rate': 1.5},
                {'endpoint': '/api/export', 'avg_response_time': 2100, 'request_count': 18, 'error_rate': 0.8},
                {'endpoint': '/api/users', 'avg_response_time': 150, 'request_count': 156, 'error_rate': 0.2}
            ],
            'timestamp': datetime.now()
        }
    
    def _calculate_web_vitals_score(self, vitals_data: Dict[str, Any]) -> float:
        """Calculate overall web vitals performance score"""
        lcp = vitals_data.get('lcp', 0)
        fid = vitals_data.get('fid', 0)
        cls = vitals_data.get('cls', 0)
        
        # Score each metric (0-100)
        lcp_score = 100 if lcp < 2500 else 50 if lcp < 4000 else 0
        fid_score = 100 if fid < 100 else 50 if fid < 300 else 0
        cls_score = 100 if cls < 0.1 else 50 if cls < 0.25 else 0
        
        # Average score
        return (lcp_score + fid_score + cls_score) / 3
    
    def _check_performance_alerts(self, system_metrics: Dict, web_vitals: Dict, app_metrics: Dict) -> List[Dict]:
        """Check for performance alerts"""
        alerts = []
        
        # System alerts
        cpu_usage = system_metrics.get('cpu_percent', 0)
        if cpu_usage > 80:
            alerts.append({
                'id': 'high_cpu',
                'category': 'system',
                'severity': 'critical' if cpu_usage > 90 else 'warning',
                'title': 'High CPU Usage',
                'message': f'CPU usage is at {cpu_usage:.1f}%',
                'threshold': 80,
                'current_value': cpu_usage,
                'timestamp': datetime.now(),
                'resolved': False
            })
        
        memory_usage = system_metrics.get('memory_percent', 0)
        if memory_usage > 85:
            alerts.append({
                'id': 'high_memory',
                'category': 'system',
                'severity': 'critical' if memory_usage > 95 else 'warning',
                'title': 'High Memory Usage',
                'message': f'Memory usage is at {memory_usage:.1f}%',
                'threshold': 85,
                'current_value': memory_usage,
                'timestamp': datetime.now(),
                'resolved': False
            })
        
        # Web vitals alerts
        lcp = web_vitals.get('lcp', 0)
        if lcp > 4000:
            alerts.append({
                'id': 'poor_lcp',
                'category': 'user_experience',
                'severity': 'warning',
                'title': 'Poor LCP Performance',
                'message': f'Largest Contentful Paint is {lcp/1000:.2f}s (should be < 2.5s)',
                'threshold': 2500,
                'current_value': lcp,
                'timestamp': datetime.now(),
                'resolved': False
            })
        
        return alerts


def demo_unified_performance_monitoring():
    """Demo the unified performance monitoring dashboard"""
    
    # Initialize the monitor
    monitor = UnifiedPerformanceMonitor()
    
    # Render the dashboard
    monitor.render_performance_dashboard()


if __name__ == "__main__":
    demo_unified_performance_monitoring()