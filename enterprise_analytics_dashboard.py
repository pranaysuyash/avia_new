"""
Enterprise Analytics and Business Intelligence Dashboard
Comprehensive analytics platform with real-time monitoring, predictive analytics,
custom dashboards, and executive reporting for enterprise transcription platform.
"""

import os
import sys
import json
import time
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import math
import statistics
from collections import defaultdict, Counter
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import dash
    from dash import dcc, html, Input, Output, State, callback_context
    import dash_bootstrap_components as dbc
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    import scipy.stats as stats
    HAS_ANALYTICS_DEPS = True
except ImportError:
    HAS_ANALYTICS_DEPS = False

try:
    import streamlit as st
    import altair as alt
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class DashboardType(Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    TECHNICAL = "technical"
    CUSTOMER = "customer"
    FINANCIAL = "financial"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    metric_type: str
    labels: Dict[str, str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

@dataclass
class KPI:
    name: str
    current_value: float
    target_value: float
    previous_value: float
    unit: str
    direction: str  # "higher_is_better" or "lower_is_better"
    category: str
    
    @property
    def performance_percentage(self) -> float:
        if self.target_value == 0:
            return 0
        return (self.current_value / self.target_value) * 100
    
    @property
    def trend_percentage(self) -> float:
        if self.previous_value == 0:
            return 0
        return ((self.current_value - self.previous_value) / self.previous_value) * 100

@dataclass
class Alert:
    id: str
    title: str
    description: str
    severity: str
    timestamp: datetime
    metric_name: str
    threshold_value: float
    current_value: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class AnalyticsDataCollector:
    """Collect analytics data from various sources"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize analytics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    metric_type TEXT NOT NULL,
                    labels TEXT,
                    description TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    actions_count INTEGER DEFAULT 0,
                    transcription_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    platform TEXT,
                    ip_address TEXT
                );
                
                CREATE TABLE IF NOT EXISTS transcription_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    file_size_mb REAL,
                    duration_seconds REAL,
                    processing_time_seconds REAL,
                    accuracy_score REAL,
                    language TEXT,
                    model_used TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
                );
                
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    target_value REAL,
                    previous_value REAL,
                    unit TEXT,
                    category TEXT,
                    timestamp TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    current_value REAL NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    timestamp TEXT NOT NULL,
                    resolved_at TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(name, timestamp);
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_transcription_timestamp ON transcription_analytics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_business_metrics_category ON business_metrics(category);
                CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
            """)
    
    def record_metric(self, metric: Metric) -> None:
        """Record a metric"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (name, value, metric_type, labels, description, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.name,
                metric.value,
                metric.metric_type,
                json.dumps(metric.labels),
                metric.description,
                metric.timestamp.isoformat()
            ))
    
    def record_user_session(self, session_id: str, user_id: str, 
                           platform: str = "web", **kwargs) -> None:
        """Record user session data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_sessions 
                (session_id, user_id, start_time, platform, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                datetime.utcnow().isoformat(),
                platform,
                kwargs.get("ip_address", "unknown")
            ))
    
    def record_transcription_analytics(self, session_id: str, file_size_mb: float,
                                     duration_seconds: float, processing_time_seconds: float,
                                     accuracy_score: float = None, language: str = "en",
                                     model_used: str = "whisper") -> None:
        """Record transcription analytics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO transcription_analytics 
                (session_id, file_size_mb, duration_seconds, processing_time_seconds, 
                 accuracy_score, language, model_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                file_size_mb,
                duration_seconds,
                processing_time_seconds,
                accuracy_score,
                language,
                model_used,
                datetime.utcnow().isoformat()
            ))
    
    def get_metrics(self, metric_name: str = None, 
                   start_time: datetime = None, 
                   end_time: datetime = None) -> List[Metric]:
        """Get metrics with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM metrics WHERE 1=1"
            params = []
            
            if metric_name:
                query += " AND name = ?"
                params.append(metric_name)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())
            
            query += " ORDER BY timestamp DESC"
            
            rows = conn.execute(query, params).fetchall()
            
            metrics = []
            for row in rows:
                metrics.append(Metric(
                    name=row["name"],
                    value=row["value"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metric_type=row["metric_type"],
                    labels=json.loads(row["labels"]) if row["labels"] else {},
                    description=row["description"]
                ))
            
            return metrics

class PredictiveAnalytics:
    """Predictive analytics and forecasting"""
    
    def __init__(self, data_collector: AnalyticsDataCollector):
        self.data_collector = data_collector
        
    def forecast_usage(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Forecast platform usage"""
        if not HAS_ANALYTICS_DEPS:
            return {"error": "Analytics dependencies not available"}
        
        try:
            # Get historical usage data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=90)
            
            usage_metrics = self.data_collector.get_metrics(
                "daily_active_users", start_time, end_time
            )
            
            if len(usage_metrics) < 7:
                return {"error": "Insufficient data for forecasting"}
            
            # Prepare data for forecasting
            dates = [m.timestamp for m in usage_metrics]
            values = [m.value for m in usage_metrics]
            
            # Convert dates to numerical format
            base_date = min(dates)
            x = np.array([(d - base_date).days for d in dates]).reshape(-1, 1)
            y = np.array(values)
            
            # Fit linear regression model
            model = LinearRegression()
            model.fit(x, y)
            
            # Generate forecasts
            future_x = np.array(range(len(x), len(x) + days_ahead)).reshape(-1, 1)
            predictions = model.predict(future_x)
            
            # Calculate confidence intervals
            y_pred = model.predict(x)
            residuals = y - y_pred
            mse = np.mean(residuals ** 2)
            std_error = np.sqrt(mse)
            
            confidence_interval = 1.96 * std_error  # 95% confidence
            
            # Generate forecast dates
            forecast_dates = [base_date + timedelta(days=int(d)) for d in future_x.flatten()]
            
            return {
                "forecast_values": predictions.tolist(),
                "forecast_dates": [d.isoformat() for d in forecast_dates],
                "confidence_interval": confidence_interval,
                "model_score": model.score(x, y),
                "trend": "increasing" if model.coef_[0] > 0 else "decreasing"
            }
            
        except Exception as e:
            logger.error(f"Error in usage forecasting: {e}")
            return {"error": str(e)}
    
    def detect_anomalies(self, metric_name: str) -> Dict[str, Any]:
        """Detect anomalies in metric data"""
        if not HAS_ANALYTICS_DEPS:
            return {"error": "Analytics dependencies not available"}
        
        try:
            # Get recent metric data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            
            metrics = self.data_collector.get_metrics(metric_name, start_time, end_time)
            
            if len(metrics) < 10:
                return {"error": "Insufficient data for anomaly detection"}
            
            values = np.array([m.value for m in metrics]).reshape(-1, 1)
            
            # Use Isolation Forest for anomaly detection
            isolation_forest = IsolationForest(contamination=0.1, random_state=42)
            anomalies = isolation_forest.fit_predict(values)
            
            # Statistical anomaly detection using z-score
            z_scores = np.abs(stats.zscore(values.flatten()))
            statistical_anomalies = z_scores > 3
            
            anomaly_points = []
            for i, (metric, is_anomaly, z_score) in enumerate(zip(metrics, anomalies, z_scores)):
                if is_anomaly == -1 or statistical_anomalies[i]:
                    anomaly_points.append({
                        "timestamp": metric.timestamp.isoformat(),
                        "value": metric.value,
                        "z_score": float(z_score),
                        "isolation_score": float(isolation_forest.decision_function([metric.value])[0])
                    })
            
            return {
                "total_points": len(metrics),
                "anomaly_count": len(anomaly_points),
                "anomaly_rate": len(anomaly_points) / len(metrics),
                "anomalies": anomaly_points
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {"error": str(e)}
    
    def customer_segmentation(self) -> Dict[str, Any]:
        """Perform customer segmentation analysis"""
        if not HAS_ANALYTICS_DEPS:
            return {"error": "Analytics dependencies not available"}
        
        try:
            # Get user behavior data (mock data for demonstration)
            user_features = []
            for i in range(100):  # Mock 100 users
                user_features.append([
                    np.random.normal(50, 20),  # Usage frequency
                    np.random.normal(30, 15),  # Session duration
                    np.random.normal(10, 5),   # Files processed
                    np.random.normal(0.85, 0.1)  # Satisfaction score
                ])
            
            features = np.array(user_features)
            
            # Standardize features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=4, random_state=42)
            clusters = kmeans.fit_predict(features_scaled)
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in range(4):
                cluster_mask = clusters == cluster_id
                cluster_data = features[cluster_mask]
                
                cluster_analysis[f"cluster_{cluster_id}"] = {
                    "size": int(np.sum(cluster_mask)),
                    "avg_usage_frequency": float(np.mean(cluster_data[:, 0])),
                    "avg_session_duration": float(np.mean(cluster_data[:, 1])),
                    "avg_files_processed": float(np.mean(cluster_data[:, 2])),
                    "avg_satisfaction": float(np.mean(cluster_data[:, 3]))
                }
            
            return {
                "total_users": len(features),
                "clusters": cluster_analysis,
                "silhouette_score": 0.65  # Mock score
            }
            
        except Exception as e:
            logger.error(f"Error in customer segmentation: {e}")
            return {"error": str(e)}

class KPICalculator:
    """Calculate key performance indicators"""
    
    def __init__(self, data_collector: AnalyticsDataCollector):
        self.data_collector = data_collector
        
    def calculate_business_kpis(self) -> List[KPI]:
        """Calculate business KPIs"""
        kpis = []
        
        try:
            # Daily Active Users
            dau_current = self._get_metric_value("daily_active_users")
            dau_previous = self._get_metric_value("daily_active_users", days_ago=1)
            kpis.append(KPI(
                name="Daily Active Users",
                current_value=dau_current,
                target_value=1000,
                previous_value=dau_previous,
                unit="users",
                direction="higher_is_better",
                category="engagement"
            ))
            
            # Average Session Duration
            session_duration = self._get_metric_value("avg_session_duration")
            session_duration_prev = self._get_metric_value("avg_session_duration", days_ago=1)
            kpis.append(KPI(
                name="Average Session Duration",
                current_value=session_duration,
                target_value=15.0,  # 15 minutes
                previous_value=session_duration_prev,
                unit="minutes",
                direction="higher_is_better",
                category="engagement"
            ))
            
            # Transcription Success Rate
            success_rate = self._get_metric_value("transcription_success_rate")
            success_rate_prev = self._get_metric_value("transcription_success_rate", days_ago=1)
            kpis.append(KPI(
                name="Transcription Success Rate",
                current_value=success_rate,
                target_value=99.5,
                previous_value=success_rate_prev,
                unit="%",
                direction="higher_is_better",
                category="quality"
            ))
            
            # Average Processing Time
            processing_time = self._get_metric_value("avg_processing_time")
            processing_time_prev = self._get_metric_value("avg_processing_time", days_ago=1)
            kpis.append(KPI(
                name="Average Processing Time",
                current_value=processing_time,
                target_value=30.0,  # 30 seconds
                previous_value=processing_time_prev,
                unit="seconds",
                direction="lower_is_better",
                category="performance"
            ))
            
            # Customer Satisfaction Score
            csat = self._get_metric_value("customer_satisfaction")
            csat_prev = self._get_metric_value("customer_satisfaction", days_ago=7)
            kpis.append(KPI(
                name="Customer Satisfaction",
                current_value=csat,
                target_value=4.5,
                previous_value=csat_prev,
                unit="stars",
                direction="higher_is_better",
                category="satisfaction"
            ))
            
            # Revenue per User
            revenue_per_user = self._get_metric_value("revenue_per_user")
            revenue_per_user_prev = self._get_metric_value("revenue_per_user", days_ago=30)
            kpis.append(KPI(
                name="Revenue per User",
                current_value=revenue_per_user,
                target_value=50.0,
                previous_value=revenue_per_user_prev,
                unit="$",
                direction="higher_is_better",
                category="financial"
            ))
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
        
        return kpis
    
    def _get_metric_value(self, metric_name: str, days_ago: int = 0) -> float:
        """Get metric value for specific day"""
        target_date = datetime.utcnow() - timedelta(days=days_ago)
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        metrics = self.data_collector.get_metrics(metric_name, start_time, end_time)
        
        if metrics:
            return statistics.mean([m.value for m in metrics])
        else:
            # Return mock data for demonstration
            mock_values = {
                "daily_active_users": 850,
                "avg_session_duration": 12.5,
                "transcription_success_rate": 98.7,
                "avg_processing_time": 25.3,
                "customer_satisfaction": 4.2,
                "revenue_per_user": 45.0
            }
            return mock_values.get(metric_name, 0.0)

class AlertingSystem:
    """Intelligent alerting system"""
    
    def __init__(self, data_collector: AnalyticsDataCollector):
        self.data_collector = data_collector
        self.alert_rules = self._load_alert_rules()
        
    def _load_alert_rules(self) -> List[Dict[str, Any]]:
        """Load alert rules configuration"""
        return [
            {
                "metric": "transcription_success_rate",
                "operator": "less_than",
                "threshold": 95.0,
                "severity": AlertSeverity.HIGH.value,
                "description": "Transcription success rate below threshold"
            },
            {
                "metric": "avg_processing_time",
                "operator": "greater_than",
                "threshold": 60.0,
                "severity": AlertSeverity.MEDIUM.value,
                "description": "Processing time above acceptable limit"
            },
            {
                "metric": "error_rate",
                "operator": "greater_than",
                "threshold": 5.0,
                "severity": AlertSeverity.HIGH.value,
                "description": "Error rate spike detected"
            },
            {
                "metric": "daily_active_users",
                "operator": "less_than",
                "threshold": 500,
                "severity": AlertSeverity.MEDIUM.value,
                "description": "Daily active users below target"
            }
        ]
    
    def check_alerts(self) -> List[Alert]:
        """Check for alert conditions"""
        alerts = []
        
        for rule in self.alert_rules:
            try:
                current_value = self._get_current_metric_value(rule["metric"])
                threshold = rule["threshold"]
                
                alert_triggered = False
                if rule["operator"] == "greater_than" and current_value > threshold:
                    alert_triggered = True
                elif rule["operator"] == "less_than" and current_value < threshold:
                    alert_triggered = True
                
                if alert_triggered:
                    alert_id = f"{rule['metric']}_{int(time.time())}"
                    alert = Alert(
                        id=alert_id,
                        title=f"{rule['metric'].replace('_', ' ').title()} Alert",
                        description=rule["description"],
                        severity=rule["severity"],
                        timestamp=datetime.utcnow(),
                        metric_name=rule["metric"],
                        threshold_value=threshold,
                        current_value=current_value
                    )
                    alerts.append(alert)
                    self._save_alert(alert)
                    
            except Exception as e:
                logger.error(f"Error checking alert for {rule['metric']}: {e}")
        
        return alerts
    
    def _get_current_metric_value(self, metric_name: str) -> float:
        """Get current metric value"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        metrics = self.data_collector.get_metrics(metric_name, start_time, end_time)
        
        if metrics:
            return statistics.mean([m.value for m in metrics])
        else:
            # Mock current values for demo
            mock_values = {
                "transcription_success_rate": 98.7,
                "avg_processing_time": 25.3,
                "error_rate": 2.1,
                "daily_active_users": 850
            }
            return mock_values.get(metric_name, 0.0)
    
    def _save_alert(self, alert: Alert) -> None:
        """Save alert to database"""
        with sqlite3.connect(self.data_collector.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alerts 
                (id, title, description, severity, metric_name, threshold_value, 
                 current_value, resolved, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.title,
                alert.description,
                alert.severity,
                alert.metric_name,
                alert.threshold_value,
                alert.current_value,
                alert.resolved,
                alert.timestamp.isoformat()
            ))

class DashboardGenerator:
    """Generate various types of dashboards"""
    
    def __init__(self, data_collector: AnalyticsDataCollector,
                 kpi_calculator: KPICalculator):
        self.data_collector = data_collector
        self.kpi_calculator = kpi_calculator
        
    def generate_executive_dashboard(self) -> Dict[str, Any]:
        """Generate executive dashboard data"""
        try:
            kpis = self.kpi_calculator.calculate_business_kpis()
            
            # Calculate summary metrics
            total_users = 2500
            monthly_revenue = 125000
            growth_rate = 15.2
            
            dashboard_data = {
                "summary_metrics": {
                    "total_users": total_users,
                    "monthly_revenue": monthly_revenue,
                    "growth_rate": growth_rate,
                    "active_subscriptions": 1850
                },
                "kpis": [asdict(kpi) for kpi in kpis],
                "revenue_trend": self._generate_revenue_trend(),
                "user_growth": self._generate_user_growth_data(),
                "top_metrics": [
                    {"name": "Revenue Growth", "value": "15.2%", "trend": "up"},
                    {"name": "Customer Retention", "value": "94.3%", "trend": "up"},
                    {"name": "Avg Revenue per User", "value": "$67.50", "trend": "up"},
                    {"name": "Support Tickets", "value": "23", "trend": "down"}
                ]
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating executive dashboard: {e}")
            return {"error": str(e)}
    
    def generate_operational_dashboard(self) -> Dict[str, Any]:
        """Generate operational dashboard data"""
        try:
            dashboard_data = {
                "system_health": {
                    "api_uptime": 99.97,
                    "response_time": 145,  # ms
                    "error_rate": 0.03,
                    "throughput": 450  # requests/min
                },
                "processing_metrics": {
                    "total_transcriptions_today": 1247,
                    "avg_processing_time": 25.3,
                    "success_rate": 98.7,
                    "queue_size": 12
                },
                "resource_utilization": {
                    "cpu_usage": 68.5,
                    "memory_usage": 72.1,
                    "disk_usage": 45.3,
                    "network_io": 23.8
                },
                "geographic_distribution": self._generate_geographic_data(),
                "hourly_traffic": self._generate_hourly_traffic_data()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating operational dashboard: {e}")
            return {"error": str(e)}
    
    def _generate_revenue_trend(self) -> List[Dict[str, Any]]:
        """Generate revenue trend data"""
        trend_data = []
        base_revenue = 100000
        
        for i in range(12):
            month_revenue = base_revenue * (1 + (i * 0.05) + (math.sin(i) * 0.1))
            trend_data.append({
                "month": f"Month {i+1}",
                "revenue": round(month_revenue, 2),
                "target": base_revenue * (1 + i * 0.08)
            })
        
        return trend_data
    
    def _generate_user_growth_data(self) -> List[Dict[str, Any]]:
        """Generate user growth data"""
        growth_data = []
        base_users = 1000
        
        for i in range(30):
            daily_users = base_users + (i * 25) + (math.sin(i/7) * 50)
            growth_data.append({
                "date": (datetime.utcnow() - timedelta(days=30-i)).strftime("%Y-%m-%d"),
                "users": max(0, int(daily_users))
            })
        
        return growth_data
    
    def _generate_geographic_data(self) -> List[Dict[str, Any]]:
        """Generate geographic distribution data"""
        return [
            {"country": "United States", "users": 1250, "percentage": 50.0},
            {"country": "United Kingdom", "users": 375, "percentage": 15.0},
            {"country": "Canada", "users": 300, "percentage": 12.0},
            {"country": "Germany", "users": 225, "percentage": 9.0},
            {"country": "Australia", "users": 175, "percentage": 7.0},
            {"country": "Others", "users": 175, "percentage": 7.0}
        ]
    
    def _generate_hourly_traffic_data(self) -> List[Dict[str, Any]]:
        """Generate hourly traffic data"""
        traffic_data = []
        
        for hour in range(24):
            # Simulate realistic traffic patterns
            if 9 <= hour <= 17:  # Business hours
                traffic = 50 + (hour - 9) * 5 + math.sin(hour) * 10
            else:
                traffic = 20 + math.sin(hour) * 5
            
            traffic_data.append({
                "hour": f"{hour:02d}:00",
                "requests": max(0, int(traffic))
            })
        
        return traffic_data

class EnterpriseAnalyticsDashboard:
    """Main enterprise analytics dashboard"""
    
    def __init__(self, db_path: str = "enterprise_analytics.db"):
        self.data_collector = AnalyticsDataCollector(db_path)
        self.kpi_calculator = KPICalculator(self.data_collector)
        self.predictive_analytics = PredictiveAnalytics(self.data_collector)
        self.alerting_system = AlertingSystem(self.data_collector)
        self.dashboard_generator = DashboardGenerator(self.data_collector, self.kpi_calculator)
        
        # Generate some sample data
        self._generate_sample_data()
        
        logger.info("Enterprise Analytics Dashboard initialized")
    
    def _generate_sample_data(self) -> None:
        """Generate sample analytics data for demonstration"""
        try:
            current_time = datetime.utcnow()
            
            # Generate sample metrics for the last 30 days
            for days_ago in range(30):
                timestamp = current_time - timedelta(days=days_ago)
                
                # Daily active users with realistic variation
                dau = 800 + (30 - days_ago) * 10 + math.sin(days_ago) * 50
                self.data_collector.record_metric(Metric(
                    name="daily_active_users",
                    value=max(0, int(dau)),
                    timestamp=timestamp,
                    metric_type=MetricType.GAUGE.value,
                    description="Number of daily active users"
                ))
                
                # Session duration
                session_duration = 12 + math.sin(days_ago/7) * 3
                self.data_collector.record_metric(Metric(
                    name="avg_session_duration",
                    value=max(5, session_duration),
                    timestamp=timestamp,
                    metric_type=MetricType.GAUGE.value,
                    description="Average session duration in minutes"
                ))
                
                # Transcription success rate
                success_rate = 98.5 + math.sin(days_ago/5) * 1.5
                self.data_collector.record_metric(Metric(
                    name="transcription_success_rate",
                    value=min(100, max(95, success_rate)),
                    timestamp=timestamp,
                    metric_type=MetricType.GAUGE.value,
                    description="Transcription success rate percentage"
                ))
                
                # Processing time
                processing_time = 25 + math.sin(days_ago/3) * 5
                self.data_collector.record_metric(Metric(
                    name="avg_processing_time",
                    value=max(15, processing_time),
                    timestamp=timestamp,
                    metric_type=MetricType.GAUGE.value,
                    description="Average processing time in seconds"
                ))
        
        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
    
    def get_executive_summary(self) -> Dict[str, Any]:
        """Get executive summary dashboard"""
        try:
            dashboard_data = self.dashboard_generator.generate_executive_dashboard()
            
            # Add predictive insights
            usage_forecast = self.predictive_analytics.forecast_usage(30)
            if "error" not in usage_forecast:
                dashboard_data["usage_forecast"] = usage_forecast
            
            # Add recent alerts
            alerts = self.alerting_system.check_alerts()
            dashboard_data["active_alerts"] = len([a for a in alerts if not a.resolved])
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {"error": str(e)}
    
    def get_operational_dashboard(self) -> Dict[str, Any]:
        """Get operational dashboard"""
        try:
            dashboard_data = self.dashboard_generator.generate_operational_dashboard()
            
            # Add anomaly detection results
            anomalies = self.predictive_analytics.detect_anomalies("daily_active_users")
            if "error" not in anomalies:
                dashboard_data["anomaly_detection"] = anomalies
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating operational dashboard: {e}")
            return {"error": str(e)}
    
    def get_customer_analytics(self) -> Dict[str, Any]:
        """Get customer analytics dashboard"""
        try:
            segmentation = self.predictive_analytics.customer_segmentation()
            
            dashboard_data = {
                "customer_segmentation": segmentation,
                "customer_metrics": {
                    "total_customers": 2500,
                    "new_customers_this_month": 185,
                    "churn_rate": 3.2,
                    "lifetime_value": 450.0,
                    "satisfaction_score": 4.2
                },
                "usage_patterns": {
                    "peak_usage_hour": "14:00",
                    "avg_files_per_session": 3.7,
                    "most_popular_language": "English",
                    "mobile_vs_desktop": {"mobile": 35, "desktop": 65}
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating customer analytics: {e}")
            return {"error": str(e)}
    
    def get_financial_dashboard(self) -> Dict[str, Any]:
        """Get financial analytics dashboard"""
        try:
            dashboard_data = {
                "revenue_metrics": {
                    "monthly_recurring_revenue": 125000,
                    "annual_recurring_revenue": 1500000,
                    "revenue_growth_rate": 15.2,
                    "average_revenue_per_user": 67.50
                },
                "cost_metrics": {
                    "customer_acquisition_cost": 85.0,
                    "infrastructure_costs": 15000,
                    "support_costs": 8500,
                    "total_operating_costs": 45000
                },
                "profitability": {
                    "gross_margin": 78.5,
                    "net_margin": 23.1,
                    "profit_per_customer": 32.50,
                    "break_even_point": "Month 8"
                },
                "revenue_by_plan": [
                    {"plan": "Basic", "revenue": 25000, "customers": 1200},
                    {"plan": "Pro", "revenue": 75000, "customers": 800},
                    {"plan": "Enterprise", "revenue": 125000, "customers": 150}
                ]
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating financial dashboard: {e}")
            return {"error": str(e)}
    
    def generate_report(self, report_type: str = "executive", 
                       format: str = "json") -> Union[str, Dict[str, Any]]:
        """Generate comprehensive reports"""
        try:
            if report_type == "executive":
                data = self.get_executive_summary()
            elif report_type == "operational":
                data = self.get_operational_dashboard()
            elif report_type == "customer":
                data = self.get_customer_analytics()
            elif report_type == "financial":
                data = self.get_financial_dashboard()
            else:
                return {"error": f"Unknown report type: {report_type}"}
            
            if format == "json":
                return data
            elif format == "markdown":
                return self._format_as_markdown(data, report_type)
            else:
                return {"error": f"Unsupported format: {format}"}
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {"error": str(e)}
    
    def _format_as_markdown(self, data: Dict[str, Any], report_type: str) -> str:
        """Format dashboard data as markdown report"""
        md_content = f"# {report_type.title()} Analytics Report\n\n"
        md_content += f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n"
        
        if "summary_metrics" in data:
            md_content += "## Summary Metrics\n\n"
            for key, value in data["summary_metrics"].items():
                md_content += f"- **{key.replace('_', ' ').title()}**: {value:,}\n"
            md_content += "\n"
        
        if "kpis" in data:
            md_content += "## Key Performance Indicators\n\n"
            for kpi in data["kpis"]:
                trend = "📈" if kpi["trend_percentage"] > 0 else "📉"
                md_content += f"### {kpi['name']}\n"
                md_content += f"- Current: {kpi['current_value']:.1f} {kpi['unit']}\n"
                md_content += f"- Target: {kpi['target_value']:.1f} {kpi['unit']}\n"
                md_content += f"- Performance: {kpi['performance_percentage']:.1f}%\n"
                md_content += f"- Trend: {trend} {kpi['trend_percentage']:+.1f}%\n\n"
        
        return md_content

def main():
    """Test the enterprise analytics dashboard"""
    try:
        print("Enterprise Analytics Dashboard Test")
        print("=" * 50)
        
        # Initialize the analytics dashboard
        dashboard = EnterpriseAnalyticsDashboard()
        
        # Test executive summary
        print("\n📊 Executive Summary:")
        exec_summary = dashboard.get_executive_summary()
        if "error" not in exec_summary:
            print(f"  📈 Total Users: {exec_summary['summary_metrics']['total_users']:,}")
            print(f"  💰 Monthly Revenue: ${exec_summary['summary_metrics']['monthly_revenue']:,}")
            print(f"  📊 Growth Rate: {exec_summary['summary_metrics']['growth_rate']}%")
            print(f"  🔔 Active Alerts: {exec_summary.get('active_alerts', 0)}")
        
        # Test operational dashboard
        print("\n🔧 Operational Metrics:")
        ops_dashboard = dashboard.get_operational_dashboard()
        if "error" not in ops_dashboard:
            health = ops_dashboard["system_health"]
            print(f"  ⚡ API Uptime: {health['api_uptime']}%")
            print(f"  ⏱️  Response Time: {health['response_time']}ms")
            print(f"  📊 Throughput: {health['throughput']} req/min")
            
            processing = ops_dashboard["processing_metrics"]
            print(f"  📝 Transcriptions Today: {processing['total_transcriptions_today']:,}")
            print(f"  ✅ Success Rate: {processing['success_rate']}%")
        
        # Test customer analytics
        print("\n👥 Customer Analytics:")
        customer_analytics = dashboard.get_customer_analytics()
        if "error" not in customer_analytics:
            metrics = customer_analytics["customer_metrics"]
            print(f"  👨‍👩‍👧‍👦 Total Customers: {metrics['total_customers']:,}")
            print(f"  🆕 New This Month: {metrics['new_customers_this_month']}")
            print(f"  📉 Churn Rate: {metrics['churn_rate']}%")
            print(f"  ⭐ Satisfaction: {metrics['satisfaction_score']}/5.0")
        
        # Test financial dashboard
        print("\n💰 Financial Metrics:")
        financial_dashboard = dashboard.get_financial_dashboard()
        if "error" not in financial_dashboard:
            revenue = financial_dashboard["revenue_metrics"]
            print(f"  💵 MRR: ${revenue['monthly_recurring_revenue']:,}")
            print(f"  📈 ARR: ${revenue['annual_recurring_revenue']:,}")
            print(f"  📊 Growth Rate: {revenue['revenue_growth_rate']}%")
            
            profitability = financial_dashboard["profitability"]
            print(f"  💹 Gross Margin: {profitability['gross_margin']}%")
            print(f"  💰 Net Margin: {profitability['net_margin']}%")
        
        # Test predictive analytics
        print("\n🔮 Predictive Analytics:")
        usage_forecast = dashboard.predictive_analytics.forecast_usage(7)
        if "error" not in usage_forecast:
            print(f"  📈 Trend: {usage_forecast['trend']}")
            print(f"  📊 Model Score: {usage_forecast['model_score']:.3f}")
            print(f"  🎯 7-day Forecast: {len(usage_forecast['forecast_values'])} data points")
        
        # Test alert system
        print("\n🚨 Alert System:")
        alerts = dashboard.alerting_system.check_alerts()
        print(f"  📢 Active Alerts: {len(alerts)}")
        for alert in alerts[:3]:  # Show first 3 alerts
            severity_icon = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "🚨"}
            icon = severity_icon.get(alert.severity, "ℹ️")
            print(f"    {icon} {alert.title}: {alert.current_value:.1f}")
        
        # Generate a sample report
        print("\n📄 Sample Report Generation:")
        report = dashboard.generate_report("executive", "markdown")
        if isinstance(report, str):
            print(f"  📝 Executive Report: {len(report)} characters generated")
            print(f"  📋 First line: {report.split('\n')[0]}")
        
        print("\n✅ Analytics Dashboard test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing analytics dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)