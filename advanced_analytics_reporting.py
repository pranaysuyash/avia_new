"""
Advanced Analytics and Reporting System
Comprehensive analytics, metrics tracking, and automated reporting with visualization
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import sqlite3
import redis.asyncio as redis
from pathlib import Path
import jinja2
import pdfkit
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.application import MimeApplication
import xlsxwriter
import io
import base64
from collections import defaultdict, deque
import scipy.stats as stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Medical schema integration
from comprehensive_medical_schema import ComprehensiveMedicalSchema

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types of reports available"""
    USAGE = "usage"
    PERFORMANCE = "performance"
    MEDICAL = "medical"
    BUSINESS = "business"
    TECHNICAL = "technical"
    COMPLIANCE = "compliance"
    TREND = "trend"
    PREDICTIVE = "predictive"

class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    JSON = "json"
    CSV = "csv"
    DASHBOARD = "dashboard"

class MetricCategory(Enum):
    """Categories of metrics"""
    SYSTEM = "system"
    BUSINESS = "business"
    MEDICAL = "medical"
    USER = "user"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    FINANCIAL = "financial"

@dataclass
class MetricDefinition:
    """Definition of a metric to track"""
    id: str
    name: str
    category: MetricCategory
    description: str
    calculation_method: str
    data_sources: List[str]
    unit: str
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    trend_direction: str = "higher_better"  # higher_better, lower_better, stable
    business_impact: str = "medium"  # low, medium, high
    calculation_frequency: str = "daily"  # real_time, hourly, daily, weekly, monthly

@dataclass
class AnalyticsData:
    """Analytics data point"""
    timestamp: datetime
    metric_id: str
    value: float
    dimensions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class ReportConfig:
    """Report configuration"""
    id: str
    name: str
    type: ReportType
    format: ReportFormat
    metrics: List[str]
    time_range: str  # 1d, 7d, 30d, 90d, 1y
    filters: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)
    schedule: Optional[str] = None  # cron expression
    template: Optional[str] = None
    enabled: bool = True

@dataclass
class Report:
    """Generated report"""
    id: str
    config_id: str
    name: str
    type: ReportType
    format: ReportFormat
    generated_at: datetime
    data: Dict[str, Any]
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AdvancedAnalyticsEngine:
    """Core analytics engine with advanced calculations"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.db_connection = None
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.data_buffer: deque = deque(maxlen=10000)
        self.cache: Dict[str, Any] = {}
        self._initialize_database()
        self._initialize_default_metrics()
    
    def _initialize_database(self):
        """Initialize analytics database"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        # Analytics data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                metric_id TEXT,
                value REAL,
                dimensions TEXT,
                metadata TEXT,
                session_id TEXT,
                user_id TEXT,
                INDEX(timestamp),
                INDEX(metric_id),
                INDEX(user_id)
            )
        ''')
        
        # Calculated metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculated_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                metric_id TEXT,
                period TEXT,
                value REAL,
                calculation_metadata TEXT
            )
        ''')
        
        # Report cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_cache (
                id TEXT PRIMARY KEY,
                config_id TEXT,
                generated_at TEXT,
                data TEXT,
                file_path TEXT
            )
        ''')
        
        self.db_connection.commit()
    
    def _initialize_default_metrics(self):
        """Initialize default metric definitions"""
        default_metrics = [
            MetricDefinition(
                id="transcription_accuracy",
                name="Transcription Accuracy",
                category=MetricCategory.QUALITY,
                description="Average accuracy of transcription results",
                calculation_method="mean",
                data_sources=["transcription_service"],
                unit="percentage",
                target_value=95.0,
                warning_threshold=90.0,
                critical_threshold=85.0
            ),
            MetricDefinition(
                id="response_time",
                name="Average Response Time",
                category=MetricCategory.PERFORMANCE,
                description="Average API response time",
                calculation_method="percentile_95",
                data_sources=["api_logs"],
                unit="milliseconds",
                target_value=500.0,
                warning_threshold=1000.0,
                critical_threshold=2000.0,
                trend_direction="lower_better"
            ),
            MetricDefinition(
                id="daily_active_users",
                name="Daily Active Users",
                category=MetricCategory.USER,
                description="Number of unique users per day",
                calculation_method="count_distinct",
                data_sources=["user_sessions"],
                unit="users",
                trend_direction="higher_better"
            ),
            MetricDefinition(
                id="medical_compliance_score",
                name="Medical Compliance Score",
                category=MetricCategory.MEDICAL,
                description="HIPAA and medical standards compliance score",
                calculation_method="weighted_average",
                data_sources=["compliance_service", "medical_validator"],
                unit="percentage",
                target_value=98.0,
                warning_threshold=95.0,
                critical_threshold=90.0,
                business_impact="high"
            ),
            MetricDefinition(
                id="revenue_per_user",
                name="Revenue Per User",
                category=MetricCategory.FINANCIAL,
                description="Average revenue generated per user",
                calculation_method="total_sum",
                data_sources=["billing_service"],
                unit="dollars",
                trend_direction="higher_better",
                business_impact="high"
            ),
            MetricDefinition(
                id="error_rate",
                name="System Error Rate",
                category=MetricCategory.SYSTEM,
                description="Percentage of requests resulting in errors",
                calculation_method="error_percentage",
                data_sources=["api_logs", "error_logs"],
                unit="percentage",
                target_value=1.0,
                warning_threshold=3.0,
                critical_threshold=5.0,
                trend_direction="lower_better"
            )
        ]
        
        for metric in default_metrics:
            self.metric_definitions[metric.id] = metric
    
    def add_metric_definition(self, metric: MetricDefinition):
        """Add a new metric definition"""
        self.metric_definitions[metric.id] = metric
        logger.info(f"Added metric definition: {metric.name}")
    
    def record_data(self, data: AnalyticsData):
        """Record analytics data point"""
        # Add to buffer for real-time processing
        self.data_buffer.append(data)
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT INTO analytics_data (
                timestamp, metric_id, value, dimensions, 
                metadata, session_id, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.timestamp.isoformat(),
            data.metric_id,
            data.value,
            json.dumps(data.dimensions),
            json.dumps(data.metadata),
            data.session_id,
            data.user_id
        ))
        self.db_connection.commit()
    
    def calculate_metric(
        self,
        metric_id: str,
        time_range: str = "24h",
        filters: Optional[Dict] = None
    ) -> float:
        """Calculate metric value for given time range"""
        if metric_id not in self.metric_definitions:
            raise ValueError(f"Unknown metric: {metric_id}")
        
        metric_def = self.metric_definitions[metric_id]
        
        # Parse time range
        end_time = datetime.now()
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            start_time = end_time - timedelta(days=days)
        else:
            start_time = end_time - timedelta(days=1)
        
        # Query data
        cursor = self.db_connection.cursor()
        query = '''
            SELECT value, dimensions, metadata
            FROM analytics_data
            WHERE metric_id = ? AND timestamp BETWEEN ? AND ?
        '''
        params = [metric_id, start_time.isoformat(), end_time.isoformat()]
        
        # Add filters
        if filters:
            for key, value in filters.items():
                query += f" AND JSON_EXTRACT(dimensions, '$.{key}') = ?"
                params.append(value)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            return 0.0
        
        values = [row[0] for row in rows]
        
        # Calculate based on method
        if metric_def.calculation_method == "mean":
            return np.mean(values)
        elif metric_def.calculation_method == "sum":
            return np.sum(values)
        elif metric_def.calculation_method == "max":
            return np.max(values)
        elif metric_def.calculation_method == "min":
            return np.min(values)
        elif metric_def.calculation_method == "percentile_95":
            return np.percentile(values, 95)
        elif metric_def.calculation_method == "percentile_99":
            return np.percentile(values, 99)
        elif metric_def.calculation_method == "count_distinct":
            return len(set(values))
        elif metric_def.calculation_method == "error_percentage":
            errors = sum(1 for v in values if v > 0)
            return (errors / len(values)) * 100
        else:
            return np.mean(values)
    
    def calculate_trend(
        self,
        metric_id: str,
        periods: int = 30,
        period_length: str = "1d"
    ) -> Dict[str, Any]:
        """Calculate metric trend over time"""
        trends = []
        timestamps = []
        
        end_time = datetime.now()
        
        for i in range(periods):
            if period_length == "1d":
                period_end = end_time - timedelta(days=i)
                period_start = period_end - timedelta(days=1)
            elif period_length == "1h":
                period_end = end_time - timedelta(hours=i)
                period_start = period_end - timedelta(hours=1)
            else:
                continue
            
            # Calculate metric for this period
            cursor = self.db_connection.cursor()
            cursor.execute('''
                SELECT AVG(value)
                FROM analytics_data
                WHERE metric_id = ? AND timestamp BETWEEN ? AND ?
            ''', (metric_id, period_start.isoformat(), period_end.isoformat()))
            
            result = cursor.fetchone()
            value = result[0] if result[0] is not None else 0
            
            trends.append(value)
            timestamps.append(period_start)
        
        # Reverse to get chronological order
        trends.reverse()
        timestamps.reverse()
        
        # Calculate trend statistics
        if len(trends) > 1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                range(len(trends)), trends
            )
            
            trend_direction = "increasing" if slope > 0 else "decreasing"
            trend_strength = abs(r_value)
        else:
            slope = 0
            trend_direction = "stable"
            trend_strength = 0
        
        return {
            "values": trends,
            "timestamps": [t.isoformat() for t in timestamps],
            "slope": slope,
            "direction": trend_direction,
            "strength": trend_strength,
            "latest_value": trends[-1] if trends else 0,
            "change_percent": ((trends[-1] - trends[0]) / trends[0] * 100) if trends and trends[0] != 0 else 0
        }
    
    def detect_anomalies(
        self,
        metric_id: str,
        time_range: str = "7d",
        method: str = "zscore"
    ) -> List[Dict]:
        """Detect anomalies in metric data"""
        # Get data
        end_time = datetime.now()
        days = int(time_range[:-1]) if time_range.endswith('d') else 7
        start_time = end_time - timedelta(days=days)
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
            SELECT timestamp, value
            FROM analytics_data
            WHERE metric_id = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        ''', (metric_id, start_time.isoformat(), end_time.isoformat()))
        
        rows = cursor.fetchall()
        if len(rows) < 10:  # Need minimum data points
            return []
        
        timestamps = [row[0] for row in rows]
        values = [row[1] for row in rows]
        
        anomalies = []
        
        if method == "zscore":
            z_scores = np.abs(stats.zscore(values))
            threshold = 3.0
            
            for i, (timestamp, value, z_score) in enumerate(zip(timestamps, values, z_scores)):
                if z_score > threshold:
                    anomalies.append({
                        "timestamp": timestamp,
                        "value": value,
                        "z_score": z_score,
                        "severity": "high" if z_score > 4 else "medium",
                        "method": "zscore"
                    })
        
        elif method == "iqr":
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            for timestamp, value in zip(timestamps, values):
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        "timestamp": timestamp,
                        "value": value,
                        "bounds": [lower_bound, upper_bound],
                        "severity": "high" if value < q1 - 3 * iqr or value > q3 + 3 * iqr else "medium",
                        "method": "iqr"
                    })
        
        return anomalies
    
    def perform_cohort_analysis(
        self,
        cohort_metric: str = "user_registration",
        retention_metric: str = "user_login",
        periods: int = 12
    ) -> Dict[str, Any]:
        """Perform cohort analysis"""
        # This is a simplified cohort analysis
        # In practice, this would be more sophisticated
        
        cursor = self.db_connection.cursor()
        
        # Get cohort data (simplified)
        cursor.execute('''
            SELECT 
                DATE(timestamp) as cohort_date,
                COUNT(DISTINCT user_id) as cohort_size
            FROM analytics_data
            WHERE metric_id = ?
            GROUP BY DATE(timestamp)
            ORDER BY cohort_date
            LIMIT ?
        ''', (cohort_metric, periods))
        
        cohorts = cursor.fetchall()
        
        cohort_data = []
        for cohort_date, cohort_size in cohorts:
            # Calculate retention for each period
            retention_data = []
            for period in range(periods):
                period_start = datetime.fromisoformat(cohort_date) + timedelta(days=period*30)
                period_end = period_start + timedelta(days=30)
                
                cursor.execute('''
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_data
                    WHERE metric_id = ? 
                    AND timestamp BETWEEN ? AND ?
                    AND user_id IN (
                        SELECT DISTINCT user_id
                        FROM analytics_data
                        WHERE metric_id = ? AND DATE(timestamp) = ?
                    )
                ''', (
                    retention_metric,
                    period_start.isoformat(),
                    period_end.isoformat(),
                    cohort_metric,
                    cohort_date
                ))
                
                retained_users = cursor.fetchone()[0]
                retention_rate = (retained_users / cohort_size) * 100 if cohort_size > 0 else 0
                retention_data.append(retention_rate)
            
            cohort_data.append({
                "cohort_date": cohort_date,
                "cohort_size": cohort_size,
                "retention_rates": retention_data
            })
        
        return {
            "cohorts": cohort_data,
            "periods": periods,
            "metrics": {
                "cohort_metric": cohort_metric,
                "retention_metric": retention_metric
            }
        }

class ReportGenerator:
    """Advanced report generation system"""
    
    def __init__(self, analytics_engine: AdvancedAnalyticsEngine):
        self.analytics_engine = analytics_engine
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self.reports_path = Path("reports")
        self.reports_path.mkdir(exist_ok=True)
        
        # Medical schema for specialized reporting
        self.medical_schema = None
        try:
            self.medical_schema = ComprehensiveMedicalSchema()
        except Exception as e:
            logger.warning(f"Medical schema not available: {e}")
    
    async def generate_report(self, config: ReportConfig) -> Report:
        """Generate a report based on configuration"""
        report_id = str(uuid.uuid4())
        
        # Collect data for metrics
        report_data = {}
        
        for metric_id in config.metrics:
            try:
                # Calculate current value
                current_value = self.analytics_engine.calculate_metric(
                    metric_id, 
                    config.time_range, 
                    config.filters
                )
                
                # Calculate trend
                trend_data = self.analytics_engine.calculate_trend(
                    metric_id, 
                    periods=30
                )
                
                # Detect anomalies
                anomalies = self.analytics_engine.detect_anomalies(metric_id)
                
                report_data[metric_id] = {
                    "current_value": current_value,
                    "trend": trend_data,
                    "anomalies": anomalies,
                    "definition": self.analytics_engine.metric_definitions.get(metric_id)
                }
                
            except Exception as e:
                logger.error(f"Error calculating metric {metric_id}: {e}")
                report_data[metric_id] = {"error": str(e)}
        
        # Add specialized data based on report type
        if config.type == ReportType.MEDICAL and self.medical_schema:
            report_data["medical_analysis"] = await self._generate_medical_analysis(config)
        elif config.type == ReportType.BUSINESS:
            report_data["business_insights"] = await self._generate_business_insights(config)
        elif config.type == ReportType.PREDICTIVE:
            report_data["predictions"] = await self._generate_predictions(config)
        
        # Generate visualizations
        visualizations = await self._generate_visualizations(report_data, config)
        report_data["visualizations"] = visualizations
        
        # Create report object
        report = Report(
            id=report_id,
            config_id=config.id,
            name=config.name,
            type=config.type,
            format=config.format,
            generated_at=datetime.now(),
            data=report_data
        )
        
        # Generate output file
        if config.format != ReportFormat.DASHBOARD:
            file_path = await self._generate_report_file(report, config)
            report.file_path = file_path
        
        return report
    
    async def _generate_medical_analysis(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate medical-specific analysis"""
        if not self.medical_schema:
            return {"error": "Medical schema not available"}
        
        # Analyze medical transcription quality
        medical_metrics = []
        
        # Get medical accuracy data
        cursor = self.analytics_engine.db_connection.cursor()
        cursor.execute('''
            SELECT timestamp, value, dimensions
            FROM analytics_data
            WHERE metric_id LIKE '%medical%' OR metric_id LIKE '%hipaa%'
            ORDER BY timestamp DESC
            LIMIT 1000
        ''')
        
        medical_data = cursor.fetchall()
        
        # Analyze compliance trends
        compliance_scores = []
        accuracy_scores = []
        
        for row in medical_data:
            dimensions = json.loads(row[2]) if row[2] else {}
            if 'compliance' in dimensions:
                compliance_scores.append(row[1])
            if 'accuracy' in dimensions:
                accuracy_scores.append(row[1])
        
        return {
            "compliance_average": np.mean(compliance_scores) if compliance_scores else 0,
            "accuracy_average": np.mean(accuracy_scores) if accuracy_scores else 0,
            "total_medical_sessions": len(medical_data),
            "compliance_trend": "improving" if len(compliance_scores) > 1 and compliance_scores[-1] > compliance_scores[0] else "stable",
            "risk_assessment": "low" if np.mean(compliance_scores) > 95 else "medium" if np.mean(compliance_scores) > 90 else "high"
        }
    
    async def _generate_business_insights(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate business intelligence insights"""
        cursor = self.analytics_engine.db_connection.cursor()
        
        # Revenue analysis
        cursor.execute('''
            SELECT DATE(timestamp) as date, SUM(value) as daily_revenue
            FROM analytics_data
            WHERE metric_id = 'revenue_per_user'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        revenue_data = cursor.fetchall()
        
        # User growth analysis
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as daily_users
            FROM analytics_data
            WHERE metric_id = 'daily_active_users'
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        user_data = cursor.fetchall()
        
        # Calculate insights
        revenue_trend = "growing" if len(revenue_data) > 1 and revenue_data[0][1] > revenue_data[-1][1] else "declining"
        user_trend = "growing" if len(user_data) > 1 and user_data[0][1] > user_data[-1][1] else "declining"
        
        return {
            "revenue_trend": revenue_trend,
            "user_growth_trend": user_trend,
            "total_revenue_30d": sum(row[1] for row in revenue_data),
            "average_daily_users": np.mean([row[1] for row in user_data]) if user_data else 0,
            "key_insights": [
                f"Revenue is {revenue_trend} over the last 30 days",
                f"User base is {user_trend}",
                "Consider A/B testing new features" if user_trend == "declining" else "Scale infrastructure for growth"
            ]
        }
    
    async def _generate_predictions(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate predictive analysis"""
        predictions = {}
        
        for metric_id in config.metrics:
            try:
                # Get historical data
                cursor = self.analytics_engine.db_connection.cursor()
                cursor.execute('''
                    SELECT DATE(timestamp) as date, AVG(value) as daily_avg
                    FROM analytics_data
                    WHERE metric_id = ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                    LIMIT 90
                ''', (metric_id,))
                
                data = cursor.fetchall()
                
                if len(data) > 10:
                    values = [row[1] for row in data]
                    
                    # Simple linear prediction (in practice, use more sophisticated models)
                    X = np.array(range(len(values))).reshape(-1, 1)
                    y = np.array(values)
                    
                    # Calculate trend
                    slope, intercept, r_value, p_value, std_err = stats.linregress(range(len(values)), values)
                    
                    # Predict next 7 days
                    future_days = 7
                    future_values = []
                    for i in range(len(values), len(values) + future_days):
                        predicted_value = slope * i + intercept
                        future_values.append(predicted_value)
                    
                    predictions[metric_id] = {
                        "next_7_days": future_values,
                        "confidence": abs(r_value),
                        "trend": "increasing" if slope > 0 else "decreasing",
                        "accuracy_note": "Simple linear prediction - actual results may vary"
                    }
                
            except Exception as e:
                logger.error(f"Error generating prediction for {metric_id}: {e}")
                predictions[metric_id] = {"error": str(e)}
        
        return predictions
    
    async def _generate_visualizations(
        self, 
        report_data: Dict[str, Any], 
        config: ReportConfig
    ) -> Dict[str, str]:
        """Generate visualization charts"""
        visualizations = {}
        
        for metric_id in config.metrics:
            if metric_id not in report_data or "error" in report_data[metric_id]:
                continue
            
            try:
                metric_data = report_data[metric_id]
                trend_data = metric_data.get("trend", {})
                
                if trend_data.get("values") and trend_data.get("timestamps"):
                    # Create time series chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=trend_data["timestamps"],
                        y=trend_data["values"],
                        mode='lines+markers',
                        name=metric_id,
                        line=dict(width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"{metric_id.replace('_', ' ').title()} Trend",
                        xaxis_title="Time",
                        yaxis_title="Value",
                        height=400,
                        showlegend=True
                    )
                    
                    # Convert to JSON for storage
                    visualizations[f"{metric_id}_trend"] = fig.to_json()
                
                # Create anomaly chart if anomalies exist
                anomalies = metric_data.get("anomalies", [])
                if anomalies:
                    fig_anomaly = go.Figure()
                    
                    anomaly_times = [a["timestamp"] for a in anomalies]
                    anomaly_values = [a["value"] for a in anomalies]
                    
                    fig_anomaly.add_trace(go.Scatter(
                        x=anomaly_times,
                        y=anomaly_values,
                        mode='markers',
                        marker=dict(
                            size=10,
                            color='red',
                            symbol='x'
                        ),
                        name='Anomalies'
                    ))
                    
                    fig_anomaly.update_layout(
                        title=f"{metric_id.replace('_', ' ').title()} Anomalies",
                        xaxis_title="Time",
                        yaxis_title="Value",
                        height=400
                    )
                    
                    visualizations[f"{metric_id}_anomalies"] = fig_anomaly.to_json()
                
            except Exception as e:
                logger.error(f"Error generating visualization for {metric_id}: {e}")
        
        return visualizations
    
    async def _generate_report_file(self, report: Report, config: ReportConfig) -> str:
        """Generate report file in specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.name}_{timestamp}"
        
        if config.format == ReportFormat.PDF:
            return await self._generate_pdf_report(report, filename)
        elif config.format == ReportFormat.HTML:
            return await self._generate_html_report(report, filename)
        elif config.format == ReportFormat.EXCEL:
            return await self._generate_excel_report(report, filename)
        elif config.format == ReportFormat.JSON:
            return await self._generate_json_report(report, filename)
        elif config.format == ReportFormat.CSV:
            return await self._generate_csv_report(report, filename)
        else:
            return ""
    
    async def _generate_pdf_report(self, report: Report, filename: str) -> str:
        """Generate PDF report"""
        # First generate HTML
        html_content = await self._create_html_content(report)
        
        # Convert to PDF
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            
            file_path = self.reports_path / f"{filename}.pdf"
            pdfkit.from_string(html_content, str(file_path), options=options)
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return ""
    
    async def _generate_html_report(self, report: Report, filename: str) -> str:
        """Generate HTML report"""
        html_content = await self._create_html_content(report)
        
        file_path = self.reports_path / f"{filename}.html"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _create_html_content(self, report: Report) -> str:
        """Create HTML content for reports"""
        # Basic HTML template (in practice, use Jinja2 templates)
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .metric {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; }}
                .metric-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .metric-value {{ font-size: 24px; color: #007bff; margin-bottom: 10px; }}
                .trend {{ color: #28a745; }}
                .trend.declining {{ color: #dc3545; }}
                .chart {{ margin: 20px 0; }}
                .summary {{ background: #f8f9fa; padding: 20px; margin: 20px 0; }}
            </style>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        </head>
        <body>
            <div class="header">
                <h1>{report.name}</h1>
                <p>Generated on: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Report Type: {report.type.value.title()}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p>This report provides comprehensive analytics for the specified metrics and time period.</p>
            </div>
        """
        
        # Add metric sections
        for metric_id, metric_data in report.data.items():
            if metric_id in ["visualizations", "medical_analysis", "business_insights", "predictions"]:
                continue
                
            if "error" in metric_data:
                continue
            
            definition = metric_data.get("definition")
            current_value = metric_data.get("current_value", 0)
            trend = metric_data.get("trend", {})
            
            trend_class = "trend"
            if trend.get("direction") == "decreasing":
                if definition and definition.trend_direction == "lower_better":
                    trend_class = "trend"
                else:
                    trend_class = "trend declining"
            
            html_template += f"""
            <div class="metric">
                <div class="metric-title">{metric_id.replace('_', ' ').title()}</div>
                <div class="metric-value">{current_value:.2f}</div>
                <div class="{trend_class}">
                    Trend: {trend.get('direction', 'stable')} 
                    ({trend.get('change_percent', 0):.1f}% change)
                </div>
                <div class="chart" id="chart_{metric_id}"></div>
            </div>
            """
        
        # Add JavaScript for charts
        html_template += "<script>"
        
        visualizations = report.data.get("visualizations", {})
        for chart_id, chart_json in visualizations.items():
            if "_trend" in chart_id:
                metric_id = chart_id.replace("_trend", "")
                html_template += f"""
                try {{
                    var chartData_{metric_id} = {chart_json};
                    Plotly.newPlot('chart_{metric_id}', chartData_{metric_id}.data, chartData_{metric_id}.layout);
                }} catch(e) {{
                    console.error('Error rendering chart for {metric_id}:', e);
                }}
                """
        
        html_template += "</script></body></html>"
        
        return html_template
    
    async def _generate_excel_report(self, report: Report, filename: str) -> str:
        """Generate Excel report"""
        file_path = self.reports_path / f"{filename}.xlsx"
        
        with xlsxwriter.Workbook(str(file_path)) as workbook:
            # Summary worksheet
            summary_ws = workbook.add_worksheet('Summary')
            
            # Add headers
            bold = workbook.add_format({'bold': True})
            summary_ws.write('A1', 'Metric', bold)
            summary_ws.write('B1', 'Current Value', bold)
            summary_ws.write('C1', 'Trend Direction', bold)
            summary_ws.write('D1', 'Change %', bold)
            
            row = 1
            for metric_id, metric_data in report.data.items():
                if metric_id in ["visualizations", "medical_analysis", "business_insights", "predictions"]:
                    continue
                    
                if "error" in metric_data:
                    continue
                
                current_value = metric_data.get("current_value", 0)
                trend = metric_data.get("trend", {})
                
                summary_ws.write(row, 0, metric_id.replace('_', ' ').title())
                summary_ws.write(row, 1, current_value)
                summary_ws.write(row, 2, trend.get("direction", "stable"))
                summary_ws.write(row, 3, trend.get("change_percent", 0))
                row += 1
            
            # Detailed data worksheets
            for metric_id, metric_data in report.data.items():
                if metric_id in ["visualizations", "medical_analysis", "business_insights", "predictions"]:
                    continue
                    
                if "error" in metric_data:
                    continue
                
                trend = metric_data.get("trend", {})
                if trend.get("values") and trend.get("timestamps"):
                    ws = workbook.add_worksheet(metric_id[:31])  # Excel worksheet name limit
                    
                    ws.write('A1', 'Timestamp', bold)
                    ws.write('B1', 'Value', bold)
                    
                    for i, (timestamp, value) in enumerate(zip(trend["timestamps"], trend["values"]), 1):
                        ws.write(i, 0, timestamp)
                        ws.write(i, 1, value)
        
        return str(file_path)
    
    async def _generate_json_report(self, report: Report, filename: str) -> str:
        """Generate JSON report"""
        file_path = self.reports_path / f"{filename}.json"
        
        # Convert report to JSON-serializable format
        report_dict = {
            "id": report.id,
            "name": report.name,
            "type": report.type.value,
            "format": report.format.value,
            "generated_at": report.generated_at.isoformat(),
            "data": report.data
        }
        
        with open(file_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        return str(file_path)
    
    async def _generate_csv_report(self, report: Report, filename: str) -> str:
        """Generate CSV report"""
        file_path = self.reports_path / f"{filename}.csv"
        
        # Create summary CSV
        rows = []
        rows.append(["Metric", "Current Value", "Trend Direction", "Change %"])
        
        for metric_id, metric_data in report.data.items():
            if metric_id in ["visualizations", "medical_analysis", "business_insights", "predictions"]:
                continue
                
            if "error" in metric_data:
                continue
            
            current_value = metric_data.get("current_value", 0)
            trend = metric_data.get("trend", {})
            
            rows.append([
                metric_id.replace('_', ' ').title(),
                current_value,
                trend.get("direction", "stable"),
                trend.get("change_percent", 0)
            ])
        
        with open(file_path, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerows(rows)
        
        return str(file_path)

class ReportScheduler:
    """Automated report scheduling and distribution"""
    
    def __init__(self, report_generator: ReportGenerator):
        self.report_generator = report_generator
        self.scheduled_reports: Dict[str, ReportConfig] = {}
        self.running = False
    
    def schedule_report(self, config: ReportConfig):
        """Schedule a report for automatic generation"""
        if config.schedule:
            self.scheduled_reports[config.id] = config
            logger.info(f"Scheduled report: {config.name}")
    
    def unschedule_report(self, config_id: str):
        """Remove a scheduled report"""
        if config_id in self.scheduled_reports:
            del self.scheduled_reports[config_id]
            logger.info(f"Unscheduled report: {config_id}")
    
    async def start_scheduler(self):
        """Start the report scheduler"""
        self.running = True
        
        while self.running:
            try:
                await self._check_scheduled_reports()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """Stop the report scheduler"""
        self.running = False
    
    async def _check_scheduled_reports(self):
        """Check if any reports need to be generated"""
        current_time = datetime.now()
        
        for config in self.scheduled_reports.values():
            if not config.enabled:
                continue
            
            # Simple scheduling check (in practice, use proper cron parser)
            if await self._should_generate_report(config, current_time):
                try:
                    report = await self.report_generator.generate_report(config)
                    
                    if config.recipients:
                        await self._distribute_report(report, config)
                    
                    logger.info(f"Generated scheduled report: {report.name}")
                    
                except Exception as e:
                    logger.error(f"Error generating scheduled report {config.name}: {e}")
    
    async def _should_generate_report(self, config: ReportConfig, current_time: datetime) -> bool:
        """Check if report should be generated now"""
        # Simplified scheduling logic
        if config.schedule == "daily":
            # Generate at 9 AM daily
            return current_time.hour == 9 and current_time.minute == 0
        elif config.schedule == "weekly":
            # Generate on Monday at 9 AM
            return current_time.weekday() == 0 and current_time.hour == 9 and current_time.minute == 0
        elif config.schedule == "monthly":
            # Generate on 1st of month at 9 AM
            return current_time.day == 1 and current_time.hour == 9 and current_time.minute == 0
        
        return False
    
    async def _distribute_report(self, report: Report, config: ReportConfig):
        """Distribute report to recipients"""
        if not config.recipients:
            return
        
        try:
            # Email distribution (simplified)
            smtp_server = "smtp.gmail.com"  # Configure as needed
            smtp_port = 587
            smtp_user = "your-email@gmail.com"  # Configure
            smtp_password = "your-password"  # Configure
            
            msg = MimeMultipart()
            msg['Subject'] = f"Analytics Report: {report.name}"
            msg['From'] = smtp_user
            msg['To'] = ", ".join(config.recipients)
            
            # Email body
            body = f"""
            Analytics Report: {report.name}
            Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
            Type: {report.type.value.title()}
            
            This report has been automatically generated and contains the latest analytics data.
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Attach report file if available
            if report.file_path and Path(report.file_path).exists():
                with open(report.file_path, 'rb') as f:
                    attachment = MimeApplication(f.read())
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=Path(report.file_path).name
                    )
                    msg.attach(attachment)
            
            # Send email (commented out for security)
            # with smtplib.SMTP(smtp_server, smtp_port) as server:
            #     server.starttls()
            #     server.login(smtp_user, smtp_password)
            #     server.send_message(msg)
            
            logger.info(f"Report distributed to {len(config.recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Error distributing report: {e}")

class AdvancedMetricsCalculator:
    """Advanced metrics calculation and KPI system"""
    
    def __init__(self, analytics_collector: AnalyticsDataCollector):
        self.analytics = analytics_collector
        self.kpi_definitions: Dict[str, Dict[str, Any]] = {}
        self.cached_calculations: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize default KPIs
        self._initialize_default_kpis()
    
    def _initialize_default_kpis(self):
        """Initialize default KPI definitions"""
        self.kpi_definitions = {
            "user_engagement_score": {
                "name": "User Engagement Score",
                "description": "Composite score measuring user engagement",
                "target": 75,
                "unit": "score"
            },
            "customer_satisfaction": {
                "name": "Customer Satisfaction",  
                "description": "Customer satisfaction index based on usage patterns",
                "target": 85,
                "unit": "percentage"
            },
            "operational_efficiency": {
                "name": "Operational Efficiency",
                "description": "System operational efficiency metric",
                "target": 95,
                "unit": "percentage"
            }
        }
    
    async def calculate_kpi(self, kpi_name: str, time_range: str = "24h") -> Dict[str, Any]:
        """Calculate a specific KPI"""
        cache_key = f"kpi:{kpi_name}:{time_range}"
        
        # Check cache
        if cache_key in self.cached_calculations:
            cached_entry = self.cached_calculations[cache_key]
            if time.time() - cached_entry['timestamp'] < self.cache_ttl:
                return cached_entry['data']
        
        if kpi_name not in self.kpi_definitions:
            raise ValueError(f"KPI {kpi_name} not defined")
        
        kpi_def = self.kpi_definitions[kpi_name]
        
        # Calculate based on KPI type
        if kpi_name == "user_engagement_score":
            result = await self._calculate_user_engagement(time_range)
        elif kpi_name == "customer_satisfaction":
            result = await self._calculate_customer_satisfaction(time_range)
        elif kpi_name == "operational_efficiency":
            result = await self._calculate_operational_efficiency(time_range)
        else:
            result = {"value": 0, "status": "unknown"}
        
        # Add metadata
        result.update({
            "name": kpi_def["name"],
            "description": kpi_def["description"],
            "target": kpi_def["target"],
            "unit": kpi_def["unit"],
            "calculated_at": datetime.now().isoformat()
        })
        
        # Cache the result
        self.cached_calculations[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        
        return result
    
    async def _calculate_user_engagement(self, time_range: str) -> Dict[str, Any]:
        """Calculate user engagement score"""
        end_time = datetime.now()
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            start_time = end_time - timedelta(hours=hours)
        else:
            start_time = end_time - timedelta(hours=24)
        
        events = await self.analytics.get_events(
            start_time, end_time,
            [AnalyticsEventType.USER_LOGIN, AnalyticsEventType.TRANSCRIPTION_COMPLETE]
        )
        
        if not events:
            return {"value": 0, "components": {}}
        
        unique_users = len(set(e['user_id'] for e in events if e['user_id']))
        total_events = len(events)
        engagement_score = min((total_events / max(unique_users, 1)) * 10, 100)
        
        return {
            "value": round(engagement_score, 2),
            "components": {
                "unique_users": unique_users,
                "total_events": total_events
            }
        }
    
    async def _calculate_customer_satisfaction(self, time_range: str) -> Dict[str, Any]:
        """Calculate customer satisfaction score"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        events = await self.analytics.get_events(
            start_time, end_time,
            [AnalyticsEventType.TRANSCRIPTION_COMPLETE]
        )
        
        if not events:
            return {"value": 80, "components": {}}
        
        total_transcriptions = len(events)
        successful_transcriptions = sum(1 for e in events if e.get('properties', {}).get('accuracy', 0) > 0.8)
        satisfaction_score = (successful_transcriptions / total_transcriptions) * 100 if total_transcriptions > 0 else 80
        
        return {
            "value": round(satisfaction_score, 2),
            "components": {
                "total_transcriptions": total_transcriptions,
                "successful_transcriptions": successful_transcriptions
            }
        }
    
    async def _calculate_operational_efficiency(self, time_range: str) -> Dict[str, Any]:
        """Calculate operational efficiency score"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        error_events = await self.analytics.get_events(
            start_time, end_time,
            [AnalyticsEventType.ERROR_OCCURRED]
        )
        
        all_events = await self.analytics.get_events(start_time, end_time)
        
        total_events = len(all_events)
        error_count = len(error_events)
        
        if total_events == 0:
            return {"value": 100, "components": {}}
        
        error_rate = (error_count / total_events) * 100
        efficiency_score = max(0, 100 - error_rate)
        
        return {
            "value": round(efficiency_score, 2),
            "components": {
                "total_events": total_events,
                "error_count": error_count,
                "error_rate": round(error_rate, 2)
            }
        }

# Usage example
async def demo_analytics_reporting():
    """Demonstrate advanced analytics and reporting system"""
    
    # Initialize components
    analytics_engine = AdvancedAnalyticsEngine()
    report_generator = ReportGenerator(analytics_engine)
    scheduler = ReportScheduler(report_generator)
    
    # Simulate some analytics data
    for i in range(100):
        # Transcription accuracy
        accuracy = 0.95 + np.random.normal(0, 0.03)
        analytics_engine.record_data(AnalyticsData(
            timestamp=datetime.now() - timedelta(hours=i),
            metric_id="transcription_accuracy",
            value=max(0, min(1, accuracy)),
            dimensions={"session_type": "medical" if i % 3 == 0 else "general"},
            user_id=f"user_{i % 10}"
        ))
        
        # Response time
        response_time = 500 + np.random.normal(0, 100)
        analytics_engine.record_data(AnalyticsData(
            timestamp=datetime.now() - timedelta(hours=i),
            metric_id="response_time",
            value=max(0, response_time),
            user_id=f"user_{i % 10}"
        ))
        
        # Daily active users
        analytics_engine.record_data(AnalyticsData(
            timestamp=datetime.now() - timedelta(hours=i),
            metric_id="daily_active_users",
            value=1,
            user_id=f"user_{i % 15}"
        ))
    
    # Create report configuration
    report_config = ReportConfig(
        id=str(uuid.uuid4()),
        name="Weekly Analytics Report",
        type=ReportType.PERFORMANCE,
        format=ReportFormat.HTML,
        metrics=["transcription_accuracy", "response_time", "daily_active_users"],
        time_range="7d",
        recipients=["admin@company.com"],
        schedule="weekly"
    )
    
    # Generate report
    report = await report_generator.generate_report(report_config)
    print(f"Generated report: {report.name}")
    print(f"Report file: {report.file_path}")
    
    # Schedule report
    scheduler.schedule_report(report_config)
    print("Report scheduled for weekly generation")
    
    # Calculate some metrics
    current_accuracy = analytics_engine.calculate_metric("transcription_accuracy", "24h")
    print(f"Current transcription accuracy: {current_accuracy:.3f}")
    
    trend = analytics_engine.calculate_trend("response_time", periods=7)
    print(f"Response time trend: {trend['direction']} ({trend['change_percent']:.1f}% change)")
    
    # Detect anomalies
    anomalies = analytics_engine.detect_anomalies("transcription_accuracy")
    print(f"Detected {len(anomalies)} anomalies in transcription accuracy")
    
    # Business insights
    if report.data.get("business_insights"):
        insights = report.data["business_insights"]
        print(f"Key business insights: {insights.get('key_insights', [])}")

if __name__ == "__main__":
    asyncio.run(demo_analytics_reporting())